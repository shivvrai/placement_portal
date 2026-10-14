import pytest
import uuid
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.user import User


@pytest.fixture
def anyio_backend():
    return "asyncio"


def get_mock_student():
    user = User(
        id=uuid.uuid4(),
        email="student@example.com",
        role="student",
        first_name="Test",
        last_name="Student",
        is_active=True,
    )
    return user


def get_mock_faculty():
    user = User(
        id=uuid.uuid4(),
        email="faculty@example.com",
        role="faculty",
        first_name="Test",
        last_name="Faculty",
        is_active=True,
    )
    return user


@pytest.mark.anyio
async def test_question_selection_insufficient():
    """Test insufficient questions handling."""
    transport = ASGITransport(app=app)
    student = get_mock_student()
    
    # Mock get_current_user
    from app.core.security import get_current_user
    app.dependency_overrides[get_current_user] = lambda: student
    
    # Mock db.execute to return empty
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result
    
    with patch("app.services.assessment_engine.AsyncSession") as _:
        with patch("app.api.v1.assessments.get_db", return_value=mock_db):
            from app.core.database import get_db
            app.dependency_overrides[get_db] = lambda: mock_db
            
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/assessments/start",
                    json={"topic": "Python", "difficulty": "advanced"},
                )
                assert response.status_code == 400
                assert "Insufficient questions" in response.json()["detail"]
                
    # Only clear our own overrides — preserve get_db test override
    from app.core.security import get_current_user as gcu
    app.dependency_overrides.pop(gcu, None)


@pytest.mark.anyio
async def test_answer_leakage_prevention():
    """
    SECURITY TEST: Verify that the /start response NEVER leaks:
    - correct_answer
    - correct_option
    - is_correct
    - explanation
    
    These fields must only appear in the post-submission /submit response.
    """
    transport = ASGITransport(app=app)
    student = get_mock_student()
    
    from app.core.security import get_current_user
    app.dependency_overrides[get_current_user] = lambda: student
    
    # Mock db.execute to return enough questions to pass the >= 5 check
    mock_qs = []
    for i in range(5):
        mock_q = MagicMock()
        mock_q.id = uuid.uuid4()
        mock_q.question_text = f"What is 2+{i}?"
        mock_q.options = ["1", "2", "3", "4"]
        mock_q.correct_answer = str(2+i)
        mock_q.explanation = f"Because {2+i} is the sum"
        mock_qs.append(mock_q)
        
    mock_result_1 = MagicMock()
    mock_result_1.scalars.return_value.all.return_value = mock_qs
    
    # Mock session
    mock_session = MagicMock()
    mock_session.id = uuid.uuid4()
    mock_session.topic = "Math"
    mock_session.difficulty = "beginner"
    mock_session.status = "in_progress"
    
    # Mock session questions
    session_qs = []
    for q in mock_qs:
        sq = MagicMock()
        sq.question = q
        session_qs.append(sq)
        
    mock_session.session_questions = session_qs
    
    mock_result_2 = MagicMock()
    mock_result_2.scalar_one.return_value = mock_session
    
    mock_db = AsyncMock()
    mock_db.execute.side_effect = [mock_result_1, mock_result_2]
    
    from app.core.database import get_db
    app.dependency_overrides[get_db] = lambda: mock_db
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/assessments/start",
            json={"topic": "Math", "difficulty": "beginner"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["questions"]) == 5
        
        # Verify NO answer leakage in ANY question
        for q in data["questions"]:
            assert "correct_answer" not in q, f"SECURITY: correct_answer leaked in question {q['id']}"
            assert "correct_option" not in q, f"SECURITY: correct_option leaked in question {q['id']}"
            assert "is_correct" not in q, f"SECURITY: is_correct leaked in question {q['id']}"
            assert "explanation" not in q, f"SECURITY: explanation leaked in question {q['id']}"
        
        # Also verify correct_answer does not appear anywhere in the raw response body
        raw_body = response.text
        for q in mock_qs:
            # The correct answer values should not appear as field values
            # (they may appear as option values which is fine)
            assert f'"correct_answer"' not in raw_body, "SECURITY: correct_answer key found in response"
            
    # Only clear our own overrides — preserve get_db test override
    from app.core.security import get_current_user as gcu
    app.dependency_overrides.pop(gcu, None)
    from app.core.database import get_db as _gdb
    # Restore to test override if it was replaced
    from tests.conftest import _override_get_db
    app.dependency_overrides[_gdb] = _override_get_db


