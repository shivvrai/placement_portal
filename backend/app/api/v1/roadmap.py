"""
Roadmap API — generate and manage student learning roadmaps.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.roadmap import RoadmapResponse, RoadmapGenerateRequest, TaskStatusUpdateRequest
from app.schemas.common import MessageResponse
from app.services import roadmap_service

router = APIRouter(prefix="/roadmap", tags=["Roadmap"])


@router.get("/me", response_model=RoadmapResponse | None, summary="Get my active roadmap")
@router.get("/students/{student_id}", response_model=RoadmapResponse | None, include_in_schema=False)
async def get_my_roadmap(
    student_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target_id = student_id if student_id else current_user.id
    return await roadmap_service.get_student_roadmap(db, target_id)


@router.post("/me/generate", response_model=RoadmapResponse, status_code=status.HTTP_201_CREATED)
async def generate_my_roadmap(
    data: RoadmapGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new roadmap for the target role. Archives any existing active roadmap."""
    return await roadmap_service.generate_roadmap(db, student_id=current_user.id, data=data)


@router.patch("/tasks/{task_id}", response_model=MessageResponse)
async def update_task_status(
    task_id: uuid.UUID,
    data: TaskStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await roadmap_service.update_task_status(db, task_id=task_id, data=data, student_id=current_user.id)
    return MessageResponse(message=f"Task status updated to '{data.status}'")
