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
from app.models.placement import Application, PlacementOutcome
from app.schemas.student import StudentUpdateRequest, ConsentUpdateRequest, AddStudentSkillRequest


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


