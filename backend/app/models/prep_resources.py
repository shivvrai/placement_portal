"""
SQLAlchemy ORM models — Placement Preparation Resources domain.
Tables: prep_resources, prep_collections, prep_progress

Sprint 3 — Sakshi Kumari
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


class PrepResource(Base):
    """Individual placement preparation resource (article, video, problem set, etc.)."""
    __tablename__ = "prep_resources"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(30), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags = mapped_column(JSONB, nullable=True, default=list)
    target_companies = mapped_column(JSONB, nullable=True, default=list)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30)
    author_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    upvotes: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    creator = relationship("User", lazy="selectin")

    __table_args__ = (
        CheckConstraint(
            "category IN ('aptitude', 'coding', 'system_design', 'behavioral', 'hr', 'gd', 'case_study', 'resume', 'general')",
            name="ck_prep_category",
        ),
        CheckConstraint(
            "resource_type IN ('article', 'video', 'problem_set', 'mock_test', 'cheatsheet', 'roadmap', 'template')",
            name="ck_prep_resource_type",
        ),
        CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced')",
            name="ck_prep_difficulty",
        ),
        Index("idx_prep_cat_diff", "category", "difficulty"),
    )


class PrepCollection(Base):
    """Curated collection / playlist of prep resources."""
    __tablename__ = "prep_collections"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resource_ids = mapped_column(JSONB, nullable=True, default=list)
    target_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    creator = relationship("User", lazy="selectin")


class PrepProgress(Base):
    """Student progress tracking for a specific prep resource."""
    __tablename__ = "prep_progress"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    resource_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("prep_resources.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="not_started", nullable=False)
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0)
    time_spent_minutes: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    student = relationship("Student", lazy="selectin")
    resource = relationship("PrepResource", lazy="selectin")

    __table_args__ = (
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed', 'bookmarked')",
            name="ck_prep_progress_status",
        ),
        Index("idx_prep_progress_student_resource", "student_id", "resource_id", unique=True),
    )
