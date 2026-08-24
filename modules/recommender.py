"""
modules/recommender.py
Hybrid Career Recommendation Engine
─────────────────────────────────────
Combines three scoring signals:
  1. Content-Based Filtering  (cosine similarity)        weight = 0.40
  2. Collaborative Filtering  (SVD matrix factorisation) weight = 0.30
  3. Random Forest Classifier (career category proba)    weight = 0.30

Training is triggered automatically if model files are absent.
"""
import os, json
import numpy as np
import pandas as pd
import joblib
from flask import Blueprint, jsonify, session

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse.linalg import svds

from database.models import get_db
from modules.auth import login_required

rec_bp = Blueprint("rec", __name__)

# ── paths ─────────────────────────────────────────────────────────────────────
_BASE     = os.path.dirname(os.path.dirname(__file__))
_MODEL_DIR = os.path.join(_BASE, "models")
os.makedirs(_MODEL_DIR, exist_ok=True)

RF_MODEL_PATH    = os.path.join(_MODEL_DIR, "rf_classifier.pkl")
PREPROC_PATH     = os.path.join(_MODEL_DIR, "preprocessor.pkl")
CAREER_VEC_PATH  = os.path.join(_MODEL_DIR, "career_vectors.pkl")


# ─────────────────────────────────────────────────────────────────────────────
# 1.  DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

NUMERIC_FEATS     = ["math_score","science_score","english_score",
                     "skill_avg","interest_avg"]
CATEGORICAL_FEATS = ["education_level","personality_type"]

ALL_SKILLS    = [
    "Programming","Data Structures","Python","Statistics","Machine Learning",
    "SQL","Networking","Security Tools","HTML/CSS","JavaScript",
    "Biology","Chemistry","Clinical Skills","Empathy","Pharmacology",
    "Mathematics","Physics","CAD Software","Accounting","Taxation",
    "Financial Analysis","Communication","Problem Solving","Creativity",
    "Leadership","Writing","Research","Critical Thinking","Attention to Detail",
    "UI Design","Adobe Suite","Marketing",
]

INTEREST_DOMAINS = [
    "Technology","Healthcare","Engineering","Business","Law",
    "Design","Arts & Media","Science & Research","Education",
]

CAREER_DOMAINS = [
    "Information Technology","Healthcare","Engineering",
    "Finance & Commerce","Business","Law","Design",
    "Media & Communication","Analytics","Research","Education",
]


# ─────────────────────────────────────────────────────────────────────────────
# 2.  PREPROCESSING PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def build_preprocessor() -> ColumnTransformer:
    """Build (unfitted) sklearn ColumnTransformer for user feature vectors."""
    numeric_pipe  = Pipeline([("scaler", StandardScaler())])
    category_pipe = Pipeline([("ohe", OneHotEncoder(handle_unknown="ignore",
                                                     sparse_output=False))])
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe,  NUMERIC_FEATS),
            ("cat", category_pipe, CATEGORICAL_FEATS),
        ],
        remainder="drop"
    )


def _user_to_df(profile: dict) -> pd.DataFrame:
    """
    Convert raw user profile dict to a single-row DataFrame
    with the columns expected by the preprocessor.
    """
    academic = profile.get("academic_records", {})
    row = {
        "math_score"     : academic.get("Mathematics", 50),
        "science_score"  : academic.get("Science",     50),
        "english_score"  : academic.get("English",     50),
        "skill_avg"      : profile.get("skill_avg",     2.5),
        "interest_avg"   : profile.get("interest_avg",  5.0),
        "education_level": profile.get("education_level","Undergraduate"),
        "personality_type": profile.get("personality_type","I"),
    }
    return pd.DataFrame([row])


