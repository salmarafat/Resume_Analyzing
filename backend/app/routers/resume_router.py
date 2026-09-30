import json
import uuid
import sqlite3
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.database import get_db
from app.auth import get_current_user
from app.config import UPLOADS_DIR
from app.models import ResumeResponse, ResumeAnalysisResponse, ExperienceItem, EducationItem
from app.services.file_extractor import validate_and_extract_file
from app.services.agents.resume_agent import resume_analyzer_agent

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])

@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Uploads a PDF or DOCX resume, extracts text, performs AI analysis,
    and stores structured results.
    """
    # 1. Validate file and extract text
    raw_text, file_type, file_size = validate_and_extract_file(file)

    # 2. Save physical file to uploads directory
    safe_filename = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    save_path = UPLOADS_DIR / safe_filename
    file.file.seek(0)
    with open(save_path, "wb") as buffer:
        buffer.write(file.file.read())

    # 3. Insert record into resumes table
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO resumes (user_id, file_name, file_path, file_type, file_size, raw_text)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        current_user["id"],
        file.filename,
        str(save_path),
        file_type,
        file_size,
        raw_text
    ))
    conn.commit()
    resume_id = cursor.lastrowid

    # 4. Trigger Resume Analyzer Agent
    analysis_data = resume_analyzer_agent.analyze(raw_text)

    # 5. Insert analysis into resume_analyses table
    cursor.execute("""
        INSERT INTO resume_analyses (
            resume_id, candidate_name, email, phone, summary,
            technical_skills, soft_skills, experience, education,
            certifications, ats_score, improvement_tips
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        resume_id,
        analysis_data["candidate_name"],
        analysis_data["email"],
        analysis_data["phone"],
        analysis_data["summary"],
        json.dumps(analysis_data["technical_skills"]),
        json.dumps(analysis_data["soft_skills"]),
        json.dumps(analysis_data["experience"]),
        json.dumps(analysis_data["education"]),
        json.dumps(analysis_data["certifications"]),
        analysis_data["ats_score"],
        json.dumps(analysis_data["improvement_tips"])
    ))
    conn.commit()
    analysis_id = cursor.lastrowid

    # 6. Build response
    analysis_resp = ResumeAnalysisResponse(
        id=analysis_id,
        resume_id=resume_id,
        candidate_name=analysis_data["candidate_name"],
        email=analysis_data["email"],
        phone=analysis_data["phone"],
        summary=analysis_data["summary"],
        technical_skills=analysis_data["technical_skills"],
        soft_skills=analysis_data["soft_skills"],
        experience=[ExperienceItem(**e) for e in analysis_data["experience"]],
        education=[EducationItem(**ed) for ed in analysis_data["education"]],
        certifications=analysis_data["certifications"],
        ats_score=analysis_data["ats_score"],
        improvement_tips=analysis_data["improvement_tips"],
        analyzed_at=str(cursor.execute("SELECT analyzed_at FROM resume_analyses WHERE id = ?", (analysis_id,)).fetchone()[0])
    )

    resume_row = cursor.execute("SELECT uploaded_at FROM resumes WHERE id = ?", (resume_id,)).fetchone()

    return ResumeResponse(
        id=resume_id,
        user_id=current_user["id"],
        file_name=file.filename,
        file_type=file_type,
        file_size=file_size,
        uploaded_at=str(resume_row["uploaded_at"]),
        analysis=analysis_resp
    )

