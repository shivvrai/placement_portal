"""
Service layer — Company Reviews & Insights, Application Tracker, Document Vault.

Sprint 3 — Anjula
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.company_reviews import CompanyReview, CompanyInsight
from app.models.document_vault import StudentDocument
from app.models.application_timeline import ApplicationTimelineEvent
from app.models.placement import Application, PlacementDrive
from app.schemas.anjula_sprint3 import (
    CompanyReviewCreate, DocumentUpload, DocumentUpdateRequest,
)


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ═══════════════════════════════════════════════════════════════════
# COMPANY REVIEWS & INSIGHTS
# ═══════════════════════════════════════════════════════════════════

async def create_company_review(db: AsyncSession, student_id: uuid.UUID, data: CompanyReviewCreate) -> CompanyReview:
    review = CompanyReview(
        student_id=student_id,
        company_name=data.company_name,
        company_id=data.company_id,
        role=data.role,
        review_type=data.review_type,
        overall_rating=data.overall_rating,
        work_culture_rating=data.work_culture_rating,
        growth_rating=data.growth_rating,
        compensation_rating=data.compensation_rating,
        interview_rating=data.interview_rating,
        pros=data.pros,
        cons=data.cons,
        advice=data.advice,
        interview_process=data.interview_process,
        salary_range=data.salary_range,
        is_anonymous=data.is_anonymous,
    )
    db.add(review)
    await db.flush()

    # Update aggregated company insights
    await _refresh_company_insight(db, data.company_name)

    return review


async def _refresh_company_insight(db: AsyncSession, company_name: str):
    """Recompute aggregated insight for a company after a new review."""
    result = await db.execute(
        select(CompanyReview).where(CompanyReview.company_name == company_name)
    )
    reviews = list(result.scalars().all())

    if not reviews:
        return

    avg_rating = sum(r.overall_rating for r in reviews) / len(reviews)
    roles = list(set(r.role for r in reviews))

    # Find or create insight
    insight_result = await db.execute(
        select(CompanyInsight).where(CompanyInsight.company_name == company_name)
    )
    insight = insight_result.scalar_one_or_none()
    if not insight:
        insight = CompanyInsight(company_name=company_name)
        db.add(insight)

    insight.avg_rating = round(avg_rating, 2)
    insight.total_reviews = len(reviews)
    insight.common_roles = roles[:10]
    insight.updated_at = _utcnow()
    await db.flush()


async def list_company_reviews(
    db: AsyncSession,
    company_name: Optional[str] = None,
    review_type: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[CompanyReview], int]:
    q = select(CompanyReview).where(CompanyReview.is_approved == True)  # noqa: E712
    if company_name:
        q = q.where(CompanyReview.company_name.ilike(f"%{company_name}%"))
    if review_type:
        q = q.where(CompanyReview.review_type == review_type)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(CompanyReview.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(q)).scalars().all()
    return list(rows), total


async def get_company_insight(db: AsyncSession, company_name: str) -> CompanyInsight:
    result = await db.execute(
        select(CompanyInsight).where(CompanyInsight.company_name.ilike(f"%{company_name}%"))
    )
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company insight not found")
    return insight


async def list_company_insights(db: AsyncSession, page: int = 1, per_page: int = 20) -> tuple[list[CompanyInsight], int]:
    q = select(CompanyInsight)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(CompanyInsight.avg_rating.desc()).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(q)).scalars().all()
    return list(rows), total


async def upvote_review(db: AsyncSession, review_id: uuid.UUID) -> CompanyReview:
    result = await db.execute(select(CompanyReview).where(CompanyReview.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    review.upvotes += 1
    await db.flush()
    return review


# ═══════════════════════════════════════════════════════════════════
# APPLICATION TRACKER & TIMELINE
# ═══════════════════════════════════════════════════════════════════

async def record_timeline_event(
    db: AsyncSession,
    application_id: uuid.UUID,
    student_id: uuid.UUID,
    event_type: str,
    from_status: Optional[str],
    to_status: str,
    description: Optional[str] = None,
    actor_id: Optional[uuid.UUID] = None,
    metadata: Optional[dict] = None,
) -> ApplicationTimelineEvent:
    event = ApplicationTimelineEvent(
        application_id=application_id,
        student_id=student_id,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        description=description,
        actor_id=actor_id,
        metadata_payload=metadata,
    )
    db.add(event)
    await db.flush()
    return event


async def get_application_timeline(db: AsyncSession, application_id: uuid.UUID) -> list[ApplicationTimelineEvent]:
    result = await db.execute(
        select(ApplicationTimelineEvent)
        .where(ApplicationTimelineEvent.application_id == application_id)
        .order_by(ApplicationTimelineEvent.created_at.asc())
    )
    return list(result.scalars().all())


async def get_student_application_tracker(db: AsyncSession, student_id: uuid.UUID) -> list[dict]:
    """Get all applications for a student with their timeline events."""
    result = await db.execute(
        select(Application)
        .where(Application.student_id == student_id)
        .order_by(Application.applied_at.desc())
    )
    applications = list(result.scalars().all())

    tracker_data = []
    for app in applications:
        # Get drive info
        drive_result = await db.execute(
            select(PlacementDrive).where(PlacementDrive.id == app.drive_id)
        )
        drive = drive_result.scalar_one_or_none()

        # Get timeline events
        timeline = await get_application_timeline(db, app.id)

        tracker_data.append({
            "application_id": app.id,
            "drive_title": drive.title if drive else "Unknown Drive",
            "company_name": drive.company.name if drive and hasattr(drive, 'company') and drive.company else "Unknown",
            "role": drive.role if drive else "Unknown",
            "current_status": app.status,
            "applied_at": app.applied_at,
            "last_updated": timeline[-1].created_at if timeline else app.applied_at,
            "timeline": timeline,
            "next_steps": _get_next_steps(app.status),
        })

    return tracker_data


def _get_next_steps(current_status: str) -> str:
    """Provide helpful next-step guidance based on current application status."""
    steps = {
        "applied": "Your application is being reviewed. Prepare for the Online Assessment.",
        "shortlisted": "Congratulations! You've been shortlisted. Prepare for the technical interview.",
        "in_progress": "Interview rounds are in progress. Stay prepared for the next round.",
        "selected": "🎉 You've been selected! Check for your offer letter in the Document Vault.",
        "rejected": "Don't be discouraged. Review your interview experience and keep preparing.",
        "withdrawn": "Application was withdrawn. You can apply to other opportunities.",
    }
    return steps.get(current_status, "Check with TPO for updates.")


# ═══════════════════════════════════════════════════════════════════
# DOCUMENT VAULT
# ═══════════════════════════════════════════════════════════════════

async def upload_document(db: AsyncSession, student_id: uuid.UUID, data: DocumentUpload) -> StudentDocument:
    doc = StudentDocument(
        student_id=student_id,
        document_type=data.document_type,
        title=data.title,
        description=data.description,
        file_url=data.file_url,
        file_name=data.file_name,
        file_size_bytes=data.file_size_bytes,
        mime_type=data.mime_type,
        tags=data.tags,
        expiry_date=data.expiry_date,
        is_shared_with_tpo=data.is_shared_with_tpo,
    )
    db.add(doc)
    await db.flush()
    return doc


async def list_student_documents(
    db: AsyncSession,
    student_id: uuid.UUID,
    document_type: Optional[str] = None,
) -> list[StudentDocument]:
    q = select(StudentDocument).where(StudentDocument.student_id == student_id)
    if document_type:
        q = q.where(StudentDocument.document_type == document_type)
    q = q.order_by(StudentDocument.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_document(db: AsyncSession, doc_id: uuid.UUID, student_id: uuid.UUID) -> StudentDocument:
    result = await db.execute(
        select(StudentDocument).where(
            StudentDocument.id == doc_id,
            StudentDocument.student_id == student_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


async def update_document(
    db: AsyncSession, doc_id: uuid.UUID, student_id: uuid.UUID, data: DocumentUpdateRequest
) -> StudentDocument:
    doc = await get_document(db, doc_id, student_id)
    if data.title is not None:
        doc.title = data.title
    if data.description is not None:
        doc.description = data.description
    if data.tags is not None:
        doc.tags = data.tags
    if data.is_shared_with_tpo is not None:
        doc.is_shared_with_tpo = data.is_shared_with_tpo
    doc.updated_at = _utcnow()
    await db.flush()
    return doc


async def delete_document(db: AsyncSession, doc_id: uuid.UUID, student_id: uuid.UUID):
    doc = await get_document(db, doc_id, student_id)
    await db.delete(doc)
    await db.flush()


async def verify_document(db: AsyncSession, doc_id: uuid.UUID, verifier_id: uuid.UUID) -> StudentDocument:
    """TPO verifies a student document."""
    result = await db.execute(select(StudentDocument).where(StudentDocument.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    doc.is_verified = True
    doc.verified_by = verifier_id
    doc.verified_at = _utcnow()
    await db.flush()
    return doc


async def list_shared_documents(db: AsyncSession, page: int = 1, per_page: int = 50) -> tuple[list[StudentDocument], int]:
    """TPO view: all documents shared by students."""
    q = select(StudentDocument).where(StudentDocument.is_shared_with_tpo == True)  # noqa: E712
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(StudentDocument.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(q)).scalars().all()
    return list(rows), total
