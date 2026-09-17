"""
SQLAlchemy ORM models — Academic domain.
Tables: semesters, subjects, academic_records, attendance
"""

import uuid
from datetime import date, datetime, timezone
from sqlalchemy import (
    String, Boolean, Integer, Numeric, Text, Date, DateTime, ForeignKey,
    UniqueConstraint, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Semester(Base):
    __tablename__ = "semesters"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    academic_records: Mapped[list["AcademicRecord"]] = relationship(back_populates="semester")
    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="semester")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("departments.id"))
    semester_number: Mapped[int] = mapped_column(Integer, nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    subject_type: Mapped[str] = mapped_column(String(20), default="core")
    syllabus_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    department: Mapped["Department"] = relationship(back_populates="subjects")
    academic_records: Mapped[list["AcademicRecord"]] = relationship(back_populates="subject")
    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="subject")
    curriculum_skills: Mapped[list["CurriculumSkill"]] = relationship(back_populates="subject")

    __table_args__ = (
        Index("idx_subjects_dept_sem", "department_id", "semester_number"),
    )


class AcademicRecord(Base):
    __tablename__ = "academic_records"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("subjects.id"), nullable=False, index=True)
    semester_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("semesters.id"), nullable=False)
    grade: Mapped[str | None] = mapped_column(String(5))
    grade_points: Mapped[float | None] = mapped_column(Numeric(3, 1))
    marks: Mapped[float | None] = mapped_column(Numeric(5, 2))
    max_marks: Mapped[float | None] = mapped_column(Numeric(5, 2))
    status: Mapped[str] = mapped_column(String(20), default="completed")

    student: Mapped["Student"] = relationship(back_populates="academic_records")
    subject: Mapped["Subject"] = relationship(back_populates="academic_records")
    semester: Mapped["Semester"] = relationship(back_populates="academic_records")

    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", "semester_id", name="uq_academic_record"),
    )


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("subjects.id"), nullable=False)
    semester_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("semesters.id"), nullable=False)
    total_classes: Mapped[int] = mapped_column(Integer, nullable=False)
    attended: Mapped[int] = mapped_column(Integer, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    student: Mapped["Student"] = relationship(back_populates="attendance_records")
    subject: Mapped["Subject"] = relationship(back_populates="attendance_records")
    semester: Mapped["Semester"] = relationship(back_populates="attendance_records")

    @property
    def percentage(self) -> float:
        if self.total_classes == 0:
            return 0.0
        return round((self.attended / self.total_classes) * 100, 2)

    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", "semester_id", name="uq_attendance"),
    )


from app.models.user import Department, Student  # noqa: E402, F401
from app.models.skill import CurriculumSkill  # noqa: E402, F401
