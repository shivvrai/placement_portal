"""
SQLAlchemy ORM models — Student Portfolio domain.
Tables: projects, certifications, internships, career_goals, resumes
"""

import uuid
from datetime import date, datetime, timezone
from sqlalchemy import String, Integer, Text, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, ARRAY, JSONB


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    technologies = mapped_column(ARRAY(String), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    domain: Mapped[str | None] = mapped_column(String(100))
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    student: Mapped["Student"] = relationship(back_populates="projects")

    @property
    def tech_stack(self) -> list[str]:
        return self.technologies or []

    @tech_stack.setter
    def tech_stack(self, val: list[str]):
        self.technologies = val

    @property
    def live_url(self) -> str | None:
        return self.url

    @live_url.setter
    def live_url(self, val: str | None):
        self.url = val


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(200))
    credential_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    credential_url: Mapped[str | None] = mapped_column(String(500))
    issue_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    student: Mapped["Student"] = relationship(back_populates="certifications")

    @property
    def name(self) -> str:
        return self.title

    @name.setter
    def name(self, val: str):
        self.title = val

    @property
    def issuing_organization(self) -> str | None:
        return self.issuer

    @issuing_organization.setter
    def issuing_organization(self, val: str | None):
        self.issuer = val

    @property
    def expiration_date(self) -> date | None:
        return self.expiry_date

    @expiration_date.setter
    def expiration_date(self, val: date | None):
        self.expiry_date = val


class Internship(Base):
    __tablename__ = "internships"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    employment_type: Mapped[str] = mapped_column(String(50), default="Internship")
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(Text)
    technologies = mapped_column(ARRAY(String), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    domain: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    student: Mapped["Student"] = relationship(back_populates="internships")

    @property
    def skills_used(self) -> list[str]:
        return self.technologies or []

    @skills_used.setter
    def skills_used(self, val: list[str]):
        self.technologies = val


WorkExperience = Internship


class CareerGoal(Base):
    __tablename__ = "career_goals"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    target_role: Mapped[str] = mapped_column(String(200), nullable=False)
    target_domain: Mapped[str | None] = mapped_column(String(100))
    target_companies = mapped_column(ARRAY(String), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    student: Mapped["Student"] = relationship(back_populates="career_goals")


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    parsed_data = mapped_column(JSONB, nullable=True)
    parse_status: Mapped[str] = mapped_column(String(20), default="pending")
    parse_error: Mapped[str | None] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime)

    student: Mapped["Student"] = relationship(back_populates="resumes")


from app.models.user import Student  # noqa: E402, F401
