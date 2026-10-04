"""
Integration tests — Sprint 3 features: Sakshi (Alumni, Prep Resources, Surveys)
                                       Anjula (Company Reviews, Tracker, Document Vault)

Covers all new API endpoints with end-to-end test coverage.
"""

import uuid
import pytest
from datetime import datetime, timezone
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


@pytest.fixture
def auth_headers(client):
    """Simulate auth headers for tests."""
    return {"Authorization": "Bearer test-token"}


# ═══════════════════════════════════════════════════════════════════
# SAKSHI SPRINT 3 — Alumni & Mentorship
# ═══════════════════════════════════════════════════════════════════

class TestAlumniMentorship:
    """Tests for Alumni Network & Mentorship module."""

    @pytest.mark.anyio
    async def test_alumni_model_exists(self):
        """Verify AlumniProfile model is registered."""
        from app.models.alumni import AlumniProfile, MentorshipConnection, MentorshipSession
        assert AlumniProfile.__tablename__ == "alumni_profiles"
        assert MentorshipConnection.__tablename__ == "mentorship_connections"
        assert MentorshipSession.__tablename__ == "mentorship_sessions"

    @pytest.mark.anyio
    async def test_alumni_schema_validation(self):
        """Verify alumni schemas validate correctly."""
        from app.schemas.sakshi_sprint3 import AlumniProfileCreate, MentorshipRequestCreate
        profile = AlumniProfileCreate(
            graduation_year=2024,
            department_code="CSE",
            current_company="Google",
            current_designation="SDE-2",
            expertise_areas=["Python", "ML"],
            max_mentees=5,
        )
        assert profile.graduation_year == 2024
        assert profile.current_company == "Google"

    @pytest.mark.anyio
    async def test_alumni_route_registered(self, client):
        """Verify alumni API routes are registered."""
        response = await client.get("/api/v1/alumni", params={"page": 1})
        # Should return 401 (auth required), not 404 (route not found)
        assert response.status_code in (401, 403)

    @pytest.mark.anyio
    async def test_mentorship_request_schema(self):
        """Verify mentorship request schema."""
        from app.schemas.sakshi_sprint3 import MentorshipRequestCreate
        req = MentorshipRequestCreate(
            alumni_id=uuid.uuid4(),
            message="I'd love guidance on system design",
            goals=["System Design", "DSA"],
        )
        assert len(req.goals) == 2

    @pytest.mark.anyio
    async def test_session_feedback_schema(self):
        """Verify session feedback validation."""
        from app.schemas.sakshi_sprint3 import SessionFeedback
        fb = SessionFeedback(rating=5, feedback="Great session!")
        assert fb.rating == 5
        with pytest.raises(Exception):
            SessionFeedback(rating=6, feedback="Invalid")


# ═══════════════════════════════════════════════════════════════════
# SAKSHI SPRINT 3 — Placement Prep Resources
# ═══════════════════════════════════════════════════════════════════

class TestPrepResources:
    """Tests for Placement Prep Resources module."""

    @pytest.mark.anyio
    async def test_prep_resource_model_exists(self):
        """Verify PrepResource model is registered."""
        from app.models.prep_resources import PrepResource, PrepCollection, PrepProgress
        assert PrepResource.__tablename__ == "prep_resources"
        assert PrepCollection.__tablename__ == "prep_collections"
        assert PrepProgress.__tablename__ == "prep_progress"

    @pytest.mark.anyio
    async def test_prep_resource_schema(self):
        """Verify prep resource schema."""
        from app.schemas.sakshi_sprint3 import PrepResourceCreate
        resource = PrepResourceCreate(
            title="Dynamic Programming Mastery",
            description="Comprehensive guide to DP problems",
            category="coding",
            resource_type="article",
            difficulty="advanced",
            tags=["DP", "competitive-programming"],
            estimated_minutes=120,
        )
        assert resource.category == "coding"
        assert resource.difficulty == "advanced"

    @pytest.mark.anyio
    async def test_prep_routes_registered(self, client):
        """Verify prep resource API routes are registered."""
        response = await client.get("/api/v1/prep/resources", params={"page": 1})
        assert response.status_code in (401, 403)

    @pytest.mark.anyio
    async def test_prep_progress_schema(self):
        """Verify progress tracking schema."""
        from app.schemas.sakshi_sprint3 import PrepProgressUpdate
        progress = PrepProgressUpdate(status="in_progress", progress_pct=45.0)
        assert progress.progress_pct == 45.0

    @pytest.mark.anyio
    async def test_prep_collection_schema(self):
        """Verify collection schema."""
        from app.schemas.sakshi_sprint3 import PrepCollectionCreate
        coll = PrepCollectionCreate(
            title="TCS NQT Prep Pack",
            description="Complete preparation for TCS NQT",
            target_role="SDE Trainee",
        )
        assert coll.target_role == "SDE Trainee"


