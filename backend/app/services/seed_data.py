import json
import logging
from app.database import get_db_connection
from app.auth import hash_password
from app.config import KNOWLEDGE_BASE_DIR

logger = logging.getLogger("seed_data")

def seed_initial_data():
    """Seeds the database with initial users and job openings if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Seed Users
    user_count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    recruiter_id = 1
    if user_count == 0:
        logger.info("Seeding initial users...")
        demo_pwd = hash_password("password123")
        cursor.execute("""
            INSERT INTO users (email, username, hashed_password, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        """, ("demo@resume.ai", "demo_user", demo_pwd, "Alex Taylor", "job_seeker"))

        cursor.execute("""
            INSERT INTO users (email, username, hashed_password, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        """, ("recruiter@techcorp.io", "tech_recruiter", demo_pwd, "Sarah Jenkins", "recruiter"))

        conn.commit()
        recruiter_id = cursor.lastrowid

    # 2. Seed Jobs from Knowledge Base
    job_count = cursor.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    if job_count == 0:
        logger.info("Seeding initial job postings...")
        jobs_file = KNOWLEDGE_BASE_DIR / "job_descriptions.json"
        if jobs_file.exists():
            with open(jobs_file, "r", encoding="utf-8") as f:
                jobs_data = json.load(f)

            companies = [
                ("Stripe Technologies", "San Francisco, CA (Hybrid)", "$130,000 - $165,000"),
                ("Datadog Systems", "New York, NY (Remote)", "$150,000 - $190,000"),
                ("Spotify Analytics", "Boston, MA (Remote)", "$120,000 - $155,000"),
                ("OpenAI Labs", "San Francisco, CA (Onsite)", "$180,000 - $240,000"),
                ("Airbnb Experiences", "Austin, TX (Remote)", "$100,000 - $135,000"),
                ("Amazon Web Services", "Seattle, WA (Hybrid)", "$140,000 - $185,000")
            ]

            for i, job in enumerate(jobs_data):
                company_info = companies[i % len(companies)]
                req_skills_json = json.dumps(job.get("required_skills", []))
                pref_skills_json = json.dumps(job.get("preferred_skills", []))
                desc = (
                    f"{job.get('summary')}\n\n"
                    f"Key Responsibilities:\n" +
                    "\n".join([f"• {r}" for r in job.get("key_responsibilities", [])]) +
                    f"\n\nTypical Experience: {job.get('typical_experience_years', '2+ years')}."
                )

                cursor.execute("""
                    INSERT INTO jobs (
                        posted_by, title, company, location, employment_type,
                        experience_level, salary_range, department, description,
                        required_skills, preferred_skills
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    recruiter_id,
                    job.get("title"),
                    company_info[0],
                    company_info[1],
                    "Full-time",
                    job.get("experience_level", "Mid"),
                    company_info[2],
                    job.get("department", "Engineering"),
                    desc,
                    req_skills_json,
                    pref_skills_json
                ))

            conn.commit()

    conn.close()
