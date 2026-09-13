"""
Tests for Curriculum Intelligence API and Faculty Analytics endpoints.
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import auth_headers
from app.models.academic import Subject
from app.models.user import Department

pytestmark = pytest.mark.asyncio


async def test_get_department_overview(client: AsyncClient, seed_tpo):
    """Faculty / TPO can get department overview analytics."""
    res = await client.get("/api/v1/analytics/departments/CS", headers=auth_headers(seed_tpo))
    assert res.status_code == 200
    data = res.json()
    assert "kpis" in data
    assert "coverage_donut" in data
    assert "skill_radar" in data
    assert "subject_gap_rank" in data
    assert "batch_skill" in data
    assert "at_risk" in data

    # Check KPI fields
    kpis = data["kpis"]
    assert "avg_skill_score" in kpis
    assert "curriculum_coverage" in kpis
    assert "subjects_high_gap" in kpis
    assert "students_at_risk" in kpis


async def test_get_curriculum_subjects(client: AsyncClient, seed_tpo, db: AsyncSession, seed_department: Department):
    """Faculty / TPO can retrieve subjects with curriculum skill mappings and AI suggestions."""
    # Ensure at least one subject exists for CS department
    subject = Subject(
        id=uuid.uuid4(),
        code="CS501_TEST",
        name="Cloud Computing Systems",
        department_id=seed_department.id,
        semester_number=7,
        credits=4,
    )
    db.add(subject)
    await db.commit()

    res = await client.get("/api/v1/curriculum/subjects?dept=CS&semester=7", headers=auth_headers(seed_tpo))
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0

    found = next((s for s in data if s["code"] == "CS501_TEST"), None)
    assert found is not None
    assert found["credits"] == 4
    assert "coverage_pct" in found
    assert "demand_score" in found
    assert isinstance(found["mapped_skills"], list)
    assert isinstance(found["ai_suggestions"], list)


async def test_apply_suggested_mappings(client: AsyncClient, seed_tpo, db: AsyncSession, seed_department: Department):
    """Faculty can apply AI suggested skill mappings to a subject."""
    subject = Subject(
        id=uuid.uuid4(),
        code="CS502_TEST",
        name="Deep Learning Foundations",
        department_id=seed_department.id,
        semester_number=7,
        credits=4,
    )
    db.add(subject)
    await db.commit()

    res = await client.post(
        f"/api/v1/curriculum/subjects/{subject.id}/suggest-mappings",
        headers=auth_headers(seed_tpo),
    )
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    assert data["subject_id"] == str(subject.id)
    assert len(data.get("applied_skills", [])) > 0

    # Second call should handle cleanly (skills already mapped)
    res2 = await client.post(
        f"/api/v1/curriculum/subjects/{subject.id}/suggest-mappings",
        headers=auth_headers(seed_tpo),
    )
    assert res2.status_code == 200
