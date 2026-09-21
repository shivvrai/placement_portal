"""
Applications API — student's personal application history.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.drive import ApplicationResponse, InterviewStageResponse
from app.services import drive_service

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.get("/mine", response_model=list[ApplicationResponse], summary="My application history")
async def get_my_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all applications for the current student, newest first."""
    applications = await drive_service.get_my_applications(db, student_id=current_user.id)
    result = []
    for app in applications:
        company_name = None
        salary_ctc = None
        drive_title = None
        if app.drive:
            drive_title = app.drive.title
            salary_ctc = float(app.drive.salary_ctc) if app.drive.salary_ctc else None
            if app.drive.company:
                company_name = app.drive.company.name

        result.append(ApplicationResponse(
            id=app.id,
            student_id=app.student_id,
            drive_id=app.drive_id,
            drive_title=drive_title,
            company_name=company_name,
            salary_ctc=salary_ctc,
            status=app.status,
            current_stage=app.current_stage,
            applied_at=app.applied_at,
            updated_at=app.updated_at,
            stages=[
                InterviewStageResponse(
                    id=s.id,
                    stage_name=s.stage_name,
                    stage_order=s.stage_order,
                    status=s.status,
                    feedback=s.feedback,
                    scheduled_at=s.scheduled_at,
                    completed_at=s.completed_at,
                )
                for s in sorted(app.stages, key=lambda s: s.stage_order)
            ],
            offer_ctc_lpa=float(app.offer_ctc_lpa) if app.offer_ctc_lpa else None,
            offer_fixed_lpa=float(app.offer_fixed_lpa) if app.offer_fixed_lpa else None,
            offer_variable_lpa=float(app.offer_variable_lpa) if app.offer_variable_lpa else None,
            offer_designation=app.offer_designation,
            offer_joining_date=app.offer_joining_date,
            offer_reference_number=app.offer_reference_number,
            offer_recorded_at=app.offer_recorded_at,
        ))
    return result
