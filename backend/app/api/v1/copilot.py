"""
Copilot API — AI career advisor conversations + Mock Interview.
Uses Server-Sent Events (text/event-stream) for streaming responses.
"""

import uuid
from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.middleware.rate_limit import limiter

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.copilot import (
    ConversationResponse, ConversationSummary,
    NewMessageRequest, NewConversationRequest, ChatMessage,
)
from pydantic import BaseModel
from app.services import copilot_service

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])


def _conv_to_response(conv) -> ConversationResponse:
    messages = [
        ChatMessage(role=m["role"], content=m["content"], timestamp=m.get("timestamp"))
        for m in (conv.messages or [])
        if m.get("role") in ("user", "assistant")
    ]
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        messages=messages,
        message_count=conv.message_count,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
    )


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    convs = await copilot_service.list_conversations(db, student_id=current_user.id)
    return [
        ConversationSummary(
            id=c.id, title=c.title,
            message_count=c.message_count,
            created_at=c.created_at, updated_at=c.updated_at,
        )
        for c in convs
    ]


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    data: NewConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await copilot_service.create_conversation(
        db,
        student_id=current_user.id,
        title=data.title,
        initial_message=data.initial_message,
    )
    return _conv_to_response(conv)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await copilot_service.get_conversation(db, conversation_id, current_user.id)
    return _conv_to_response(conv)


@router.post("/conversations/{conversation_id}/messages")
@limiter.limit("30/hour")
async def send_message(
    request: Request,
    conversation_id: uuid.UUID,
    data: NewMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to the copilot and get a streaming SSE response.
    Uses text/event-stream for incremental delivery.
    """
    async def sse_generator():
        async for chunk in copilot_service.add_message_stream(db, conversation_id, current_user.id, data):
            # SSE format: data: <chunk>\n\n
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


# ─── Chat Stream (POST /copilot/chat/stream) — V3 endpoint ────────
@router.post("/chat/stream")
@limiter.limit("30/hour")
async def chat_stream(
    request: Request,
    data: NewMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    V3 streaming endpoint: POST /copilot/chat/stream
    Automatically creates a conversation if needed, then streams SSE.
    """
    async def sse_generator():
        # Auto-create or reuse latest conversation
        convs = await copilot_service.list_conversations(db, student_id=current_user.id)
        if convs:
            conv = convs[0]
        else:
            conv = await copilot_service.create_conversation(db, student_id=current_user.id)

        yield f"data: {{\"conversation_id\": \"{conv.id}\"}}\n\n"

        async for chunk in copilot_service.add_message_stream(db, conv.id, current_user.id, data):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


# ─── Mock Interview ──────────────────────────────────────────────────

class MockInterviewStartRequest(BaseModel):
    role: str
    difficulty: str
    total_questions: int


@router.post("/mock-interview/start")
async def start_mock_interview(
    data: MockInterviewStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a Mock Interview and yield the first question via SSE."""
    async def sse_generator():
        async for chunk in copilot_service.start_mock_interview_stream(
            db, current_user.id, data.role, data.difficulty, data.total_questions
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.post("/mock-interview/{conversation_id}/respond")
async def respond_mock_interview(
    conversation_id: uuid.UUID,
    data: NewMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Respond to an interview question via SSE — evaluation+next question or scorecard."""
    async def sse_generator():
        async for chunk in copilot_service.respond_mock_interview_stream(
            db, conversation_id, current_user.id, data
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.post("/mock-interview/{conversation_id}/complete")
async def complete_mock_interview(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    POST /mock-interviews/{session_id}/complete — generate final scorecard
    for a mock interview session that is still in progress.
    """
    result = await copilot_service.complete_mock_interview(db, conversation_id, current_user.id)
    return result
