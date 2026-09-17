"""
TPO Operations API — Talent pool cohort builder, smart recruitment search,
cohort CSV export, and batch drive invitations.
"""

import csv
import io
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload, joinedload

from app.core.database import get_db
from app.core.security import RoleChecker, get_current_user
from app.models.user import User, Student, Department
from app.models.skill import StudentSkill, Skill
from app.models.placement import PlacementDrive, PlacementOutcome, Application
from app.models.cohort import StudentCohort, Notification

router = APIRouter(prefix="/tpo", tags=["TPO Operations"])
_tpo_admin = RoleChecker(["tpo", "admin"])


class CohortQuery(BaseModel):
    min_cgpa: Optional[float] = None
    max_cgpa: Optional[float] = None
    max_backlogs: Optional[int] = None
    departments: Optional[list[str]] = None
    must_have_skills: Optional[list[str]] = None
    any_of_skills: Optional[list[str]] = None
    min_skill_score: Optional[float] = None
    placement_status: Optional[str] = None  # "placed" | "unplaced" | "any"
    graduation_year: Optional[int] = None


class StudentSummary(BaseModel):
    id: str
    roll_number: str
    first_name: str
    last_name: str
    email: str
    department: str
    cgpa: Optional[float] = None
    skills: list[str] = []
    skills_count: int = 0
    placement_status: str = "unplaced"
    phone: Optional[str] = None


class QueryResponse(BaseModel):
    students: list[StudentSummary]
    total: int
    page: int
    page_size: int
    query_id: str


class SaveCohortRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=300)
    description: Optional[str] = None
    criteria: dict = {}
    student_ids: list[str] = []


class CohortResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_by: str
    criteria: dict
    student_ids: list[str]
    student_count: int
    created_at: str
    is_archived: bool


