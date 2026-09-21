"""
Drives API — placement drive management and student applications.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.core.audit import record_audit_event
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.models.placement import Application
from app.models.announcements import DriveAnnouncement
from app.api.v1.notifications import create_notification
from app.schemas.drive import (
    DriveResponse, DriveCreateRequest, DriveUpdateRequest,
    ApplicationResponse, ApplicationStudentRow, CompanyBrief,
    ApplicationStageUpdate, OfferCreate, AnnouncementCreate, AnnouncementResponse,
)
from app.schemas.common import MessageResponse, PaginatedResponse, PaginationMeta
from app.services import drive_service

router = APIRouter(prefix="/drives", tags=["Placement Drives"])

_tpo_admin = RoleChecker(["tpo", "admin"])
_authenticated = get_current_user


def _drive_to_response(drive, counts: dict = None, has_applied: bool = False) -> DriveResponse:
    counts = counts or {}
    return DriveResponse(
        id=drive.id,
        company=CompanyBrief(
            id=drive.company.id,
            name=drive.company.name,
            industry=drive.company.industry,
            location=drive.company.location,
        ) if drive.company else CompanyBrief(id=uuid.uuid4(), name="Unknown"),
        title=drive.title,
        description=drive.description,
        drive_date=drive.drive_date,
        registration_deadline=drive.registration_deadline,
        min_cgpa=float(drive.min_cgpa) if drive.min_cgpa else None,
        eligible_departments=drive.eligible_departments or [],
        max_backlogs=drive.max_backlogs,
        roles_offered=drive.roles_offered or [],
        salary_ctc=float(drive.salary_ctc) if drive.salary_ctc else None,
        status=drive.status,
        academic_year=drive.academic_year,
        registered_count=counts.get("registered_count", 0),
        shortlisted_count=counts.get("shortlisted_count", 0),
        selected_count=counts.get("selected_count", 0),
        has_applied=has_applied,
    )


@router.get("", response_model=PaginatedResponse, summary="List placement drives")
async def list_drives(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    drives, total = await drive_service.list_drives(
        db, status_filter=status_filter, page=page, per_page=per_page
    )
    data = []
    for drive in drives:
        counts = await drive_service.get_application_count(db, drive.id)
        has_applied = (
            await drive_service.check_applied(db, current_user.id, drive.id)
            if current_user.role == "student" else False
        )
        data.append(_drive_to_response(drive, counts, has_applied))

    total_pages = max(1, (total + per_page - 1) // per_page)
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total, total_pages=total_pages),
    )


@router.post("", response_model=DriveResponse, status_code=status.HTTP_201_CREATED, summary="Create drive (TPO)")
async def create_drive(
    data: DriveCreateRequest,
    request: Request,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    drive = await drive_service.create_drive(db, data, created_by=current_user.id)
    await record_audit_event(
        db=db,
        actor_id=current_user.id,
        event_type="DRIVE_CREATE",
        resource_type="PlacementDrive",
        resource_id=str(drive.id),
        details={"company": data.company_name, "title": data.title},
        ip_address=request.client.host if request.client else None,
    )
    return _drive_to_response(drive)


@router.get("/{drive_id}", response_model=DriveResponse)
async def get_drive(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    drive = await drive_service.get_drive(db, drive_id)
    counts = await drive_service.get_application_count(db, drive_id)
    has_applied = (
        await drive_service.check_applied(db, current_user.id, drive_id)
        if current_user.role == "student" else False
    )
    return _drive_to_response(drive, counts, has_applied)


@router.patch("/{drive_id}", response_model=DriveResponse, summary="Update drive (TPO)")
async def update_drive(
    drive_id: uuid.UUID,
    data: DriveUpdateRequest,
    request: Request,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    drive = await drive_service.get_drive(db, drive_id)
    changed_fields = [k for k, v in data.model_dump(exclude_none=True).items()]
    drive = await drive_service.update_drive(db, drive, data)
    await record_audit_event(
        db=db,
        actor_id=current_user.id,
        event_type="DRIVE_UPDATE",
        resource_type="PlacementDrive",
        resource_id=str(drive_id),
        details={"drive_id": str(drive_id), "changed_fields": changed_fields},
        ip_address=request.client.host if request.client else None,
    )
    counts = await drive_service.get_application_count(db, drive_id)
    return _drive_to_response(drive, counts)


@router.post("/{drive_id}/apply", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_drive(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await drive_service.apply_to_drive(db, student_id=current_user.id, drive_id=drive_id)
    return MessageResponse(message="Application submitted successfully")


@router.get("/{drive_id}/shortlisted", summary="View shortlisted students (TPO)")
async def get_shortlisted(
    drive_id: uuid.UUID,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    applications = await drive_service.get_shortlisted_students(db, drive_id)
    return [
        ApplicationStudentRow(
            application_id=app.id,
            student_id=app.student.id,
            roll_number=app.student.roll_number,
            first_name=app.student.user.first_name,
            last_name=app.student.user.last_name,
            cgpa=float(app.student.cgpa) if app.student.cgpa else None,
            department=app.student.department.code if app.student.department else None,
            status=app.status,
            current_stage=app.current_stage,
            feedback=app.stages[-1].feedback if app.stages else None,
            applied_at=app.applied_at,
            offer_ctc_lpa=float(app.offer_ctc_lpa) if app.offer_ctc_lpa else None,
            offer_fixed_lpa=float(app.offer_fixed_lpa) if app.offer_fixed_lpa else None,
            offer_variable_lpa=float(app.offer_variable_lpa) if app.offer_variable_lpa else None,
            offer_designation=app.offer_designation,
            offer_joining_date=app.offer_joining_date,
            offer_reference_number=app.offer_reference_number,
            offer_recorded_at=app.offer_recorded_at,
        )
        for app in applications
    ]
@router.get("/{drive_id}/applicants", response_model=list[ApplicationStudentRow], summary="View all applicants (TPO)")
async def get_all_applicants(
    drive_id: uuid.UUID,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """Returns all applicants for a drive with student details and offer info."""
    applications = await drive_service.get_all_applicants(db, drive_id)
    return [
        ApplicationStudentRow(
            application_id=app.id,
            student_id=app.student.id,
            roll_number=app.student.roll_number,
            first_name=app.student.user.first_name,
            last_name=app.student.user.last_name,
            cgpa=float(app.student.cgpa) if app.student.cgpa else None,
            department=app.student.department.code if app.student.department else None,
            status=app.status,
            current_stage=app.current_stage,
            feedback=app.stages[-1].feedback if app.stages else None,
            applied_at=app.applied_at,
            offer_ctc_lpa=float(app.offer_ctc_lpa) if app.offer_ctc_lpa else None,
            offer_fixed_lpa=float(app.offer_fixed_lpa) if app.offer_fixed_lpa else None,
            offer_variable_lpa=float(app.offer_variable_lpa) if app.offer_variable_lpa else None,
            offer_designation=app.offer_designation,
            offer_joining_date=app.offer_joining_date,
            offer_reference_number=app.offer_reference_number,
            offer_recorded_at=app.offer_recorded_at,
        )
        for app in applications
    ]


@router.patch("/{drive_id}/applications/{application_id}", summary="Update applicant stage (TPO)")
async def update_application_stage(
    drive_id: uuid.UUID,
    application_id: uuid.UUID,
    update: ApplicationStageUpdate,
    request: Request,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    TPO advances or updates an applicant's stage in a drive.
    Must call record_audit_event with event_type='APPLICATION_STATUS_CHANGE'.
    Must call create_notification() for the student if status changes.
    """
    app, old_status = await drive_service.update_application_stage(
        drive_id=drive_id,
        application_id=application_id,
        update=update,
        actor_id=current_user.id,
        db=db,
    )

    new_status = app.status
    await record_audit_event(
        db=db,
        actor_id=current_user.id,
        event_type="APPLICATION_STATUS_CHANGE",
        resource_type="Application",
        resource_id=str(application_id),
        details={
            "app_id": str(application_id),
            "drive_id": str(drive_id),
            "old_status": old_status,
            "new_status": new_status,
            "current_stage": app.current_stage,
        },
        ip_address=request.client.host if request.client else None,
    )

    # Notify student if status or stage changed
    if old_status != new_status or update.current_stage or update.scheduled_at:
        company_name = app.drive.company.name if (app.drive and app.drive.company) else "Placement Drive"
        stage_info = f" ({app.current_stage})" if app.current_stage else ""
        notif_msg = f"Your application status for {company_name} is now '{new_status}'{stage_info}."
        if update.scheduled_at:
            notif_msg += f" Scheduled: {update.scheduled_at.strftime('%Y-%m-%d %H:%M')}."
        if update.meeting_link:
            notif_msg += f" Meeting link: {update.meeting_link}."
        if update.venue:
            notif_msg += f" Venue: {update.venue}."

        await create_notification(
            db=db,
            user_id=app.student_id,
            title=f"Application Update: {company_name}",
            message=notif_msg,
            type="info",
            link="/student/drives",
        )

    await db.commit()
    await db.refresh(app)
    return {
        "message": "Application updated successfully",
        "status": app.status,
        "current_stage": app.current_stage,
    }