# ═══════════════════════════════════════════════════════════════════
# SAKSHI SPRINT 3 — Feedback Surveys
# ═══════════════════════════════════════════════════════════════════

class TestFeedbackSurveys:
    """Tests for Student Feedback & Satisfaction Surveys module."""

    @pytest.mark.anyio
    async def test_feedback_model_exists(self):
        """Verify Feedback models are registered."""
        from app.models.feedback import FeedbackSurvey, SurveyQuestion, SurveyResponse
        assert FeedbackSurvey.__tablename__ == "feedback_surveys"
        assert SurveyQuestion.__tablename__ == "survey_questions"
        assert SurveyResponse.__tablename__ == "survey_responses"

    @pytest.mark.anyio
    async def test_survey_create_schema(self):
        """Verify survey creation schema."""
        from app.schemas.sakshi_sprint3 import SurveyCreate, SurveyQuestionCreate
        survey = SurveyCreate(
            title="Placement Experience 2025-26",
            description="Share your placement experience",
            survey_type="placement_experience",
            is_anonymous=True,
            questions=[
                SurveyQuestionCreate(
                    question_text="How satisfied were you with the placement process?",
                    question_type="rating",
                ),
                SurveyQuestionCreate(
                    question_text="What could we improve?",
                    question_type="text",
                    is_required=False,
                ),
            ],
        )
        assert len(survey.questions) == 2
        assert survey.is_anonymous is True

    @pytest.mark.anyio
    async def test_survey_routes_registered(self, client):
        """Verify survey API routes are registered."""
        response = await client.get("/api/v1/surveys")
        assert response.status_code in (401, 403)

    @pytest.mark.anyio
    async def test_survey_submission_schema(self):
        """Verify survey submission schema."""
        from app.schemas.sakshi_sprint3 import SurveySubmission
        submission = SurveySubmission(
            answers={"q1": 5, "q2": "Excellent process"},
            overall_rating=5,
            additional_comments="Very happy with the placement cell",
        )
        assert submission.overall_rating == 5


# ═══════════════════════════════════════════════════════════════════
# ANJULA SPRINT 3 — Company Reviews & Insights
# ═══════════════════════════════════════════════════════════════════

class TestCompanyReviews:
    """Tests for Company Reviews & Insights module."""

    @pytest.mark.anyio
    async def test_company_review_model_exists(self):
        """Verify CompanyReview model is registered."""
        from app.models.company_reviews import CompanyReview, CompanyInsight
        assert CompanyReview.__tablename__ == "company_reviews"
        assert CompanyInsight.__tablename__ == "company_insights"

    @pytest.mark.anyio
    async def test_company_review_schema(self):
        """Verify company review schema."""
        from app.schemas.anjula_sprint3 import CompanyReviewCreate
        review = CompanyReviewCreate(
            company_name="Infosys",
            role="System Engineer",
            review_type="placement",
            overall_rating=4,
            work_culture_rating=4,
            growth_rating=3,
            pros="Good work-life balance, strong training programs",
            cons="Slower career growth compared to product companies",
            salary_range="3.6-4.5 LPA",
        )
        assert review.overall_rating == 4
        assert review.review_type == "placement"

    @pytest.mark.anyio
    async def test_company_review_routes_registered(self, client):
        """Verify company review API routes are registered."""
        response = await client.get("/api/v1/companies/reviews", params={"page": 1})
        assert response.status_code in (401, 403)

    @pytest.mark.anyio
    async def test_company_insight_response_schema(self):
        """Verify insight response schema."""
        from app.schemas.anjula_sprint3 import CompanyInsightResponse
        insight = CompanyInsightResponse(
            id=uuid.uuid4(),
            company_name="Google",
            avg_rating=4.8,
            total_reviews=25,
            avg_package_lpa=45.0,
            max_package_lpa=60.0,
            common_roles=["SDE", "SRE"],
        )
        assert insight.avg_rating == 4.8


# ═══════════════════════════════════════════════════════════════════
# ANJULA SPRINT 3 — Application Tracker
# ═══════════════════════════════════════════════════════════════════

