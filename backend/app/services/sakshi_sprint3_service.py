"""
Service layer — Alumni Network & Mentorship, Placement Prep Resources, Feedback Surveys.

Sprint 3 — Sakshi Kumari
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from fastapi import HTTPException, status

from app.models.alumni import AlumniProfile, MentorshipConnection, MentorshipSession
from app.models.prep_resources import PrepResource, PrepCollection, PrepProgress
from app.models.feedback import FeedbackSurvey, SurveyQuestion, SurveyResponse as SurveyResponseModel
from app.schemas.sakshi_sprint3 import (
    AlumniProfileCreate, MentorshipRequestCreate, MentorshipSessionCreate,
    SessionFeedback, PrepResourceCreate, PrepCollectionCreate,
    PrepProgressUpdate, SurveyCreate, SurveySubmission,
)


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ═══════════════════════════════════════════════════════════════════
# ALUMNI & MENTORSHIP
# ═══════════════════════════════════════════════════════════════════

async def create_alumni_profile(db: AsyncSession, user_id: uuid.UUID, data: AlumniProfileCreate) -> AlumniProfile:
    profile = AlumniProfile(
        user_id=user_id,
        graduation_year=data.graduation_year,
        department_code=data.department_code,
        current_company=data.current_company,
        current_designation=data.current_designation,
        linkedin_url=data.linkedin_url,
        expertise_areas=data.expertise_areas,
        bio=data.bio,
        max_mentees=data.max_mentees,
    )
    db.add(profile)
    await db.flush()
    return profile


async def list_alumni(
    db: AsyncSession,
    department: Optional[str] = None,
    available_only: bool = True,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[AlumniProfile], int]:
    q = select(AlumniProfile)
    if department:
        q = q.where(AlumniProfile.department_code == department)
    if available_only:
        q = q.where(AlumniProfile.is_available_for_mentorship == True)  # noqa: E712

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(AlumniProfile.rating.desc()).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(q)).scalars().all()
    return list(rows), total


async def get_alumni_profile(db: AsyncSession, alumni_id: uuid.UUID) -> AlumniProfile:
    result = await db.execute(select(AlumniProfile).where(AlumniProfile.id == alumni_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumni profile not found")
    return profile


async def request_mentorship(db: AsyncSession, student_id: uuid.UUID, data: MentorshipRequestCreate) -> MentorshipConnection:
    # Check if connection already exists
    existing = await db.execute(
        select(MentorshipConnection).where(
            MentorshipConnection.alumni_id == data.alumni_id,
            MentorshipConnection.student_id == student_id,
            MentorshipConnection.status.in_(["pending", "active"]),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Active mentorship request already exists")

    connection = MentorshipConnection(
        alumni_id=data.alumni_id,
        student_id=student_id,
        message=data.message,
        goals=data.goals,
    )
    db.add(connection)
    await db.flush()
    return connection


async def update_mentorship_status(db: AsyncSession, connection_id: uuid.UUID, new_status: str) -> MentorshipConnection:
    result = await db.execute(select(MentorshipConnection).where(MentorshipConnection.id == connection_id))
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentorship connection not found")
    conn.status = new_status
    conn.updated_at = _utcnow()
    await db.flush()
    return conn


async def list_student_mentorships(db: AsyncSession, student_id: uuid.UUID) -> list[MentorshipConnection]:
    result = await db.execute(
        select(MentorshipConnection).where(MentorshipConnection.student_id == student_id)
        .order_by(MentorshipConnection.created_at.desc())
    )
    return list(result.scalars().all())


async def create_session(db: AsyncSession, data: MentorshipSessionCreate) -> MentorshipSession:
    session = MentorshipSession(
        connection_id=data.connection_id,
        scheduled_at=data.scheduled_at,
        duration_minutes=data.duration_minutes,
        topic=data.topic,
        meeting_link=data.meeting_link,
    )
    db.add(session)
    await db.flush()
    return session


async def submit_session_feedback(db: AsyncSession, session_id: uuid.UUID, feedback: SessionFeedback) -> MentorshipSession:
    result = await db.execute(select(MentorshipSession).where(MentorshipSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    session.student_rating = feedback.rating
    session.student_feedback = feedback.feedback
    session.status = "completed"
    await db.flush()
    return session


# ═══════════════════════════════════════════════════════════════════
# PLACEMENT PREP RESOURCES
# ═══════════════════════════════════════════════════════════════════

async def create_prep_resource(db: AsyncSession, data: PrepResourceCreate, user_id: uuid.UUID) -> PrepResource:
    resource = PrepResource(
        title=data.title,
        description=data.description,
        category=data.category,
        resource_type=data.resource_type,
        difficulty=data.difficulty,
        url=data.url,
        content=data.content,
        tags=data.tags,
        target_companies=data.target_companies,
        estimated_minutes=data.estimated_minutes,
        created_by=user_id,
    )
    db.add(resource)
    await db.flush()
    return resource


async def list_prep_resources(
    db: AsyncSession,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    resource_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[PrepResource], int]:
    q = select(PrepResource)
    if category:
        q = q.where(PrepResource.category == category)
    if difficulty:
        q = q.where(PrepResource.difficulty == difficulty)
    if resource_type:
        q = q.where(PrepResource.resource_type == resource_type)
    if search:
        q = q.where(PrepResource.title.ilike(f"%{search}%"))

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(PrepResource.upvotes.desc()).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(q)).scalars().all()
    return list(rows), total


async def get_prep_resource(db: AsyncSession, resource_id: uuid.UUID) -> PrepResource:
    result = await db.execute(select(PrepResource).where(PrepResource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    # Increment view count
    resource.view_count += 1
    await db.flush()
    return resource


async def upvote_resource(db: AsyncSession, resource_id: uuid.UUID) -> PrepResource:
    result = await db.execute(select(PrepResource).where(PrepResource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    resource.upvotes += 1
    await db.flush()
    return resource


async def update_prep_progress(
    db: AsyncSession, student_id: uuid.UUID, resource_id: uuid.UUID, data: PrepProgressUpdate
) -> PrepProgress:
    result = await db.execute(
        select(PrepProgress).where(
            PrepProgress.student_id == student_id,
            PrepProgress.resource_id == resource_id,
        )
    )
    progress = result.scalar_one_or_none()
    if not progress:
        progress = PrepProgress(student_id=student_id, resource_id=resource_id)
        db.add(progress)
    progress.status = data.status
    progress.progress_pct = data.progress_pct
    if data.notes:
        progress.notes = data.notes
    if data.status == "completed":
        progress.completed_at = _utcnow()
        progress.progress_pct = 100.0
    progress.updated_at = _utcnow()
    await db.flush()
    return progress


async def get_student_prep_progress(db: AsyncSession, student_id: uuid.UUID) -> list[PrepProgress]:
    result = await db.execute(
        select(PrepProgress).where(PrepProgress.student_id == student_id)
        .order_by(PrepProgress.updated_at.desc())
    )
    return list(result.scalars().all())


async def create_collection(db: AsyncSession, data: PrepCollectionCreate, user_id: uuid.UUID) -> PrepCollection:
    collection = PrepCollection(
        title=data.title,
        description=data.description,
        resource_ids=[str(rid) for rid in data.resource_ids],
        target_role=data.target_role,
        created_by=user_id,
    )
    db.add(collection)
    await db.flush()
    return collection


async def list_collections(db: AsyncSession) -> list[PrepCollection]:
    result = await db.execute(select(PrepCollection).order_by(PrepCollection.created_at.desc()))
    return list(result.scalars().all())


# ═══════════════════════════════════════════════════════════════════
# FEEDBACK SURVEYS
# ═══════════════════════════════════════════════════════════════════

async def create_survey(db: AsyncSession, data: SurveyCreate, creator_id: uuid.UUID) -> FeedbackSurvey:
    survey = FeedbackSurvey(
        title=data.title,
        description=data.description,
        survey_type=data.survey_type,
        target_audience=data.target_audience,
        drive_id=data.drive_id,
        is_anonymous=data.is_anonymous,
        created_by=creator_id,
    )
    db.add(survey)
    await db.flush()

    for i, q_data in enumerate(data.questions):
        question = SurveyQuestion(
            survey_id=survey.id,
            question_text=q_data.question_text,
            question_type=q_data.question_type,
            options=q_data.options,
            is_required=q_data.is_required,
            order_index=i,
        )
        db.add(question)
    await db.flush()
    return survey


async def list_surveys(db: AsyncSession, active_only: bool = True) -> list[FeedbackSurvey]:
    q = select(FeedbackSurvey)
    if active_only:
        q = q.where(FeedbackSurvey.is_active == True)  # noqa: E712
    q = q.order_by(FeedbackSurvey.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_survey(db: AsyncSession, survey_id: uuid.UUID) -> FeedbackSurvey:
    result = await db.execute(select(FeedbackSurvey).where(FeedbackSurvey.id == survey_id))
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    return survey


async def submit_survey_response(
    db: AsyncSession, survey_id: uuid.UUID, student_id: Optional[uuid.UUID], data: SurveySubmission
) -> SurveyResponseModel:
    # Check for duplicate submission
    if student_id:
        existing = await db.execute(
            select(SurveyResponseModel).where(
                SurveyResponseModel.survey_id == survey_id,
                SurveyResponseModel.student_id == student_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already submitted a response for this survey")

    response = SurveyResponseModel(
        survey_id=survey_id,
        student_id=student_id,
        answers=data.answers,
        overall_rating=data.overall_rating,
        additional_comments=data.additional_comments,
    )
    db.add(response)
    await db.flush()
    return response


async def get_survey_responses(db: AsyncSession, survey_id: uuid.UUID) -> list[SurveyResponseModel]:
    result = await db.execute(
        select(SurveyResponseModel).where(SurveyResponseModel.survey_id == survey_id)
        .order_by(SurveyResponseModel.submitted_at.desc())
    )
    return list(result.scalars().all())


async def get_survey_analytics(db: AsyncSession, survey_id: uuid.UUID) -> dict:
    survey = await get_survey(db, survey_id)
    responses = await get_survey_responses(db, survey_id)

    total = len(responses)
    ratings = [r.overall_rating for r in responses if r.overall_rating is not None]
    avg_rating = sum(ratings) / len(ratings) if ratings else None

    return {
        "survey_id": survey.id,
        "title": survey.title,
        "total_responses": total,
        "avg_rating": round(avg_rating, 2) if avg_rating else None,
        "question_stats": [],
        "sentiment_summary": f"{total} responses collected" if total else "No responses yet",
    }
