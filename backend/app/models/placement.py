"""
SQLAlchemy ORM models — Placement domain.
Tables: placement_drives, applications, interview_stages, placement_outcomes
"""

import uuid
from datetime import date, datetime, timezone
from sqlalchemy import (
    String, Integer, Numeric, Text, Date, DateTime, ForeignKey,
    Boolean, CheckConstraint, UniqueConstraint, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, ARRAY, JSONB


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PlacementDrive(Base):
    __tablename__ = "placement_drives"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("companies.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    drive_date: Mapped[date | None] = mapped_column(Date)
    registration_deadline: Mapped[datetime | None] = mapped_column(DateTime)
    min_cgpa: Mapped[float | None] = mapped_column(Numeric(4, 2))
    eligible_departments = mapped_column(ARRAY(String), nullable=True)
    max_backlogs: Mapped[int | None] = mapped_column(Integer, default=0)
    roles_offered = mapped_column(ARRAY(String), nullable=True)
    salary_ctc: Mapped[float | None] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), default="upcoming")
    academic_year: Mapped[str | None] = mapped_column(String(10))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    company: Mapped["Company"] = relationship(back_populates="placement_drives")
    applications: Mapped[list["Application"]] = relationship(back_populates="drive")

    __table_args__ = (
        CheckConstraint(
            "status IN ('upcoming','open','in_progress','completed','cancelled')",
            name="ck_drive_status",
        ),
    )


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    drive_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("placement_drives.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="applied")
    current_stage: Mapped[str | None] = mapped_column(String(50))
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    # Offer details — populated by TPO after candidate is selected
    offer_ctc_lpa: Mapped[float | None] = mapped_column(Numeric(8, 2))
    offer_fixed_lpa: Mapped[float | None] = mapped_column(Numeric(8, 2))
    offer_variable_lpa: Mapped[float | None] = mapped_column(Numeric(8, 2))
    offer_designation: Mapped[str | None] = mapped_column(String(200))
    offer_joining_date: Mapped[date | None] = mapped_column(Date)
    offer_reference_number: Mapped[str | None] = mapped_column(String(100))
    offer_recorded_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Offer Letter Pipeline — added in Sprint 3
    offer_letter_url: Mapped[str | None] = mapped_column(String(500))
    offer_letter_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime)
    offer_letter_status: Mapped[str] = mapped_column(String(20), default="pending")
    offer_accepted_at: Mapped[datetime | None] = mapped_column(DateTime)
    offer_declined_reason: Mapped[str | None] = mapped_column(Text)
    offer_joining_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    offer_joining_date_confirmed: Mapped[date | None] = mapped_column(Date)

    # Shortlisting metadata — reasons for pass/fail per applicant
    extra_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True, name="metadata")

    student: Mapped["Student"] = relationship(back_populates="applications")
    drive: Mapped["PlacementDrive"] = relationship(back_populates="applications")
    stages: Mapped[list["InterviewStage"]] = relationship(back_populates="application")

    __table_args__ = (
        UniqueConstraint("student_id", "drive_id", name="uq_student_drive_application"),
        CheckConstraint(
            "status IN ('applied','shortlisted','in_progress','selected','rejected','withdrawn')",
            name="ck_application_status",
        ),
        CheckConstraint(
            "offer_letter_status IN ('pending','uploaded','accepted','declined')",
            name="ck_offer_letter_status",
        ),
    )



class InterviewStage(Base):
    __tablename__ = "interview_stages"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("applications.id"), nullable=False, index=True)
    stage_name: Mapped[str] = mapped_column(String(100), nullable=False)
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    feedback: Mapped[str | None] = mapped_column(Text)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    application: Mapped["Application"] = relationship(back_populates="stages")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','scheduled','completed','passed','failed','skipped')",
            name="ck_stage_status",
        ),
    )


class PlacementOutcome(Base):
    __tablename__ = "placement_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    salary_ctc: Mapped[float | None] = mapped_column(Numeric(12, 2))
    placement_type: Mapped[str] = mapped_column(String(20), default="on_campus")
    academic_year: Mapped[str | None] = mapped_column(String(10))
    data_type: Mapped[str] = mapped_column(String(20), default="real")
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    student: Mapped["Student"] = relationship(back_populates="placement_outcomes")

    __table_args__ = (
        CheckConstraint("data_type IN ('real','synthetic')", name="ck_outcome_data_type"),
    )


from app.models.industry import Company  # noqa: E402, F401
from app.models.user import Student  # noqa: E402, F401
