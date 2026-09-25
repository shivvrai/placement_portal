"""
Shortlisting Service
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.placement import Application, PlacementDrive
from app.models.user import Student
from app.core.audit import record_audit_event
from app.api.v1.notifications import create_notification
from app.ml.matcher import predict_match_score


class ShortlistingCriteria(BaseModel):
    min_cgpa: Optional[float] = None
    max_backlogs: Optional[int] = None
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    min_skill_match_pct: Optional[float] = None
    eligible_departments: list[str] = []
    min_projects: Optional[int] = None
    has_resume: Optional[bool] = None
    min_match_score: Optional[float] = None


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ShortlistingService:

    async def _evaluate_applicant(self, app, criteria, drive):
        student = app.student
        pass_reasons = []
        fail_reasons = []

        if criteria.min_cgpa is not None:
            cgpa = float(student.cgpa) if student.cgpa else 0.0
            if cgpa < criteria.min_cgpa:
                fail_reasons.append(f'CGPA {cgpa:.2f} < required {criteria.min_cgpa}')
            else:
                pass_reasons.append(f'CGPA {cgpa:.2f}')

        if criteria.max_backlogs is not None:
            backlogs = 0
            meta = getattr(student, 'extra_metadata', None) or {}
            if isinstance(meta, dict):
                backlogs = meta.get('backlogs_count', 0)
            if backlogs > criteria.max_backlogs:
                fail_reasons.append(f'Backlogs {backlogs} > max {criteria.max_backlogs}')
            else:
                pass_reasons.append(f'Backlogs {backlogs}')

        if criteria.eligible_departments:
            student_dept = student.department.code if student.department else None
            if student_dept and student_dept.upper() not in [d.upper() for d in criteria.eligible_departments]:
                fail_reasons.append(f'Dept {student_dept} not eligible')
            else:
                pass_reasons.append(f'Dept eligible')

        student_skill_names = [s.skill.name.lower() for s in (student.skills or []) if s.skill]
        if criteria.required_skills:
            missing = [sk for sk in criteria.required_skills if sk.lower() not in student_skill_names]
            if missing:
                missing_str = ", ".join(missing)
                fail_reasons.append(f"Missing skills: {missing_str}")
            else:
                pass_reasons.append("Has all required skills")

        if criteria.min_skill_match_pct is not None and criteria.required_skills:
            matched = sum(1 for sk in criteria.required_skills if sk.lower() in student_skill_names)
            pct = (matched / len(criteria.required_skills)) * 100.0
            if pct < criteria.min_skill_match_pct:
                fail_reasons.append(f'Skill match {pct:.1f}% < {criteria.min_skill_match_pct}%')
            else:
                pass_reasons.append(f'Skill match {pct:.1f}%')

        if criteria.has_resume:
            if not student.resume_url:
                fail_reasons.append('No resume uploaded')
            else:
                pass_reasons.append('Resume uploaded')

        if criteria.min_projects is not None:
            cnt = len(student.projects) if student.projects else 0
            if cnt < criteria.min_projects:
                fail_reasons.append(f'Projects {cnt} < {criteria.min_projects}')
            else:
                pass_reasons.append(f'{cnt} projects')

        if criteria.min_match_score is not None:
            skills_dict = {ss.skill.name.lower(): float(ss.confidence or 0.7) for ss in (student.skills or []) if ss.skill}
            job_skills = {sk: 'required' for sk in criteria.required_skills}
            for sk in criteria.preferred_skills:
                job_skills[sk] = 'preferred'
            score = predict_match_score(
                student_skills=skills_dict, job_skills=job_skills,
                student_cgpa=float(student.cgpa) if student.cgpa else None,
                job_min_cgpa=float(drive.min_cgpa) if drive.min_cgpa else None,
                student_dept=student.department.code if student.department else None,
                eligible_depts=drive.eligible_departments or [],
            )
            if score < criteria.min_match_score:
                fail_reasons.append(f'ML score {score:.1f} < {criteria.min_match_score}')
            else:
                pass_reasons.append(f'ML score {score:.1f}')

        return len(fail_reasons) == 0, pass_reasons, fail_reasons

    async def run_auto_shortlist(self, drive_id, criteria, tpo_user_id, db):
        from app.models.skill import StudentSkill
        drive_result = await db.execute(select(PlacementDrive).where(PlacementDrive.id == drive_id))
        drive = drive_result.scalar_one_or_none()
        if not drive:
            raise ValueError(f'Drive {drive_id} not found')

        stmt = (select(Application).where(Application.drive_id == drive_id).where(Application.status == 'applied')
            .options(selectinload(Application.student).selectinload(Student.department),
                     selectinload(Application.student).selectinload(Student.skills).selectinload(StudentSkill.skill),
                     selectinload(Application.student).selectinload(Student.projects)))
        result = await db.execute(stmt)
        applications = result.scalars().all()

        shortlisted, skipped = [], []
        for app in applications:
            passed, p, f = await self._evaluate_applicant(app, criteria, drive)
            app.extra_metadata = {**(app.extra_metadata or {}), 'shortlisting': {'passed': passed, 'pass_reasons': p, 'fail_reasons': f, 'criteria_used': criteria.model_dump()}}
            if passed:
                app.status = 'shortlisted'
                app.updated_at = utcnow()
                shortlisted.append(app)
            else:
                skipped.append(app)

        await db.flush()
        await record_audit_event(db=db, actor_id=tpo_user_id, event_type='SHORTLIST_GENERATED',
            resource_type='PlacementDrive', resource_id=str(drive_id),
            details={'total_evaluated': len(applications), 'shortlisted': len(shortlisted), 'criteria': criteria.model_dump()})

        company_name = drive.company.name if drive.company else drive.title
        for app in shortlisted:
            await create_notification(db=db, user_id=app.student_id,
                title=f'Shortlisted: {company_name}',
                message=f'You have been shortlisted for {drive.title} at {company_name}.',
                type='success', link='/student/drives')
        await db.commit()
        return {'total_evaluated': len(applications), 'shortlisted': len(shortlisted), 'skipped': len(skipped), 'criteria_used': criteria.model_dump()}

    async def dry_run(self, drive_id, criteria, db):
        from app.models.skill import StudentSkill
        drive_result = await db.execute(select(PlacementDrive).where(PlacementDrive.id == drive_id))
        drive = drive_result.scalar_one_or_none()
        if not drive:
            raise ValueError(f'Drive {drive_id} not found')

        stmt = (select(Application).where(Application.drive_id == drive_id).where(Application.status == 'applied')
            .options(selectinload(Application.student).selectinload(Student.department),
                     selectinload(Application.student).selectinload(Student.skills).selectinload(StudentSkill.skill),
                     selectinload(Application.student).selectinload(Student.projects),
                     selectinload(Application.student).selectinload(Student.user)))
        result = await db.execute(stmt)
        applications = result.scalars().all()

        would_shortlist, would_skip = [], []
        for app in applications:
            passed, p, f = await self._evaluate_applicant(app, criteria, drive)
            s = app.student
            entry = {'application_id': str(app.id), 'student_id': str(app.student_id),
                     'first_name': s.user.first_name if s.user else '', 'last_name': s.user.last_name if s.user else '',
                     'cgpa': float(s.cgpa) if s.cgpa else None, 'department': s.department.code if s.department else None,
                     'pass_reasons': p, 'fail_reasons': f}
            (would_shortlist if passed else would_skip).append(entry)

        return {'total_evaluated': len(applications), 'would_shortlist': len(would_shortlist), 'would_skip': len(would_skip),
                'criteria_used': criteria.model_dump(), 'preview_pass': would_shortlist[:20], 'preview_fail': would_skip[:20]}

    async def manual_override(self, application_id, new_status, reason, tpo_user_id, db):
        result = await db.execute(select(Application).where(Application.id == application_id))
        app = result.scalar_one_or_none()
        if not app:
            raise ValueError(f'Application {application_id} not found')
        old_status = app.status
        app.status = new_status
        app.updated_at = utcnow()
        app.extra_metadata = {**(app.extra_metadata or {}), 'manual_override': {'by': str(tpo_user_id), 'old_status': old_status, 'new_status': new_status, 'reason': reason}}
        await db.flush()
        await record_audit_event(db=db, actor_id=tpo_user_id, event_type='APPLICATION_STATUS_CHANGE',
            resource_type='Application', resource_id=str(application_id),
            details={'old_status': old_status, 'new_status': new_status, 'reason': reason, 'manual_override': True})
        await db.commit()
        return app


shortlisting_service = ShortlistingService()
