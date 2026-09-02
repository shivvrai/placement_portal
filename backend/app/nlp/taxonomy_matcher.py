"""
Taxonomy Matcher — fuzzy-match raw extracted skill strings to
canonical Skill records in the database.

Uses rapidfuzz for fast string similarity (no external API needed).
Falls back to exact normalised match first for speed.
"""

from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.skill import Skill


# Similarity threshold — strings scoring below this are rejected
MATCH_THRESHOLD = 75.0  # out of 100


def _normalise(s: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    import re
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s\+#\.]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


async def load_skill_index(db: AsyncSession) -> dict[str, Skill]:
    """
    Load all Skills from DB into a dict keyed by normalised_name.
    Call once per request and pass the result around.
    """
    result = await db.execute(select(Skill))
    skills = result.scalars().all()
    return {s.normalized_name: s for s in skills}


def match_skill(
    raw_skill: str,
    skill_index: dict[str, Skill],
    threshold: float = MATCH_THRESHOLD,
) -> Optional[Skill]:
    """
    Match a raw skill string to the best canonical Skill in the index.

    Strategy:
      1. Exact match on normalised name
      2. Fuzzy match using rapidfuzz WRatio scorer

    Returns the matched Skill object or None if no match above threshold.
    """
    try:
        from rapidfuzz import process, fuzz
    except ImportError:
        # Fallback to exact match only
        norm = _normalise(raw_skill)
        return skill_index.get(norm)

    norm = _normalise(raw_skill)

    # 1. Exact match (fast path)
    if norm in skill_index:
        return skill_index[norm]

    # 2. Fuzzy match across all keys
    if not skill_index:
        return None

    candidates = list(skill_index.keys())
    result = process.extractOne(
        norm,
        candidates,
        scorer=fuzz.WRatio,
        score_cutoff=threshold,
    )

    if result is None:
        return None

    best_key, score, _ = result
    return skill_index[best_key]


async def match_skills_to_db(
    raw_skills: list[str],
    db: AsyncSession,
    threshold: float = MATCH_THRESHOLD,
) -> list[tuple[str, Optional[Skill], float]]:
    """
    Match a list of raw skill strings against the DB taxonomy.

    Returns list of (raw_skill, matched_Skill_or_None, confidence_score).
    """
    try:
        from rapidfuzz import fuzz
    except ImportError:
        fuzz = None

    skill_index = await load_skill_index(db)
    results: list[tuple[str, Optional[Skill], float]] = []

    for raw in raw_skills:
        norm = _normalise(raw)

        # Exact match
        if norm in skill_index:
            results.append((raw, skill_index[norm], 100.0))
            continue

        # Fuzzy match
        if fuzz and skill_index:
            from rapidfuzz import process
            match = process.extractOne(
                norm,
                list(skill_index.keys()),
                scorer=fuzz.WRatio,
                score_cutoff=threshold,
            )
            if match:
                best_key, score, _ = match
                results.append((raw, skill_index[best_key], float(score)))
            else:
                results.append((raw, None, 0.0))
        else:
            results.append((raw, None, 0.0))

    return results


async def create_or_get_skill(db: AsyncSession, name: str) -> Skill:
    """
    Find a skill by normalised name, or create a new one if it doesn't exist.
    Used when the NLP pipeline finds a brand-new skill not in the taxonomy.
    """
    import re
    normalised = re.sub(r"\s+", " ", name.lower().strip())

    result = await db.execute(
        select(Skill).where(Skill.normalized_name == normalised)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    new_skill = Skill(
        name=name.strip().title(),
        normalized_name=normalised,
        category="other",
    )
    db.add(new_skill)
    await db.flush()
    return new_skill
