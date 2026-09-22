"""
Mock Interview API V2 — AI-powered multi-round interview sessions.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.mock_interview_service import mock_interview_service

router = APIRouter(prefix="/mock-interviews", tags=["Mock Interviews"])


# ─── Request / Response Schemas ──────────────────────────────────────

class StartInterviewRequest(BaseModel):
    role_target: str = Field(..., min_length=2, max_length=200)
    company_style: str = Field(default="Product")
    difficulty: str = Field(default="campus")


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


# ─── Static path endpoints MUST come before {session_id} ────────────

@router.post("/start", summary="Start a new mock interview session")
async def start_interview(
    data: StartInterviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a new mock interview session and returns the interviewer's
    opening greeting. The session transitions through intro → technical →
    behavioral → completed rounds automatically.
    """
    result = await mock_interview_service.start_session(
        db=db,
        student_id=current_user.id,
        role_target=data.role_target,
        company_style=data.company_style,
        difficulty=data.difficulty,
    )
    return result


@router.get("/my", summary="List student's past interview sessions")
async def list_my_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the student's past mock interview sessions, most recent first."""
    sessions = await mock_interview_service.list_sessions(db, current_user.id, limit)
    return [
        {
            "id": str(s.id),
            "role_target": s.role_target,
            "company_style": s.company_style,
            "difficulty": s.difficulty,
            "status": s.status,
            "performance_scores": s.performance_scores,
            "verdict": (s.final_report or {}).get("verdict"),
            "filler_word_count": s.filler_word_count,
            "duration_seconds": s.duration_seconds,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        }
        for s in sessions
    ]


@router.get("/my/stats", summary="Aggregate mock interview statistics")
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns aggregate stats: total sessions, average scores, and improvement trend."""
    return await mock_interview_service.get_stats(db, current_user.id)


# ─── Dynamic path endpoints ─────────────────────────────────────────

@router.post("/{session_id}/message", summary="Send candidate message and get interviewer response")
async def send_message(
    session_id: uuid.UUID,
    data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Sends the candidate's response, triggers Gemini for the interviewer's
    next question or evaluation. If the interview ends, automatically
    generates and returns the final report.
    """
    result = await mock_interview_service.send_message(
        db=db,
        session_id=session_id,
        student_id=current_user.id,
        student_message=data.content,
    )
    return result


@router.get("/{session_id}", summary="Get interview session details")
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full interview session including transcript."""
    session = await mock_interview_service.get_session(db, session_id, current_user.id)
    return {
        "id": str(session.id),
        "role_target": session.role_target,
        "company_style": session.company_style,
        "difficulty": session.difficulty,
        "status": session.status,
        "current_round": session.current_round,
        "transcript": session.transcript or [],
        "performance_scores": session.performance_scores,
        "filler_word_count": session.filler_word_count,
        "word_count": session.word_count,
        "duration_seconds": session.duration_seconds,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
    }


@router.get("/{session_id}/report", summary="Get final interview report")
async def get_report(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the final performance report. Returns 404 if interview is not completed."""
    session = await mock_interview_service.get_session(db, session_id, current_user.id)
    if session.status != "completed" or not session.final_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview report not available. Complete the interview first."
        )
    return session.final_report
