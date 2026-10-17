"""
Pydantic schemas — Student Identity & Portfolio domain.
Public Portfolio, Vanity Slugs, Settings, Profile Completeness, ATS Resume Score.
"""

import uuid
from datetime import date, datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# ─── Public Portfolio Showcase ──────────────────────────────────────────────────

class PublicSocialLinks(BaseModel):
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class PublicProjectItem(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    tech_stack: list[str] = []
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: Optional[str] = "completed"
    role: Optional[str] = None
    team_size: Optional[int] = 1
    highlights: list[str] = []
    is_featured: bool = False
    featured: bool = False
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    model_config = {"from_attributes": True}


class PublicCertificationItem(BaseModel):
    id: uuid.UUID
    name: str
    title: Optional[str] = None
    issuing_organization: str
    issuer: Optional[str] = None
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None
    certificate_image_url: Optional[str] = None
    skills_covered: list[str] = []
    is_verified: bool = False
    verified: bool = False

    model_config = {"from_attributes": True}


class PublicInternshipItem(BaseModel):
    id: uuid.UUID
    company_name: str
    company: Optional[str] = None
    role: str
    location: Optional[str] = None
    employment_type: str = "Internship"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None
    skills_used: list[str] = []
    technologies: list[str] = []
    is_verified: bool = False
    verified: bool = False

    model_config = {"from_attributes": True}


class PublicPortfolioResponse(BaseModel):
    id: uuid.UUID
    name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    roll_number: Optional[str] = None
    department: str
    branch: str
    graduation_year: int
    custom_slug: Optional[str] = None
    is_public: bool = True
    social_links: PublicSocialLinks = Field(default_factory=PublicSocialLinks)
    verified_skills: list[str] = []
    skills: list[str] = []
    featured_projects: list[PublicProjectItem] = []
    projects: list[PublicProjectItem] = []
    certifications: list[PublicCertificationItem] = []
    internships: list[PublicInternshipItem] = []
    work_experience: list[PublicInternshipItem] = []
    college_name: str = "University Placement Cell"
    last_updated: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Settings & Visibility ──────────────────────────────────────────────────────

class PortfolioSettingsUpdate(BaseModel):
    is_public: Optional[bool] = None
    custom_slug: Optional[str] = Field(None, min_length=2, max_length=100)


class PortfolioSettingsResponse(BaseModel):
    student_id: uuid.UUID
    is_public: bool
    custom_slug: Optional[str] = None
    public_url: Optional[str] = None


# ─── Profile Completeness ───────────────────────────────────────────────────────

class CompletenessBreakdownItem(BaseModel):
    points_earned: int
    max_points: int
    completed: bool
    description: str


class ProfileCompletenessResponse(BaseModel):
    completeness_score: int = Field(..., ge=0, le=100)
    score: int = Field(..., ge=0, le=100)  # alias for score
    tier: str = "Beginner"  # "Beginner", "Intermediate", "All-Star", "Recruiter Ready"
    breakdown: dict[str, CompletenessBreakdownItem]
    actionable_steps: list[str]
    missing_elements: list[str] = []


# ─── ATS Resume Scorer ──────────────────────────────────────────────────────────

class AtsScoreRequest(BaseModel):
    resume_text: Optional[str] = None
    job_description: Optional[str] = None
    drive_id: Optional[uuid.UUID] = None


class AtsScoreResponse(BaseModel):
    ats_score: float = Field(..., ge=0.0, le=100.0)
    grade: str  # "Needs Improvement", "Competitive", "Strong", "Exceptional"
    breakdown: dict[str, float]
    matched_skills: list[str] = []
    missing_target_skills: list[str] = []
    formatting_flags: list[str] = []
    actionable_recommendations: list[str] = []
