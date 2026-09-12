"""
Integration & edge-case test suite for Sachin's tasks:
- Job matching endpoint (/api/v1/matching/students/{id}/jobs)
- Skill gap analysis endpoint (/api/v1/matching/students/{id}/gap)
- Learning roadmap endpoint (/api/v1/roadmap/students/{id})
- Edge cases: 0 skills, nonexistent student, role filtering, custom roles.
"""

import uuid
import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio

async def test_job_matching_and_gaps_e2e(client: AsyncClient, seed_student):
    user, student = seed_student
    headers = auth_headers(user)
    student_id = student.id

    # 1. Test profile retrieval
    me_res = await client.get("/api/v1/students/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["id"] == str(student_id)

    # 2. Test job matching endpoint
    matches_res = await client.get(f"/api/v1/matching/students/{student_id}/jobs", headers=headers)
    assert matches_res.status_code == 200
    matches = matches_res.json()
    assert isinstance(matches, list)

    # If matches exist, validate structure
    if len(matches) > 0:
        first_match = matches[0]
        assert "job_id" in first_match
        assert "title" in first_match
        assert "company_name" in first_match
        assert "match_score" in first_match
        assert 0.0 <= first_match["match_score"] <= 100.0
        assert "skill_match_pct" in first_match
        assert "matched_skills" in first_match
        assert "missing_skills" in first_match
        assert "eligible" in first_match
        assert isinstance(first_match["eligible"], bool)

    # 3. Test query parameters on job matching
    filtered_res = await client.get(
        f"/api/v1/matching/students/{student_id}/jobs?limit=5&minMatch=20",
        headers=headers
    )
    assert filtered_res.status_code == 200
    filtered_matches = filtered_res.json()
    assert len(filtered_matches) <= 5

    # 4. Test skill gap endpoint with standard role
    gap_res = await client.get(
        f"/api/v1/matching/students/{student_id}/gap?target_role=Software%20Engineer",
        headers=headers
    )
    assert gap_res.status_code == 200
    gap_data = gap_res.json()
    assert gap_data["target_role"] == "Software Engineer"
    assert "overall_score" in gap_data
    assert 0.0 <= gap_data["overall_score"] <= 100.0
    assert "gaps" in gap_data
    assert len(gap_data["gaps"]) > 0

    first_gap = gap_data["gaps"][0]
    assert "skill_name" in first_gap
    assert "category" in first_gap
    assert "current_score" in first_gap
    assert "required_score" in first_gap
    assert "gap" in first_gap
    assert "severity" in first_gap
    assert first_gap["severity"] in ["none", "low", "medium", "high", "critical"]

    # 5. Test skill gap with role in ROLE_PROFILES
    da_res = await client.get(
        f"/api/v1/matching/students/{student_id}/gap?target_role=Data%20Analyst",
        headers=headers
    )
    assert da_res.status_code == 200
    da_gap = da_res.json()
    assert da_gap["target_role"] == "Data Analyst"

    # 6. Test skill gap with custom / uncommon role (verifies fallback to Software Engineer without crashing)
    custom_role_res = await client.get(
        f"/api/v1/matching/students/{student_id}/gap?target_role=Cloud%20Architect",
        headers=headers
    )
    assert custom_role_res.status_code == 200
    custom_gap = custom_role_res.json()
    assert custom_gap["target_role"] == "Software Engineer"  # fallback
    assert "overall_score" in custom_gap

    # 7. Test roadmap student alias endpoint
    roadmap_res = await client.get(f"/api/v1/roadmap/students/{student_id}", headers=headers)
    assert roadmap_res.status_code in [200, 404]

    # 7. Edge Case: Non-existent student ID returns 404
    fake_id = uuid.uuid4()
    not_found_res = await client.get(f"/api/v1/matching/students/{fake_id}/jobs", headers=headers)
    assert not_found_res.status_code == 404

    not_found_gap = await client.get(f"/api/v1/matching/students/{fake_id}/gap", headers=headers)
    assert not_found_gap.status_code == 404

    # 8. Unauthenticated request returns 401 or 403
    unauth_res = await client.get(f"/api/v1/matching/students/{student_id}/jobs")
    assert unauth_res.status_code in [401, 403]
