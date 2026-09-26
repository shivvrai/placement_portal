"""
Calendar API - drive scheduling, month view, and conflict detection.
Prefix: /calendar
"""

import uuid
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.placement import PlacementDrive, Application
from app.models.user import User
from app.api.v1.notifications import create_notification

router = APIRouter(prefix="/calendar", tags=["Drive Calendar"])
_tpo_admin = RoleChecker(["tpo", "admin"])


@router.get("/drives", summary="All drives with calendar metadata")
async def get_calendar_drives(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns all drives formatted for calendar display, with conflict flags."""
    stmt = (
        select(PlacementDrive)
        .options(selectinload(PlacementDrive.company))
        .order_by(PlacementDrive.drive_date.asc().nullslast())
    )
    result = await db.execute(stmt)
    drives = result.scalars().all()

    conflicts_map = _get_conflict_pairs(drives)
    conflicted_ids = set()
    for c in conflicts_map:
        conflicted_ids.add(str(c["drive_a_id"]))
        conflicted_ids.add(str(c["drive_b_id"]))

    return [
        {
            "id": str(d.id),
            "title": d.title,
            "company_name": d.company.name if d.company else "Unknown",
            "company_id": str(d.company_id) if d.company_id else None,
            "drive_date": d.drive_date.isoformat() if d.drive_date else None,
            "registration_deadline": d.registration_deadline.isoformat() if d.registration_deadline else None,
            "status": d.status,
            "eligible_departments": d.eligible_departments or [],
            "academic_year": d.academic_year,
            "has_conflict": str(d.id) in conflicted_ids,
        }
        for d in drives
    ]


@router.get("/drives/month", summary="Drives for a specific month")
async def get_drives_for_month(
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns drives in a specific month for calendar display."""
    from calendar import monthrange
    _, days_in_month = monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, days_in_month)

    stmt = (
        select(PlacementDrive)
        .options(selectinload(PlacementDrive.company))
        .where(PlacementDrive.drive_date >= start_date)
        .where(PlacementDrive.drive_date <= end_date)
        .order_by(PlacementDrive.drive_date.asc())
    )
    result = await db.execute(stmt)
    drives = result.scalars().all()

    return [
        {
            "id": str(d.id),
            "title": d.title,
            "company_name": d.company.name if d.company else "Unknown",
            "drive_date": d.drive_date.isoformat() if d.drive_date else None,
            "registration_deadline": d.registration_deadline.isoformat() if d.registration_deadline else None,
            "status": d.status,
            "eligible_departments": d.eligible_departments or [],
            "day": d.drive_date.day if d.drive_date else None,
        }
        for d in drives
    ]


@router.post("/drives/{drive_id}/reschedule", summary="Reschedule a drive and notify applicants")
async def reschedule_drive(
    drive_id: uuid.UUID,
    body: dict,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reschedule a drive: update drive_date and/or registration_deadline. Notifies all registered applicants."""
    result = await db.execute(
        select(PlacementDrive)
        .options(selectinload(PlacementDrive.company))
        .where(PlacementDrive.id == drive_id)
    )
    drive = result.scalar_one_or_none()
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")

    new_date_str = body.get("drive_date")
    new_deadline_str = body.get("registration_deadline")

    if new_date_str:
        drive.drive_date = date.fromisoformat(new_date_str)
    if new_deadline_str:
        drive.registration_deadline = datetime.fromisoformat(new_deadline_str)

    await db.flush()

    stmt_apps = select(Application.student_id).where(Application.drive_id == drive_id)
    apps_result = await db.execute(stmt_apps)
    student_ids = apps_result.scalars().all()

    company_name = drive.company.name if drive.company else drive.title
    new_date_display = drive.drive_date.strftime("%B %d, %Y") if drive.drive_date else "TBD"
    for sid in student_ids:
        await create_notification(
            db=db, user_id=sid,
            title=f"Drive Rescheduled: {company_name}",
            message=f"The {drive.title} drive has been rescheduled to {new_date_display}. Please update your calendar.",
            type="info", link="/student/drives",
        )

    await db.commit()
    return {
        "message": "Drive rescheduled successfully",
        "drive_id": str(drive_id),
        "new_drive_date": drive.drive_date.isoformat() if drive.drive_date else None,
        "new_registration_deadline": drive.registration_deadline.isoformat() if drive.registration_deadline else None,
        "notified_applicants": len(student_ids),
    }


@router.get("/conflicts", summary="Detect scheduling conflicts between drives")
async def get_conflicts(
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """Detect overlapping drives that could cause student conflicts."""
    stmt = (
        select(PlacementDrive)
        .options(selectinload(PlacementDrive.company))
        .where(PlacementDrive.status.in_(["upcoming", "open", "in_progress"]))
        .where(PlacementDrive.drive_date != None)  # noqa: E711
    )
    result = await db.execute(stmt)
    drives = result.scalars().all()
    return _get_conflict_pairs(drives)


def _get_conflict_pairs(drives: list) -> list[dict]:
    """
    Detect conflicts: two drives conflict if they share >=1 eligible dept AND drive_date within 2 days.
    """
    conflicts = []
    for i in range(len(drives)):
        for j in range(i + 1, len(drives)):
            a = drives[i]
            b = drives[j]

            if not a.drive_date or not b.drive_date:
                continue

            depts_a = set(d.upper() for d in (a.eligible_departments or []))
            depts_b = set(d.upper() for d in (b.eligible_departments or []))
            shared_depts = depts_a & depts_b

            if not shared_depts:
                continue

            delta = abs((a.drive_date - b.drive_date).days)
            if delta > 2:
                continue

            conflict_type = "SAME_DAY" if delta == 0 else "DEADLINE_OVERLAP"
            severity = "critical" if delta == 0 else "warning"

            conflicts.append({
                "drive_a_id": str(a.id),
                "drive_a_title": a.title,
                "drive_a_company": a.company.name if a.company else "Unknown",
                "drive_a_date": a.drive_date.isoformat(),
                "drive_b_id": str(b.id),
                "drive_b_title": b.title,
                "drive_b_company": b.company.name if b.company else "Unknown",
                "drive_b_date": b.drive_date.isoformat(),
                "shared_departments": list(shared_depts),
                "conflict_type": conflict_type,
                "severity": severity,
                "days_apart": delta,
            })
    return conflicts
