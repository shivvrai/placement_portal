"""
Unit and Integration Tests for Sachin's Final Task Sheet:
- Semantic Embedding & 152-Feature Vector Pipeline
- ML Model Matcher & Heuristic Fallback
- Explainable Match Diagnostics & Edge Cases (Zero-Skill, Archetype Fallback)
- Multi-Severity Skill Gap Analyzer & Readiness Score
- Holt's Double Exponential Smoothing Skill Demand Forecasting
- Institutional Peer Benchmarking & Cohort Distribution
"""

import uuid
import pytest
import numpy as np
from httpx import AsyncClient
from sqlalchemy import select
from app.ml.embeddings import SkillEmbedder
from app.ml.features import build_152_feature_vector, PAIR_FEATURE_DIM
from app.ml.matcher import predict_match_probability, predict_match_score, heuristic_match_score
from app.ml.gap_engine import classify_gap_severity, compute_gap_scores
import app.ml.forecasting as forecasting
from app.ml.forecasting import holts_double_exponential_smoothing, compute_holt_skill_trends
from app.models.user import User, Student, Department
from app.models.industry import Company, Job, JobSkill
from app.models.placement import PlacementDrive
from app.models.skill import Skill, StudentSkill
from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


class TestTask1SemanticAndFeaturePipeline:
    def test_semantic_embedding_dense_and_similarity(self):
        embedder = SkillEmbedder()
        skills = ["Python", "FastAPI", "React", "Docker"]
        matrix = embedder.compute_similarity_matrix(skills, skills)
        assert matrix.shape == (4, 4)
        for i in range(4):
            # Self similarity should be near 1.0
            assert matrix[i, i] >= 0.95

        dense_vec_384 = embedder.encode_dense("Machine Learning", target_dim=384)
        assert isinstance(dense_vec_384, np.ndarray)
        assert len(dense_vec_384) == 384

        dense_vec_128 = embedder.encode_dense("Machine Learning", target_dim=128)
        assert isinstance(dense_vec_128, np.ndarray)
        assert len(dense_vec_128) == 128

    def test_152_feature_vector_dimension(self):
        student_skills = {"python": 0.9, "sql": 0.8}
        job_skills = {"python": 1.0, "docker": 0.8}
        vec = build_152_feature_vector(
            student_skills=student_skills,
            job_skills=job_skills,
            student_cgpa=8.5,
            job_min_cgpa=7.0,
            student_dept="CS",
            job_depts=["CS", "IT"],
            verified_ratio=0.8,
            experience_months=6,
        )
        assert len(vec) == 152
        assert PAIR_FEATURE_DIM == 152

    def test_matcher_probability_and_fallback(self):
        prob = predict_match_probability(
            student_skills={"python": 0.9, "react": 0.8},
            job_skills={"python": 1.0, "react": 0.8},
            student_cgpa=8.5,
            job_min_cgpa=7.0,
            student_dept="CS",
            job_depts=["CS"],
        )
        assert isinstance(prob, float)
        assert 0.0 <= prob <= 1.0

    def test_zero_skill_candidate_safety(self):
        # Empty skills should not trigger ZeroDivisionError
        score = predict_match_score(
            student_skills={},
            job_skills={"python": 1.0, "kubernetes": 0.8},
            student_cgpa=8.0,
            job_min_cgpa=7.0,
            student_dept="CS",
            job_depts=["CS"],
        )
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

        heuristic = heuristic_match_score(
            student_skills={},
            job_skills={"python": 1.0},
            student_cgpa=8.0,
            job_min_cgpa=7.0,
            student_dept="CS",
            job_depts=["CS"],
        )
        assert isinstance(heuristic, float)
        assert 0.0 <= heuristic <= 100.0


class TestTask2ExplainableDiagnostics:
    async def test_student_jobs_explainability_payload(self, client: AsyncClient, seed_student, db):
        student_user, student = seed_student

        # Create company and job
        company = Company(id=uuid.uuid4(), name=f"TestTech-{uuid.uuid4().hex[:4]}")
        db.add(company)
        await db.commit()

        job = Job(
            id=uuid.uuid4(),
            company_id=company.id,
            title="Software Development Engineer",
            description="Build scalable distributed services and APIs.",
            min_cgpa=7.0,
            eligible_departments=["CS", "IT"],
            is_active=True,
        )
        db.add(job)
        await db.commit()

        # Add python skill
        r = await db.execute(select(Skill).where(Skill.normalized_name == "python"))
        py_skill = r.scalar_one_or_none()
        if py_skill:
            db.add(JobSkill(job_id=job.id, skill_id=py_skill.id, importance="required"))
            await db.commit()

        res = await client.get(f"/api/v1/matching/students/{student.id}/jobs", headers=auth_headers(student_user))
        assert res.status_code == 200
        matches = res.json()
        assert isinstance(matches, list)
        if matches:
            first = matches[0]
            # Verify explainability payload schema
            assert "job_id" in first
            assert "drive_id" in first
            assert "company_name" in first
            assert "role" in first
            assert "match_score" in first
            assert "eligibility_passed" in first
            assert "matching_skills" in first
            assert "missing_skills" in first
            assert "diagnostic_summary" in first
            assert "match_breakdown" in first
            assert "skill_alignment" in first["match_breakdown"]
            assert "academic_score" in first["match_breakdown"]
            assert "experience_bonus" in first["match_breakdown"]


