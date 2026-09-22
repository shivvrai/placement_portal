"""
Copilot API — AI career advisor conversations.
"""

import uuid
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

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
async def send_message(
    conversation_id: uuid.UUID,
    data: NewMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to the copilot and get a streaming text response.
    Returns plain text chunks.
    """
    # copilot_service.add_message_stream returns an AsyncGenerator of strings
    generator = copilot_service.add_message_stream(db, conversation_id, current_user.id, data)
    return StreamingResponse(generator, media_type="text/plain")


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
    """
    Start a Mock Interview and yield the first question.
    """
    generator = copilot_service.start_mock_interview_stream(db, current_user.id, data.role, data.difficulty, data.total_questions)
    return StreamingResponse(generator, media_type="text/plain")


@router.post("/mock-interview/{conversation_id}/respond")
async def respond_mock_interview(
    conversation_id: uuid.UUID,
    data: NewMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Respond to an interview question and yield the evaluation+next question or scorecard.
    """
    generator = copilot_service.respond_mock_interview_stream(db, conversation_id, current_user.id, data)
    return StreamingResponse(generator, media_type="text/plain")


# ─── V3: Context Inspector ──────────────────────────────────────────

@router.get("/conversations/{conversation_id}/context")
async def get_conversation_context(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Debug view: shows what context is currently injected into the copilot
    for this student. Useful for students to understand what the AI knows.
    """
    return await copilot_service.get_context_summary(db, current_user.id)


@router.get("/suggestions")
async def get_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns 3 proactive suggestions based on student's profile.
    Used by the Copilot UI to show action cards.
    """
    return await copilot_service.generate_suggestions(db, current_user.id)

