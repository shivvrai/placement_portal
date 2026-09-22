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


# ─── V2: Remediation Plan Generator ─────────────────────────────────

async def generate_remediation_plan(
    db: AsyncSession,
    session_id: uuid.UUID,
    student_id: uuid.UUID,
) -> list[dict]:
    """
    After a session with score < 60%:
    1. Identify which questions the student got wrong
    2. Map wrong questions to sub-topics
    3. Call Gemini for targeted learning tasks
    4. Create RoadmapTask records
    """
    import json
    import logging
    from app.models.roadmap import Roadmap, RoadmapTask
    from app.services.gemini_client import generate_json_content, is_gemini_configured

    logger = logging.getLogger(__name__)

    # Fetch session with questions
    result = await db.execute(
        select(AssessmentSession)
        .where(
            AssessmentSession.id == session_id,
            AssessmentSession.student_id == student_id,
            AssessmentSession.status == "completed",
        )
        .options(
            selectinload(AssessmentSession.session_questions)
            .selectinload(AssessmentSessionQuestion.question)
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Completed session not found")

    if (session.score or 0) >= 60:
        return []  # No remediation needed

    # Identify wrong questions and their topics/subtopics
    wrong_subtopics = []
    for sq in session.session_questions:
        if not sq.is_correct and sq.question:
            subtopic = sq.question.subtopic or sq.question.concept or session.topic
            if subtopic not in wrong_subtopics:
                wrong_subtopics.append(subtopic)

    if not wrong_subtopics:
        wrong_subtopics = [session.topic]

    # Generate remediation tasks via Gemini
    tasks_data = []
    if is_gemini_configured():
        prompt = f"""A student scored {int(session.score or 0)}% on a {session.topic} assessment.
They struggled with these sub-topics: {', '.join(wrong_subtopics)}.

Generate exactly 5 specific learning tasks to help them improve. Each task should be actionable.
Respond ONLY with valid JSON (no markdown wrapping):
[
    {{
        "title": "Task title",
        "description": "What to do and why",
        "resource_type": "video|article|practice",
        "estimated_hours": 1.5,
        "resource_url": "URL to free resource (YouTube, GeeksForGeeks, LeetCode, etc.)"
    }}
]"""
        system_prompt = "You are a learning advisor. Generate targeted study tasks with real free resource URLs."
        try:
            raw = await generate_json_content(system_prompt, prompt)
            clean = raw.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.startswith("```"):
                clean = clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            tasks_data = json.loads(clean.strip())
        except Exception as e:
            logger.error(f"Failed to generate remediation plan: {e}")
            tasks_data = _fallback_remediation_tasks(session.topic, wrong_subtopics)
    else:
        tasks_data = _fallback_remediation_tasks(session.topic, wrong_subtopics)

    # Find or create an active roadmap for the student
    roadmap_res = await db.execute(
        select(Roadmap)
        .where(Roadmap.student_id == student_id, Roadmap.status == "active")
        .limit(1)
    )
    roadmap = roadmap_res.scalar_one_or_none()
    if not roadmap:
        roadmap = Roadmap(
            student_id=student_id,
            target_role="Skill Improvement",
            total_weeks=4,
            status="active",
        )
        db.add(roadmap)
        await db.flush()

    # Create RoadmapTask records
    created_tasks = []
    for i, task in enumerate(tasks_data[:5]):
        rt = RoadmapTask(
            roadmap_id=roadmap.id,
            title=f"[Remediation] {task.get('title', f'Study {session.topic}')}",
            description=task.get('description', ''),
            week_number=1,
            order_in_week=i + 1,
            estimated_hours=task.get('estimated_hours', 1),
            status="pending",
        )
        db.add(rt)
        created_tasks.append({
            "title": rt.title,
            "description": rt.description,
            "resource_type": task.get("resource_type", "article"),
            "resource_url": task.get("resource_url", ""),
            "estimated_hours": task.get("estimated_hours", 1),
        })

    await db.commit()
    return created_tasks


def _fallback_remediation_tasks(topic: str, subtopics: list[str]) -> list[dict]:
    """Generate fallback tasks when Gemini is unavailable."""
    tasks = []
    for i, sub in enumerate(subtopics[:3]):
        tasks.append({
            "title": f"Review {sub} concepts",
            "description": f"Study the fundamentals of {sub} in {topic}. Focus on understanding core principles before practicing problems.",
            "resource_type": "article",
            "estimated_hours": 1.5,
            "resource_url": f"https://www.geeksforgeeks.org/{sub.lower().replace(' ', '-')}/",
        })
    tasks.append({
        "title": f"Practice {topic} problems",
        "description": f"Solve 10 practice problems on {topic} to reinforce your understanding.",
        "resource_type": "practice",
        "estimated_hours": 2,
        "resource_url": f"https://leetcode.com/tag/{topic.lower().replace(' ', '-')}/",
    })
    tasks.append({
        "title": f"Watch {topic} tutorial video",
        "description": f"Watch a comprehensive video explanation of {topic} concepts.",
        "resource_type": "video",
        "estimated_hours": 1,
        "resource_url": f"https://www.youtube.com/results?search_query={topic.replace(' ', '+')}+tutorial",
    })
    return tasks[:5]


# ─── V2: Recommended Quiz Engine ────────────────────────────────────

async def get_recommended_quizzes(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> list[dict]:
    """
    Cross-reference assessment history with active drive skill requirements.
    Returns top 5 recommended quiz topics with reason and urgency.
    """
    from app.models.user import Student
    from app.models.placement import PlacementDrive
    from app.models.industry import JobSkill
    from app.models.skill import Skill

    # 1. Load student's assessment history (per-topic last score)
    assess_result = await db.execute(
        select(AssessmentSession)
        .where(
            AssessmentSession.student_id == student_id,
            AssessmentSession.status == "completed",
        )
        .order_by(AssessmentSession.completed_at.desc())
    )
    sessions = assess_result.scalars().all()

    # Build per-topic latest score
    topic_scores = {}  # topic -> latest score
    for s in sessions:
        if s.topic not in topic_scores:
            topic_scores[s.topic] = s.score or 0

    # 2. Load student info
    student_res = await db.execute(
        select(Student)
        .where(Student.id == student_id)
        .options(selectinload(Student.department))
    )
    student = student_res.scalar_one_or_none()
    dept_code = student.department.code if student and student.department else ""

    # 3. Get skills from active drives
    drives_res = await db.execute(
        select(PlacementDrive)
        .where(PlacementDrive.status.in_(["upcoming", "open"]))
    )
    drives = drives_res.scalars().all()

    # Filter by department eligibility
    eligible_drives = []
    for d in drives:
        eligible_depts = d.eligible_departments or []
        if not eligible_depts or dept_code.upper() in [ed.upper() for ed in eligible_depts]:
            eligible_drives.append(d)

    # 4. Get in-demand skills
    job_skills_res = await db.execute(
        select(JobSkill)
        .options(selectinload(JobSkill.skill))
    )
    all_job_skills = job_skills_res.scalars().all()

    skill_demand = {}  # skill_name -> count
    for js in all_job_skills:
        if js.skill:
            skill_demand[js.skill.name] = skill_demand.get(js.skill.name, 0) + 1

    # 5. Check which available topics match in-demand skills
    # Load available assessment topics
    topic_result = await db.execute(
        select(AssessmentQuestionBank.topic, func.count(AssessmentQuestionBank.id))
        .where(AssessmentQuestionBank.is_active == True)
        .group_by(AssessmentQuestionBank.topic)
    )
    available_topics = {row[0]: row[1] for row in topic_result.all()}

    # 6. Build recommendations
    recommendations = []
    for topic, q_count in available_topics.items():
        if q_count < 5:
            continue

        # Check if topic matches any in-demand skill
        demand = 0
        matching_skill = None
        for skill_name, count in skill_demand.items():
            if topic.lower() in skill_name.lower() or skill_name.lower() in topic.lower():
                demand = count
                matching_skill = skill_name
                break

        last_score = topic_scores.get(topic)
        urgency = "low"
        reason = f"Available topic with {q_count} questions"

        if demand > 0 and matching_skill:
            if last_score is None:
                urgency = "high"
                reason = f"Required in {demand} active drive(s) — not yet assessed"
            elif last_score < 60:
                urgency = "high"
                reason = f"Scored {int(last_score)}% — needed for {demand} drive(s)"
            elif last_score < 80:
                urgency = "medium"
                reason = f"Room to improve ({int(last_score)}%) — skill in demand"
            else:
                urgency = "low"
                reason = f"Strong score ({int(last_score)}%) — keep it sharp"
        elif last_score is not None and last_score < 60:
            urgency = "medium"
            reason = f"Previous score: {int(last_score)}% — needs improvement"

        recommendations.append({
            "topic": topic,
            "reason": reason,
            "urgency": urgency,
            "last_score": last_score,
            "question_count": q_count,
        })

    # Sort: high urgency first, then by demand
    urgency_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda x: (urgency_order.get(x["urgency"], 3), -(x.get("last_score") or 0)))

    return recommendations[:5]


# ─── V2: Performance Trends ─────────────────────────────────────────

async def get_performance_trends(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> dict:
    """Returns score trends per topic over time."""
    result = await db.execute(
        select(AssessmentSession)
        .where(
            AssessmentSession.student_id == student_id,
            AssessmentSession.status == "completed",
        )
        .order_by(AssessmentSession.completed_at.asc())
    )
    sessions = result.scalars().all()

    trends = {}  # topic -> [{date, score}]
    for s in sessions:
        if s.topic not in trends:
            trends[s.topic] = []
        trends[s.topic].append({
            "date": s.completed_at.isoformat() if s.completed_at else None,
            "score": s.score,
        })

    return {"trends": trends}

