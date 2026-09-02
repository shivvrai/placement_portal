"""
Mock UMS Adapter — reads from local PostgreSQL/SQLite tables.

This is the development implementation of the UMSAdapter interface.
It simulates a real UMS by reading data that has been seeded locally
(or returning synthetic placeholder data if the DB has no records).

In production, swap this for ApiUMSAdapter (calls real UMS REST API)
or EtlUMSAdapter (reads from UMS database exports).
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.adapters.ums_adapter import (
    UMSAdapter, StudentDTO, AcademicRecordDTO, AttendanceDTO, SubjectDTO,
)
from app.models.user import Student, User, Department
from app.models.academic import Subject, AcademicRecord, Attendance, Semester

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Synthetic data generators (used when DB has no records — fresh dev env)
# ---------------------------------------------------------------------------

_SYNTHETIC_STUDENTS: dict[str, StudentDTO] = {
    "CS2022001": StudentDTO(
        ums_id="UMS-CS-001",
        roll_number="CS2022001",
        first_name="Aryan",
        last_name="Sharma",
        email="aryan.sharma@university.ac.in",
        department_code="CS",
        current_semester=6,
        admission_year=2022,
        cgpa=8.4,
        phone="9876543210",
    ),
    "CS2022002": StudentDTO(
        ums_id="UMS-CS-002",
        roll_number="CS2022002",
        first_name="Priya",
        last_name="Verma",
        email="priya.verma@university.ac.in",
        department_code="CS",
        current_semester=6,
        admission_year=2022,
        cgpa=9.1,
        phone="9123456780",
    ),
    "EC2021010": StudentDTO(
        ums_id="UMS-EC-010",
        roll_number="EC2021010",
        first_name="Rohan",
        last_name="Mehta",
        email="rohan.mehta@university.ac.in",
        department_code="EC",
        current_semester=8,
        admission_year=2021,
        cgpa=7.8,
        phone="9988776655",
    ),
}

_SYNTHETIC_RECORDS: dict[str, list[AcademicRecordDTO]] = {
    "CS2022001": [
        AcademicRecordDTO(subject_code="CS101", subject_name="Programming Fundamentals", semester_number=1, grade="A", grade_points=9.0, marks=88, max_marks=100),
        AcademicRecordDTO(subject_code="CS102", subject_name="Data Structures", semester_number=2, grade="A+", grade_points=10.0, marks=95, max_marks=100),
        AcademicRecordDTO(subject_code="CS201", subject_name="Algorithms", semester_number=3, grade="A", grade_points=9.0, marks=87, max_marks=100),
        AcademicRecordDTO(subject_code="CS301", subject_name="Database Systems", semester_number=4, grade="B+", grade_points=8.0, marks=78, max_marks=100),
        AcademicRecordDTO(subject_code="CS401", subject_name="Machine Learning", semester_number=5, grade="A", grade_points=9.0, marks=91, max_marks=100),
    ],
    "CS2022002": [
        AcademicRecordDTO(subject_code="CS101", subject_name="Programming Fundamentals", semester_number=1, grade="A+", grade_points=10.0, marks=97, max_marks=100),
        AcademicRecordDTO(subject_code="CS102", subject_name="Data Structures", semester_number=2, grade="A+", grade_points=10.0, marks=98, max_marks=100),
        AcademicRecordDTO(subject_code="CS201", subject_name="Algorithms", semester_number=3, grade="A+", grade_points=10.0, marks=96, max_marks=100),
    ],
}

_SYNTHETIC_ATTENDANCE: dict[str, list[AttendanceDTO]] = {
    "CS2022001": [
        AttendanceDTO(subject_code="CS401", semester_number=5, total_classes=60, attended=54),
        AttendanceDTO(subject_code="CS402", semester_number=5, total_classes=45, attended=40),
    ],
    "CS2022002": [
        AttendanceDTO(subject_code="CS401", semester_number=5, total_classes=60, attended=60),
    ],
}

_SYNTHETIC_SUBJECTS: list[SubjectDTO] = [
    SubjectDTO(code="CS101", name="Programming Fundamentals", department_code="CS", semester_number=1, credits=4, subject_type="core", syllabus_text="Python basics, control flow, functions, OOP"),
    SubjectDTO(code="CS102", name="Data Structures", department_code="CS", semester_number=2, credits=4, subject_type="core", syllabus_text="Arrays, linked lists, stacks, queues, trees, graphs"),
    SubjectDTO(code="CS201", name="Algorithms", department_code="CS", semester_number=3, credits=4, subject_type="core", syllabus_text="Sorting, searching, dynamic programming, greedy algorithms"),
    SubjectDTO(code="CS301", name="Database Systems", department_code="CS", semester_number=4, credits=3, subject_type="core", syllabus_text="SQL, normalization, transactions, PostgreSQL"),
    SubjectDTO(code="CS401", name="Machine Learning", department_code="CS", semester_number=5, credits=4, subject_type="elective", syllabus_text="Supervised learning, neural networks, scikit-learn"),
    SubjectDTO(code="CS402", name="Web Technologies", department_code="CS", semester_number=5, credits=3, subject_type="elective", syllabus_text="HTML, CSS, JavaScript, React, REST APIs"),
    SubjectDTO(code="EC101", name="Basic Electronics", department_code="EC", semester_number=1, credits=4, subject_type="core", syllabus_text="Diodes, transistors, op-amps"),
    SubjectDTO(code="EC201", name="Digital Electronics", department_code="EC", semester_number=3, credits=4, subject_type="core", syllabus_text="Logic gates, flip-flops, counters, VHDL"),
]


# ---------------------------------------------------------------------------
# MockUMSAdapter
# ---------------------------------------------------------------------------

class MockUMSAdapter(UMSAdapter):
    """
    Development UMS adapter.

    Priority order:
      1. If the DB has real Student records → build DTOs from them.
      2. If the roll_number matches _SYNTHETIC_STUDENTS → return synthetic data.
      3. Return None / empty list.
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    # ── helpers ──────────────────────────────────────────────────────────────

    async def _get_student_orm(self, roll_number: str) -> Optional[Student]:
        result = await self._db.execute(
            select(Student).where(Student.roll_number == roll_number)
        )
        return result.scalar_one_or_none()

    async def _get_dept_code(self, dept_id: uuid.UUID) -> str:
        result = await self._db.execute(
            select(Department.code).where(Department.id == dept_id)
        )
        return result.scalar_one_or_none() or "UNKNOWN"

    def _orm_to_dto(self, student: Student, dept_code: str, user: User) -> StudentDTO:
        return StudentDTO(
            ums_id=student.ums_student_id or f"UMS-{student.roll_number}",
            roll_number=student.roll_number,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            department_code=dept_code,
            current_semester=student.current_semester,
            admission_year=student.admission_year,
            cgpa=float(student.cgpa) if student.cgpa else None,
            phone=user.phone,
        )

    # ── interface implementation ──────────────────────────────────────────────

    async def get_student(self, identifier: str) -> Optional[StudentDTO]:
        """Fetch by roll number — first from DB, then from synthetic data."""
        # Try DB first
        result = await self._db.execute(
            select(Student, User, Department)
            .join(User, User.id == Student.id)
            .join(Department, Department.id == Student.department_id)
            .where(Student.roll_number == identifier)
        )
        row = result.one_or_none()
        if row:
            student, user, dept = row
            return self._orm_to_dto(student, dept.code, user)

        # Fall back to synthetic data
        return _SYNTHETIC_STUDENTS.get(identifier)

    async def get_students_by_department(self, department_code: str) -> list[StudentDTO]:
        """Fetch all students in a department from DB."""
        result = await self._db.execute(
            select(Student, User, Department)
            .join(User, User.id == Student.id)
            .join(Department, Department.id == Student.department_id)
            .where(Department.code == department_code)
        )
        rows = result.all()
        if rows:
            return [self._orm_to_dto(s, d.code, u) for s, u, d in rows]

        # Synthetic fallback
        return [
            dto for dto in _SYNTHETIC_STUDENTS.values()
            if dto.department_code == department_code
        ]

    async def get_academic_records(self, roll_number: str) -> list[AcademicRecordDTO]:
        """Fetch academic records for a student."""
        # Try DB
        student_q = await self._db.execute(
            select(Student.id).where(Student.roll_number == roll_number)
        )
        student_id = student_q.scalar_one_or_none()

        if student_id:
            result = await self._db.execute(
                select(AcademicRecord, Subject)
                .join(Subject, Subject.id == AcademicRecord.subject_id)
                .where(AcademicRecord.student_id == student_id)
                .order_by(AcademicRecord.semester_id)
            )
            rows = result.all()
            if rows:
                return [
                    AcademicRecordDTO(
                        subject_code=subj.code,
                        subject_name=subj.name,
                        semester_number=subj.semester_number,
                        grade=rec.grade,
                        grade_points=float(rec.grade_points) if rec.grade_points else None,
                        marks=float(rec.marks) if rec.marks else None,
                        max_marks=float(rec.max_marks) if rec.max_marks else None,
                        status=rec.status,
                    )
                    for rec, subj in rows
                ]

        return _SYNTHETIC_RECORDS.get(roll_number, [])

    async def get_attendance(self, roll_number: str, semester: Optional[int] = None) -> list[AttendanceDTO]:
        """Fetch attendance data, optionally filtered by semester."""
        student_q = await self._db.execute(
            select(Student.id).where(Student.roll_number == roll_number)
        )
        student_id = student_q.scalar_one_or_none()

        if student_id:
            query = (
                select(Attendance, Subject)
                .join(Subject, Subject.id == Attendance.subject_id)
                .where(Attendance.student_id == student_id)
            )
            if semester is not None:
                query = query.where(Subject.semester_number == semester)
            result = await self._db.execute(query)
            rows = result.all()
            if rows:
                return [
                    AttendanceDTO(
                        subject_code=subj.code,
                        semester_number=subj.semester_number,
                        total_classes=att.total_classes,
                        attended=att.attended,
                    )
                    for att, subj in rows
                ]

        records = _SYNTHETIC_ATTENDANCE.get(roll_number, [])
        if semester is not None:
            records = [r for r in records if r.semester_number == semester]
        return records

    async def get_subjects(self, department_code: Optional[str] = None) -> list[SubjectDTO]:
        """Fetch all subjects, optionally filtered by department."""
        query = select(Subject, Department).join(Department, Department.id == Subject.department_id, isouter=True)
        if department_code:
            query = query.where(Department.code == department_code)
        result = await self._db.execute(query)
        rows = result.all()

        if rows:
            return [
                SubjectDTO(
                    code=subj.code,
                    name=subj.name,
                    department_code=dept.code if dept else "UNKNOWN",
                    semester_number=subj.semester_number,
                    credits=subj.credits,
                    subject_type=subj.subject_type,
                    syllabus_text=subj.syllabus_text,
                )
                for subj, dept in rows
            ]

        # Synthetic fallback
        subjects = _SYNTHETIC_SUBJECTS
        if department_code:
            subjects = [s for s in subjects if s.department_code == department_code]
        return subjects

    async def sync_student(self, roll_number: str) -> bool:
        """
        Sync a student's data from UMS into the local DB.

        This mock implementation just verifies the student exists
        in the DB or synthetic data. A real implementation would
        call an external UMS API and upsert the response.
        """
        dto = await self.get_student(roll_number)
        if dto is None:
            logger.warning("UMS sync: student %s not found", roll_number)
            return False

        logger.info(
            "UMS sync (mock): student %s — %s %s, CGPA=%.2f",
            roll_number, dto.first_name, dto.last_name, dto.cgpa or 0,
        )
        return True
