import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from app.middleware.rate_limit import limiter

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.assessment import AssessmentSession, AssessmentSessionQuestion

from app.schemas.assessment import (
    AssessmentStartRequest,
    AssessmentSessionResponse,
    AssessmentSubmitRequest,
    AssessmentResultResponse,
    AssessmentHistoryItemResponse
)
from app.services.assessment_engine import create_assessment_session, submit_assessment
from app.services.notification_service import NotificationService
from app.core.config import get_settings
import redis.asyncio as aioredis


router = APIRouter(prefix="/assessments", tags=["Assessments"])

ASSESSMENT_TIME_LIMIT_MINUTES = 30


@router.post("/start", response_model=AssessmentSessionResponse)
@limiter.limit("20/hour")
async def start_assessment(
    request: Request,
    data: AssessmentStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new assessment session.
    
    SECURITY: Response NEVER includes correct_answer, is_correct, or explanation.
    These are only revealed after submission.
    """
    session = await create_assessment_session(
        db=db,
        student_id=current_user.id,
        topic=data.topic,
        difficulty=data.difficulty
    )
    
    # SECURITY: Only expose question_text, options, and id — NO correct_answer, is_correct, or explanation
    questions_response = [
        {
            "id": sq.question.id,
            "question_text": sq.question.question_text,
            "options": sq.question.options
        }
        for sq in session.session_questions
    ]
    
    return {
        "id": session.id,
        "topic": session.topic,
        "difficulty": session.difficulty,
        "status": session.status,
        "started_at": session.started_at,
        "questions": questions_response
    }


class TabSwitchReport(BaseModel):
    tab_switches: int = 0


@router.post("/{session_id}/tab-switch")
async def report_tab_switch(
    session_id: uuid.UUID,
    report: TabSwitchReport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report tab switches during an active assessment."""
    result = await db.execute(
        select(AssessmentSession)
        .where(
            AssessmentSession.id == session_id,
            AssessmentSession.student_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.status == "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session already completed")
    
    # Tab switches are logged but do not auto-disqualify
    return {"acknowledged": True, "tab_switches_reported": report.tab_switches}


@router.post("/{session_id}/submit", response_model=AssessmentResultResponse)
async def submit_assessment_endpoint(
    session_id: uuid.UUID,
    request: AssessmentSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit assessment answers and get the result.
    
    Grading happens securely on the backend.
    correct_answer and is_correct are ONLY returned AFTER submission.
    On score >= 70%, student skill confidence is updated.
    """
    session = await submit_assessment(
        db=db,
        student_id=current_user.id,
        session_id=session_id,
        data=request
    )
    
    correct = sum(1 for sq in session.session_questions if sq.is_correct)
    total = len(session.session_questions)
    
    # ONLY reveal correct answers AFTER submission (post-grading)
    questions_response = [
        {
            "id": sq.question.id,
            "question_text": sq.question.question_text,
            "options": sq.question.options,
            "selected_option": sq.selected_option,
            "correct_answer": sq.question.correct_answer,
            "is_correct": bool(sq.is_correct),
            "explanation": sq.question.explanation
        }
        for sq in session.session_questions
    ]
    
    # Notify on high score (>= 70%) and update skill confidence via assessment_engine
    if session.score and session.score >= 70:
        try:
            redis_client = aioredis.from_url(get_settings().REDIS_URL, decode_responses=True)
            ns = NotificationService(db, redis_client)
            if session.score >= 85:
                title = "🎯 Top scorer! Roadmap updated"
                message = f"You scored {session.score:.0f}% on {session.topic}. Amazing job!"
            else:
                title = "✅ Assessment passed!"
                message = f"You scored {session.score:.0f}% on {session.topic}. Skill confidence updated."
            await ns.publish(
                user_id=current_user.id,
                type="ASSESSMENT_RESULT",
                title=title,
                message=message,
                priority="normal"
            )
            await redis_client.aclose()
        except Exception:
            pass  # Don't fail the submission if notification fails

    return {
        "id": session.id,
        "topic": session.topic,
        "difficulty": session.difficulty,
        "score": session.score,
        "total_questions": total,
        "correct": correct,
        "incorrect": total - correct,
        "percentage": session.score,
        "questions": questions_response,
        "completed_at": session.completed_at
    }


@router.get("/history", response_model=list[AssessmentHistoryItemResponse])
async def get_assessment_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the student's assessment history."""
    result = await db.execute(
        select(AssessmentSession)
        .where(AssessmentSession.student_id == current_user.id)
        .order_by(AssessmentSession.started_at.desc())
    )
    
    sessions = result.scalars().all()
    
    return [
        {
            "id": session.id,
            "topic": session.topic,
            "difficulty": session.difficulty,
            "score": session.score,
            "percentage": session.score,
            "status": session.status,
            "started_at": session.started_at,
            "completed_at": session.completed_at
        }
        for session in sessions
    ]
