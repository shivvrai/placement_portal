"""
Comprehensive test suite for Sprint 2 features:
1. Explainable Match Diagnostics & Breakdown
2. TPO Talent Pool Cohort Builder, Recruiter Search, CSV Export, Batch Drive Invites
3. Predictive Skill Demand Trend Engine
"""

import uuid
import pytest
from httpx import AsyncClient
from app.models.user import User
from app.models.industry import Company
from app.models.placement import PlacementDrive
from app.models.cohort import StudentCohort, Notification
from app.ml.matcher import compute_breakdown
from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Task 1: Explainable Match Breakdown Unit Tests
# ---------------------------------------------------------------------------

class TestExplainableMatcher:
    def test_compute_breakdown_full_fit(self):
        student_skills = {"python": 0.9, "react": 0.85, "flask": 0.8}
        job_skills = {
            "Python": "required",
            "React": "required",
            "FastAPI": "preferred",  # adjacent to flask
            "Kubernetes": "nice_to_have",  # missing
        }
        student_projects = [
            {"title": "Web Chat App", "technologies": ["React", "Flask", "Python"]}
        ]

        breakdown = compute_breakdown(
            student_skills=student_skills,
            job_skills=job_skills,
            student_cgpa=8.5,
            job_min_cgpa=7.5,
            student_dept="CS",
            eligible_depts=["CS", "IT"],
            student_projects=student_projects,
        )

        assert breakdown.academic_score >= 90.0
        assert "meets threshold" in breakdown.academic_reason.lower()
        assert breakdown.skills_score > 60.0
        assert breakdown.experience_bonus == 5.0
        assert 0.0 <= breakdown.total_score <= 100.0

        # Check per-skill classification
        details_by_skill = {d.required_skill: d for d in breakdown.skill_details}
        assert details_by_skill["Python"].match_type == "direct"
        assert details_by_skill["React"].match_type == "direct"
        assert details_by_skill["FastAPI"].match_type == "adjacent"
        assert details_by_skill["Kubernetes"].match_type == "missing"

        # Check recommendation
        assert len(breakdown.top_missing_skills) >= 1
        assert "Kubernetes" in breakdown.top_missing_skills
        assert "boost this match" in breakdown.recommendation.lower()

    def test_compute_breakdown_ineligible_dept(self):
        breakdown = compute_breakdown(
            student_skills={"python": 0.8},
            job_skills={"Python": "required"},
            student_cgpa=9.0,
            job_min_cgpa=7.0,
            student_dept="Civil",
            eligible_depts=["CS", "IT"],
        )
        assert breakdown.academic_score == 0.0
        assert "outside eligible departments" in breakdown.academic_reason.lower()


# ---------------------------------------------------------------------------
# Task 1: Job Match Breakdown API Integration Test
# ---------------------------------------------------------------------------

async def test_job_matches_contain_breakdown(client: AsyncClient, seed_student):
    user, student = seed_student
    headers = auth_headers(user)
    student_id = student.id

    res = await client.get(f"/api/v1/matching/students/{student_id}/jobs", headers=headers)
    assert res.status_code == 200
    matches = res.json()
    assert isinstance(matches, list)

    if len(matches) > 0:
        first = matches[0]
        assert "breakdown" in first
        b = first["breakdown"]
        if b is not None:
            assert "academic_score" in b
            assert "skills_score" in b
            assert "experience_bonus" in b
            assert "total_score" in b
            assert "skill_details" in b
            assert "academic_reason" in b
            assert "recommendation" in b
            assert isinstance(b["skill_details"], list)


# ---------------------------------------------------------------------------
# Task 2: TPO Cohort Builder API Integration Tests
# ---------------------------------------------------------------------------

