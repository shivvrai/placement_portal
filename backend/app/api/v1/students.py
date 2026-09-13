"""
Students API — profile, academic records, skills, consent.
Accessible by:
  - Students (own profile only)
  - TPO / Admin (all students)
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.user import User
from app.models.placement import PlacementOutcome, Application, PlacementDrive
from app.models.skill import StudentSkill
from app.models.academic import AcademicRecord
from app.schemas.student import (
    StudentProfile, StudentSummary, StudentUpdateRequest,
    ConsentUpdateRequest, AcademicRecordResponse, AddStudentSkillRequest,
)
from app.schemas.skill import StudentSkillResponse
from app.schemas.common import MessageResponse, PaginatedResponse, PaginationMeta
from app.services import student_service

router = APIRouter(prefix="/students", tags=["Students"])


_tpo_admin = RoleChecker(["tpo", "admin", "faculty", "hod"])
_student_or_tpo = RoleChecker(["student", "tpo", "faculty", "hod", "admin"])


def _build_profile(student) -> StudentProfile:
    """Merge Student + User ORM objects into a flat response."""
    return StudentProfile(
        id=student.id,
        roll_number=student.roll_number,
        first_name=student.user.first_name,
        last_name=student.user.last_name,
        email=student.user.email,
        phone=student.user.phone,
        department=student.department,
        current_semester=student.current_semester,
        admission_year=student.admission_year,
        cgpa=float(student.cgpa) if student.cgpa else None,
        github_url=student.github_url,
        portfolio_url=student.portfolio_url,
        linkedin_url=student.linkedin_url,
        bio=student.bio,
        resume_url=student.resume_url,
        resume_parsed=student.resume_parsed,
        consent_resume_analysis=student.consent_resume_analysis,
        consent_profile_visible=student.consent_profile_visible,
        created_at=student.created_at,
        updated_at=student.updated_at,
    )


@router.get("/me", response_model=StudentProfile, summary="Get my student profile")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Authenticated student fetches their own profile."""
    student = await student_service.get_student_full(db, current_user.id)
    return _build_profile(student)


