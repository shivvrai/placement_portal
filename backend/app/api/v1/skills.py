"""
Skills API — skill taxonomy lookup and search.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.skill import Skill
from app.schemas.skill import SkillResponse

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("", response_model=list[SkillResponse], summary="List all skills")
async def list_skills(
    category: Optional[str] = Query(None, description="Filter by category e.g. language"),
    domain: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Skill).order_by(Skill.name).limit(limit)
    if category:
        q = q.where(Skill.category == category)
    if domain:
        q = q.where(Skill.domain == domain)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/search", response_model=list[SkillResponse], summary="Search skills by name")
async def search_skills(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Skill)
        .where(func.lower(Skill.name).contains(q.lower()))
        .order_by(Skill.name)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()
