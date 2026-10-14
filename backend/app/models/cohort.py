"""
SQLAlchemy ORM models — TPO Talent Cohorts & Notifications.
Tables: student_cohorts, notifications
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.core.db_types import UUIDType, JSONB


def utcnow():
    return datetime.now(timezone.utc)


class StudentCohort(Base):
    __tablename__ = "student_cohorts"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=False)
    criteria = mapped_column(JSONB, nullable=False)   # The filter payload used to generate this cohort
    student_ids = mapped_column(JSONB, nullable=False)  # List of student UUID strings at time of creation
    student_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)


from app.models.notification import Notification

