import json
import sqlite3
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.database import get_db
from app.auth import get_current_user
from app.models import CareerImprovementResponse, ChatMessageRequest, ChatMessageResponse
from app.services.agents.advisor_agent import career_advisor_agent
from app.services.rag_engine import rag_engine

router = APIRouter(prefix="/api/career", tags=["Career Advisor & Improvement"])

@router.get("/improve/{resume_id}", response_model=CareerImprovementResponse)
def get_resume_improvements(
    resume_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    FR-5: Resume Improvement - Evaluates missing skills, weaknesses,
    actionable improvements, recommended certifications, and learning resources.
    """
    cursor = conn.cursor()

    # Validate resume ownership
    resume = cursor.execute(
        "SELECT id FROM resumes WHERE id = ? AND user_id = ?",
        (resume_id, current_user["id"])
    ).fetchone()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} was not found."
        )

    analysis_row = cursor.execute(
        """SELECT resume_id, candidate_name, summary, technical_skills,
                  soft_skills, experience, ats_score, improvement_tips
           FROM resume_analyses WHERE resume_id = ?""",
        (resume_id,)
    ).fetchone()

    if not analysis_row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume has not been analyzed yet. Please trigger an analysis first."
        )

    analysis_dict = {
        "resume_id": analysis_row["resume_id"],
        "candidate_name": analysis_row["candidate_name"],
        "summary": analysis_row["summary"],
        "technical_skills": json.loads(analysis_row["technical_skills"] or "[]"),
        "soft_skills": json.loads(analysis_row["soft_skills"] or "[]"),
        "experience": json.loads(analysis_row["experience"] or "[]"),
        "ats_score": analysis_row["ats_score"] or 60,
        "improvement_tips": json.loads(analysis_row["improvement_tips"] or "[]")
    }

    # Generate plan via Career Advisor Agent
    plan = career_advisor_agent.generate_improvement_plan(analysis_dict)

    return CareerImprovementResponse(**plan)

@router.post("/chat", response_model=ChatMessageResponse)
def chat_with_career_advisor(
    req: ChatMessageRequest,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Interactive AI Career Advisor Agent session with RAG knowledge base retrieval.
    Answers career questions, resume improvement queries, and roadmap guidance.
    """
    if not req.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty."
        )

    cursor = conn.cursor()
    resume_summary = None
    skills = []

    # If resume_id is provided, pull context from it
    if req.resume_id:
        row = cursor.execute("""
            SELECT a.summary, a.technical_skills
            FROM resume_analyses a
            JOIN resumes r ON a.resume_id = r.id
            WHERE r.id = ? AND r.user_id = ?
        """, (req.resume_id, current_user["id"])).fetchone()

        if row:
            resume_summary = row["summary"]
            skills = json.loads(row["technical_skills"] or "[]")

    # Call Career Advisor Agent
    agent_output = career_advisor_agent.answer_career_question(
        user_message=req.message,
        resume_summary=resume_summary,
        candidate_skills=skills
    )

    # Store user message and assistant response in chat_messages table
    cursor.execute("""
        INSERT INTO chat_messages (user_id, resume_id, role, message, retrieved_sources)
        VALUES (?, ?, 'user', ?, ?)
    """, (current_user["id"], req.resume_id, req.message, json.dumps([])))

    cursor.execute("""
        INSERT INTO chat_messages (user_id, resume_id, role, message, retrieved_sources)
        VALUES (?, ?, 'assistant', ?, ?)
    """, (
        current_user["id"],
        req.resume_id,
        agent_output["message"],
        json.dumps(agent_output["retrieved_sources"])
    ))
    conn.commit()

    created_at_row = cursor.execute(
        "SELECT created_at FROM chat_messages WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()

    return ChatMessageResponse(
        role="assistant",
        message=agent_output["message"],
        retrieved_sources=agent_output["retrieved_sources"],
        created_at=str(created_at_row["created_at"])
    )

@router.get("/history", response_model=List[ChatMessageResponse])
def get_chat_history(
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db)
):
    """Fetches chat message history for the authenticated user."""
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT role, message, retrieved_sources, created_at
        FROM chat_messages
        WHERE user_id = ?
        ORDER BY id ASC
        LIMIT 50
    """, (current_user["id"],)).fetchall()

    return [
        ChatMessageResponse(
            role=r["role"],
            message=r["message"],
            retrieved_sources=json.loads(r["retrieved_sources"] or "[]"),
            created_at=str(r["created_at"])
        )
        for r in rows
    ]

@router.get("/knowledge/search")
def search_knowledge_base(
    query: str = Query(..., min_length=2, description="Knowledge base search query"),
    category: Optional[str] = Query(None, description="Category filter: jobs, skills, roadmaps, resources, guidelines"),
    top_k: int = Query(5, ge=1, le=20)
):
    """Direct search endpoint into the RAG knowledge base for transparency and exploration."""
    categories = [category] if category else None
    results = rag_engine.retrieve(query=query, top_k=top_k, categories=categories)
    return {
        "query": query,
        "category": category,
        "count": len(results),
        "results": results
    }
