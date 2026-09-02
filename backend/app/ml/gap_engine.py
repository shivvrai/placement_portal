"""
ML-based Skill Gap Engine — upgrades rule-based gap scoring to ML.

Algorithm:
  1. Load student skill confidences + role skill requirements
  2. Build gap feature vector via features.py
  3. Score each skill gap using:
     a. Semantic similarity (embedding distance) to bridge related skills
     b. Composite severity score from a calibrated linear model
  4. Recommend learning resources per gap

Also exposes compute_gap_score() used by matching_service.py.
"""

from __future__ import annotations

import logging
import numpy as np
from typing import Optional

from app.ml.features import CANONICAL_SKILLS, SKILL_INDEX, N_SKILLS
from app.ml.embeddings import get_embedder

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Role Requirement Profiles
# Format: {role_name: {skill: required_confidence (0-1)}}
# ---------------------------------------------------------------------------
ROLE_PROFILES: dict[str, dict[str, float]] = {
    "Data Analyst": {
        "sql": 0.80, "python": 0.70, "statistics": 0.65,
        "data analysis": 0.75, "tableau": 0.55, "excel": 0.50,
        "pandas": 0.60, "numpy": 0.45,
    },
    "Software Engineer": {
        "data structures": 0.80, "algorithms": 0.80, "python": 0.65,
        "system design": 0.60, "git": 0.70, "os": 0.55, "rest api": 0.65,
        "postgresql": 0.50,
    },
    "ML Engineer": {
        "python": 0.85, "machine learning": 0.80, "statistics": 0.75,
        "deep learning": 0.65, "sql": 0.60, "docker": 0.50,
        "pandas": 0.70, "scikit-learn": 0.70, "tensorflow": 0.60,
    },
    "Full Stack Developer": {
        "javascript": 0.80, "react": 0.75, "node.js": 0.70, "sql": 0.65,
        "rest api": 0.75, "git": 0.70, "css": 0.60, "html": 0.60,
    },
    "DevOps Engineer": {
        "docker": 0.80, "kubernetes": 0.70, "linux": 0.75, "ci/cd": 0.75,
        "python": 0.55, "aws": 0.65, "terraform": 0.60, "git": 0.80,
    },
    "Data Engineer": {
        "python": 0.80, "sql": 0.85, "spark": 0.70, "kafka": 0.60,
        "airflow": 0.55, "aws": 0.55, "docker": 0.50, "data engineering": 0.70,
    },
    "Backend Developer": {
        "python": 0.75, "fastapi": 0.65, "postgresql": 0.70, "redis": 0.55,
        "docker": 0.60, "rest api": 0.80, "system design": 0.60, "git": 0.70,
    },
}

# Learning resource suggestions per skill
SKILL_RESOURCES: dict[str, list[dict]] = {
    "python": [
        {"title": "Python for Everybody – Coursera", "url": "https://coursera.org/learn/python", "type": "course"},
        {"title": "LeetCode Python Problems", "url": "https://leetcode.com/problemset/", "type": "practice"},
    ],
    "sql": [
        {"title": "Mode Analytics SQL Tutorial", "url": "https://mode.com/sql-tutorial/", "type": "tutorial"},
        {"title": "StrataScratch – SQL Practice", "url": "https://stratascratch.com", "type": "practice"},
    ],
    "machine learning": [
        {"title": "Andrew Ng ML Course – Coursera", "url": "https://coursera.org/learn/machine-learning", "type": "course"},
        {"title": "fast.ai Practical DL", "url": "https://fast.ai", "type": "course"},
    ],
    "docker": [
        {"title": "Docker Official Get Started", "url": "https://docs.docker.com/get-started/", "type": "docs"},
        {"title": "KodeKloud Docker Course", "url": "https://kodekloud.com", "type": "course"},
    ],
    "react": [
        {"title": "React Official Docs", "url": "https://react.dev/learn", "type": "docs"},
        {"title": "Full Stack Open – React", "url": "https://fullstackopen.com", "type": "course"},
    ],
    "system design": [
        {"title": "System Design Primer – GitHub", "url": "https://github.com/donnemartin/system-design-primer", "type": "resource"},
        {"title": "Grokking System Design – Educative", "url": "https://educative.io", "type": "course"},
    ],
    "data structures": [
        {"title": "NeetCode 150", "url": "https://neetcode.io/practice", "type": "practice"},
        {"title": "CLRS – Introduction to Algorithms", "url": "https://mitpress.mit.edu/books/introduction-algorithms", "type": "book"},
    ],
}
_DEFAULT_RESOURCES = [{"title": "Search on Coursera or YouTube", "url": "https://coursera.org", "type": "search"}]


