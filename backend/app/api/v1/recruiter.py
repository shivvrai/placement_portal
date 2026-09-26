"""
Recruiter CRM API - Company HR portal for viewing candidates and submitting feedback.
Prefix: /recruiter
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.placement import Application, PlacementDrive, InterviewStage
from app.models.user import User, Student

router = APIRouter(prefix="/recruiter", tags=["Recruiter CRM"])


def _require_recruiter(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("recruiter", "tpo", "admin"):
        raise HTTPException(status_code=403, detail="Recruiter access required")
    return current_user


@router.get("/drives", summary="Get drives for recruiter's company")
async def get_recruiter_drives(
    current_user: User = Depends(_require_recruiter),
    db: AsyncSession = Depends(get_db),
):
    """Returns drives linked to the recruiter's company_id."""
    company_id = getattr(current_user, "company_id", None)
    if not company_id and current_user.role not in ("tpo", "admin"):
        raise HTTPException(status_code=400, detail="Recruiter has no company_id set")

    stmt = select(PlacementDrive).options(selectinload(PlacementDrive.company)).order_by(PlacementDrive.created_at.desc())
    if company_id:
        stmt = stmt.where(PlacementDrive.company_id == company_id)

    result = await db.execute(stmt)
    drives = result.scalars().all()

    drive_list = []
    for d in drives:
        count_stmt = (
            select(Application.status, func.count(Application.id).label("cnt"))
            .where(Application.drive_id == d.id)
            .where(Application.status.in_(["shortlisted", "in_progress", "selected"]))
            .group_by(Application.status)
        )
        count_result = await db.execute(count_stmt)
        counts = {r.status: r.cnt for r in count_result.all()}
        drive_list.append({
            "id": str(d.id),
            "title": d.title,
            "status": d.status,
            "drive_date": d.drive_date.isoformat() if d.drive_date else None,
            "company_name": d.company.name if d.company else "Unknown",
            "shortlisted_count": counts.get("shortlisted", 0) + counts.get("in_progress", 0),
            "selected_count": counts.get("selected", 0),
        })
    return drive_list


@router.get("/drives/{drive_id}/applicants", summary="Get shortlisted/selected applicants for a drive")
async def get_drive_applicants(
    drive_id: uuid.UUID,
    current_user: User = Depends(_require_recruiter),
    db: AsyncSession = Depends(get_db),
):
    """Returns shortlisted and selected applicants (anonymized - no personal contact)."""
    drive_result = await db.execute(select(PlacementDrive).where(PlacementDrive.id == drive_id))
    drive = drive_result.scalar_one_or_none()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    company_id = getattr(current_user, "company_id", None)
    if company_id and drive.company_id != company_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this drive")

    from app.models.skill import StudentSkill
    stmt = (
        select(Application)
        .where(Application.drive_id == drive_id)
        .where(Application.status.in_(["shortlisted", "in_progress", "selected"]))
        .options(
            selectinload(Application.student).selectinload(Student.department),
            selectinload(Application.student).selectinload(Student.skills).selectinload(StudentSkill.skill),
            selectinload(Application.student).selectinload(Student.projects),
            selectinload(Application.stages),
        )
        .order_by(Application.updated_at.desc())
    )
    result = await db.execute(stmt)
    applications = result.scalars().all()

    return [
        {
            "application_id": str(app.id),
            "status": app.status,
            "current_stage": app.current_stage,
            "department": app.student.department.code if (app.student and app.student.department) else None,
            "cgpa": float(app.student.cgpa) if (app.student and app.student.cgpa) else None,
            "skills": [{"name": ss.skill.name, "category": ss.skill.category} for ss in (app.student.skills or []) if ss.skill],
            "project_count": len(app.student.projects) if (app.student and app.student.projects) else 0,
            "display_name": f"Candidate #{str(app.student_id)[:8].upper()}",
            "applied_at": app.applied_at.isoformat() if app.applied_at else None,
            "stage_count": len(app.stages) if app.stages else 0,
        }
        for app in applications
    ]


