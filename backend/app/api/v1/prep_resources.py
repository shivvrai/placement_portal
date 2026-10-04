"""
Placement Prep Resources API — resource library, collections, progress tracking.

Sprint 3 — Sakshi Kumari

Endpoints:
  POST   /prep/resources              — Create prep resource (TPO)
  GET    /prep/resources              — List & filter resources
  GET    /prep/resources/{id}         — Get resource detail
  POST   /prep/resources/{id}/upvote  — Upvote a resource
  POST   /prep/collections            — Create collection (TPO)
  GET    /prep/collections            — List collections
  POST   /prep/progress/{resource_id} — Update my prep progress
  GET    /prep/progress/mine          — Get my progress across resources
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker, get_current_student
from app.models.user import User
from app.schemas.sakshi_sprint3 import (
    PrepResourceCreate, PrepResourceResponse,
    PrepCollectionCreate, PrepCollectionResponse,
    PrepProgressUpdate, PrepProgressResponse,
)
from app.schemas.common import MessageResponse, PaginatedResponse, PaginationMeta
from app.services import sakshi_sprint3_service as svc

router = APIRouter(prefix="/prep", tags=["Placement Prep Resources"])

_tpo_admin = RoleChecker(["tpo", "admin"])
_any_user = RoleChecker(["student", "tpo", "admin", "faculty", "hod"])


@router.post("/resources", response_model=PrepResourceResponse, summary="Create prep resource")
async def create_resource(
    data: PrepResourceCreate,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    resource = await svc.create_prep_resource(db, data, current_user.id)
    return PrepResourceResponse(
        id=resource.id, title=resource.title, description=resource.description,
        category=resource.category, resource_type=resource.resource_type,
        difficulty=resource.difficulty, url=resource.url, content=resource.content,
        tags=resource.tags or [], target_companies=resource.target_companies or [],
        estimated_minutes=resource.estimated_minutes,
        upvotes=resource.upvotes, view_count=resource.view_count,
        created_at=resource.created_at,
    )


@router.get("/resources", response_model=PaginatedResponse, summary="List prep resources")
async def list_resources(
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(_any_user),
    db: AsyncSession = Depends(get_db),
):
    resources, total = await svc.list_prep_resources(db, category, difficulty, resource_type, search, page, per_page)
    items = [PrepResourceResponse(
        id=r.id, title=r.title, description=r.description,
        category=r.category, resource_type=r.resource_type,
        difficulty=r.difficulty, url=r.url, content=r.content,
        tags=r.tags or [], target_companies=r.target_companies or [],
        estimated_minutes=r.estimated_minutes,
        author_name=f"{r.creator.first_name} {r.creator.last_name}" if r.creator else None,
        upvotes=r.upvotes, view_count=r.view_count,
        created_at=r.created_at,
    ) for r in resources]
    return PaginatedResponse(
        data=[i.model_dump() for i in items],
        pagination=PaginationMeta(page=page, per_page=per_page, total=total),
    )


@router.get("/resources/{resource_id}", response_model=PrepResourceResponse, summary="Get resource detail")
async def get_resource(
    resource_id: uuid.UUID,
    current_user: User = Depends(_any_user),
    db: AsyncSession = Depends(get_db),
):
    r = await svc.get_prep_resource(db, resource_id)
    return PrepResourceResponse(
        id=r.id, title=r.title, description=r.description,
        category=r.category, resource_type=r.resource_type,
        difficulty=r.difficulty, url=r.url, content=r.content,
        tags=r.tags or [], target_companies=r.target_companies or [],
        estimated_minutes=r.estimated_minutes,
        author_name=f"{r.creator.first_name} {r.creator.last_name}" if r.creator else None,
        is_premium=r.is_premium, upvotes=r.upvotes, view_count=r.view_count,
        created_at=r.created_at,
    )


@router.post("/resources/{resource_id}/upvote", response_model=MessageResponse, summary="Upvote resource")
async def upvote(
    resource_id: uuid.UUID,
    current_user: User = Depends(_any_user),
    db: AsyncSession = Depends(get_db),
):
    r = await svc.upvote_resource(db, resource_id)
    return MessageResponse(message=f"Upvoted! Total: {r.upvotes}")


@router.post("/collections", response_model=PrepCollectionResponse, summary="Create collection")
async def create_collection(
    data: PrepCollectionCreate,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    c = await svc.create_collection(db, data, current_user.id)
    return PrepCollectionResponse(
        id=c.id, title=c.title, description=c.description,
        resource_ids=c.resource_ids or [], target_role=c.target_role,
        is_official=c.is_official, created_at=c.created_at,
    )


@router.get("/collections", response_model=list[PrepCollectionResponse], summary="List collections")
async def list_collections(
    current_user: User = Depends(_any_user),
    db: AsyncSession = Depends(get_db),
):
    collections = await svc.list_collections(db)
    return [PrepCollectionResponse(
        id=c.id, title=c.title, description=c.description,
        resource_ids=c.resource_ids or [], target_role=c.target_role,
        is_official=c.is_official, created_at=c.created_at,
    ) for c in collections]


@router.post("/progress/{resource_id}", response_model=PrepProgressResponse, summary="Update my prep progress")
async def update_progress(
    resource_id: uuid.UUID,
    data: PrepProgressUpdate,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    p = await svc.update_prep_progress(db, current_user.id, resource_id, data)
    return PrepProgressResponse(
        id=p.id, student_id=p.student_id, resource_id=p.resource_id,
        resource_title=p.resource.title if p.resource else None,
        status=p.status, progress_pct=p.progress_pct,
        time_spent_minutes=p.time_spent_minutes, notes=p.notes,
        completed_at=p.completed_at,
    )


@router.get("/progress/mine", response_model=list[PrepProgressResponse], summary="My prep progress")
async def my_progress(
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    progress_list = await svc.get_student_prep_progress(db, current_user.id)
    return [PrepProgressResponse(
        id=p.id, student_id=p.student_id, resource_id=p.resource_id,
        resource_title=p.resource.title if p.resource else None,
        status=p.status, progress_pct=p.progress_pct,
        time_spent_minutes=p.time_spent_minutes, notes=p.notes,
        completed_at=p.completed_at,
    ) for p in progress_list]
