"""
Matching Service — connects ML gap engine + ML matcher to the database layer.

This replaces the Phase 2 rule-based version. Key changes:
  - compute_skill_gap() now uses ml.gap_engine (semantic embedding boost)
  - compute_job_matches() now uses ml.matcher (GBT model or heuristic fallback)
"""

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.skill import StudentSkill, Skill
from app.models.industry import Job, JobSkill
from app.models.user import Student
from app.models.portfolio import Project

from app.ml.gap_engine import compute_gap_scores
from app.ml.matcher import predict_match_score, compute_breakdown

from app.schemas.skill import SkillGapItem, SkillGapResponse
from app.schemas.matching import JobMatchResponse



# ---------------------------------------------------------------------------
# Skill Gap (ML-powered)
# ---------------------------------------------------------------------------

async def compute_skill_gap(
    db: AsyncSession,
    student_id: uuid.UUID,
    target_role: str,
) -> SkillGapResponse:
    """
    Compute ML-enhanced skill gap between student's skills and a target role.
    Uses semantic embeddings to detect partial coverage from related skills.
    """
    # Fetch student skills from DB
    result = await db.execute(
        select(StudentSkill)
        .where(StudentSkill.student_id == student_id)
        .options(selectinload(StudentSkill.skill))
    )
    student_skills = {
        ss.skill.normalized_name: float(ss.confidence)
        for ss in result.scalars().all()
    }

    # Run ML gap engine
    gap_result = compute_gap_scores(
        student_skills=student_skills,
        target_role=target_role,
        use_embeddings=True,
    )

    # Map to Pydantic schema
    gaps = [
        SkillGapItem(
            skill_name=g["skill_name"],
            category=_infer_category(g["skill_name"]),
            current_score=g["current_score"],
            required_score=g["required_score"],
            gap=g["gap"],
            severity=g["severity"],
        )
        for g in gap_result["gaps"]
    ]

    return SkillGapResponse(
        student_id=student_id,
        target_role=gap_result["target_role"],
        overall_score=gap_result["overall_score"],
        gaps=gaps,
    )


def _infer_category(skill_name: str) -> str:
    lang = {"python", "javascript", "java", "sql", "typescript", "r", "scala", "go", "rust", "c++", "c#", "php", "swift", "kotlin"}
    tools = {"docker", "kubernetes", "git", "linux", "ci/cd", "aws", "gcp", "azure", "terraform", "nginx"}
    ml = {"machine learning", "deep learning", "statistics", "nlp", "computer vision", "tensorflow", "pytorch", "scikit-learn", "xgboost"}
    web = {"react", "angular", "vue", "node.js", "django", "flask", "fastapi", "spring", "html", "css", "graphql", "rest api"}
    cs = {"data structures", "algorithms", "system design", "os", "computer networks", "oop", "design patterns"}
    data = {"pandas", "numpy", "spark", "kafka", "airflow", "tableau", "power bi", "excel", "bigquery", "data analysis", "data engineering"}

    sn = skill_name.lower()
    if sn in lang:        return "language"
    if sn in tools:       return "tools"
    if sn in ml:          return "ml_ai"
    if sn in web:         return "web"
    if sn in cs:          return "cs_fundamentals"
    if sn in data:        return "data"
    return "other"


# ---------------------------------------------------------------------------
# Job Matching (ML-powered)
# ---------------------------------------------------------------------------

async def compute_job_matches(
    db: AsyncSession,
    student_id: uuid.UUID,
    student_cgpa: Optional[float],
    student_dept_code: Optional[str],
    limit: int = 20,
) -> list[JobMatchResponse]:
    """
    Score and rank all active jobs for a student using the ML matcher.
    Falls back to heuristic if no trained model is present.
    """
    # Load student skills
    skill_result = await db.execute(
        select(StudentSkill)
        .where(StudentSkill.student_id == student_id)
        .options(selectinload(StudentSkill.skill))
    )
    student_skills = {
        ss.skill.normalized_name: float(ss.confidence)
        for ss in skill_result.scalars().all()
    }

    # Load student projects for experience bonus
    proj_result = await db.execute(
        select(Project).where(Project.student_id == student_id)
    )
    student_projects = [
        {
            "title": p.title,
            "technologies": p.technologies or [],
            "description": p.description or "",
        }
        for p in proj_result.scalars().all()
    ]

    # Load active jobs with their skills
    job_result = await db.execute(
        select(Job)
        .where(Job.is_active == True)  # noqa: E712
        .options(
            selectinload(Job.company),
            selectinload(Job.job_skills).selectinload(JobSkill.skill),
        )
        .limit(200)
    )
    jobs = job_result.scalars().all()

    matches: list[JobMatchResponse] = []

    for job in jobs:
        job_skills_dict = {
            js.skill.normalized_name: js.importance
            for js in job.job_skills
        }
        eligible_depts = job.eligible_departments or []

        # ML match score
        match_score = predict_match_score(
            student_skills=student_skills,
            job_skills=job_skills_dict,
            student_cgpa=student_cgpa,
            job_min_cgpa=float(job.min_cgpa) if job.min_cgpa else None,
            student_dept=student_dept_code,
            eligible_depts=eligible_depts or None,
        )

        # Compute diagnostic breakdown
        breakdown = compute_breakdown(
            student_skills=student_skills,
            job_skills=job_skills_dict,
            student_cgpa=student_cgpa,
            job_min_cgpa=float(job.min_cgpa) if job.min_cgpa else None,
            student_dept=student_dept_code,
            eligible_depts=eligible_depts or None,
            student_projects=student_projects,
        )

        # Eligibility check (hard constraint)
        eligible = True
        if job.min_cgpa and student_cgpa and student_cgpa < float(job.min_cgpa):
            eligible = False
        if eligible_depts and student_dept_code and student_dept_code not in eligible_depts:
            eligible = False

        # Split skills into matched / missing for UI display
        matched_skills = [s for s in job_skills_dict if student_skills.get(s, 0) >= 0.5]
        missing_skills = [s for s in job_skills_dict if student_skills.get(s, 0) < 0.5]

        # Simple skill-only match % for display
        total = len(job_skills_dict)
        skill_match_pct = round(len(matched_skills) / max(total, 1) * 100, 1)

        matches.append(JobMatchResponse(
            job_id=job.id,
            title=job.title,
            company_name=job.company.name if job.company else "Unknown",
            location=job.location,
            salary_ctc_min=float(job.salary_min) if job.salary_min else None,
            salary_ctc_max=float(job.salary_max) if job.salary_max else None,
            role_category=job.role_category,
            match_score=match_score,
            skill_match_pct=skill_match_pct,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            eligible=eligible,
            breakdown=breakdown,
        ))

    # Sort by match score, penalise ineligible
    matches.sort(key=lambda m: (m.eligible, m.match_score), reverse=True)
    return matches[:limit]