@router.get("/applicants/{app_id}", summary="Get applicant profile (anonymized)")
async def get_applicant_profile(
    app_id: uuid.UUID,
    current_user: User = Depends(_require_recruiter),
    db: AsyncSession = Depends(get_db),
):
    """Returns anonymized applicant profile."""
    from app.models.skill import StudentSkill
    result = await db.execute(
        select(Application)
        .where(Application.id == app_id)
        .options(
            selectinload(Application.drive).selectinload(PlacementDrive.company),
            selectinload(Application.student).selectinload(Student.department),
            selectinload(Application.student).selectinload(Student.skills).selectinload(StudentSkill.skill),
            selectinload(Application.student).selectinload(Student.projects),
            selectinload(Application.stages),
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    company_id = getattr(current_user, "company_id", None)
    if company_id and app.drive and app.drive.company_id != company_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    student = app.student
    return {
        "application_id": str(app.id),
        "display_name": f"Candidate #{str(app.student_id)[:8].upper()}",
        "status": app.status,
        "current_stage": app.current_stage,
        "cgpa": float(student.cgpa) if student.cgpa else None,
        "department": student.department.code if student.department else None,
        "admission_year": student.admission_year,
        "skills": [
            {"name": ss.skill.name, "category": ss.skill.category, "confidence": float(ss.confidence) if ss.confidence else None}
            for ss in (student.skills or []) if ss.skill
        ],
        "projects": [
            {"title": p.title, "description": p.description, "technologies": p.technologies}
            for p in (student.projects or [])
        ],
        "has_resume": bool(student.resume_url),
        "stages": [
            {
                "stage_name": s.stage_name,
                "status": s.status,
                "feedback": s.feedback,
                "scheduled_at": s.scheduled_at.isoformat() if s.scheduled_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            }
            for s in (app.stages or [])
        ],
    }


class FeedbackRequest(BaseModel):
    stage: str
    rating: int
    comments: str = ""
    outcome: str  # "pass" | "fail" | "on_hold"


@router.post("/applicants/{app_id}/feedback", summary="Submit interview feedback")
async def submit_feedback(
    app_id: uuid.UUID,
    feedback: FeedbackRequest,
    current_user: User = Depends(_require_recruiter),
    db: AsyncSession = Depends(get_db),
):
    """Recruiter submits interview feedback for an applicant stage."""
    result = await db.execute(
        select(Application)
        .where(Application.id == app_id)
        .options(selectinload(Application.drive), selectinload(Application.stages))
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    company_id = getattr(current_user, "company_id", None)
    if company_id and app.drive and app.drive.company_id != company_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not (1 <= feedback.rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    if feedback.outcome not in ("pass", "fail", "on_hold"):
        raise HTTPException(status_code=400, detail="Outcome must be pass, fail, or on_hold")

    existing_stage = next((s for s in (app.stages or []) if s.stage_name == feedback.stage), None)
    feedback_text = f"[Rating: {feedback.rating}/5] {feedback.comments}\nOutcome: {feedback.outcome}"

    if existing_stage:
        existing_stage.feedback = feedback_text
        existing_stage.status = "completed" if feedback.outcome in ("pass", "fail") else "pending"
    else:
        stage_order = len(app.stages) + 1 if app.stages else 1
        new_stage = InterviewStage(
            id=uuid.uuid4(),
            application_id=app_id,
            stage_name=feedback.stage,
            stage_order=stage_order,
            status="completed" if feedback.outcome in ("pass", "fail") else "pending",
            feedback=feedback_text,
        )
        db.add(new_stage)

    await db.flush()
    await db.commit()
    return {"message": "Feedback submitted successfully", "application_id": str(app_id)}


@router.get("/dashboard", summary="Recruiter dashboard stats")
async def recruiter_dashboard(
    current_user: User = Depends(_require_recruiter),
    db: AsyncSession = Depends(get_db),
):
    """Returns dashboard stats for the recruiter company."""
    company_id = getattr(current_user, "company_id", None)

    drive_stmt = select(func.count(PlacementDrive.id)).where(
        PlacementDrive.status.in_(["upcoming", "open", "in_progress"])
    )
    if company_id:
        drive_stmt = drive_stmt.where(PlacementDrive.company_id == company_id)
    drive_count = (await db.execute(drive_stmt)).scalar_one_or_none() or 0

    drive_ids_stmt = select(PlacementDrive.id)
    if company_id:
        drive_ids_stmt = drive_ids_stmt.where(PlacementDrive.company_id == company_id)
    drive_ids_result = await db.execute(drive_ids_stmt)
    drive_ids = [r[0] for r in drive_ids_result.all()]

    shortlisted_count, selected_count = 0, 0
    if drive_ids:
        sl_stmt = select(func.count(Application.id)).where(
            Application.drive_id.in_(drive_ids),
            Application.status.in_(["shortlisted", "in_progress"])
        )
        shortlisted_count = (await db.execute(sl_stmt)).scalar_one_or_none() or 0
        sel_stmt = select(func.count(Application.id)).where(
            Application.drive_id.in_(drive_ids), Application.status == "selected"
        )
        selected_count = (await db.execute(sel_stmt)).scalar_one_or_none() or 0

    return {
        "active_drives": drive_count,
        "shortlisted_total": shortlisted_count,
        "selected_total": selected_count,
        "pending_interviews": 0,
        "company_id": str(company_id) if company_id else None,
    }
