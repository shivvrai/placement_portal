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
