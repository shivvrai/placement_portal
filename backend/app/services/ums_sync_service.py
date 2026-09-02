"""
UMS Sync Service — orchestrates syncing student data from UMS into local DB.

Called by:
  - Celery tasks (background / scheduled sync)
  - API endpoint (on-demand manual sync by TPO)

This service handles upsert logic: it creates new records if they don't
exist or updates them with fresh UMS data.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.adapters.ums_adapter import UMSAdapter, StudentDTO
from app.models.user import Student, Department
from app.models.academic import Subject, AcademicRecord, Attendance, Semester

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _get_or_create_semester(
    db: AsyncSession,
    semester_number: int,
) -> Semester:
    """Get an existing Semester row or create a placeholder for this number."""
    result = await db.execute(
        select(Semester).where(Semester.number == semester_number)
    )
    sem = result.scalar_one_or_none()
    if sem:
        return sem

    sem = Semester(
        id=uuid.uuid4(),
        name=f"Semester {semester_number}",
        number=semester_number,
        academic_year="2025-26",
        is_current=(semester_number == 6),
    )
    db.add(sem)
    await db.flush()
    return sem


async def _get_or_create_subject(
    db: AsyncSession,
    subject_code: str,
    subject_name: str,
    semester_number: int,
    dept_id: Optional[uuid.UUID],
) -> Subject:
    """Upsert a Subject row by code."""
    result = await db.execute(
        select(Subject).where(Subject.code == subject_code)
    )
    subj = result.scalar_one_or_none()
    if subj:
        return subj

    subj = Subject(
        id=uuid.uuid4(),
        code=subject_code,
        name=subject_name,
        semester_number=semester_number,
        department_id=dept_id,
        credits=3,  # default — real UMS would provide this
        subject_type="core",
    )
    db.add(subj)
    await db.flush()
    return subj


# ---------------------------------------------------------------------------
# Public sync functions
# ---------------------------------------------------------------------------

async def sync_student_academic_records(
    db: AsyncSession,
    adapter: UMSAdapter,
    student: Student,
) -> dict:
    """
    Sync academic records from UMS → local AcademicRecord table.

    Returns a summary dict with counts of created/updated/skipped records.
    """
    roll = student.roll_number
    records_dto = await adapter.get_academic_records(roll)

    created = updated = skipped = 0

    for dto in records_dto:
        sem = await _get_or_create_semester(db, dto.semester_number)
        subj = await _get_or_create_subject(
            db,
            dto.subject_code,
            dto.subject_name,
            dto.semester_number,
            student.department_id,
        )

        result = await db.execute(
            select(AcademicRecord).where(
                AcademicRecord.student_id == student.id,
                AcademicRecord.subject_id == subj.id,
                AcademicRecord.semester_id == sem.id,
            )
        )
        rec = result.scalar_one_or_none()

        if rec is None:
            rec = AcademicRecord(
                id=uuid.uuid4(),
                student_id=student.id,
                subject_id=subj.id,
                semester_id=sem.id,
                grade=dto.grade,
                grade_points=dto.grade_points,
                marks=dto.marks,
                max_marks=dto.max_marks,
                status=dto.status,
            )
            db.add(rec)
            created += 1
        else:
            if rec.grade != dto.grade or rec.marks != dto.marks:
                rec.grade = dto.grade
                rec.grade_points = dto.grade_points
                rec.marks = dto.marks
                rec.max_marks = dto.max_marks
                rec.status = dto.status
                updated += 1
            else:
                skipped += 1

    await db.flush()
    return {"created": created, "updated": updated, "skipped": skipped, "total": len(records_dto)}


async def sync_student_attendance(
    db: AsyncSession,
    adapter: UMSAdapter,
    student: Student,
) -> dict:
    """
    Sync attendance data from UMS → local Attendance table.
    """
    roll = student.roll_number
    att_dtos = await adapter.get_attendance(roll)

    created = updated = skipped = 0

    for dto in att_dtos:
        sem = await _get_or_create_semester(db, dto.semester_number)
        subj = await _get_or_create_subject(
            db,
            dto.subject_code,
            dto.subject_code,  # use code as name fallback
            dto.semester_number,
            student.department_id,
        )

        result = await db.execute(
            select(Attendance).where(
                Attendance.student_id == student.id,
                Attendance.subject_id == subj.id,
                Attendance.semester_id == sem.id,
            )
        )
        att = result.scalar_one_or_none()

        if att is None:
            att = Attendance(
                id=uuid.uuid4(),
                student_id=student.id,
                subject_id=subj.id,
                semester_id=sem.id,
                total_classes=dto.total_classes,
                attended=dto.attended,
                last_updated=utcnow(),
            )
            db.add(att)
            created += 1
        else:
            if att.total_classes != dto.total_classes or att.attended != dto.attended:
                att.total_classes = dto.total_classes
                att.attended = dto.attended
                att.last_updated = utcnow()
                updated += 1
            else:
                skipped += 1

    await db.flush()
    return {"created": created, "updated": updated, "skipped": skipped, "total": len(att_dtos)}


async def update_student_cgpa(
    db: AsyncSession,
    student: Student,
) -> Optional[float]:
    """
    Re-compute CGPA from AcademicRecord rows in the DB.
    Only considers records with a non-null grade_points value.
    """
    result = await db.execute(
        select(AcademicRecord).where(
            AcademicRecord.student_id == student.id,
            AcademicRecord.grade_points.is_not(None),
        )
    )
    records = result.scalars().all()

    if not records:
        return None

    avg = round(sum(float(r.grade_points) for r in records) / len(records), 2)
    student.cgpa = avg
    student.updated_at = utcnow()
    await db.flush()
    logger.info("Updated CGPA for %s → %.2f", student.roll_number, avg)
    return avg


async def sync_single_student(
    db: AsyncSession,
    adapter: UMSAdapter,
    roll_number: str,
) -> dict:
    """
    Full sync pipeline for one student:
      1. Verify the student exists in local DB
      2. Sync academic records
      3. Sync attendance
      4. Recompute CGPA
      5. Return a result summary

    This is the main entry point for both the API endpoint
    and the Celery task.
    """
    # ── 1. Find the student in local DB ──────────────────────────────────────
    result = await db.execute(
        select(Student).where(Student.roll_number == roll_number)
    )
    student = result.scalar_one_or_none()

    if student is None:
        logger.warning("sync_single_student: %s not found in DB", roll_number)
        return {
            "success": False,
            "roll_number": roll_number,
            "error": "Student not found in local database",
        }

    # ── 2. Verify with UMS adapter ────────────────────────────────────────────
    ums_ok = await adapter.sync_student(roll_number)
    if not ums_ok:
        return {
            "success": False,
            "roll_number": roll_number,
            "error": "UMS lookup failed — student may not exist in UMS",
        }

    # ── 3. Sync records ───────────────────────────────────────────────────────
    rec_summary = await sync_student_academic_records(db, adapter, student)
    att_summary = await sync_student_attendance(db, adapter, student)
    new_cgpa = await update_student_cgpa(db, student)

    await db.commit()

    summary = {
        "success": True,
        "roll_number": roll_number,
        "synced_at": utcnow().isoformat(),
        "academic_records": rec_summary,
        "attendance": att_summary,
        "cgpa_updated": new_cgpa,
    }
    logger.info("UMS sync complete: %s — %s", roll_number, summary)
    return summary


async def sync_department(
    db: AsyncSession,
    adapter: UMSAdapter,
    department_code: str,
) -> dict:
    """
    Sync all students in a department.
    Returns per-student results + aggregate summary.
    """
    students_result = await db.execute(
        select(Student)
        .join(Student.department)
        .where(Student.department.has(code=department_code))
    )
    students = students_result.scalars().all()

    results = []
    total_success = 0
    total_failed = 0

    for student in students:
        r = await sync_single_student(db, adapter, student.roll_number)
        results.append(r)
        if r["success"]:
            total_success += 1
        else:
            total_failed += 1

    return {
        "department_code": department_code,
        "total_students": len(students),
        "synced": total_success,
        "failed": total_failed,
        "results": results,
    }
