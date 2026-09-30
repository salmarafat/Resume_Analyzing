import json
import sqlite3
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.auth import get_current_user
from app.models import RecommendationResponse, JobMatchItem, JobResponse
from app.routers.jobs_router import _format_job_row
from app.services.agents.matching_agent import job_matching_agent

router = APIRouter(prefix="/api/recommendations", tags=["Job Recommendations & Matching"])

@router.get("/resume/{resume_id}", response_model=RecommendationResponse)
def get_recommendations_for_resume(
    resume_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    FR-4: Evaluates candidate resume against all available jobs, calculates
    matching scores (0-100%), ranks recommendations, and explains each match.
    """
    cursor = conn.cursor()

    # 1. Fetch resume and analysis
    resume = cursor.execute(
        "SELECT id, raw_text, user_id FROM resumes WHERE id = ? AND user_id = ?",
        (resume_id, current_user["id"])
    ).fetchone()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} was not found."
        )

    analysis_row = cursor.execute(
        "SELECT candidate_name, technical_skills FROM resume_analyses WHERE resume_id = ?",
        (resume_id,)
    ).fetchone()

    candidate_name = analysis_row["candidate_name"] if analysis_row else "Candidate"
    skills = json.loads(analysis_row["technical_skills"] or "[]") if analysis_row else []

    # 2. Fetch all jobs
    jobs = cursor.execute("SELECT * FROM jobs ORDER BY id ASC").fetchall()
    if not jobs:
        return RecommendationResponse(
            resume_id=resume_id,
            candidate_name=candidate_name,
            total_jobs_evaluated=0,
            recommendations=[]
        )

    recommendations: List[JobMatchItem] = []

    # 3. Evaluate each job using Job Matching Agent
    for job_row in jobs:
        job_dict = dict(job_row)
        match_result = job_matching_agent.evaluate_match(
            resume_text=resume["raw_text"],
            candidate_skills=skills,
            job=job_dict
        )

        # Store or update in job_matches table
        cursor.execute("""
            INSERT INTO job_matches (
                resume_id, job_id, match_score, matched_skills, missing_skills, match_explanation, calculated_at
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(resume_id, job_id) DO UPDATE SET
                match_score = excluded.match_score,
                matched_skills = excluded.matched_skills,
                missing_skills = excluded.missing_skills,
                match_explanation = excluded.match_explanation,
                calculated_at = CURRENT_TIMESTAMP
        """, (
            resume_id,
            job_row["id"],
            match_result["match_score"],
            json.dumps(match_result["matched_skills"]),
            json.dumps(match_result["missing_skills"]),
            match_result["match_explanation"]
        ))

        job_resp = _format_job_row(job_row)
        recommendations.append(JobMatchItem(
            job=job_resp,
            match_score=match_result["match_score"],
            matched_skills=match_result["matched_skills"],
            missing_skills=match_result["missing_skills"],
            match_explanation=match_result["match_explanation"]
        ))

    conn.commit()

    # 4. Sort recommendations by match_score descending
    recommendations.sort(key=lambda x: x.match_score, reverse=True)

    return RecommendationResponse(
        resume_id=resume_id,
        candidate_name=candidate_name,
        total_jobs_evaluated=len(jobs),
        recommendations=recommendations
    )

@router.get("/job/{job_id}/compare/{resume_id}", response_model=JobMatchItem)
def compare_specific_job_with_resume(
    job_id: int,
    resume_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Directly compares a specific job posting against a specific candidate resume.
    """
    cursor = conn.cursor()

    resume = cursor.execute(
        "SELECT id, raw_text, user_id FROM resumes WHERE id = ? AND user_id = ?",
        (resume_id, current_user["id"])
    ).fetchone()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} was not found."
        )

    job_row = cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} was not found."
        )

    analysis_row = cursor.execute(
        "SELECT technical_skills FROM resume_analyses WHERE resume_id = ?",
        (resume_id,)
    ).fetchone()
    skills = json.loads(analysis_row["technical_skills"] or "[]") if analysis_row else []

    match_result = job_matching_agent.evaluate_match(
        resume_text=resume["raw_text"],
        candidate_skills=skills,
        job=dict(job_row)
    )

    return JobMatchItem(
        job=_format_job_row(job_row),
        match_score=match_result["match_score"],
        matched_skills=match_result["matched_skills"],
        missing_skills=match_result["missing_skills"],
        match_explanation=match_result["match_explanation"]
    )
