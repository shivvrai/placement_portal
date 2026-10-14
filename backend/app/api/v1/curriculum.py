"""
Curriculum API — Curriculum intelligence, subjects with skill mappings,
coverage scores, and AI-powered skill mapping recommendations.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import RoleChecker
from app.models.user import User, Department
from app.models.academic import Subject
from app.models.skill import Skill, CurriculumSkill
from app.schemas.skill import SubjectWithSkillsResponse, CurriculumSkillResponse, SkillResponse, ApplySuggestionRequest
from app.services.curriculum_proposal_service import curriculum_proposal_service

router = APIRouter(prefix="/curriculum", tags=["Curriculum"])

_faculty_or_tpo = RoleChecker(["faculty", "hod", "tpo", "admin"])

# Domain suggestions mapping by subject keywords
DOMAIN_SUGGESTIONS = {
    "data structure": ["Advanced Graph Algorithms", "Competitive programming patterns", "Dynamic Programming"],
    "database": ["Window Functions & CTEs", "NoSQL fundamentals", "Query Optimization"],
    "operating system": ["Linux system calls", "Concurrency patterns", "Bash scripting"],
    "software engineering": ["Agile / Scrum practices", "Git workflow & CI/CD", "Design Patterns"],
    "network": ["REST API design", "Load balancing concepts", "Network Security basics"],
    "machine learning": ["Feature engineering techniques", "Model deployment with FastAPI", "scikit-learn best practices"],
    "big data": ["Apache Spark", "Real-time streaming with Kafka", "Cloud data lakes"],
    "web": ["React", "RESTful API development", "Authentication & JWT"],
    "cloud": ["AWS core services", "Infrastructure as Code (Terraform)", "Kubernetes fundamentals"],
    "deep learning": ["PyTorch", "Transformer architecture basics", "Fine-tuning pre-trained models"],
    "natural language": ["Large Language Model APIs", "Retrieval-Augmented Generation (RAG)", "spaCy for production NLP"],
    "distributed": ["Microservices design patterns", "Message queues", "gRPC for inter-service communication"],
    "security": ["JWT and OAuth 2.0", "Secure coding practices", "OWASP Top 10 mitigation"],
    "project": ["Containerize project with Docker", "Cloud platform deployment", "CI/CD automation"],
}


def _get_ai_suggestions_for_subject(subject_name: str, current_skill_names: set[str]) -> list[str]:
    sub_lower = subject_name.lower()
    matched_suggestions = []
    for keyword, suggestions in DOMAIN_SUGGESTIONS.items():
        if keyword in sub_lower:
            for sug in suggestions:
                if sug.lower() not in current_skill_names and sug not in matched_suggestions:
                    matched_suggestions.append(sug)
    if not matched_suggestions:
        fallbacks = ["Production-ready testing", "Git version control", "Performance profiling"]
        matched_suggestions = [f for f in fallbacks if f.lower() not in current_skill_names]
    return matched_suggestions[:4]


@router.get("/subjects", response_model=list[SubjectWithSkillsResponse], summary="List subjects with curriculum skill mappings")
async def list_subjects_with_skills(
    dept: Optional[str] = Query("CS", description="Department code, e.g. CS"),
    semester: Optional[int] = Query(None, ge=1, le=10, description="Semester number"),
    current_user: User = Depends(_faculty_or_tpo),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve subjects with mapped skills, coverage percentage, and AI suggestions."""
    dept_res = await db.execute(select(Department).where(Department.code == dept.upper()))
    department = dept_res.scalar_one_or_none()
    if not department:
        dept_res = await db.execute(select(Department).limit(1))
        department = dept_res.scalar_one_or_none()
        if not department:
            return []

    q = (
        select(Subject)
        .where(Subject.department_id == department.id)
        .options(
            selectinload(Subject.curriculum_skills).selectinload(CurriculumSkill.skill)
        )
        .order_by(Subject.semester_number, Subject.code)
    )
    if semester:
        q = q.where(Subject.semester_number == semester)

    subjects = (await db.execute(q)).scalars().all()

    response_list = []
    for sub in subjects:
        curr_skills = sub.curriculum_skills or []
        mapped_skill_responses = []
        mapped_skill_names = set()

        for cs in curr_skills:
            if cs.skill:
                mapped_skill_names.add(cs.skill.name.lower())
                mapped_skill_responses.append(
                    CurriculumSkillResponse(
                        id=cs.id,
                        skill=SkillResponse.model_validate(cs.skill),
                        coverage_level=cs.coverage_level or "intermediate",
                        mapping_source=cs.mapping_source or "syllabus",
                    )
                )

        mapped_count = len(curr_skills)
        coverage_pct = min(96.0, max(25.0, round(mapped_count * 16.5, 1))) if mapped_count > 0 else 30.0
        demand_score = min(98.0, max(60.0, round(70.0 + (mapped_count * 3.5), 1)))
        ai_sugs = _get_ai_suggestions_for_subject(sub.name, mapped_skill_names)

        response_list.append(
            SubjectWithSkillsResponse(
                id=sub.id,
                code=sub.code,
                name=sub.name,
                semester_number=sub.semester_number,
                credits=sub.credits,
                coverage_pct=coverage_pct,
                demand_score=demand_score,
                mapped_skills=mapped_skill_responses,
                ai_suggestions=ai_sugs,
            )
        )

    return response_list


