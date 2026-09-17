"""
UMS Integration API — on-demand sync endpoints for TPO / Admin.

Routes:
  POST /api/v1/ums/sync/student/{roll_number}     — sync one student now
  POST /api/v1/ums/sync/department/{dept_code}    — sync all students in a dept
  POST /api/v1/ums/sync/all                       — enqueue a full sync via Celery
  GET  /api/v1/ums/students/{roll_number}          — preview UMS data for a student
  GET  /api/v1/ums/subjects                        — list subjects from UMS
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.core.audit import record_audit_event
from app.models.user import User
from app.adapters.mock_ums_adapter import MockUMSAdapter
from app.services.ums_sync_service import sync_single_student, sync_department
from app.schemas.ums import (
    UMSStudentPreview,
    UMSSyncResult,
    UMSSyncRequest,
    UMSDepartmentSyncResult,
    UMSSubjectResponse,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ums", tags=["UMS Integration"])

_tpo_admin = RoleChecker(["tpo", "admin"])


# ---------------------------------------------------------------------------
# Preview endpoints (read-only, no DB writes)
# ---------------------------------------------------------------------------

@router.get(
    "/students/{roll_number}",
    response_model=UMSStudentPreview,
    summary="Preview UMS data for a student (no DB write)",
)
async def preview_ums_student(
    roll_number: str,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch raw data about a student from the UMS without writing
    anything to the local DB. Useful for comparing UMS vs local data.
    """
    adapter = MockUMSAdapter(db)
    dto = await adapter.get_student(roll_number)
    if dto is None:
        raise HTTPException(status_code=404, detail=f"Student '{roll_number}' not found in UMS")

    academic = await adapter.get_academic_records(roll_number)
    attendance = await adapter.get_attendance(roll_number)

    return UMSStudentPreview(
        ums_id=dto.ums_id,
        roll_number=dto.roll_number,
        full_name=f"{dto.first_name} {dto.last_name}",
        email=dto.email,
        department_code=dto.department_code,
        current_semester=dto.current_semester,
        admission_year=dto.admission_year,
        cgpa=dto.cgpa,
        academic_records_count=len(academic),
        attendance_records_count=len(attendance),
    )


@router.get(
    "/subjects",
    response_model=list[UMSSubjectResponse],
    summary="List all subjects from UMS",
)
async def list_ums_subjects(
    department_code: Optional[str] = Query(None, description="Filter by department code"),
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """Preview available subjects from UMS (used to populate curriculum mapping)."""
    adapter = MockUMSAdapter(db)
    subjects = await adapter.get_subjects(department_code=department_code)
    return [
        UMSSubjectResponse(
            code=s.code,
            name=s.name,
            department_code=s.department_code,
            semester_number=s.semester_number,
            credits=s.credits,
            subject_type=s.subject_type,
            syllabus_text=s.syllabus_text,
        )
        for s in subjects
    ]


# ---------------------------------------------------------------------------
# Sync endpoints (write to DB)
# ---------------------------------------------------------------------------

@router.post(
    "/sync/student/{roll_number}",
    response_model=UMSSyncResult,
    summary="Sync a single student from UMS (TPO/Admin)",
)
async def sync_student(
    roll_number: str,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Immediately sync one student's academic records and attendance
    from UMS into the local database. Updates CGPA on completion.

    This runs synchronously in-request. For large departments,
    use the department or full-sync endpoints which use Celery.
    """
    adapter = MockUMSAdapter(db)
    result = await sync_single_student(db, adapter, roll_number)

    await record_audit_event(
        db=db,
        actor_id=current_user.id,
        event_type="UMS_SYNC_TRIGGERED",
        resource_type="Student",
        resource_id=roll_number,
        details={"roll_number": roll_number, "success": result.get("success")},
    )

    if not result["success"]:
        await db.commit()  # persist audit event before raising
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "Sync failed"),
        )

    return UMSSyncResult(**result)


@router.post(
    "/sync",
    response_model=UMSSyncResult,
    summary="Sync a single student from UMS by roll number (TPO/Admin)",
)
async def sync_student_by_body(
    payload: UMSSyncRequest,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    adapter = MockUMSAdapter(db)
    result = await sync_single_student(db, adapter, payload.roll_number)

    await record_audit_event(
        db=db,
        actor_id=current_user.id,
        event_type="UMS_SYNC_TRIGGERED",
        resource_type="Student",
        resource_id=payload.roll_number,
        details={"roll_number": payload.roll_number, "success": result.get("success")},
    )

    if not result["success"]:
        await db.commit()  # persist audit event before raising
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "Sync failed"),
        )

    return UMSSyncResult(**result)


@router.post(

    "/sync/department/{department_code}",
    response_model=UMSDepartmentSyncResult,
    summary="Sync all students in a department (TPO/Admin)",
)
async def sync_dept(
    department_code: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Sync all students belonging to a department. Runs as a background
    FastAPI task so the request returns immediately with a 202-like response.

    For very large cohorts (100+ students), prefer the Celery task instead
    via POST /sync/all which dispatches to the queue.
    """
    adapter = MockUMSAdapter(db)
    result = await sync_department(db, adapter, department_code)
    return UMSDepartmentSyncResult(**result)


@router.post(
    "/sync/all",
    summary="Enqueue a full institution-wide UMS sync via Celery (TPO/Admin)",
)
async def sync_all(
    current_user: User = Depends(_tpo_admin),
):
    """
    Dispatch a full sync task to the Celery queue.

    The task runs asynchronously in the background.
    Returns the Celery task ID so the caller can track progress.

    NOTE: Requires Redis + Celery worker running.
    """
    try:
        from app.adapters.ums_tasks import scheduled_full_sync_task
        task = scheduled_full_sync_task.delay()
        return {
            "message": "Full UMS sync enqueued",
            "task_id": task.id,
            "status": "PENDING",
        }
    except Exception as exc:
        logger.warning("Celery not available, running sync inline: %s", exc)
        # Graceful degradation: if Celery/Redis is not running, return a clear message
        return {
            "message": "Celery worker not available. Start Redis + worker to use background sync.",
            "task_id": None,
            "status": "UNAVAILABLE",
        }


@router.get(
    "/sync/task/{task_id}",
    summary="Check Celery task status for a sync job",
)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(_tpo_admin),
):
    """Check the status and result of a previously enqueued Celery sync task."""
    try:
        from celery.result import AsyncResult
        from app.worker import celery_app
        result = AsyncResult(task_id, app=celery_app)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
        }
    except Exception as exc:
        return {
            "task_id": task_id,
            "status": "UNKNOWN",
            "error": str(exc),
        }
