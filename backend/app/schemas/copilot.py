"""Pydantic schemas — AI Copilot conversation domain."""

import uuid
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: Optional[datetime] = None


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str] = None
    messages: list[ChatMessage] = []
    message_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationSummary(BaseModel):
    id: uuid.UUID
    title: Optional[str] = None
    message_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NewMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class NewConversationRequest(BaseModel):
    title: Optional[str] = None
    initial_message: Optional[str] = None
