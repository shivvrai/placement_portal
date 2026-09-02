import uuid
import random
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.assessment import AssessmentQuestionBank, AssessmentSession, AssessmentSessionQuestion
from app.schemas.assessment import AssessmentSubmitRequest
from app.services.skill_profile_service import update_student_skill_from_assessment


async def create_assessment_session(
    db: AsyncSession, student_id: uuid.UUID, topic: str, difficulty: str
) -> AssessmentSession:
    # 1. Fetch available questions for the topic and difficulty
    query = (
        select(AssessmentQuestionBank)
        .where(
            func.lower(AssessmentQuestionBank.topic) == topic.lower(),
            AssessmentQuestionBank.difficulty == difficulty,
            AssessmentQuestionBank.is_active == True
        )
    )
    result = await db.execute(query)
    all_questions = result.scalars().all()
    
    if len(all_questions) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient questions for topic '{topic}' at '{difficulty}' difficulty."
        )
        
    # Select up to 10 questions randomly
    selected_questions = random.sample(list(all_questions), min(10, len(all_questions)))
    
    # 2. Create session
    session = AssessmentSession(
        student_id=student_id,
        topic=topic,
        difficulty=difficulty,
        status="in_progress"
    )
    db.add(session)
    await db.flush() # flush to get session.id
    
    # 3. Create session questions
    for i, q in enumerate(selected_questions):
        session_q = AssessmentSessionQuestion(
            session_id=session.id,
            question_id=q.id,
            order_index=i
        )
        db.add(session_q)
        
    await db.commit()
    
    # Reload session with questions and their bank data
    result = await db.execute(
        select(AssessmentSession)
        .where(AssessmentSession.id == session.id)
        .options(
            selectinload(AssessmentSession.session_questions)
            .selectinload(AssessmentSessionQuestion.question)
        )
    )
    return result.scalar_one()


async def submit_assessment(
    db: AsyncSession, student_id: uuid.UUID, session_id: uuid.UUID, data: AssessmentSubmitRequest
) -> AssessmentSession:
    # 1. Fetch session
    result = await db.execute(
        select(AssessmentSession)
        .where(
            AssessmentSession.id == session_id,
            AssessmentSession.student_id == student_id
        )
        .options(
            selectinload(AssessmentSession.session_questions)
            .selectinload(AssessmentSessionQuestion.question)
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment session not found")
        
    if session.status == "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assessment already submitted")
        
    # 2. Evaluate answers
    correct_count = 0
    total_questions = len(session.session_questions)
    
    # Create map of student's answers
    student_answers = {ans.question_id: ans.selected_option for ans in data.answers}
    
    for sq in session.session_questions:
        q_id = sq.question_id
        selected = student_answers.get(q_id)
        
        sq.selected_option = selected
        
        if selected and selected == sq.question.correct_answer:
            sq.is_correct = True
            correct_count += 1
        else:
            sq.is_correct = False

    # 3. Calculate score
    score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
    session.score = score
    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(session)
    
    # 4. Trigger skill profile update and skill gap recalculation
    await update_student_skill_from_assessment(db, student_id, session)
    
    return session
