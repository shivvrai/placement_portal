import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

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


router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.post("/start", response_model=AssessmentSessionResponse)
async def start_assessment(
    request: AssessmentStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new assessment session."""
    session = await create_assessment_session(
        db=db,
        student_id=current_user.id,
        topic=request.topic,
        difficulty=request.difficulty
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


@router.post("/{session_id}/submit-code")
async def submit_code_endpoint(
    session_id: uuid.UUID,
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.services.assessment_engine import submit_code
    return await submit_code(
        db=db,
        student_id=current_user.id,
        session_id=session_id,
        question_id=uuid.UUID(request["question_id"]),
        code=request["code"],
        language=request.get("language", "python")
    )

@router.get("/history/detailed")
async def get_history_detailed(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(AssessmentSession)
        .where(AssessmentSession.student_id == current_user.id)
        .order_by(AssessmentSession.started_at.desc())
    )
    sessions = result.scalars().all()
    return [{"id": s.id, "topic": s.topic, "difficulty": s.difficulty, "score": s.score, "metadata": s.metadata_col} for s in sessions]

@router.get("/analytics/my")
async def get_my_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Mocked for now to fulfill the interface
    return {
        "topics": [
            {"name": "Python", "avg_score": 85.0, "attempts": 3, "trend": 5.0}
        ],
        "overall_avg": 85.0,
        "total_sessions": 3
    }

@router.get("/analytics/cohort/{skill}")
async def get_cohort_analytics(
    skill: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Mocked for now
    return {
        "skill": skill,
        "cohort_avg": 65.0,
        "student_score": 85.0,
        "percentile": 90.0,
        "distribution": [10, 20, 30, 25, 15]
    }