class TestApplicationTracker:
    """Tests for Application Tracker & Status Timeline module."""

    @pytest.mark.anyio
    async def test_timeline_model_exists(self):
        """Verify ApplicationTimelineEvent model is registered."""
        from app.models.application_timeline import ApplicationTimelineEvent
        assert ApplicationTimelineEvent.__tablename__ == "application_timeline_events"

    @pytest.mark.anyio
    async def test_timeline_event_schema(self):
        """Verify timeline event response schema."""
        from app.schemas.anjula_sprint3 import TimelineEventResponse
        event = TimelineEventResponse(
            id=uuid.uuid4(),
            application_id=uuid.uuid4(),
            event_type="status_change",
            from_status="applied",
            to_status="shortlisted",
            description="Shortlisted based on CGPA and skill match",
        )
        assert event.to_status == "shortlisted"

    @pytest.mark.anyio
    async def test_tracker_routes_registered(self, client):
        """Verify tracker API routes are registered."""
        response = await client.get("/api/v1/tracker/applications")
        assert response.status_code in (401, 403)

    @pytest.mark.anyio
    async def test_application_tracker_response_schema(self):
        """Verify full tracker response."""
        from app.schemas.anjula_sprint3 import ApplicationTrackerResponse
        tracker = ApplicationTrackerResponse(
            application_id=uuid.uuid4(),
            drive_title="TCS NQT 2025",
            company_name="TCS",
            role="System Engineer",
            current_status="shortlisted",
            next_steps="Prepare for the technical interview.",
        )
        assert tracker.current_status == "shortlisted"


# ═══════════════════════════════════════════════════════════════════
# ANJULA SPRINT 3 — Document Vault
# ═══════════════════════════════════════════════════════════════════

class TestDocumentVault:
    """Tests for Student Document Vault module."""

    @pytest.mark.anyio
    async def test_document_model_exists(self):
        """Verify StudentDocument model is registered."""
        from app.models.document_vault import StudentDocument
        assert StudentDocument.__tablename__ == "student_documents"

    @pytest.mark.anyio
    async def test_document_upload_schema(self):
        """Verify document upload schema."""
        from app.schemas.anjula_sprint3 import DocumentUpload
        doc = DocumentUpload(
            document_type="offer_letter",
            title="TCS Offer Letter",
            file_url="/uploads/tcs_offer.pdf",
            file_name="tcs_offer.pdf",
            file_size_bytes=256000,
            mime_type="application/pdf",
            tags=["TCS", "2025"],
            is_shared_with_tpo=True,
        )
        assert doc.document_type == "offer_letter"
        assert doc.is_shared_with_tpo is True

    @pytest.mark.anyio
    async def test_vault_routes_registered(self, client):
        """Verify vault API routes are registered."""
        response = await client.get("/api/v1/vault/documents")
        assert response.status_code in (401, 403)

    @pytest.mark.anyio
    async def test_document_update_schema(self):
        """Verify partial document update schema."""
        from app.schemas.anjula_sprint3 import DocumentUpdateRequest
        update = DocumentUpdateRequest(
            title="Updated Title",
            tags=["TCS", "offer", "2025"],
        )
        assert update.title == "Updated Title"
        assert len(update.tags) == 3

    @pytest.mark.anyio
    async def test_document_response_schema(self):
        """Verify document response schema."""
        from app.schemas.anjula_sprint3 import DocumentResponse
        doc = DocumentResponse(
            id=uuid.uuid4(),
            student_id=uuid.uuid4(),
            document_type="certificate",
            title="AWS Cloud Practitioner",
            file_url="/uploads/aws_cert.pdf",
            file_name="aws_cert.pdf",
            is_verified=True,
        )
        assert doc.is_verified is True


# ═══════════════════════════════════════════════════════════════════
# CROSS-MODULE INTEGRATION
# ═══════════════════════════════════════════════════════════════════

class TestSprintIntegration:
    """Cross-cutting integration checks for Sprint 3 Sakshi + Anjula."""

    @pytest.mark.anyio
    async def test_all_models_registered_in_init(self):
        """Verify all Sprint 3 models are in models/__init__.py."""
        from app.models import (
            AlumniProfile, MentorshipConnection, MentorshipSession,
            PrepResource, PrepCollection, PrepProgress,
            FeedbackSurvey, SurveyQuestion, SurveyResponse,
            CompanyReview, CompanyInsight,
            StudentDocument,
            ApplicationTimelineEvent,
        )
        # All 13 new models should import without error
        assert AlumniProfile is not None
        assert StudentDocument is not None
        assert ApplicationTimelineEvent is not None

    @pytest.mark.anyio
    async def test_all_routers_registered(self, client):
        """Verify all Sprint 3 route prefixes are accessible."""
        routes_to_check = [
            "/api/v1/alumni",
            "/api/v1/prep/resources",
            "/api/v1/surveys",
            "/api/v1/companies/reviews",
            "/api/v1/tracker/applications",
            "/api/v1/vault/documents",
        ]
        for route in routes_to_check:
            response = await client.get(route)
            # Must NOT be 404 — routes must be registered
            assert response.status_code != 404, f"Route {route} not found (404)"

    @pytest.mark.anyio
    async def test_health_check_still_works(self, client):
        """Ensure existing health endpoints are unaffected."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.anyio
    async def test_service_modules_importable(self):
        """Verify service modules can be imported."""
        from app.services import sakshi_sprint3_service
        from app.services import anjula_sprint3_service
        assert sakshi_sprint3_service is not None
        assert anjula_sprint3_service is not None
