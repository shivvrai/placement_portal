"""
SQLAlchemy ORM models — Company Insights & Reviews domain.
Tables: company_reviews, company_insights

Sprint 3 — Anjula
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Text, Boolean, DateTime, Float, ForeignKey,
    CheckConstraint, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, JSONB


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CompanyReview(Base):
    """Student-submitted review of a company after placement/internship."""
    __tablename__ = "company_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("companies.id"), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    review_type: Mapped[str] = mapped_column(String(30), nullable=False)
    overall_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    work_culture_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    growth_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    compensation_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interview_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pros: Mapped[str] = mapped_column(Text, nullable=False)
    cons: Mapped[str] = mapped_column(Text, nullable=False)
    advice: Mapped[str | None] = mapped_column(Text, nullable=True)
    interview_process: Mapped[str | None] = mapped_column(Text, nullable=True)
    salary_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    upvotes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    student = relationship("Student", lazy="selectin")
    company = relationship("Company", lazy="selectin")

    __table_args__ = (
        CheckConstraint(
            "review_type IN ('placement', 'internship', 'ppo', 'off_campus')",
            name="ck_review_type",
        ),
        CheckConstraint(
            "overall_rating >= 1 AND overall_rating <= 5",
            name="ck_review_overall_rating",
        ),
        Index("idx_review_company_type", "company_name", "review_type"),
    )


class CompanyInsight(Base):
    """Aggregated company insight data (auto-computed or TPO-maintained)."""
    __tablename__ = "company_insights"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("companies.id"), nullable=True)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    total_hires_from_college: Mapped[int] = mapped_column(Integer, default=0)
    avg_package_lpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_package_lpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_package_lpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    hiring_frequency: Mapped[str | None] = mapped_column(String(30), nullable=True)
    common_roles = mapped_column(JSONB, nullable=True, default=list)
    required_skills = mapped_column(JSONB, nullable=True, default=list)
    selection_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_visited_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    company = relationship("Company", lazy="selectin")
