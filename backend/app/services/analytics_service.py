"""
Analytics service — aggregation queries for TPO & Faculty dashboards.
"""

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, distinct
from sqlalchemy.orm import joinedload

from app.models.user import Student, Department
from app.models.placement import Application, PlacementOutcome, PlacementDrive
from app.models.industry import Company, Job, JobSkill, IndustrySkillTrend
from app.models.skill import Skill, CurriculumSkill, StudentSkill
from app.models.academic import Subject
from app.schemas.analytics import (
    PlacementStatsResponse, DeptPlacementRow, MonthlyTrendRow,
    RecruiterRow, PackageBandRow, SkillDemandRow, CurriculumGapRow,
)


async def get_placement_stats(
    db: AsyncSession,
    academic_year: str = "2025-26",
) -> PlacementStatsResponse:
    """Aggregate placement statistics for the given academic year."""

    total_students = (await db.execute(select(func.count(Student.id)))).scalar_one()

    placed_result = await db.execute(
        select(func.count(PlacementOutcome.id))
        .where(PlacementOutcome.academic_year == academic_year)
    )
    placed = placed_result.scalar_one() or 0

    companies_result = await db.execute(
        select(func.count(distinct(PlacementDrive.company_id)))
        .where(PlacementDrive.academic_year == academic_year)
    )
    companies_visited = companies_result.scalar_one() or 0

    offers_result = await db.execute(
        select(func.count(Application.id))
        .where(Application.status == "selected")
    )
    offers_released = offers_result.scalar_one() or 0

    avg_result = await db.execute(
        select(func.avg(PlacementOutcome.salary_ctc))
        .where(PlacementOutcome.academic_year == academic_year)
    )
    avg_package = avg_result.scalar_one()

    max_result = await db.execute(
        select(func.max(PlacementOutcome.salary_ctc))
        .where(PlacementOutcome.academic_year == academic_year)
    )
    highest_package = max_result.scalar_one()

    return PlacementStatsResponse(
        academic_year=academic_year,
        total_students=total_students,
        registered=total_students,
        placed=placed,
        placement_pct=round(placed / total_students * 100, 1) if total_students else 0.0,
        avg_package=float(avg_package) if avg_package else None,
        median_package=None,  # complex query — skip for now
        highest_package=float(highest_package) if highest_package else None,
        companies_visited=companies_visited,
        offers_released=offers_released,
    )


async def get_dept_placement_stats(db: AsyncSession) -> list[DeptPlacementRow]:
    """Per-department placement breakdown."""
    depts_result = await db.execute(select(Department))
    depts = depts_result.scalars().all()

    rows = []
    for dept in depts:
        total = (await db.execute(
            select(func.count(Student.id)).where(Student.department_id == dept.id)
        )).scalar_one()

        placed = (await db.execute(
            select(func.count(PlacementOutcome.id))
            .join(Student, PlacementOutcome.student_id == Student.id)
            .where(Student.department_id == dept.id)
        )).scalar_one()

        avg_pkg_result = (await db.execute(
            select(func.avg(PlacementOutcome.salary_ctc))
            .join(Student, PlacementOutcome.student_id == Student.id)
            .where(Student.department_id == dept.id)
        )).scalar_one()

        if total > 0:
            rows.append(DeptPlacementRow(
                department_code=dept.code,
                department_name=dept.name,
                total=total,
                placed=placed,
                placement_pct=round(placed / total * 100, 1),
                avg_package=float(avg_pkg_result) if avg_pkg_result else None,
            ))

    return rows


async def get_skill_demand_vs_supply(db: AsyncSession) -> list[SkillDemandRow]:
    """Compare industry demand vs student supply for top skills."""
    # Count student skill occurrences
    student_skill_counts = await db.execute(
        select(Skill.name, func.count(StudentSkill.id).label("supply_cnt"))
        .join(StudentSkill, Skill.id == StudentSkill.skill_id)
        .group_by(Skill.name)
        .order_by(func.count(StudentSkill.id).desc())
        .limit(15)
    )
    supply_map = {r.name: r.supply_cnt for r in student_skill_counts}

    # Count job skill demand
    job_skill_counts = await db.execute(
        select(Skill.name, func.count(JobSkill.id).label("demand_cnt"))
        .join(JobSkill, Skill.id == JobSkill.skill_id)
        .join(Job, JobSkill.job_id == Job.id)
        .where(Job.is_active == True)  # noqa: E712
        .group_by(Skill.name)
        .order_by(func.count(JobSkill.id).desc())
        .limit(15)
    )
    demand_map = {r.name: r.demand_cnt for r in job_skill_counts}

    all_skills = set(supply_map) | set(demand_map)
    total_students = (await db.execute(select(func.count(Student.id)))).scalar_one() or 1
    total_jobs = (await db.execute(select(func.count(Job.id)).where(Job.is_active == True))).scalar_one() or 1  # noqa: E712

    rows = []
    for skill in all_skills:
        demand_pct = round(demand_map.get(skill, 0) / total_jobs * 100, 1)
        supply_pct = round(supply_map.get(skill, 0) / total_students * 100, 1)
        rows.append(SkillDemandRow(
            skill_name=skill,
            demand_pct=demand_pct,
            supply_pct=supply_pct,
            gap=round(demand_pct - supply_pct, 1),
        ))

    return sorted(rows, key=lambda r: r.gap, reverse=True)[:12]


async def get_curriculum_gaps(
    db: AsyncSession,
    department_code: str,
    semester_number: Optional[int] = None,
) -> list[CurriculumGapRow]:
    """Compute curriculum coverage gap per subject."""
    dept_result = await db.execute(
        select(Department).where(Department.code == department_code)
    )
    dept = dept_result.scalar_one_or_none()
    if not dept:
        return []

    subjects_q = select(Subject).where(Subject.department_id == dept.id)
    if semester_number:
        subjects_q = subjects_q.where(Subject.semester_number == semester_number)

    subjects = (await db.execute(subjects_q)).scalars().all()

    rows = []
    for subject in subjects:
        # How many curriculum skills mapped
        mapped_count = (await db.execute(
            select(func.count(CurriculumSkill.id))
            .where(CurriculumSkill.subject_id == subject.id)
        )).scalar_one()

        # How many of those are in demand
        in_demand = (await db.execute(
            select(func.count(CurriculumSkill.id))
            .join(JobSkill, CurriculumSkill.skill_id == JobSkill.skill_id)
            .where(CurriculumSkill.subject_id == subject.id)
        )).scalar_one()

        demand_score = round(in_demand / mapped_count * 100, 1) if mapped_count else 0.0
        coverage_pct = min(100.0, mapped_count * 8.0)  # heuristic: 12 skills = 96%
        gap_score = max(0.0, demand_score - coverage_pct)

        rows.append(CurriculumGapRow(
            subject_code=subject.code,
            subject_name=subject.name,
            semester_number=subject.semester_number,
            coverage_pct=coverage_pct,
            demand_score=demand_score,
            gap_score=gap_score,
        ))

    return sorted(rows, key=lambda r: r.gap_score, reverse=True)
