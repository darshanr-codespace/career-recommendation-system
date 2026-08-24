"""
modules/skill_gap.py
Computes per-skill gaps between a user's current proficiency and the
requirements of a target career.  Returns structured data ready for
Chart.js radar charts.
"""
from flask import Blueprint, jsonify, session
from modules.auth import login_required
from database.models import get_db

skill_gap_bp = Blueprint("skill_gap", __name__)


# ── pure function (testable without Flask) ───────────────────────────────────

def compute_skill_gaps(user_skills: dict, career_requirements: dict) -> dict:
    """
    Parameters
    ----------
    user_skills          : {skill_name: proficiency_level (0-5)}
    career_requirements  : {skill_name: {"importance": int, "is_mandatory": bool}}

    Returns
    -------
    {
      skill_name: {
        "required"  : int,   # career requirement (1-5)
        "current"   : int,   # user's level (0-5, 0 if not rated)
        "gap"       : int,   # max(0, required - current)
        "status"    : str,   # "strength" | "minor_gap" | "major_gap"
        "mandatory" : bool
      }, ...
    }
    """
    gaps = {}
    for skill, req_info in career_requirements.items():
        required  = req_info.get("importance", 3)
        mandatory = bool(req_info.get("is_mandatory", True))
        current   = user_skills.get(skill, 0)
        gap       = max(0, required - current)

        if gap == 0:
            status = "strength"
        elif gap <= 1:
            status = "minor_gap"
        else:
            status = "major_gap"

        gaps[skill] = {
            "required" : required,
            "current"  : current,
            "gap"      : gap,
            "status"   : status,
            "mandatory": mandatory,
        }
    return gaps


def _build_radar_payload(gaps: dict) -> dict:
    """Convert gap dict to Chart.js-ready radar chart data."""
    skills  = list(gaps.keys())
    current = [gaps[s]["current"]  for s in skills]
    required= [gaps[s]["required"] for s in skills]

    return {
        "labels"  : skills,
        "datasets": [
            {
                "label"          : "Your Level",
                "data"           : current,
                "backgroundColor": "rgba(54, 162, 235, 0.2)",
                "borderColor"    : "rgba(54, 162, 235, 1)",
                "pointBackgroundColor": "rgba(54, 162, 235, 1)",
            },
            {
                "label"          : "Required Level",
                "data"           : required,
                "backgroundColor": "rgba(255, 99, 132, 0.2)",
                "borderColor"    : "rgba(255, 99, 132, 1)",
                "pointBackgroundColor": "rgba(255, 99, 132, 1)",
            },
        ],
    }


# ── routes ───────────────────────────────────────────────────────────────────

@skill_gap_bp.route("/skill-gap/<int:career_id>", methods=["GET"])
@login_required
def skill_gap(career_id: int):
    """
    GET /api/skill-gap/<career_id>
    Returns skill gap analysis + radar chart data + learning resources.
    """
    uid  = session["user_id"]
    conn = get_db()

    # Fetch career
    career = conn.execute(
        "SELECT * FROM career WHERE career_id=?", (career_id,)
    ).fetchone()
    if not career:
        conn.close()
        return jsonify({"error": "Career not found"}), 404

    # Fetch career skill requirements
    req_rows = conn.execute(
        "SELECT skill_name, importance, is_mandatory FROM career_skill WHERE career_id=?",
        (career_id,)
    ).fetchall()
    career_requirements = {
        r["skill_name"]: {"importance": r["importance"], "is_mandatory": r["is_mandatory"]}
        for r in req_rows
    }

    # Fetch user skills
    skill_rows = conn.execute(
        "SELECT skill_name, proficiency FROM user_skill WHERE user_id=?", (uid,)
    ).fetchall()
    user_skills = {r["skill_name"]: r["proficiency"] for r in skill_rows}

    # Compute gaps
    gaps = compute_skill_gaps(user_skills, career_requirements)

    # Fetch learning resources for skills with gaps
    gap_skills = [s for s, g in gaps.items() if g["gap"] > 0]
    resources  = {}
    for skill in gap_skills:
        rows = conn.execute(
            """SELECT title, url, provider, resource_type
               FROM learning_resource
               WHERE career_id=? AND skill_name=?""",
            (career_id, skill)
        ).fetchall()
        if rows:
            resources[skill] = [dict(r) for r in rows]
        else:
            # Generic fallback resource
            resources[skill] = [{
                "title"        : f"Learn {skill}",
                "url"          : f"https://www.coursera.org/search?query={skill.replace(' ','+')}",
                "provider"     : "Coursera",
                "resource_type": "Search",
            }]

    conn.close()

    # Summary stats
    total      = len(gaps)
    strengths  = sum(1 for g in gaps.values() if g["status"] == "strength")
    minor_gaps = sum(1 for g in gaps.values() if g["status"] == "minor_gap")
    major_gaps = sum(1 for g in gaps.values() if g["status"] == "major_gap")
    readiness  = round((strengths / total * 100) if total else 0, 1)

    return jsonify({
        "career": {
            "career_id"  : career["career_id"],
            "career_name": career["career_name"],
            "domain"     : career["domain"],
        },
        "summary": {
            "total_skills" : total,
            "strengths"    : strengths,
            "minor_gaps"   : minor_gaps,
            "major_gaps"   : major_gaps,
            "readiness_pct": readiness,
        },
        "gaps"     : gaps,
        "chart_data": _build_radar_payload(gaps),
        "resources": resources,
    }), 200
