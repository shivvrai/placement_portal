"""
Copilot service — manages AI career advisor conversations.
Calls Gemini API with streaming; falls back to rule-based replies.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.system import CopilotConversation
from app.core.config import get_settings
from app.schemas.copilot import NewMessageRequest
from app.services.prompt_builder import build_system_prompt
from app.services.gemini_client import stream_chat, is_gemini_configured

settings = get_settings()

# ─── Context-aware fallback replies ──────────────────────────────────
FALLBACK_REPLIES = [
    "Based on your skill profile, I'd recommend focusing on **Python** and **SQL** first — they appear in 80%+ of data roles. "
    "Start with a small project: build an ETL pipeline that pulls data from a public API, transforms it with pandas, and loads it into a SQLite database.",
    "Your CGPA is solid. To strengthen your placement prospects, add **2 data projects** with measurable outcomes to your GitHub. "
    "Projects with real datasets (Kaggle competitions, government open data) stand out to recruiters.",
    "For your target role, the top 3 skills in demand right now are: **SQL** (window functions & CTEs), **Python** (pandas + data cleaning), "
    "and **data visualisation** (Matplotlib/Seaborn or Tableau). Focus on these in order of priority.",
    "I recommend practicing **1 SQL problem on StrataScratch or HackerRank daily** for the next 2 weeks. "
    "That's the fastest way to close your SQL gap. Focus on JOIN patterns, subqueries, and window functions.",
    "Great question! Here's a step-by-step approach:\n\n"
    "1. **Identify your target companies** — check your Placement Drives page for upcoming drives\n"
    "2. **Map required skills** — use your Skill Gap analysis to see what you're missing\n"
    "3. **Create a 2-week plan** — dedicate 2 hours daily to the highest-priority gap\n"
    "4. **Practice mock interviews** — use the Mock Interview feature here to prepare\n\n"
    "Your roadmap already covers some of these. Focus on completing the current week's tasks first.",
    "For interview preparation, I recommend this structured approach:\n\n"
    "- **Week 1-2**: Data Structures (arrays, linked lists, trees, graphs)\n"
    "- **Week 3**: Algorithms (sorting, searching, dynamic programming)\n"
    "- **Week 4**: System Design basics (for SDE roles) or SQL advanced (for data roles)\n\n"
    "Practice at least 2 problems daily on LeetCode, focusing on medium difficulty.",
]
_reply_idx = 0


def _fallback_reply(user_message: str = "") -> str:
    """
    Return deterministic, useful career guidance when Gemini is unavailable.
    Attempts basic keyword matching for relevance.
    """
    global _reply_idx
    msg_lower = user_message.lower() if user_message else ""

    # Keyword-based relevance matching for better fallback quality
    if any(kw in msg_lower for kw in ["interview", "prepare", "mock"]):
        return FALLBACK_REPLIES[5]
    if any(kw in msg_lower for kw in ["skill", "gap", "missing", "learn"]):
        return FALLBACK_REPLIES[2]
    if any(kw in msg_lower for kw in ["project", "github", "portfolio"]):
        return FALLBACK_REPLIES[1]
    if any(kw in msg_lower for kw in ["sql", "database", "query"]):
        return FALLBACK_REPLIES[3]
    if any(kw in msg_lower for kw in ["plan", "roadmap", "strategy", "prepare"]):
        return FALLBACK_REPLIES[4]

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
            reply = _fallback_reply(initial_message)

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
    Falls back to deterministic career advice if Gemini is unavailable.
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
    history = [m for m in messages[:-1]]  # exclude the new user message

    full_response = ""

    if is_gemini_configured():
        try:
            async for chunk in stream_chat(system_prompt, history, data.content):
                full_response += chunk
                yield chunk
        except Exception:
            # Gemini failed mid-stream — provide fallback
            if not full_response:
                fallback = _fallback_reply(data.content)
                full_response = fallback
                yield fallback
    else:
        # Fallback — no Gemini key
        reply = _fallback_reply(data.content)
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
            "total_questions": total_questions,
            "state": "intro",
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

    # 3. Stream the first question (intro → technical transition)
    system_prompt = (
        f"You are Alex, an expert technical interviewer for a {difficulty} {role} position. "
        "This is a mock interview. Introduce yourself briefly, and then ask the VERY FIRST technical question. "
        "Ask EXACTLY ONE question. Do not provide the answer."
    )

    full_response = ""
    if is_gemini_configured():
        try:
            async for chunk in stream_chat(system_prompt, [], "Start the interview."):
                full_response += chunk
                yield chunk
        except Exception:
            reply = f"Hi, I'm Alex, your interviewer for the {difficulty} {role} position. Let's get started!\n\n**Question 1:** Can you explain a complex project you worked on recently and what technical challenges you faced?"
            full_response = reply
            yield reply
    else:
        reply = f"Hi, I'm Alex, your interviewer for the {difficulty} {role} position. Let's get started!\n\n**Question 1:** Can you explain a complex project you worked on recently and what technical challenges you faced?"
        full_response = reply
        yield reply

    # 4. Save the assistant's first question and update state to technical
    now_resp = datetime.now(timezone.utc).isoformat()
    messages = list(conv.messages)
    messages.append({"role": "assistant", "content": full_response, "timestamp": now_resp})
    # Update state: intro -> technical
    messages[0]["mock_interview"]["state"] = "technical"
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
    current_state = config.get("state", "technical")

    # Count how many times the user has responded:
    current_question = sum(1 for m in messages if m.get("role") == "user") + 1  # +1 for the current answer

    now = datetime.now(timezone.utc).isoformat()
    messages.append({"role": "user", "content": data.content, "timestamp": now})

    history = [m for m in messages[1:-1]]  # Exclude the system config [0] and the new user msg [-1]

    # Determine next state
    is_behavioral = current_question > max(1, total_questions - 1)
    is_final = current_question >= total_questions

    if not is_final:
        q_type = "behavioral" if is_behavioral else "technical"
        system_prompt = (
            f"You are Alex, interviewing a candidate for a {difficulty} {role} role. "
            f"We are on question {current_question} of {total_questions} ({q_type} round). "
            "EVALUATE the candidate's last answer. You MUST structure your response strictly as follows:\n\n"
            "**Strengths:** <what they did well>\n"
            "**Missing Concepts / Gaps:** <what they missed>\n"
            "**Score:** <1-10>\n\n"
            f"After the evaluation, ask EXACTLY ONE next {q_type} question."
        )
        next_state = "behavioral" if is_behavioral else "technical"
    else:
        system_prompt = (
            f"You are Alex, interviewing a candidate for a {difficulty} {role} role. "
            f"The candidate has just answered the final question ({total_questions} of {total_questions}). "
            "DO NOT ask any more questions. "
            "You MUST output exactly a JSON block containing the Final Scorecard evaluating the ENTIRE interview. "
            "Wrap the JSON in ```json and ```. The JSON MUST have exactly these keys: "
            '"technical_correctness" (score 1-10), "communication_clarity" (score 1-10), '
            '"response_depth" (score 1-10), "problem_solving" (score 1-10), '
            '"overall_readiness" (string like "Ready" / "Almost Ready" / "Needs Work"), '
            '"filler_word_estimate" (string, e.g. "Low — text-based estimate"), '
            '"response_pace_estimate" (string, e.g. "Moderate — text-based estimate"), '
            '"key_strengths" (list of strings), "areas_to_improve" (list of strings), '
            '"actionable_recommendations" (list of strings).\n\n'
            "NOTE: Filler word count and response pace are text-based estimates only, not measured from audio."
        )
        next_state = "completed"

    full_response = ""
    if is_gemini_configured():
        try:
            async for chunk in stream_chat(system_prompt, history, data.content):
                full_response += chunk
                yield chunk
        except Exception:
            if is_final:
                reply = _fallback_scorecard()
            else:
                reply = f"**Strengths:** Good attempt with relevant concepts.\n**Missing Concepts / Gaps:** Consider exploring edge cases and trade-offs.\n**Score:** 6/10\n\n**Next Question:** How would you design a system that handles {role.lower()}-related workloads at scale?"
            full_response = reply
            yield reply
    else:
        if is_final:
            reply = _fallback_scorecard()
        else:
            reply = f"**Strengths:** Good attempt with relevant concepts.\n**Missing Concepts / Gaps:** Consider exploring edge cases and trade-offs.\n**Score:** 6/10\n\n**Next Question:** How would you design a system that handles {role.lower()}-related workloads at scale?"
        full_response = reply
        yield reply

    now_resp = datetime.now(timezone.utc).isoformat()
    messages.append({"role": "assistant", "content": full_response, "timestamp": now_resp})

    # Update state machine
    messages[0]["mock_interview"]["state"] = next_state

    conv.messages = messages
    conv.message_count = len(messages)
    conv.updated_at = datetime.now(timezone.utc)
    await db.commit()


def _fallback_scorecard() -> str:
    """Deterministic scorecard when Gemini is unavailable."""
    return (
        '```json\n'
        '{\n'
        '  "technical_correctness": 7,\n'
        '  "communication_clarity": 7,\n'
        '  "response_depth": 6,\n'
        '  "problem_solving": 7,\n'
        '  "overall_readiness": "Almost Ready",\n'
        '  "filler_word_estimate": "Low — text-based estimate only",\n'
        '  "response_pace_estimate": "Moderate — text-based estimate only",\n'
        '  "key_strengths": ["Clear communication", "Relevant examples used", "Good problem decomposition"],\n'
        '  "areas_to_improve": ["Add more depth to technical explanations", "Discuss trade-offs and edge cases", "Practice system design questions"],\n'
        '  "actionable_recommendations": ["Practice 2 LeetCode medium problems daily", "Study system design with Designing Data-Intensive Applications", "Review common behavioral question frameworks (STAR method)"]\n'
        '}\n'
        '```'
    )


async def complete_mock_interview(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    student_id: uuid.UUID,
) -> dict:
    """
    Complete a mock interview session and generate the final scorecard.
    Used by POST /mock-interview/{id}/complete.
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    messages = list(conv.messages or [])
    config = messages[0].get("mock_interview", {})

    if config.get("state") == "completed":
        # Already completed — return existing transcript
        transcript = [
            {"role": m["role"], "content": m["content"], "timestamp": m.get("timestamp")}
            for m in messages if m.get("role") in ("user", "assistant")
        ]
        return {
            "status": "completed",
            "session_id": str(conv.id),
            "role": config.get("role"),
            "difficulty": config.get("difficulty"),
            "total_questions": config.get("total_questions"),
            "transcript": transcript,
        }

    # Mark as completed
    messages[0]["mock_interview"]["state"] = "completed"
    conv.messages = messages
    conv.updated_at = datetime.now(timezone.utc)
    await db.commit()

    transcript = [
        {"role": m["role"], "content": m["content"], "timestamp": m.get("timestamp")}
        for m in messages if m.get("role") in ("user", "assistant")
    ]

    return {
        "status": "completed",
        "session_id": str(conv.id),
        "role": config.get("role"),
        "difficulty": config.get("difficulty"),
        "total_questions": config.get("total_questions"),
        "transcript": transcript,
    }


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
