"""
SQLite database models using raw sqlite3 — no ORM dependency required.
All DDL is in init_db(); call once at startup.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'career.db')


def get_db():
    """Return a connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't already exist."""
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS user (
        user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL,
        email       TEXT    NOT NULL UNIQUE,
        password_hash TEXT  NOT NULL,
        age         INTEGER,
        gender      TEXT,
        education_level TEXT,
        highest_qualification TEXT,
        specialization TEXT,
        career_goal TEXT,
        personality_type TEXT DEFAULT 'I',
        created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS user_skill (
        skill_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES user(user_id),
        skill_name      TEXT    NOT NULL,
        proficiency     INTEGER NOT NULL CHECK(proficiency BETWEEN 0 AND 5),
        category        TEXT    NOT NULL DEFAULT 'technical'
    );

    CREATE TABLE IF NOT EXISTS user_interest (
        interest_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES user(user_id),
        domain          TEXT    NOT NULL,
        interest_score  INTEGER NOT NULL CHECK(interest_score BETWEEN 0 AND 10)
    );

    CREATE TABLE IF NOT EXISTS academic_record (
        record_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL REFERENCES user(user_id),
        subject     TEXT    NOT NULL,
        score       REAL    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS career (
        career_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        career_name     TEXT    NOT NULL UNIQUE,
        domain          TEXT    NOT NULL,
        description     TEXT,
        avg_salary_lpa  REAL,
        growth_rate     TEXT,
        work_environment TEXT,
        personality_fit TEXT,   -- comma-separated RIASEC codes  e.g. "R,I"
        interest_domain TEXT    -- primary interest domain tag
    );

    CREATE TABLE IF NOT EXISTS career_skill (
        cs_id           INTEGER PRIMARY KEY AUTOINCREMENT,
        career_id       INTEGER NOT NULL REFERENCES career(career_id),
        skill_name      TEXT    NOT NULL,
        importance      INTEGER NOT NULL CHECK(importance BETWEEN 1 AND 5),
        is_mandatory    INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS recommendation (
        rec_id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id             INTEGER NOT NULL REFERENCES user(user_id),
        career_id           INTEGER NOT NULL REFERENCES career(career_id),
        compatibility_score REAL,
        rank                INTEGER,
        generated_at        DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS learning_resource (
        resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
        career_id   INTEGER REFERENCES career(career_id),
        skill_name  TEXT    NOT NULL,
        title       TEXT    NOT NULL,
        url         TEXT,
        provider    TEXT,
        resource_type TEXT
    );

    CREATE TABLE IF NOT EXISTS resume_data (
        resume_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id          INTEGER NOT NULL REFERENCES user(user_id),
        filename         TEXT,
        raw_text         TEXT,
        parsed_skills    TEXT,
        parsed_education TEXT,
        parsed_experience TEXT,
        parsed_projects  TEXT,
        parsed_certs     TEXT,
        uploaded_at      DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS assessment_result (
        result_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES user(user_id),
        domain          TEXT    NOT NULL,
        score           REAL    NOT NULL,
        total_questions INTEGER NOT NULL,
        correct_answers INTEGER NOT NULL,
        strengths       TEXT,
        weak_areas      TEXT,
        taken_at        DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS company (
        company_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        name           TEXT NOT NULL,
        industry       TEXT,
        location       TEXT,
        size           TEXT,
        description    TEXT,
        website        TEXT,
        logo_icon      TEXT,
        has_internship INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS job_listing (
        job_id          INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id      INTEGER NOT NULL REFERENCES company(company_id),
        title           TEXT NOT NULL,
        domain          TEXT,
        location        TEXT,
        job_type        TEXT DEFAULT 'Full-time',
        salary_min      INTEGER,
        salary_max      INTEGER,
        required_skills TEXT,
        description     TEXT,
        is_internship   INTEGER DEFAULT 0,
        posted_days_ago INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS bookmarked_job (
        bookmark_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id       INTEGER NOT NULL REFERENCES user(user_id),
        job_id        INTEGER NOT NULL REFERENCES job_listing(job_id),
        bookmarked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, job_id)
    );

    CREATE TABLE IF NOT EXISTS user_experience (
        exp_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL REFERENCES user(user_id),
        title       TEXT,
        company     TEXT,
        duration    TEXT,
        description TEXT
    );
    """)

    conn.commit()
    conn.close()
    print("[DB] Tables initialised.")