@router.post("/cohorts/query", response_model=QueryResponse)
async def query_students(
    query: CohortQuery,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Executes a precision multi-condition search against the student talent pool.
    """
    stmt = (
        select(Student)
        .options(
            joinedload(Student.user),
            joinedload(Student.department),
            selectinload(Student.skills).selectinload(StudentSkill.skill),
            selectinload(Student.placement_outcomes),
        )
    )

    if query.min_cgpa is not None:
        stmt = stmt.where(Student.cgpa >= query.min_cgpa)
    if query.max_cgpa is not None:
        stmt = stmt.where(Student.cgpa <= query.max_cgpa)

    if query.departments:
        dept_codes = [d.upper() for d in query.departments if d and d != "All"]
        if dept_codes:
            stmt = stmt.join(Student.department).where(func.upper(Department.code).in_(dept_codes))

    if query.graduation_year is not None:
        # Assuming 4-year degree: admission_year = graduation_year - 4
        stmt = stmt.where(
            or_(
                Student.admission_year == query.graduation_year - 4,
                Student.admission_year == query.graduation_year,
            )
        )

    result = await db.execute(stmt)
    all_students = result.unique().scalars().all()

    # In-memory evaluation for rich skill matching and placement status
    matched_students: list[StudentSummary] = []

    norm_must_have = [s.lower().strip() for s in (query.must_have_skills or []) if s.strip()]
    norm_any_of = [s.lower().strip() for s in (query.any_of_skills or []) if s.strip()]

    for s in all_students:
        s_skills_map = {
            ss.skill.normalized_name.lower(): float(ss.confidence)
            for ss in s.skills if ss.skill
        }
        skill_names = [ss.skill.name for ss in s.skills if ss.skill]
        is_placed = len(s.placement_outcomes) > 0
        p_status = "placed" if is_placed else "unplaced"

        # Placement status filter
        if query.placement_status and query.placement_status.lower() != "any":
            if query.placement_status.lower() == "placed" and not is_placed:
                continue
            if query.placement_status.lower() == "unplaced" and is_placed:
                continue

        # Must-have skills check
        if norm_must_have:
            missing_must = False
            for req in norm_must_have:
                # Direct match or partial match
                has_req = any(req in k or k in req for k in s_skills_map.keys())
                if not has_req:
                    missing_must = True
                    break
            if missing_must:
                continue

        # Any-of skills check
        if norm_any_of:
            has_any = any(
                any(req in k or k in req for k in s_skills_map.keys())
                for req in norm_any_of
            )
            if not has_any:
                continue

        # Minimum average skill score filter
        if query.min_skill_score is not None and s_skills_map:
            avg_score = (sum(s_skills_map.values()) / len(s_skills_map)) * 100.0
            if avg_score < query.min_skill_score:
                continue

        matched_students.append(
            StudentSummary(
                id=str(s.id),
                roll_number=s.roll_number,
                first_name=s.user.first_name if s.user else "",
                last_name=s.user.last_name if s.user else "",
                email=s.user.email if s.user else "",
                department=s.department.code if s.department else "N/A",
                cgpa=float(s.cgpa) if s.cgpa else None,
                skills=skill_names,
                skills_count=len(skill_names),
                placement_status=p_status,
                phone=s.user.phone if (s.user and s.user.phone) else None,
            )
        )

    total_count = len(matched_students)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paged_students = matched_students[start_idx:end_idx]

    return QueryResponse(
        students=paged_students,
        total=total_count,
        page=page,
        page_size=page_size,
        query_id=str(uuid.uuid4()),
    )


@router.post("/cohorts", response_model=CohortResponse)
async def save_cohort(
    payload: SaveCohortRequest,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """Saves a named student talent cohort for recurrent recruiter sharing."""
    cohort = StudentCohort(
        name=payload.name,
        description=payload.description,
        created_by=current_user.id,
        criteria=payload.criteria,
        student_ids=payload.student_ids,
        student_count=len(payload.student_ids),
    )
    db.add(cohort)
    await db.commit()
    await db.refresh(cohort)

    return CohortResponse(
        id=str(cohort.id),
        name=cohort.name,
        description=cohort.description,
        created_by=str(cohort.created_by),
        criteria=cohort.criteria or {},
        student_ids=cohort.student_ids or [],
        student_count=cohort.student_count,
        created_at=cohort.created_at.isoformat() if cohort.created_at else "",
        is_archived=cohort.is_archived,
    )


@router.get("/cohorts", response_model=list[CohortResponse])
async def list_cohorts(
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lists all active talent cohorts created by TPO."""
    res = await db.execute(
        select(StudentCohort)
        .where(StudentCohort.is_archived == False)  # noqa: E712
        .order_by(StudentCohort.created_at.desc())
    )
    cohorts = res.scalars().all()
    return [
        CohortResponse(
            id=str(c.id),
            name=c.name,
            description=c.description,
            created_by=str(c.created_by),
            criteria=c.criteria or {},
            student_ids=c.student_ids or [],
            student_count=c.student_count,
            created_at=c.created_at.isoformat() if c.created_at else "",
            is_archived=c.is_archived,
        )
        for c in cohorts
    ]


@router.get("/cohorts/{cohort_id}/export")
async def export_cohort_csv(
    cohort_id: uuid.UUID,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Streams a recruiter-formatted CSV file with columns:
    Roll Number, Name, Email, Branch, CGPA, Skills, Placement Status, Phone.
    """
    res = await db.execute(
        select(StudentCohort).where(StudentCohort.id == cohort_id)
    )
    cohort = res.scalar_one_or_none()
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")

    student_uuids = []
    for sid in (cohort.student_ids or []):
        try:
            student_uuids.append(uuid.UUID(str(sid)))
        except ValueError:
            pass

    st_res = await db.execute(
        select(Student)
        .where(Student.id.in_(student_uuids))
        .options(
            joinedload(Student.user),
            joinedload(Student.department),
            selectinload(Student.skills).selectinload(StudentSkill.skill),
            selectinload(Student.placement_outcomes),
        )
    )
    students = st_res.unique().scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Roll Number", "Name", "Email", "Branch",
        "CGPA", "Skills", "Placement Status", "Phone"
    ])

    for s in students:
        full_name = f"{s.user.first_name} {s.user.last_name}" if s.user else "Unknown"
        email = s.user.email if s.user else ""
        dept = s.department.code if s.department else ""
        cgpa_str = f"{float(s.cgpa):.2f}" if s.cgpa else "N/A"
        skills_str = "; ".join([ss.skill.name for ss in s.skills if ss.skill])
        status_str = "Placed" if len(s.placement_outcomes) > 0 else "Unplaced"
        phone_str = s.user.phone if (s.user and s.user.phone) else "N/A"

        writer.writerow([
            s.roll_number, full_name, email, dept,
            cgpa_str, skills_str, status_str, phone_str
        ])

    csv_content = output.getvalue()
    safe_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in cohort.name).strip()
    filename = f"cohort_{safe_name}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/cohorts/{cohort_id}/invite-to-drive")
async def batch_invite_to_drive(
    cohort_id: uuid.UUID,
    drive_id: uuid.UUID = Query(..., description="ID of the placement drive"),
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates in-platform notification records for all students in the cohort,
    inviting them to apply to the specified drive.
    """
    c_res = await db.execute(select(StudentCohort).where(StudentCohort.id == cohort_id))
    cohort = c_res.scalar_one_or_none()
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")

    d_res = await db.execute(
        select(PlacementDrive)
        .where(PlacementDrive.id == drive_id)
        .options(joinedload(PlacementDrive.company))
    )
    drive = d_res.scalar_one_or_none()
    if not drive:
        raise HTTPException(status_code=404, detail="Placement drive not found")

    company_name = drive.company.name if drive.company else "Recruiter"
    student_ids = cohort.student_ids or []
    notifications_created = 0

    for sid in student_ids:
        try:
            uid = uuid.UUID(str(sid))
            notif = Notification(
                user_id=uid,
                title=f"Invitation to Apply: {drive.title}",
                message=(
                    f"You have been invited by the TPO to apply for {drive.title} at {company_name}. "
                    f"Visit your Placement Drives dashboard before registration closes."
                ),
                type="drive_invite",
                link="/student/drives",
            )
            db.add(notif)
            notifications_created += 1
        except Exception:
            continue

    await db.commit()

    return {
        "success": True,
        "cohort_id": str(cohort.id),
        "cohort_name": cohort.name,
        "drive_id": str(drive.id),
        "drive_title": drive.title,
        "invited_count": notifications_created,
    }


@router.delete("/cohorts/{cohort_id}")
async def archive_cohort(
    cohort_id: uuid.UUID,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete / archive a saved talent cohort."""
    res = await db.execute(select(StudentCohort).where(StudentCohort.id == cohort_id))
    cohort = res.scalar_one_or_none()
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")

    cohort.is_archived = True
    await db.commit()
    return {"status": "success", "cohort_id": str(cohort_id)}
