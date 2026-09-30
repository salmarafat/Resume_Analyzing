import sqlite3
from typing import Generator
from app.config import DB_PATH

def get_db_connection() -> sqlite3.Connection:
    """Creates and returns an SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency that yields a database connection and handles closing."""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initializes all database tables and necessary indexes."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'job_seeker', -- 'job_seeker', 'recruiter', 'admin'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT NOT NULL, -- 'pdf' or 'docx'
        file_size INTEGER NOT NULL,
        raw_text TEXT NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS resume_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER UNIQUE NOT NULL,
        candidate_name TEXT,
        email TEXT,
        phone TEXT,
        summary TEXT,
        technical_skills TEXT, -- JSON Array
        soft_skills TEXT,      -- JSON Array
        experience TEXT,       -- JSON Array of objects
        education TEXT,        -- JSON Array of objects
        certifications TEXT,   -- JSON Array
        ats_score INTEGER DEFAULT 0,
        improvement_tips TEXT, -- JSON Array
        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        posted_by INTEGER,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT NOT NULL,
        employment_type TEXT NOT NULL DEFAULT 'Full-time',
        experience_level TEXT NOT NULL DEFAULT 'Mid',
        salary_range TEXT,
        department TEXT NOT NULL DEFAULT 'Engineering',
        description TEXT NOT NULL,
        required_skills TEXT NOT NULL, -- JSON Array
        preferred_skills TEXT,         -- JSON Array
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (posted_by) REFERENCES users (id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS job_matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER NOT NULL,
        job_id INTEGER NOT NULL,
        match_score REAL NOT NULL, -- 0.0 to 100.0
        matched_skills TEXT,       -- JSON Array
        missing_skills TEXT,       -- JSON Array
        match_explanation TEXT,
        calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE CASCADE,
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE,
        UNIQUE (resume_id, job_id)
    );

    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        resume_id INTEGER,
        role TEXT NOT NULL,        -- 'user' or 'assistant'
        message TEXT NOT NULL,
        retrieved_sources TEXT,    -- JSON Array
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE SET NULL
    );

    CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
    CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);
    CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
    CREATE INDEX IF NOT EXISTS idx_matches_resume ON job_matches(resume_id);
    CREATE INDEX IF NOT EXISTS idx_matches_job ON job_matches(job_id);
    """)

    conn.commit()
    conn.close()
