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
from app.ml.embeddings import get_embedder
from app.schemas.matching import SemanticSkillDetail, MatchBreakdown

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


def compute_breakdown(
    student_skills: dict[str, float],
    job_skills: dict[str, str],
    student_cgpa: Optional[float] = None,
    job_min_cgpa: Optional[float] = None,
    student_dept: Optional[str] = None,
    eligible_depts: Optional[list[str]] = None,
    student_projects: Optional[list[dict]] = None,
) -> MatchBreakdown:
    """
    Computes the diagnostic breakdown alongside the match score.
    Breakdown includes:
      - Academic fit score (0-100) & human-readable reason
      - Technical skills score (0-100) with semantic direct/adjacent/missing details
      - Practical experience bonus (0-20) from relevant projects/internships
      - Total weighted score (0-100)
      - Top missing skills & targeted learning recommendation
    """
    embedder = get_embedder()

    # 1. Academic Score & Reason
    academic_score = 100.0
    dept_eligible = True
    if eligible_depts and student_dept:
        dept_eligible = student_dept.upper() in [d.upper() for d in eligible_depts]
        if not dept_eligible:
            academic_score = 0.0
            academic_reason = f"Branch {student_dept} is outside eligible departments ({', '.join(eligible_depts)})."
        else:
            academic_reason = f"Branch {student_dept} is eligible."
    else:
        academic_reason = "Branch criteria satisfied."

    if dept_eligible:
        if student_cgpa is not None and job_min_cgpa is not None:
            if student_cgpa >= job_min_cgpa:
                academic_score = min(100.0, 85.0 + (student_cgpa - job_min_cgpa) * 10.0)
                academic_reason = f"CGPA {student_cgpa:.1f} meets threshold {job_min_cgpa:.1f}. {academic_reason}"
            else:
                deficit = job_min_cgpa - student_cgpa
                academic_score = max(0.0, 100.0 - deficit * 35.0)
                academic_reason = f"CGPA {student_cgpa:.1f} is below required {job_min_cgpa:.1f}. {academic_reason}"
        else:
            academic_score = 100.0
            academic_reason = f"No minimum CGPA required. {academic_reason}"

    academic_score = round(min(100.0, max(0.0, academic_score)), 1)

    # 2. Skills Score & Semantic Details
    skill_details: list[SemanticSkillDetail] = []
    weight_map = {"required": 1.5, "preferred": 1.0, "nice_to_have": 0.6}
    total_skill_weight = 0.0
    weighted_sim_sum = 0.0

    # Ensure lowercase comparison keys
    norm_student_skills = {k.lower().strip(): v for k, v in student_skills.items()}

    for req_skill_raw, importance in job_skills.items():
        req_skill = req_skill_raw.lower().strip()
        w = weight_map.get(str(importance).lower(), 1.0)
        total_skill_weight += w

        best_student_skill = ""
        best_sim = 0.0

        if req_skill in norm_student_skills:
            best_student_skill = req_skill_raw
            best_sim = 1.0
        else:
            for s_skill, conf in norm_student_skills.items():
                if conf < 0.2:
                    continue
                sim = embedder.cosine_similarity(req_skill, s_skill)
                if sim > best_sim:
                    best_sim = sim
                    best_student_skill = s_skill

        if best_sim >= 0.95:
            m_type = "direct"
            if not best_student_skill:
                best_student_skill = req_skill_raw
        elif best_sim >= 0.60:
            m_type = "adjacent"
        else:
            m_type = "missing"
            if not best_student_skill:
                best_student_skill = "None"

        weighted_sim_sum += (best_sim * w)
        skill_details.append(
            SemanticSkillDetail(
                required_skill=req_skill_raw,
                student_skill=best_student_skill,
                similarity=round(best_sim, 2),
                match_type=m_type,
            )
        )

    skills_score = (weighted_sim_sum / total_skill_weight * 100.0) if total_skill_weight > 0 else 50.0
    skills_score = round(min(100.0, max(0.0, skills_score)), 1)

    # 3. Practical Experience Bonus
    experience_bonus = 0.0
    relevant_projects: list[str] = []

    req_keywords = [k.lower().strip() for k in job_skills.keys()]

    if student_projects:
        for p in student_projects:
            techs = [str(t).lower() for t in p.get("technologies", [])]
            p_title = str(p.get("title", ""))
            p_desc = str(p.get("description", "")).lower()
            # check relevance
            matched_techs = [kw for kw in req_keywords if kw in techs or kw in p_desc or kw in p_title.lower()]
            if matched_techs:
                experience_bonus += 5.0
                relevant_projects.append(f'Project: "{p_title}" ({", ".join(matched_techs[:3])})')
                if len(relevant_projects) >= 3:
                    break

    experience_bonus = min(20.0, experience_bonus)

    # 4. Total Score Calculation
    total_score = round(
        0.40 * academic_score + 0.45 * skills_score + 0.15 * (experience_bonus / 20.0 * 100.0),
        1
    )
    total_score = min(100.0, max(0.0, total_score))

    # 5. Missing Skills & Recommendation
    missing_items = [d for d in skill_details if d.match_type == "missing"]
    top_missing_skills = [d.required_skill for d in missing_items[:3]]

    if missing_items:
        target = missing_items[0].required_skill
        w_target = weight_map.get(str(job_skills.get(target, "required")).lower(), 1.0)
        boost = round((0.45 * (1.0 - missing_items[0].similarity) * w_target / max(total_skill_weight, 1.0)) * 100)
        boost = max(6, min(22, boost))
        recommendation = f"Adding 1 {target} project would boost this match by +{boost}%"
    else:
        recommendation = "You possess all required technical competencies for this role!"

    return MatchBreakdown(
        academic_score=academic_score,
        skills_score=skills_score,
        experience_bonus=round(experience_bonus, 1),
        total_score=total_score,
        skill_details=skill_details,
        academic_reason=academic_reason,
        top_missing_skills=top_missing_skills,
        recommendation=recommendation,
        relevant_projects=relevant_projects,
    )


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
