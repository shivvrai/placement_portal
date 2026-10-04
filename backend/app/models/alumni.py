"""
SQLAlchemy ORM models — Alumni Network & Mentorship domain.
Tables: alumni_profiles, mentorship_connections, mentorship_sessions

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


class AlumniProfile(Base):
    """Registered alumni who opted into the mentorship network."""
    __tablename__ = "alumni_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=False)
    department_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    current_company: Mapped[str] = mapped_column(String(200), nullable=False)
    current_designation: Mapped[str] = mapped_column(String(200), nullable=False)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    expertise_areas = mapped_column(JSONB, nullable=True, default=list)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_available_for_mentorship: Mapped[bool] = mapped_column(Boolean, default=True)
    max_mentees: Mapped[int] = mapped_column(Integer, default=3)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True, default=0.0)
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", lazy="selectin")
    mentorship_connections = relationship("MentorshipConnection", back_populates="alumni", lazy="selectin")

    __table_args__ = (
        Index("idx_alumni_dept_year", "department_code", "graduation_year"),
    )


class MentorshipConnection(Base):
    """Active mentorship pairing between an alumni mentor and a student mentee."""
    __tablename__ = "mentorship_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    alumni_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("alumni_profiles.id"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    goals = mapped_column(JSONB, nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    alumni = relationship("AlumniProfile", back_populates="mentorship_connections", lazy="selectin")
    student = relationship("Student", lazy="selectin")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'active', 'completed', 'rejected')",
            name="ck_mentorship_status",
        ),
        Index("idx_mentorship_student_status", "student_id", "status"),
    )


class MentorshipSession(Base):
    """Individual mentorship meeting / session log."""
    __tablename__ = "mentorship_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    connection_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("mentorship_connections.id"), nullable=False, index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    topic: Mapped[str] = mapped_column(String(300), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    meeting_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled", nullable=False)
    student_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    student_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    connection = relationship("MentorshipConnection", lazy="selectin")

    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'completed', 'cancelled', 'no_show')",
            name="ck_session_status",
        ),
        CheckConstraint(
            "student_rating IS NULL OR (student_rating >= 1 AND student_rating <= 5)",
            name="ck_session_rating_range",
        ),
    )
