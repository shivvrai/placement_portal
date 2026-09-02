"""
Analytics API — TPO & Faculty dashboard data.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import RoleChecker
from app.models.user import User
from app.schemas.analytics import (
    PlacementStatsResponse, DeptPlacementRow,
    SkillDemandRow, CurriculumGapRow,
)
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])

_tpo_or_faculty = RoleChecker(["tpo", "faculty", "hod", "admin"])


@router.get("/placement", response_model=PlacementStatsResponse, summary="Overall placement stats")
async def get_placement_stats(
    academic_year: str = Query("2025-26"),
    current_user: User = Depends(_tpo_or_faculty),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_placement_stats(db, academic_year=academic_year)


@router.get("/departments", response_model=list[DeptPlacementRow], summary="Dept-wise placement breakdown")
async def get_dept_stats(
    current_user: User = Depends(_tpo_or_faculty),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_dept_placement_stats(db)


@router.get("/skill-demand", response_model=list[SkillDemandRow], summary="Skill demand vs campus supply")
async def get_skill_demand(
    current_user: User = Depends(_tpo_or_faculty),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_skill_demand_vs_supply(db)


@router.get("/curriculum-gaps/{department_code}", response_model=list[CurriculumGapRow])
async def get_curriculum_gaps(
    department_code: str,
    semester_number: Optional[int] = Query(None, ge=1, le=10),
    current_user: User = Depends(_tpo_or_faculty),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_curriculum_gaps(db, department_code, semester_number)
