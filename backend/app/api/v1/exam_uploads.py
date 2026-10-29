"""
Exam Upload API — TPO uploads exam sheets (PDF/Excel/CSV),
system parses dynamic columns, computes ranks, and serves data
to TPO (full), Faculty (section), and Students (individual).

Routes:
  POST   /exam-uploads/upload       — TPO uploads a file
  GET    /exam-uploads               — List all uploads (TPO/admin)
  GET    /exam-uploads/{id}          — Full sheet detail + results
  GET    /exam-uploads/{id}/stats    — Statistics for an upload
  GET    /exam-uploads/my-results    — Student sees their own results
  GET    /exam-uploads/{id}/section  — Faculty sees section results
  DELETE /exam-uploads/{id}          — Delete an upload
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Query, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import User, Student
from app.services import exam_upload_service

router = APIRouter(prefix="/exam-uploads", tags=["Exam Uploads"])
settings = get_settings()

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.ms-excel": "xls",
    "text/csv": "csv",
    "application/csv": "csv",
    "application/vnd.ms-excel": "xls",
}
ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv"}
MAX_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


def _get_upload_dir() -> Path:
    upload_dir = Path(settings.UPLOAD_DIR) / "exam_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


# ─── TPO: Upload Exam Sheet ────────────────────────────────────────

@router.post("/upload", summary="Upload exam/assessment sheet (TPO/Admin)")
async def upload_exam_sheet(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    section: Optional[str] = Form(None),
    semester: Optional[int] = Form(None),
    exam_type: Optional[str] = Form(None),
    academic_year: Optional[str] = Form(None),
    rank_column: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    TPO/Admin uploads a PDF, Excel, or CSV file containing exam results.
    The system will parse it, extract all columns dynamically, match
    students by roll number, and compute rankings.
    """
    # Role check
    if current_user.role not in ("tpo", "admin", "faculty", "hod"):
        raise HTTPException(status_code=403, detail="Only TPO, Admin, or Faculty can upload exam sheets.")

    # Validate file type
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum {MAX_SIZE_BYTES // (1024*1024)}MB allowed.")

    # Save file
    file_id = uuid.uuid4()
    file_type = ext.lstrip(".")
    save_path = _get_upload_dir() / f"{file_id}{ext}"
    with open(save_path, "wb") as f:
        f.write(content)

    # Create upload record
    from app.models.exam_upload import ExamUpload
    upload = ExamUpload(
        id=file_id,
        title=title,
        description=description,
        uploaded_by=current_user.id,
        original_filename=file.filename,
        file_type=file_type,
        file_path=str(save_path),
        department=department,
        section=section,
        semester=semester,
        exam_type=exam_type,
        academic_year=academic_year,
        rank_column=rank_column,
        status="processing",
    )
    db.add(upload)
    await db.commit()
    await db.refresh(upload)

    # Process in background — parse, extract data, compute ranks
    # For now, process synchronously (small files)
    try:
        await exam_upload_service.process_exam_upload(db, upload.id)
        await db.refresh(upload)
    except Exception as e:
        # Already marked as failed inside the service
        pass

    return {
        "id": str(upload.id),
        "title": upload.title,
        "status": upload.status,
        "total_rows": upload.total_rows,
        "total_columns": upload.total_columns,
        "column_headers": upload.column_headers,
        "rank_column": upload.rank_column,
        "message": "File uploaded and processed successfully." if upload.status == "completed" else "File processing failed.",
    }


# ─── TPO/Admin: List All Uploads ────────────────────────────────────

@router.get("", summary="List all exam uploads")
async def list_uploads(
    department: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all exam uploads. TPO/Admin sees all, Faculty sees their department."""
    dept_filter = department
    if current_user.role in ("faculty", "hod"):
        # Faculty can only see their department's uploads
        from sqlalchemy import select
        stmt = select(Student).where(Student.id == current_user.id)
        # Actually, get faculty's department
        from app.models.user import Faculty
        stmt = select(Faculty).where(Faculty.id == current_user.id)
        result = await db.execute(stmt)
        fac = result.scalar_one_or_none()
        if fac:
            from app.models.user import Department
            dept_obj = await db.get(Department, fac.department_id)
            if dept_obj:
                dept_filter = dept_obj.name

    uploads = await exam_upload_service.list_uploads(db, department=dept_filter, section=section, limit=limit, offset=offset)
    return [
        {
            "id": str(u.id),
            "title": u.title,
            "description": u.description,
            "original_filename": u.original_filename,
            "file_type": u.file_type,
            "total_rows": u.total_rows,
            "total_columns": u.total_columns,
            "column_headers": u.column_headers,
            "department": u.department,
            "section": u.section,
            "semester": u.semester,
            "exam_type": u.exam_type,
            "academic_year": u.academic_year,
            "rank_column": u.rank_column,
            "status": u.status,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in uploads
    ]


# ─── Student: My Results (MUST be before /{upload_id} routes) ────────

@router.get("/my/results", summary="Student views their own exam results")
async def get_my_results(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Student sees their own results across all uploaded exams, matched by roll number or student_id."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can view their own results.")

    from sqlalchemy import select
    stmt = select(Student).where(Student.id == current_user.id)
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")

    results = await exam_upload_service.get_student_results(
        db,
        student_id=student.id,
        roll_number=student.roll_number,
    )
    return results


# ─── Full Upload Detail ─────────────────────────────────────────────

@router.get("/{upload_id}", summary="Get full exam upload details with all results")
async def get_upload_detail(
    upload_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full details of an uploaded exam sheet including all student results and ranks."""
    data = await exam_upload_service.get_upload_detail(db, upload_id)
    if not data:
        raise HTTPException(status_code=404, detail="Upload not found")

    upload = data["upload"]
    results = data["results"]

    return {
        "upload": {
            "id": str(upload.id),
            "title": upload.title,
            "description": upload.description,
            "original_filename": upload.original_filename,
            "file_type": upload.file_type,
            "total_rows": upload.total_rows,
            "total_columns": upload.total_columns,
            "column_headers": upload.column_headers,
            "department": upload.department,
            "section": upload.section,
            "semester": upload.semester,
            "exam_type": upload.exam_type,
            "academic_year": upload.academic_year,
            "rank_column": upload.rank_column,
            "status": upload.status,
            "created_at": upload.created_at.isoformat() if upload.created_at else None,
        },
        "results": [
            {
                "id": str(r.id),
                "roll_number": r.roll_number,
                "student_name": r.student_name,
                "student_id": str(r.student_id) if r.student_id else None,
                "row_data": r.row_data,
                "rank": r.rank,
                "section": r.section,
                "department": r.department,
            }
            for r in results
        ],
        "total": len(results),
    }


# ─── Upload Statistics ───────────────────────────────────────────────

@router.get("/{upload_id}/stats", summary="Get exam upload statistics")
async def get_upload_stats(
    upload_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get statistics (avg, max, min, pass/fail count) for an uploaded exam."""
    stats = await exam_upload_service.get_upload_stats(db, upload_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Upload not found or no rankable column detected.")
    return stats


# ─── Faculty: Section Results ─────────────────────────────────────────

@router.get("/{upload_id}/section", summary="Faculty views section results")
async def get_section_results(
    upload_id: uuid.UUID,
    section: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Faculty views results for their section/department within a specific upload."""
    results = await exam_upload_service.get_section_results(
        db, upload_id, section=section, department=department
    )
    return [
        {
            "id": str(r.id),
            "roll_number": r.roll_number,
            "student_name": r.student_name,
            "row_data": r.row_data,
            "rank": r.rank,
            "section": r.section,
            "department": r.department,
        }
        for r in results
    ]


# ─── Delete Upload ───────────────────────────────────────────────────

@router.delete("/{upload_id}", summary="Delete an exam upload")
async def delete_upload(
    upload_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an exam upload and all associated results. TPO/Admin only."""
    if current_user.role not in ("tpo", "admin"):
        raise HTTPException(status_code=403, detail="Only TPO/Admin can delete uploads.")

    success = await exam_upload_service.delete_upload(db, upload_id)
    if not success:
        raise HTTPException(status_code=404, detail="Upload not found.")
    return {"message": "Upload deleted successfully."}