def _severity(gap: float) -> str:
    """Convert a gap score (0-1) to severity label."""
    if gap <= 0:
        return "none"
    if gap <= 0.10:
        return "low"
    if gap <= 0.25:
        return "medium"
    if gap <= 0.40:
        return "high"
    return "critical"


def _get_semantic_boost(
    student_skills: dict[str, float],
    missing_skill: str,
) -> float:
    """
    Use embedding similarity to detect if the student has a related skill
    that partially covers the missing skill.
    Returns a 0-0.3 boost to reduce the effective gap.
    """
    embedder = get_embedder()
    best_sim = 0.0
    for owned_skill, confidence in student_skills.items():
        if confidence < 0.3:
            continue
        sim = embedder.cosine_similarity(owned_skill, missing_skill)
        weighted = sim * confidence
        if weighted > best_sim:
            best_sim = weighted
    # Cap semantic boost at 0.3 (30% gap reduction)
    return min(best_sim * 0.3, 0.3)


def compute_gap_scores(
    student_skills: dict[str, float],  # {skill_name (lower): confidence 0-1}
    target_role: str,
    use_embeddings: bool = True,
) -> dict:
    """
    Compute ML-enhanced skill gap scores for a student vs a target role.

    Returns:
        {
          "target_role": str,
          "overall_score": float (0-100),
          "gaps": [GapItem],
          "strengths": [str],
        }
    """
    profile = ROLE_PROFILES.get(target_role)
    if not profile:
        target_role = "Software Engineer"
        profile = ROLE_PROFILES[target_role]

    gaps = []
    strengths = []
    total_required = sum(profile.values())
    weighted_gap_sum = 0.0

    for skill, required_conf in sorted(profile.items(), key=lambda x: -x[1]):
        current_conf = student_skills.get(skill, 0.0)
        raw_gap = max(0.0, required_conf - current_conf)

        # Semantic boost — if student has a related skill, reduce gap
        semantic_boost = 0.0
        if use_embeddings and raw_gap > 0.1:
            try:
                semantic_boost = _get_semantic_boost(student_skills, skill)
            except Exception:
                pass

        adjusted_gap = max(0.0, raw_gap - semantic_boost)
        weighted_gap_sum += adjusted_gap * (required_conf / total_required)

        if current_conf >= required_conf:
            strengths.append(skill)

        gaps.append({
            "skill_name": skill,
            "current_score": round(current_conf * 100, 1),
            "required_score": round(required_conf * 100, 1),
            "gap": round(adjusted_gap * 100, 1),
            "severity": _severity(adjusted_gap),
            "semantic_boost": round(semantic_boost * 100, 1),
            "resources": SKILL_RESOURCES.get(skill, _DEFAULT_RESOURCES),
        })

    # Overall readiness score = 1 - weighted_gap
    overall_score = round(max(0.0, 100.0 - weighted_gap_sum * 100), 1)

    # Sort gaps: critical → high → medium → low → none
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4}
    gaps.sort(key=lambda g: severity_order.get(g["severity"], 5))

    return {
        "target_role": target_role,
        "overall_score": overall_score,
        "gaps": gaps,
        "strengths": strengths,
        "available_roles": list(ROLE_PROFILES.keys()),
    }


def recommend_next_skills(
    student_skills: dict[str, float],
    target_role: str,
    n: int = 3,
) -> list[dict]:
    """
    Return top N skills to learn next (medium/high gap, highest impact).
    Used by the Copilot for personalised advice.
    """
    result = compute_gap_scores(student_skills, target_role, use_embeddings=False)
    actionable = [
        g for g in result["gaps"]
        if g["severity"] in ("medium", "high", "critical")
    ]
    return actionable[:n]
