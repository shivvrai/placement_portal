"""
Student service — DB queries and business logic for the student domain.
"""

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload
from fastapi import HTTPException, status

from app.models.user import User, Student, Department
from app.models.academic import AcademicRecord, Subject
from app.models.skill import StudentSkill, Skill
from app.models.placement import Application, PlacementOutcome
from app.schemas.student import StudentUpdateRequest, ConsentUpdateRequest


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
    for field, value in data.model_dump(exclude_none=True).items():
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
