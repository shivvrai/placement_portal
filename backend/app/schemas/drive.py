"""Pydantic schemas — Placement Drives & Applications domain."""

import uuid
from datetime import date, datetime
from typing import Optional
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

    model_config = {"from_attributes": True}


class ApplicationStudentRow(BaseModel):
    """Row in TPO shortlist / student management view."""
    application_id: uuid.UUID
    student_id: uuid.UUID
    roll_number: str
    first_name: str
    last_name: str
    cgpa: Optional[float] = None
    status: str
    current_stage: Optional[str] = None
    applied_at: datetime

    model_config = {"from_attributes": True}