@router.get("/subjects/{subject_id}/skills", response_model=list[CurriculumSkillResponse], summary="Get skills mapped to a subject")
async def get_subject_skills(
    subject_id: uuid.UUID,
    current_user: User = Depends(_faculty_or_tpo),
    db: AsyncSession = Depends(get_db),
):
    """Fetch all skills mapped to a specific subject."""
    q = (
        select(CurriculumSkill)
        .where(CurriculumSkill.subject_id == subject_id)
        .options(selectinload(CurriculumSkill.skill))
    )
    res = await db.execute(q)
    items = res.scalars().all()
    return items


@router.post("/subjects/{subject_id}/suggest-mappings", summary="Apply AI suggested skill mappings to a subject")
async def apply_suggested_mappings(
    subject_id: uuid.UUID,
    skill_name: Optional[str] = Query(None, description="Optional specific skill to apply. If omitted, applies all suggestions."),
    payload: Optional[ApplySuggestionRequest] = Body(default=None),
    current_user: User = Depends(_faculty_or_tpo),
    db: AsyncSession = Depends(get_db),
):
    """
    Applies recommended missing skills to the subject's curriculum skills mappings.
    If a specific skill_name is provided in query or JSON body, only that skill is applied.
    Otherwise, applies all remaining AI suggestions for the subject.
    """
    sub_res = await db.execute(
        select(Subject)
        .where(Subject.id == subject_id)
        .options(selectinload(Subject.curriculum_skills).selectinload(CurriculumSkill.skill))
    )
    subject = sub_res.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    existing_skill_names = {cs.skill.name.lower() for cs in subject.curriculum_skills if cs.skill}
    target_skill_name = payload.skill_name.strip() if (payload and payload.skill_name) else (skill_name.strip() if skill_name else None)

    if target_skill_name:
        if target_skill_name.lower() in existing_skill_names:
            return {
                "message": f"Skill '{target_skill_name}' is already mapped to {subject.name}.",
                "applied_skills": [],
                "subject_id": str(subject.id),
            }
        suggestions = [target_skill_name]
    else:
        suggestions = _get_ai_suggestions_for_subject(subject.name, existing_skill_names)
        if not suggestions:
            return {
                "message": "All recommended skills are already mapped to this subject.",
                "applied_skills": [],
                "subject_id": str(subject.id),
            }

    applied_names = []
    for sug_name in suggestions:
        norm_name = sug_name.lower().strip()
        skill_res = await db.execute(select(Skill).where(Skill.normalized_name == norm_name))
        skill = skill_res.scalar_one_or_none()
        if not skill:
            skill = Skill(
                name=sug_name,
                normalized_name=norm_name,
                category="tool" if any(t in norm_name for t in ["docker", "git", "aws", "terraform", "kubernetes", "fastapi"]) else "concept",
            )
            db.add(skill)
            await db.flush()

        curr_skill = CurriculumSkill(
            subject_id=subject.id,
            skill_id=skill.id,
            coverage_level="practiced",
            mapping_source="faculty_confirmed",
        )
        db.add(curr_skill)
        applied_names.append(sug_name)

    await db.commit()

    if target_skill_name:
        msg = f"Successfully added '{target_skill_name}' to {subject.name}"
    else:
        msg = f"Successfully mapped {len(applied_names)} skills to {subject.name}"

    return {
        "message": msg,
        "applied_skills": applied_names,
        "subject_id": str(subject.id),
    }

@router.post("/subjects/{subject_id}/generate-proposal")
async def generate_bos_proposal(
    subject_id: uuid.UUID,
    current_user: User = Depends(_faculty_or_tpo),
    db: AsyncSession = Depends(get_db),
):
    """
    Generates an AI-powered Board of Studies syllabus modernization proposal
    for the specified subject.
    """
    try:
        proposal = await curriculum_proposal_service.generate(subject_id, db)
        return proposal
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate proposal: {e}")


# ─── V2: Department Gap Analysis ─────────────────────────────────────

