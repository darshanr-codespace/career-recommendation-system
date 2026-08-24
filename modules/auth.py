"""
modules/auth.py
User registration, login, and session management.
Password hashing uses hashlib + PBKDF2-HMAC (built-in, no extra deps).
"""
import hashlib, os, functools
from flask import Blueprint, request, jsonify, session, g
from database.models import get_db

auth_bp = Blueprint("auth", __name__)

# ── helpers ──────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """Return PBKDF2-HMAC-SHA256 hash as hex string with embedded salt."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260_000)
    return salt.hex() + ":" + dk.hex()


def _verify_password(password: str, stored: str) -> bool:
    """Verify a password against a stored hash created by _hash_password."""
    try:
        salt_hex, dk_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260_000)
        return dk.hex() == dk_hex
    except Exception:
        return False


def login_required(f):
    """Decorator — returns 401 if no active session."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    """Return the logged-in user row, or None."""
    uid = session.get("user_id")
    if uid is None:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM user WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return user


# ── routes ───────────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    POST /auth/register
    Body: { name, email, password, age?, gender?, education_level? }
    """
    data = request.get_json(force=True)
    required = ("name", "email", "password")
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    name      = data["name"].strip()
    email     = data["email"].strip().lower()
    password  = data["password"]
    age       = data.get("age")
    gender    = data.get("gender", "")
    edu       = data.get("education_level", "")
    h_qual    = data.get("highest_qualification", "")
    speciali  = data.get("specialization", "")
    c_goal    = data.get("career_goal", "")

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    pw_hash = _hash_password(password)

    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO user (name, email, password_hash, age, gender, education_level,
                                 highest_qualification, specialization, career_goal)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (name, email, pw_hash, age, gender, edu, h_qual, speciali, c_goal)
        )
        conn.commit()
        uid = conn.execute(
            "SELECT user_id FROM user WHERE email=?", (email,)
        ).fetchone()["user_id"]
    except Exception as e:
        conn.close()
        if "UNIQUE" in str(e):
            return jsonify({"error": "Email already registered"}), 409
        return jsonify({"error": str(e)}), 500

    conn.close()
    session["user_id"] = uid
    return jsonify({"message": "Registration successful", "user_id": uid,
                    "redirect": "/profile?new=1"}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /auth/login
    Body: { email, password }
    """
    data  = request.get_json(force=True)
    email = data.get("email", "").strip().lower()
    pwd   = data.get("password", "")

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM user WHERE email=?", (email,)
    ).fetchone()
    conn.close()

    if not user or not _verify_password(pwd, user["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = user["user_id"]
    return jsonify({
        "message": "Login successful",
        "user": {
            "user_id":        user["user_id"],
            "name":           user["name"],
            "education_level": user["education_level"],
        }
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "user_id":               user["user_id"],
        "name":                  user["name"],
        "email":                 user["email"],
        "age":                   user["age"],
        "gender":                user["gender"],
        "education_level":       user["education_level"],
        "highest_qualification": user["highest_qualification"],
        "specialization":        user["specialization"],
        "career_goal":           user["career_goal"],
    })


@auth_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    """
    POST /auth/profile/update
    Body: {
        education_level?, age?, gender?,
        academic_records: [{subject, score}, ...],
        skills:           [{skill_name, proficiency, category}, ...],
        interests:        [{domain, interest_score}, ...],
        personality_type: "R" | "I" | "A" | "S" | "E" | "C"
    }
    """
    data = request.get_json(force=True)
    uid  = session["user_id"]
    conn = get_db()

    # Update basic fields
    fields = {}
    for f in ("education_level", "age", "gender",
                "highest_qualification", "specialization", "career_goal"):
        if data.get(f) is not None:
            fields[f] = data[f]

    if data.get("personality_type"):
        fields["personality_type"] = data["personality_type"]

    if fields:
        sets = ", ".join(f"{k}=?" for k in fields)
        conn.execute(
            f"UPDATE user SET {sets} WHERE user_id=?",
            list(fields.values()) + [uid]
        )

    # Replace skills
    if "skills" in data:
        conn.execute("DELETE FROM user_skill WHERE user_id=?", (uid,))
        for s in data["skills"]:
            conn.execute(
                "INSERT INTO user_skill (user_id,skill_name,proficiency,category) VALUES(?,?,?,?)",
                (uid, s["skill_name"], s["proficiency"], s.get("category","technical"))
            )

    # Replace interests
    if "interests" in data:
        conn.execute("DELETE FROM user_interest WHERE user_id=?", (uid,))
        for i in data["interests"]:
            conn.execute(
                "INSERT INTO user_interest (user_id,domain,interest_score) VALUES(?,?,?)",
                (uid, i["domain"], i["interest_score"])
            )

    # Update name
    if data.get("name"):
        conn.execute("UPDATE user SET name=? WHERE user_id=?", (data["name"].strip(), uid))

    # Replace academic records (accepts dict {subject: score} or list [{subject, score}])
    if "academic_records" in data:
        conn.execute("DELETE FROM academic_record WHERE user_id=?", (uid,))
        acad = data["academic_records"]
        if isinstance(acad, dict):
            acad = [{"subject": k, "score": v} for k, v in acad.items()]
        for r in acad:
            conn.execute(
                "INSERT INTO academic_record (user_id,subject,score) VALUES(?,?,?)",
                (uid, r["subject"], r["score"])
            )

    # Replace experiences
    if "experiences" in data:
        conn.execute("DELETE FROM user_experience WHERE user_id=?", (uid,))
        for e in data["experiences"]:
            conn.execute(
                "INSERT INTO user_experience (user_id,title,company,duration) VALUES(?,?,?,?)",
                (uid, e.get("title",""), e.get("company",""), e.get("duration",""))
            )

    conn.commit()
    conn.close()
    return jsonify({"message": "Profile updated"}), 200



@auth_bp.route("/profile/completeness", methods=["GET"])
@login_required
def profile_completeness():
    """
    GET /auth/profile/completeness
    Returns which required fields are filled and an overall is_complete flag.
    Required for recommendations: education_level OR highest_qualification,
    at least one interest, career_goal.
    """
    uid  = session["user_id"]
    conn = get_db()
    user = conn.execute("SELECT * FROM user WHERE user_id=?", (uid,)).fetchone()
    interest_count = conn.execute(
        "SELECT COUNT(*) FROM user_interest WHERE user_id=?", (uid,)
    ).fetchone()[0]
    conn.close()

    has_education  = bool(user["education_level"] or user["highest_qualification"])
    has_interests  = interest_count > 0
    has_goal       = bool(user["career_goal"])

    missing = []
    if not has_education:  missing.append("highest_qualification")
    if not has_interests:  missing.append("interests")
    if not has_goal:       missing.append("career_goal")

    return jsonify({
        "is_complete":     len(missing) == 0,
        "missing":         missing,
        "has_education":   has_education,
        "has_interests":   has_interests,
        "has_career_goal": has_goal,
        "specialization":  user["specialization"] or "",
    }), 200


@auth_bp.route("/profile/skills", methods=["GET"])
@login_required
def get_skills():
    uid  = session["user_id"]
    conn = get_db()
    rows = conn.execute(
        "SELECT skill_name, proficiency, category FROM user_skill WHERE user_id=?", (uid,)
    ).fetchall()
    conn.close()
    return jsonify({"skills": [dict(r) for r in rows]}), 200


@auth_bp.route("/profile/interests", methods=["GET"])
@login_required
def get_interests():
    uid  = session["user_id"]
    conn = get_db()
    rows = conn.execute(
        "SELECT domain, interest_score FROM user_interest WHERE user_id=?", (uid,)
    ).fetchall()
    conn.close()
    return jsonify({"interests": [dict(r) for r in rows]}), 200
