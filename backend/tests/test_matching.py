"""
Unit tests for the ML Gap Engine and ML Matcher.

These tests run entirely in-process (no DB, no network).
They validate scoring logic, edge cases, and regression baselines.
"""

import pytest

from app.ml.gap_engine import (
    compute_gap_scores,
    recommend_next_skills,
    _severity,
    ROLE_PROFILES,
)
from app.ml.matcher import predict_match_score, _heuristic_score


# ---------------------------------------------------------------------------
# Gap Engine — severity classifier
# ---------------------------------------------------------------------------

class TestSeverityClassifier:
    def test_no_gap(self):
        assert _severity(0.0) == "none"

    def test_low_gap(self):
        assert _severity(0.05) == "low"

    def test_medium_gap(self):
        assert _severity(0.20) == "medium"

    def test_high_gap(self):
        assert _severity(0.35) == "high"

    def test_critical_gap(self):
        assert _severity(0.60) == "critical"

    def test_boundary_low(self):
        assert _severity(0.10) == "low"

    def test_boundary_medium(self):
        assert _severity(0.25) == "medium"

    def test_boundary_high(self):
        assert _severity(0.40) == "high"


# ---------------------------------------------------------------------------
# Gap Engine — compute_gap_scores
# ---------------------------------------------------------------------------

class TestGapEngine:
    def test_perfect_student_scores_near_100(self):
        """A student who meets all requirements should have a high overall score."""
        profile = ROLE_PROFILES["Data Analyst"]
        # Give student exactly what is required
        student_skills = {skill: req for skill, req in profile.items()}
        result = compute_gap_scores(student_skills, "Data Analyst", use_embeddings=False)
        assert result["overall_score"] >= 95.0

    def test_empty_student_scores_low(self):
        """A student with no skills should score well below a proficient student."""
        result = compute_gap_scores({}, "Software Engineer", use_embeddings=False)
        # No skills = large gaps; score should be below 40 (generous to semantic boosts)
        assert result["overall_score"] < 40.0

    def test_returns_correct_structure(self):
        result = compute_gap_scores({"python": 0.8}, "ML Engineer", use_embeddings=False)
        assert "target_role" in result
        assert "overall_score" in result
        assert "gaps" in result
        assert "strengths" in result
        assert isinstance(result["gaps"], list)

    def test_gaps_list_has_expected_fields(self):
        result = compute_gap_scores({"python": 0.5}, "Data Analyst", use_embeddings=False)
        for gap in result["gaps"]:
            assert "skill_name" in gap
            assert "current_score" in gap
            assert "required_score" in gap
            assert "gap" in gap
            assert "severity" in gap

    def test_unknown_role_falls_back_to_swe(self):
        """An unknown role should fall back to Software Engineer."""
        result = compute_gap_scores({}, "Ninja Wizard Developer", use_embeddings=False)
        assert result["target_role"] == "Software Engineer"

    def test_strength_detected_when_skill_met(self):
        """A skill that meets the requirement should appear in strengths."""
        result = compute_gap_scores(
            {"python": 0.95, "machine learning": 0.85},
            "ML Engineer",
            use_embeddings=False,
        )
        assert "python" in result["strengths"]

    def test_overall_score_in_valid_range(self):
        result = compute_gap_scores({"sql": 0.5, "python": 0.4}, "Data Analyst", use_embeddings=False)
        assert 0.0 <= result["overall_score"] <= 100.0

    def test_all_roles_produce_valid_output(self):
        """Smoke test every role profile."""
        for role in ROLE_PROFILES:
            result = compute_gap_scores({}, role, use_embeddings=False)
            assert 0.0 <= result["overall_score"] <= 100.0
            assert len(result["gaps"]) > 0


# ---------------------------------------------------------------------------
# Gap Engine — recommend_next_skills
# ---------------------------------------------------------------------------