@router.get("/gap-analysis/{dept}", summary="Run department-wide gap analysis")
async def get_gap_analysis(
    dept: str,
    current_user: User = Depends(_faculty_or_tpo),
    db: AsyncSession = Depends(get_db),
):
    """Analyze the gap between curriculum skills and industry demands for a department."""
    try:
        result = await curriculum_proposal_service.run_full_gap_analysis(dept, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ─── V2: Proposal CRUD ──────────────────────────────────────────────

from pydantic import BaseModel as PydanticBase, Field as PydanticField


class CreateProposalRequest(PydanticBase):
    department_code: str = PydanticField(default="CS")
    academic_year: str = PydanticField(default="2026-27")


class UpdateProposalStatusRequest(PydanticBase):
    status: str  # approved | rejected
    comments: Optional[str] = None


@router.post("/proposals", summary="Generate a full BoS curriculum proposal")
async def create_proposal(
    data: CreateProposalRequest,
    current_user: User = Depends(_faculty_or_tpo),
    db: AsyncSession = Depends(get_db),
):
    """Generate an AI-powered full curriculum proposal for the department."""
    try:
        result = await curriculum_proposal_service.generate_full_proposal(
            department_code=data.department_code,
            academic_year=data.academic_year,
            faculty_id=current_user.id,
            db=db,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/proposals", summary="List all proposals for faculty's department")
async def list_proposals(
    current_user: User = Depends(_faculty_or_tpo),
    db: AsyncSession = Depends(get_db),
):
    """List all curriculum proposals."""
    from app.models.curriculum_proposal import CurriculumProposal
    result = await db.execute(
        select(CurriculumProposal).order_by(CurriculumProposal.created_at.desc())
    )
    proposals = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "department_code": p.department_code,
            "academic_year": p.academic_year,
            "status": p.status,
            "impact_projection": p.impact_projection,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in proposals
    ]


@router.get("/proposals/{proposal_id}", summary="Get proposal detail")
async def get_proposal(
    proposal_id: uuid.UUID,
    current_user: User = Depends(_faculty_or_tpo),
    db: AsyncSession = Depends(get_db),
):
    """Get full detail of a curriculum proposal."""
    from app.models.curriculum_proposal import CurriculumProposal
    result = await db.execute(
        select(CurriculumProposal).where(CurriculumProposal.id == proposal_id)
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    return {
        "id": str(p.id),
        "department_code": p.department_code,
        "academic_year": p.academic_year,
        "status": p.status,
        "gap_analysis": p.gap_analysis,
        "proposed_subjects": p.proposed_subjects,
        "impact_projection": p.impact_projection,
        "hod_comments": p.hod_comments,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "reviewed_at": p.reviewed_at.isoformat() if p.reviewed_at else None,
    }


@router.patch("/proposals/{proposal_id}/status", summary="HOD approves or rejects a proposal")
async def update_proposal_status(
    proposal_id: uuid.UUID,
    data: UpdateProposalStatusRequest,
    current_user: User = Depends(RoleChecker(["hod", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """HOD approves or rejects a curriculum proposal."""
    from app.models.curriculum_proposal import CurriculumProposal
    from datetime import datetime, timezone
    result = await db.execute(
        select(CurriculumProposal).where(CurriculumProposal.id == proposal_id)
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    if data.status not in ("approved", "rejected"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be 'approved' or 'rejected'")
    proposal.status = data.status
    proposal.hod_comments = data.comments
    proposal.reviewed_by = current_user.id
    proposal.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    return {"message": f"Proposal {data.status}", "id": str(proposal.id)}


@router.get("/proposals/{proposal_id}/download", summary="Download proposal as .docx")
async def download_proposal(
    proposal_id: uuid.UUID,
    current_user: User = Depends(_faculty_or_tpo),
    db: AsyncSession = Depends(get_db),
):
    """Download the curriculum proposal as a formatted .docx file."""
    from fastapi.responses import Response
    try:
        docx_bytes = await curriculum_proposal_service.export_proposal_to_word(proposal_id, db)
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=BoS_Proposal_{proposal_id}.docx"},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/proposals/{proposal_id}/submit", summary="Submit proposal to HOD for review")
async def submit_proposal(
    proposal_id: uuid.UUID,
    current_user: User = Depends(_faculty_or_tpo),
    db: AsyncSession = Depends(get_db),
):
    """Faculty submits their proposal for HOD review."""
    try:
        await curriculum_proposal_service.submit_proposal_for_review(proposal_id, current_user.id, db)
        return {"message": "Proposal submitted for HOD review", "id": str(proposal_id)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/coverage-heatmap/{dept}", summary="Subject × skill demand heatmap data")
async def get_coverage_heatmap(
    dept: str,
    current_user: User = Depends(_faculty_or_tpo),
    db: AsyncSession = Depends(get_db),
):
    """Get heatmap data: rows=subjects, cols=top industry skills, cells=0/1 coverage."""
    return await curriculum_proposal_service.get_coverage_heatmap(dept, db)

