"""
Comprehensive test suite for Anjula's Final Task Sheet Submission:
  - Task 1: Anonymous Company Reviews & Peer Interview Intelligence Hub
  - Task 2: Application Tracker Timeline & Milestone State Machine
  - Task 3: Secure Student Document Vault with TPO Verification Lock & Checksum
  - Task 4: Faculty Department Placement & Curriculum Analytics Dashboard
"""

import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestTask1CompanyReviewsIntelligence:
    """Task 1: Anonymous Company Reviews & Peer Interview Intelligence Hub."""

    @pytest.mark.anyio
    async def test_company_review_extended_model_columns(self):
        """Verify CompanyReview model has all interview intelligence columns."""
        from app.models.company_reviews import CompanyReview, CompanyInsight
        columns = [c.name for c in CompanyReview.__table__.columns]
        assert "difficulty_rating" in columns
        assert "selection_outcome" in columns
        assert "academic_year" in columns
        assert "offered_ctc_lpa" in columns
        assert "stipend_monthly" in columns
        assert "round_breakdown" in columns
        assert "question_tags" in columns

        insight_cols = [c.name for c in CompanyInsight.__table__.columns]
        assert "avg_difficulty" in insight_cols
        assert "topic_tags_cloud" in insight_cols

    @pytest.mark.anyio
    async def test_company_review_schemas_validation(self):
        """Verify CompanyReviewCreate and Response schemas validate all fields."""
        from app.schemas.anjula_sprint3 import CompanyReviewCreate, CompanyReviewResponse
        review = CompanyReviewCreate(
            company_name="Google",
            role="Software Engineer",
            academic_year="2025-26",
            overall_rating=5,
            difficulty_rating=4,
            selection_outcome="Selected",
            offered_ctc_lpa=38.5,
            stipend_monthly=110000.0,
            round_breakdown=[
                {"round_number": 1, "round_name": "Online Assessment", "duration_mins": 90, "platform": "HackerEarth"},
                {"round_number": 2, "round_name": "DSA Interview", "duration_mins": 45, "platform": "Google Meet"},
            ],
            question_tags=["Dynamic Programming", "Trie", "Graphs"],
            pros="Great compensation and engineering autonomy",
            cons="Challenging interview rounds",
            advice_to_juniors="Focus on DSA patterns",
        )
        assert review.company_name == "Google"
        assert review.difficulty_rating == 4
        assert review.selection_outcome == "Selected"
        assert review.offered_ctc_lpa == 38.5
        assert len(review.question_tags) == 3

    @pytest.mark.anyio
    async def test_company_reviews_routes_registered(self, client):
        """Verify company review routes are registered and active."""
        res_reviews = await client.get("/api/v1/companies/reviews")
        assert res_reviews.status_code in (401, 403)

        res_insights = await client.get("/api/v1/companies/insights")
        assert res_insights.status_code in (401, 403, 200)


class TestTask2ApplicationTrackerTimeline:
    """Task 2: Application Tracker Timeline & Milestone State Machine."""

    @pytest.mark.anyio
    async def test_timeline_event_model_registered(self):
        """Verify ApplicationTimelineEvent model exists with correct structure."""
        from app.models.company_reviews import ApplicationTimelineEvent
        assert ApplicationTimelineEvent.__tablename__ == "application_timeline_events"
        cols = [c.name for c in ApplicationTimelineEvent.__table__.columns]
        assert "application_id" in cols
        assert "event_type" in cols
        assert "from_status" in cols
        assert "to_status" in cols
        assert "actor_id" in cols
        assert "metadata_payload" in cols

    @pytest.mark.anyio
    async def test_tracker_routes_accessible(self, client):
        """Verify /tracker/applications and timeline routes exist."""
        res = await client.get("/api/v1/tracker/applications")
        assert res.status_code in (401, 403)

        res_tl = await client.get(f"/api/v1/tracker/timeline/{uuid.uuid4()}")
        assert res_tl.status_code in (401, 403)


