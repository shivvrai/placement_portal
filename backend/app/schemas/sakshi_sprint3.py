"""
Pydantic schemas — Alumni Network & Mentorship + Placement Prep Resources + Feedback Surveys.

Sprint 3 — Sakshi Kumari
"""

import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ─── Alumni & Mentorship ──────────────────────────────────────────

class AlumniProfileCreate(BaseModel):
    graduation_year: int = Field(..., ge=2000, le=2040)
    department_code: str = Field(..., min_length=2, max_length=20)
    current_company: str = Field(..., min_length=2, max_length=200)
    current_designation: str = Field(..., min_length=2, max_length=200)
    linkedin_url: Optional[str] = None
    expertise_areas: list[str] = []
    bio: Optional[str] = None
    max_mentees: int = Field(default=3, ge=1, le=10)


class AlumniProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_name: Optional[str] = None
    graduation_year: int
    department_code: str
    current_company: str
    current_designation: str
    linkedin_url: Optional[str] = None
    expertise_areas: list[str] = []
    bio: Optional[str] = None
    is_available_for_mentorship: bool = True
    max_mentees: int = 3
    rating: Optional[float] = 0.0
    total_sessions: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MentorshipRequestCreate(BaseModel):
    alumni_id: uuid.UUID
    message: Optional[str] = None
    goals: list[str] = []


class MentorshipConnectionResponse(BaseModel):
    id: uuid.UUID
    alumni_id: uuid.UUID
    student_id: uuid.UUID
    alumni_name: Optional[str] = None
    student_name: Optional[str] = None
    alumni_company: Optional[str] = None
    status: str
    message: Optional[str] = None
    goals: list[str] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MentorshipSessionCreate(BaseModel):
    connection_id: uuid.UUID
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=15, le=120)
    topic: str = Field(..., min_length=3, max_length=300)
    meeting_link: Optional[str] = None


class MentorshipSessionResponse(BaseModel):
    id: uuid.UUID
    connection_id: uuid.UUID
    scheduled_at: datetime
    duration_minutes: int
    topic: str
    notes: Optional[str] = None
    meeting_link: Optional[str] = None
    status: str
    student_rating: Optional[int] = None
    student_feedback: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionFeedback(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


# ─── Placement Prep Resources ─────────────────────────────────────

class PrepResourceCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    description: str = Field(..., min_length=10)
    category: str
    resource_type: str
    difficulty: str
    url: Optional[str] = None
    content: Optional[str] = None
    tags: list[str] = []
    target_companies: list[str] = []
    estimated_minutes: int = Field(default=30, ge=5, le=480)


class PrepResourceResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    category: str
    resource_type: str
    difficulty: str
    url: Optional[str] = None
    content: Optional[str] = None
    tags: list[str] = []
    target_companies: list[str] = []
    estimated_minutes: int = 30
    author_name: Optional[str] = None
    is_premium: bool = False
    upvotes: int = 0
    view_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PrepCollectionCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    description: Optional[str] = None
    resource_ids: list[uuid.UUID] = []
    target_role: Optional[str] = None


class PrepCollectionResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    resource_ids: list = []
    target_role: Optional[str] = None
    is_official: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PrepProgressUpdate(BaseModel):
    status: str = "in_progress"
    progress_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    notes: Optional[str] = None


class PrepProgressResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    resource_id: uuid.UUID
    resource_title: Optional[str] = None
    status: str
    progress_pct: float = 0.0
    time_spent_minutes: int = 0
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Feedback Surveys ─────────────────────────────────────────────

class SurveyQuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=5)
    question_type: str
    options: list[str] = []
    is_required: bool = True
    order_index: int = 0


class SurveyCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    description: Optional[str] = None
    survey_type: str
    target_audience: str = "all_students"
    drive_id: Optional[uuid.UUID] = None
    is_anonymous: bool = False
    questions: list[SurveyQuestionCreate] = []


class SurveyQuestionResponse(BaseModel):
    id: uuid.UUID
    question_text: str
    question_type: str
    options: list = []
    is_required: bool = True
    order_index: int = 0

    class Config:
        from_attributes = True


class SurveyResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    survey_type: str
    target_audience: str
    is_anonymous: bool = False
    is_active: bool = True
    questions: list[SurveyQuestionResponse] = []
    response_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SurveySubmission(BaseModel):
    answers: dict
    overall_rating: Optional[int] = Field(None, ge=1, le=5)
    additional_comments: Optional[str] = None


class SurveyResponseDetail(BaseModel):
    id: uuid.UUID
    survey_id: uuid.UUID
    student_name: Optional[str] = None
    answers: dict
    overall_rating: Optional[int] = None
    additional_comments: Optional[str] = None
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SurveyAnalytics(BaseModel):
    survey_id: uuid.UUID
    title: str
    total_responses: int = 0
    avg_rating: Optional[float] = None
    question_stats: list[dict] = []
    sentiment_summary: Optional[str] = None
