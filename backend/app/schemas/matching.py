"""Pydantic schemas — Job Matching domain."""

import uuid
from typing import Optional
from pydantic import BaseModel, Field


class SkillMatchDetail(BaseModel):
    skill_name: str
    student_score: float
    required_score: float
    matched: bool


class JobMatchResponse(BaseModel):
    job_id: uuid.UUID
    title: str
    company_name: str
    location: Optional[str] = None
    salary_ctc_min: Optional[float] = None
    salary_ctc_max: Optional[float] = None
    role_category: Optional[str] = None
    match_score: float = Field(..., ge=0, le=100)
    skill_match_pct: float
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    eligible: bool
