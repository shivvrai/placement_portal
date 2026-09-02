"""
Students API — profile, academic records, skills, consent.
Accessible by:
  - Students (own profile only)
  - TPO / Admin (all students)
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.student import (
    StudentProfile, StudentSummary, StudentUpdateRequest,
    ConsentUpdateRequest, AcademicRecordResponse,
)
from app.schemas.skill import StudentSkillResponse
from app.schemas.common import MessageResponse, PaginatedResponse, PaginationMeta
from app.services import student_service

router = APIRouter(prefix="/students", tags=["Students"])

_tpo_admin = RoleChecker(["tpo", "admin"])
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


# ─── TPO / Admin endpoints ────────────────────────────────────────────────────

@router.get("", response_model=PaginatedResponse, summary="List all students (TPO/Admin)")
async def list_students(
    department_code: Optional[str] = Query(None, description="Filter by dept code e.g. CS"),
    min_cgpa: Optional[float] = Query(None, ge=0, le=10),
    semester: Optional[int] = Query(None, ge=1, le=10),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    students, total = await student_service.list_students(
        db, department_code=department_code,
        min_cgpa=min_cgpa, semester=semester,
        page=page, per_page=per_page,
    )
    data = [
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
        )
        for s in students
    ]
    total_pages = max(1, (total + per_page - 1) // per_page)
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total, total_pages=total_pages),
    )


@router.get("/{student_id}", response_model=StudentProfile, summary="Get student by ID (TPO)")
async def get_student(
    student_id: uuid.UUID,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    student = await student_service.get_student_full(db, student_id)
    return _build_profile(student)


@router.get("/{student_id}/skills", response_model=list[StudentSkillResponse])
async def get_student_skills(
    student_id: uuid.UUID,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    return await student_service.get_student_skills(db, student_id)


@router.get("/{student_id}/academic-records", response_model=list[AcademicRecordResponse])
async def get_student_academic_records(
    student_id: uuid.UUID,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    return await student_service.get_academic_records(db, student_id)
