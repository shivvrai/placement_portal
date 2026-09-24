import uuid
import random
import subprocess
import json
import asyncio
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
        
    selected_questions = random.sample(list(all_questions), min(10, len(all_questions)))
    
    session = AssessmentSession(
        student_id=student_id,
        topic=topic,
        difficulty=difficulty,
        status="in_progress",
        metadata_col={
            "current_difficulty": difficulty,
            "streak": 0,
            "difficulty_history": [difficulty]
        }
    )
    db.add(session)
    await db.flush() 
    
    for i, q in enumerate(selected_questions):
        session_q = AssessmentSessionQuestion(
            session_id=session.id,
            question_id=q.id,
            order_index=i
        )
        db.add(session_q)
        
    await db.commit()
    
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
        
    correct_count = 0
    total_questions = len(session.session_questions)
    
    student_answers = {ans.question_id: ans.selected_option for ans in data.answers}
    
    meta = dict(session.metadata_col or {})
    streak = meta.get("streak", 0)
    current_difficulty = meta.get("current_difficulty", session.difficulty)
    diff_history = meta.get("difficulty_history", [current_difficulty])
    
    difficulties = ["easy", "medium", "hard", "expert"]
    
    for sq in session.session_questions:
        q_id = sq.question_id
        selected = student_answers.get(q_id)
        
        sq.selected_option = selected
        
        if selected and selected == sq.question.correct_answer:
            sq.is_correct = True
            correct_count += 1
            streak += 1
            if streak >= 3:
                idx = difficulties.index(current_difficulty) if current_difficulty in difficulties else 0
                if idx < len(difficulties) - 1:
                    current_difficulty = difficulties[idx + 1]
                streak = 0
        else:
            sq.is_correct = False
            streak = -1 if streak > 0 else streak - 1
            if streak <= -2:
                idx = difficulties.index(current_difficulty) if current_difficulty in difficulties else 0
                if idx > 0:
                    current_difficulty = difficulties[idx - 1]
                streak = 0
                
        diff_history.append(current_difficulty)

    meta["streak"] = streak
    meta["current_difficulty"] = current_difficulty
    meta["difficulty_history"] = diff_history
    session.metadata_col = meta

    score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
    session.score = score
    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(session)
    
    await update_student_skill_from_assessment(db, student_id, session)
    
    return session

async def submit_code(db: AsyncSession, student_id: uuid.UUID, session_id: uuid.UUID, question_id: uuid.UUID, code: str, language: str) -> dict:
    result = await db.execute(select(AssessmentQuestionBank).where(AssessmentQuestionBank.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    test_cases = question.code_test_cases or []
    if not test_cases:
        return {"passed": 0, "failed": 0, "total": 0, "error": "No test cases found", "time_ms": 0, "results": []}

    passed = 0
    failed = 0
    results = []
    time_ms = 0

    if language.lower() == "python":
        import sys
        for tc in test_cases:
            input_data = tc.get("input", "")
            expected = tc.get("output", "")
            
            start = datetime.now()
            try:
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, "-c", code,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(input=input_data.encode()), timeout=3.0)
                actual = stdout.decode().strip()
                err = stderr.decode().strip()
                
                if proc.returncode == 0 and actual == expected.strip():
                    passed += 1
                    results.append({"input": input_data, "expected": expected, "actual": actual, "passed": True})
                else:
                    failed += 1
                    results.append({"input": input_data, "expected": expected, "actual": actual, "passed": False, "error": err})
            except asyncio.TimeoutError:
                failed += 1
                results.append({"input": input_data, "expected": expected, "actual": "Timeout", "passed": False, "error": "Time Limit Exceeded"})
            except Exception as e:
                failed += 1
                results.append({"input": input_data, "expected": expected, "actual": "Error", "passed": False, "error": str(e)})
            
            time_ms += int((datetime.now() - start).total_seconds() * 1000)
    else:
        return {"passed": 0, "failed": 0, "total": len(test_cases), "error": "Unsupported language", "time_ms": 0, "results": []}

    return {
        "passed": passed,
        "failed": failed,
        "total": len(test_cases),
        "error": None,
        "time_ms": time_ms,
        "results": results
    }