@router.get("/my", response_model=List[ResumeResponse])
def get_my_resumes(
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db)
):
    """Retrieves all resumes uploaded by the current authenticated user."""
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT r.id, r.user_id, r.file_name, r.file_type, r.file_size, r.uploaded_at,
               a.id as analysis_id, a.candidate_name, a.email, a.phone, a.summary,
               a.technical_skills, a.soft_skills, a.experience, a.education,
               a.certifications, a.ats_score, a.improvement_tips, a.analyzed_at
        FROM resumes r
        LEFT JOIN resume_analyses a ON r.id = a.resume_id
        WHERE r.user_id = ?
        ORDER BY r.uploaded_at DESC
    """, (current_user["id"],)).fetchall()

    resumes = []
    for r in rows:
        analysis = None
        if r["analysis_id"]:
            analysis = ResumeAnalysisResponse(
                id=r["analysis_id"],
                resume_id=r["id"],
                candidate_name=r["candidate_name"],
                email=r["email"],
                phone=r["phone"],
                summary=r["summary"],
                technical_skills=json.loads(r["technical_skills"] or "[]"),
                soft_skills=json.loads(r["soft_skills"] or "[]"),
                experience=[ExperienceItem(**e) for e in json.loads(r["experience"] or "[]")],
                education=[EducationItem(**ed) for ed in json.loads(r["education"] or "[]")],
                certifications=json.loads(r["certifications"] or "[]"),
                ats_score=r["ats_score"] or 0,
                improvement_tips=json.loads(r["improvement_tips"] or "[]"),
                analyzed_at=str(r["analyzed_at"])
            )

        resumes.append(ResumeResponse(
            id=r["id"],
            user_id=r["user_id"],
            file_name=r["file_name"],
            file_type=r["file_type"],
            file_size=r["file_size"],
            uploaded_at=str(r["uploaded_at"]),
            analysis=analysis
        ))

    return resumes

@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume_by_id(
    resume_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db)
):
    """Retrieves a single resume and its AI analysis report."""
    cursor = conn.cursor()
    r = cursor.execute("""
        SELECT r.id, r.user_id, r.file_name, r.file_type, r.file_size, r.uploaded_at,
               a.id as analysis_id, a.candidate_name, a.email, a.phone, a.summary,
               a.technical_skills, a.soft_skills, a.experience, a.education,
               a.certifications, a.ats_score, a.improvement_tips, a.analyzed_at
        FROM resumes r
        LEFT JOIN resume_analyses a ON r.id = a.resume_id
        WHERE r.id = ? AND r.user_id = ?
    """, (resume_id, current_user["id"])).fetchone()

    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} was not found."
        )

    analysis = None
    if r["analysis_id"]:
        analysis = ResumeAnalysisResponse(
            id=r["analysis_id"],
            resume_id=r["id"],
            candidate_name=r["candidate_name"],
            email=r["email"],
            phone=r["phone"],
            summary=r["summary"],
            technical_skills=json.loads(r["technical_skills"] or "[]"),
            soft_skills=json.loads(r["soft_skills"] or "[]"),
            experience=[ExperienceItem(**e) for e in json.loads(r["experience"] or "[]")],
            education=[EducationItem(**ed) for ed in json.loads(r["education"] or "[]")],
            certifications=json.loads(r["certifications"] or "[]"),
            ats_score=r["ats_score"] or 0,
            improvement_tips=json.loads(r["improvement_tips"] or "[]"),
            analyzed_at=str(r["analyzed_at"])
        )

    return ResumeResponse(
        id=r["id"],
        user_id=r["user_id"],
        file_name=r["file_name"],
        file_type=r["file_type"],
        file_size=r["file_size"],
        uploaded_at=str(r["uploaded_at"]),
        analysis=analysis
    )

@router.post("/{resume_id}/reanalyze", response_model=ResumeResponse)
def reanalyze_resume(
    resume_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db)
):
    """Triggers re-analysis of an existing resume."""
    cursor = conn.cursor()
    resume = cursor.execute(
        "SELECT id, raw_text, file_name, file_type, file_size, uploaded_at FROM resumes WHERE id = ? AND user_id = ?",
        (resume_id, current_user["id"])
    ).fetchone()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} was not found."
        )

    analysis_data = resume_analyzer_agent.analyze(resume["raw_text"])

    cursor.execute("""
        INSERT INTO resume_analyses (
            resume_id, candidate_name, email, phone, summary,
            technical_skills, soft_skills, experience, education,
            certifications, ats_score, improvement_tips, analyzed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(resume_id) DO UPDATE SET
            candidate_name = excluded.candidate_name,
            email = excluded.email,
            phone = excluded.phone,
            summary = excluded.summary,
            technical_skills = excluded.technical_skills,
            soft_skills = excluded.soft_skills,
            experience = excluded.experience,
            education = excluded.education,
            certifications = excluded.certifications,
            ats_score = excluded.ats_score,
            improvement_tips = excluded.improvement_tips,
            analyzed_at = CURRENT_TIMESTAMP
    """, (
        resume_id,
        analysis_data["candidate_name"],
        analysis_data["email"],
        analysis_data["phone"],
        analysis_data["summary"],
        json.dumps(analysis_data["technical_skills"]),
        json.dumps(analysis_data["soft_skills"]),
        json.dumps(analysis_data["experience"]),
        json.dumps(analysis_data["education"]),
        json.dumps(analysis_data["certifications"]),
        analysis_data["ats_score"],
        json.dumps(analysis_data["improvement_tips"])
    ))
    conn.commit()

    return get_resume_by_id(resume_id, current_user, conn)

@router.delete("/{resume_id}")
def delete_resume(
    resume_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db)
):
    """Deletes a resume and associated analyses and matches."""
    cursor = conn.cursor()
    resume = cursor.execute(
        "SELECT id, file_path FROM resumes WHERE id = ? AND user_id = ?",
        (resume_id, current_user["id"])
    ).fetchone()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} was not found."
        )

    # Delete physical file if exists
    try:
        p = Path(resume["file_path"])
        if p.exists():
            p.unlink()
    except Exception:
        pass

    cursor.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
    conn.commit()

    return {"message": f"Resume {resume_id} deleted successfully."}
