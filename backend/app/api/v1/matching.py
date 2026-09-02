"""
Matching API — skill gaps and job-student matching.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.skill import SkillGapResponse
from app.schemas.matching import JobMatchResponse
from app.services import matching_service, student_service

router = APIRouter(tags=["Matching & Intelligence"])

_authenticated = get_current_user


@router.get("/gaps/me", response_model=SkillGapResponse, summary="My skill gap for target role")
async def get_my_skill_gap(
    target_role: str = Query("Data Analyst", description="Target role for gap analysis"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compute skill gap between the current student and a target role."""
    return await matching_service.compute_skill_gap(db, current_user.id, target_role)


@router.get("/gaps/students/{student_id}", response_model=SkillGapResponse, summary="Student skill gap (TPO)")
async def get_student_skill_gap(
    student_id: uuid.UUID,
    target_role: str = Query("Data Analyst"),
    current_user: User = Depends(RoleChecker(["tpo", "faculty", "hod", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    return await matching_service.compute_skill_gap(db, student_id, target_role)


@router.get("/matching/me", response_model=list[JobMatchResponse], summary="My job matches")
async def get_my_job_matches(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return ranked list of job matches for the current student."""
    student = await student_service.get_student_by_user_id(db, current_user.id)
    return await matching_service.compute_job_matches(
        db,
        student_id=current_user.id,
        student_cgpa=float(student.cgpa) if student.cgpa else None,
        student_dept_code=student.department.code if student.department else None,
        limit=limit,
    )


@router.get("/matching/students/{student_id}", response_model=list[JobMatchResponse])
async def get_student_job_matches(
    student_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(RoleChecker(["tpo", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    student = await student_service.get_student_full(db, student_id)
    return await matching_service.compute_job_matches(
        db,
        student_id=student_id,
        student_cgpa=float(student.cgpa) if student.cgpa else None,
        student_dept_code=student.department.code if student.department else None,
        limit=limit,
    )
