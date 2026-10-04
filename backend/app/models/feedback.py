"""
SQLAlchemy ORM models — Student Feedback & Satisfaction Surveys domain.
Tables: feedback_surveys, survey_questions, survey_responses

Sprint 3 — Sakshi Kumari
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Text, Boolean, DateTime, ForeignKey,
    CheckConstraint, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, JSONB


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class FeedbackSurvey(Base):
    """TPO-created satisfaction survey template."""
    __tablename__ = "feedback_surveys"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    survey_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    target_audience: Mapped[str] = mapped_column(String(30), default="all_students")
    drive_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("placement_drives.id"), nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    creator = relationship("User", lazy="selectin")
    drive = relationship("PlacementDrive", lazy="selectin")
    questions = relationship("SurveyQuestion", back_populates="survey", lazy="selectin", order_by="SurveyQuestion.order_index")

    __table_args__ = (
        CheckConstraint(
            "survey_type IN ('placement_experience', 'training_feedback', 'general_satisfaction', 'drive_specific', 'faculty_feedback')",
            name="ck_survey_type",
        ),
    )


class SurveyQuestion(Base):
    """Individual question within a feedback survey."""
    __tablename__ = "survey_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("feedback_surveys.id"), nullable=False, index=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(20), nullable=False)
    options = mapped_column(JSONB, nullable=True, default=list)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    survey = relationship("FeedbackSurvey", back_populates="questions")

    __table_args__ = (
        CheckConstraint(
            "question_type IN ('rating', 'text', 'mcq', 'checkbox', 'scale', 'yes_no')",
            name="ck_question_type",
        ),
    )


class SurveyResponse(Base):
    """Student's response to a feedback survey."""
    __tablename__ = "survey_responses"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("feedback_surveys.id"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=True, index=True)
    answers = mapped_column(JSONB, nullable=False)
    overall_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    additional_comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    survey = relationship("FeedbackSurvey", lazy="selectin")
    student = relationship("Student", lazy="selectin")

    __table_args__ = (
        CheckConstraint(
            "overall_rating IS NULL OR (overall_rating >= 1 AND overall_rating <= 5)",
            name="ck_response_rating_range",
        ),
        Index("idx_response_survey_student", "survey_id", "student_id"),
    )
