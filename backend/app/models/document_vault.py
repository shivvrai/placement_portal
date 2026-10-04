"""
SQLAlchemy ORM models — Student Document Vault domain.
Tables: student_documents

Sprint 3 — Anjula
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Text, Boolean, DateTime, ForeignKey,
    CheckConstraint, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, JSONB


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class StudentDocument(Base):
    """Student-uploaded document in the secure vault."""
    __tablename__ = "student_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(300), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tags = mapped_column(JSONB, nullable=True, default=list)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_shared_with_tpo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    student = relationship("Student", lazy="selectin")
    verifier = relationship("User", lazy="selectin")

    __table_args__ = (
        CheckConstraint(
            "document_type IN ('offer_letter', 'id_proof', 'certificate', 'transcript', 'resume', 'recommendation', 'other')",
            name="ck_document_type",
        ),
        Index("idx_doc_student_type", "student_id", "document_type"),
    )
