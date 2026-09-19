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
from app.core.security import get_current_user, RoleChecker, get_current_student
from app.models.user import User
from app.models.placement import PlacementOutcome, Application, PlacementDrive
from app.models.skill import StudentSkill
from app.models.academic import AcademicRecord
from app.schemas.student import (
    StudentProfile, StudentSummary, StudentUpdateRequest,
    ConsentUpdateRequest, AcademicRecordResponse, AddStudentSkillRequest,
    ProjectCreate, ProjectResponse,
    CertificationCreate, CertificationResponse,
    WorkExperienceCreate, WorkExperienceResponse,
    BulkSkillConfirm,
    PublicProfileResponse,
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


# ─── Projects ─────────────────────────────────────────────────────────────────

@router.get("/me/projects", response_model=list[ProjectResponse], summary="Get my projects")
async def get_my_projects(
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Returns all projects for the current student, sorted by start_date DESC."""
    return await student_service.get_student_projects(db, current_user.id)


@router.post("/me/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Add a project")
async def add_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new project entry for the current student."""
    return await student_service.create_student_project(db, current_user.id, data)


@router.delete("/me/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a project")
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Deletes a project. Returns 403 if project doesn't belong to current student."""
    await student_service.delete_student_project(db, current_user.id, project_id)
    return None


# ─── Certifications ───────────────────────────────────────────────────────────

@router.get("/me/certifications", response_model=list[CertificationResponse], summary="Get my certifications")
async def get_my_certifications(
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Returns all certifications for the current student, sorted by issue_date DESC."""
    return await student_service.get_student_certifications(db, current_user.id)


@router.post("/me/certifications", response_model=CertificationResponse, status_code=status.HTTP_201_CREATED, summary="Add a certification")
async def add_certification(
    data: CertificationCreate,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new certification entry for the current student."""
    return await student_service.create_student_certification(db, current_user.id, data)


@router.delete("/me/certifications/{cert_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a certification")
async def delete_certification(
    cert_id: uuid.UUID,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Deletes a certification. Returns 403 if certification doesn't belong to current student."""
    await student_service.delete_student_certification(db, current_user.id, cert_id)
    return None


# ─── Work Experience ──────────────────────────────────────────────────────────

@router.get("/me/experience", response_model=list[WorkExperienceResponse], summary="Get my work experience")
async def get_my_experience(
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Returns all work experience/internships for the current student, sorted by start_date DESC."""
    return await student_service.get_student_experience(db, current_user.id)


@router.post("/me/experience", response_model=WorkExperienceResponse, status_code=status.HTTP_201_CREATED, summary="Add work experience")
async def add_experience(
    data: WorkExperienceCreate,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new work experience entry for the current student."""
    return await student_service.create_student_experience(db, current_user.id, data)


@router.delete("/me/experience/{exp_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete work experience")
async def delete_experience(
    exp_id: uuid.UUID,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Deletes a work experience entry. Returns 403 if work experience doesn't belong to current student."""
    await student_service.delete_student_experience(db, current_user.id, exp_id)
    return None


# ─── Bulk Skill Confirmation ───────────────────────────────────────────────────

@router.post("/me/skills/bulk", response_model=list[StudentSkillResponse], summary="Bulk confirm skills")
async def bulk_confirm_skills(
    data: BulkSkillConfirm,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates StudentSkill rows for all confirmed skills.
    For each skill name: find or create Skill record, then upsert StudentSkill.
    Sets source='resume_verified' and is_verified=True on each skill.
    """
    return await student_service.bulk_confirm_skills(db, current_user.id, data)


# ─── Public Recruiter Profile (No Auth Required) ──────────────────────────────

@router.get("/{student_id}/public-profile", response_model=PublicProfileResponse, summary="Get public recruiter portfolio")
async def get_public_profile(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a safe subset of student data for public recruiter view.
    MUST NOT include: email, phone, address, academic records, attendance.
    MUST include: name, branch, department, graduation_year,
                  verified skills (source='resume_verified' only),
                  projects, certifications, work_experience,
                  CGPA (only if student.consent_profile_visible = True).
    Returns 404 if student does not exist, 403 if student has disabled public profile.
    """
    return await student_service.get_public_profile(db, student_id)




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

