"""
Comprehensive test suite for Sprint 3 features:
1. Live ML Match Scores across Drives & Rich Matching Endpoints (What-If, Drive Match, Rank-Cohort, Top Drives)
2. Gemini-Powered Skill Demand Forecasting, Emerging Trends, & Heatmap Matrix
3. Peer Benchmarking Engine (Cohort aggregates, Leaderboard, Readiness Score)
4. Adaptive Assessment Engine (Code Execution Sandbox, Analytics, Questions Bank CRUD)
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.user import User, Student, Department
from app.models.industry import Company, Job, JobSkill
from app.models.placement import PlacementDrive, Application
from app.models.skill import Skill, StudentSkill
from app.models.assessment import AssessmentQuestionBank, AssessmentSession, AssessmentSessionQuestion
from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Task 1: Live ML Match Scores & Matching Endpoints
# ---------------------------------------------------------------------------

class TestSprint3MatchingEndpoints:
    async def test_list_drives_includes_match_score(self, client: AsyncClient, seed_student, seed_tpo, db):
        student_user, student = seed_student
        tpo_user = seed_tpo
        
        # Create a company and a drive
        company = Company(id=uuid.uuid4(), name=f"TechCorp-{uuid.uuid4().hex[:4]}")
        db.add(company)
        await db.commit()
        await db.refresh(company)

        job = Job(
            id=uuid.uuid4(),
            company_id=company.id,
            title="Software Development Engineer",
            description="Full-time software engineering role working on backend APIs and microservices.",
            min_cgpa=7.0,
            eligible_departments=["CS", "IT"],
            is_active=True,
        )
        db.add(job)
        await db.commit()

        # Add skill requirement to job
        r = await db.execute(select(Skill).where(Skill.normalized_name == "python"))
        py_skill = r.scalar_one_or_none()
        if py_skill:
            js = JobSkill(job_id=job.id, skill_id=py_skill.id, importance="required")
            db.add(js)
            await db.commit()

        drive = PlacementDrive(
            id=uuid.uuid4(),
            company_id=company.id,
            title="TechCorp SDE Campus Drive",
            min_cgpa=7.0,
            eligible_departments=["CS", "IT"],
            status="open",
        )
        db.add(drive)
        await db.commit()
        await db.refresh(drive)

        # 1. Student lists drives -> should have match_score
        res = await client.get("/api/v1/drives", headers=auth_headers(student_user))
        assert res.status_code == 200
        data = res.json()
        assert "data" in data
        assert len(data["data"]) >= 1
        
        target_drive = next((d for d in data["data"] if d["id"] == str(drive.id)), None)
        assert target_drive is not None
        assert "match_score" in target_drive
        assert target_drive["match_score"] is not None
        assert target_drive["match_score"] > 0

    async def test_get_matching_drive_breakdown(self, client: AsyncClient, seed_student, db):
        student_user, _ = seed_student
        
        # Query any existing drive
        r = await db.execute(select(PlacementDrive).limit(1))
        drive = r.scalar_one()

        res = await client.get(f"/api/v1/matching/drives/{drive.id}", headers=auth_headers(student_user))
        assert res.status_code == 200
        data = res.json()
        assert "drive_id" in data
        assert "overall_score" in data
        assert "skill_score" in data
        assert "cgpa_score" in data
        assert "dept_eligible" in data
        assert "skill_breakdown" in data
        assert "recommendation" in data

    async def test_get_top_drives(self, client: AsyncClient, seed_student):
        student_user, _ = seed_student
        res = await client.get("/api/v1/matching/my-top-drives", headers=auth_headers(student_user))
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "drive_id" in data[0]
            assert "match_score" in data[0]

    async def test_get_drive_skill_gap(self, client: AsyncClient, seed_student, db):
        student_user, _ = seed_student
        r = await db.execute(select(PlacementDrive).limit(1))
        drive = r.scalar_one()

        res = await client.get(f"/api/v1/matching/skill-gap/{drive.id}", headers=auth_headers(student_user))
        assert res.status_code == 200
        data = res.json()
        assert "drive_id" in data
        assert "gaps" in data
        assert isinstance(data["gaps"], list)

    async def test_get_job_fit(self, client: AsyncClient, seed_student, db):
        student_user, _ = seed_student
        r = await db.execute(select(Job).limit(1))
        job = r.scalar_one_or_none()
        if job:
            res = await client.get(f"/api/v1/matching/job-fit/{job.id}", headers=auth_headers(student_user))
            assert res.status_code == 200
            data = res.json()
            assert "job_id" in data
            assert "score" in data

    async def test_rank_cohort(self, client: AsyncClient, seed_student):
        student_user, _ = seed_student
        res = await client.get("/api/v1/matching/rank-cohort", headers=auth_headers(student_user))
        assert res.status_code == 200
        data = res.json()
        assert "student_avg_score" in data
        assert "dept_median" in data
        assert "percentile" in data

    async def test_what_if_simulation(self, client: AsyncClient, seed_student, db):
        student_user, _ = seed_student
        r = await db.execute(select(PlacementDrive).limit(1))
        drive = r.scalar_one()

        # 1. Simulate skill addition
        res = await client.post(
            "/api/v1/matching/what-if",
            json={"skill_to_add": "Kubernetes", "drive_id": str(drive.id)},
            headers=auth_headers(student_user),
        )
        assert res.status_code == 200
        data = res.json()
        assert "current_score" in data
        assert "simulated_score" in data
        assert "delta" in data
        assert data["skill_added"] == "Kubernetes"

        # 2. Simulate CGPA improvement
        res_cgpa = await client.post(
            "/api/v1/matching/what-if",
            json={"target_cgpa": 9.5, "drive_id": str(drive.id)},
            headers=auth_headers(student_user),
        )
        assert res_cgpa.status_code == 200
        data_cgpa = res_cgpa.json()
        assert "current_score" in data_cgpa
        assert "simulated_score" in data_cgpa
        assert "delta" in data_cgpa


# ---------------------------------------------------------------------------
# Task 2: Gemini Skill Trend Forecasting & Analytics Endpoints
# ---------------------------------------------------------------------------

class TestSprint3SkillTrends:
    async def test_skill_trends_full(self, client: AsyncClient, seed_student):
        student_user, _ = seed_student
        res = await client.get("/api/v1/analytics/skill-trends/full", headers=auth_headers(student_user))
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "skill_name" in data[0] or "skill" in data[0]
        assert "demand_count" in data[0]

    async def test_skill_trends_emerging(self, client: AsyncClient, seed_student):
        student_user, _ = seed_student
        res = await client.get("/api/v1/analytics/skill-trends/emerging", headers=auth_headers(student_user))
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "skill_name" in data[0] or "skill" in data[0]
            assert "narrative" in data[0] or "forecast_narrative" in data[0]

    async def test_skill_trends_heatmap(self, client: AsyncClient, seed_student):
        student_user, _ = seed_student
        res = await client.get("/api/v1/analytics/skill-trends/heatmap", headers=auth_headers(student_user))
        assert res.status_code == 200
        data = res.json()
        assert "departments" in data
        assert "skills" in data
        assert "matrix" in data
        assert isinstance(data["matrix"], list)

    async def test_skill_trends_single_skill(self, client: AsyncClient, seed_student):
        student_user, _ = seed_student
        res = await client.get("/api/v1/analytics/skill-trends/Python", headers=auth_headers(student_user))
        assert res.status_code == 200
        data = res.json()
        assert "skill_name" in data or "skill" in data
        assert "forecast_narrative" in data or "narrative" in data


# ---------------------------------------------------------------------------
# Task 3: Peer Benchmarking Engine
# ---------------------------------------------------------------------------

class TestSprint3Benchmarking:
    async def test_get_cohort_benchmark(self, client: AsyncClient, seed_student):
        student_user, _ = seed_student
        res = await client.get("/api/v1/matching/benchmark", headers=auth_headers(student_user))
        assert res.status_code == 200
        data = res.json()
        assert "cgpa" in data
        assert "skills" in data
        assert "assessments" in data
        assert "applications" in data
        assert "percentile" in data["cgpa"]

    async def test_get_leaderboard(self, client: AsyncClient, seed_student):
        student_user, _ = seed_student
        res = await client.get("/api/v1/matching/leaderboard/CS?metric=cgpa", headers=auth_headers(student_user))
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "rank" in data[0]
            assert "label" in data[0]
            assert "value" in data[0]
            assert "is_me" in data[0]

    async def test_get_readiness_score(self, client: AsyncClient, seed_student):
        student_user, _ = seed_student
        res = await client.get("/api/v1/matching/readiness", headers=auth_headers(student_user))
        assert res.status_code == 200
        data = res.json()
        assert "total_score" in data
        assert "components" in data
        assert "label" in data
        assert data["label"] in ["Placement Ready", "Almost There", "Needs Work"]


# ---------------------------------------------------------------------------
# Task 4: Adaptive Assessment Engine & Questions Bank CRUD
# ---------------------------------------------------------------------------

class TestSprint3AssessmentsAndQuestions:
    async def test_questions_crud_as_tpo(self, client: AsyncClient, seed_tpo):
        tpo_user = seed_tpo
        
        # 1. Create a coding question
        payload = {
            "topic": "Python",
            "difficulty": "medium",
            "question_type": "coding",
            "question_text": "Write a function to return the square of a number.",
            "code_problem_statement": "Given an integer n, return n * n.",
            "code_input_format": "Integer n",
            "code_output_format": "Integer n squared",
            "code_sample_inputs": ["5", "3"],
            "code_sample_outputs": ["25", "9"],
            "code_test_cases": [
                {"input": "5", "output": "25"},
                {"input": "3", "output": "9"},
                {"input": "0", "output": "0"}
            ],
            "code_language": "python",
        }
        res = await client.post("/api/v1/questions", json=payload, headers=auth_headers(tpo_user))
        assert res.status_code == 200
        created = res.json()
        q_id = created["id"]
        assert created["question_type"] == "coding"

        # 2. List questions
        list_res = await client.get("/api/v1/questions?topic=Python", headers=auth_headers(tpo_user))
        assert list_res.status_code == 200
        assert any(q["id"] == q_id for q in list_res.json())

        # 3. Patch question
        patch_res = await client.patch(
            f"/api/v1/questions/{q_id}",
            json={"difficulty": "hard"},
            headers=auth_headers(tpo_user)
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["difficulty"] == "hard"

        # 4. Usage stats
        stats_res = await client.get(f"/api/v1/questions/{q_id}/usage-stats", headers=auth_headers(tpo_user))
        assert stats_res.status_code == 200
        assert "times_asked" in stats_res.json()

        # 5. Delete question
        del_res = await client.delete(f"/api/v1/questions/{q_id}", headers=auth_headers(tpo_user))
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "success"

    async def test_questions_crud_forbidden_for_student(self, client: AsyncClient, seed_student):
        student_user, _ = seed_student
        res = await client.post("/api/v1/questions", json={"topic": "Python"}, headers=auth_headers(student_user))
        assert res.status_code == 403

    async def test_submit_code_sandbox(self, client: AsyncClient, seed_student, db):
        student_user, _ = seed_student

        # Create a coding question
        q = AssessmentQuestionBank(
            id=uuid.uuid4(),
            topic="Python",
            difficulty="easy",
            question_type="coding",
            question_text="Return sum of two numbers",
            code_problem_statement="Read a and b from input and print a + b",
            code_test_cases=[
                {"input": "2 3", "output": "5"},
                {"input": "10 20", "output": "30"}
            ],
            is_active=True
        )
        db.add(q)
        
        session = AssessmentSession(
            id=uuid.uuid4(),
            student_id=student_user.id,
            topic="Python",
            difficulty="easy",
            status="in_progress",
            metadata_col={"current_difficulty": "easy", "streak": 0}
        )
        db.add(session)
        await db.commit()

        # Test valid Python code
        code_sub = {
            "question_id": str(q.id),
            "code": "import sys\nline = sys.stdin.read().strip()\nif line:\n    a, b = map(int, line.split())\n    print(a + b)",
            "language": "python"
        }
        res = await client.post(
            f"/api/v1/assessments/{session.id}/submit-code",
            json=code_sub,
            headers=auth_headers(student_user)
        )
        assert res.status_code == 200
        result = res.json()
        assert "passed" in result
        assert "total" in result
        assert result["passed"] == 2

    async def test_assessment_analytics(self, client: AsyncClient, seed_student):
        student_user, _ = seed_student

        res = await client.get("/api/v1/assessments/analytics/my", headers=auth_headers(student_user))
        assert res.status_code == 200
        data = res.json()
        assert "topics" in data
        assert "overall_avg" in data

        cohort_res = await client.get("/api/v1/assessments/analytics/cohort/Python", headers=auth_headers(student_user))
        assert cohort_res.status_code == 200
        c_data = cohort_res.json()
        assert "skill" in c_data
        assert "cohort_avg" in c_data
