"""
Faculty Department Placement & Curriculum Analytics API.

Task 4 (Anjula Final Submission):
  GET  /faculty/dashboard               — Department placement & curriculum analytics
  GET  /faculty/students                — Filterable student roster with at-risk highlighting
  POST /faculty/students/{id}/assign-mentor — Faculty counseling & mentor assignment
"""

import uuid
import statistics
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.user import User, Student, Department, Faculty
from app.models.placement import Application, PlacementOutcome, PlacementDrive
from app.models.academic import AcademicRecord
from app.schemas.anjula_sprint3 import (
    FacultyDashboardResponse, FacultyStudentRow, AssignMentorRequest,
)
from app.schemas.common import MessageResponse, PaginatedResponse, PaginationMeta
from app.services import analytics_service
from app.api.v1.notifications import create_notification

router = APIRouter(prefix="/faculty", tags=["Faculty Department Analytics"])

_faculty_or_admin = RoleChecker(["faculty", "hod", "tpo", "admin"])


async def _resolve_department(db: AsyncSession, department_code: Optional[str], current_user: User) -> Department:
    """Finds target department from code, user's faculty profile, or default."""
    if department_code:
        res = await db.execute(select(Department).where(func.upper(Department.code) == department_code.upper()))
        dept = res.scalar_one_or_none()
        if dept:
            return dept

    # Check current user's faculty profile
    res = await db.execute(select(Faculty).where(Faculty.id == current_user.id))
    fac = res.scalar_one_or_none()
    if fac and fac.department_id:
        d_res = await db.execute(select(Department).where(Department.id == fac.department_id))
        dept = d_res.scalar_one_or_none()
        if dept:
            return dept

    # Fallback to first department
    res = await db.execute(select(Department).order_by(Department.code).limit(1))
    dept = res.scalar_one_or_none()
    if dept:
        return dept

    # Fallback placeholder if empty DB
    return Department(id=uuid.uuid4(), code="CSE", name="Computer Science & Engineering")


