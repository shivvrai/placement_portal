"""
Drive service — business logic for placement drives and applications.
"""

import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload
from fastapi import HTTPException, status

from app.models.industry import Company
from app.models.placement import PlacementDrive, Application, InterviewStage
from app.models.user import Student, Department
from app.schemas.drive import DriveCreateRequest, DriveUpdateRequest, ApplicationStageUpdate, OfferCreate


# ─── Drives ────────────────────────────────────────────────────────────────────

async def get_drive(db: AsyncSession, drive_id: uuid.UUID) -> PlacementDrive:
    result = await db.execute(
        select(PlacementDrive)
        .where(PlacementDrive.id == drive_id)
        .options(selectinload(PlacementDrive.company))
    )
    drive = result.scalar_one_or_none()
    if not drive:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drive not found")
    return drive


async def list_drives(
    db: AsyncSession,
    status_filter: Optional[str] = None,
    department_code: Optional[str] = None,
    student_id: Optional[uuid.UUID] = None,  # used to compute has_applied
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[PlacementDrive], int]:
    query = (
        select(PlacementDrive)
        .options(selectinload(PlacementDrive.company))
        .order_by(PlacementDrive.registration_deadline.asc())
    )

    if status_filter:
        query = query.where(PlacementDrive.status == status_filter)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    query = query.offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(query)).scalars().all()
    return list(rows), total


async def create_drive(
    db: AsyncSession,
    data: DriveCreateRequest,
    created_by: uuid.UUID,
) -> PlacementDrive:
    # Upsert company by name
    result = await db.execute(select(Company).where(Company.name == data.company_name))
    company = result.scalar_one_or_none()
    if not company:
        company = Company(
            name=data.company_name,
            industry=data.company_industry,
            location=data.company_location,
        )
        db.add(company)
        await db.flush()

    drive = PlacementDrive(
        company_id=company.id,
        title=data.title,
        description=data.description,
        drive_date=data.drive_date,
        registration_deadline=data.registration_deadline,
        min_cgpa=data.min_cgpa,
        eligible_departments=data.eligible_departments,
        max_backlogs=data.max_backlogs,
        roles_offered=data.roles_offered,
        salary_ctc=data.salary_ctc,
        academic_year=data.academic_year,
        status="upcoming",
        created_by=created_by,
    )
    db.add(drive)
    await db.commit()
    return await get_drive(db, drive.id)


async def update_drive(
    db: AsyncSession,
    drive: PlacementDrive,
    data: DriveUpdateRequest,
) -> PlacementDrive:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(drive, field, value)
    await db.commit()
    return await get_drive(db, drive.id)


# ─── Applications ──────────────────────────────────────────────────────────────

async def get_application_count(db: AsyncSession, drive_id: uuid.UUID) -> dict:
    """Return counts: registered, shortlisted, selected."""
    rows = await db.execute(
        select(Application.status, func.count(Application.id).label("cnt"))
        .where(Application.drive_id == drive_id)
        .group_by(Application.status)
    )
    counts = {r.status: r.cnt for r in rows}
    return {
        "registered_count": sum(counts.values()),
        "shortlisted_count": counts.get("shortlisted", 0),
        "selected_count": counts.get("selected", 0),
    }


async def check_applied(db: AsyncSession, student_id: uuid.UUID, drive_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(Application.id)
        .where(Application.student_id == student_id, Application.drive_id == drive_id)
    )
    return result.scalar_one_or_none() is not None


async def apply_to_drive(
    db: AsyncSession,
    student_id: uuid.UUID,
    drive_id: uuid.UUID,
) -> Application:
    # Check duplicate
    exists = await check_applied(db, student_id, drive_id)
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already applied to this drive",
        )

    drive = await get_drive(db, drive_id)
    if drive.status not in ("open", "upcoming"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Drive is not open for applications",
        )

    app = Application(student_id=student_id, drive_id=drive_id)
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app


async def get_my_applications(
    db: AsyncSession,
    student_id: uuid.UUID,
) -> list[Application]:
    result = await db.execute(
        select(Application)
        .where(Application.student_id == student_id)
        .options(
            selectinload(Application.drive).selectinload(PlacementDrive.company),
            selectinload(Application.stages),
        )
        .order_by(Application.applied_at.desc())
    )
    return result.scalars().all()


async def get_shortlisted_students(
    db: AsyncSession,
    drive_id: uuid.UUID,
) -> list[Application]:
    result = await db.execute(
        select(Application)
        .where(
            Application.drive_id == drive_id,
            Application.status.in_(["shortlisted", "in_progress", "selected"]),
        )
        .options(
            selectinload(Application.student).selectinload(Student.user),
            selectinload(Application.student).selectinload(Student.department),
            selectinload(Application.stages),
        )
        .order_by(Application.applied_at.asc())
    )
    return result.scalars().all()


