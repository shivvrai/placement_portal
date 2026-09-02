"""Pydantic schemas — Roadmap & Learning Tasks domain."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RoadmapTaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    week_number: int
    order_in_week: int
    estimated_hours: Optional[float] = None
    status: str
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RoadmapResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    target_role: str
    total_weeks: int
    status: str
    progress_pct: float
    generated_at: datetime
    updated_at: datetime
    tasks: list[RoadmapTaskResponse] = []

    model_config = {"from_attributes": True}


class RoadmapGenerateRequest(BaseModel):
    target_role: str = Field(..., min_length=1)
    weeks: int = Field(12, ge=4, le=52)


class TaskStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(pending|in_progress|completed|skipped)$")
