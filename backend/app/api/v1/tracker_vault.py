"""
Application Tracker & Document Vault API.

Sprint 3 — Anjula

Endpoints:
  GET    /tracker/applications        — Student application tracker
  GET    /tracker/timeline/{app_id}   — Application timeline events
  POST   /vault/documents             — Upload document to vault
  GET    /vault/documents             — List my documents
  GET    /vault/documents/{id}        — Get document detail
  PATCH  /vault/documents/{id}        — Update document metadata
  DELETE /vault/documents/{id}        — Delete document
  PATCH  /vault/documents/{id}/verify — TPO verifies a document
  GET    /vault/shared                — TPO view: shared documents
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker, get_current_student
from app.models.user import User
from app.schemas.anjula_sprint3 import (
    ApplicationTrackerResponse, TimelineEventResponse,
    DocumentUpload, DocumentResponse, DocumentUpdateRequest,
)
from app.schemas.common import MessageResponse, PaginatedResponse, PaginationMeta
from app.services import anjula_sprint3_service as svc

router = APIRouter(tags=["Application Tracker & Document Vault"])

_tpo_admin = RoleChecker(["tpo", "admin"])
_student_or_tpo = RoleChecker(["student", "tpo", "admin"])


# ─── Application Tracker ─────────────────────────────────────────

@router.get("/tracker/applications", response_model=list[ApplicationTrackerResponse], summary="My application tracker")
async def my_applications(
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    tracker_data = await svc.get_student_application_tracker(db, current_user.id)
    return [ApplicationTrackerResponse(
        application_id=t["application_id"],
        drive_title=t["drive_title"],
        company_name=t["company_name"],
        role=t["role"],
        current_status=t["current_status"],
        applied_at=t["applied_at"],
        last_updated=t["last_updated"],
        timeline=[TimelineEventResponse(
            id=e.id, application_id=e.application_id,
            event_type=e.event_type, from_status=e.from_status,
            to_status=e.to_status, description=e.description,
            actor_name=f"{e.actor.first_name} {e.actor.last_name}" if e.actor else None,
            metadata_payload=e.metadata_payload,
            created_at=e.created_at,
        ) for e in t["timeline"]],
        next_steps=t["next_steps"],
    ) for t in tracker_data]


@router.get("/tracker/timeline/{application_id}", response_model=list[TimelineEventResponse], summary="Application timeline")
async def application_timeline(
    application_id: uuid.UUID,
    current_user: User = Depends(_student_or_tpo),
    db: AsyncSession = Depends(get_db),
):
    events = await svc.get_application_timeline(db, application_id)
    return [TimelineEventResponse(
        id=e.id, application_id=e.application_id,
        event_type=e.event_type, from_status=e.from_status,
        to_status=e.to_status, description=e.description,
        actor_name=f"{e.actor.first_name} {e.actor.last_name}" if e.actor else None,
        metadata_payload=e.metadata_payload,
        created_at=e.created_at,
    ) for e in events]


# ─── Document Vault ──────────────────────────────────────────────

@router.post("/vault/documents", response_model=DocumentResponse, summary="Upload document to vault")
async def upload_doc(
    data: DocumentUpload,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    doc = await svc.upload_document(db, current_user.id, data)
    return DocumentResponse(
        id=doc.id, student_id=doc.student_id, document_type=doc.document_type,
        title=doc.title, description=doc.description, file_url=doc.file_url,
        file_name=doc.file_name, file_size_bytes=doc.file_size_bytes,
        mime_type=doc.mime_type, is_verified=doc.is_verified,
        tags=doc.tags or [], expiry_date=doc.expiry_date,
        is_shared_with_tpo=doc.is_shared_with_tpo, created_at=doc.created_at,
    )


@router.get("/vault/documents", response_model=list[DocumentResponse], summary="My documents")
async def list_my_docs(
    document_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    docs = await svc.list_student_documents(db, current_user.id, document_type)
    return [DocumentResponse(
        id=d.id, student_id=d.student_id, document_type=d.document_type,
        title=d.title, description=d.description, file_url=d.file_url,
        file_name=d.file_name, file_size_bytes=d.file_size_bytes,
        mime_type=d.mime_type, is_verified=d.is_verified,
        verified_at=d.verified_at, tags=d.tags or [],
        expiry_date=d.expiry_date, is_shared_with_tpo=d.is_shared_with_tpo,
        created_at=d.created_at,
    ) for d in docs]


@router.get("/vault/documents/{doc_id}", response_model=DocumentResponse, summary="Get document")
async def get_doc(
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    d = await svc.get_document(db, doc_id, current_user.id)
    return DocumentResponse(
        id=d.id, student_id=d.student_id, document_type=d.document_type,
        title=d.title, description=d.description, file_url=d.file_url,
        file_name=d.file_name, file_size_bytes=d.file_size_bytes,
        mime_type=d.mime_type, is_verified=d.is_verified,
        verified_at=d.verified_at, tags=d.tags or [],
        expiry_date=d.expiry_date, is_shared_with_tpo=d.is_shared_with_tpo,
        created_at=d.created_at,
    )


@router.patch("/vault/documents/{doc_id}", response_model=DocumentResponse, summary="Update document")
async def update_doc(
    doc_id: uuid.UUID,
    data: DocumentUpdateRequest,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    d = await svc.update_document(db, doc_id, current_user.id, data)
    return DocumentResponse(
        id=d.id, student_id=d.student_id, document_type=d.document_type,
        title=d.title, description=d.description, file_url=d.file_url,
        file_name=d.file_name, file_size_bytes=d.file_size_bytes,
        mime_type=d.mime_type, is_verified=d.is_verified,
        verified_at=d.verified_at, tags=d.tags or [],
        expiry_date=d.expiry_date, is_shared_with_tpo=d.is_shared_with_tpo,
        created_at=d.created_at,
    )


@router.delete("/vault/documents/{doc_id}", response_model=MessageResponse, summary="Delete document")
async def delete_doc(
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    await svc.delete_document(db, doc_id, current_user.id)
    return MessageResponse(message="Document deleted")


@router.patch("/vault/documents/{doc_id}/verify", response_model=DocumentResponse, summary="Verify document (TPO)")
async def verify_doc(
    doc_id: uuid.UUID,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    d = await svc.verify_document(db, doc_id, current_user.id)
    return DocumentResponse(
        id=d.id, student_id=d.student_id, document_type=d.document_type,
        title=d.title, description=d.description, file_url=d.file_url,
        file_name=d.file_name, file_size_bytes=d.file_size_bytes,
        mime_type=d.mime_type, is_verified=d.is_verified,
        verified_at=d.verified_at, tags=d.tags or [],
        expiry_date=d.expiry_date, is_shared_with_tpo=d.is_shared_with_tpo,
        created_at=d.created_at,
    )


@router.get("/vault/shared", response_model=PaginatedResponse, summary="TPO: shared documents")
async def shared_docs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    docs, total = await svc.list_shared_documents(db, page, per_page)
    items = [DocumentResponse(
        id=d.id, student_id=d.student_id, document_type=d.document_type,
        title=d.title, description=d.description, file_url=d.file_url,
        file_name=d.file_name, file_size_bytes=d.file_size_bytes,
        mime_type=d.mime_type, is_verified=d.is_verified,
        verified_at=d.verified_at, tags=d.tags or [],
        expiry_date=d.expiry_date, is_shared_with_tpo=d.is_shared_with_tpo,
        created_at=d.created_at,
    ) for d in docs]
    return PaginatedResponse(
        data=[i.model_dump() for i in items],
        pagination=PaginationMeta(page=page, per_page=per_page, total=total),
    )
