"""
Student service — DB queries and business logic for the student domain.
"""

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload, joinedload
from fastapi import HTTPException, status

from app.models.user import User, Student, Department
from app.models.academic import AcademicRecord, Subject
from app.models.skill import StudentSkill, Skill
from app.models.portfolio import Project, Certification, Internship, WorkExperience
from app.models.placement import Application, PlacementOutcome
from app.schemas.student import (
    StudentUpdateRequest, ConsentUpdateRequest, AddStudentSkillRequest,
    ProjectCreate, CertificationCreate, WorkExperienceCreate, BulkSkillConfirm,
)


async def get_student_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Student:
    """Fetch student row (with department eager-loaded) or raise 404."""
    result = await db.execute(
        select(Student)
        .where(Student.id == user_id)
        .options(selectinload(Student.department))
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


async def get_student_full(db: AsyncSession, student_id: uuid.UUID) -> Student:
    """Fetch student with user, department, and skills eager-loaded."""
    result = await db.execute(
        select(Student)
        .where(Student.id == student_id)
        .options(
            selectinload(Student.department),
            selectinload(Student.user),
            selectinload(Student.skills).selectinload(StudentSkill.skill),
        )
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


async def list_students(
    db: AsyncSession,
    department_code: Optional[str] = None,
    min_cgpa: Optional[float] = None,
    semester: Optional[int] = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[Student], int]:
    """Return paginated list of students with filters, plus total count."""
    query = (
        select(Student)
        .options(
            joinedload(Student.user),
            joinedload(Student.department),
        )
    )

    if department_code:
        query = query.join(Student.department).where(Department.code == department_code)
    if min_cgpa is not None:
        query = query.where(Student.cgpa >= min_cgpa)
    if semester is not None:
        query = query.where(Student.current_semester == semester)

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    # Paginate
    query = query.offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(query)).unique().scalars().all()

    return list(rows), total


async def update_student_profile(
    db: AsyncSession,
    student: Student,
    data: StudentUpdateRequest,
) -> Student:
    """Apply partial update to student profile."""
    update_data = data.model_dump(exclude_none=True)
    if "phone" in update_data:
        if student.user:
            student.user.phone = update_data.pop("phone")
        else:
            update_data.pop("phone")
    for field, value in update_data.items():
        setattr(student, field, value)
    await db.commit()
    await db.refresh(student)
    return student


async def update_consent(
    db: AsyncSession,
    student: Student,
    data: ConsentUpdateRequest,
) -> Student:
    if data.consent_resume_analysis is not None:
        student.consent_resume_analysis = data.consent_resume_analysis
    if data.consent_profile_visible is not None:
        student.consent_profile_visible = data.consent_profile_visible
    await db.commit()
    await db.refresh(student)
    return student


async def get_academic_records(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> list[AcademicRecord]:
    result = await db.execute(
        select(AcademicRecord)
        .where(AcademicRecord.student_id == student_id)
        .options(selectinload(AcademicRecord.subject))
        .order_by(AcademicRecord.subject_id)
    )
    return result.scalars().all()


async def get_student_skills(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> list[StudentSkill]:
    result = await db.execute(
        select(StudentSkill)
        .where(StudentSkill.student_id == student_id)
        .options(selectinload(StudentSkill.skill))
        .order_by(StudentSkill.confidence.desc())
    )
    return result.scalars().all()


async def update_skill_confidence(
    db: AsyncSession,
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
    normalized_score: float,
    source: str
):
    """
    Update student skill confidence based on an evidence source (assessment, project, etc.).
    Weightings can be configured here.
    """
    from datetime import datetime, timezone
    
    result = await db.execute(
        select(StudentSkill)
        .where(StudentSkill.student_id == student_id, StudentSkill.skill_id == skill_id)
    )
    student_skill = result.scalar_one_or_none()
    
    if student_skill:
        # Example weighting: previous confidence 70%, new assessment 30%
        old_confidence = float(student_skill.confidence)
        if source == "assessment":
            new_confidence = (old_confidence * 0.7) + (normalized_score * 0.3)
        else:
            new_confidence = (old_confidence * 0.9) + (normalized_score * 0.1)
            
        student_skill.confidence = round(new_confidence, 2)
        student_skill.last_updated = datetime.now(timezone.utc)
    else:
        db.add(StudentSkill(
            student_id=student_id,
            skill_id=skill_id,
            confidence=round(normalized_score, 2),
            source=source
        ))
    
    return student_skill


async def add_student_skill(
    db: AsyncSession,
    student_id: uuid.UUID,
    data: AddStudentSkillRequest,
) -> StudentSkill:
    """Add or update a manual/self-reported skill for a student."""
    from datetime import datetime, timezone
    import re
    from fastapi import HTTPException
    
    skill = None
    if data.skill_id:
        res = await db.execute(select(Skill).where(Skill.id == data.skill_id))
        skill = res.scalar_one_or_none()
    
    if not skill and data.skill_name:
        clean_name = data.skill_name.strip()
        normalised = re.sub(r"\s+", " ", clean_name.lower())
        
        # 1. Find or create Skill in taxonomy
        res = await db.execute(select(Skill).where(Skill.normalized_name == normalised))
        skill = res.scalar_one_or_none()
        if not skill:
            valid_categories = {
                'language','framework','library','tool','platform',
                'concept','methodology','database','cloud','soft_skill','domain_knowledge','other'
            }
            category = data.category if data.category in valid_categories else 'other'
            skill = Skill(
                name=clean_name.title(),
                normalized_name=normalised,
                category=category,
                created_at=datetime.now(timezone.utc),
            )
            db.add(skill)
            await db.flush()

    if not skill:
        raise HTTPException(status_code=400, detail="Skill ID or valid skill name required")
    
    # 2. Check if student already has this skill under manual source
    res = await db.execute(
        select(StudentSkill)
        .where(
            StudentSkill.student_id == student_id,
            StudentSkill.skill_id == skill.id,
            StudentSkill.source == "manual"
        )
        .options(selectinload(StudentSkill.skill))
    )
    student_skill = res.scalar_one_or_none()
    
    confidence_val = min(1.0, max(0.0, float(data.confidence)))
    
    if student_skill:
        student_skill.confidence = round(confidence_val, 2)
        student_skill.proficiency_level = data.proficiency_level
        student_skill.last_updated = datetime.now(timezone.utc)
    else:
        student_skill = StudentSkill(
            student_id=student_id,
            skill_id=skill.id,
            confidence=round(confidence_val, 2),
            source="manual",
            proficiency_level=data.proficiency_level,
            last_updated=datetime.now(timezone.utc),
        )
        db.add(student_skill)
        await db.flush()
    
    await db.commit()
    
    # Re-fetch with relationship loaded
    res = await db.execute(
        select(StudentSkill)
        .where(StudentSkill.id == student_skill.id)
        .options(selectinload(StudentSkill.skill))
    )
    return res.scalar_one()


async def delete_student_skill(
    db: AsyncSession,
    student_id: uuid.UUID,
    skill_identifier: uuid.UUID | str,
) -> bool:
    """Delete a student skill by StudentSkill.id, Skill.id, or skill name."""
    import re

    parsed_uuid = None
    if isinstance(skill_identifier, uuid.UUID):
        parsed_uuid = skill_identifier
    elif isinstance(skill_identifier, str):
        try:
            parsed_uuid = uuid.UUID(skill_identifier)
        except ValueError:
            parsed_uuid = None

    if parsed_uuid:
        # 1. Check if identifier is a StudentSkill.id (a specific entry)
        res = await db.execute(
            select(StudentSkill).where(
                StudentSkill.student_id == student_id,
                StudentSkill.id == parsed_uuid,
            )
        )
        entry = res.scalar_one_or_none()
        if entry:
            target_skill_id = entry.skill_id
            # Delete this record and any duplicates of this skill for the student
            await db.execute(
                delete(StudentSkill).where(
                    StudentSkill.student_id == student_id,
                    (StudentSkill.id == parsed_uuid) | (StudentSkill.skill_id == target_skill_id)
                )
            )
            await db.commit()
            return True

        # 2. Check if identifier is a taxonomy Skill.id
        res = await db.execute(
            select(StudentSkill).where(
                StudentSkill.student_id == student_id,
                StudentSkill.skill_id == parsed_uuid,
            )
        )
        matching = res.scalars().all()
        if matching:
            for item in matching:
                await db.delete(item)
            await db.commit()
            return True

    # 3. If identifier is a skill name string
    if isinstance(skill_identifier, str) and skill_identifier.strip():
        clean_name = skill_identifier.strip()
        normalised = re.sub(r"\s+", " ", clean_name.lower())
        res = await db.execute(
            select(StudentSkill)
            .join(StudentSkill.skill)
            .where(
                StudentSkill.student_id == student_id,
                (Skill.normalized_name == normalised) | (Skill.name.ilike(clean_name))
            )
        )
        matching = res.scalars().all()
        if matching:
            for item in matching:
                await db.delete(item)
            await db.commit()
            return True

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found for this student")


# ─── Projects CRUD ─────────────────────────────────────────────────────────────

async def get_student_projects(db: AsyncSession, student_id: uuid.UUID) -> list[Project]:
    """Returns all projects for a student sorted by start_date DESC."""
    res = await db.execute(
        select(Project)
        .where(Project.student_id == student_id)
        .order_by(Project.start_date.desc().nullslast(), Project.created_at.desc())
    )
    return list(res.scalars().all())


async def create_student_project(
    db: AsyncSession,
    student_id: uuid.UUID,
    data: ProjectCreate,
) -> Project:
    """Create a new project entry for student."""
    project = Project(
        student_id=student_id,
        title=data.title,
        description=data.description,
        technologies=data.tech_stack,
        url=data.live_url,
        github_url=data.github_url,
        start_date=data.start_date,
        end_date=data.end_date,
        is_featured=data.is_featured,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def delete_student_project(
    db: AsyncSession,
    student_id: uuid.UUID,
    project_id: uuid.UUID,
) -> bool:
    """Delete a student project, returning 404 or 403 if unauthorized."""
    res = await db.execute(select(Project).where(Project.id == project_id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.student_id != student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this project")
    await db.delete(project)
    await db.commit()
    return True


# ─── Certifications CRUD ───────────────────────────────────────────────────────

async def get_student_certifications(db: AsyncSession, student_id: uuid.UUID) -> list[Certification]:
    """Returns all certifications for a student sorted by issue_date DESC."""
    res = await db.execute(
        select(Certification)
        .where(Certification.student_id == student_id)
        .order_by(Certification.issue_date.desc().nullslast(), Certification.created_at.desc())
    )
    return list(res.scalars().all())


async def create_student_certification(
    db: AsyncSession,
    student_id: uuid.UUID,
    data: CertificationCreate,
) -> Certification:
    """Create a new certification entry for student."""
    cert = Certification(
        student_id=student_id,
        title=data.name,
        issuer=data.issuing_organization,
        issue_date=data.issue_date,
        expiry_date=data.expiration_date,
        credential_id=data.credential_id,
        credential_url=data.credential_url,
    )
    db.add(cert)
    await db.commit()
    await db.refresh(cert)
    return cert


async def delete_student_certification(
    db: AsyncSession,
    student_id: uuid.UUID,
    cert_id: uuid.UUID,
) -> bool:
    """Delete a student certification, returning 404 or 403 if unauthorized."""
    res = await db.execute(select(Certification).where(Certification.id == cert_id))
    cert = res.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification not found")
    if cert.student_id != student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this certification")
    await db.delete(cert)
    await db.commit()
    return True


# ─── Work Experience CRUD ──────────────────────────────────────────────────────

async def get_student_experience(db: AsyncSession, student_id: uuid.UUID) -> list[Internship]:
    """Returns all work experience/internship entries for a student sorted by start_date DESC."""
    res = await db.execute(
        select(Internship)
        .where(Internship.student_id == student_id)
        .order_by(Internship.start_date.desc().nullslast(), Internship.created_at.desc())
    )
    return list(res.scalars().all())


async def create_student_experience(
    db: AsyncSession,
    student_id: uuid.UUID,
    data: WorkExperienceCreate,
) -> Internship:
    """Create a new work experience entry for student."""
    exp = Internship(
        student_id=student_id,
        company_name=data.company_name,
        role=data.role,
        location=data.location,
        employment_type=data.employment_type,
        start_date=data.start_date,
        end_date=data.end_date,
        is_current=data.is_current,
        description=data.description,
        technologies=data.skills_used or [],
    )
    db.add(exp)
    await db.commit()
    await db.refresh(exp)
    return exp


async def delete_student_experience(
    db: AsyncSession,
    student_id: uuid.UUID,
    exp_id: uuid.UUID,
) -> bool:
    """Delete a student work experience entry, returning 404 or 403 if unauthorized."""
    res = await db.execute(select(Internship).where(Internship.id == exp_id))
    exp = res.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work experience not found")
    if exp.student_id != student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this work experience")
    await db.delete(exp)
    await db.commit()
    return True


# ─── Bulk Skill Confirmation ───────────────────────────────────────────────────

async def bulk_confirm_skills(
    db: AsyncSession,
    student_id: uuid.UUID,
    data: BulkSkillConfirm,
) -> list[StudentSkill]:
    """
    Creates or updates StudentSkill rows for all confirmed skills.
    Sets source='resume_verified' (or data.source) and is_verified=True on each skill.
    """
    import re
    from datetime import datetime, timezone

    confirmed_skills: list[StudentSkill] = []
    source = data.source or "resume_verified"
    now = datetime.now(timezone.utc)

    for skill_name in data.skills:
        clean_name = skill_name.strip()
        if not clean_name:
            continue
        normalised = re.sub(r"\s+", " ", clean_name.lower())

        # 1. Find or create Skill record
        res = await db.execute(select(Skill).where(Skill.normalized_name == normalised))
        skill = res.scalar_one_or_none()
        if not skill:
            skill = Skill(
                name=clean_name.title(),
                normalized_name=normalised,
                category="other",
                created_at=now,
            )
            db.add(skill)
            await db.flush()

        # 2. Check if StudentSkill already exists for this (student, skill, source)
        res_ss = await db.execute(
            select(StudentSkill).where(
                StudentSkill.student_id == student_id,
                StudentSkill.skill_id == skill.id,
                StudentSkill.source == source,
            )
        )
        student_skill = res_ss.scalar_one_or_none()

        if student_skill:
            student_skill.confidence = 0.9
            student_skill.is_verified = True
            student_skill.last_updated = now
        else:
            student_skill = StudentSkill(
                student_id=student_id,
                skill_id=skill.id,
                confidence=0.9,
                source=source,
                is_verified=True,
                last_updated=now,
            )
            db.add(student_skill)
            await db.flush()

        confirmed_skills.append(student_skill)

    await db.commit()

    # Re-fetch with loaded relationship
    if confirmed_skills:
        skill_ids = [s.id for s in confirmed_skills]
        res = await db.execute(
            select(StudentSkill)
            .where(StudentSkill.id.in_(skill_ids))
            .options(selectinload(StudentSkill.skill))
        )
        return list(res.scalars().all())
    return []


async def get_public_profile(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> dict:
    """
    Returns a safe subset of student data for public recruiter view.
    Raises 404 if student does not exist.
    Raises 403 if student has disabled public profile visibility.
    """
    from datetime import date
    from fastapi import HTTPException, status
    from app.models.user import Student
    from app.models.skill import StudentSkill
    from sqlalchemy.orm import selectinload

    res = await db.execute(
        select(Student)
        .where(Student.id == student_id)
        .options(
            selectinload(Student.user),
            selectinload(Student.department),
            selectinload(Student.projects),
            selectinload(Student.certifications),
            selectinload(Student.internships),
            selectinload(Student.skills).selectinload(StudentSkill.skill),
        )
    )
    student = res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    if not student.consent_profile_visible:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This student has disabled public profile visibility.",
        )

    user = student.user
    name = f"{user.first_name} {user.last_name}".strip() if user else "Student"
    dept_name = student.department.name if student.department else "Engineering"

    grad_year = (student.admission_year + 4) if student.admission_year else 2026

    # CGPA only if student consents to sharing
    can_show_cgpa = bool(student.consent_profile_visible)
    cgpa_val = float(student.cgpa) if (can_show_cgpa and student.cgpa is not None) else None

    # Verified skills (source='resume_verified' or is_verified)
    seen_skills = set()
    verified_skills = []
    for ss in sorted(student.skills, key=lambda s: s.confidence or 0, reverse=True):
        if ss.source == "resume_verified" or getattr(ss, "is_verified", False):
            s_name = ss.skill.name if ss.skill else None
            if s_name and s_name.lower() not in seen_skills:
                seen_skills.add(s_name.lower())
                verified_skills.append(s_name)

    # Public projects
    public_projects = []
    for p in sorted(student.projects, key=lambda x: (x.is_featured, x.start_date or date.min), reverse=True):
        public_projects.append({
            "title": p.title,
            "description": p.description,
            "technologies": p.technologies or [],
            "github_url": p.github_url,
            "live_url": p.live_url or p.url,
            "start_date": p.start_date,
            "end_date": p.end_date,
            "is_featured": getattr(p, "is_featured", False),
        })

    # Public certifications
    public_certs = []
    for c in sorted(student.certifications, key=lambda x: x.issue_date or date.min, reverse=True):
        public_certs.append({
            "name": c.name or c.title,
            "issuing_organization": c.issuing_organization or c.issuer,
            "issue_date": c.issue_date,
            "expiration_date": c.expiration_date or c.expiry_date,
            "credential_id": getattr(c, "credential_id", None),
            "credential_url": c.credential_url,
        })

    # Public work experience
    public_exp = []
    for exp in sorted(student.internships, key=lambda x: x.start_date or date.min, reverse=True):
        public_exp.append({
            "company_name": exp.company_name,
            "role": exp.role,
            "location": getattr(exp, "location", None),
            "employment_type": getattr(exp, "employment_type", "Internship"),
            "start_date": exp.start_date,
            "end_date": exp.end_date,
            "is_current": getattr(exp, "is_current", False),
            "description": exp.description,
            "skills_used": getattr(exp, "skills_used", None) or exp.technologies or [],
        })

    return {
        "id": student.id,
        "name": name,
        "roll_number": student.roll_number,
        "branch": dept_name,
        "department": dept_name,
        "graduation_year": grad_year,
        "cgpa": cgpa_val,
        "verified_skills": verified_skills,
        "projects": public_projects,
        "certifications": public_certs,
        "work_experience": public_exp,
        "college_name": "University Placement Cell",
        "last_updated": student.updated_at or student.created_at,
    }



