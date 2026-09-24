import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.skill import StudentSkill
from app.models.placement import PlacementDrive
from app.models.user import Student
from app.models.industry import Job, JobSkill, Company
from app.ml.matcher import predict_match_score

class WhatIfService:
    async def simulate_skill_addition(self, db: AsyncSession, student_id: uuid.UUID, skill_to_add: str, drive_id: uuid.UUID) -> dict:
        skill_result = await db.execute(
            select(StudentSkill)
            .where(StudentSkill.student_id == student_id)
            .options(selectinload(StudentSkill.skill))
        )
        student_skills = {
            ss.skill.normalized_name: float(ss.confidence)
            for ss in skill_result.scalars().all()
        }

        student = await db.get(Student, student_id, options=[selectinload(Student.department)])
        student_cgpa = float(student.cgpa) if student and student.cgpa else None
        student_dept = student.department.code if student and student.department else None

        drive = await db.get(PlacementDrive, drive_id)
        job_result = await db.execute(
            select(Job)
            .where(Job.company_id == drive.company_id, Job.is_active == True)
            .options(selectinload(Job.job_skills).selectinload(JobSkill.skill))
        )
        jobs = job_result.scalars().all()
        
        current_score = 0.0
        simulated_score = 0.0
        
        simulated_skills = dict(student_skills)
        simulated_skills[skill_to_add.lower()] = 0.8
        
        for job in jobs:
            job_skills = {js.skill.normalized_name: js.importance for js in job.job_skills}
            job_min_cgpa = float(job.min_cgpa) if job.min_cgpa else (float(drive.min_cgpa) if drive.min_cgpa else None)
            eligible_depts = job.eligible_departments or drive.eligible_departments
            
            c_score = predict_match_score(student_skills, job_skills, student_cgpa, job_min_cgpa, student_dept, eligible_depts)
            if c_score > current_score:
                current_score = c_score
                
            s_score = predict_match_score(simulated_skills, job_skills, student_cgpa, job_min_cgpa, student_dept, eligible_depts)
            if s_score > simulated_score:
                simulated_score = s_score

        return {
            "current_score": current_score,
            "simulated_score": simulated_score,
            "delta": round(simulated_score - current_score, 1),
            "skill_added": skill_to_add
        }

    async def simulate_cgpa_improvement(self, db: AsyncSession, student_id: uuid.UUID, target_cgpa: float, drive_id: uuid.UUID) -> dict:
        skill_result = await db.execute(
            select(StudentSkill)
            .where(StudentSkill.student_id == student_id)
            .options(selectinload(StudentSkill.skill))
        )
        student_skills = {
            ss.skill.normalized_name: float(ss.confidence)
            for ss in skill_result.scalars().all()
        }

        student = await db.get(Student, student_id, options=[selectinload(Student.department)])
        student_cgpa = float(student.cgpa) if student and student.cgpa else None
        student_dept = student.department.code if student and student.department else None

        drive = await db.get(PlacementDrive, drive_id)
        job_result = await db.execute(
            select(Job)
            .where(Job.company_id == drive.company_id, Job.is_active == True)
            .options(selectinload(Job.job_skills).selectinload(JobSkill.skill))
        )
        jobs = job_result.scalars().all()
        
        current_score = 0.0
        simulated_score = 0.0
        
        for job in jobs:
            job_skills = {js.skill.normalized_name: js.importance for js in job.job_skills}
            job_min_cgpa = float(job.min_cgpa) if job.min_cgpa else (float(drive.min_cgpa) if drive.min_cgpa else None)
            eligible_depts = job.eligible_departments or drive.eligible_departments
            
            c_score = predict_match_score(student_skills, job_skills, student_cgpa, job_min_cgpa, student_dept, eligible_depts)
            if c_score > current_score:
                current_score = c_score
                
            s_score = predict_match_score(student_skills, job_skills, target_cgpa, job_min_cgpa, student_dept, eligible_depts)
            if s_score > simulated_score:
                simulated_score = s_score

        return {
            "current_score": current_score,
            "simulated_score": simulated_score,
            "delta": round(simulated_score - current_score, 1),
            "current_cgpa": student_cgpa,
            "target_cgpa": target_cgpa
        }

what_if_service = WhatIfService()
