"""
Pydantic schemas — Company Reviews, Application Timeline, Document Vault.

Sprint 3 — Anjula
"""

import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ─── Company Reviews & Insights ───────────────────────────────────

class CompanyReviewCreate(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=200)
    company_id: Optional[uuid.UUID] = None
    role: str = Field(..., min_length=2, max_length=200)
    review_type: str
    overall_rating: int = Field(..., ge=1, le=5)
    work_culture_rating: Optional[int] = Field(None, ge=1, le=5)
    growth_rating: Optional[int] = Field(None, ge=1, le=5)
    compensation_rating: Optional[int] = Field(None, ge=1, le=5)
    interview_rating: Optional[int] = Field(None, ge=1, le=5)
    pros: str = Field(..., min_length=10)
    cons: str = Field(..., min_length=10)
    advice: Optional[str] = None
    interview_process: Optional[str] = None
    salary_range: Optional[str] = None
    is_anonymous: bool = False


class CompanyReviewResponse(BaseModel):
    id: uuid.UUID
    student_name: Optional[str] = None
    company_name: str
    role: str
    review_type: str
    overall_rating: int
    work_culture_rating: Optional[int] = None
    growth_rating: Optional[int] = None
    compensation_rating: Optional[int] = None
    interview_rating: Optional[int] = None
    pros: str
    cons: str
    advice: Optional[str] = None
    interview_process: Optional[str] = None
    salary_range: Optional[str] = None
    is_anonymous: bool = False
    is_verified: bool = False
    upvotes: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompanyInsightResponse(BaseModel):
    id: uuid.UUID
    company_name: str
    avg_rating: float = 0.0
    total_reviews: int = 0
    total_hires_from_college: int = 0
    avg_package_lpa: Optional[float] = None
    max_package_lpa: Optional[float] = None
    min_package_lpa: Optional[float] = None
    hiring_frequency: Optional[str] = None
    common_roles: list[str] = []
    required_skills: list[str] = []
    selection_ratio: Optional[float] = None
    last_visited_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Application Timeline ────────────────────────────────────────

class TimelineEventResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    event_type: str
    from_status: Optional[str] = None
    to_status: str
    description: Optional[str] = None
    actor_name: Optional[str] = None
    metadata_payload: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApplicationTrackerResponse(BaseModel):
    application_id: uuid.UUID
    drive_title: str
    company_name: str
    role: str
    current_status: str
    applied_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    timeline: list[TimelineEventResponse] = []
    next_steps: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Document Vault ───────────────────────────────────────────────

class DocumentUpload(BaseModel):
    document_type: str
    title: str = Field(..., min_length=3, max_length=300)
    description: Optional[str] = None
    file_url: str = Field(..., min_length=5)
    file_name: str = Field(..., min_length=1, max_length=300)
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    tags: list[str] = []
    expiry_date: Optional[datetime] = None
    is_shared_with_tpo: bool = False


class DocumentResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    document_type: str
    title: str
    description: Optional[str] = None
    file_url: str
    file_name: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    is_verified: bool = False
    verified_at: Optional[datetime] = None
    tags: list[str] = []
    expiry_date: Optional[datetime] = None
    is_shared_with_tpo: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    is_shared_with_tpo: Optional[bool] = None