class TestTask3SecureDocumentVault:
    """Task 3: Secure Student Document Vault with Extension Limits & TPO Lock."""

    @pytest.mark.anyio
    async def test_document_model_has_checksum(self):
        """Verify StudentDocument model has file_checksum column."""
        from app.models.document_vault import StudentDocument
        cols = [c.name for c in StudentDocument.__table__.columns]
        assert "file_checksum" in cols
        assert "is_verified" in cols

    @pytest.mark.anyio
    async def test_document_validation_rejects_disallowed_extension(self):
        """Verify service rejects executables / unapproved file extensions."""
        from app.services import anjula_sprint3_service as svc
        from app.schemas.anjula_sprint3 import DocumentUpload
        from fastapi import HTTPException

        doc_bad = DocumentUpload(
            document_type="resume_pdf",
            title="Resume Script",
            file_url="/uploads/resume.exe",
            file_name="resume.exe",
            file_size_bytes=1024,
        )
        with pytest.raises(HTTPException) as exc:
            # Pass mock db session
            class DummySession:
                pass
            await svc.upload_document(DummySession(), uuid.uuid4(), doc_bad)
        assert exc.value.status_code == 400
        assert "Invalid file extension" in exc.value.detail

    @pytest.mark.anyio
    async def test_document_validation_rejects_oversized_file(self):
        """Verify service rejects files exceeding 10MB limit."""
        from app.services import anjula_sprint3_service as svc
        from app.schemas.anjula_sprint3 import DocumentUpload
        from fastapi import HTTPException

        doc_oversized = DocumentUpload(
            document_type="marksheet_10th",
            title="Oversized Marksheet",
            file_url="/uploads/marksheet.pdf",
            file_name="marksheet.pdf",
            file_size_bytes=11 * 1024 * 1024,  # 11MB > 10MB
        )
        with pytest.raises(HTTPException) as exc:
            class DummySession:
                pass
            await svc.upload_document(DummySession(), uuid.uuid4(), doc_oversized)
        assert exc.value.status_code == 400
        assert "exceeds the maximum allowed ceiling of 10MB" in exc.value.detail

    @pytest.mark.anyio
    async def test_vault_routes_registered(self, client):
        """Verify vault routes are registered."""
        res = await client.get("/api/v1/vault/documents")
        assert res.status_code in (401, 403)

        res_shared = await client.get("/api/v1/vault/shared")
        assert res_shared.status_code in (401, 403)


class TestTask4FacultyDepartmentAnalytics:
    """Task 4: Faculty Department Placement & Curriculum Analytics Dashboard."""

    @pytest.mark.anyio
    async def test_faculty_schemas_validation(self):
        """Verify FacultyDashboardResponse and FacultyStudentRow schemas."""
        from app.schemas.anjula_sprint3 import FacultyDashboardResponse, FacultyStudentRow, AssignMentorRequest
        dash = FacultyDashboardResponse(
            department_code="CSE",
            department_name="Computer Science & Engineering",
            total_students=120,
            placed_count=96,
            placement_pct=80.0,
            eligible_count=100,
            total_offers=110,
            dual_offers_count=18,
            highest_ctc_lpa=42.0,
            median_ctc_lpa=8.5,
            avg_ctc_lpa=9.8,
            top_recruiters=[{"company_name": "TCS", "hires_count": 25}],
        )
        assert dash.placement_pct == 80.0
        assert dash.dual_offers_count == 18

        row = FacultyStudentRow(
            student_id=uuid.uuid4(),
            roll_number="CS21B001",
            first_name="Aarav",
            last_name="Sharma",
            email="aarav@univ.edu",
            department_code="CSE",
            cgpa=6.4,
            active_backlogs=0,
            placement_status="unplaced",
            skill_score=44.0,
            is_at_risk=True,
            risk_level="high",
            total_applications=4,
            total_offers=0,
        )
        assert row.is_at_risk is True
        assert row.risk_level == "high"

        mentor_req = AssignMentorRequest(
            mentor_name="Dr. Ramanathan",
            counseling_note="Review DSA progress",
            intervention_type="academic_counseling",
        )
        assert mentor_req.mentor_name == "Dr. Ramanathan"

    @pytest.mark.anyio
    async def test_faculty_routes_registered(self, client):
        """Verify /faculty/dashboard and /faculty/students routes are active."""
        res_dash = await client.get("/api/v1/faculty/dashboard")
        assert res_dash.status_code in (401, 403)

        res_students = await client.get("/api/v1/faculty/students")
        assert res_students.status_code in (401, 403)

        res_mentor = await client.post(f"/api/v1/faculty/students/{uuid.uuid4()}/assign-mentor", json={
            "mentor_name": "Prof. Smith",
            "counseling_note": "Test note",
            "intervention_type": "academic_counseling",
        })
        assert res_mentor.status_code in (401, 403)