# ─────────────────────────────────────────────────────────────────────────────
# 3.  SYNTHETIC TRAINING DATA GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def _generate_synthetic_data(n=800) -> pd.DataFrame:
    """
    Generate synthetic training data for the Random Forest classifier.
    Each row is a user-profile → career-category label.
    The domain mapping is intentionally noisy to reflect real-world variation.
    """
    rng = np.random.default_rng(42)

    domain_map = {
        "Information Technology": ("Undergraduate","Postgraduate"),
        "Healthcare":             ("Undergraduate","Postgraduate"),
        "Engineering":            ("Undergraduate","Postgraduate"),
        "Finance & Commerce":     ("Undergraduate","Postgraduate"),
        "Business":               ("Undergraduate","Postgraduate","Professional"),
        "Law":                    ("Postgraduate","Professional"),
        "Design":                 ("Undergraduate","Postgraduate"),
        "Education":              ("Postgraduate","Professional"),
        "Research":               ("Postgraduate","Professional"),
        "Analytics":              ("Undergraduate","Postgraduate"),
        "Media & Communication":  ("Undergraduate","Postgraduate"),
    }

    rows = []
    for domain, edu_options in domain_map.items():
        n_per = n // len(domain_map)
        for _ in range(n_per):
            edu  = rng.choice(edu_options)
            pers = rng.choice(list("RIASEC"))
            math = float(rng.integers(30, 100))
            sci  = float(rng.integers(30, 100))
            eng  = float(rng.integers(30, 100))
            # Bias scores toward domain
            if domain in ("Information Technology","Engineering","Analytics"):
                math = float(rng.integers(55, 100))
                sci  = float(rng.integers(50, 100))
            elif domain in ("Healthcare","Research"):
                sci  = float(rng.integers(60, 100))
            rows.append({
                "math_score"     : math,
                "science_score"  : sci,
                "english_score"  : eng,
                "skill_avg"      : rng.uniform(1.0, 5.0),
                "interest_avg"   : rng.uniform(3.0, 9.0),
                "education_level": edu,
                "personality_type": pers,
                "domain_label"   : domain,
            })

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# 4.  CAREER FEATURE MATRIX  (for content-based filtering)
# ─────────────────────────────────────────────────────────────────────────────

def _build_career_matrix(careers: list, career_skills_map: dict) -> tuple:
    """
    Build a matrix where each row represents a career as a feature vector.
    Dimensions:
      - RIASEC one-hot (6)
      - interest domain one-hot (9)
      - avg_salary normalised (1)
      - top-skill average importance (1)
      ──────────────────────────────
      Total: 17 features per career
    """
    riasec_codes  = list("RIASEC")
    rows, ids     = [], []

    for c in careers:
        row = []

        # RIASEC fit one-hot
        fit_codes = [x.strip() for x in (c.get("personality_fit") or "").split(",")]
        row += [1 if code in fit_codes else 0 for code in riasec_codes]

        # Interest domain one-hot
        idomain = c.get("interest_domain", "")
        row += [1 if d == idomain else 0 for d in INTEREST_DOMAINS]

        # Normalised salary (0-1, max assumed ₹25 LPA for normalisation)
        row.append(min(1.0, (c.get("avg_salary_lpa") or 10) / 25.0))

        # Average skill importance for this career
        skills = career_skills_map.get(c["career_id"], [])
        avg_imp = np.mean([s["importance"] for s in skills]) if skills else 3.0
        row.append(avg_imp / 5.0)

        rows.append(row)
        ids.append(c["career_id"])

    return np.array(rows, dtype=float), ids


def _user_to_career_space(profile: dict, riasec_codes=list("RIASEC")) -> np.ndarray:
    """
    Encode user profile into the same 17-dim career feature space
    so cosine similarity is meaningful.
    """
    row = []

    # RIASEC
    user_pers = profile.get("personality_type", "I")
    row += [1 if code == user_pers else 0 for code in riasec_codes]

    # Interest domain
    interests      = profile.get("interests", {})
    top_domain     = max(interests, key=interests.get) if interests else ""
    row += [1 if d == top_domain else 0 for d in INTEREST_DOMAINS]

    # Normalised expected salary preference (neutral = 0.5)
    row.append(0.5)

    # Normalised average skill
    row.append(profile.get("skill_avg", 2.5) / 5.0)

    return np.array([row], dtype=float)


