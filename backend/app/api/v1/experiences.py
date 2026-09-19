"""
API router — Student Company Interview Experiences & Question Bank Hub.
Prefix: /experiences
"""

import uuid
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, Student
from app.models.experiences import InterviewExperience


router = APIRouter(prefix="/experiences", tags=["Interview Experiences"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class ExperienceCreate(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=200)
    role: str = Field(..., min_length=2, max_length=200)
    placement_drive_id: Optional[uuid.UUID] = None
    difficulty: str = Field(..., pattern="^(Easy|Medium|Hard)$")
    verdict: str = Field(..., pattern="^(Selected|Rejected|In Progress)$")
    overall_experience: str = Field(..., min_length=30)
    questions_asked: List[str] = Field(default_factory=list)
    tips_for_juniors: Optional[str] = None


class ExperienceResponse(BaseModel):
    id: uuid.UUID
    student_name: str
    department: Optional[str] = None
    company_name: str
    role: str
    placement_drive_id: Optional[uuid.UUID] = None
    difficulty: str
    verdict: str
    overall_experience: str
    questions_asked: List[str] = Field(default_factory=list)
    tips_for_juniors: Optional[str] = None
    upvotes: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class ExperienceListResponse(BaseModel):
    items: List[ExperienceResponse]
    total: int
    page: int
    per_page: int


# ─── Helper Functions ─────────────────────────────────────────────────────────

def _format_author_name(exp: InterviewExperience) -> tuple[str, Optional[str]]:
    dept_name = None
    if exp.student and exp.student.user:
        first = exp.student.user.first_name or "Anonymous"
        last = exp.student.user.last_name or ""
        masked_name = f"{first} {last[:1]}." if last else first
        if exp.student.department:
            dept_name = exp.student.department.name
        return masked_name, dept_name
    return "Verified Senior", dept_name


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("", response_model=ExperienceListResponse, summary="Browse interview experiences")
async def list_experiences(
    company: Optional[str] = Query(None, description="Search company name"),
    role: Optional[str] = Query(None, description="Filter by role"),
    difficulty: Optional[str] = Query(None, description="Easy, Medium, or Hard"),
    verdict: Optional[str] = Query(None, description="Selected, Rejected, In Progress"),
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Browse community interview experiences and questions asked during campus drives.
    Supports filtering by company, role, difficulty, and verdict.
    """
    query = select(InterviewExperience).options(
        selectinload(InterviewExperience.student).selectinload(Student.user),
        selectinload(InterviewExperience.student).selectinload(Student.department),
    )

    if company:
        query = query.where(InterviewExperience.company_name.ilike(f"%{company}%"))
    if role:
        query = query.where(InterviewExperience.role.ilike(f"%{role}%"))
    if difficulty:
        query = query.where(InterviewExperience.difficulty == difficulty)
    if verdict:
        query = query.where(InterviewExperience.verdict == verdict)

    # Count total
    count_query = select(func.count(InterviewExperience.id))
    if company:
        count_query = count_query.where(InterviewExperience.company_name.ilike(f"%{company}%"))
    if role:
        count_query = count_query.where(InterviewExperience.role.ilike(f"%{role}%"))
    if difficulty:
        count_query = count_query.where(InterviewExperience.difficulty == difficulty)
    if verdict:
        count_query = count_query.where(InterviewExperience.verdict == verdict)

    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    # Paginate and sort by created_at DESC
    query = query.order_by(desc(InterviewExperience.created_at)).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    experiences = result.scalars().all()

    items = []
    for exp in experiences:
        author_name, dept = _format_author_name(exp)
        items.append(
            ExperienceResponse(
                id=exp.id,
                student_name=author_name,
                department=dept,
                company_name=exp.company_name,
                role=exp.role,
                placement_drive_id=exp.placement_drive_id,
                difficulty=exp.difficulty,
                verdict=exp.verdict,
                overall_experience=exp.overall_experience,
                questions_asked=exp.questions_asked or [],
                tips_for_juniors=exp.tips_for_juniors,
                upvotes=exp.upvotes or 0,
                created_at=exp.created_at,
            )
        )

    return ExperienceListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=ExperienceResponse, status_code=status.HTTP_201_CREATED, summary="Share interview experience")
async def submit_experience(
    data: ExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an interview experience. Authenticated students can post their interview process.
    """
    # Find student record
    res = await db.execute(
        select(Student).where(Student.id == current_user.id)
    )
    student = res.scalar_one_or_none()
    if not student:
        # For non-students or admin testing, link or create student fallback
        if current_user.role == "student":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
        # Create a lightweight student link if admin/TPO tests posting
        student = Student(id=current_user.id, roll_number=f"USR-{current_user.id.hex[:6]}")
        db.add(student)
        await db.flush()

    new_exp = InterviewExperience(
        student_id=student.id,
        company_name=data.company_name.strip(),
        role=data.role.strip(),
        placement_drive_id=data.placement_drive_id,
        difficulty=data.difficulty,
        verdict=data.verdict,
        overall_experience=data.overall_experience.strip(),
        questions_asked=data.questions_asked,
        tips_for_juniors=data.tips_for_juniors.strip() if data.tips_for_juniors else None,
        upvotes=0,
    )
    db.add(new_exp)
    await db.commit()
    await db.refresh(new_exp)

    author_name = f"{current_user.first_name} {current_user.last_name[:1]}." if current_user.last_name else current_user.first_name

    return ExperienceResponse(
        id=new_exp.id,
        student_name=author_name,
        department=None,
        company_name=new_exp.company_name,
        role=new_exp.role,
        placement_drive_id=new_exp.placement_drive_id,
        difficulty=new_exp.difficulty,
        verdict=new_exp.verdict,
        overall_experience=new_exp.overall_experience,
        questions_asked=new_exp.questions_asked or [],
        tips_for_juniors=new_exp.tips_for_juniors,
        upvotes=new_exp.upvotes,
        created_at=new_exp.created_at,
    )


@router.post("/{experience_id}/upvote", summary="Upvote an experience")
async def upvote_experience(
    experience_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Increment the helpful upvotes count for an interview experience.
    """
    res = await db.execute(
        select(InterviewExperience).where(InterviewExperience.id == experience_id)
    )
    exp = res.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview experience not found")

    exp.upvotes = (exp.upvotes or 0) + 1
    await db.commit()
    await db.refresh(exp)

    return {"id": str(exp.id), "upvotes": exp.upvotes}
