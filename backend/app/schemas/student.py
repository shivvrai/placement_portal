"""Pydantic schemas — Student domain."""

import uuid
from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel, HttpUrl, Field


# ─── Department ────────────────────────────────────────────────────────────────

class DepartmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str

    model_config = {"from_attributes": True}


# ─── Student ───────────────────────────────────────────────────────────────────

class StudentSummary(BaseModel):
    """Lightweight student card used in lists."""
    id: uuid.UUID
    roll_number: str
    first_name: str
    last_name: str
    email: str
    department_code: str
    department_name: str
    current_semester: int
    cgpa: Optional[float] = None
    resume_parsed: bool
    placement_status: Optional[str] = "unregistered"  # derived
    company: Optional[str] = None
    package: Optional[float] = None
    skill_score: Optional[int] = None
    backlogs: Optional[int] = 0
    year: Optional[int] = None

    model_config = {"from_attributes": True}




class StudentProfile(BaseModel):
    """Full student profile returned to the student themselves or TPO."""
    id: uuid.UUID
    roll_number: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    department: DepartmentResponse
    current_semester: int
    admission_year: int
    cgpa: Optional[float] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    bio: Optional[str] = None
    resume_url: Optional[str] = None
    resume_parsed: bool
    consent_resume_analysis: bool
    consent_profile_visible: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StudentUpdateRequest(BaseModel):
    """PATCH body for student profile."""
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None


class AddStudentSkillRequest(BaseModel):
    skill_id: Optional[uuid.UUID] = None
    skill_name: Optional[str] = None
    category: Optional[str] = "other"
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    proficiency_level: Optional[str] = "intermediate"


class ConsentUpdateRequest(BaseModel):
    consent_resume_analysis: Optional[bool] = None
    consent_profile_visible: Optional[bool] = None


# ─── Academic ──────────────────────────────────────────────────────────────────

class SubjectResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    semester_number: int
    credits: int
    subject_type: str

    model_config = {"from_attributes": True}


class AcademicRecordResponse(BaseModel):
    id: uuid.UUID
    subject: SubjectResponse
    grade: Optional[str] = None
    grade_points: Optional[float] = None
    marks: Optional[float] = None
    max_marks: Optional[float] = None
    status: str

    model_config = {"from_attributes": True}


# ─── Portfolio: Projects ────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    tech_stack: list[str] = Field(..., min_length=1, max_length=20)  # e.g. ["React", "FastAPI", "PostgreSQL"]
    github_url: Optional[str] = Field(None, pattern=r"^https://github\.com/.+")
    live_url: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_featured: bool = False


class ProjectResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    title: str
    description: Optional[str] = None
    tech_stack: list[str] = []
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_featured: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Portfolio: Certifications ──────────────────────────────────────────────────

class CertificationCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=300)
    issuing_organization: str = Field(..., min_length=2, max_length=200)
    issue_date: date
    expiration_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None  # URL to verify credential


class CertificationResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    name: str
    issuing_organization: str
    issue_date: date
    expiration_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Portfolio: Work Experience ─────────────────────────────────────────────────

class WorkExperienceCreate(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=200)
    role: str = Field(..., min_length=2, max_length=200)
    location: Optional[str] = None
    employment_type: Literal["Internship", "Full-Time", "Part-Time", "Contract"] = "Internship"
    start_date: date
    end_date: Optional[date] = None    # None means currently working
    is_current: bool = False
    description: Optional[str] = None  # Bullet points / responsibilities
    skills_used: Optional[list[str]] = None


class WorkExperienceResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    company_name: str
    role: str
    location: Optional[str] = None
    employment_type: str = "Internship"
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None
    skills_used: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Bulk Skill Confirmation ───────────────────────────────────────────────────

class BulkSkillConfirm(BaseModel):
    skills: list[str]           # List of confirmed skill names
    source: str = "resume_verified"


# ─── Public Profile (Recruiter Showcase) ───────────────────────────────────────

class PublicProjectResponse(BaseModel):
    title: str
    description: Optional[str] = None
    technologies: list[str] = []
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_featured: bool = False


class PublicCertificationResponse(BaseModel):
    name: str
    issuing_organization: str
    issue_date: date
    expiration_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None


class PublicWorkExperienceResponse(BaseModel):
    company_name: str
    role: str
    location: Optional[str] = None
    employment_type: str = "Internship"
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None
    skills_used: list[str] = []


class PublicProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    roll_number: str
    branch: str
    department: str
    graduation_year: int
    cgpa: Optional[float] = None
    verified_skills: list[str] = []
    projects: list[PublicProjectResponse] = []
    certifications: list[PublicCertificationResponse] = []
    work_experience: list[PublicWorkExperienceResponse] = []
    college_name: str = "University Placement Cell"
    last_updated: Optional[datetime] = None