class TestTask3SkillGapSeverityAndReadiness:
    def test_classify_gap_severity(self):
        # Critical gap: Required skill missing (importance >= 0.70)
        _, sev1, _ = classify_gap_severity(importance_weight=0.9, current_conf=0.0, raw_gap=0.9)
        assert sev1 == "critical"

        # Moderate gap: Skill present but confidence < 0.60
        _, sev2, _ = classify_gap_severity(importance_weight=0.7, current_conf=0.45, raw_gap=0.25)
        assert sev2 == "moderate"

        # Minor gap: Optional/bonus skill missing (importance < 0.70)
        _, sev3, _ = classify_gap_severity(importance_weight=0.5, current_conf=0.0, raw_gap=0.5)
        assert sev3 == "minor"

        # No gap: student meets or exceeds required confidence
        _, sev4, _ = classify_gap_severity(importance_weight=0.8, current_conf=0.9, raw_gap=0.0)
        assert sev4 == "none"

    def test_gap_analysis_readiness_and_hours(self):
        student_skills = {"python": 0.85, "git": 0.70}
        analysis = compute_gap_scores(student_skills, target_role="Software Engineer")

        assert "readiness_score" in analysis
        assert "overall_score" in analysis
        assert 0.0 <= analysis["readiness_score"] <= 100.0
        assert "estimated_hours_to_bridge" in analysis
        assert analysis["estimated_hours_to_bridge"] >= 0

        # Verify gap items have gap_type and estimated_hours
        for gap in analysis["gaps"]:
            assert "gap_type" in gap
            assert gap["gap_type"] in ["critical", "moderate", "minor", "none"]
            assert "estimated_hours" in gap


class TestTask4InstitutionalBenchmarking:
    async def test_institutional_benchmark_endpoint(self, client: AsyncClient, seed_student):
        student_user, _ = seed_student
        res = await client.get("/api/v1/analytics/benchmark", headers=auth_headers(student_user))
        assert res.status_code == 200
        data = res.json()

        assert "department_name" in data
        assert "department_rank" in data
        assert "total_students" in data
        assert "overall_percentile" in data

        # Verify 4 institutional dimensions
        dims = data["dimensions"]
        assert "cgpa" in dims
        assert "verified_skills" in dims
        assert "assessment_pass_rate" in dims
        assert "mock_interview" in dims

        for d_key in ["cgpa", "verified_skills", "assessment_pass_rate", "mock_interview"]:
            d = dims[d_key]
            assert "value" in d
            assert "percentile" in d
            assert "mean" in d
            assert "std_dev" in d
            assert "median" in d

        # Verify Radar Chart overlay
        assert "radar_chart" in data
        assert len(data["radar_chart"]) == 4
        for r_item in data["radar_chart"]:
            assert "dimension" in r_item
            assert "candidate" in r_item
            assert "department_avg" in r_item
            assert "top_10_pct" in r_item

        # Verify Bell Curve Normal distribution points
        assert "bell_curve" in data
        assert len(data["bell_curve"]) > 10
        for pt in data["bell_curve"]:
            assert "percentile" in pt
            assert "density" in pt
            assert "is_candidate" in pt


class TestTask5HoltsDoubleExponentialForecasting:
    def test_holts_smoothing_algorithm(self):
        # 24-month upward trend series
        series = [10 + i * 2.5 for i in range(24)]
        y_hat, growth_rate, level = holts_double_exponential_smoothing(series, alpha=0.3, beta=0.1, h=3)
        # In an upward series, future forecast should be higher than the last historical point
        assert y_hat > series[-1]
        assert growth_rate > 0.0
        assert level > 0.0

    def test_holt_trends_classification_and_caching(self):
        forecasting._forecast_cache = None
        forecasting._forecast_cache_time = None
        trends = compute_holt_skill_trends()
        assert "surging" in trends
        assert "stable" in trends
        assert "declining" in trends
        assert "forecast_horizon_months" in trends
        assert trends["forecast_horizon_months"] == 3

        # Surging items should have growth > 15.0
        for item in trends["surging"]:
            assert item["growth_pct"] >= 15.0
            assert item["classification"] == "Surging"

        # Stable items should have -10.0 <= growth <= 10.0
        for item in trends["stable"]:
            assert -10.0 <= item["growth_pct"] <= 10.0
            assert item["classification"] == "Stable"

        # Declining items should have growth < -15.0
        for item in trends["declining"]:
            assert item["growth_pct"] <= -15.0
            assert item["classification"] == "Declining"

        # Second call should return from cache
        trends2 = compute_holt_skill_trends()
        assert trends2["as_of"] == trends["as_of"]
