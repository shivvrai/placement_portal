import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
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


@router.post("/start", response_model=AssessmentSessionResponse)
@limiter.limit("20/hour")
async def start_assessment(
    request: Request,
    data: AssessmentStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new assessment session."""
    session = await create_assessment_session(
        db=db,
        student_id=current_user.id,
        topic=data.topic,
        difficulty=data.difficulty
    )
    
    # Map to schema (correct_answer will NOT be included due to schema definition)
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


@router.post("/{session_id}/submit", response_model=AssessmentResultResponse)
async def submit_assessment_endpoint(
    session_id: uuid.UUID,
    request: AssessmentSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit assessment answers and get the result."""
    session = await submit_assessment(
        db=db,
        student_id=current_user.id,
        session_id=session_id,
        data=request
    )
    
    correct = sum(1 for sq in session.session_questions if sq.is_correct)
    total = len(session.session_questions)
    
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
    
    
    if session.score and session.score >= 85:
        redis_client = aioredis.from_url(get_settings().REDIS_URL, decode_responses=True)
        ns = NotificationService(db, redis_client)
        await ns.publish(
            user_id=current_user.id,
            type="ASSESSMENT_RESULT",
            title="🎯 Top scorer! Roadmap updated",
            message=f"You scored {session.score}% on {session.topic}. Amazing job!",
            priority="normal"
        )
        await redis_client.aclose()

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


# ─── V2: Quick Quiz ──────────────────────────────────────────────────

@router.post("/quiz/quick", response_model=AssessmentSessionResponse)
async def start_quick_quiz(
    request: AssessmentStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a quick 5-question quiz on a specific topic."""
    # Reuse existing create_assessment_session which already selects random questions
    session = await create_assessment_session(
        db=db,
        student_id=current_user.id,
        topic=request.topic,
        difficulty=request.difficulty
    )

    # Limit to 5 questions for quick quiz
    questions_response = [
        {
            "id": sq.question.id,
            "question_text": sq.question.question_text,
            "options": sq.question.options
        }
        for sq in session.session_questions[:5]
    ]

    return {
        "id": session.id,
        "topic": session.topic,
        "difficulty": session.difficulty,
        "status": session.status,
        "started_at": session.started_at,
        "questions": questions_response
    }


# ─── V2: Recommended Quizzes ────────────────────────────────────────

@router.get("/quiz/recommended")
async def get_recommended_quizzes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI-recommended quiz topics based on skill gaps and active drive requirements."""
    from app.services.assessment_engine import get_recommended_quizzes as _get_recommended
    return await _get_recommended(db, current_user.id)


# ─── V2: Remediation Plan ───────────────────────────────────────────

@router.post("/quiz/{session_id}/remediate")
async def generate_remediation(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """After failing a quiz (<60%), generate targeted remediation roadmap tasks."""
    from app.services.assessment_engine import generate_remediation_plan
    tasks = await generate_remediation_plan(db, session_id, current_user.id)
    if not tasks:
        return {"message": "No remediation needed — score is 60% or above.", "tasks": []}
    return {
        "message": f"Generated {len(tasks)} remediation tasks added to your roadmap.",
        "tasks": tasks,
    }


# ─── V2: Performance Trends ─────────────────────────────────────────

@router.get("/performance/trends")
async def get_trends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Score trends per topic over time."""
    from app.services.assessment_engine import get_performance_trends
    return await get_performance_trends(db, current_user.id)

