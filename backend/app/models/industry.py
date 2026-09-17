"""
SQLAlchemy ORM models — Industry & Jobs domain.
Tables: companies, jobs, job_skills, industry_skill_trends
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Numeric, Text, DateTime, ForeignKey,
    UniqueConstraint, Index, CheckConstraint, Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, ARRAY, JSONB, Vector


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    domain: Mapped[str | None] = mapped_column(String(100))
    industry: Mapped[str | None] = mapped_column(String(100))
    website: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(200))
    company_size: Mapped[str | None] = mapped_column(String(50))
    data_source: Mapped[str] = mapped_column(String(30), default="curated")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    jobs: Mapped[list["Job"]] = relationship(back_populates="company")
    placement_drives: Mapped[list["PlacementDrive"]] = relationship(back_populates="company")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("companies.id"), index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    role_category: Mapped[str | None] = mapped_column(String(100), index=True)
    min_cgpa: Mapped[float | None] = mapped_column(Numeric(4, 2))
    min_experience_years: Mapped[int | None] = mapped_column(Integer, default=0)
    location: Mapped[str | None] = mapped_column(String(200))
    job_type: Mapped[str | None] = mapped_column(String(30))
    salary_min: Mapped[float | None] = mapped_column(Numeric(12, 2))
    salary_max: Mapped[float | None] = mapped_column(Numeric(12, 2))
    eligible_departments = mapped_column(ARRAY(String), nullable=True)
    embedding = mapped_column(Vector(384), nullable=True)
    data_source: Mapped[str] = mapped_column(String(30), default="curated")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    company: Mapped["Company | None"] = relationship(back_populates="jobs")
    job_skills: Mapped[list["JobSkill"]] = relationship(back_populates="job")

    __table_args__ = (
        Index("idx_jobs_category_active", "role_category", "is_active"),
    )


class JobSkill(Base):
    __tablename__ = "job_skills"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("jobs.id"), nullable=False, index=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("skills.id"), nullable=False, index=True)
    importance: Mapped[str] = mapped_column(String(20), default="required")
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), default=0.8)

    job: Mapped["Job"] = relationship(back_populates="job_skills")
    skill: Mapped["Skill"] = relationship(back_populates="job_skills")

    __table_args__ = (
        UniqueConstraint("job_id", "skill_id", name="uq_job_skill"),
        CheckConstraint("importance IN ('required','preferred','nice_to_have')", name="ck_job_skill_importance"),
    )


class IndustrySkillTrend(Base):
    __tablename__ = "industry_skill_trends"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    skill_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("skills.id"), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    demand_count: Mapped[int] = mapped_column(Integer, nullable=False)
    demand_percentage: Mapped[float] = mapped_column(Numeric(5, 2))
    growth_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    __table_args__ = (
        UniqueConstraint("skill_id", "period", name="uq_skill_trend_period"),
    )


from app.models.placement import PlacementDrive  # noqa: E402, F401
from app.models.skill import Skill  # noqa: E402, F401