@router.patch("/me", response_model=StudentProfile, summary="Update my profile")
async def update_my_profile(
    data: StudentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await student_service.get_student_full(db, current_user.id)
    student = await student_service.update_student_profile(db, student, data)
    return _build_profile(student)


@router.patch("/me/consent", response_model=MessageResponse, summary="Update data consent")
async def update_consent(
    data: ConsentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await student_service.get_student_by_user_id(db, current_user.id)
    await student_service.update_consent(db, student, data)
    return MessageResponse(message="Consent preferences updated")


@router.get("/me/academic-records", response_model=list[AcademicRecordResponse])
async def get_my_academic_records(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    records = await student_service.get_academic_records(db, current_user.id)
    return records


@router.get("/me/skills", response_model=list[StudentSkillResponse])
async def get_my_skills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    skills = await student_service.get_student_skills(db, current_user.id)
    return skills


@router.post("/me/skills", response_model=StudentSkillResponse, summary="Add a skill to my profile")
async def add_my_skill(
    data: AddStudentSkillRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add or update a manual skill on the student's profile."""
    return await student_service.add_student_skill(db, current_user.id, data)


@router.delete("/me/skills/{skill_id}", response_model=MessageResponse, summary="Remove a skill from my profile")
async def delete_my_skill(
    skill_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a skill from the student's profile."""
    await student_service.delete_student_skill(db, current_user.id, skill_id)
    return MessageResponse(message="Skill removed successfully")



# ─── TPO / Admin endpoints ────────────────────────────────────────────────────

@router.get("", response_model=PaginatedResponse, summary="List all students (TPO/Admin)")
async def list_students(
    department_code: Optional[str] = Query(None, description="Filter by dept code e.g. CS"),
    min_cgpa: Optional[float] = Query(None, ge=0, le=10),
    semester: Optional[int] = Query(None, ge=1, le=10),
    status: Optional[str] = Query(None, description="Filter by placement status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    if not isinstance(department_code, str):
        department_code = None
    if not isinstance(min_cgpa, (int, float)):
        min_cgpa = None
    if not isinstance(semester, int):
        semester = None
    if not isinstance(status, str):
        status = None

    students, total = await student_service.list_students(

        db, department_code=department_code,
        min_cgpa=min_cgpa, semester=semester,
        page=page, per_page=per_page,
    )
    data = []
    for s in students:
        # Placement status & details
        company = None
        pkg = None
        placement_status = "unregistered"

        # Check placement outcome first
        outcome_res = await db.execute(
            select(PlacementOutcome)
            .where(PlacementOutcome.student_id == s.id)
            .limit(1)
        )
        outcome = outcome_res.scalar_one_or_none()
        if outcome:
            placement_status = "selected"
            company = outcome.company_name
            pkg = float(outcome.salary_ctc) if outcome.salary_ctc else None
        else:
            app_res = await db.execute(
                select(Application)
                .options(joinedload(Application.drive).joinedload(PlacementDrive.company))
                .where(Application.student_id == s.id)
                .order_by(Application.applied_at.desc())
                .limit(1)
            )
            latest_app = app_res.scalar_one_or_none()
            if latest_app:
                placement_status = latest_app.status
                if latest_app.drive and latest_app.drive.company:
                    company = latest_app.drive.company.name
                    pkg = float(latest_app.drive.salary_ctc) if latest_app.drive.salary_ctc else None
                elif latest_app.drive:
                    company = latest_app.drive.title
                    pkg = float(latest_app.drive.salary_ctc) if latest_app.drive.salary_ctc else None

        # Backlogs
        backlogs_cnt = (await db.execute(
            select(func.count(AcademicRecord.id))
            .where(AcademicRecord.student_id == s.id, AcademicRecord.status == "failed")
        )).scalar_one() or 0

        # Skill score
        skills_cnt = (await db.execute(
            select(func.count(StudentSkill.id)).where(StudentSkill.student_id == s.id)
        )).scalar_one() or 0
        cgpa_val = float(s.cgpa) if s.cgpa else 7.5
        skill_score = min(98, max(50, int(skills_cnt * 6 + cgpa_val * 4 + 20)))

        # Year
        year = (s.current_semester + 1) // 2 if s.current_semester else 4

        # Filter by status if requested
        if status and status != "All" and placement_status != status:
            continue

        data.append(
            StudentSummary(
                id=s.id,
                roll_number=s.roll_number,
                first_name=s.user.first_name,
                last_name=s.user.last_name,
                email=s.user.email,
                department_code=s.department.code,
                department_name=s.department.name,
                current_semester=s.current_semester,
                cgpa=float(s.cgpa) if s.cgpa else None,
                resume_parsed=s.resume_parsed,
                placement_status=placement_status,
                company=company,
                package=pkg,
                skill_score=skill_score,
                backlogs=backlogs_cnt,
                year=year,
            )
        )

    total_pages = max(1, (total + per_page - 1) // per_page)
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total, total_pages=total_pages),
    )



@router.get("/{student_id}", response_model=StudentProfile, summary="Get student by ID (TPO or self)")
async def get_student(
    student_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("tpo", "admin") and current_user.id != student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    student = await student_service.get_student_full(db, student_id)
    return _build_profile(student)


@router.patch("/{student_id}", response_model=StudentProfile, summary="Update student profile (TPO or self)")
async def update_student(
    student_id: uuid.UUID,
    data: StudentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("tpo", "admin") and current_user.id != student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    student = await student_service.get_student_full(db, student_id)
    student = await student_service.update_student_profile(db, student, data)
    return _build_profile(student)


@router.patch("/{student_id}/consent", response_model=MessageResponse, summary="Update student consent (TPO or self)")
async def update_student_consent(
    student_id: uuid.UUID,
    data: ConsentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("tpo", "admin") and current_user.id != student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    student = await student_service.get_student_by_user_id(db, student_id)
    await student_service.update_consent(db, student, data)
    return MessageResponse(message="Consent preferences updated")


@router.get("/{student_id}/skills", response_model=list[StudentSkillResponse], summary="Get student skills (TPO or self)")
async def get_student_skills(
    student_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("tpo", "admin") and current_user.id != student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return await student_service.get_student_skills(db, student_id)


@router.get("/{student_id}/academic-records", response_model=list[AcademicRecordResponse], summary="Get student academic records (TPO or self)")
async def get_student_academic_records(
    student_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("tpo", "admin") and current_user.id != student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return await student_service.get_academic_records(db, student_id)

