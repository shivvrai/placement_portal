"""
Pydantic schemas for UMS Integration API.
"""

from pydantic import BaseModel
from typing import Optional


class UMSSyncRequest(BaseModel):
    roll_number: str



class UMSStudentPreview(BaseModel):
    """Read-only preview of a student's data as seen in UMS."""
    ums_id: str
    roll_number: str
    full_name: str
    email: str
    department_code: str
    current_semester: int
    admission_year: int
    cgpa: Optional[float] = None
    academic_records_count: int
    attendance_records_count: int


class UMSAcademicRecordResult(BaseModel):
    created: int
    updated: int
    skipped: int
    total: int


class UMSAttendanceResult(BaseModel):
    created: int
    updated: int
    skipped: int
    total: int


class UMSSyncResult(BaseModel):
    """Result of a single-student UMS sync operation."""
    success: bool
    roll_number: str
    synced_at: Optional[str] = None
    academic_records: Optional[UMSAcademicRecordResult] = None
    attendance: Optional[UMSAttendanceResult] = None
    cgpa_updated: Optional[float] = None
    error: Optional[str] = None


class UMSDepartmentSyncResult(BaseModel):
    """Result of a full department sync."""
    department_code: str
    total_students: int
    synced: int
    failed: int
    results: list[UMSSyncResult]


class UMSSubjectResponse(BaseModel):
    """Subject data as returned by UMS."""
    code: str
    name: str
    department_code: str
    semester_number: int
    credits: int
    subject_type: str
    syllabus_text: Optional[str] = None