@router.post("/{drive_id}/applications/{application_id}/offer", summary="Record official offer (TPO)")
async def record_offer(
    drive_id: uuid.UUID,
    application_id: uuid.UUID,
    offer: OfferCreate,
    request: Request,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Records an official offer for a selected candidate.
    1. Validates applicant status is 'selected'.
    2. Updates Application with offer fields.
    3. Updates Student.placement_status = 'placed'.
    4. Calls record_audit_event with event_type='OFFER_RECORDED'.
    5. Calls create_notification() for the student with the offer details.
    """
    app = await drive_service.record_offer(
        drive_id=drive_id,
        application_id=application_id,
        offer=offer,
        actor_id=current_user.id,
        db=db,
    )

    await record_audit_event(
        db=db,
        actor_id=current_user.id,
        event_type="OFFER_RECORDED",
        resource_type="Application",
        resource_id=str(application_id),
        details={
            "drive_id": str(drive_id),
            "application_id": str(application_id),
            "offer_ctc_lpa": offer.offer_ctc_lpa,
            "offer_fixed_lpa": offer.offer_fixed_lpa,
            "offer_variable_lpa": offer.offer_variable_lpa,
            "offer_designation": offer.offer_designation,
            "offer_reference_number": offer.offer_reference_number,
        },
        ip_address=request.client.host if request.client else None,
    )

    company_name = app.drive.company.name if (app.drive and app.drive.company) else "Company"
    await create_notification(
        db=db,
        user_id=app.student_id,
        title=f"🎉 Offer Letter: {company_name}",
        message=(
            f"Congratulations! An official offer has been recorded for the role of "
            f"'{offer.offer_designation}' with a package of ₹{offer.offer_ctc_lpa} LPA at {company_name}."
        ),
        type="success",
        link="/student/drives",
    )

    await db.commit()
    await db.refresh(app)
    return {
        "message": "Offer recorded successfully",
        "application_id": app.id,
        "offer_ctc_lpa": float(app.offer_ctc_lpa) if app.offer_ctc_lpa else None,
        "offer_designation": app.offer_designation,
    }


# ─── Drive Announcements ──────────────────────────────────────────────────────

@router.post("/{drive_id}/announcements", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED, summary="Post drive announcement (TPO)")
async def post_announcement(
    drive_id: uuid.UUID,
    data: AnnouncementCreate,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    TPO posts an announcement for a specific drive.
    After saving to DB, creates a Notification for all students who have applied to this drive.
    """
    drive = await drive_service.get_drive(db, drive_id)

    announcement = DriveAnnouncement(
        id=uuid.uuid4(),
        drive_id=drive_id,
        author_id=current_user.id,
        title=data.title,
        message=data.message,
        urgency=data.urgency,
    )
    db.add(announcement)
    await db.flush()

    # Create notification for all students who applied to this drive
    stmt = select(Application.student_id).where(Application.drive_id == drive_id)
    result = await db.execute(stmt)
    applied_student_ids = result.scalars().all()

    company_name = drive.company.name if drive.company else drive.title
    urgency_prefix = "🔴 [URGENT] " if data.urgency == "urgent" else "⚠️ [IMPORTANT] " if data.urgency == "important" else ""
    notif_type = "alert" if data.urgency in ("urgent", "important") else "info"

    for s_id in applied_student_ids:
        await create_notification(
            db=db,
            user_id=s_id,
            title=f"{urgency_prefix}Announcement: {company_name}",
            message=f"{data.title}: {data.message}",
            type=notif_type,
            link="/student/drives",
        )

    await db.commit()
    await db.refresh(announcement)

    author_name = f"{current_user.first_name} {current_user.last_name}".strip() if current_user else "TPO"
    return AnnouncementResponse(
        id=announcement.id,
        drive_id=announcement.drive_id,
        author_id=announcement.author_id,
        author_name=author_name,
        title=announcement.title,
        message=announcement.message,
        urgency=announcement.urgency,
        created_at=announcement.created_at,
    )


@router.get("/{drive_id}/announcements", response_model=list[AnnouncementResponse], summary="Get drive announcements")
async def get_announcements(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns all announcements for a drive, newest first."""
    stmt = (
        select(DriveAnnouncement)
        .where(DriveAnnouncement.drive_id == drive_id)
        .options(selectinload(DriveAnnouncement.author))
        .order_by(DriveAnnouncement.created_at.desc())
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    return [
        AnnouncementResponse(
            id=a.id,
            drive_id=a.drive_id,
            author_id=a.author_id,
            author_name=f"{a.author.first_name} {a.author.last_name}".strip() if a.author else "TPO",
            title=a.title,
            message=a.message,
            urgency=a.urgency,
            created_at=a.created_at,
        )
        for a in items
    ]
