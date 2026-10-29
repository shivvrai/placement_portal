"""
SQLAlchemy ORM models — Exam Upload domain.
Tables: exam_uploads, exam_student_results

TPO uploads PDF/Excel sheets with dynamic columns (marks, test details, etc.)
The system parses them, stores row-level data, and computes rankings.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Float, Text, DateTime, ForeignKey, Index, Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, JSONB


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ExamUpload(Base):
    """
    Represents a single uploaded exam/assessment sheet.
    The parsed data with dynamic columns is stored as JSON.
    """
    __tablename__ = "exam_uploads"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Who uploaded it
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=False)

    # File info
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'pdf', 'xlsx', 'xls', 'csv'
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Parsed metadata
    column_headers = mapped_column(JSONB, nullable=True)  # List of detected column names
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    total_columns: Mapped[int] = mapped_column(Integer, default=0)

    # Filtering context
    department: Mapped[str | None] = mapped_column(String(100), index=True)
    section: Mapped[str | None] = mapped_column(String(50), index=True)
    semester: Mapped[int | None] = mapped_column(Integer)
    exam_type: Mapped[str | None] = mapped_column(String(100))  # 'MST-1', 'MST-2', 'End Sem', 'Quiz', etc.
    academic_year: Mapped[str | None] = mapped_column(String(20))

    # Status
    status: Mapped[str] = mapped_column(String(20), default="processing")  # processing, completed, failed

    # Rank column — which column to use for ranking (auto-detected or set by TPO)
    rank_column: Mapped[str | None] = mapped_column(String(200))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    uploader: Mapped["User"] = relationship()
    student_results: Mapped[list["ExamStudentResult"]] = relationship(
        back_populates="exam_upload", cascade="all, delete-orphan"
    )


class ExamStudentResult(Base):
    """
    One row per student per uploaded exam sheet.
    All dynamic columns from the sheet are stored in `row_data` JSON.
    """
    __tablename__ = "exam_student_results"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    exam_upload_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("exam_uploads.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Student identification — extracted from the sheet
    roll_number: Mapped[str | None] = mapped_column(String(50), index=True)
    student_name: Mapped[str | None] = mapped_column(String(200))

    # Link to actual student record if roll number matches
    student_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("students.id"), index=True)

    # All dynamic column data stored as JSON {column_name: value}
    row_data = mapped_column(JSONB, nullable=False)

    # Computed rank within this upload (based on rank_column)
    rank: Mapped[int | None] = mapped_column(Integer)

    # Section/department extracted from row or inherited from upload
    section: Mapped[str | None] = mapped_column(String(50), index=True)
    department: Mapped[str | None] = mapped_column(String(100), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    # Relationships
    exam_upload: Mapped["ExamUpload"] = relationship(back_populates="student_results")
    student: Mapped["Student | None"] = relationship()

    __table_args__ = (
        Index("idx_exam_result_upload_roll", "exam_upload_id", "roll_number"),
        Index("idx_exam_result_dept_section", "department", "section"),
    )


from app.models.user import User, Student  # noqa: E402, F401
