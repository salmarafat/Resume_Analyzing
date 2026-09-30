import json
import sqlite3
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.database import get_db
from app.auth import get_current_user, get_optional_user
from app.models import JobCreate, JobUpdate, JobResponse

router = APIRouter(prefix="/api/jobs", tags=["Job Management & Search"])

def _format_job_row(row: sqlite3.Row) -> JobResponse:
    """Helper to convert a database job row into a Pydantic JobResponse."""
    req_skills = row["required_skills"]
    if isinstance(req_skills, str):
        try:
            req_skills = json.loads(req_skills)
        except Exception:
            req_skills = [s.strip() for s in req_skills.split(",") if s.strip()]

    pref_skills = row["preferred_skills"]
    if isinstance(pref_skills, str):
        try:
            pref_skills = json.loads(pref_skills)
        except Exception:
            pref_skills = [s.strip() for s in pref_skills.split(",") if s.strip()]
    elif pref_skills is None:
        pref_skills = []

    return JobResponse(
        id=row["id"],
        posted_by=row["posted_by"],
        title=row["title"],
        company=row["company"],
        location=row["location"],
        employment_type=row["employment_type"],
        experience_level=row["experience_level"],
        salary_range=row["salary_range"],
        department=row["department"],
        description=row["description"],
        required_skills=req_skills,
        preferred_skills=pref_skills,
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"])
    )

@router.get("", response_model=List[JobResponse])
def search_and_list_jobs(
    keyword: Optional[str] = Query(None, description="Search keyword in title, company, or description"),
    location: Optional[str] = Query(None, description="Filter by location (e.g. Remote, Hybrid, San Francisco)"),
    department: Optional[str] = Query(None, description="Filter by department (e.g. Engineering, Data)"),
    experience_level: Optional[str] = Query(None, description="Filter by experience (Entry, Mid, Senior, Lead)"),
    skill: Optional[str] = Query(None, description="Filter by required skill (e.g. Python, Docker)"),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    FR-7: Job Search - Search and filter jobs using multiple criteria.
    """
    cursor = conn.cursor()
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if keyword:
        query += " AND (title LIKE ? OR company LIKE ? OR description LIKE ?)"
        term = f"%{keyword}%"
        params.extend([term, term, term])

    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")

    if department:
        query += " AND department LIKE ?"
        params.append(f"%{department}%")

    if experience_level:
        query += " AND experience_level = ?"
        params.append(experience_level)

    if skill:
        query += " AND required_skills LIKE ?"
        params.append(f"%{skill}%")

    query += " ORDER BY created_at DESC"

    rows = cursor.execute(query, params).fetchall()
    return [_format_job_row(r) for r in rows]

@router.get("/{job_id}", response_model=JobResponse)
def get_job_by_id(job_id: int, conn: sqlite3.Connection = Depends(get_db)):
    """FR-6: View single job details."""
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} was not found."
        )
    return _format_job_row(row)

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_data: JobCreate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db)
):
    """FR-6: Add a new job posting."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (
            posted_by, title, company, location, employment_type,
            experience_level, salary_range, department, description,
            required_skills, preferred_skills
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        current_user["id"],
        job_data.title.strip(),
        job_data.company.strip(),
        job_data.location.strip(),
        job_data.employment_type,
        job_data.experience_level,
        job_data.salary_range,
        job_data.department,
        job_data.description.strip(),
        json.dumps(job_data.required_skills),
        json.dumps(job_data.preferred_skills or [])
    ))
    conn.commit()
    job_id = cursor.lastrowid

    row = cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return _format_job_row(row)

@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    job_update: JobUpdate,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db)
):
    """FR-6: Edit an existing job posting."""
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} was not found."
        )

    # Permission check: must be owner or admin
    if row["posted_by"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this job posting."
        )

    # Prepare update fields
    updates = []
    params = []

    if job_update.title is not None:
        updates.append("title = ?")
        params.append(job_update.title.strip())
    if job_update.company is not None:
        updates.append("company = ?")
        params.append(job_update.company.strip())
    if job_update.location is not None:
        updates.append("location = ?")
        params.append(job_update.location.strip())
    if job_update.employment_type is not None:
        updates.append("employment_type = ?")
        params.append(job_update.employment_type)
    if job_update.experience_level is not None:
        updates.append("experience_level = ?")
        params.append(job_update.experience_level)
    if job_update.salary_range is not None:
        updates.append("salary_range = ?")
        params.append(job_update.salary_range)
    if job_update.department is not None:
        updates.append("department = ?")
        params.append(job_update.department)
    if job_update.description is not None:
        updates.append("description = ?")
        params.append(job_update.description.strip())
    if job_update.required_skills is not None:
        updates.append("required_skills = ?")
        params.append(json.dumps(job_update.required_skills))
    if job_update.preferred_skills is not None:
        updates.append("preferred_skills = ?")
        params.append(json.dumps(job_update.preferred_skills))

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(job_id)
        sql = f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(sql, params)
        conn.commit()

    updated_row = cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return _format_job_row(updated_row)

@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db)
):
    """FR-6: Delete a job posting."""
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} was not found."
        )

    # Permission check: must be owner or admin
    if row["posted_by"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this job posting."
        )

    cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()

    return {"message": f"Job {job_id} deleted successfully."}
