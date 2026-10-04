"""
SQLAlchemy ORM models — Application Tracker & Status Timeline domain.
Tables: application_timeline_events

Sprint 3 — Anjula
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Text, DateTime, ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, JSONB


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ApplicationTimelineEvent(Base):
    """Immutable audit log of every application status change."""
    __tablename__ = "application_timeline_events"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("applications.id"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=True)
    metadata_payload = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    application = relationship("Application", lazy="selectin")
    student = relationship("Student", lazy="selectin")
    actor = relationship("User", lazy="selectin")

    __table_args__ = (
        Index("idx_timeline_app_created", "application_id", "created_at"),
        Index("idx_timeline_student", "student_id", "created_at"),
    )
