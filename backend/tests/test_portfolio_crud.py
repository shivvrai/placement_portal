"""
Tests for Task 1: Student Portfolio CRUD (Projects, Certifications, Work Experience)
and Bulk Skill Confirmation endpoints.
"""

import uuid
from datetime import date
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, Student
from app.core.security import hash_password
from tests.conftest import auth_headers


pytestmark = pytest.mark.asyncio


# ─── Helper: Create Second Student ──────────────────────────────────────────

async def _create_second_student(db: AsyncSession, department_id: uuid.UUID) -> tuple[User, Student]:
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"student2_{user_id.hex[:6]}@ccip.edu",
        password_hash=hash_password("student123"),
        first_name="Second",
        last_name="Student",
        role="student",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    student = Student(
        id=user_id,
        roll_number=f"ROLL_{user_id.hex[:6]}",
        department_id=department_id,
        current_semester=6,
        admission_year=2024,
        cgpa=8.2,
    )
    db.add(student)
    await db.commit()
    await db.refresh(user)
    await db.refresh(student)
    return user, student


# ─── PROJECTS TESTS ─────────────────────────────────────────────────────────

async def test_get_my_projects(client: AsyncClient, seed_student):
    user, _ = seed_student
    res = await client.get("/api/v1/students/me/projects", headers=auth_headers(user))
    assert res.status_code == 200
    assert isinstance(res.json(), list)


