"""
SQLAlchemy ORM models — Learning & Roadmap domain.
Tables: resources, resource_skills, roadmaps, roadmap_tasks
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Numeric, Text, DateTime, ForeignKey,
    Boolean, CheckConstraint, UniqueConstraint, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, JSONB


def utcnow():
    return datetime.now(timezone.utc)


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(30), nullable=False)
    platform: Mapped[str | None] = mapped_column(String(100))
    difficulty: Mapped[str | None] = mapped_column(String(20))
    estimated_hours: Mapped[float | None] = mapped_column(Numeric(5, 1))
    description: Mapped[str | None] = mapped_column(Text)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    resource_skills: Mapped[list["ResourceSkill"]] = relationship(back_populates="resource")

    __table_args__ = (
        CheckConstraint(
            "resource_type IN ('course','tutorial','documentation','video','book','practice','article')",
            name="ck_resource_type",
        ),
        CheckConstraint("difficulty IN ('beginner','intermediate','advanced')", name="ck_resource_difficulty"),
    )


class ResourceSkill(Base):
    __tablename__ = "resource_skills"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    resource_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("resources.id"), nullable=False, index=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("skills.id"), nullable=False, index=True)
    relevance: Mapped[float] = mapped_column(Numeric(3, 2), default=0.8)

    resource: Mapped["Resource"] = relationship(back_populates="resource_skills")
    skill: Mapped["Skill"] = relationship(back_populates="resource_skills")

    __table_args__ = (
        UniqueConstraint("resource_id", "skill_id", name="uq_resource_skill"),
    )


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    target_role: Mapped[str] = mapped_column(String(200), nullable=False)
    total_weeks: Mapped[int] = mapped_column(Integer, default=12)
    status: Mapped[str] = mapped_column(String(20), default="active")
    progress_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    student: Mapped["Student"] = relationship(back_populates="roadmaps")
    tasks: Mapped[list["RoadmapTask"]] = relationship(
        back_populates="roadmap",
        order_by="RoadmapTask.week_number, RoadmapTask.order_in_week",
    )

    __table_args__ = (
        CheckConstraint("status IN ('active','paused','completed','archived')", name="ck_roadmap_status"),
    )


class RoadmapTask(Base):
    __tablename__ = "roadmap_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    roadmap_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("skills.id"))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("resources.id"))
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    order_in_week: Mapped[int] = mapped_column(Integer, default=1)
    estimated_hours: Mapped[float | None] = mapped_column(Numeric(5, 1))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    roadmap: Mapped["Roadmap"] = relationship(back_populates="tasks")

    __table_args__ = (
        CheckConstraint("status IN ('pending','in_progress','completed','skipped')", name="ck_roadmap_task_status"),
        Index("idx_roadmap_tasks_week", "roadmap_id", "week_number"),
    )


from app.models.skill import Skill  # noqa: E402, F401
from app.models.user import Student  # noqa: E402, F401
