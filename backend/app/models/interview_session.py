"""
SQLAlchemy ORM model — Mock Interview Sessions.
Dedicated table for the V2 mock interview engine with structured lifecycle,
transcript storage, performance scoring, and filler-word analytics.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Float, Text, DateTime, ForeignKey,
    CheckConstraint, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, JSONB, ARRAY


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class MockInterviewSession(Base):
    __tablename__ = "mock_interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("students.id"), nullable=False, index=True
    )

    # Interview configuration
    role_target: Mapped[str] = mapped_column(String(200), nullable=False)
    company_style: Mapped[str] = mapped_column(String(50), nullable=False, default="Product")
    difficulty: Mapped[str] = mapped_column(String(30), nullable=False, default="campus")

    # Lifecycle state
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="setup"
    )  # setup | intro | technical | behavioral | completed
    current_round: Mapped[int] = mapped_column(Integer, default=0)

    # Conversation data
    transcript = mapped_column(JSONB, nullable=True, default=list)
    # Each entry: {role: "interviewer"|"candidate", content: str, timestamp: str, analysis: dict|None}

    questions_asked = mapped_column(ARRAY(String), nullable=True, default=list)

    # Performance scoring (populated progressively and finalized at completion)
    performance_scores = mapped_column(JSONB, nullable=True)
    # {communication: int, technical: int, confidence: int, relevance: int}

    # Final report (populated when status=completed)
    final_report = mapped_column(JSONB, nullable=True)
    # {verdict, technical_score, communication_score, confidence_score, relevance_score,
    #  strengths: [{point, evidence}], improvements: [{point, advice}], ...}

    # Analytics
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    word_count: Mapped[int | None] = mapped_column(Integer)
    filler_word_count: Mapped[int | None] = mapped_column(Integer, default=0)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationships
    student: Mapped["Student"] = relationship(backref="mock_interview_sessions")

    __table_args__ = (
        CheckConstraint(
            "status IN ('setup','intro','technical','behavioral','completed')",
            name="ck_mock_interview_status",
        ),
        CheckConstraint(
            "difficulty IN ('campus','fresher','experienced')",
            name="ck_mock_interview_difficulty",
        ),
        Index("idx_mock_interview_student_status", "student_id", "status"),
    )


from app.models.user import Student  # noqa: E402, F401
