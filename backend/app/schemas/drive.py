"""Pydantic schemas — Placement Drives & Applications domain."""

import uuid
from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ─── Drive ─────────────────────────────────────────────────────────────────────

class CompanyBrief(BaseModel):
    id: uuid.UUID
    name: str
    industry: Optional[str] = None
    location: Optional[str] = None

    model_config = {"from_attributes": True}


class DriveResponse(BaseModel):
    id: uuid.UUID
    company: CompanyBrief
    title: str
    description: Optional[str] = None
    drive_date: Optional[date] = None
    registration_deadline: Optional[datetime] = None
    min_cgpa: Optional[float] = None
    eligible_departments: Optional[list[str]] = None
    max_backlogs: Optional[int] = None
    roles_offered: Optional[list[str]] = None
    salary_ctc: Optional[float] = None
    status: str
    academic_year: Optional[str] = None
    # Derived at query time
    registered_count: int = 0
    shortlisted_count: int = 0
    selected_count: int = 0
    has_applied: bool = False
    match_score: Optional[float] = None

    model_config = {"from_attributes": True}


class DriveCreateRequest(BaseModel):
    company_name: str = Field(..., min_length=1)
    company_industry: Optional[str] = None
    company_location: Optional[str] = None
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    drive_date: Optional[date] = None
    registration_deadline: Optional[datetime] = None
    min_cgpa: Optional[float] = Field(None, ge=0, le=10)
    eligible_departments: Optional[list[str]] = None
    max_backlogs: Optional[int] = Field(None, ge=0)
    roles_offered: Optional[list[str]] = None
    salary_ctc: Optional[float] = Field(None, ge=0)
    academic_year: Optional[str] = None


class DriveUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    drive_date: Optional[date] = None
    registration_deadline: Optional[datetime] = None
    min_cgpa: Optional[float] = None
    eligible_departments: Optional[list[str]] = None
    max_backlogs: Optional[int] = None
    roles_offered: Optional[list[str]] = None
    salary_ctc: Optional[float] = None
    status: Optional[str] = None


# ─── Application ───────────────────────────────────────────────────────────────

class InterviewStageResponse(BaseModel):
    id: uuid.UUID
    stage_name: str
    stage_order: int
    status: str
    feedback: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    drive_id: uuid.UUID
    drive_title: Optional[str] = None
    company_name: Optional[str] = None
    salary_ctc: Optional[float] = None
    status: str
    current_stage: Optional[str] = None
    applied_at: datetime
    updated_at: datetime
    stages: list[InterviewStageResponse] = []
    # Offer details
    offer_ctc_lpa: Optional[float] = None
    offer_fixed_lpa: Optional[float] = None
    offer_variable_lpa: Optional[float] = None
    offer_designation: Optional[str] = None
    offer_joining_date: Optional[date] = None
    offer_reference_number: Optional[str] = None
    offer_recorded_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ApplicationStudentRow(BaseModel):
    """Row in TPO shortlist / student management view."""
    application_id: uuid.UUID
    student_id: uuid.UUID
    roll_number: str
    first_name: str
    last_name: str
    cgpa: Optional[float] = None
    department: Optional[str] = None
    status: str
    current_stage: Optional[str] = None
    feedback: Optional[str] = None
    applied_at: datetime
    offer_ctc_lpa: Optional[float] = None
    offer_fixed_lpa: Optional[float] = None
    offer_variable_lpa: Optional[float] = None
    offer_designation: Optional[str] = None
    offer_joining_date: Optional[date] = None
    offer_reference_number: Optional[str] = None
    offer_recorded_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ApplicationStageUpdate(BaseModel):
    status: Optional[Literal["applied", "shortlisted", "in_progress", "selected", "rejected", "withdrawn"]] = None
    current_stage: Optional[str] = None   # "OA", "Technical Interview 1", "Technical Interview 2", "HR", "Final"
    stage_status: Optional[Literal["scheduled", "passed", "failed"]] = None
    feedback: Optional[str] = None        # Internal TPO notes (not shown to student)
    scheduled_at: Optional[datetime] = None  # Interview scheduled datetime
    meeting_link: Optional[str] = None    # Virtual meeting URL
    venue: Optional[str] = None           # Physical venue if in-person


class OfferCreate(BaseModel):
    offer_ctc_lpa: float = Field(..., gt=0, le=200, description="Total CTC in Lakhs Per Annum")
    offer_fixed_lpa: float = Field(..., gt=0)
    offer_variable_lpa: float = Field(default=0.0, ge=0)
    offer_designation: str = Field(..., min_length=3, max_length=200)
    offer_joining_date: Optional[date] = None
    offer_reference_number: Optional[str] = None


# ─── Announcements ─────────────────────────────────────────────────────────────

class AnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    message: str = Field(..., min_length=1)
    urgency: Literal["normal", "important", "urgent"] = "normal"


class AnnouncementResponse(BaseModel):
    id: uuid.UUID
    drive_id: uuid.UUID
    author_id: uuid.UUID
    author_name: Optional[str] = None
    title: str
    message: str
    urgency: str
    created_at: datetime

    model_config = {"from_attributes": True}
