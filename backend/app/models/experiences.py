"""
SQLAlchemy ORM models — Interview Experiences & Question Bank domain.
Table: interview_experiences
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Text, DateTime, ForeignKey,
    CheckConstraint, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, JSONB


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class InterviewExperience(Base):
    __tablename__ = "interview_experiences"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    placement_drive_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("placement_drives.id"), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    verdict: Mapped[str] = mapped_column(String(30), nullable=False)
    overall_experience: Mapped[str] = mapped_column(Text, nullable=False)
    questions_asked = mapped_column(JSONB, nullable=True, default=list)
    tips_for_juniors: Mapped[str | None] = mapped_column(Text)
    upvotes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    student = relationship("Student", lazy="selectin")
    drive = relationship("PlacementDrive", lazy="selectin")

    __table_args__ = (
        CheckConstraint(
            "difficulty IN ('Easy', 'Medium', 'Hard')",
            name="ck_experience_difficulty",
        ),
        CheckConstraint(
            "verdict IN ('Selected', 'Rejected', 'In Progress')",
            name="ck_experience_verdict",
        ),
        Index("idx_exp_company_diff", "company_name", "difficulty"),
    )
