import sqlite3
import os
import json
from datetime import datetime

# Place the database in the job-alert-agent folder
DB_PATH = os.environ.get("DATABASE_PATH") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "job_applications.db")

def get_db_connection():
    """Return a database connection with a timeout for concurrent access."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Applications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_url TEXT NOT NULL,
            job_title TEXT,
            company TEXT,
            status TEXT DEFAULT 'Queued',
            current_step TEXT,
            candidate_profile TEXT,
            resume_path TEXT,
            screenshot_path TEXT,
            error_message TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    # Run simple schema migration to add column if table exists without it
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN current_step TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN candidate_profile TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN resume_path TEXT")
    except sqlite3.OperationalError:
        pass
    
    # 2. HITL Prompts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hitl_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER,
            question_text TEXT NOT NULL,
            input_type TEXT DEFAULT 'text',
            options TEXT,  -- JSON serialized list of options for dropdown/radio
            answer_value TEXT,
            status TEXT DEFAULT 'Pending', -- Pending, Resolved
            created_at TEXT,
            FOREIGN KEY (application_id) REFERENCES applications(id)
        )
    """)
    
    # 3. QA Cache table (for learning/caching)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qa_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT UNIQUE NOT NULL,
            answer_value TEXT NOT NULL,
            created_at TEXT
        )
    """)
    
    # 4. Application Logs table (observability)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS application_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER,
            timestamp TEXT,
            level TEXT,
            step TEXT,
            message TEXT,
            FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()

def create_application(job_url, job_title="", company="", candidate_profile=None, resume_path=None) -> int:
    """Create a new job application and return its ID."""
    now = datetime.now().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    profile_json = json.dumps(candidate_profile) if candidate_profile else None
    
    cursor.execute(
        """
        INSERT INTO applications (job_url, job_title, company, status, current_step, candidate_profile, resume_path, created_at, updated_at)
        VALUES (?, ?, ?, 'Queued', 'Added to application queue', ?, ?, ?, ?)
        """,
        (job_url, job_title, company, profile_json, resume_path, now, now)
    )
    app_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return app_id

def update_application_step(app_id, step):
    """Update the current step description of a job application."""
    now = datetime.now().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE applications SET current_step = ?, updated_at = ? WHERE id = ?",
        (step, now, app_id)
    )
    conn.commit()
    conn.close()

def update_application_status(app_id, status, screenshot_path=None, error_message=None):
    """Update the status of a job application."""
    now = datetime.now().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if screenshot_path and error_message:
        cursor.execute(
            """
            UPDATE applications
            SET status = ?, screenshot_path = ?, error_message = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, screenshot_path, error_message, now, app_id)
        )
    elif screenshot_path:
        cursor.execute(
            """
            UPDATE applications
            SET status = ?, screenshot_path = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, screenshot_path, now, app_id)
        )
    elif error_message:
        cursor.execute(
            """
            UPDATE applications
            SET status = ?, error_message = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, error_message, now, app_id)
        )
    else:
        cursor.execute(
            """
            UPDATE applications
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, now, app_id)
        )
    conn.commit()
    conn.close()

def get_application(app_id) -> dict:
    """Retrieve application details by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_applications() -> list:
    """Retrieve all job applications sorted by creation time descending."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_hitl_prompt(app_id, question_text, input_type="text", options=None) -> int:
    """Add a new HITL prompt for an application."""
    now = datetime.now().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if a pending prompt for this exact question already exists
    cursor.execute(
        "SELECT id FROM hitl_prompts WHERE application_id = ? AND question_text = ? AND status = 'Pending'",
        (app_id, question_text)
    )
    row = cursor.fetchone()
    if row:
        conn.close()
        return row[0]
        
    options_json = json.dumps(options) if options else None
    cursor.execute(
        """
        INSERT INTO hitl_prompts (application_id, question_text, input_type, options, status, created_at)
        VALUES (?, ?, ?, ?, 'Pending', ?)
        """,
        (app_id, question_text, input_type, options_json, now)
    )
    prompt_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return prompt_id

def get_pending_hitl_prompt(app_id) -> dict:
    """Get the first active/pending HITL prompt for an application."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM hitl_prompts WHERE application_id = ? AND status = 'Pending' ORDER BY id ASC LIMIT 1",
        (app_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        if d.get("options"):
            d["options"] = json.loads(d["options"])
        return d
    return None

def get_hitl_prompt(prompt_id) -> dict:
    """Retrieve an HITL prompt details by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hitl_prompts WHERE id = ?", (prompt_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        if d.get("options"):
            d["options"] = json.loads(d["options"])
        return d
    return None

def get_all_pending_hitl_prompts() -> list:
    """Get all active/pending HITL prompts across all applications."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM hitl_prompts WHERE status = 'Pending' ORDER BY id ASC"
    )
    rows = cursor.fetchall()
    conn.close()
    res = []
    for row in rows:
        d = dict(row)
        if d.get("options"):
            d["options"] = json.loads(d["options"])
        res.append(d)
    return res

def resolve_hitl_prompt(prompt_id, answer_value):
    """Resolve an HITL prompt with a given answer."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE hitl_prompts SET answer_value = ?, status = 'Resolved' WHERE id = ?",
        (str(answer_value), prompt_id)
    )
    conn.commit()
    conn.close()

def get_cached_answer(question_text) -> str:
    """Retrieve cached answer for a question if it exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Direct matching first
    cursor.execute("SELECT answer_value FROM qa_cache WHERE question_text = ?", (question_text,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def cache_answer(question_text, answer_value):
    """Cache a question-answer pair for learning."""
    now = datetime.now().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO qa_cache (question_text, answer_value, created_at)
        VALUES (?, ?, ?)
        ON CONFLICT(question_text) DO UPDATE SET answer_value = excluded.answer_value, created_at = excluded.created_at
        """,
        (question_text, str(answer_value), now)
    )
    conn.commit()
    conn.close()

def add_application_log(application_id, level, step, message):
    """Inserts a structured log record for a job application."""
    now = datetime.now().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO application_logs (application_id, timestamp, level, step, message)
        VALUES (?, ?, ?, ?, ?)
        """,
        (application_id, now, level, step, message)
    )
    conn.commit()
    conn.close()

def get_application_logs(application_id) -> list:
    """Retrieves all log records for a job application sorted chronologically."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM application_logs WHERE application_id = ? ORDER BY id ASC",
        (application_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Initialize database right away when imported/run
init_db()
