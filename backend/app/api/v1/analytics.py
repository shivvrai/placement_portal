"""
Analytics API — TPO & Faculty dashboard data.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import RoleChecker, get_current_user
from app.models.user import User
from app.schemas.analytics import (
    PlacementStatsResponse, DeptPlacementRow,
    SkillDemandRow, CurriculumGapRow,
    RecruiterRow, MonthlyTrendRow, PackageBandRow,
    YoYPlacementRow, SectorPieRow, DepartmentOverviewResponse,
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
@router.get("/placement/departments", response_model=list[DeptPlacementRow], summary="Dept-wise placement breakdown")
async def get_dept_stats(
    current_user: User = Depends(_tpo_or_faculty),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_dept_placement_stats(db)


@router.get("/top-recruiters", response_model=list[RecruiterRow], summary="Top recruiters by offers")
async def get_top_recruiters(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(_tpo_or_faculty),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_top_recruiters(db, limit=limit)


@router.get("/trends", response_model=list[MonthlyTrendRow], summary="Monthly placement & offer trends")
async def get_placement_trends(
    academic_year: str = Query("2025-26"),
    current_user: User = Depends(_tpo_or_faculty),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_monthly_trends(db, academic_year=academic_year)


@router.get("/package-distribution", response_model=list[PackageBandRow], summary="Salary package band distribution")
async def get_package_distribution(
    current_user: User = Depends(_tpo_or_faculty),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_package_distribution(db)


@router.get("/yoy", response_model=list[YoYPlacementRow], summary="Year-over-year placement performance")
async def get_yoy_stats(
    current_user: User = Depends(_tpo_or_faculty),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_yoy_stats(db)


@router.get("/sectors", response_model=list[SectorPieRow], summary="Placement breakdown by company sector")
async def get_sector_distribution(
    current_user: User = Depends(_tpo_or_faculty),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_sector_distribution(db)



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


@router.get("/departments/{department_code}", response_model=DepartmentOverviewResponse, summary="Department analytics overview (Faculty Dashboard)")
async def get_department_overview(
    department_code: str,
    current_user: User = Depends(_tpo_or_faculty),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.get_department_overview(db, department_code)


@router.get("/skills/trends", summary="Skill demand trend classification: surging, stable, declining")
async def get_skill_trends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns skill demand trend classification: surging, stable, declining.
    Accessible to both students and TPO.
    Cached for 6 hours.
    """
    return await analytics_service.compute_skill_trends(db)
