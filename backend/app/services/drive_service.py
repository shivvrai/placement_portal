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
from app.schemas.drive import DriveCreateRequest, DriveUpdateRequest


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
            selectinload(Application.stages),
        )
        .order_by(Application.applied_at.asc())
    )
    return result.scalars().all()
