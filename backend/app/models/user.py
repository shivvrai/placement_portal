"""
SQLAlchemy ORM models — Identity & Auth domain.
Tables: users, departments, students, faculty
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Boolean, Integer, Numeric, Text, DateTime, ForeignKey,
    Index, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, ARRAY, JSONB


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(15))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    student: Mapped["Student | None"] = relationship(back_populates="user", uselist=False)
    faculty_profile: Mapped["Faculty | None"] = relationship(back_populates="user", uselist=False)

    __table_args__ = (
        CheckConstraint("role IN ('student','tpo','faculty','hod','admin')", name="ck_users_role"),
    )


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    students: Mapped[list["Student"]] = relationship(back_populates="department")
    faculty_members: Mapped[list["Faculty"]] = relationship(back_populates="department")
    subjects: Mapped[list["Subject"]] = relationship(back_populates="department")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"), primary_key=True)
    roll_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("departments.id"), nullable=False, index=True)
    current_semester: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    admission_year: Mapped[int] = mapped_column(Integer, nullable=False)
    cgpa: Mapped[float | None] = mapped_column(Numeric(4, 2), index=True)
    ums_student_id: Mapped[str | None] = mapped_column(String(50))
    github_url: Mapped[str | None] = mapped_column(String(500))
    portfolio_url: Mapped[str | None] = mapped_column(String(500))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    bio: Mapped[str | None] = mapped_column(Text)
    resume_url: Mapped[str | None] = mapped_column(String(500))
    resume_parsed: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_resume_analysis: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_profile_visible: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship(back_populates="student")
    department: Mapped["Department"] = relationship(back_populates="students")
    academic_records: Mapped[list["AcademicRecord"]] = relationship(back_populates="student")
    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="student")
    skills: Mapped[list["StudentSkill"]] = relationship(back_populates="student")
    projects: Mapped[list["Project"]] = relationship(back_populates="student")
    certifications: Mapped[list["Certification"]] = relationship(back_populates="student")
    internships: Mapped[list["Internship"]] = relationship(back_populates="student")
    career_goals: Mapped[list["CareerGoal"]] = relationship(back_populates="student")
    resumes: Mapped[list["Resume"]] = relationship(back_populates="student")
    applications: Mapped[list["Application"]] = relationship(back_populates="student")
    placement_outcomes: Mapped[list["PlacementOutcome"]] = relationship(back_populates="student")
    roadmaps: Mapped[list["Roadmap"]] = relationship(back_populates="student")
    copilot_conversations: Mapped[list["CopilotConversation"]] = relationship(back_populates="student")


class Faculty(Base):
    __tablename__ = "faculty"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"), primary_key=True)
    department_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("departments.id"), nullable=False)
    designation: Mapped[str | None] = mapped_column(String(100))
    is_hod: Mapped[bool] = mapped_column(Boolean, default=False)
    employee_id: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship(back_populates="faculty_profile")
    department: Mapped["Department"] = relationship(back_populates="faculty_members")


from app.models.academic import Subject, AcademicRecord, Attendance  # noqa: E402, F401
from app.models.skill import StudentSkill  # noqa: E402, F401
from app.models.portfolio import Project, Certification, Internship, CareerGoal, Resume  # noqa: E402, F401
from app.models.placement import Application, PlacementOutcome  # noqa: E402, F401
from app.models.roadmap import Roadmap  # noqa: E402, F401
from app.models.system import CopilotConversation  # noqa: E402, F401
