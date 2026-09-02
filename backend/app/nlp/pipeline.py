"""
NLP Pipeline Orchestrator — connects all NLP steps end-to-end.

resume bytes  ->  parse text  ->  extract skills  ->  match taxonomy  ->  store StudentSkills

Also exposes a JD processing path:
jd text  ->  extract skills  ->  match taxonomy  ->  store JobSkills
"""

from __future__ import annotations
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.nlp.resume_parser import parse_resume
from app.nlp.skill_extractor import extract_skills_from_sections
from app.nlp.taxonomy_matcher import match_skills_to_db, create_or_get_skill
from app.models.skill import StudentSkill, JobSkill
from app.models.user import Student
from app.models.industry import Job

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Resume Pipeline
# ---------------------------------------------------------------------------

class ResumeParseResult:
    """Result object returned after processing a resume."""
    def __init__(
        self,
        raw_text: str,
        extracted_skills: list[str],
        matched_skills: list[dict],
        stored_count: int,
        errors: list[str],
    ):
        self.raw_text = raw_text
        self.extracted_skills = extracted_skills
        self.matched_skills = matched_skills
        self.stored_count = stored_count
        self.errors = errors


async def process_resume(
    db: AsyncSession,
    student_id: uuid.UUID,
    file_content: bytes,
    filename: str,
    overwrite_existing: bool = False,
) -> ResumeParseResult:
    """
    Full resume processing pipeline:
      1. Extract text from PDF/DOCX/TXT
      2. Extract skill mentions
      3. Fuzzy-match to Skill taxonomy
      4. Upsert StudentSkill rows
      5. Mark student.resume_parsed = True

    Args:
        db: Async database session
        student_id: UUID of the student
        file_content: Raw bytes of the uploaded file
        filename: Original filename (determines parser)
        overwrite_existing: If True, delete old resume-sourced skills first

    Returns:
        ResumeParseResult with statistics and any errors
    """
    errors: list[str] = []

    # Step 1: Parse text
    try:
        raw_text = parse_resume(file_content, filename)
    except ValueError as e:
        return ResumeParseResult("", [], [], 0, [str(e)])

    if not raw_text.strip():
        return ResumeParseResult(raw_text, [], [], 0, ["No text could be extracted from the file"])

    # Step 2: Extract skill strings
    extraction_result = extract_skills_from_sections(raw_text)
    raw_skills: list[str] = extraction_result["combined"]

    if not raw_skills:
        return ResumeParseResult(raw_text, [], [], 0, ["No skills detected in the resume"])

    # Step 3: Match to taxonomy
    matched = await match_skills_to_db(raw_skills, db)

    # Step 4: Store StudentSkill rows
    stored_count = 0
    matched_summary: list[dict] = []

    if overwrite_existing:
        # Remove old resume-sourced skills
        existing = await db.execute(
            select(StudentSkill).where(
                StudentSkill.student_id == student_id,
                StudentSkill.source == "resume",
            )
        )
        for ss in existing.scalars().all():
            await db.delete(ss)
        await db.flush()

    # Fetch existing to avoid duplicate key violations
    existing_result = await db.execute(
        select(StudentSkill.skill_id).where(
            StudentSkill.student_id == student_id,
            StudentSkill.source == "resume",
        )
    )
    existing_skill_ids: set[uuid.UUID] = set(existing_result.scalars().all())

    for raw, skill_obj, confidence in matched:
        if skill_obj is None:
            # Auto-create new skill entry
            try:
                skill_obj = await create_or_get_skill(db, raw)
                confidence = 60.0  # lower confidence for auto-created
            except Exception as e:
                errors.append(f"Could not create skill '{raw}': {e}")
                continue

        matched_summary.append({
            "raw": raw,
            "matched_to": skill_obj.name,
            "confidence": round(confidence, 1),
            "skill_id": str(skill_obj.id),
        })

        if skill_obj.id in existing_skill_ids:
            continue  # Already stored from a previous parse

        try:
            ss = StudentSkill(
                student_id=student_id,
                skill_id=skill_obj.id,
                confidence=round(min(confidence / 100.0, 1.0), 2),
                source="resume",
                evidence_text=f"Extracted from resume: '{raw}'",
            )
            db.add(ss)
            existing_skill_ids.add(skill_obj.id)
            stored_count += 1
        except Exception as e:
            errors.append(f"Could not store skill '{raw}': {e}")

    # Step 5: Mark resume as parsed
    student_result = await db.execute(select(Student).where(Student.id == student_id))
    student = student_result.scalar_one_or_none()
    if student:
        student.resume_parsed = True
        student.updated_at = datetime.now(timezone.utc)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        return ResumeParseResult(raw_text, raw_skills, matched_summary, 0, [f"DB commit failed: {e}"])

    logger.info(
        "Resume processed for student %s: %d skills extracted, %d stored",
        student_id, len(raw_skills), stored_count,
    )

    return ResumeParseResult(
        raw_text=raw_text,
        extracted_skills=raw_skills,
        matched_skills=matched_summary,
        stored_count=stored_count,
        errors=errors,
    )


# ---------------------------------------------------------------------------
# JD Pipeline
# ---------------------------------------------------------------------------

async def process_job_description(
    db: AsyncSession,
    job_id: uuid.UUID,
    jd_text: str,
) -> dict:
    """
    Parse a job description and store JobSkill rows.

    Returns summary dict with matched skill count.
    """
    from app.nlp.jd_parser import parse_jd

    parsed = parse_jd(jd_text)
    all_skills = parsed["all_skills"]
    required_skills = set(parsed["required_skills"])

    matched = await match_skills_to_db(all_skills, db)

    stored = 0
    for raw, skill_obj, confidence in matched:
        if skill_obj is None:
            continue

        importance = "required" if raw in required_skills else "preferred"

        # Check for existing
        existing = await db.execute(
            select(JobSkill).where(
                JobSkill.job_id == job_id,
                JobSkill.skill_id == skill_obj.id,
            )
        )
        if existing.scalar_one_or_none():
            continue

        js = JobSkill(
            job_id=job_id,
            skill_id=skill_obj.id,
            importance=importance,
            confidence=round(min(confidence / 100.0, 1.0), 2),
        )
        db.add(js)
        stored += 1

    await db.commit()
    return {
        "job_id": str(job_id),
        "raw_skills_found": len(all_skills),
        "skills_stored": stored,
        "min_cgpa": parsed["min_cgpa"],
        "min_experience_years": parsed["min_experience_years"],
    }
