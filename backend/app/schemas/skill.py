"""Pydantic schemas — Skill domain."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SkillResponse(BaseModel):
    id: uuid.UUID
    name: str
    normalized_name: str
    category: str
    domain: Optional[str] = None
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class StudentSkillResponse(BaseModel):
    id: uuid.UUID
    skill: SkillResponse
    confidence: float
    source: str
    proficiency_level: Optional[str] = None
    last_updated: datetime

    model_config = {"from_attributes": True}


class SkillGapItem(BaseModel):
    """A single skill gap entry for one skill."""
    skill_name: str
    category: str
    current_score: float = Field(..., ge=0, le=100)
    required_score: float = Field(..., ge=0, le=100)
    gap: float
    severity: str  # low | medium | high | critical


class SkillGapResponse(BaseModel):
    student_id: uuid.UUID
    target_role: str
    overall_score: float
    gaps: list[SkillGapItem]


class CurriculumSkillResponse(BaseModel):
    id: uuid.UUID
    skill: SkillResponse
    coverage_level: str
    mapping_source: str

    model_config = {"from_attributes": True}


class SubjectWithSkillsResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    semester_number: int
    credits: int
    coverage_pct: float = 0.0
    demand_score: float = 0.0
    mapped_skills: list[CurriculumSkillResponse] = []
    ai_suggestions: list[str] = []

    model_config = {"from_attributes": True}


class AddSkillRequest(BaseModel):
    skill_id: Optional[uuid.UUID] = None
    skill_name: Optional[str] = None
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    category: Optional[str] = "other"
    proficiency_level: Optional[str] = "intermediate"


class ApplySuggestionRequest(BaseModel):
    skill_name: Optional[str] = None

