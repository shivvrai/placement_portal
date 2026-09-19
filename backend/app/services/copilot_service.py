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
