"""Pydantic schemas — Job Matching domain."""

import uuid
from typing import Optional, Literal
from pydantic import BaseModel, Field


class SkillMatchDetail(BaseModel):
    skill_name: str
    student_score: float
    required_score: float
    matched: bool


class SemanticSkillDetail(BaseModel):
    required_skill: str       # Skill required by job
    student_skill: str        # Closest skill student has
    similarity: float         # 0.0 to 1.0 cosine similarity
    match_type: Literal["direct", "adjacent", "missing"]


class MatchBreakdown(BaseModel):
    academic_score: float            # 0-100: CGPA eligibility + dept match
    skills_score: float              # 0-100: weighted avg of semantic skill matches
    experience_bonus: float          # 0-20: bonus for relevant projects/internships
    total_score: float               # Weighted sum: 0.4*academic + 0.45*skills + 0.15*experience (normalized to 100)
    skill_details: list[SemanticSkillDetail] = []  # Per-skill breakdown
    academic_reason: str             # e.g. "CGPA 8.4 meets threshold 7.5. Branch CS is eligible."
    top_missing_skills: list[str] = []    # Top 3 skills student lacks
    recommendation: str             # e.g. "Adding 1 Docker project would boost this match by +14%"
    relevant_projects: list[str] = []


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
    breakdown: Optional[MatchBreakdown] = None