@pytest.mark.anyio
async def test_answer_leakage_full_response_check():
    """
    SECURITY TEST: Deeper check that verifies no internal correctness 
    data is exposed in the question response schema.
    """
    transport = ASGITransport(app=app)
    student = get_mock_student()
    
    from app.core.security import get_current_user
    app.dependency_overrides[get_current_user] = lambda: student
    
    mock_qs = []
    for i in range(6):
        mock_q = MagicMock()
        mock_q.id = uuid.uuid4()
        mock_q.question_text = f"Security question {i}"
        mock_q.options = ["A", "B", "C", "D"]
        mock_q.correct_answer = "B"  # Secret - must not leak
        mock_q.explanation = "Secret explanation"
        mock_qs.append(mock_q)

    mock_result_1 = MagicMock()
    mock_result_1.scalars.return_value.all.return_value = mock_qs

    mock_session = MagicMock()
    mock_session.id = uuid.uuid4()
    mock_session.topic = "Security"
    mock_session.difficulty = "intermediate"
    mock_session.status = "in_progress"
    
    session_qs = []
    for q in mock_qs:
        sq = MagicMock()
        sq.question = q
        session_qs.append(sq)
    mock_session.session_questions = session_qs

    mock_result_2 = MagicMock()
    mock_result_2.scalar_one.return_value = mock_session

    mock_db = AsyncMock()
    mock_db.execute.side_effect = [mock_result_1, mock_result_2]

    from app.core.database import get_db
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/assessments/start",
            json={"topic": "Security", "difficulty": "intermediate"},
        )
        assert response.status_code == 200
        data = response.json()
        
        # Each question should have EXACTLY these keys
        allowed_keys = {"id", "question_text", "options"}
        for q in data["questions"]:
            actual_keys = set(q.keys())
            assert actual_keys == allowed_keys, (
                f"SECURITY: Question has unexpected keys: {actual_keys - allowed_keys}"
            )

    from app.core.security import get_current_user as gcu
    app.dependency_overrides.pop(gcu, None)
    from app.core.database import get_db as _gdb
    from tests.conftest import _override_get_db
    app.dependency_overrides[_gdb] = _override_get_db


@pytest.mark.anyio
async def test_scoring_and_skill_updates():
    """Test scoring logic and skill confidence update."""
    from app.services.assessment_engine import submit_assessment
    from app.schemas.assessment import AssessmentSubmitRequest, AssessmentAnswerItem
    
    mock_db = AsyncMock()
    session_id = uuid.uuid4()
    student_id = uuid.uuid4()
    
    # Mock session
    mock_session = MagicMock()
    mock_session.id = session_id
    mock_session.student_id = student_id
    mock_session.status = "in_progress"
    
    # Mock session question
    q_id = uuid.uuid4()
    mock_sq = MagicMock()
    mock_sq.question_id = q_id
    
    # Mock actual question
    mock_q = MagicMock()
    mock_q.id = q_id
    mock_q.correct_answer = "opt2"
    mock_q.question_text = "Test"
    mock_q.explanation = "Because"
    mock_sq.question = mock_q
    
    mock_session.session_questions = [mock_sq]
    
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_session
    mock_db.execute.return_value = mock_res
    
    with patch("app.services.assessment_engine.update_student_skill_from_assessment", new_callable=AsyncMock) as mock_update:
        request_data = AssessmentSubmitRequest(answers=[AssessmentAnswerItem(question_id=q_id, selected_option="opt2")])
        result = await submit_assessment(
            mock_db,
            student_id,
            session_id,
            data=request_data
        )
        
        assert result.score == 100.0
        assert mock_session.status == "completed"
        
        # Verify update was called
        mock_update.assert_called_once_with(mock_db, student_id, mock_session)


@pytest.mark.anyio
async def test_completed_assessment_resubmission_rejected():
    """Test that already-completed assessments cannot be resubmitted."""
    from app.services.assessment_engine import submit_assessment
    from app.schemas.assessment import AssessmentSubmitRequest, AssessmentAnswerItem
    
    mock_db = AsyncMock()
    session_id = uuid.uuid4()
    student_id = uuid.uuid4()
    
    mock_session = MagicMock()
    mock_session.id = session_id
    mock_session.student_id = student_id
    mock_session.status = "completed"  # Already completed
    
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_session
    mock_db.execute.return_value = mock_res
    
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        request_data = AssessmentSubmitRequest(answers=[AssessmentAnswerItem(question_id=uuid.uuid4(), selected_option="opt1")])
        await submit_assessment(mock_db, student_id, session_id, data=request_data)
    
    assert exc_info.value.status_code == 400
    assert "already submitted" in str(exc_info.value.detail).lower()
