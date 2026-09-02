"""
UMS (University Management System) Adapter Interface.

Defines the abstract interface for UMS integration.
The MockUMSAdapter reads from local PostgreSQL tables.
Future adapters can implement API or ETL-based integration.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class StudentDTO:
    """Data Transfer Object for student data from UMS."""
    ums_id: str
    roll_number: str
    first_name: str
    last_name: str
    email: str
    department_code: str
    current_semester: int
    admission_year: int
    cgpa: Optional[float] = None
    phone: Optional[str] = None


@dataclass
class AcademicRecordDTO:
    """DTO for a single academic record from UMS."""
    subject_code: str
    subject_name: str
    semester_number: int
    grade: Optional[str] = None
    grade_points: Optional[float] = None
    marks: Optional[float] = None
    max_marks: Optional[float] = None
    status: str = "completed"


@dataclass
class AttendanceDTO:
    """DTO for attendance data from UMS."""
    subject_code: str
    semester_number: int
    total_classes: int
    attended: int


@dataclass
class SubjectDTO:
    """DTO for subject/course data from UMS."""
    code: str
    name: str
    department_code: str
    semester_number: int
    credits: int
    subject_type: str = "core"
    syllabus_text: Optional[str] = None


class UMSAdapter(ABC):
    """
    Abstract interface for University Management System integration.

    Three modes are supported:
    - mock: Reads from seeded PostgreSQL tables (for development)
    - api: Calls external UMS REST API (for production)
    - etl: Reads from UMS database export files (for batch sync)
    """

    @abstractmethod
    async def get_student(self, identifier: str) -> Optional[StudentDTO]:
        """Fetch a student by roll number or UMS ID."""
        ...

    @abstractmethod
    async def get_students_by_department(self, department_code: str) -> list[StudentDTO]:
        """Fetch all students in a department."""
        ...

    @abstractmethod
    async def get_academic_records(self, roll_number: str) -> list[AcademicRecordDTO]:
        """Fetch all academic records for a student."""
        ...

    @abstractmethod
    async def get_attendance(self, roll_number: str, semester: Optional[int] = None) -> list[AttendanceDTO]:
        """Fetch attendance data for a student, optionally filtered by semester."""
        ...

    @abstractmethod
    async def get_subjects(self, department_code: Optional[str] = None) -> list[SubjectDTO]:
        """Fetch subjects/courses, optionally filtered by department."""
        ...

    @abstractmethod
    async def sync_student(self, roll_number: str) -> bool:
        """Sync a student's data from UMS to local DB. Returns True if successful."""
        ...