async def test_create_and_delete_project(client: AsyncClient, seed_student):
    user, _ = seed_student
    payload = {
        "title": "Real-time Chat App",
        "description": "A scalable real-time messaging application built with WebSocket support.",
        "tech_stack": ["React", "FastAPI", "PostgreSQL", "Socket.io"],
        "github_url": "https://github.com/riya/chat-app",
        "live_url": "https://chat-demo.vercel.app",
        "start_date": "2026-01-15",
        "end_date": None,
        "is_featured": True,
    }

    # Create project
    res = await client.post(
        "/api/v1/students/me/projects",
        json=payload,
        headers=auth_headers(user),
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["tech_stack"] == payload["tech_stack"]
    assert data["github_url"] == payload["github_url"]
    assert data["live_url"] == payload["live_url"]
    assert data["is_featured"] is True
    project_id = data["id"]

    # Verify project in list
    list_res = await client.get("/api/v1/students/me/projects", headers=auth_headers(user))
    assert list_res.status_code == 200
    projects = list_res.json()
    assert any(p["id"] == project_id for p in projects)

    # Delete project
    del_res = await client.delete(f"/api/v1/students/me/projects/{project_id}", headers=auth_headers(user))
    assert del_res.status_code == 204

    # Verify deleted
    list_res_after = await client.get("/api/v1/students/me/projects", headers=auth_headers(user))
    assert not any(p["id"] == project_id for p in list_res_after.json())


async def test_project_validation(client: AsyncClient, seed_student):
    user, _ = seed_student

    # Short title (< 3 chars)
    res = await client.post(
        "/api/v1/students/me/projects",
        json={
            "title": "Ab",
            "description": "Valid description long enough.",
            "tech_stack": ["Python"],
        },
        headers=auth_headers(user),
    )
    assert res.status_code == 422

    # Short description (< 10 chars)
    res = await client.post(
        "/api/v1/students/me/projects",
        json={
            "title": "Valid Title",
            "description": "Short",
            "tech_stack": ["Python"],
        },
        headers=auth_headers(user),
    )
    assert res.status_code == 422

    # Invalid GitHub URL format
    res = await client.post(
        "/api/v1/students/me/projects",
        json={
            "title": "Valid Title",
            "description": "Valid description long enough.",
            "tech_stack": ["Python"],
            "github_url": "https://notgithub.com/someone/repo",
        },
        headers=auth_headers(user),
    )
    assert res.status_code == 422


async def test_project_ownership_and_not_found(client: AsyncClient, seed_student, seed_department, db):
    user1, _ = seed_student
    user2, _ = await _create_second_student(db, seed_department.id)

    # User 1 creates a project
    res = await client.post(
        "/api/v1/students/me/projects",
        json={
            "title": "Student 1 Project",
            "description": "Description of project by student 1.",
            "tech_stack": ["Python", "FastAPI"],
        },
        headers=auth_headers(user1),
    )
    assert res.status_code == 201
    project_id = res.json()["id"]

    # User 2 tries to delete User 1's project -> 403 Forbidden
    del_forbidden = await client.delete(
        f"/api/v1/students/me/projects/{project_id}",
        headers=auth_headers(user2),
    )
    assert del_forbidden.status_code == 403

    # Delete non-existent project -> 404
    non_existent = uuid.uuid4()
    del_404 = await client.delete(
        f"/api/v1/students/me/projects/{non_existent}",
        headers=auth_headers(user1),
    )
    assert del_404.status_code == 404

    # Cleanup
    await client.delete(f"/api/v1/students/me/projects/{project_id}", headers=auth_headers(user1))


# ─── CERTIFICATIONS TESTS ───────────────────────────────────────────────────

async def test_get_my_certifications(client: AsyncClient, seed_student):
    user, _ = seed_student
    res = await client.get("/api/v1/students/me/certifications", headers=auth_headers(user))
    assert res.status_code == 200
    assert isinstance(res.json(), list)


async def test_create_and_delete_certification(client: AsyncClient, seed_student):
    user, _ = seed_student
    payload = {
        "name": "AWS Solutions Architect – Associate",
        "issuing_organization": "Amazon Web Services",
        "issue_date": "2026-03-01",
        "expiration_date": "2028-03-01",
        "credential_id": "AWS-SAA-2026-R4891",
        "credential_url": "https://aws.amazon.com/verify",
    }

    # Create certification
    res = await client.post(
        "/api/v1/students/me/certifications",
        json=payload,
        headers=auth_headers(user),
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == payload["name"]
    assert data["issuing_organization"] == payload["issuing_organization"]
    assert data["credential_id"] == payload["credential_id"]
    assert data["credential_url"] == payload["credential_url"]
    cert_id = data["id"]

    # Verify certification in list
    list_res = await client.get("/api/v1/students/me/certifications", headers=auth_headers(user))
    assert list_res.status_code == 200
    certs = list_res.json()
    assert any(c["id"] == cert_id for c in certs)

    # Delete certification
    del_res = await client.delete(f"/api/v1/students/me/certifications/{cert_id}", headers=auth_headers(user))
    assert del_res.status_code == 204


async def test_certification_ownership_and_not_found(client: AsyncClient, seed_student, seed_department, db):
    user1, _ = seed_student
    user2, _ = await _create_second_student(db, seed_department.id)

    res = await client.post(
        "/api/v1/students/me/certifications",
        json={
            "name": "Google Cloud Engineer",
            "issuing_organization": "Google Cloud",
            "issue_date": "2026-02-01",
        },
        headers=auth_headers(user1),
    )
    assert res.status_code == 201
    cert_id = res.json()["id"]

    # User 2 tries to delete -> 403
    del_forbidden = await client.delete(
        f"/api/v1/students/me/certifications/{cert_id}",
        headers=auth_headers(user2),
    )
    assert del_forbidden.status_code == 403

    # Delete non-existent -> 404
    del_404 = await client.delete(
        f"/api/v1/students/me/certifications/{uuid.uuid4()}",
        headers=auth_headers(user1),
    )
    assert del_404.status_code == 404

    # Cleanup
    await client.delete(f"/api/v1/students/me/certifications/{cert_id}", headers=auth_headers(user1))


# ─── WORK EXPERIENCE TESTS ──────────────────────────────────────────────────

async def test_get_my_experience(client: AsyncClient, seed_student):
    user, _ = seed_student
    res = await client.get("/api/v1/students/me/experience", headers=auth_headers(user))
    assert res.status_code == 200
    assert isinstance(res.json(), list)


async def test_create_and_delete_experience(client: AsyncClient, seed_student):
    user, _ = seed_student
    payload = {
        "company_name": "Razorpay",
        "role": "Software Engineering Intern",
        "location": "Bengaluru, IN",
        "employment_type": "Internship",
        "start_date": "2026-07-01",
        "end_date": "2026-09-30",
        "is_current": False,
        "description": "Built the merchant dashboard analytics module using React and FastAPI.",
        "skills_used": ["React", "TypeScript", "REST APIs"],
    }

    # Create work experience
    res = await client.post(
        "/api/v1/students/me/experience",
        json=payload,
        headers=auth_headers(user),
    )
    assert res.status_code == 201
    data = res.json()
    assert data["company_name"] == payload["company_name"]
    assert data["role"] == payload["role"]
    assert data["location"] == payload["location"]
    assert data["employment_type"] == payload["employment_type"]
    assert data["skills_used"] == payload["skills_used"]
    exp_id = data["id"]

    # Verify experience in list
    list_res = await client.get("/api/v1/students/me/experience", headers=auth_headers(user))
    assert list_res.status_code == 200
    assert any(e["id"] == exp_id for e in list_res.json())

    # Delete experience
    del_res = await client.delete(f"/api/v1/students/me/experience/{exp_id}", headers=auth_headers(user))
    assert del_res.status_code == 204


async def test_experience_ownership_and_not_found(client: AsyncClient, seed_student, seed_department, db):
    user1, _ = seed_student
    user2, _ = await _create_second_student(db, seed_department.id)

    res = await client.post(
        "/api/v1/students/me/experience",
        json={
            "company_name": "Microsoft",
            "role": "Summer Intern",
            "start_date": "2026-05-01",
        },
        headers=auth_headers(user1),
    )
    assert res.status_code == 201
    exp_id = res.json()["id"]

    # User 2 tries to delete -> 403
    del_forbidden = await client.delete(
        f"/api/v1/students/me/experience/{exp_id}",
        headers=auth_headers(user2),
    )
    assert del_forbidden.status_code == 403

    # Delete non-existent -> 404
    del_404 = await client.delete(
        f"/api/v1/students/me/experience/{uuid.uuid4()}",
        headers=auth_headers(user1),
    )
    assert del_404.status_code == 404

    # Cleanup
    await client.delete(f"/api/v1/students/me/experience/{exp_id}", headers=auth_headers(user1))


# ─── BULK SKILL CONFIRMATION TESTS ──────────────────────────────────────────

async def test_bulk_confirm_skills(client: AsyncClient, seed_department, db):
    user, _ = await _create_second_student(db, seed_department.id)
    payload = {
        "skills": ["FastAPI", "React", "Docker", "PyTorch"],
        "source": "resume_verified",
    }

    res = await client.post(
        "/api/v1/students/me/skills/bulk",
        json=payload,
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    skills_data = res.json()
    assert isinstance(skills_data, list)
    assert len(skills_data) >= 4

    # Verify each confirmed skill has source=resume_verified and is_verified=True
    names = [s["skill"]["name"].lower() for s in skills_data]
    for skill_name in ["fastapi", "react", "docker", "pytorch"]:
        assert skill_name in names

    verified_skills = [s for s in skills_data if s["source"] == "resume_verified"]
    for s in verified_skills:
        assert s["is_verified"] is True
        assert s["confidence"] == 0.9

    # Verify skill appears in student's skills list
    get_skills = await client.get("/api/v1/students/me/skills", headers=auth_headers(user))
    assert get_skills.status_code == 200
    all_names = [s["skill"]["name"].lower() for s in get_skills.json()]
    for skill_name in ["fastapi", "react", "docker", "pytorch"]:
        assert skill_name in all_names


async def test_resume_upload_and_preview_skills(client: AsyncClient, seed_department, db):
    """Resume upload returns extracted_skills for human review preview."""
    user, _ = await _create_second_student(db, seed_department.id)
    resume_text = (
        "John Doe\nSoftware Developer\n"
        "Proficient in Python, React, FastAPI, Docker, and PostgreSQL.\n"
        "Experience in Machine Learning projects and Git version control."
    )
    files = {
        "file": ("resume.txt", resume_text.encode("utf-8"), "text/plain")
    }

    res = await client.post(
        "/api/v1/resume/upload",
        files=files,
        headers=auth_headers(user),
    )
    assert res.status_code in (200, 202)
    data = res.json()
    assert "extracted_skills" in data
    assert isinstance(data["extracted_skills"], list)
    assert len(data["extracted_skills"]) > 0

    skill_names = [s["name"].lower() for s in data["extracted_skills"]]
    assert "python" in skill_names or "react" in skill_names or "fastapi" in skill_names
    for item in data["extracted_skills"]:
        assert "name" in item
        assert "confidence" in item
        assert 0.0 <= item["confidence"] <= 1.0


async def test_resume_status_includes_extracted_skills(client: AsyncClient, seed_department, db):
    """Resume status endpoint returns parsed flag and extracted_skills."""
    user, _ = await _create_second_student(db, seed_department.id)
    res = await client.get(
        "/api/v1/resume/status",
        headers=auth_headers(user),
    )
    assert res.status_code == 200
    data = res.json()
    assert "resume_parsed" in data
    assert "extracted_skills" in data
    assert isinstance(data["extracted_skills"], list)


# ─── PUBLIC PROFILE TESTS (TASK 3) ──────────────────────────────────────────

async def test_public_profile_success(client: AsyncClient, seed_department, db):
    """Unauthenticated recruiter can view student public portfolio when consent is enabled."""
    user, student = await _create_second_student(db, seed_department.id)

    # Enable public profile visibility
    student.consent_profile_visible = True
    student.cgpa = 8.75
    await db.commit()

    # Add project, cert, exp, and confirmed skills
    await client.post(
        "/api/v1/students/me/projects",
        json={
            "title": "Public Showcase App",
            "description": "A public showcase application built for portfolio.",
            "tech_stack": ["React", "FastAPI"],
            "github_url": "https://github.com/student/showcase",
            "is_featured": True,
        },
        headers=auth_headers(user),
    )

    await client.post(
        "/api/v1/students/me/skills/bulk",
        json={
            "skills": ["Python", "FastAPI", "React"],
            "source": "resume_verified",
        },
        headers=auth_headers(user),
    )

    # Request public profile WITHOUT ANY AUTH HEADERS
    res = await client.get(f"/api/v1/students/{student.id}/public-profile")
    assert res.status_code == 200
    data = res.json()

    # Verify safe fields
    assert data["id"] == str(student.id)
    assert data["name"] == f"{user.first_name} {user.last_name}".strip()
    assert data["roll_number"] == student.roll_number
    assert data["department"] == seed_department.name
    assert data["graduation_year"] == student.admission_year + 4
    assert data["cgpa"] == 8.75
    assert "projects" in data
    assert len(data["projects"]) >= 1
    assert data["projects"][0]["title"] == "Public Showcase App"
    assert data["projects"][0]["is_featured"] is True
    assert "verified_skills" in data
    assert len(data["verified_skills"]) >= 3

    # Verify sensitive fields are NOT exposed
    assert "email" not in data
    assert "phone" not in data
    assert "password_hash" not in data
    assert "academic_records" not in data
    assert "attendance" not in data


async def test_public_profile_disabled_403(client: AsyncClient, seed_department, db):
    """If student disabled public profile visibility, public endpoint returns 403."""
    user, student = await _create_second_student(db, seed_department.id)
    student.consent_profile_visible = False
    await db.commit()

    res = await client.get(f"/api/v1/students/{student.id}/public-profile")
    assert res.status_code == 403
    assert "disabled" in res.json()["detail"].lower()


async def test_public_profile_not_found_404(client: AsyncClient):
    """Non-existent student returns 404."""
    random_id = uuid.uuid4()
    res = await client.get(f"/api/v1/students/{random_id}/public-profile")
    assert res.status_code == 404


