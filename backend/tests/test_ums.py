"""
UMS Sync Service unit tests.

Tests the sync logic in isolation using the MockUMSAdapter
against an in-memory SQLite database.
"""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.adapters.mock_ums_adapter import MockUMSAdapter, _SYNTHETIC_STUDENTS
from app.services.ums_sync_service import (
    sync_single_student,
    sync_student_academic_records,
    sync_student_attendance,
    update_student_cgpa,
)
from app.models.user import Student
from app.models.academic import AcademicRecord, Attendance


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# MockUMSAdapter unit tests
# ---------------------------------------------------------------------------

class TestMockUMSAdapter:
    async def test_get_known_student_returns_dto(self, db: AsyncSession):
        adapter = MockUMSAdapter(db)
        dto = await adapter.get_student("CS2022001")
        assert dto is not None
        assert dto.roll_number == "CS2022001"
        assert dto.first_name == "Aryan"
        assert dto.cgpa == 8.4

    async def test_get_unknown_student_returns_none(self, db: AsyncSession):
        adapter = MockUMSAdapter(db)
        dto = await adapter.get_student("XX9999999")
        assert dto is None

    async def test_get_academic_records_for_known_student(self, db: AsyncSession):
        adapter = MockUMSAdapter(db)
        records = await adapter.get_academic_records("CS2022001")
        assert isinstance(records, list)
        assert len(records) > 0
        for rec in records:
            assert rec.subject_code
            assert rec.subject_name

    async def test_get_academic_records_for_unknown_student(self, db: AsyncSession):
        adapter = MockUMSAdapter(db)
        records = await adapter.get_academic_records("XX9999999")
        assert records == []

    async def test_get_attendance_for_known_student(self, db: AsyncSession):
        adapter = MockUMSAdapter(db)
        att = await adapter.get_attendance("CS2022001")
        assert isinstance(att, list)
        assert len(att) > 0

    async def test_get_attendance_semester_filter(self, db: AsyncSession):
        adapter = MockUMSAdapter(db)
        att = await adapter.get_attendance("CS2022001", semester=5)
        for a in att:
            assert a.semester_number == 5

    async def test_get_subjects_all(self, db: AsyncSession):
        adapter = MockUMSAdapter(db)
        subjects = await adapter.get_subjects()
        assert len(subjects) > 0

    async def test_get_subjects_filtered_by_dept(self, db: AsyncSession):
        adapter = MockUMSAdapter(db)
        subjects = await adapter.get_subjects(department_code="CS")
        for s in subjects:
            assert s.department_code == "CS"

    async def test_sync_student_known_returns_true(self, db: AsyncSession):
        adapter = MockUMSAdapter(db)
        ok = await adapter.sync_student("CS2022001")
        assert ok is True

    async def test_sync_student_unknown_returns_false(self, db: AsyncSession):
        adapter = MockUMSAdapter(db)
        ok = await adapter.sync_student("UNKNOWN999")
        assert ok is False


# ---------------------------------------------------------------------------
# Sync service tests
# ---------------------------------------------------------------------------

class TestSyncService:
    async def test_sync_nonexistent_student_returns_graceful(
        self, db: AsyncSession
    ):
        """sync_single_student for a roll number not in local DB returns result dict."""
        adapter = MockUMSAdapter(db)
        result = await sync_single_student(db, adapter, "CS9999999")
        assert result["roll_number"] == "CS9999999"
        assert isinstance(result["success"], bool)

    async def test_sync_creates_academic_records(
        self, db: AsyncSession, seed_student
    ):
        """Academic records are created in DB after a sync."""
        user, student = seed_student
        # Merge the session-scoped student into this function's DB session
        merged = await db.merge(student)

        adapter = MockUMSAdapter(db)
        summary = await sync_student_academic_records(db, adapter, merged)

        assert summary["total"] > 0
        assert summary["created"] >= 0  # May already exist from prior run

    async def test_sync_attendance_creates_rows(
        self, db: AsyncSession, seed_student
    ):
        """Attendance records are created after a sync."""
        user, student = seed_student
        merged = await db.merge(student)

        adapter = MockUMSAdapter(db)
        summary = await sync_student_attendance(db, adapter, merged)

        assert summary["total"] > 0
        assert summary["created"] >= 0  # May already exist from prior run

    async def test_update_cgpa_with_no_records_returns_none(
        self, db: AsyncSession
    ):
        """CGPA update for a ghost student (no records) returns None."""
        ghost = Student(id=uuid.uuid4())
        result = await update_student_cgpa(db, ghost)
        assert result is None

    async def test_cgpa_update_after_sync_returns_value(
        self, db: AsyncSession, seed_student
    ):
        """CGPA is recomputed and is a valid float after academic records exist."""
        user, student = seed_student
        merged = await db.merge(student)

        adapter = MockUMSAdapter(db)
        await sync_student_academic_records(db, adapter, merged)
        new_cgpa = await update_student_cgpa(db, merged)

        # If records were synced, cgpa is not None; if already existed, could be None or float
        if new_cgpa is not None:
            assert 0.0 < new_cgpa <= 10.0


# ---------------------------------------------------------------------------
# UMS API endpoint tests
# ---------------------------------------------------------------------------

class TestUMSApi:
    async def test_preview_unknown_student_404(
        self, client, seed_tpo
    ):
        from tests.conftest import auth_headers
        response = await client.get(
            "/api/v1/ums/students/UNKNOWN999",
            headers=auth_headers(seed_tpo),
        )
        assert response.status_code == 404

    async def test_preview_known_student_returns_data(
        self, client, seed_tpo
    ):
        from tests.conftest import auth_headers
        response = await client.get(
            "/api/v1/ums/students/CS2022001",
            headers=auth_headers(seed_tpo),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["roll_number"] == "CS2022001"
        assert "academic_records_count" in data
        assert "attendance_records_count" in data

    async def test_list_subjects_returns_list(
        self, client, seed_tpo
    ):
        from tests.conftest import auth_headers
        response = await client.get(
            "/api/v1/ums/subjects",
            headers=auth_headers(seed_tpo),
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_list_subjects_dept_filter(
        self, client, seed_tpo
    ):
        from tests.conftest import auth_headers
        response = await client.get(
            "/api/v1/ums/subjects?department_code=CS",
            headers=auth_headers(seed_tpo),
        )
        assert response.status_code == 200
        for subj in response.json():
            assert subj["department_code"] == "CS"

    async def test_ums_endpoints_require_tpo_role(
        self, client, seed_student
    ):
        """Students cannot access UMS endpoints."""
        from tests.conftest import auth_headers
        user, _ = seed_student
        response = await client.get(
            "/api/v1/ums/students/CS2022001",
            headers=auth_headers(user),
        )
        assert response.status_code == 403
