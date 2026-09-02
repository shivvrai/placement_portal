"""
Pydantic schemas for authentication and user management.
These are the API contracts — frontend can build against these immediately.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ─── Auth Requests ───────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: str = Field(pattern="^(student|tpo|faculty|hod|admin)$")
    phone: str | None = None
    # Student-specific (required when role = "student")
    roll_number: str | None = None
    department_code: str | None = None
    current_semester: int | None = Field(default=None, ge=1, le=8)
    admission_year: int | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


# ─── Auth Responses ──────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    first_name: str
    last_name: str
    phone: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class StudentResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    first_name: str
    last_name: str
    roll_number: str
    department_code: str | None = None
    department_name: str | None = None
    current_semester: int
    admission_year: int
    cgpa: float | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    linkedin_url: str | None = None
    bio: str | None = None
    resume_parsed: bool = False
    consent_resume_analysis: bool = False
    consent_profile_visible: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Common ──────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    """Generic message response for simple confirmations."""
    message: str
    detail: str | None = None
