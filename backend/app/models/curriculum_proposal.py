"""
SQLAlchemy ORM model — Curriculum Proposals.
Stores AI-generated BoS curriculum modernization proposals with
gap analysis data, proposed subjects, impact projections, and HOD review workflow.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Text, DateTime, ForeignKey, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, JSONB


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CurriculumProposal(Base):
    __tablename__ = "curriculum_proposals"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    department_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g. "2026-27"

    # Who created this proposal
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )

    # Workflow status
    status: Mapped[str] = mapped_column(String(20), default="draft")

    # AI-generated content (JSONB)
    gap_analysis = mapped_column(JSONB, nullable=True)
    # {coverage_pct, gap_skills: [], redundant_topics: [], high_demand_uncovered: [], ...}

    proposed_subjects = mapped_column(JSONB, nullable=True)
    # [{name, code, credits, semester, topics, learning_outcomes, textbooks, mapped_skills, demand_score}, ...]

    impact_projection = mapped_column(JSONB, nullable=True)
    # {current_coverage, projected_coverage, improvement_pct, ...}

    # HOD review
    hod_comments: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    # Relationships
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])
    reviewer: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by])

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','submitted','approved','rejected')",
            name="ck_proposal_status",
        ),
    )


from app.models.user import User  # noqa: E402, F401
