import sqlite3
import json
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "talent_matcher.db")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Candidates Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        linkedin_url TEXT,
        current_summary TEXT
    )
    """)
    
    # Resume Versions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resume_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER,
        version_name TEXT,
        resume_json TEXT, -- JSON representation of structured resume
        region TEXT DEFAULT 'Global', -- US, India, Europe, Middle East, Remote, Global
        created_at TEXT,
        FOREIGN KEY (candidate_id) REFERENCES candidates (id)
    )
    """)
    
    # Job Postings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_postings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT UNIQUE,
        title TEXT,
        company TEXT,
        location TEXT,
        url TEXT,
        description TEXT,
        source TEXT,
        created_at TEXT
    )
    """)
    
    # Match Results Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS match_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_version_id INTEGER,
        job_posting_id INTEGER,
        match_score INTEGER,
        matched_skills TEXT, -- Comma-separated or JSON
        missing_skills TEXT, -- Comma-separated or JSON
        missing_keywords TEXT, -- Comma-separated or JSON
        roi_metadata TEXT, -- JSON containing salary range, interview probability, hiring chances, searchability score
        created_at TEXT,
        FOREIGN KEY (resume_version_id) REFERENCES resume_versions (id),
        FOREIGN KEY (job_posting_id) REFERENCES job_postings (id)
    )
    """)
    
    # Application Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS application_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_posting_id INTEGER,
        status TEXT, -- applied, failed, skipped, unsupported, pending
        applied_at TEXT,
        log_details TEXT,
        FOREIGN KEY (job_posting_id) REFERENCES job_postings (id)
    )
    """)
    
    # Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        details TEXT,
        timestamp TEXT
    )
    """)
    
    # Settings Table (SMTP and Auto-Apply Threshold)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    
    # Chat/Interview turns table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interview_turns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        role TEXT, -- user, agent
        message TEXT,
        timestamp TEXT
    )
    """)
    
    conn.commit()
    conn.close()

# Initialize database on module import
init_db()

# CRUD and Helper functions
def add_audit_log(event_type: str, details: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_logs (event_type, details, timestamp) VALUES (?, ?, ?)",
        (event_type, details, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_audit_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_setting(key: str, value: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_setting(key: str, default=None) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default

def save_candidate(name, email, phone, linkedin_url, current_summary) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM candidates LIMIT 1")
    row = cursor.fetchone()
    if row:
        cand_id = row["id"]
        cursor.execute(
            "UPDATE candidates SET name = ?, email = ?, phone = ?, linkedin_url = ?, current_summary = ? WHERE id = ?",
            (name, email, phone, linkedin_url, current_summary, cand_id)
        )
    else:
        cursor.execute(
            "INSERT INTO candidates (name, email, phone, linkedin_url, current_summary) VALUES (?, ?, ?, ?, ?)",
            (name, email, phone, linkedin_url, current_summary)
        )
        cand_id = cursor.lastrowid
    conn.commit()
    conn.close()
    add_audit_log("CANDIDATE_UPDATE", f"Candidate profile updated for {name}")
    return cand_id

def get_candidate():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_resume_version(candidate_id: int, version_name: str, resume_json: dict, region: str = "Global") -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO resume_versions (candidate_id, version_name, resume_json, region, created_at) VALUES (?, ?, ?, ?, ?)",
        (candidate_id, version_name, json.dumps(resume_json), region, datetime.now().isoformat())
    )
    version_id = cursor.lastrowid
    conn.commit()
    conn.close()
    add_audit_log("RESUME_VERSION_CREATED", f"Resume version '{version_name}' ({region}) created.")
    return version_id

def get_resume_versions(candidate_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM resume_versions WHERE candidate_id = ? ORDER BY id DESC", (candidate_id,))
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        d["resume_json"] = json.loads(d["resume_json"])
        res.append(d)
    return res

def get_latest_resume_version(candidate_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM resume_versions WHERE candidate_id = ? ORDER BY id DESC LIMIT 1", (candidate_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["resume_json"] = json.loads(d["resume_json"])
        return d
    return None

def save_job_posting(job_id: str, title: str, company: str, location: str, url: str, description: str, source: str = "Playwright") -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO job_postings (job_id, title, company, location, url, description, source, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (job_id, title, company, location, url, description, source, datetime.now().isoformat()))
    posting_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return posting_id

def get_job_postings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM job_postings ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_job_posting(job_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM job_postings WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_match_result(resume_version_id: int, job_posting_id: int, match_score: int, matched_skills: list, missing_skills: list, missing_keywords: list, roi_metadata: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO match_results (resume_version_id, job_posting_id, match_score, matched_skills, missing_skills, missing_keywords, roi_metadata, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        resume_version_id,
        job_posting_id,
        match_score,
        ",".join(matched_skills),
        ",".join(missing_skills),
        ",".join(missing_keywords),
        json.dumps(roi_metadata),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    add_audit_log("JOB_MATCH_ANALYZED", f"Job posting {job_posting_id} matched with resume version {resume_version_id}. Score: {match_score}%")

def get_match_results():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT mr.*, jp.title, jp.company, jp.job_id, rv.version_name
    FROM match_results mr
    JOIN job_postings jp ON mr.job_posting_id = jp.id
    JOIN resume_versions rv ON mr.resume_version_id = rv.id
    ORDER BY mr.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        d["roi_metadata"] = json.loads(d["roi_metadata"])
        d["matched_skills"] = d["matched_skills"].split(",") if d["matched_skills"] else []
        d["missing_skills"] = d["missing_skills"].split(",") if d["missing_skills"] else []
        d["missing_keywords"] = d["missing_keywords"].split(",") if d["missing_keywords"] else []
        res.append(d)
    return res

def save_application_log(job_posting_id: int, status: str, log_details: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO application_logs (job_posting_id, status, applied_at, log_details)
    VALUES (?, ?, ?, ?)
    """, (job_posting_id, status, datetime.now().isoformat(), log_details))
    conn.commit()
    conn.close()
    add_audit_log("APPLICATION_SUBMITTED", f"Application for job ID {job_posting_id} marked as {status}.")

def get_application_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT al.*, jp.title, jp.company, jp.job_id, jp.url
    FROM application_logs al
    JOIN job_postings jp ON al.job_posting_id = jp.id
    ORDER BY al.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def clear_interview_turns(session_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM interview_turns WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

def add_interview_turn(session_id: str, role: str, message: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO interview_turns (session_id, role, message, timestamp) VALUES (?, ?, ?, ?)",
        (session_id, role, message, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_interview_turns(session_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM interview_turns WHERE session_id = ? ORDER BY id ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def reset_database():
    """Drops all tables and re-initializes them."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS candidates")
    cursor.execute("DROP TABLE IF EXISTS resume_versions")
    cursor.execute("DROP TABLE IF EXISTS job_postings")
    cursor.execute("DROP TABLE IF EXISTS match_results")
    cursor.execute("DROP TABLE IF EXISTS application_logs")
    cursor.execute("DROP TABLE IF EXISTS audit_logs")
    cursor.execute("DROP TABLE IF EXISTS settings")
    cursor.execute("DROP TABLE IF EXISTS interview_turns")
    conn.commit()
    conn.close()
    init_db()
    add_audit_log("SYSTEM_RESET", "Database reset and re-initialized successfully.")
