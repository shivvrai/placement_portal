"""
Analytics API — TPO & Faculty dashboard data.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import RoleChecker, get_current_user
from app.core.audit import record_audit_event
from app.models.user import User
from app.schemas.analytics import (
    PlacementStatsResponse, DeptPlacementRow,
    SkillDemandRow, CurriculumGapRow,
    RecruiterRow, MonthlyTrendRow, PackageBandRow,
    YoYPlacementRow, SectorPieRow, DepartmentOverviewResponse,
)
from app.services import analytics_service
from app.services.accreditation_service import AccreditationService

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


# ─── Accreditation Report ────────────────────────────────────────────────────

@router.get(
    "/accreditation/preview",
    summary="Quick NIRF 1A metrics preview for Analytics page",
)
async def preview_accreditation_metrics(
    academic_year: str = Query("2026-27", description="e.g. 2025-26 or 2026-27"),
    current_user: User = Depends(_tpo_or_faculty),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a quick summary of NIRF 1A placement metrics for the analytics dashboard card.
    Includes: placement %, median CTC, avg CTC, top-10% CTC, gender breakdown.
    """
    svc = AccreditationService(db)
    return await svc.compute_nirf_1a(academic_year)


@router.get(
    "/accreditation/report",
    summary="Full NIRF / NAAC accreditation dossier (JSON or CSV download)",
)
async def get_accreditation_report(
    academic_year: str = Query("2026-27"),
    format: str = Query("json", description="'json' for API response, 'csv' to trigger browser download"),
    current_user: User = Depends(_tpo_or_faculty),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the complete NIRF/NAAC placement report.
    - format=json  → returns structured JSON (NIRF 1A + 1C + NAAC 1.1.3)
    - format=csv   → returns a downloadable CSV file for BoS/IQAC submission
    """
    svc = AccreditationService(db)
    report = await svc.build_full_report(academic_year, format)

    # Audit: log every export so there's a traceable record
    await record_audit_event(
        db=db,
        actor_id=current_user.id,
        event_type="ACCREDITATION_REPORT_EXPORTED",
        resource_type="AccreditationReport",
        resource_id=academic_year,
        details={"year": academic_year, "format": format, "actor_email": current_user.email},
    )
    await db.commit()

    if format == "csv":
        return Response(
            content=report,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="nirf_naac_report_{academic_year}.csv"'
            },
        )
    return report
