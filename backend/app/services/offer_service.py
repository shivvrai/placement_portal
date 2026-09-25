"""
Offer Service - Manage offer letter upload, download, accept/decline.
"""

import uuid
from datetime import datetime, date, timezone
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.placement import Application
from app.core.audit import record_audit_event
from app.api.v1.notifications import create_notification

UPLOAD_DIR = Path("uploads/offer_letters")
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class OfferService:

    async def _get_application(self, db: AsyncSession, application_id: uuid.UUID) -> Application:
        from app.models.user import Student
        result = await db.execute(
            select(Application)
            .options(
                selectinload(Application.drive).selectinload(Application.drive.property.mapper.class_.company),
                selectinload(Application.student),
            )
            .where(Application.id == application_id)
        )
        app = result.scalar_one_or_none()
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        return app

    async def upload_letter(self, application_id: uuid.UUID, file: UploadFile, tpo_id: uuid.UUID, db: AsyncSession) -> str:
        """Validate, save PDF, update DB, notify student."""
        filename_lower = (file.filename or "").lower()
        content_type = file.content_type or ""
        if "pdf" not in content_type and not filename_lower.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are accepted")

        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File exceeds 5MB limit")

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{application_id}.pdf"
        file_path = UPLOAD_DIR / filename
        with open(file_path, "wb") as f:
            f.write(contents)

        relative_path = f"/uploads/offer_letters/{filename}"

        result = await db.execute(
            select(Application)
            .options(
                selectinload(Application.drive),
            )
            .where(Application.id == application_id)
        )
        app = result.scalar_one_or_none()
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        app.offer_letter_url = relative_path
        app.offer_letter_uploaded_at = utcnow()
        app.offer_letter_status = "uploaded"
        app.updated_at = utcnow()

        await db.flush()

        company_name = "Company"
        if app.drive:
            try:
                if app.drive.company:
                    company_name = app.drive.company.name
            except Exception:
                pass

        await create_notification(
            db=db, user_id=app.student_id,
            title=f"Offer Letter Ready: {company_name}",
            message=f"Your offer letter from {company_name} is now available. Please review and respond.",
            type="success", link="/student/drives",
        )

        await db.commit()
        return relative_path

    async def accept_offer(self, application_id: uuid.UUID, student_id: uuid.UUID, db: AsyncSession) -> None:
        result = await db.execute(select(Application).where(Application.id == application_id))
        app = result.scalar_one_or_none()
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        if app.student_id != student_id:
            raise HTTPException(status_code=403, detail="Not authorized to accept this offer")
        if app.offer_letter_status != "uploaded":
            raise HTTPException(status_code=400, detail=f"Offer is not in uploaded state (current: {app.offer_letter_status})")

        app.offer_letter_status = "accepted"
        app.offer_accepted_at = utcnow()
        app.updated_at = utcnow()
        await db.commit()

    async def decline_offer(self, application_id: uuid.UUID, student_id: uuid.UUID, reason: str, db: AsyncSession) -> None:
        result = await db.execute(select(Application).where(Application.id == application_id))
        app = result.scalar_one_or_none()
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        if app.student_id != student_id:
            raise HTTPException(status_code=403, detail="Not authorized to decline this offer")
        if app.offer_letter_status not in ("uploaded", "accepted"):
            raise HTTPException(status_code=400, detail="No offer letter to decline")

        old_status = app.offer_letter_status
        app.offer_letter_status = "declined"
        app.offer_declined_reason = reason
        app.updated_at = utcnow()

        await db.flush()
        await record_audit_event(
            db=db, actor_id=student_id, event_type="APPLICATION_STATUS_CHANGE",
            resource_type="Application", resource_id=str(application_id),
            details={"event": "OFFER_DECLINED", "old_offer_status": old_status, "reason": reason},
        )
        await db.commit()

    async def confirm_joining(self, application_id: uuid.UUID, student_id: uuid.UUID, joining_date: date, db: AsyncSession) -> None:
        result = await db.execute(select(Application).where(Application.id == application_id))
        app = result.scalar_one_or_none()
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        if app.student_id != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        app.offer_joining_confirmed = True
        app.offer_joining_date_confirmed = joining_date
        app.updated_at = utcnow()
        await db.commit()

    async def generate_pending_summary(self, academic_year: str, db: AsyncSession) -> dict:
        from sqlalchemy import func
        from app.models.placement import PlacementDrive
        stmt = (
            select(Application.offer_letter_status, func.count(Application.id).label("cnt"))
            .join(PlacementDrive, Application.drive_id == PlacementDrive.id)
            .where(Application.status == "selected")
            .where(PlacementDrive.academic_year == academic_year)
            .group_by(Application.offer_letter_status)
        )
        result = await db.execute(stmt)
        counts = {r.offer_letter_status: r.cnt for r in result.all()}
        return {
            "pending": counts.get("pending", 0),
            "uploaded": counts.get("uploaded", 0),
            "accepted": counts.get("accepted", 0),
            "declined": counts.get("declined", 0),
            "total_selected": sum(counts.values()),
        }


offer_service = OfferService()
