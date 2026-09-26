"""
Offer Letters API - upload, download, accept/decline offer letters.
Prefix: /offer-letters
"""

import uuid
from datetime import date
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.placement import Application, PlacementDrive
from app.models.user import User, Student
from app.services.offer_service import offer_service

router = APIRouter(prefix="/offer-letters", tags=["Offer Letters"])
_tpo_admin = RoleChecker(["tpo", "admin"])
_authenticated = get_current_user


@router.post("/{application_id}/upload", summary="TPO uploads offer letter PDF")
async def upload_offer_letter(
    application_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """TPO uploads a PDF offer letter for a selected candidate."""
    download_url = await offer_service.upload_letter(application_id, file, current_user.id, db)
    return {
        "message": "Offer letter uploaded successfully. Student has been notified.",
        "application_id": str(application_id),
        "download_url": download_url,
    }


@router.get("/{application_id}/download", summary="Student downloads their offer letter")
async def download_offer_letter(
    application_id: uuid.UUID,
    current_user: User = Depends(_authenticated),
    db: AsyncSession = Depends(get_db),
):
    """Student downloads their own offer letter PDF. Only own applications allowed."""
    result = await db.execute(select(Application).where(Application.id == application_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if current_user.role == "student" and app.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to download this offer letter")

    if not app.offer_letter_url:
        raise HTTPException(status_code=404, detail="No offer letter uploaded yet")

    file_path = Path(app.offer_letter_url.lstrip("/"))
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Offer letter file not found on server")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"offer_letter_{application_id}.pdf",
    )


@router.post("/{application_id}/accept", summary="Student accepts offer")
async def accept_offer(
    application_id: uuid.UUID,
    current_user: User = Depends(_authenticated),
    db: AsyncSession = Depends(get_db),
):
    """Student accepts their offer letter."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can accept offers")
    await offer_service.accept_offer(application_id, current_user.id, db)
    return {"message": "Offer accepted successfully", "application_id": str(application_id)}


@router.post("/{application_id}/decline", summary="Student declines offer")
async def decline_offer(
    application_id: uuid.UUID,
    body: dict = {},
    current_user: User = Depends(_authenticated),
    db: AsyncSession = Depends(get_db),
):
    """Student declines their offer letter with an optional reason."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can decline offers")
    reason = (body or {}).get("reason", "")
    await offer_service.decline_offer(application_id, current_user.id, reason, db)
    return {"message": "Offer declined", "application_id": str(application_id)}


@router.get("/tpo/pending", summary="List selected applications without offer letter (TPO)")
async def list_pending_offer_letters(
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """Returns selected candidates who have not yet received an offer letter."""
    stmt = (
        select(Application)
        .where(Application.status == "selected")
        .where(Application.offer_letter_status == "pending")
        .options(
            selectinload(Application.student).selectinload(Student.user),
            selectinload(Application.student).selectinload(Student.department),
            selectinload(Application.drive).selectinload(PlacementDrive.company),
        )
        .order_by(Application.updated_at.desc())
    )
    result = await db.execute(stmt)
    applications = result.scalars().all()

    return [
        {
            "application_id": str(app.id),
            "student_id": str(app.student_id),
            "first_name": app.student.user.first_name if (app.student and app.student.user) else "",
            "last_name": app.student.user.last_name if (app.student and app.student.user) else "",
            "department": app.student.department.code if (app.student and app.student.department) else None,
            "drive_id": str(app.drive_id),
            "drive_title": app.drive.title if app.drive else "",
            "company_name": app.drive.company.name if (app.drive and app.drive.company) else "",
            "offer_ctc_lpa": float(app.offer_ctc_lpa) if app.offer_ctc_lpa else None,
            "offer_designation": app.offer_designation,
            "offer_letter_status": app.offer_letter_status,
            "selected_at": app.updated_at.isoformat() if app.updated_at else None,
        }
        for app in applications
    ]


@router.get("/tpo/accepted", summary="All accepted offer letters (TPO)")
async def list_accepted_offers(
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """Returns all accepted offer letters for reporting."""
    stmt = (
        select(Application)
        .where(Application.offer_letter_status == "accepted")
        .options(
            selectinload(Application.student).selectinload(Student.user),
            selectinload(Application.student).selectinload(Student.department),
            selectinload(Application.drive).selectinload(PlacementDrive.company),
        )
        .order_by(Application.offer_accepted_at.desc())
    )
    result = await db.execute(stmt)
    applications = result.scalars().all()

    return [
        {
            "application_id": str(app.id),
            "student_id": str(app.student_id),
            "first_name": app.student.user.first_name if (app.student and app.student.user) else "",
            "last_name": app.student.user.last_name if (app.student and app.student.user) else "",
            "department": app.student.department.code if (app.student and app.student.department) else None,
            "drive_title": app.drive.title if app.drive else "",
            "company_name": app.drive.company.name if (app.drive and app.drive.company) else "",
            "offer_ctc_lpa": float(app.offer_ctc_lpa) if app.offer_ctc_lpa else None,
            "offer_designation": app.offer_designation,
            "offer_accepted_at": app.offer_accepted_at.isoformat() if app.offer_accepted_at else None,
            "offer_joining_confirmed": app.offer_joining_confirmed,
            "offer_joining_date_confirmed": app.offer_joining_date_confirmed.isoformat() if app.offer_joining_date_confirmed else None,
        }
        for app in applications
    ]


@router.patch("/{application_id}/joining", summary="Student confirms joining date")
async def confirm_joining(
    application_id: uuid.UUID,
    body: dict,
    current_user: User = Depends(_authenticated),
    db: AsyncSession = Depends(get_db),
):
    """Student confirms their joining date after accepting the offer."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can confirm joining date")
    joining_date_str = body.get("joining_date")
    if not joining_date_str:
        raise HTTPException(status_code=400, detail="joining_date is required")
    joining_date = date.fromisoformat(joining_date_str)
    await offer_service.confirm_joining(application_id, current_user.id, joining_date, db)
    return {"message": "Joining date confirmed", "joining_date": joining_date_str}