# ─────────────────────────────────────────────────────────────────────────────
# 5.  COLLABORATIVE FILTERING  (SVD)
# ─────────────────────────────────────────────────────────────────────────────

def _compute_cf_scores(user_id: int, career_ids: list, conn) -> dict:
    """
    Build user-career interaction matrix from saved recommendations
    and compute predicted scores via truncated SVD.
    Returns {career_id: cf_score} (0-1 normalised).
    """
    # Fetch interaction data
    rows = conn.execute("""
        SELECT user_id, career_id, compatibility_score
        FROM recommendation
    """).fetchall()

    if len(rows) < 5:
        # Not enough history yet — return uniform scores
        return {cid: 0.5 for cid in career_ids}

    df = pd.DataFrame(rows, columns=["user_id","career_id","score"])
    pivot = df.pivot_table(index="user_id", columns="career_id",
                           values="score", aggfunc="mean", fill_value=0)

    # Ensure current user row exists
    if user_id not in pivot.index:
        pivot.loc[user_id] = 0

    # SVD factorisation
    k = min(min(pivot.shape) - 1, 5)
    if k < 1:
        return {cid: 0.5 for cid in career_ids}

    U, sigma, Vt = svds(pivot.values.astype(float), k=k)
    predicted = np.dot(np.dot(U, np.diag(sigma)), Vt)

    user_idx = list(pivot.index).index(user_id)
    pred_row = predicted[user_idx]

    # Normalise to [0,1]
    mn, mx = pred_row.min(), pred_row.max()
    if mx > mn:
        pred_row = (pred_row - mn) / (mx - mn)
    else:
        pred_row = np.ones_like(pred_row) * 0.5

    cf_scores = {}
    for cid in career_ids:
        if cid in pivot.columns:
            col_idx = list(pivot.columns).index(cid)
            cf_scores[cid] = float(pred_row[col_idx])
        else:
            cf_scores[cid] = 0.5
    return cf_scores


# ─────────────────────────────────────────────────────────────────────────────
# 6.  SCORE FUSION
# ─────────────────────────────────────────────────────────────────────────────

def fuse_scores(
    cb_scores : np.ndarray,
    cf_scores : np.ndarray,
    rf_probs  : np.ndarray,
    career_ids: list,
    w_cb: float = 0.40,
    w_cf: float = 0.30,
    w_rf: float = 0.30,
    top_k: int  = 10,
) -> list:
    """
    Parameters
    ----------
    cb_scores  : 1-D array, content-based cosine similarity per career (0-1)
    cf_scores  : 1-D array, collaborative filtering score per career (0-1)
    rf_probs   : 1-D array, RF probability per career (0-1)
    career_ids : list of career IDs matching array positions
    w_cb, w_cf, w_rf : weights (must sum to 1.0)
    top_k      : number of top careers to return

    Returns
    -------
    List of (career_id, final_score) tuples sorted desc, length = top_k
    """
    assert abs(w_cb + w_cf + w_rf - 1.0) < 1e-6, "Weights must sum to 1.0"

    final = w_cb * cb_scores + w_cf * cf_scores + w_rf * rf_probs
    ranked_idx = np.argsort(final)[::-1][:top_k]
    return [(career_ids[i], float(final[i])) for i in ranked_idx]


# ─────────────────────────────────────────────────────────────────────────────
# 7.  MODEL TRAINING & LOADING
# ─────────────────────────────────────────────────────────────────────────────

def train_and_save_models():
    """
    Train preprocessor + Random Forest on synthetic data.
    Saves both artefacts to disk.
    """
    print("[ML] Generating synthetic training data …")
    df = _generate_synthetic_data(n=1200)

    X = df[NUMERIC_FEATS + CATEGORICAL_FEATS]
    y = df["domain_label"]

    preproc = build_preprocessor()
    X_transformed = preproc.fit_transform(X)

    rf = RandomForestClassifier(
        n_estimators=200, max_depth=20,
        min_samples_split=5, random_state=42, n_jobs=-1
    )
    rf.fit(X_transformed, y)

    scores = cross_val_score(rf, X_transformed, y, cv=5, scoring="accuracy")
    print(f"[ML] RF cross-val accuracy: {scores.mean():.3f} ± {scores.std():.3f}")

    joblib.dump(preproc, PREPROC_PATH)
    joblib.dump(rf,      RF_MODEL_PATH)
    print(f"[ML] Models saved to {_MODEL_DIR}")


