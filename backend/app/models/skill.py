"""
SQLAlchemy ORM models — Skills domain.
Tables: skills, skill_relationships, student_skills, curriculum_skills
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Numeric, Text, DateTime, ForeignKey,
    UniqueConstraint, Index, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.db_types import UUIDType, ARRAY, JSONB, Vector


def utcnow():
    return datetime.now(timezone.utc)


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    domain: Mapped[str | None] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    aliases = mapped_column(ARRAY(String), nullable=True)
    embedding = mapped_column(Vector(384), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    student_skills: Mapped[list["StudentSkill"]] = relationship(back_populates="skill")
    curriculum_skills: Mapped[list["CurriculumSkill"]] = relationship(back_populates="skill")
    job_skills: Mapped[list["JobSkill"]] = relationship(back_populates="skill")
    resource_skills: Mapped[list["ResourceSkill"]] = relationship(back_populates="skill")
    related_from: Mapped[list["SkillRelationship"]] = relationship(
        foreign_keys="SkillRelationship.skill_id", back_populates="skill"
    )
    related_to: Mapped[list["SkillRelationship"]] = relationship(
        foreign_keys="SkillRelationship.related_skill_id", back_populates="related_skill"
    )

    __table_args__ = (
        CheckConstraint(
            "category IN ('language','framework','library','tool','platform',"
            "'concept','methodology','database','cloud','soft_skill','domain_knowledge','other')",
            name="ck_skills_category",
        ),
    )


class SkillRelationship(Base):
    __tablename__ = "skill_relationships"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    skill_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("skills.id"), nullable=False)
    related_skill_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("skills.id"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(30), nullable=False)

    skill: Mapped["Skill"] = relationship(foreign_keys=[skill_id], back_populates="related_from")
    related_skill: Mapped["Skill"] = relationship(foreign_keys=[related_skill_id], back_populates="related_to")

    __table_args__ = (
        UniqueConstraint("skill_id", "related_skill_id", "relationship_type", name="uq_skill_rel"),
        CheckConstraint("relationship_type IN ('prerequisite','related','subset_of')", name="ck_skill_rel_type"),
    )


class StudentSkill(Base):
    __tablename__ = "student_skills"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("students.id"), nullable=False, index=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("skills.id"), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, default=0.5)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    proficiency_level: Mapped[str | None] = mapped_column(String(20))
    evidence_text: Mapped[str | None] = mapped_column(Text)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    student: Mapped["Student"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship(back_populates="student_skills")

    __table_args__ = (
        UniqueConstraint("student_id", "skill_id", "source", name="uq_student_skill_source"),
        CheckConstraint(
            "source IN ('resume','academic','project','certification','internship','manual','assessment')",
            name="ck_student_skill_source",
        ),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_student_skill_confidence"),
    )


class CurriculumSkill(Base):
    __tablename__ = "curriculum_skills"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("subjects.id"), nullable=False, index=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("skills.id"), nullable=False, index=True)
    coverage_level: Mapped[str] = mapped_column(String(20), nullable=False, default="introduced")
    mapping_source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    subject: Mapped["Subject"] = relationship(back_populates="curriculum_skills")
    skill: Mapped["Skill"] = relationship(back_populates="curriculum_skills")

    __table_args__ = (
        UniqueConstraint("subject_id", "skill_id", name="uq_curriculum_skill"),
        CheckConstraint("coverage_level IN ('introduced','practiced','mastered')", name="ck_curriculum_coverage"),
        CheckConstraint("mapping_source IN ('manual','nlp_suggested','faculty_confirmed')", name="ck_curriculum_source"),
    )


from app.models.industry import JobSkill  # noqa: E402, F401
from app.models.roadmap import ResourceSkill  # noqa: E402, F401
