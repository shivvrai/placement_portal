"""
Matching API — skill gaps and job-student matching.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.skill import SkillGapResponse
from app.schemas.matching import JobMatchResponse
from app.services import matching_service, student_service

router = APIRouter(tags=["Matching & Intelligence"])

_authenticated = get_current_user


@router.get("/gaps/me", response_model=SkillGapResponse, summary="My skill gap for target role")
async def get_my_skill_gap(
    target_role: str = Query("Data Analyst", description="Target role for gap analysis"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compute skill gap between the current student and a target role."""
    return await matching_service.compute_skill_gap(db, current_user.id, target_role)


@router.get("/gaps/students/{student_id}", response_model=SkillGapResponse, summary="Student skill gap (TPO)")
async def get_student_skill_gap(
    student_id: uuid.UUID,
    target_role: str = Query("Data Analyst"),
    current_user: User = Depends(RoleChecker(["tpo", "faculty", "hod", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    return await matching_service.compute_skill_gap(db, student_id, target_role)


@router.get("/matching/students/{student_id}/gap", response_model=SkillGapResponse, summary="Student skill gap (ML)")
@router.get("/students/{student_id}/gap", response_model=SkillGapResponse, include_in_schema=False)
async def get_skill_gap_for_student(
    student_id: uuid.UUID,
    target_role: str = Query("Software Engineer", description="Target role for gap analysis"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await student_service.get_student_by_user_id(db, student_id)
    return await matching_service.compute_skill_gap(db, student_id, target_role)



@router.get("/matching/me", response_model=list[JobMatchResponse], summary="My job matches")
async def get_my_job_matches(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return ranked list of job matches for the current student."""
    student = await student_service.get_student_by_user_id(db, current_user.id)
    return await matching_service.compute_job_matches(
        db,
        student_id=current_user.id,
        student_cgpa=float(student.cgpa) if student.cgpa else None,
        student_dept_code=student.department.code if student.department else None,
        limit=limit,
    )


@router.get("/matching/students/{student_id}", response_model=list[JobMatchResponse])
async def get_student_job_matches(
    student_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(RoleChecker(["tpo", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    student = await student_service.get_student_full(db, student_id)
    return await matching_service.compute_job_matches(
        db,
        student_id=student_id,
        student_cgpa=float(student.cgpa) if student.cgpa else None,
        student_dept_code=student.department.code if student.department else None,
        limit=limit,
    )


@router.get("/matching/students/{student_id}/jobs", response_model=list[JobMatchResponse], summary="Student job matches (ML-ranked)")
@router.get("/students/{student_id}/jobs", response_model=list[JobMatchResponse], include_in_schema=False)
async def get_student_job_matches_jobs(
    student_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    role: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    minMatch: Optional[float] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    student = await student_service.get_student_full(db, student_id)
    matches = await matching_service.compute_job_matches(
        db=db,
        student_id=student_id,
        student_cgpa=float(student.cgpa) if student.cgpa else None,
        student_dept_code=student.department.code if student.department else None,
        limit=limit,
    )
    return matches


from pydantic import BaseModel
from typing import Any
from app.services.what_if_service import what_if_service
from app.services.benchmarking_service import benchmarking_service
from app.models.placement import PlacementDrive
from app.models.industry import Job, JobSkill
from app.models.skill import StudentSkill
from app.models.user import Student
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.ml.matcher import predict_match_score, compute_breakdown
from app.ml.gap_engine import compute_gap_scores

class WhatIfRequest(BaseModel):
    skill_to_add: Optional[str] = None
    target_cgpa: Optional[float] = None
    drive_id: uuid.UUID

@router.get("/drives/{drive_id}")
async def get_drive_match(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    student = await db.get(Student, current_user.id, options=[selectinload(Student.department)])
    student_cgpa = float(student.cgpa) if student and student.cgpa else None
    student_dept = student.department.code if student and student.department else None
    
    skill_result = await db.execute(
        select(StudentSkill).where(StudentSkill.student_id == current_user.id).options(selectinload(StudentSkill.skill))
    )
    student_skills = {ss.skill.normalized_name: float(ss.confidence) for ss in skill_result.scalars().all()}
    
    drive = await db.get(PlacementDrive, drive_id)
    job_result = await db.execute(
        select(Job).where(Job.company_id == drive.company_id, Job.is_active == True).options(selectinload(Job.job_skills).selectinload(JobSkill.skill))
    )
    jobs = job_result.scalars().all()
    
    best_score = 0
    best_breakdown = None
    best_job = None
    
    for job in jobs:
        job_skills = {js.skill.normalized_name: js.importance for js in job.job_skills}
        min_cgpa = float(job.min_cgpa) if job.min_cgpa else (float(drive.min_cgpa) if drive.min_cgpa else None)
        eligible_depts = job.eligible_departments or drive.eligible_departments
        
        score = predict_match_score(student_skills, job_skills, student_cgpa, min_cgpa, student_dept, eligible_depts)
        if score >= best_score:
            best_score = score
            best_breakdown = compute_breakdown(student_skills, job_skills, student_cgpa, min_cgpa, student_dept, eligible_depts)
            best_job = job
            
    from app.models.placement import Application
    app_cnt = (await db.execute(select(func.count(Application.id)).where(Application.drive_id == drive_id))).scalar() or 0
            
    return {
        "drive_id": drive_id,
        "overall_score": best_score,
        "skill_score": best_breakdown.skills_score if best_breakdown else 0,
        "cgpa_score": best_breakdown.academic_score if best_breakdown else 0,
        "dept_eligible": (best_breakdown.academic_score > 0) if best_breakdown else False,
        "skill_breakdown": [d.dict() for d in best_breakdown.skill_details] if best_breakdown else [],
        "recommendation": best_breakdown.recommendation if best_breakdown else "",
        "rank_in_applicants": 1,
        "total_applicants": app_cnt
    }

@router.get("/my-top-drives")
async def get_my_top_drives(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    student = await db.get(Student, current_user.id, options=[selectinload(Student.department)])
    student_cgpa = float(student.cgpa) if student and student.cgpa else None
    student_dept = student.department.code if student and student.department else None
    
    skill_result = await db.execute(
        select(StudentSkill).where(StudentSkill.student_id == current_user.id).options(selectinload(StudentSkill.skill))
    )
    student_skills = {ss.skill.normalized_name: float(ss.confidence) for ss in skill_result.scalars().all()}
    
    drives = (await db.execute(select(PlacementDrive).where(PlacementDrive.status.in_(["open", "upcoming"])).options(selectinload(PlacementDrive.company)))).scalars().all()
    
    results = []
    for drive in drives:
        if not drive.company_id: continue
        job_result = await db.execute(
            select(Job).where(Job.company_id == drive.company_id, Job.is_active == True).options(selectinload(Job.job_skills).selectinload(JobSkill.skill))
        )
        jobs = job_result.scalars().all()
        
        best_score = 0
        for job in jobs:
            job_skills = {js.skill.normalized_name: js.importance for js in job.job_skills}
            min_cgpa = float(job.min_cgpa) if job.min_cgpa else (float(drive.min_cgpa) if drive.min_cgpa else None)
            eligible_depts = job.eligible_departments or drive.eligible_departments
            
            score = predict_match_score(student_skills, job_skills, student_cgpa, min_cgpa, student_dept, eligible_depts)
            if score > best_score:
                best_score = score
                
        results.append({
            "drive_id": drive.id,
            "title": drive.title,
            "company_name": drive.company.name if drive.company else "Unknown",
            "match_score": best_score,
            "salary_ctc": float(drive.salary_ctc) if drive.salary_ctc else None
        })
        
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:10]

@router.get("/skill-gap/{drive_id}")
async def get_drive_skill_gap(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    skill_result = await db.execute(
        select(StudentSkill).where(StudentSkill.student_id == current_user.id).options(selectinload(StudentSkill.skill))
    )
    student_skills = {ss.skill.normalized_name: float(ss.confidence) for ss in skill_result.scalars().all()}
    
    drive = await db.get(PlacementDrive, drive_id)
    job_result = await db.execute(
        select(Job).where(Job.company_id == drive.company_id, Job.is_active == True).options(selectinload(Job.job_skills).selectinload(JobSkill.skill))
    )
    jobs = job_result.scalars().all()
    
    target_skills = {}
    for job in jobs:
        for js in job.job_skills:
            imp = 0.8 if js.importance == "required" else 0.5
            if target_skills.get(js.skill.normalized_name, 0) < imp:
                target_skills[js.skill.normalized_name] = imp
                
    gaps = []
    for skill, req in target_skills.items():
        stud_conf = student_skills.get(skill, 0.0)
        if stud_conf < req:
            gaps.append({
                "skill": skill,
                "required_level": req,
                "student_level": stud_conf,
                "gap": req - stud_conf,
                "status": "missing" if stud_conf == 0 else "needs_improvement"
            })
            
    return {"drive_id": drive_id, "gaps": gaps}

@router.get("/job-fit/{job_id}")
async def get_job_fit(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    student = await db.get(Student, current_user.id, options=[selectinload(Student.department)])
    student_cgpa = float(student.cgpa) if student and student.cgpa else None
    student_dept = student.department.code if student and student.department else None
    
    skill_result = await db.execute(
        select(StudentSkill).where(StudentSkill.student_id == current_user.id).options(selectinload(StudentSkill.skill))
    )
    student_skills = {ss.skill.normalized_name: float(ss.confidence) for ss in skill_result.scalars().all()}
    
    job = await db.get(Job, job_id, options=[selectinload(Job.job_skills).selectinload(JobSkill.skill)])
    job_skills = {js.skill.normalized_name: js.importance for js in job.job_skills}
    min_cgpa = float(job.min_cgpa) if job.min_cgpa else None
    eligible_depts = job.eligible_departments
    
    score = predict_match_score(student_skills, job_skills, student_cgpa, min_cgpa, student_dept, eligible_depts)
    breakdown = compute_breakdown(student_skills, job_skills, student_cgpa, min_cgpa, student_dept, eligible_depts)
    
    return {
        "job_id": job_id,
        "score": score,
        "breakdown": breakdown.dict() if breakdown else {}
    }

@router.get("/rank-cohort")
async def get_rank_cohort(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return {
        "student_avg_score": 75.0,
        "dept_median": 65.0,
        "percentile": 80,
        "rank": 10,
        "total_in_dept": 150
    }

@router.post("/what-if")
async def simulate_what_if(
    req: WhatIfRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if req.skill_to_add:
        return await what_if_service.simulate_skill_addition(db, current_user.id, req.skill_to_add, req.drive_id)
    elif req.target_cgpa:
        return await what_if_service.simulate_cgpa_improvement(db, current_user.id, req.target_cgpa, req.drive_id)
    return {}

@router.get("/benchmark")
async def get_benchmark(
    scope: str = "department",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await benchmarking_service.get_cohort_stats(db, current_user.id, scope)

@router.get("/leaderboard/{dept}")
async def get_leaderboard(
    dept: str,
    metric: str = "cgpa",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await benchmarking_service.get_department_leaderboard(db, dept, metric, current_user.id)

@router.get("/readiness")
async def get_readiness(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await benchmarking_service.get_readiness_score(db, current_user.id)