def _load_models():
    if not (os.path.exists(RF_MODEL_PATH) and os.path.exists(PREPROC_PATH)):
        train_and_save_models()
    preproc = joblib.load(PREPROC_PATH)
    rf      = joblib.load(RF_MODEL_PATH)
    return preproc, rf


def _load_career_vectors(conn):
    """
    Load (or rebuild) career feature matrix from DB.
    Cached on disk; invalidated if career count changes.
    """
    careers = [dict(r) for r in conn.execute(
        "SELECT * FROM career"
    ).fetchall()]

    career_ids = [c["career_id"] for c in careers]

    career_skills_map = {}
    for cid in career_ids:
        rows = conn.execute(
            "SELECT skill_name, importance FROM career_skill WHERE career_id=?", (cid,)
        ).fetchall()
        career_skills_map[cid] = [dict(r) for r in rows]

    matrix, ids = _build_career_matrix(careers, career_skills_map)
    return matrix, ids, careers


# ─────────────────────────────────────────────────────────────────────────────
# 8.  PROFILE LOADER
# ─────────────────────────────────────────────────────────────────────────────

def _load_user_profile(uid: int, conn) -> dict:
    """Assemble full user profile dict from DB."""
    user     = dict(conn.execute("SELECT * FROM user WHERE user_id=?", (uid,)).fetchone() or {})
    skills   = conn.execute("SELECT skill_name, proficiency FROM user_skill WHERE user_id=?", (uid,)).fetchall()
    interests= conn.execute("SELECT domain, interest_score FROM user_interest WHERE user_id=?", (uid,)).fetchall()
    acad     = conn.execute("SELECT subject, score FROM academic_record WHERE user_id=?", (uid,)).fetchall()

    skill_dict    = {r["skill_name"]: r["proficiency"] for r in skills}
    interest_dict = {r["domain"]: r["interest_score"]  for r in interests}
    acad_dict     = {r["subject"]: r["score"]          for r in acad}

    skill_avg    = float(np.mean(list(skill_dict.values()))) if skill_dict    else 2.5
    interest_avg = float(np.mean(list(interest_dict.values()))) if interest_dict else 5.0

    return {
        "user_id"         : uid,
        "education_level" : user.get("education_level", "Undergraduate") or "Undergraduate",
        "personality_type": user.get("personality_type", "I") or "I",
        "academic_records": acad_dict,
        "skills"          : skill_dict,
        "interests"       : interest_dict,
        "skill_avg"       : skill_avg,
        "interest_avg"    : interest_avg,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 9.  MAIN RECOMMENDATION FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def run_recommendation(uid: int) -> list:
    """
    Full hybrid recommendation pipeline.
    Returns list of dicts (top-10), each with career info + scores.
    """
    conn    = get_db()
    profile = _load_user_profile(uid, conn)

    # --- Load models ---
    preproc, rf = _load_models()

    # --- Content-Based Filtering ---
    career_matrix, career_ids, careers = _load_career_vectors(conn)
    user_career_vec = _user_to_career_space(profile)
    cb_scores       = cosine_similarity(user_career_vec, career_matrix)[0]

    # Normalise CB scores to [0,1]
    cb_mn, cb_mx = cb_scores.min(), cb_scores.max()
    if cb_mx > cb_mn:
        cb_scores = (cb_scores - cb_mn) / (cb_mx - cb_mn)
    else:
        cb_scores = np.ones_like(cb_scores) * 0.5

    # --- Collaborative Filtering ---
    cf_dict  = _compute_cf_scores(uid, career_ids, conn)
    cf_scores= np.array([cf_dict.get(cid, 0.5) for cid in career_ids])

    # --- Random Forest ---
    user_df      = _user_to_df(profile)
    user_trans   = preproc.transform(user_df)
    domain_probs = rf.predict_proba(user_trans)[0]     # proba per domain class

    # Map domain probabilities back to individual careers
    classes   = list(rf.classes_)
    career_objects = {c["career_id"]: c for c in careers}
    rf_scores = np.array([
        domain_probs[classes.index(career_objects[cid]["domain"])]
        if career_objects[cid]["domain"] in classes else 0.3
        for cid in career_ids
    ])

    # --- Fuse ---
    ranked = fuse_scores(cb_scores, cf_scores, rf_scores, career_ids)

    # --- Persist top-10 ---
    conn.execute("DELETE FROM recommendation WHERE user_id=?", (uid,))
    results = []
    for rank, (cid, score) in enumerate(ranked, start=1):
        conn.execute(
            """INSERT INTO recommendation
               (user_id, career_id, compatibility_score, rank)
               VALUES (?,?,?,?)""",
            (uid, cid, round(score, 4), rank)
        )
        c = career_objects[cid]
        results.append({
            "rank"              : rank,
            "career_id"         : cid,
            "career_name"       : c["career_name"],
            "domain"            : c["domain"],
            "description"       : c["description"],
            "avg_salary_lpa"    : c["avg_salary_lpa"],
            "growth_rate"       : c["growth_rate"],
            "work_environment"  : c["work_environment"],
            "compatibility_score": round(score * 100, 1),   # as %
            "scores": {
                "content_based"  : round(float(cb_scores[career_ids.index(cid)]) * 100, 1),
                "collaborative"  : round(float(cf_scores[career_ids.index(cid)]) * 100, 1),
                "random_forest"  : round(float(rf_scores[career_ids.index(cid)]) * 100, 1),
            }
        })

    conn.commit()
    conn.close()
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 10.  FLASK ROUTE
# ─────────────────────────────────────────────────────────────────────────────

@rec_bp.route("/recommend", methods=["GET"])
@login_required
def recommend():
    """GET /api/recommend — run the full hybrid engine for the logged-in user."""
    uid  = session["user_id"]
    conn = get_db()

    # ── Profile completeness gate ─────────────────────────────────────────────
    user = conn.execute("SELECT * FROM user WHERE user_id=?", (uid,)).fetchone()
    interest_count = conn.execute(
        "SELECT COUNT(*) FROM user_interest WHERE user_id=?", (uid,)
    ).fetchone()[0]
    conn.close()

    has_education = bool(user["education_level"] or user["highest_qualification"])
    has_interests = interest_count > 0
    has_goal      = bool(user["career_goal"])

    missing = []
    if not has_education: missing.append("Highest Qualification / Education Level")
    if not has_interests: missing.append("Career Interests")
    if not has_goal:      missing.append("Career Goal")

    if missing:
        return jsonify({
            "error":            "incomplete_profile",
            "message":          "Not enough data to predict. Please complete your profile to get personalised career recommendations.",
            "missing_fields":   missing,
            "redirect":         "/profile",
        }), 422

    # ── Run recommendation engine ─────────────────────────────────────────────
    try:
        results = run_recommendation(uid)
        return jsonify({
            "user_id"        : uid,
            "total_careers"  : len(results),
            "recommendations": results,
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@rec_bp.route("/career-path/<int:career_id>", methods=["GET"])
@login_required
def career_path(career_id: int):
    """GET /api/career-path/<career_id> — return staged career progression."""
    conn   = get_db()
    career = conn.execute(
        "SELECT * FROM career WHERE career_id=?", (career_id,)
    ).fetchone()
    conn.close()

    if not career:
        return jsonify({"error": "Career not found"}), 404

    c = dict(career)
    name = c["career_name"]

    # Static progression data keyed by career domain
    progressions = _get_career_progression(name, c["domain"])

    return jsonify({
        "career"     : c,
        "progression": progressions,
    }), 200


def _get_career_progression(name: str, domain: str) -> list:
    """Return a list of career stage dicts for a given career."""
    generic = [
        {
            "stage"       : 1,
            "title"       : f"Junior {name}",
            "experience"  : "0-2 years",
            "education"   : "Bachelor's degree",
            "salary_range": "₹3-6 LPA",
            "key_skills"  : ["Domain Fundamentals","Communication","Teamwork"],
            "certifications": ["Relevant entry-level certification"],
        },
        {
            "stage"       : 2,
            "title"       : name,
            "experience"  : "2-5 years",
            "education"   : "Bachelor's + specialisation",
            "salary_range": "₹6-12 LPA",
            "key_skills"  : ["Advanced Domain Skills","Project Management","Leadership"],
            "certifications": ["Professional certification"],
        },
        {
            "stage"       : 3,
            "title"       : f"Senior {name}",
            "experience"  : "5-10 years",
            "education"   : "Master's preferred",
            "salary_range": "₹12-20 LPA",
            "key_skills"  : ["Strategic Thinking","Mentoring","Technical Leadership"],
            "certifications": ["Advanced certification"],
        },
        {
            "stage"       : 4,
            "title"       : f"Principal / Lead {name}",
            "experience"  : "10+ years",
            "education"   : "Master's / MBA",
            "salary_range": "₹20+ LPA",
            "key_skills"  : ["Visionary Leadership","Stakeholder Management","Business Strategy"],
            "certifications": ["Executive / domain leadership certification"],
        },
    ]

    # Domain-specific overrides
    overrides = {
        "Information Technology": [
            {"stage":1,"title":f"Junior {name}","experience":"0-2 yrs","education":"B.Tech/BCA","salary_range":"₹4-8 LPA","key_skills":["Core Language","Git","Agile Basics"],"certifications":["AWS Cloud Practitioner","Google IT Support"]},
            {"stage":2,"title":name,"experience":"2-5 yrs","education":"B.Tech/M.Tech","salary_range":"₹8-18 LPA","key_skills":["System Design","Cloud","CI/CD"],"certifications":["AWS Solutions Architect","Azure Administrator"]},
            {"stage":3,"title":f"Senior {name}","experience":"5-10 yrs","education":"M.Tech/MBA optional","salary_range":"₹18-35 LPA","key_skills":["Architecture","Team Leadership","Mentoring"],"certifications":["TOGAF","PMP"]},
            {"stage":4,"title":"Principal Engineer / Engineering Manager","experience":"10+ yrs","education":"M.Tech/MBA","salary_range":"₹35+ LPA","key_skills":["Org Strategy","Cross-Team Collaboration","P&L Ownership"],"certifications":["CISO / CTO track"]},
        ],
        "Healthcare": [
            {"stage":1,"title":"Intern / Junior Clinician","experience":"0-2 yrs (internship)","education":"MBBS / B.Pharm / B.Sc Nursing","salary_range":"₹3-7 LPA","key_skills":["Clinical Examination","Patient Communication","EMR"],"certifications":["BLS","ACLS"]},
            {"stage":2,"title":"Resident / Junior Doctor","experience":"2-5 yrs","education":"MD / MS","salary_range":"₹7-15 LPA","key_skills":["Specialisation","Diagnosis","Research"],"certifications":["Board Certification in Specialty"]},
            {"stage":3,"title":"Consultant / Attending Physician","experience":"5-10 yrs","education":"DM / MCh (super-speciality)","salary_range":"₹15-35 LPA","key_skills":["Complex Case Management","Teaching","Research"],"certifications":["Fellowship"]},
            {"stage":4,"title":"Department Head / Senior Consultant","experience":"10+ yrs","education":"Senior Fellowship / MBA Healthcare","salary_range":"₹35+ LPA","key_skills":["Hospital Management","Policy","Research Leadership"],"certifications":["FAMS / FRCS"]},
        ],
    }

    return overrides.get(domain, generic)