class TestRecommendNextSkills:
    def test_returns_list(self):
        result = recommend_next_skills({}, "Software Engineer", n=3)
        assert isinstance(result, list)

    def test_n_cap_respected(self):
        result = recommend_next_skills({}, "ML Engineer", n=2)
        assert len(result) <= 2

    def test_only_actionable_gaps_returned(self):
        """Only medium/high/critical gaps should be recommended."""
        result = recommend_next_skills({}, "Data Analyst", n=10)
        for item in result:
            assert item["severity"] in ("medium", "high", "critical")

    def test_no_recommendation_when_all_met(self):
        """No gaps if student perfectly matches the role."""
        profile = ROLE_PROFILES["Software Engineer"]
        perfect = {s: r + 0.1 for s, r in profile.items()}
        result = recommend_next_skills(perfect, "Software Engineer", n=5)
        assert result == []


# ---------------------------------------------------------------------------
# ML Matcher — heuristic scorer
# ---------------------------------------------------------------------------

class TestHeuristicMatcher:
    def test_full_skill_match_scores_high(self):
        student = {"python": 1.0, "sql": 1.0, "machine learning": 1.0}
        job = {"python": "required", "sql": "required", "machine learning": "required"}
        score = _heuristic_score(student, job, 9.0, 7.0, "CS", ["CS"])
        assert score >= 80.0

    def test_no_skill_match_scores_low(self):
        student = {}
        job = {"python": "required", "sql": "required"}
        score = _heuristic_score(student, job, 6.0, 7.5, "CS", None)
        # No skills + below cgpa
        assert score < 50.0

    def test_dept_mismatch_penalty(self):
        student = {"python": 1.0, "sql": 1.0}
        job = {"python": "required", "sql": "required"}
        with_dept = _heuristic_score(student, job, 8.0, 7.0, "CS", ["CS"])
        without_dept = _heuristic_score(student, job, 8.0, 7.0, "EC", ["CS"])
        assert with_dept > without_dept

    def test_score_capped_at_100(self):
        student = {s: 1.0 for s in ["python", "sql", "machine learning", "docker"]}
        job = {s: "required" for s in ["python", "sql", "machine learning", "docker"]}
        score = _heuristic_score(student, job, 10.0, 6.0, "CS", ["CS"])
        assert score <= 100.0

    def test_score_non_negative(self):
        score = _heuristic_score({}, {"java": "required"}, 5.0, 9.0, "ME", ["CS"])
        assert score >= 0.0

    def test_empty_job_skills_returns_baseline(self):
        score = _heuristic_score({"python": 0.8}, {}, 8.0, None, "CS", None)
        assert score >= 0.0


# ---------------------------------------------------------------------------
# ML Matcher — predict_match_score (uses trained model or heuristic)
# ---------------------------------------------------------------------------

class TestPredictMatchScore:
    def test_returns_float(self):
        score = predict_match_score(
            student_skills={"python": 0.8, "sql": 0.7},
            job_skills={"python": "required", "sql": "preferred"},
        )
        assert isinstance(score, float)

    def test_score_in_valid_range(self):
        score = predict_match_score(
            student_skills={"python": 0.9},
            job_skills={"python": "required"},
        )
        assert 0.0 <= score <= 100.0

    def test_good_student_scores_higher_than_weak(self):
        good = predict_match_score(
            student_skills={"python": 0.9, "sql": 0.8, "machine learning": 0.8},
            job_skills={"python": "required", "sql": "required", "machine learning": "required"},
        )
        weak = predict_match_score(
            student_skills={"python": 0.2},
            job_skills={"python": "required", "sql": "required", "machine learning": "required"},
        )
        assert good > weak

    def test_cgpa_below_minimum_reduces_score(self):
        above = predict_match_score(
            student_skills={"python": 0.8},
            job_skills={"python": "required"},
            student_cgpa=9.0,
            job_min_cgpa=7.0,
        )
        below = predict_match_score(
            student_skills={"python": 0.8},
            job_skills={"python": "required"},
            student_cgpa=5.5,
            job_min_cgpa=8.0,
        )
        assert above > below

    def test_ineligible_dept_reduces_score(self):
        eligible = predict_match_score(
            student_skills={"python": 0.8},
            job_skills={"python": "required"},
            student_dept="CS",
            eligible_depts=["CS"],
        )
        ineligible = predict_match_score(
            student_skills={"python": 0.8},
            job_skills={"python": "required"},
            student_dept="ME",
            eligible_depts=["CS"],
        )
        assert eligible > ineligible

    def test_empty_inputs_do_not_crash(self):
        score = predict_match_score(student_skills={}, job_skills={})
        assert 0.0 <= score <= 100.0
