"""
Auth endpoint tests.
"""

import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.conftest import auth_headers


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

async def test_health_check(client: AsyncClient):
    """Health endpoint returns 200 with correct structure."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert data["service"] == "ccip-backend"


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

async def test_register_student_success(client: AsyncClient, seed_department):
    """Students can register with valid data — returns user profile."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new.student@university.ac.in",
            "password": "Secure123!",
            "first_name": "New",
            "last_name": "Student",
            "role": "student",
            "roll_number": "CS2023099",
            "department_code": "CS",
            "current_semester": 2,
            "admission_year": 2023,
        },
    )
    assert response.status_code in (200, 201)
    data = response.json()
    # Register returns user profile, not a token
    assert "email" in data or "access_token" in data


async def test_register_duplicate_email(client: AsyncClient, seed_student):
    """Registering with a duplicate email is rejected."""
    user, _ = seed_student
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": user.email,
            "password": "Another123!",
            "first_name": "Dup",
            "last_name": "User",
            "role": "student",
            "roll_number": "CS2099999",
            "department_code": "CS",
            "current_semester": 1,
            "admission_year": 2024,
        },
    )
    assert response.status_code in (400, 409, 422)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

async def test_login_success(client: AsyncClient, seed_student):
    """Valid credentials return access + refresh tokens."""
    user, _ = seed_student
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "Student123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data.get("token_type", "").lower() == "bearer"


async def test_login_wrong_password(client: AsyncClient, seed_student):
    """Wrong password returns 401."""
    user, _ = seed_student
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "WrongPassword!"},
    )
    assert response.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient):
    """Non-existent email returns 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@university.ac.in", "password": "anything"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# /auth/me
# ---------------------------------------------------------------------------

async def test_me_authenticated(client: AsyncClient, seed_student):
    """Authenticated user can fetch their own profile."""
    user, _ = seed_student
    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers(user),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user.email
    assert data["role"] == "student"


async def test_me_unauthenticated(client: AsyncClient):
    """Unauthenticated request to /me is rejected."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


async def test_me_invalid_token(client: AsyncClient):
    """Malformed token is rejected."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer this.is.not.a.jwt"},
    )
    assert response.status_code in (401, 403)
