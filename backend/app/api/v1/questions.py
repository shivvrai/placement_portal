import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import RoleChecker, get_current_user
from app.models.user import User
from app.models.assessment import AssessmentQuestionBank

router = APIRouter(prefix="/questions", tags=["Question Bank"])

_authorized = RoleChecker(["tpo", "faculty", "admin"])

@router.get("")
async def list_questions(
    topic: str = None,
    difficulty: str = None,
    question_type: str = None,
    current_user: User = Depends(_authorized),
    db: AsyncSession = Depends(get_db)
):
    query = select(AssessmentQuestionBank)
    if topic:
        query = query.where(func.lower(AssessmentQuestionBank.topic) == topic.lower())
    if difficulty:
        query = query.where(AssessmentQuestionBank.difficulty == difficulty)
    if question_type:
        query = query.where(AssessmentQuestionBank.question_type == question_type)
        
    result = await db.execute(query)
    return result.scalars().all()

@router.post("")
async def create_question(
    data: dict,
    current_user: User = Depends(_authorized),
    db: AsyncSession = Depends(get_db)
):
    question = AssessmentQuestionBank(**data)
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question

@router.patch("/{question_id}")
async def update_question(
    question_id: uuid.UUID,
    data: dict,
    current_user: User = Depends(_authorized),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AssessmentQuestionBank).where(AssessmentQuestionBank.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    for key, value in data.items():
        setattr(question, key, value)
        
    await db.commit()
    await db.refresh(question)
    return question

@router.delete("/{question_id}")
async def delete_question(
    question_id: uuid.UUID,
    current_user: User = Depends(_authorized),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AssessmentQuestionBank).where(AssessmentQuestionBank.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    await db.delete(question)
    await db.commit()
    return {"status": "success", "message": "Question deleted successfully"}

@router.get("/{question_id}/usage-stats")
async def get_question_stats(
    question_id: uuid.UUID,
    current_user: User = Depends(_authorized),
    db: AsyncSession = Depends(get_db)
):
    # Mocked stats for now
    return {
        "times_asked": 42,
        "asked_count": 42,
        "correct_rate": 0.65,
        "avg_correct_rate": 0.65
    }
