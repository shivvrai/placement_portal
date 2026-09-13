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
MATCH_THRESHOLD = 80.0  # out of 100

CANONICAL_ALIASES: dict[str, str] = {
    "golang": "go",
    "go language": "go",
    "go programming": "go",
    "r language": "r",
    "r programming": "r",
    "r script": "r",
    "c programming": "c",
    "c language": "c",
    "postgres": "postgresql",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node": "node.js",
    "huggingface": "hugging face",
    "sklearn": "scikit-learn",
    "k8s": "kubernetes",
    "amazon web services": "aws",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "oops": "oop",
    "object oriented programming": "oop",
    "operating system": "operating systems",
    "data structure": "data structures",
    "data structures and algorithms": "data structures",
    "dsa": "data structures",
    "algorithm": "algorithms",
    "html5": "html",
    "css3": "css",
}


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
      1. Exact match on normalised name or alias
      2. Fuzzy match using rapidfuzz token_sort_ratio (guarded against short strings)

    Returns the matched Skill object or None if no match above threshold.
    """
    norm = _normalise(raw_skill)
    norm = CANONICAL_ALIASES.get(norm, norm)

    # 1. Exact match (fast path)
    if norm in skill_index:
        return skill_index[norm]

    # Never fuzzy-match short strings (length <= 3) to prevent mis-mapping (e.g. 'oracle' -> 'r')
    if len(norm) <= 3 or not skill_index:
        return None

    try:
        from rapidfuzz import fuzz
    except ImportError:
        return None

    # Filter candidates: never match against short candidates (length <= 3), and require length compatibility
    candidates = [
        k for k in skill_index.keys()
        if len(k) >= 4 and (min(len(norm), len(k)) / max(len(norm), len(k))) >= 0.65
    ]
    if not candidates:
        return None

    best_key = None
    best_score = 0.0
    for cand in candidates:
        score = fuzz.token_sort_ratio(norm, cand)
        if score > best_score and score >= threshold:
            best_score = score
            best_key = cand

    if best_key is not None:
        return skill_index[best_key]

    return None


async def match_skills_to_db(
    raw_skills: list[str],
    db: AsyncSession,
    threshold: float = MATCH_THRESHOLD,
) -> list[tuple[str, Optional[Skill], float]]:
    """
    Match a list of raw skill strings against the DB taxonomy.

    Returns list of (raw_skill, matched_Skill_or_None, confidence_score).
    """
    skill_index = await load_skill_index(db)
    results: list[tuple[str, Optional[Skill], float]] = []

    for raw in raw_skills:
        norm = _normalise(raw)
        norm = CANONICAL_ALIASES.get(norm, norm)

        # 1. Exact match
        if norm in skill_index:
            results.append((raw, skill_index[norm], 100.0))
            continue

        # Short strings <= 3 chars must NOT be fuzzy matched
        if len(norm) <= 3:
            results.append((raw, None, 0.0))
            continue

        try:
            from rapidfuzz import fuzz
            candidates = [
                k for k in skill_index.keys()
                if len(k) >= 4 and (min(len(norm), len(k)) / max(len(norm), len(k))) >= 0.65
            ]
            best_key = None
            best_score = 0.0
            for cand in candidates:
                score = fuzz.token_sort_ratio(norm, cand)
                if score > best_score and score >= threshold:
                    best_score = score
                    best_key = cand

            if best_key is not None:
                results.append((raw, skill_index[best_key], float(best_score)))
            else:
                results.append((raw, None, 0.0))
        except ImportError:
            results.append((raw, None, 0.0))

    return results


async def create_or_get_skill(db: AsyncSession, name: str) -> Skill:
    """
    Find a skill by normalised name, or create a new one if it doesn't exist.
    Used when the NLP pipeline finds a brand-new skill not in the taxonomy.
    """
    import re
    from datetime import datetime, timezone
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
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_skill)
    await db.flush()
    return new_skill
