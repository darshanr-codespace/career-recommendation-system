"""
modules/companies.py
Companies and job listings exploration module.
Supports search, filter, bookmark, and job details.
"""
import json
from flask import Blueprint, request, jsonify, session
from modules.auth import login_required
from database.models import get_db

companies_bp = Blueprint("companies", __name__)


@companies_bp.route("/companies", methods=["GET"])
@login_required
def list_companies():
    """
    GET /api/companies
    Query params: search, industry, location, has_internship, page, per_page
    """
    search        = request.args.get("search", "").strip().lower()
    industry      = request.args.get("industry", "").strip()
    location      = request.args.get("location", "").strip()
    has_internship= request.args.get("has_internship", "")
    page          = int(request.args.get("page", 1))
    per_page      = int(request.args.get("per_page", 12))

    conn  = get_db()
    query = "SELECT * FROM company WHERE 1=1"
    params = []

    if search:
        query += " AND (LOWER(name) LIKE ? OR LOWER(industry) LIKE ? OR LOWER(description) LIKE ?)"
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    if industry:
        query += " AND industry=?"
        params.append(industry)
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if has_internship == "1":
        query += " AND has_internship=1"

    total    = conn.execute(f"SELECT COUNT(*) FROM ({query})", params).fetchone()[0]
    offset   = (page - 1) * per_page
    companies= conn.execute(
        query + f" ORDER BY name LIMIT {per_page} OFFSET {offset}", params
    ).fetchall()

    # For each company, attach open job count
    result = []
    for c in companies:
        job_count = conn.execute(
            "SELECT COUNT(*) FROM job_listing WHERE company_id=?", (c["company_id"],)
        ).fetchone()[0]
        d = dict(c)
        d["open_jobs"] = job_count
        result.append(d)

    # Distinct industries for filter dropdown
    industries = [r[0] for r in conn.execute(
        "SELECT DISTINCT industry FROM company ORDER BY industry"
    ).fetchall()]

    conn.close()
    return jsonify({
        "companies": result,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "industries": industries,
    }), 200