async def get_all_applicants(
    db: AsyncSession,
    drive_id: uuid.UUID,
) -> list[Application]:
    result = await db.execute(
        select(Application)
        .where(Application.drive_id == drive_id)
        .options(
            selectinload(Application.student).selectinload(Student.user),
            selectinload(Application.student).selectinload(Student.department),
            selectinload(Application.stages),
            selectinload(Application.drive).selectinload(PlacementDrive.company),
        )
        .order_by(Application.applied_at.desc())
    )
    return result.scalars().all()


async def update_application_stage(
    drive_id: uuid.UUID,
    application_id: uuid.UUID,
    update: ApplicationStageUpdate,
    actor_id: uuid.UUID,
    db: AsyncSession,
) -> tuple[Application, str]:
    """
    1. Fetch the Application by (drive_id, application_id) — raise 404 if not found.
    2. Record the previous status for audit log.
    3. Apply all non-None fields from update to the Application ORM object.
    4. If update.status == 'selected': set student.placement_status = 'placed' on the related Student.
    5. Flush and return the updated Application and old_status.
    IMPORTANT: Do NOT commit here — the router handles the commit.
    """
    result = await db.execute(
        select(Application)
        .where(Application.id == application_id, Application.drive_id == drive_id)
        .options(
            selectinload(Application.student).selectinload(Student.user),
            selectinload(Application.student).selectinload(Student.department),
            selectinload(Application.stages),
            selectinload(Application.drive).selectinload(PlacementDrive.company),
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found for this drive")

    old_status = app.status

    if update.status is not None:
        app.status = update.status

    if update.current_stage is not None:
        app.current_stage = update.current_stage

    # Handle interview stage record
    if update.current_stage or update.stage_status or update.scheduled_at or update.meeting_link or update.venue:
        stage_name = update.current_stage or app.current_stage or "Interview"

        # Check existing stage with this name
        existing_stage = None
        for s in (app.stages or []):
            if s.stage_name.lower() == stage_name.lower():
                existing_stage = s
                break

        stage_notes = []
        if update.meeting_link:
            stage_notes.append(f"Meeting: {update.meeting_link}")
        if update.venue:
            stage_notes.append(f"Venue: {update.venue}")
        if update.feedback:
            stage_notes.append(f"Notes: {update.feedback}")
        combined_feedback = " | ".join(stage_notes) if stage_notes else update.feedback

        if existing_stage:
            if update.stage_status:
                existing_stage.status = update.stage_status
            if update.scheduled_at:
                existing_stage.scheduled_at = update.scheduled_at
            if combined_feedback:
                existing_stage.feedback = combined_feedback
            if update.stage_status in ("passed", "failed", "completed"):
                existing_stage.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            new_order = len(app.stages) + 1 if app.stages else 1
            new_stage = InterviewStage(
                id=uuid.uuid4(),
                application_id=app.id,
                stage_name=stage_name,
                stage_order=new_order,
                status=update.stage_status or "scheduled",
                scheduled_at=update.scheduled_at,
                feedback=combined_feedback,
                completed_at=datetime.now(timezone.utc).replace(tzinfo=None) if update.stage_status in ("passed", "failed", "completed") else None,
            )
            db.add(new_stage)
            if app.stages is None:
                app.stages = []
            app.stages.append(new_stage)

    if (update.status == "selected" or app.status == "selected") and app.student:
        if hasattr(app.student, "placement_status"):
            setattr(app.student, "placement_status", "placed")

    await db.flush()
    return app, old_status


async def record_offer(
    drive_id: uuid.UUID,
    application_id: uuid.UUID,
    offer: OfferCreate,
    actor_id: uuid.UUID,
    db: AsyncSession,
) -> Application:
    """
    Records an official offer for a selected candidate.
    1. Validates applicant exists and status is 'selected'.
    2. Updates Application with offer fields.
    3. Updates Student.placement_status = 'placed' if field exists.
    4. Flushes and returns updated Application.
    """
    result = await db.execute(
        select(Application)
        .where(Application.id == application_id, Application.drive_id == drive_id)
        .options(
            selectinload(Application.student).selectinload(Student.user),
            selectinload(Application.student).selectinload(Student.department),
            selectinload(Application.drive).selectinload(PlacementDrive.company),
            selectinload(Application.stages),
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found for this drive")

    app.status = "selected"
    app.offer_ctc_lpa = offer.offer_ctc_lpa
    app.offer_fixed_lpa = offer.offer_fixed_lpa
    app.offer_variable_lpa = offer.offer_variable_lpa
    app.offer_designation = offer.offer_designation
    app.offer_joining_date = offer.offer_joining_date
    app.offer_reference_number = offer.offer_reference_number
    app.offer_recorded_at = datetime.now(timezone.utc).replace(tzinfo=None)

    if app.student and hasattr(app.student, "placement_status"):
        setattr(app.student, "placement_status", "placed")

    await db.flush()
    return app
