"""
Alumni Network & Mentorship API — mentor discovery, connection requests, session scheduling.

Sprint 3 — Sakshi Kumari

Endpoints:
  POST   /alumni/profile         — Register as alumni mentor
  GET    /alumni                  — Browse available mentors
  GET    /alumni/{id}             — View mentor profile
  POST   /alumni/mentorship       — Request mentorship connection
  PATCH  /alumni/mentorship/{id}  — Accept/reject mentorship
  GET    /alumni/mentorship/mine  — List my mentorships
  POST   /alumni/sessions         — Schedule mentorship session
  POST   /alumni/sessions/{id}/feedback — Rate a session
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker, get_current_student
from app.models.user import User
from app.schemas.sakshi_sprint3 import (
    AlumniProfileCreate, AlumniProfileResponse,
    MentorshipRequestCreate, MentorshipConnectionResponse,
    MentorshipSessionCreate, MentorshipSessionResponse,
    SessionFeedback,
)
from app.schemas.common import MessageResponse, PaginatedResponse, PaginationMeta
from app.services import sakshi_sprint3_service as svc

router = APIRouter(prefix="/alumni", tags=["Alumni & Mentorship"])

_any_user = RoleChecker(["student", "tpo", "admin", "faculty", "hod"])


@router.post("/profile", response_model=AlumniProfileResponse, summary="Register alumni mentor profile")
async def register_alumni(
    data: AlumniProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await svc.create_alumni_profile(db, current_user.id, data)
    return AlumniProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        user_name=f"{current_user.first_name} {current_user.last_name}",
        graduation_year=profile.graduation_year,
        department_code=profile.department_code,
        current_company=profile.current_company,
        current_designation=profile.current_designation,
        linkedin_url=profile.linkedin_url,
        expertise_areas=profile.expertise_areas or [],
        bio=profile.bio,
        is_available_for_mentorship=profile.is_available_for_mentorship,
        max_mentees=profile.max_mentees,
        rating=profile.rating,
        total_sessions=profile.total_sessions,
        created_at=profile.created_at,
    )


@router.get("", response_model=PaginatedResponse, summary="Browse available alumni mentors")
async def list_alumni(
    department: Optional[str] = Query(None),
    available_only: bool = Query(True),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(_any_user),
    db: AsyncSession = Depends(get_db),
):
    alumni_list, total = await svc.list_alumni(db, department, available_only, page, per_page)
    items = []
    for a in alumni_list:
        user_name = None
        if a.user:
            user_name = f"{a.user.first_name} {a.user.last_name}"
        items.append(AlumniProfileResponse(
            id=a.id, user_id=a.user_id, user_name=user_name,
            graduation_year=a.graduation_year, department_code=a.department_code,
            current_company=a.current_company, current_designation=a.current_designation,
            linkedin_url=a.linkedin_url, expertise_areas=a.expertise_areas or [],
            bio=a.bio, is_available_for_mentorship=a.is_available_for_mentorship,
            max_mentees=a.max_mentees, rating=a.rating, total_sessions=a.total_sessions,
            created_at=a.created_at,
        ))
    return PaginatedResponse(
        data=[item.model_dump() for item in items],
        pagination=PaginationMeta(page=page, per_page=per_page, total=total),
    )


@router.get("/{alumni_id}", response_model=AlumniProfileResponse, summary="View alumni profile")
async def get_alumni(
    alumni_id: uuid.UUID,
    current_user: User = Depends(_any_user),
    db: AsyncSession = Depends(get_db),
):
    a = await svc.get_alumni_profile(db, alumni_id)
    user_name = f"{a.user.first_name} {a.user.last_name}" if a.user else None
    return AlumniProfileResponse(
        id=a.id, user_id=a.user_id, user_name=user_name,
        graduation_year=a.graduation_year, department_code=a.department_code,
        current_company=a.current_company, current_designation=a.current_designation,
        linkedin_url=a.linkedin_url, expertise_areas=a.expertise_areas or [],
        bio=a.bio, is_available_for_mentorship=a.is_available_for_mentorship,
        max_mentees=a.max_mentees, rating=a.rating, total_sessions=a.total_sessions,
        created_at=a.created_at,
    )


@router.post("/mentorship", response_model=MentorshipConnectionResponse, summary="Request mentorship")
async def request_mentorship(
    data: MentorshipRequestCreate,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    conn = await svc.request_mentorship(db, current_user.id, data)
    return MentorshipConnectionResponse(
        id=conn.id, alumni_id=conn.alumni_id, student_id=conn.student_id,
        status=conn.status, message=conn.message, goals=conn.goals or [],
        created_at=conn.created_at,
    )


@router.patch("/mentorship/{connection_id}", response_model=MentorshipConnectionResponse, summary="Update mentorship status")
async def update_mentorship(
    connection_id: uuid.UUID,
    new_status: str = Query(..., regex="^(active|completed|rejected)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conn = await svc.update_mentorship_status(db, connection_id, new_status)
    return MentorshipConnectionResponse(
        id=conn.id, alumni_id=conn.alumni_id, student_id=conn.student_id,
        status=conn.status, message=conn.message, goals=conn.goals or [],
        created_at=conn.created_at,
    )


@router.get("/mentorship/mine", response_model=list[MentorshipConnectionResponse], summary="My mentorships")
async def my_mentorships(
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    connections = await svc.list_student_mentorships(db, current_user.id)
    result = []
    for c in connections:
        alumni_name = None
        if c.alumni and c.alumni.user:
            alumni_name = f"{c.alumni.user.first_name} {c.alumni.user.last_name}"
        result.append(MentorshipConnectionResponse(
            id=c.id, alumni_id=c.alumni_id, student_id=c.student_id,
            alumni_name=alumni_name,
            alumni_company=c.alumni.current_company if c.alumni else None,
            status=c.status, message=c.message, goals=c.goals or [],
            created_at=c.created_at,
        ))
    return result


@router.post("/sessions", response_model=MentorshipSessionResponse, summary="Schedule mentorship session")
async def schedule_session(
    data: MentorshipSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await svc.create_session(db, data)
    return MentorshipSessionResponse(
        id=session.id, connection_id=session.connection_id,
        scheduled_at=session.scheduled_at, duration_minutes=session.duration_minutes,
        topic=session.topic, meeting_link=session.meeting_link,
        status=session.status, created_at=session.created_at,
    )


@router.post("/sessions/{session_id}/feedback", response_model=MentorshipSessionResponse, summary="Rate session")
async def rate_session(
    session_id: uuid.UUID,
    feedback: SessionFeedback,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    session = await svc.submit_session_feedback(db, session_id, feedback)
    return MentorshipSessionResponse(
        id=session.id, connection_id=session.connection_id,
        scheduled_at=session.scheduled_at, duration_minutes=session.duration_minutes,
        topic=session.topic, notes=session.notes, meeting_link=session.meeting_link,
        status=session.status, student_rating=session.student_rating,
        student_feedback=session.student_feedback, created_at=session.created_at,
    )