@companies_bp.route("/jobs", methods=["GET"])
@login_required
def list_jobs():
    """
    GET /api/jobs
    Query params: search, domain, location, job_type, salary_min, salary_max,
                  is_internship, company_id, page, per_page
    """
    search      = request.args.get("search", "").strip().lower()
    domain      = request.args.get("domain", "").strip()
    location    = request.args.get("location", "").strip()
    job_type    = request.args.get("job_type", "").strip()
    sal_min     = request.args.get("salary_min", "")
    sal_max     = request.args.get("salary_max", "")
    internship  = request.args.get("is_internship", "")
    company_id  = request.args.get("company_id", "")
    page        = int(request.args.get("page", 1))
    per_page    = int(request.args.get("per_page", 12))
    uid         = session["user_id"]

    conn   = get_db()
    query  = """
        SELECT j.*, c.name as company_name, c.industry, c.location as company_location,
               c.logo_icon, c.website
        FROM job_listing j
        JOIN company c ON c.company_id = j.company_id
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (LOWER(j.title) LIKE ? OR LOWER(j.required_skills) LIKE ? OR LOWER(c.name) LIKE ?)"
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    if domain:
        query += " AND j.domain=?"
        params.append(domain)
    if location:
        query += " AND (LOWER(j.location) LIKE ? OR LOWER(c.location) LIKE ?)"
        params += [f"%{location}%", f"%{location}%"]
    if job_type:
        query += " AND j.job_type=?"
        params.append(job_type)
    if sal_min:
        query += " AND j.salary_max >= ?"
        params.append(int(sal_min))
    if sal_max:
        query += " AND j.salary_min <= ?"
        params.append(int(sal_max))
    if internship == "1":
        query += " AND j.is_internship=1"
    elif internship == "0":
        query += " AND j.is_internship=0"
    if company_id:
        query += " AND j.company_id=?"
        params.append(int(company_id))

    total  = conn.execute(f"SELECT COUNT(*) FROM ({query})", params).fetchone()[0]
    offset = (page - 1) * per_page
    jobs   = conn.execute(
        query + f" ORDER BY j.posted_days_ago ASC, j.salary_max DESC LIMIT {per_page} OFFSET {offset}",
        params
    ).fetchall()

    # Get bookmarks for current user
    bookmarks = set(
        r[0] for r in conn.execute(
            "SELECT job_id FROM bookmarked_job WHERE user_id=?", (uid,)
        ).fetchall()
    )

    # Distinct domains
    domains = [r[0] for r in conn.execute(
        "SELECT DISTINCT domain FROM job_listing WHERE domain IS NOT NULL ORDER BY domain"
    ).fetchall()]

    result = []
    for j in jobs:
        d = dict(j)
        d["is_bookmarked"] = j["job_id"] in bookmarks
        d["skills_list"]   = [s.strip() for s in (j["required_skills"] or "").split(",")]
        result.append(d)

    conn.close()
    return jsonify({
        "jobs":        result,
        "total":       total,
        "page":        page,
        "per_page":    per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "domains":     domains,
    }), 200


@companies_bp.route("/jobs/<int:job_id>", methods=["GET"])
@login_required
def job_detail(job_id: int):
    uid  = session["user_id"]
    conn = get_db()
    job  = conn.execute("""
        SELECT j.*, c.name as company_name, c.industry, c.description as company_desc,
               c.location as company_location, c.logo_icon, c.website, c.size, c.has_internship
        FROM job_listing j JOIN company c ON c.company_id=j.company_id
        WHERE j.job_id=?
    """, (job_id,)).fetchone()
    if not job:
        conn.close()
        return jsonify({"error": "Job not found"}), 404

    is_bookmarked = conn.execute(
        "SELECT 1 FROM bookmarked_job WHERE user_id=? AND job_id=?", (uid, job_id)
    ).fetchone() is not None

    # Similar jobs from same company/domain
    similar = conn.execute("""
        SELECT j.job_id, j.title, j.salary_min, j.salary_max, c.name as company_name
        FROM job_listing j JOIN company c ON c.company_id=j.company_id
        WHERE (j.company_id=? OR j.domain=?) AND j.job_id != ?
        ORDER BY j.posted_days_ago ASC LIMIT 4
    """, (job["company_id"], job["domain"], job_id)).fetchall()

    conn.close()
    d = dict(job)
    d["is_bookmarked"] = is_bookmarked
    d["skills_list"]   = [s.strip() for s in (job["required_skills"] or "").split(",")]
    d["similar_jobs"]  = [dict(s) for s in similar]
    return jsonify({"job": d}), 200


@companies_bp.route("/jobs/by-career/<int:career_id>", methods=["GET"])
@login_required
def jobs_by_career(career_id: int):
    """
    GET /api/jobs/by-career/<career_id>
    Returns job listings and companies hiring for the given career's domain.
    Query params: limit (default 6)
    """
    limit = int(request.args.get("limit", 6))
    uid   = session["user_id"]
    conn  = get_db()

    # Get the career's domain
    career = conn.execute(
        "SELECT career_name, domain FROM career WHERE career_id=?", (career_id,)
    ).fetchone()
    if not career:
        conn.close()
        return jsonify({"error": "Career not found"}), 404

    domain = career["domain"]

    # Fetch jobs matching the domain
    jobs = conn.execute(
        """
        SELECT j.*, c.name as company_name, c.industry, c.location as company_location,
               c.logo_icon, c.website, c.size, c.description as company_desc
        FROM job_listing j
        JOIN company c ON c.company_id = j.company_id
        WHERE j.domain = ?
        ORDER BY j.posted_days_ago ASC, j.salary_max DESC
        LIMIT ?
        """,
        (domain, limit),
    ).fetchall()

    # Fallback: if no exact domain match, grab recent jobs
    if not jobs:
        jobs = conn.execute(
            """
            SELECT j.*, c.name as company_name, c.industry, c.location as company_location,
                   c.logo_icon, c.website, c.size, c.description as company_desc
            FROM job_listing j
            JOIN company c ON c.company_id = j.company_id
            ORDER BY j.posted_days_ago ASC, j.salary_max DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    # Get bookmarks for this user
    bookmarks = set(
        r[0]
        for r in conn.execute(
            "SELECT job_id FROM bookmarked_job WHERE user_id=?", (uid,)
        ).fetchall()
    )

    # Total jobs count in domain
    total_in_domain = conn.execute(
        "SELECT COUNT(*) FROM job_listing WHERE domain=?", (domain,)
    ).fetchone()[0]

    conn.close()

    result = []
    for j in jobs:
        d = dict(j)
        d["is_bookmarked"] = j["job_id"] in bookmarks
        d["skills_list"]   = [s.strip() for s in (j["required_skills"] or "").split(",")]
        result.append(d)

    return jsonify({
        "jobs":           result,
        "domain":         domain,
        "career_name":    career["career_name"],
        "total_in_domain": total_in_domain,
    }), 200


@companies_bp.route("/jobs/<int:job_id>/bookmark", methods=["POST"])
@login_required
def toggle_bookmark(job_id: int):
    uid  = session["user_id"]
    conn = get_db()
    existing = conn.execute(
        "SELECT 1 FROM bookmarked_job WHERE user_id=? AND job_id=?", (uid, job_id)
    ).fetchone()

    if existing:
        conn.execute(
            "DELETE FROM bookmarked_job WHERE user_id=? AND job_id=?", (uid, job_id)
        )
        bookmarked = False
    else:
        conn.execute(
            "INSERT INTO bookmarked_job (user_id, job_id) VALUES (?,?)", (uid, job_id)
        )
        bookmarked = True

    conn.commit()
    conn.close()
    return jsonify({"bookmarked": bookmarked, "job_id": job_id}), 200


@companies_bp.route("/jobs/bookmarks", methods=["GET"])
@login_required
def get_bookmarks():
    uid  = session["user_id"]
    conn = get_db()
    rows = conn.execute("""
        SELECT j.*, c.name as company_name, c.logo_icon, c.website
        FROM bookmarked_job b
        JOIN job_listing j ON j.job_id=b.job_id
        JOIN company c ON c.company_id=j.company_id
        WHERE b.user_id=?
        ORDER BY b.bookmarked_at DESC
    """, (uid,)).fetchall()
    conn.close()
    result = []
    for j in rows:
        d = dict(j)
        d["skills_list"]   = [s.strip() for s in (j["required_skills"] or "").split(",")]
        d["is_bookmarked"] = True
        result.append(d)
    return jsonify({"bookmarks": result}), 200
