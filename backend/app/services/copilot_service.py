"""
Copilot service — manages AI career advisor conversations.
Calls Gemini API with streaming; falls back to rule-based replies.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.system import CopilotConversation
from app.core.config import get_settings
from app.schemas.copilot import NewMessageRequest
from app.services.prompt_builder import build_system_prompt
from app.services.gemini_client import stream_chat, is_gemini_configured

settings = get_settings()

FALLBACK_REPLIES = [
    "Based on your skill profile, I'd recommend focusing on Python and SQL first — they appear in 80%+ of data roles.",
    "Your CGPA is solid. To strengthen your placement prospects, add 2 data projects with measurable outcomes to your GitHub.",
    "For your target role, the top 3 skills in demand right now are: SQL (window functions), Python (pandas), and data visualisation.",
    "I recommend practicing 1 SQL problem on StrataScratch daily for the next 2 weeks. That's the fastest way to close your SQL gap.",
    "Great question! Your roadmap already covers these skills. Focus on completing Week 3 tasks this week.",
]
_reply_idx = 0


def _fallback_reply() -> str:
    global _reply_idx
    reply = FALLBACK_REPLIES[_reply_idx % len(FALLBACK_REPLIES)]
    _reply_idx += 1
    return reply


async def list_conversations(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> list[CopilotConversation]:
    result = await db.execute(
        select(CopilotConversation)
        .where(CopilotConversation.student_id == student_id)
        .order_by(CopilotConversation.updated_at.desc())
    )
    return result.scalars().all()


async def create_conversation(
    db: AsyncSession,
    student_id: uuid.UUID,
    title: Optional[str] = None,
    initial_message: Optional[str] = None,
) -> CopilotConversation:
    messages = []
    if initial_message:
        now = datetime.now(timezone.utc).isoformat()
        user_msg = {"role": "user", "content": initial_message, "timestamp": now}
        messages.append(user_msg)
        
        # Note: Non-streaming block for creating initial message with content
        if is_gemini_configured():
            system_prompt = await build_system_prompt(db, student_id)
            chunks = []
            async for chunk in stream_chat(system_prompt, [], initial_message):
                chunks.append(chunk)
            reply = "".join(chunks)
        else:
            reply = _fallback_reply()
            
        messages.append({"role": "assistant", "content": reply, "timestamp": now})

    conv = CopilotConversation(
        student_id=student_id,
        title=title or (initial_message[:50] + "..." if initial_message else "New conversation"),
        messages=messages,
        message_count=len(messages),
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


async def add_message_stream(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    student_id: uuid.UUID,
    data: NewMessageRequest,
) -> AsyncGenerator[str, None]:
    """
    Adds user message to DB, calls Gemini for streaming response, yields chunks, 
    and saves the assistant's final response to DB after completion.
    """
    result = await db.execute(
        select(CopilotConversation)
        .where(
            CopilotConversation.id == conversation_id,
            CopilotConversation.student_id == student_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    now = datetime.now(timezone.utc).isoformat()
    messages = list(conv.messages or [])
    messages.append({"role": "user", "content": data.content, "timestamp": now})

    # Prepare streaming
    system_prompt = await build_system_prompt(db, student_id)
    history = [m for m in messages[:-1]] # exclude the new user message

    full_response = ""
    
    if is_gemini_configured():
        async for chunk in stream_chat(system_prompt, history, data.content):
            full_response += chunk
            yield chunk
    else:
        # Fallback
        reply = _fallback_reply()
        full_response = reply
        yield reply

    # Save to DB after stream finishes
    now_resp = datetime.now(timezone.utc).isoformat()
    messages.append({"role": "assistant", "content": full_response, "timestamp": now_resp})

    conv.messages = messages
    conv.message_count = len(messages)
    conv.updated_at = datetime.now(timezone.utc)

    # Auto-title from first message
    if conv.title == "New conversation" and len(messages) >= 2:
        conv.title = data.content[:60] + ("..." if len(data.content) > 60 else "")

    await db.commit()


async def start_mock_interview_stream(
    db: AsyncSession,
    student_id: uuid.UUID,
    role: str,
    difficulty: str,
    total_questions: int,
) -> AsyncGenerator[str, None]:
    
    # 1. Store the persistent config at messages[0]
    config_msg = {
        "role": "system",
        "content": "Interview Config",
        "mock_interview": {
            "role": role,
            "difficulty": difficulty,
            "total_questions": total_questions
        }
    }
    
    conv = CopilotConversation(
        student_id=student_id,
        title=f"[Mock Interview] {role}",
        messages=[config_msg],
        message_count=1,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)

    # 2. Yield the conversation ID as the first chunk so the frontend can bind to it
    yield f":::CONV_ID:{str(conv.id)}:::\n"

    # 3. Stream the first question
    system_prompt = (
        f"You are Alex, an expert technical interviewer for a {difficulty} {role} position. "
        "This is a mock interview. Introduce yourself briefly, and then ask the VERY FIRST technical question. "
        "Ask EXACTLY ONE question. Do not provide the answer."
    )
    
    full_response = ""
    if is_gemini_configured():
        async for chunk in stream_chat(system_prompt, [], "Start the interview."):
            full_response += chunk
            yield chunk
    else:
        reply = "Hi, I'm Alex. To start, can you explain a complex project you worked on recently?"
        full_response = reply
        yield reply

    # 4. Save the assistant's first question
    now_resp = datetime.now(timezone.utc).isoformat()
    messages = list(conv.messages)
    messages.append({"role": "assistant", "content": full_response, "timestamp": now_resp})
    conv.messages = messages
    conv.message_count = len(messages)
    conv.updated_at = datetime.now(timezone.utc)
    await db.commit()


async def respond_mock_interview_stream(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    student_id: uuid.UUID,
    data: NewMessageRequest,
) -> AsyncGenerator[str, None]:
    result = await db.execute(
        select(CopilotConversation)
        .where(
            CopilotConversation.id == conversation_id,
            CopilotConversation.student_id == student_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    messages = list(conv.messages or [])
    
    config = messages[0].get("mock_interview", {})
    role = config.get("role", "Software Engineer")
    difficulty = config.get("difficulty", "Junior SDE")
    total_questions = config.get("total_questions", 4)

    # Count how many times the user has responded:
    current_question = sum(1 for m in messages if m.get("role") == "user") + 1 # +1 for the current answer

    now = datetime.now(timezone.utc).isoformat()
    messages.append({"role": "user", "content": data.content, "timestamp": now})
    
    history = [m for m in messages[1:-1]] # Exclude the system config [0] and the new user msg [-1]

    if current_question < total_questions:
        system_prompt = (
            f"You are Alex, interviewing a candidate for a {difficulty} {role} role. "
            f"We are on question {current_question} of {total_questions}. "
            "EVALUATE the candidate's last answer. You MUST structure your response strictly as follows:\n\n"
            "**Strengths:** <what they did well>\n"
            "**Missing Concepts / Gaps:** <what they missed>\n"
            "**Score:** <1-10>\n\n"
            "After the evaluation, ask EXACTLY ONE next technical question."
        )
    else:
        system_prompt = (
            f"You are Alex, interviewing a candidate for a {difficulty} {role} role. "
            f"The candidate has just answered the final question ({total_questions} of {total_questions}). "
            "DO NOT ask any more questions. "
            "You MUST output exactly a JSON block containing the Final Scorecard evaluating the ENTIRE interview. "
            "Wrap the JSON in ```json and ```. The JSON MUST have exactly these keys: "
            '"Technical Knowledge", "Communication", "Problem Solving", "Overall Readiness", '
            '"Key Strengths" (list of strings), "Areas to Improve" (list of strings), "Recommended Resources" (list of strings).'
        )

    full_response = ""
    if is_gemini_configured():
        async for chunk in stream_chat(system_prompt, history, data.content):
            full_response += chunk
            yield chunk
    else:
        reply = "Evaluation: Good answer. Missing some depth. Score: 7/10.\n\nNext question: What is polymorphism?" if current_question < total_questions else "```json\n{\"Technical Knowledge\": \"Solid\", \"Communication\": \"Clear\", \"Problem Solving\": \"Good approach\", \"Overall Readiness\": \"Ready\", \"Key Strengths\": [\"Clear communication\"], \"Areas to Improve\": [\"Depth\"], \"Recommended Resources\": [\"LeetCode\"]}\n```"
        full_response = reply
        yield reply

    now_resp = datetime.now(timezone.utc).isoformat()
    messages.append({"role": "assistant", "content": full_response, "timestamp": now_resp})

    conv.messages = messages
    conv.message_count = len(messages)
    conv.updated_at = datetime.now(timezone.utc)
    await db.commit()


async def get_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    student_id: uuid.UUID,
) -> CopilotConversation:
    result = await db.execute(
        select(CopilotConversation)
        .where(
            CopilotConversation.id == conversation_id,
            CopilotConversation.student_id == student_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


# ─── V3: Context Inspector ───────────────────────────────────────────

async def get_context_summary(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> dict:
    """Returns a human-readable summary of what context the AI copilot sees."""
    from app.services.prompt_builder import copilot_context_builder
    context_str = await copilot_context_builder.build_full_context(db, student_id)
    lines = context_str.split("\n")
    items = []
    for line in lines:
        if ":" in line:
            key, _, value = line.partition(":")
            items.append({"category": key.strip(), "data": value.strip()})
        elif line.strip():
            items.append({"category": "Info", "data": line.strip()})
    return {
        "context_items": items,
        "raw_context": context_str,
        "token_estimate": len(context_str.split()),
    }


# ─── V3: Proactive Suggestions ──────────────────────────────────────

async def generate_suggestions(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> list[dict]:
    """
    Generate 3 proactive suggestions based on the student's profile.
    Uses heuristic rules (no Gemini call) for instant response.
    """
    from app.models.user import Student
    from app.models.skill import StudentSkill
    from app.models.placement import PlacementDrive, Application
    from app.models.assessment import AssessmentSession
    from sqlalchemy.orm import selectinload

    suggestions = []

    # Load student
    result = await db.execute(
        select(Student)
        .where(Student.id == student_id)
        .options(selectinload(Student.department))
    )
    student = result.scalar_one_or_none()
    if not student:
        return []

    dept_code = student.department.code if student.department else ""

    # 1. Check for high-match eligible drives without application
    try:
        drives_result = await db.execute(
            select(PlacementDrive)
            .where(PlacementDrive.status.in_(["upcoming", "open"]))
            .options(selectinload(PlacementDrive.company))
            .limit(10)
        )
        drives = drives_result.scalars().all()

        apps_result = await db.execute(
            select(Application.drive_id)
            .where(Application.student_id == student_id)
        )
        applied_drive_ids = {row[0] for row in apps_result.all()}

        for d in drives:
            if d.id not in applied_drive_ids:
                eligible = True
                if d.min_cgpa and student.cgpa and float(student.cgpa) < float(d.min_cgpa):
                    eligible = False
                if d.eligible_departments and dept_code.upper() not in [ed.upper() for ed in d.eligible_departments]:
                    eligible = False
                if eligible and d.company:
                    deadline = ""
                    if d.registration_deadline:
                        deadline = f" — apply before {d.registration_deadline.strftime('%b %d')}"
                    suggestions.append({
                        "title": f"Apply to {d.company.name}",
                        "message": f"You're eligible for the {d.title} drive{deadline}. Don't miss out!",
                        "action_label": "View Drive",
                        "action_link": f"/student/drives/{d.id}",
                        "priority": "high",
                    })
                    if len(suggestions) >= 1:
                        break
    except Exception:
        pass

    # 2. Check for unverified skills that are in-demand
    try:
        skill_result = await db.execute(
            select(StudentSkill)
            .where(StudentSkill.student_id == student_id, StudentSkill.is_verified == False)
            .options(selectinload(StudentSkill.skill))
            .limit(5)
        )
        unverified = skill_result.scalars().all()
        if unverified:
            skill = unverified[0]
            suggestions.append({
                "title": f"Verify your {skill.skill.name} skill",
                "message": f"Take a quick assessment to get your {skill.skill.name} skill verified — verified badges boost your profile visibility.",
                "action_label": "Take Assessment",
                "action_link": "/student/assessments",
                "priority": "medium",
            })
    except Exception:
        pass

    # 3. Check application count vs peers
    try:
        app_count_result = await db.execute(
            select(func.count(Application.id))
            .where(Application.student_id == student_id)
        )
        my_apps = app_count_result.scalar() or 0

        peer_avg_result = await db.execute(
            select(func.avg(func.count(Application.id)))
            .where(Application.student_id.in_(
                select(Student.id).where(Student.department_id == student.department_id)
            ))
            .group_by(Application.student_id)
        )
        # Simplified: just check if student has fewer than 3 applications
        if my_apps < 3:
            suggestions.append({
                "title": "Submit more applications",
                "message": f"You've applied to {my_apps} drive(s). Most successful students apply to 4+ drives — check available opportunities.",
                "action_label": "Browse Drives",
                "action_link": "/student/drives",
                "priority": "medium",
            })
    except Exception:
        # Fallback suggestion
        suggestions.append({
            "title": "Complete your profile",
            "message": "A complete profile with verified skills increases your match score with companies.",
            "action_label": "Update Profile",
            "action_link": "/student/profile",
            "priority": "low",
        })

    # 4. Check roadmap progress
    if len(suggestions) < 3:
        try:
            from app.models.roadmap import Roadmap
            roadmap_res = await db.execute(
                select(Roadmap)
                .where(Roadmap.student_id == student_id, Roadmap.status == "active")
                .limit(1)
            )
            roadmap = roadmap_res.scalar_one_or_none()
            if roadmap and float(roadmap.progress_pct) < 50:
                suggestions.append({
                    "title": "Continue your learning roadmap",
                    "message": f"Your {roadmap.target_role} roadmap is {int(roadmap.progress_pct)}% complete. Keep the momentum going!",
                    "action_label": "View Roadmap",
                    "action_link": "/student/roadmap",
                    "priority": "medium",
                })
            elif not roadmap:
                suggestions.append({
                    "title": "Generate a learning roadmap",
                    "message": "Get a personalized AI-generated study plan based on your skill gaps and target role.",
                    "action_label": "Create Roadmap",
                    "action_link": "/student/roadmap",
                    "priority": "medium",
                })
        except Exception:
            pass

    return suggestions[:3]

