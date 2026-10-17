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


# ─── Calendar Events Endpoint (Task 3 Spec) ──────────────────────────────────

@router.get("/events", summary="All upcoming campus placement milestones (calendar events)")
async def get_calendar_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /calendar/events — Returns all upcoming campus placement milestones
    across active drives, formatted as structured calendar events.

    Event types covered:
    - Pre-Placement Talks (PPTs) — upcoming drives with registration deadline
    - Online Assessment Windows — drives in 'open' status
    - Technical Interview Slots — drives in 'in_progress' status
    - Drive Day Events — drives with a drive_date set

    Also checks for scheduling conflicts: flags warnings if two Tier-1 companies
    schedule technical interviews for the same department cohort simultaneously.

    Returns iCal-compatible payload structure for dashboard integration.
    """
    stmt = (
        select(PlacementDrive)
        .options(selectinload(PlacementDrive.company))
        .where(PlacementDrive.status.in_(["upcoming", "open", "in_progress"]))
        .order_by(PlacementDrive.drive_date.asc().nullslast())
    )
    result = await db.execute(stmt)
    drives = result.scalars().all()

    conflicts_map = _get_conflict_pairs(drives)
    conflicted_ids = set()
    for c in conflicts_map:
        conflicted_ids.add(str(c["drive_a_id"]))
        conflicted_ids.add(str(c["drive_b_id"]))

    events = []
    for d in drives:
        company_name = d.company.name if d.company else "Unknown"

        # Pre-Placement Talk (PPT) event — tied to registration deadline
        if d.registration_deadline and d.status in ("upcoming", "open"):
            events.append({
                "event_id": f"ppt-{d.id}",
                "drive_id": str(d.id),
                "event_type": "Pre-Placement Talk (PPT)",
                "title": f"PPT: {company_name}",
                "company_name": company_name,
                "date": d.registration_deadline.date().isoformat(),
                "datetime": d.registration_deadline.isoformat(),
                "status": d.status,
                "eligible_departments": d.eligible_departments or [],
                "academic_year": d.academic_year,
                "has_conflict": str(d.id) in conflicted_ids,
                "conflict_warning": any(
                    c for c in conflicts_map
                    if str(d.id) in (str(c["drive_a_id"]), str(c["drive_b_id"]))
                ),
                "ical_summary": f"PPT — {company_name} | Deadline: {d.registration_deadline.strftime('%d %b %Y')}",
            })

        # Online Assessment Window — open drives
        if d.status == "open":
            events.append({
                "event_id": f"oa-{d.id}",
                "drive_id": str(d.id),
                "event_type": "Online Assessment Window",
                "title": f"Online Assessment: {company_name}",
                "company_name": company_name,
                "date": d.drive_date.isoformat() if d.drive_date else None,
                "datetime": d.registration_deadline.isoformat() if d.registration_deadline else None,
                "status": d.status,
                "eligible_departments": d.eligible_departments or [],
                "academic_year": d.academic_year,
                "has_conflict": str(d.id) in conflicted_ids,
                "conflict_warning": False,
                "ical_summary": f"Online Assessment — {company_name}",
            })

        # Technical Interview / Drive Day — in_progress drives with a drive_date
        if d.drive_date:
            event_type = "Technical Interview Slots" if d.status == "in_progress" else "Drive Day"
            events.append({
                "event_id": f"drive-{d.id}",
                "drive_id": str(d.id),
                "event_type": event_type,
                "title": f"{event_type}: {company_name} — {d.title}",
                "company_name": company_name,
                "date": d.drive_date.isoformat(),
                "datetime": d.drive_date.isoformat(),
                "status": d.status,
                "eligible_departments": d.eligible_departments or [],
                "academic_year": d.academic_year,
                "has_conflict": str(d.id) in conflicted_ids,
                "conflict_warning": str(d.id) in conflicted_ids,
                "ical_summary": f"{event_type} — {company_name} | {d.drive_date.strftime('%d %b %Y')}",
                "salary_ctc": float(d.salary_ctc) if d.salary_ctc else None,
            })

    # Sort all events by date ascending
    events.sort(key=lambda e: (e["date"] or "9999-99-99"))

    return {
        "total_events": len(events),
        "conflicts_detected": len(conflicts_map),
        "events": events,
    }
