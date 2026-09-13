"""
Resume API — upload and parse student resumes.

POST /api/v1/resume/upload   — student uploads their resume (PDF/DOCX/TXT)
GET  /api/v1/resume/status   — check parse status
POST /api/v1/resume/reparse  — trigger re-parse of an existing resume
"""

import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import User, Student
from app.nlp.pipeline import process_resume
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/resume", tags=["Resume"])
settings = get_settings()

ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
    "text/plain": ".txt",
}
MAX_SIZE_BYTES = settings.MAX_RESUME_SIZE_MB * 1024 * 1024


def _get_upload_path(student_id: uuid.UUID, ext: str) -> Path:
    upload_dir = Path(settings.UPLOAD_DIR) / "resumes"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir / f"{student_id}{ext}"


async def _run_parse_pipeline(
    student_id: uuid.UUID,
    file_path: Path,
    overwrite: bool = True,
):
    """Run in background after file is saved."""
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        content = file_path.read_bytes()
        result = await process_resume(
            db=db,
            student_id=student_id,
            file_content=content,
            filename=file_path.name,
            overwrite_existing=overwrite,
        )
        if result.errors:
            import logging
            logging.getLogger(__name__).warning(
                "Resume parse errors for %s: %s", student_id, result.errors
            )


@router.post(
    "/upload",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload and parse resume",
)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a PDF, DOCX, or TXT resume.
    The file is saved immediately; NLP parsing runs as a background task.
    Returns accepted (202) — check /status for completion.
    """
    # Validate type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed: PDF, DOCX, TXT",
        )

    # Read & validate size
    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max {settings.MAX_RESUME_SIZE_MB} MB",
        )

    ext = ALLOWED_TYPES[content_type]
    file_path = _get_upload_path(current_user.id, ext)

    # Save file
    file_path.write_bytes(content)

    # Update student.resume_url immediately
    student_result = await db.execute(select(Student).where(Student.id == current_user.id))
    student = student_result.scalar_one_or_none()
    if student:
        student.resume_url = str(file_path)
        student.resume_parsed = False  # mark as pending
        await db.commit()

    # Kick off NLP in background
    background_tasks.add_task(
        _run_parse_pipeline,
        student_id=current_user.id,
        file_path=file_path,
        overwrite=True,
    )

    return {
        "message": "Resume uploaded. NLP parsing started in background.",
        "filename": file.filename,
        "size_bytes": len(content),
        "status": "processing",
    }


@router.get("/status", summary="Check resume parse status")
async def get_resume_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return current student's resume URL and parse status."""
    result = await db.execute(select(Student).where(Student.id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    return {
        "resume_url": student.resume_url,
        "resume_parsed": student.resume_parsed,
        "consent_resume_analysis": student.consent_resume_analysis,
    }


@router.post("/reparse", status_code=status.HTTP_202_ACCEPTED, summary="Re-run NLP on existing resume")
async def reparse_resume(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a fresh NLP parse on the student's already-uploaded resume."""
    result = await db.execute(select(Student).where(Student.id == current_user.id))
    student = result.scalar_one_or_none()

    if not student or not student.resume_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume uploaded yet",
        )

    file_path = Path(student.resume_url)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file not found on server. Please re-upload.",
        )

    student.resume_parsed = False
    await db.commit()

    background_tasks.add_task(
        _run_parse_pipeline,
        student_id=current_user.id,
        file_path=file_path,
        overwrite=True,
    )

    return MessageResponse(message="Re-parse started. Check /status for completion.")
