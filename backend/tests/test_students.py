"""
Student API endpoint tests.

Tests student profile retrieval, update, consent, and skills —
verifying both happy paths and role-based access control.
"""

import pytest
from httpx import AsyncClient

from app.models.user import User, Student
from tests.conftest import auth_headers


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# GET /students/me
# ---------------------------------------------------------------------------

async def test_get_my_profile_as_student(client: AsyncClient, seed_student):
    """A student can read their own profile."""
    user, student = seed_student
    response = await client.get(
        "/api/v1/students/me",
        headers=auth_headers(user),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user.email
    assert data["roll_number"] == student.roll_number
    assert data["current_semester"] == student.current_semester


async def test_get_my_profile_unauthenticated(client: AsyncClient):
    """Unauthenticated request returns 401/403."""
    response = await client.get("/api/v1/students/me")
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# PATCH /students/me
# ---------------------------------------------------------------------------

async def test_update_my_profile(client: AsyncClient, seed_student):
    """Student can update bio and social links."""
    user, _ = seed_student
    payload = {
        "bio": "Final year CS student passionate about ML.",
        "github_url": "https://github.com/aryan",
        "linkedin_url": "https://linkedin.com/in/aryan",
    }
    response = await client.patch(
        "/api/v1/students/me",
        json=payload,
        headers=auth_headers(user),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["bio"] == payload["bio"]
    assert data["github_url"] == payload["github_url"]


# ---------------------------------------------------------------------------
# PATCH /students/me/consent
# ---------------------------------------------------------------------------

async def test_update_consent(client: AsyncClient, seed_student):
    """Student can update data consent settings."""
    user, _ = seed_student
    response = await client.patch(
        "/api/v1/students/me/consent",
        json={"consent_resume_analysis": True, "consent_profile_visible": True},
        headers=auth_headers(user),
    )
    assert response.status_code == 200
    assert "message" in response.json()


# ---------------------------------------------------------------------------
# GET /students/me/skills
# ---------------------------------------------------------------------------

async def test_get_my_skills(client: AsyncClient, seed_student, seed_student_skills):
    """Student can retrieve their own skill list."""
    user, _ = seed_student
    response = await client.get(
        "/api/v1/students/me/skills",
        headers=auth_headers(user),
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(seed_student_skills)
    # Skills should be sorted by confidence desc
    confidences = [s["confidence"] for s in data]
    assert confidences == sorted(confidences, reverse=True)


async def test_get_my_skills_empty(client: AsyncClient, seed_student):
    """Student with no skills returns empty list (not an error)."""
    user, _ = seed_student
    response = await client.get(
        "/api/v1/students/me/skills",
        headers=auth_headers(user),
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# GET /students  (TPO-only)
# ---------------------------------------------------------------------------

async def test_list_students_as_tpo(client: AsyncClient, seed_tpo, seed_student):
    """TPO can list all students."""
    response = await client.get(
        "/api/v1/students",
        headers=auth_headers(seed_tpo),
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data


async def test_list_students_as_student_forbidden(client: AsyncClient, seed_student):
    """Students cannot access the student list endpoint."""
    user, _ = seed_student
    response = await client.get(
        "/api/v1/students",
        headers=auth_headers(user),
    )
    assert response.status_code == 403


async def test_list_students_filter_by_department(client: AsyncClient, seed_tpo, seed_student):
    """TPO can filter students by department code."""
    response = await client.get(
        "/api/v1/students?department_code=CS",
        headers=auth_headers(seed_tpo),
    )
    assert response.status_code == 200
    data = response.json()
    for student in data["data"]:
        assert student["department_code"] == "CS"


async def test_list_students_pagination(client: AsyncClient, seed_tpo):
    """Pagination parameters are respected."""
    response = await client.get(
        "/api/v1/students?page=1&per_page=5",
        headers=auth_headers(seed_tpo),
    )
    assert response.status_code == 200
    meta = response.json()["meta"]
    assert meta["per_page"] == 5
    assert meta["page"] == 1


# ---------------------------------------------------------------------------
# GET /students/{id}  (TPO-only)
# ---------------------------------------------------------------------------

async def test_get_student_by_id_as_tpo(client: AsyncClient, seed_tpo, seed_student):
    """TPO can fetch any student by UUID."""
    _, student = seed_student
    response = await client.get(
        f"/api/v1/students/{student.id}",
        headers=auth_headers(seed_tpo),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(student.id)


async def test_get_student_by_id_not_found(client: AsyncClient, seed_tpo):
    """Non-existent student ID returns 404."""
    import uuid
    fake_id = uuid.uuid4()
    response = await client.get(
        f"/api/v1/students/{fake_id}",
        headers=auth_headers(seed_tpo),
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Self Access & Skill Management
# ---------------------------------------------------------------------------

async def test_get_student_by_id_as_self(client: AsyncClient, seed_student):
    """Student can fetch their own profile using /{id}."""
    user, student = seed_student
    response = await client.get(
        f"/api/v1/students/{student.id}",
        headers=auth_headers(user),
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(student.id)


async def test_update_phone_persists_to_user(client: AsyncClient, seed_student):
    """Updating phone in profile updates the User.phone field."""
    user, _ = seed_student
    new_phone = "+91 91234 56789"
    response = await client.patch(
        "/api/v1/students/me",
        json={"phone": new_phone},
        headers=auth_headers(user),
    )
    assert response.status_code == 200
    assert response.json()["phone"] == new_phone

    # Verify subsequent GET returns the new phone
    get_res = await client.get(
        "/api/v1/students/me",
        headers=auth_headers(user),
    )
    assert get_res.status_code == 200
    assert get_res.json()["phone"] == new_phone


async def test_add_and_delete_student_skill(client: AsyncClient, seed_student):
    """Student can add a manual skill and then remove it."""
    user, _ = seed_student

    # Add skill
    payload = {
        "skill_name": "Kubernetes",
        "category": "cloud",
        "confidence": 0.8,
        "proficiency_level": "advanced",
    }
    add_res = await client.post(
        "/api/v1/students/me/skills",
        json=payload,
        headers=auth_headers(user),
    )
    assert add_res.status_code == 200
    skill_data = add_res.json()
    assert skill_data["skill"]["name"] == "Kubernetes"
    assert skill_data["source"] == "manual"
    student_skill_id = skill_data["id"]

    # Verify skill appears in get_my_skills
    skills_res = await client.get(
        "/api/v1/students/me/skills",
        headers=auth_headers(user),
    )
    assert skills_res.status_code == 200
    names = [s["skill"]["name"] for s in skills_res.json()]
    assert "Kubernetes" in names

    # Delete skill
    del_res = await client.delete(
        f"/api/v1/students/me/skills/{student_skill_id}",
        headers=auth_headers(user),
    )
    assert del_res.status_code == 200
    assert "message" in del_res.json()

    # Verify skill is removed
    skills_after = await client.get(
        "/api/v1/students/me/skills",
        headers=auth_headers(user),
    )
    assert skills_after.status_code == 200
    names_after = [s["skill"]["name"] for s in skills_after.json()]
    assert "Kubernetes" not in names_after


async def test_delete_student_skill_by_name(client: AsyncClient, seed_student):
    """Student can delete a skill using its name in the endpoint."""
    user, _ = seed_student

    # Add skill
    await client.post(
        "/api/v1/students/me/skills",
        json={"skill_name": "Terraform", "category": "cloud", "confidence": 0.75},
        headers=auth_headers(user),
    )

    # Delete by skill name
    del_res = await client.delete(
        "/api/v1/students/me/skills/Terraform",
        headers=auth_headers(user),
    )
    assert del_res.status_code == 200

    # Verify skill is removed
    skills_after = await client.get(
        "/api/v1/students/me/skills",
        headers=auth_headers(user),
    )
    names_after = [s["skill"]["name"] for s in skills_after.json()]
    assert "Terraform" not in names_after


async def test_delete_student_skill_by_skill_id_with_duplicates(client: AsyncClient, seed_student, db):
    """Deleting by Skill.id cleans up duplicate entries for the student without error."""
    import uuid
    from datetime import datetime, timezone
    from app.models.skill import Skill, StudentSkill

    user, student = seed_student

    # Create a skill in taxonomy
    skill = Skill(name="GraphQL", normalized_name="graphql", category="framework", created_at=datetime.now(timezone.utc))
    db.add(skill)
    await db.flush()

    # Create two StudentSkill rows (e.g. from resume and manual)
    db.add(StudentSkill(student_id=student.id, skill_id=skill.id, confidence=0.7, source="resume"))
    db.add(StudentSkill(student_id=student.id, skill_id=skill.id, confidence=0.8, source="manual"))
    await db.commit()

    # Delete by taxonomy skill_id
    del_res = await client.delete(
        f"/api/v1/students/me/skills/{skill.id}",
        headers=auth_headers(user),
    )
    assert del_res.status_code == 200

    # Verify both rows are removed
    skills_after = await client.get(
        "/api/v1/students/me/skills",
        headers=auth_headers(user),
    )
    names_after = [s["skill"]["name"] for s in skills_after.json()]
    assert "GraphQL" not in names_after


