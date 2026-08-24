"""
modules/resume_parser.py
Parses PDF and DOCX resumes to extract skills, education, experience etc.
Uses only built-in + already installed packages (no extra deps needed).
"""
import re, json, os
from flask import Blueprint, request, jsonify, session
from modules.auth import login_required
from database.models import get_db

resume_bp = Blueprint("resume", __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Skill taxonomy for matching ───────────────────────────────────────────────
SKILL_KEYWORDS = [
    "Python","Java","JavaScript","TypeScript","C++","C#","Go","Rust","Swift","Kotlin",
    "React","Angular","Vue","Node.js","Django","Flask","Spring Boot","FastAPI",
    "HTML","CSS","Bootstrap","Tailwind","jQuery","Next.js","Express",
    "SQL","MySQL","PostgreSQL","MongoDB","Redis","SQLite","Oracle","Cassandra",
    "AWS","Azure","GCP","Docker","Kubernetes","Terraform","Jenkins","CI/CD","DevOps",
    "Machine Learning","Deep Learning","NLP","Computer Vision","TensorFlow","PyTorch",
    "Scikit-learn","Pandas","NumPy","Matplotlib","Tableau","Power BI","Excel",
    "Data Science","Data Analysis","Statistics","R","MATLAB","Spark","Hadoop",
    "Cybersecurity","Penetration Testing","Ethical Hacking","Network Security","SIEM",
    "Figma","Adobe XD","Sketch","UI/UX","Prototyping","User Research","Wireframing",
    "Git","GitHub","Linux","Agile","Scrum","JIRA","REST API","GraphQL","Microservices",
    "Communication","Leadership","Teamwork","Problem Solving","Critical Thinking",
    "Project Management","Time Management","Attention to Detail","Creativity",
    "AutoCAD","SolidWorks","MATLAB","VLSI","Embedded C","Arduino","Raspberry Pi",
    "Accounting","Taxation","Financial Analysis","Valuation","Bloomberg",
    "Marketing","SEO","Content Writing","Social Media","Google Analytics",
    "Legal Research","Contract Drafting","Negotiation","Compliance",
]

EDUCATION_KEYWORDS = [
    "B.Tech","B.E","M.Tech","M.E","BCA","MCA","B.Sc","M.Sc","MBA","PhD","B.Com",
    "Bachelor","Master","Doctorate","Engineering","Computer Science","Information Technology",
    "Electronics","Mechanical","Civil","Electrical","Data Science","Mathematics",
    "Physics","Chemistry","Biology","Commerce","Arts","Law","LLB","MBBS","BDS",
]

CERT_KEYWORDS = [
    "AWS Certified","Azure Certified","Google Cloud","CPA","CA","CFA","PMP","CISSP",
    "CEH","CompTIA","Coursera","Udemy","edX","NPTEL","certification","certified",
    "certificate","credential","credential","diploma",
]


def _extract_text_from_pdf(filepath: str) -> str:
    """Extract text from PDF using reportlab reader or fallback byte scan."""
    try:
        # Try using PyMuPDF-style extraction via reportlab
        import reportlab
        # Fallback: read raw bytes and extract printable ASCII
        with open(filepath, "rb") as f:
            raw = f.read()
        # Extract text between BT and ET markers (basic PDF text extraction)
        texts = re.findall(rb'\(([^\)]{1,200})\)', raw)
        result = " ".join(
            t.decode("latin-1", errors="ignore") for t in texts
            if len(t) > 2 and not any(c < 32 for c in t[:5])
        )
        return result if len(result) > 50 else _fallback_text(raw)
    except Exception:
        return ""


def _fallback_text(raw: bytes) -> str:
    """Fallback: extract printable ASCII runs from raw bytes."""
    printable = re.findall(b'[ -~]{4,}', raw)
    return " ".join(p.decode("ascii", errors="ignore") for p in printable)


def _extract_text_from_docx(filepath: str) -> str:
    """Extract text from DOCX by reading XML inside the zip."""
    try:
        import zipfile
        with zipfile.ZipFile(filepath) as z:
            if "word/document.xml" in z.namelist():
                xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
                # Strip XML tags
                text = re.sub(r'<[^>]+>', ' ', xml)
                text = re.sub(r'\s+', ' ', text)
                return text
    except Exception:
        pass
    return ""


def _extract_text(filepath: str, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        return _extract_text_from_pdf(filepath)
    elif ext in (".docx", ".doc"):
        return _extract_text_from_docx(filepath)
    return ""


def _parse_skills(text: str) -> list:
    found = []
    text_lower = text.lower()
    for skill in SKILL_KEYWORDS:
        if skill.lower() in text_lower:
            found.append(skill)
    return list(dict.fromkeys(found))  # preserve order, dedupe


def _parse_education(text: str) -> list:
    found = []
    for keyword in EDUCATION_KEYWORDS:
        pattern = rf'\b{re.escape(keyword)}\b'
        if re.search(pattern, text, re.IGNORECASE):
            # Extract surrounding context (up to 80 chars)
            match = re.search(rf'.{{0,40}}{re.escape(keyword)}.{{0,40}}', text, re.IGNORECASE)
            if match:
                snippet = match.group(0).strip()
                if snippet not in found:
                    found.append(snippet)
    return found[:6]


def _parse_experience(text: str) -> list:
    """Extract job title + company patterns like 'Software Engineer at Google'."""
    patterns = [
        r'([\w\s]+(?:Engineer|Developer|Analyst|Manager|Designer|Consultant|Intern|Lead|Architect))\s+(?:at|@|,)\s+([\w\s&]+)',
        r'([\w\s]+(?:Engineer|Developer|Analyst|Manager|Designer))\s*[|\-–]\s*([\w\s&]+)',
    ]
    results = []
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            entry = f"{m.group(1).strip()} at {m.group(2).strip()}"
            if len(entry) < 80 and entry not in results:
                results.append(entry)
    return results[:5]


def _parse_projects(text: str) -> list:
    """Extract project names after 'Project:' or bullet lines with 'Built'/'Developed'."""
    results = []
    for m in re.finditer(r'(?:Project|Built|Developed|Created)\s*[:\-–]?\s*([A-Z][^\n\.]{10,80})', text):
        p = m.group(1).strip()
        if p not in results:
            results.append(p)
    return results[:5]


def _parse_certs(text: str) -> list:
    results = []
    for kw in CERT_KEYWORDS:
        for m in re.finditer(rf'.{{0,20}}{re.escape(kw)}.{{0,40}}', text, re.IGNORECASE):
            c = m.group(0).strip()
            if c not in results:
                results.append(c)
    return results[:8]


def parse_resume(filepath: str, filename: str) -> dict:
    """Full parse pipeline. Returns structured dict."""
    text = _extract_text(filepath, filename)
    if not text or len(text) < 30:
        # If we can't extract real text, return empty parsed data
        return {
            "raw_text": "",
            "skills": [],
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "error": "Could not extract text from file. Please fill profile manually."
        }

    return {
        "raw_text":       text[:5000],
        "skills":         _parse_skills(text),
        "education":      _parse_education(text),
        "experience":     _parse_experience(text),
        "projects":       _parse_projects(text),
        "certifications": _parse_certs(text),
    }


# ── Flask routes ──────────────────────────────────────────────────────────────

@resume_bp.route("/resume/upload", methods=["POST"])
@login_required
def upload_resume():
    """
    POST /api/resume/upload
    Accepts multipart/form-data with file field 'resume'.
    Returns parsed profile data.
    """
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["resume"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".pdf", ".docx", ".doc"):
        return jsonify({"error": "Only PDF and DOCX files are supported"}), 400

    uid      = session["user_id"]
    safe_name = f"resume_{uid}{ext}"
    filepath  = os.path.join(UPLOAD_FOLDER, safe_name)
    file.save(filepath)

    parsed = parse_resume(filepath, file.filename)

    # Save to DB
    conn = get_db()
    conn.execute("DELETE FROM resume_data WHERE user_id=?", (uid,))
    conn.execute("""
        INSERT INTO resume_data
        (user_id, filename, raw_text, parsed_skills, parsed_education,
         parsed_experience, parsed_projects, parsed_certs)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        uid, file.filename, parsed.get("raw_text",""),
        json.dumps(parsed.get("skills",[])),
        json.dumps(parsed.get("education",[])),
        json.dumps(parsed.get("experience",[])),
        json.dumps(parsed.get("projects",[])),
        json.dumps(parsed.get("certifications",[])),
    ))
    conn.commit()

    # Auto-populate user_skill table from parsed skills
    if parsed.get("skills"):
        conn.execute("DELETE FROM user_skill WHERE user_id=?", (uid,))
        for skill in parsed["skills"]:
            conn.execute(
                "INSERT INTO user_skill (user_id,skill_name,proficiency,category) VALUES(?,?,?,?)",
                (uid, skill, 3, "technical")
            )
        conn.commit()

    conn.close()

    return jsonify({
        "message": "Resume parsed successfully",
        "parsed":  parsed,
    }), 200


@resume_bp.route("/resume/data", methods=["GET"])
@login_required
def get_resume_data():
    """GET /api/resume/data — return last parsed resume for current user."""
    uid  = session["user_id"]
    conn = get_db()
    row  = conn.execute(
        "SELECT * FROM resume_data WHERE user_id=? ORDER BY uploaded_at DESC LIMIT 1", (uid,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"data": None}), 200
    return jsonify({"data": {
        "filename":    row["filename"],
        "skills":      json.loads(row["parsed_skills"] or "[]"),
        "education":   json.loads(row["parsed_education"] or "[]"),
        "experience":  json.loads(row["parsed_experience"] or "[]"),
        "projects":    json.loads(row["parsed_projects"] or "[]"),
        "certs":       json.loads(row["parsed_certs"] or "[]"),
        "uploaded_at": row["uploaded_at"],
    }}), 200
