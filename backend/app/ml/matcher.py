"""
Job-Student Matcher — ML-based scoring model.

Architecture:
  - Gradient Boosted trees (sklearn GradientBoostingRegressor)
  - Input: pair feature vector from features.py (N_SKILLS*2 + 8 dims)
  - Output: match score in [0, 100]
  - Falls back to heuristic scoring if no trained model exists

Model lifecycle:
  1. First run with no model -> heuristic scoring
  2. Run experiments/train_matcher.py -> generates matcher_model.pkl
  3. On startup, load_model() auto-detects and loads the pkl
  4. Scoring then uses the trained model automatically
"""

from __future__ import annotations

import os
import logging
import pickle
import uuid
from pathlib import Path
from typing import Optional

import numpy as np

from app.ml.features import build_pair_features, CANONICAL_SKILLS

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "matcher_model.pkl"

# Module-level model singleton
_model = None
_model_loaded: bool = False


def load_model():
    """Load trained model from disk if available."""
    global _model, _model_loaded
    if _model_loaded:
        return
    _model_loaded = True

    if MODEL_PATH.exists():
        try:
            with open(MODEL_PATH, "rb") as f:
                _model = pickle.load(f)
            logger.info("Loaded trained matcher model from %s", MODEL_PATH)
        except Exception as e:
            logger.warning("Could not load matcher model: %s. Using heuristic.", e)
            _model = None
    else:
        logger.info("No trained model found at %s. Using heuristic scorer.", MODEL_PATH)
        _model = None


def _heuristic_score(
    student_skills: dict[str, float],
    job_skills: dict[str, str],
    student_cgpa: Optional[float],
    job_min_cgpa: Optional[float],
    student_dept: Optional[str],
    eligible_depts: Optional[list[str]],
) -> float:
    """
    Rule-based fallback scoring (used when no trained model exists).
    Weighted: skill match 70% + CGPA 20% + dept eligibility 10%
    """
    weight_map = {"required": 1.5, "preferred": 1.0, "nice_to_have": 0.5}
    total_weight = sum(weight_map.get(imp, 1.0) for imp in job_skills.values())

    weighted_match = 0.0
    for skill, importance in job_skills.items():
        w = weight_map.get(importance, 1.0)
        conf = student_skills.get(skill.lower(), 0.0)
        weighted_match += w * conf

    skill_score = (weighted_match / total_weight * 100) if total_weight > 0 else 50.0

    cgpa_score = 100.0
    if student_cgpa and job_min_cgpa:
        if student_cgpa < job_min_cgpa:
            cgpa_score = max(0, 100 - (job_min_cgpa - student_cgpa) * 20)
        else:
            cgpa_score = min(100, 80 + (student_cgpa - job_min_cgpa) * 10)

    dept_score = 100.0
    if eligible_depts and student_dept and student_dept not in eligible_depts:
        dept_score = 0.0

    final = skill_score * 0.70 + cgpa_score * 0.20 + dept_score * 0.10
    return round(min(final, 100.0), 1)


def predict_match_score(
    student_skills: dict[str, float],
    job_skills: dict[str, str],
    student_cgpa: Optional[float] = None,
    job_min_cgpa: Optional[float] = None,
    student_dept: Optional[str] = None,
    eligible_depts: Optional[list[str]] = None,
) -> float:
    """
    Predict match score for a student-job pair.

    Returns a score in [0, 100].
    Uses trained ML model if available, heuristic otherwise.
    """
    load_model()

    if _model is not None:
        try:
            features = build_pair_features(
                student_skills=student_skills,
                job_skills=job_skills,
                student_cgpa=student_cgpa,
                job_min_cgpa=job_min_cgpa,
                student_dept=student_dept,
                eligible_depts=eligible_depts,
            )
            raw = float(_model.predict(features.reshape(1, -1))[0])
            return round(max(0.0, min(100.0, raw)), 1)
        except Exception as e:
            logger.warning("Model prediction failed, using heuristic: %s", e)

    return _heuristic_score(
        student_skills, job_skills,
        student_cgpa, job_min_cgpa,
        student_dept, eligible_depts,
    )


def rank_jobs(
    student_skills: dict[str, float],
    jobs: list[dict],
    student_cgpa: Optional[float] = None,
    student_dept: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """
    Rank a list of job dicts by predicted match score.

    Each job dict must have:
        "job_skills": {skill_name: importance}
        "min_cgpa": float | None
        "eligible_departments": list[str] | None

    Returns jobs sorted by match_score desc with score injected.
    """
    scored: list[dict] = []
    for job in jobs:
        job_skills = job.get("job_skills", {})
        score = predict_match_score(
            student_skills=student_skills,
            job_skills=job_skills,
            student_cgpa=student_cgpa,
            job_min_cgpa=job.get("min_cgpa"),
            student_dept=student_dept,
            eligible_depts=job.get("eligible_departments"),
        )
        scored.append({**job, "match_score": score})

    return sorted(scored, key=lambda j: j["match_score"], reverse=True)[:limit]
