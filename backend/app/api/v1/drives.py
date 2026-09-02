"""
Drives API — placement drive management and student applications.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.drive import (
    DriveResponse, DriveCreateRequest, DriveUpdateRequest,
    ApplicationResponse, ApplicationStudentRow, CompanyBrief,
)
from app.schemas.common import MessageResponse, PaginatedResponse, PaginationMeta
from app.services import drive_service

router = APIRouter(prefix="/drives", tags=["Placement Drives"])

_tpo_admin = RoleChecker(["tpo", "admin"])
_authenticated = get_current_user


def _drive_to_response(drive, counts: dict = None, has_applied: bool = False) -> DriveResponse:
    counts = counts or {}
    return DriveResponse(
        id=drive.id,
        company=CompanyBrief(
            id=drive.company.id,
            name=drive.company.name,
            industry=drive.company.industry,
            location=drive.company.location,
        ) if drive.company else CompanyBrief(id=uuid.uuid4(), name="Unknown"),
        title=drive.title,
        description=drive.description,
        drive_date=drive.drive_date,
        registration_deadline=drive.registration_deadline,
        min_cgpa=float(drive.min_cgpa) if drive.min_cgpa else None,
        eligible_departments=drive.eligible_departments or [],
        max_backlogs=drive.max_backlogs,
        roles_offered=drive.roles_offered or [],
        salary_ctc=float(drive.salary_ctc) if drive.salary_ctc else None,
        status=drive.status,
        academic_year=drive.academic_year,
        registered_count=counts.get("registered_count", 0),
        shortlisted_count=counts.get("shortlisted_count", 0),
        selected_count=counts.get("selected_count", 0),
        has_applied=has_applied,
    )


@router.get("", response_model=PaginatedResponse, summary="List placement drives")
async def list_drives(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    drives, total = await drive_service.list_drives(
        db, status_filter=status_filter, page=page, per_page=per_page
    )
    data = []
    for drive in drives:
        counts = await drive_service.get_application_count(db, drive.id)
        has_applied = (
            await drive_service.check_applied(db, current_user.id, drive.id)
            if current_user.role == "student" else False
        )
        data.append(_drive_to_response(drive, counts, has_applied))

    total_pages = max(1, (total + per_page - 1) // per_page)
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total, total_pages=total_pages),
    )


@router.post("", response_model=DriveResponse, status_code=status.HTTP_201_CREATED, summary="Create drive (TPO)")
async def create_drive(
    data: DriveCreateRequest,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    drive = await drive_service.create_drive(db, data, created_by=current_user.id)
    return _drive_to_response(drive)


@router.get("/{drive_id}", response_model=DriveResponse)
async def get_drive(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    drive = await drive_service.get_drive(db, drive_id)
    counts = await drive_service.get_application_count(db, drive_id)
    has_applied = (
        await drive_service.check_applied(db, current_user.id, drive_id)
        if current_user.role == "student" else False
    )
    return _drive_to_response(drive, counts, has_applied)


@router.patch("/{drive_id}", response_model=DriveResponse, summary="Update drive (TPO)")
async def update_drive(
    drive_id: uuid.UUID,
    data: DriveUpdateRequest,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    drive = await drive_service.get_drive(db, drive_id)
    drive = await drive_service.update_drive(db, drive, data)
    counts = await drive_service.get_application_count(db, drive_id)
    return _drive_to_response(drive, counts)


@router.post("/{drive_id}/apply", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_drive(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await drive_service.apply_to_drive(db, student_id=current_user.id, drive_id=drive_id)
    return MessageResponse(message="Application submitted successfully")


@router.get("/{drive_id}/shortlisted", summary="View shortlisted students (TPO)")
async def get_shortlisted(
    drive_id: uuid.UUID,
    current_user: User = Depends(_tpo_admin),
    db: AsyncSession = Depends(get_db),
):
    applications = await drive_service.get_shortlisted_students(db, drive_id)
    return [
        ApplicationStudentRow(
            application_id=app.id,
            student_id=app.student.id,
            roll_number=app.student.roll_number,
            first_name=app.student.user.first_name,
            last_name=app.student.user.last_name,
            cgpa=float(app.student.cgpa) if app.student.cgpa else None,
            status=app.status,
            current_stage=app.current_stage,
            applied_at=app.applied_at,
        )
        for app in applications
    ]
