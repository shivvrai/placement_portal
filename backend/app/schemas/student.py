"""Pydantic schemas — Student domain."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl


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
    marks: Optional[float] = None
    max_marks: Optional[float] = None
    status: str

    model_config = {"from_attributes": True}
