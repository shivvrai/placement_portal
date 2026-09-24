import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Float, Text, DateTime, ForeignKey, Index, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, JSONB


def utcnow():
    return datetime.now(timezone.utc)


class AssessmentQuestionBank(Base):
    __tablename__ = "assessment_question_bank"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    topic: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subtopic: Mapped[str | None] = mapped_column(String(100))
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False) # 'beginner', 'intermediate', 'advanced'
    concept: Mapped[str | None] = mapped_column(String(100))
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Store options as a JSON array of strings
    options = mapped_column(JSONB, nullable=False)
    
    question_type: Mapped[str] = mapped_column(String(50), default="mcq")
    code_problem_statement: Mapped[str | None] = mapped_column(Text)
    code_input_format: Mapped[str | None] = mapped_column(Text)
    code_output_format: Mapped[str | None] = mapped_column(Text)
    code_sample_inputs = mapped_column(JSONB, nullable=True)
    code_sample_outputs = mapped_column(JSONB, nullable=True)
    code_test_cases = mapped_column(JSONB, nullable=True)
    code_language: Mapped[str | None] = mapped_column(String(50))
    
    correct_answer: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    
    skill_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("skills.id"), index=True)
    
    # Metadata fields
    source_reference: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    quality_status: Mapped[str] = mapped_column(String(50), default="draft") # draft, reviewed, rejected
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    skill: Mapped["Skill"] = relationship(backref="assessment_questions")


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)
    
    score: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="in_progress") # in_progress, completed
    
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    
    metadata_col = mapped_column("metadata", JSONB, nullable=True)

    student: Mapped["Student"] = relationship(backref="assessment_sessions")
    session_questions: Mapped[list["AssessmentSessionQuestion"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class AssessmentSessionQuestion(Base):
    __tablename__ = "assessment_session_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("assessment_sessions.id"), nullable=False, index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("assessment_question_bank.id"), nullable=False, index=True)
    
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    selected_option: Mapped[str | None] = mapped_column(String(255))
    is_correct: Mapped[bool | None] = mapped_column(Boolean)

    session: Mapped["AssessmentSession"] = relationship(back_populates="session_questions")
    question: Mapped["AssessmentQuestionBank"] = relationship()
    
    __table_args__ = (
        Index('idx_session_question_order', 'session_id', 'order_index', unique=True),
    )
