"""
Feedback Surveys API — TPO creates surveys, students submit responses, analytics.

Sprint 3 — Sakshi Kumari

Endpoints:
  POST   /surveys              — Create survey (TPO)
  GET    /surveys              — List active surveys
  GET    /surveys/{id}         — Get survey with questions
  POST   /surveys/{id}/submit  — Submit survey response
  GET    /surveys/{id}/responses — View responses (TPO)
  GET    /surveys/{id}/analytics — Survey analytics (TPO)
"""

import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker, get_current_student
from app.models.user import User
from app.schemas.sakshi_sprint3 import (
    SurveyCreate, SurveyResponse, SurveyQuestionResponse,
    SurveySubmission, SurveyResponseDetail, SurveyAnalytics,
)
from app.schemas.common import MessageResponse
from app.services import sakshi_sprint3_service as svc

router = APIRouter(prefix="/surveys", tags=["Feedback Surveys"])

_tpo_admin = RoleChecker(["tpo", "admin"])
_any_user = RoleChecker(["student", "tpo", "admin", "faculty", "hod"])


@router.post("", response_model=SurveyResponse, summary="Create feedback survey")
async def create_survey(
    data: SurveyCreate,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    survey = await svc.create_survey(db, data, current_user.id)
    return SurveyResponse(
        id=survey.id, title=survey.title, description=survey.description,
        survey_type=survey.survey_type, target_audience=survey.target_audience,
        is_anonymous=survey.is_anonymous, is_active=survey.is_active,
        questions=[SurveyQuestionResponse(
            id=q.id, question_text=q.question_text, question_type=q.question_type,
            options=q.options or [], is_required=q.is_required, order_index=q.order_index,
        ) for q in (survey.questions or [])],
        created_at=survey.created_at,
    )


@router.get("", response_model=list[SurveyResponse], summary="List active surveys")
async def list_surveys(
    active_only: bool = Query(True),
    current_user: User = Depends(_any_user),
    db: AsyncSession = Depends(get_db),
):
    surveys = await svc.list_surveys(db, active_only)
    return [SurveyResponse(
        id=s.id, title=s.title, description=s.description,
        survey_type=s.survey_type, target_audience=s.target_audience,
        is_anonymous=s.is_anonymous, is_active=s.is_active,
        questions=[SurveyQuestionResponse(
            id=q.id, question_text=q.question_text, question_type=q.question_type,
            options=q.options or [], is_required=q.is_required, order_index=q.order_index,
        ) for q in (s.questions or [])],
        created_at=s.created_at,
    ) for s in surveys]


@router.get("/{survey_id}", response_model=SurveyResponse, summary="Get survey detail")
async def get_survey(
    survey_id: uuid.UUID,
    current_user: User = Depends(_any_user),
    db: AsyncSession = Depends(get_db),
):
    s = await svc.get_survey(db, survey_id)
    return SurveyResponse(
        id=s.id, title=s.title, description=s.description,
        survey_type=s.survey_type, target_audience=s.target_audience,
        is_anonymous=s.is_anonymous, is_active=s.is_active,
        questions=[SurveyQuestionResponse(
            id=q.id, question_text=q.question_text, question_type=q.question_type,
            options=q.options or [], is_required=q.is_required, order_index=q.order_index,
        ) for q in (s.questions or [])],
        created_at=s.created_at,
    )


@router.post("/{survey_id}/submit", response_model=MessageResponse, summary="Submit survey response")
async def submit_response(
    survey_id: uuid.UUID,
    data: SurveySubmission,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    survey = await svc.get_survey(db, survey_id)
    student_id = None if survey.is_anonymous else current_user.id
    await svc.submit_survey_response(db, survey_id, student_id, data)
    return MessageResponse(message="Survey response submitted successfully")


@router.get("/{survey_id}/responses", response_model=list[SurveyResponseDetail], summary="View responses (TPO)")
async def get_responses(
    survey_id: uuid.UUID,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    responses = await svc.get_survey_responses(db, survey_id)
    return [SurveyResponseDetail(
        id=r.id, survey_id=r.survey_id,
        student_name=f"{r.student.user.first_name} {r.student.user.last_name}" if r.student and r.student.user else "Anonymous",
        answers=r.answers, overall_rating=r.overall_rating,
        additional_comments=r.additional_comments, submitted_at=r.submitted_at,
    ) for r in responses]


@router.get("/{survey_id}/analytics", response_model=SurveyAnalytics, summary="Survey analytics")
async def survey_analytics(
    survey_id: uuid.UUID,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    analytics = await svc.get_survey_analytics(db, survey_id)
    return SurveyAnalytics(**analytics)