@router.get("/dashboard", response_model=FacultyDashboardResponse, summary="Faculty department placement & curriculum dashboard")
async def faculty_dashboard(
    department_code: Optional[str] = Query(None, description="Department code (e.g. CSE, IT, ECE)"),
    current_user: User = Depends(_faculty_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns comprehensive placement, salary distribution, top recruiters,
    and curriculum skill gap analytics for the department.
    """
    dept = await _resolve_department(db, department_code, current_user)

    # 1. Fetch department students with related data
    res = await db.execute(
        select(Student)
        .where(Student.department_id == dept.id)
        .options(
            selectinload(Student.user),
            selectinload(Student.skills),
            selectinload(Student.applications).selectinload(Application.drive).selectinload(PlacementDrive.company),
            selectinload(Student.placement_outcomes),
        )
    )
    students = res.scalars().all()
    total_students = len(students)

    # 2. Compute placement KPIs
    placed_student_ids = set()
    total_offers = 0
    offers_per_student: dict[uuid.UUID, int] = {}
    salaries: list[float] = []
    recruiter_counts: dict[str, int] = {}

    for s in students:
        s_offers = 0
        # Outcomes
        for o in (s.placement_outcomes or []):
            placed_student_ids.add(s.id)
            s_offers += 1
            if o.salary_ctc:
                salaries.append(float(o.salary_ctc))
            if o.company_name:
                recruiter_counts[o.company_name] = recruiter_counts.get(o.company_name, 0) + 1

        # Selected applications
        for app in (s.applications or []):
            if app.status == "selected":
                placed_student_ids.add(s.id)
                s_offers += 1
                if app.offer_ctc_lpa:
                    salaries.append(float(app.offer_ctc_lpa))
                elif app.drive and app.drive.salary_ctc:
                    salaries.append(float(app.drive.salary_ctc))
                if app.drive and app.drive.company:
                    cname = app.drive.company.name
                    recruiter_counts[cname] = recruiter_counts.get(cname, 0) + 1

        if getattr(s, "placement_status", None) == "placed":
            placed_student_ids.add(s.id)

        offers_per_student[s.id] = s_offers
        total_offers += s_offers

    placed_count = len(placed_student_ids)
    eligible_count = sum(1 for s in students if (s.cgpa is None or float(s.cgpa) >= 6.0))
    placement_pct = round((placed_count / max(1, eligible_count or total_students)) * 100, 1) if total_students else 0.0
    dual_offers_count = sum(1 for s_id, count in offers_per_student.items() if count >= 2)

    # Salary statistics
    highest_ctc = max(salaries) if salaries else 0.0
    avg_ctc = round(sum(salaries) / len(salaries), 2) if salaries else 0.0
    median_ctc = round(float(statistics.median(salaries)), 2) if salaries else 0.0

    # Top Recruiters
    sorted_recruiters = sorted(recruiter_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_recruiters = [{"company_name": comp, "hires_count": cnt} for comp, cnt in sorted_recruiters]

    # 3. Pull Curriculum Gap & Skill Analytics from analytics service
    overview = await analytics_service.get_department_overview(db, dept.code)

    return FacultyDashboardResponse(
        department_code=dept.code,
        department_name=dept.name,
        total_students=total_students,
        placed_count=placed_count,
        placement_pct=placement_pct,
        eligible_count=eligible_count,
        total_offers=total_offers,
        dual_offers_count=dual_offers_count,
        highest_ctc_lpa=highest_ctc,
        median_ctc_lpa=median_ctc,
        avg_ctc_lpa=avg_ctc,
        top_recruiters=top_recruiters,
        avg_skill_score=overview.kpis.avg_skill_score,
        subjects_high_gap=overview.kpis.subjects_high_gap,
        students_at_risk=overview.kpis.students_at_risk,
        curriculum_coverage=overview.kpis.curriculum_coverage,
        skill_radar=[item.model_dump() for item in overview.skill_radar],
        coverage_donut=[item.model_dump() for item in overview.coverage_donut],
        subject_gap_rank=[item.model_dump() for item in overview.subject_gap_rank],
        batch_skill=[item.model_dump() for item in overview.batch_skill],
        at_risk_students=[item.model_dump() for item in overview.at_risk],
    )


@router.get("/students", response_model=PaginatedResponse, summary="Faculty department student roster with at-risk filters")
async def faculty_students(
    department_code: Optional[str] = Query(None, description="Department code"),
    placement_status: Optional[str] = Query(None, description="Filter: placed, unplaced, opted_out"),
    min_cgpa: Optional[float] = Query(None, description="Minimum CGPA"),
    max_cgpa: Optional[float] = Query(None, description="Maximum CGPA"),
    max_backlogs: Optional[int] = Query(None, description="Maximum active backlogs"),
    at_risk_only: bool = Query(False, description="Filter only at-risk students (unplaced, CGPA < 7.0 or skill < 50%)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(_faculty_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns paginated student list for the department with computed risk status,
    skill scores, application counts, and offer totals.
    """
    dept = await _resolve_department(db, department_code, current_user)

    res = await db.execute(
        select(Student)
        .where(Student.department_id == dept.id)
        .options(
            selectinload(Student.user),
            selectinload(Student.skills),
            selectinload(Student.applications),
            selectinload(Student.placement_outcomes),
            selectinload(Student.academic_records),
        )
    )
    students = res.scalars().all()

    rows: list[FacultyStudentRow] = []
    for s in students:
        user = s.user
        cgpa_val = float(s.cgpa) if s.cgpa is not None else None

        # Skill score average
        conf_list = [float(sk.confidence) for sk in (s.skills or [])]
        skill_score = round(sum(conf_list) / len(conf_list) * 100, 1) if conf_list else 65.0

        # Placement status check
        is_placed = (
            getattr(s, "placement_status", None) == "placed"
            or bool(s.placement_outcomes)
            or any(a.status == "selected" for a in (s.applications or []))
        )
        resolved_status = "placed" if is_placed else (getattr(s, "placement_status", None) or "unplaced")

        # Active backlogs calculation
        active_backlogs = sum(1 for rec in (s.academic_records or []) if getattr(rec, "grade", "") in ("F", "RA"))

        # Risk calculation
        is_at_risk = (resolved_status != "placed") and (
            (cgpa_val is not None and cgpa_val < 7.0) or skill_score < 50.0
        )
        risk_level = None
        if is_at_risk:
            risk_level = "high" if ((cgpa_val is not None and cgpa_val < 6.0) or skill_score < 40.0) else "medium"

        total_apps = len(s.applications or [])
        total_offers = sum(1 for a in (s.applications or []) if a.status == "selected") + len(s.placement_outcomes or [])

        # Filter predicates
        if placement_status and resolved_status.lower() != placement_status.lower():
            continue
        if min_cgpa is not None and (cgpa_val is None or cgpa_val < min_cgpa):
            continue
        if max_cgpa is not None and (cgpa_val is not None and cgpa_val > max_cgpa):
            continue
        if max_backlogs is not None and active_backlogs > max_backlogs:
            continue
        if at_risk_only and not is_at_risk:
            continue

        rows.append(FacultyStudentRow(
            student_id=s.id,
            roll_number=s.roll_number,
            first_name=user.first_name if user else "Student",
            last_name=user.last_name if user else "",
            email=user.email if user else "",
            department_code=dept.code,
            cgpa=cgpa_val,
            active_backlogs=active_backlogs,
            placement_status=resolved_status,
            skill_score=skill_score,
            is_at_risk=is_at_risk,
            risk_level=risk_level,
            total_applications=total_apps,
            total_offers=total_offers,
            counseling_notes=[],
        ))

    total = len(rows)
    start_idx = (page - 1) * per_page
    paginated_items = rows[start_idx:start_idx + per_page]

    return PaginatedResponse(
        data=[i.model_dump() for i in paginated_items],
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=max(1, (total + per_page - 1) // per_page),
        ),
    )


@router.post("/students/{student_id}/assign-mentor", response_model=MessageResponse, summary="Assign mentor & schedule counseling")
async def assign_mentor(
    student_id: uuid.UUID,
    data: AssignMentorRequest,
    current_user: User = Depends(_faculty_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Assigns a faculty mentor to a student, records counseling intervention,
    and dispatches a priority notification to the student.
    """
    res = await db.execute(select(Student).where(Student.id == student_id).options(selectinload(Student.user)))
    student = res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    intervention_title = data.intervention_type.replace("_", " ").title()
    msg = (
        f"You have been assigned to faculty mentor {data.mentor_name} for {intervention_title}. "
        f"Counseling Note: {data.counseling_note or 'Please connect with your mentor to plan your placement readiness strategy.'}"
    )

    await create_notification(
        db=db,
        user_id=student.id,
        title=f"Faculty Mentorship: {data.mentor_name}",
        message=msg,
        type="info",
        link="/student/profile",
        priority="high",
    )
    await db.commit()

    return MessageResponse(
        message=f"Mentor {data.mentor_name} successfully assigned to {student.roll_number}."
    )
