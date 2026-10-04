"""
Company Reviews & Insights API — student reviews, company rating, insights dashboard.

Sprint 3 — Anjula

Endpoints:
  POST   /companies/reviews           — Submit company review
  GET    /companies/reviews            — List reviews (filterable)
  POST   /companies/reviews/{id}/upvote — Upvote review
  GET    /companies/insights           — List all company insights
  GET    /companies/insights/{name}    — Company-specific insight
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker, get_current_student
from app.models.user import User
from app.schemas.anjula_sprint3 import (
    CompanyReviewCreate, CompanyReviewResponse,
    CompanyInsightResponse,
)
from app.schemas.common import MessageResponse, PaginatedResponse, PaginationMeta
from app.services import anjula_sprint3_service as svc

router = APIRouter(prefix="/companies", tags=["Company Reviews & Insights"])

_any_user = RoleChecker(["student", "tpo", "admin", "faculty", "hod"])


@router.post("/reviews", response_model=CompanyReviewResponse, summary="Submit company review")
async def create_review(
    data: CompanyReviewCreate,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    review = await svc.create_company_review(db, current_user.id, data)
    student_name = None
    if not review.is_anonymous and review.student and review.student.user:
        student_name = f"{review.student.user.first_name} {review.student.user.last_name}"
    return CompanyReviewResponse(
        id=review.id, student_name=student_name if not review.is_anonymous else "Anonymous",
        company_name=review.company_name, role=review.role,
        review_type=review.review_type, overall_rating=review.overall_rating,
        work_culture_rating=review.work_culture_rating, growth_rating=review.growth_rating,
        compensation_rating=review.compensation_rating, interview_rating=review.interview_rating,
        pros=review.pros, cons=review.cons, advice=review.advice,
        interview_process=review.interview_process, salary_range=review.salary_range,
        is_anonymous=review.is_anonymous, is_verified=review.is_verified,
        upvotes=review.upvotes, created_at=review.created_at,
    )


@router.get("/reviews", response_model=PaginatedResponse, summary="List company reviews")
async def list_reviews(
    company_name: Optional[str] = Query(None),
    review_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(_any_user),
    db: AsyncSession = Depends(get_db),
):
    reviews, total = await svc.list_company_reviews(db, company_name, review_type, page, per_page)
    items = [CompanyReviewResponse(
        id=r.id,
        student_name="Anonymous" if r.is_anonymous else (
            f"{r.student.user.first_name} {r.student.user.last_name}" if r.student and r.student.user else None
        ),
        company_name=r.company_name, role=r.role,
        review_type=r.review_type, overall_rating=r.overall_rating,
        work_culture_rating=r.work_culture_rating, growth_rating=r.growth_rating,
        compensation_rating=r.compensation_rating, interview_rating=r.interview_rating,
        pros=r.pros, cons=r.cons, advice=r.advice,
        interview_process=r.interview_process, salary_range=r.salary_range,
        is_anonymous=r.is_anonymous, is_verified=r.is_verified,
        upvotes=r.upvotes, created_at=r.created_at,
    ) for r in reviews]
    return PaginatedResponse(
        data=[i.model_dump() for i in items],
        pagination=PaginationMeta(page=page, per_page=per_page, total=total),
    )


@router.post("/reviews/{review_id}/upvote", response_model=MessageResponse, summary="Upvote review")
async def upvote_review(
    review_id: uuid.UUID,
    current_user: User = Depends(_any_user),
    db: AsyncSession = Depends(get_db),
):
    r = await svc.upvote_review(db, review_id)
    return MessageResponse(message=f"Upvoted! Total: {r.upvotes}")


@router.get("/insights", response_model=PaginatedResponse, summary="List company insights")
async def list_insights(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(_any_user),
    db: AsyncSession = Depends(get_db),
):
    insights, total = await svc.list_company_insights(db, page, per_page)
    items = [CompanyInsightResponse(
        id=ci.id, company_name=ci.company_name, avg_rating=ci.avg_rating,
        total_reviews=ci.total_reviews, total_hires_from_college=ci.total_hires_from_college,
        avg_package_lpa=ci.avg_package_lpa, max_package_lpa=ci.max_package_lpa,
        min_package_lpa=ci.min_package_lpa, hiring_frequency=ci.hiring_frequency,
        common_roles=ci.common_roles or [], required_skills=ci.required_skills or [],
        selection_ratio=ci.selection_ratio, last_visited_at=ci.last_visited_at,
    ) for ci in insights]
    return PaginatedResponse(
        data=[i.model_dump() for i in items],
        pagination=PaginationMeta(page=page, per_page=per_page, total=total),
    )


@router.get("/insights/{company_name}", response_model=CompanyInsightResponse, summary="Company insight")
async def get_insight(
    company_name: str,
    current_user: User = Depends(_any_user),
    db: AsyncSession = Depends(get_db),
):
    ci = await svc.get_company_insight(db, company_name)
    return CompanyInsightResponse(
        id=ci.id, company_name=ci.company_name, avg_rating=ci.avg_rating,
        total_reviews=ci.total_reviews, total_hires_from_college=ci.total_hires_from_college,
        avg_package_lpa=ci.avg_package_lpa, max_package_lpa=ci.max_package_lpa,
        min_package_lpa=ci.min_package_lpa, hiring_frequency=ci.hiring_frequency,
        common_roles=ci.common_roles or [], required_skills=ci.required_skills or [],
        selection_ratio=ci.selection_ratio, last_visited_at=ci.last_visited_at,
    )