async def test_tpo_cohort_query_and_crud(client: AsyncClient, seed_student, db):
    _, student = seed_student
    tpo_user = User(
        id=uuid.uuid4(),
        email=f"tpo.test.{uuid.uuid4().hex[:6]}@university.ac.in",
        password_hash="test_secret_hash",
        role="tpo",
        first_name="TPO",
        last_name="Officer",
        is_active=True,
    )
    db.add(tpo_user)
    await db.commit()
    await db.refresh(tpo_user)
    headers = auth_headers(tpo_user)

    # 1. Query students with multi-condition filters
    query_payload = {
        "min_cgpa": 6.0,
        "departments": ["CS", "IT"],
        "placement_status": "any",
    }
    query_res = await client.post("/api/v1/tpo/cohorts/query", json=query_payload, headers=headers)
    assert query_res.status_code == 200
    data = query_res.json()
    assert "students" in data
    assert "total" in data
    assert "query_id" in data
    students_list = data["students"]
    assert len(students_list) >= 1

    candidate_ids = [s["id"] for s in students_list]

    # 2. Save cohort
    save_payload = {
        "name": "Sprint 2 Test Cohort",
        "description": "High potential test cohort for recruiter distribution",
        "criteria": query_payload,
        "student_ids": candidate_ids,
    }
    save_res = await client.post("/api/v1/tpo/cohorts", json=save_payload, headers=headers)
    assert save_res.status_code == 200
    cohort_data = save_res.json()
    cohort_id = cohort_data["id"]
    assert cohort_data["name"] == "Sprint 2 Test Cohort"
    assert cohort_data["student_count"] == len(candidate_ids)

    # 3. List cohorts
    list_res = await client.get("/api/v1/tpo/cohorts", headers=headers)
    assert list_res.status_code == 200
    cohorts_list = list_res.json()
    assert any(c["id"] == cohort_id for c in cohorts_list)

    # 4. Export CSV
    export_res = await client.get(f"/api/v1/tpo/cohorts/{cohort_id}/export", headers=headers)
    assert export_res.status_code == 200
    assert "text/csv" in export_res.headers.get("content-type", "")
    csv_text = export_res.text
    assert "Roll Number,Name,Email,Branch,CGPA,Skills,Placement Status,Phone" in csv_text

    # 5. Batch invite to drive
    # Create or fetch a test drive
    company = Company(
        id=uuid.uuid4(),
        name=f"Amazon-{uuid.uuid4().hex[:4]}",
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)

    drive = PlacementDrive(
        id=uuid.uuid4(),
        company_id=company.id,
        title="Amazon SDE-1 Campus Hiring",
        status="upcoming",
    )
    db.add(drive)
    await db.commit()
    await db.refresh(drive)

    invite_res = await client.post(
        f"/api/v1/tpo/cohorts/{cohort_id}/invite-to-drive?drive_id={drive.id}",
        headers=headers,
    )
    assert invite_res.status_code == 200
    invite_data = invite_res.json()
    assert invite_data["success"] is True
    assert invite_data["invited_count"] == len(candidate_ids)

    # 6. Archive cohort
    del_res = await client.delete(f"/api/v1/tpo/cohorts/{cohort_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"


# ---------------------------------------------------------------------------
# Task 3: Skill Demand Trend Engine API Test
# ---------------------------------------------------------------------------

async def test_skill_trends_endpoint(client: AsyncClient, seed_student):
    user, _ = seed_student
    headers = auth_headers(user)

    res = await client.get("/api/v1/analytics/skills/trends", headers=headers)
    assert res.status_code == 200
    trends = res.json()

    assert "surging" in trends
    assert "stable" in trends
    assert "declining" in trends
    assert "computed_at" in trends
    assert "based_on_drives" in trends

    assert isinstance(trends["surging"], list)
    assert len(trends["surging"]) >= 3
    first_surging = trends["surging"][0]
    assert "skill" in first_surging
    assert "growth_pct" in first_surging
    assert first_surging["growth_pct"] > 30

    assert isinstance(trends["stable"], list)
    assert len(trends["stable"]) >= 3

    assert isinstance(trends["declining"], list)
    assert len(trends["declining"]) >= 1
    assert trends["declining"][0]["growth_pct"] < -10
