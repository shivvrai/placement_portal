"""
Unit and integration tests for Interview Experiences Hub and In-App Notifications:
- List experiences with filters
- Submit new student interview experience
- Upvote interview experience
- Notifications retrieval, mark as read, mark all read
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers
from app.api.v1.notifications import create_notification
from app.models.cohort import Notification
from app.models.experiences import InterviewExperience

pytestmark = pytest.mark.asyncio


async def test_list_interview_experiences_empty_or_populated(client: AsyncClient):
    """Anonymous/Public or authenticated users can browse experiences."""
    response = await client.get("/api/v1/experiences?company=Amazon")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


async def test_submit_and_upvote_experience(client: AsyncClient, seed_student, db: AsyncSession):
    """Students can submit interview experiences and users can upvote them."""
    user, student = seed_student
    payload = {
        "company_name": "Atlassian",
        "role": "Associate Software Engineer",
        "difficulty": "Hard",
        "verdict": "Selected",
        "overall_experience": "Initial screening on HackerRank followed by 3 rounds of coding and system design with friendly engineers.",
        "questions_asked": [
            "Implement Rate Limiter with Token Bucket Algorithm",
            "Design file storage service with LRU Cache"
        ],
        "tips_for_juniors": "Focus on concurrency, thread safety, and clean OOP structure."
    }

    response = await client.post(
        "/api/v1/experiences",
        json=payload,
        headers=auth_headers(user),
    )
    assert response.status_code == 201
    exp_data = response.json()
    assert exp_data["company_name"] == "Atlassian"
    assert exp_data["difficulty"] == "Hard"
    assert exp_data["verdict"] == "Selected"
    assert len(exp_data["questions_asked"]) == 2
    assert exp_data["upvotes"] == 0

    exp_id = exp_data["id"]

    # Upvote the experience
    upvote_res = await client.post(f"/api/v1/experiences/{exp_id}/upvote")
    assert upvote_res.status_code == 200
    assert upvote_res.json()["upvotes"] == 1

    # Verify in list
    list_res = await client.get(f"/api/v1/experiences?company=Atlassian")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert any(item["id"] == exp_id for item in items)


async def test_notifications_lifecycle(client: AsyncClient, seed_student, db: AsyncSession):
    """Users receive notifications, view unread count, mark single read and mark all read."""
    user, student = seed_student

    # Create 2 test notifications
    n1 = await create_notification(
        db=db,
        user_id=user.id,
        title="Test Shortlist Alert",
        message="Your profile has been shortlisted for Round 1.",
        type="APPLICATION_SHORTLISTED",
        link="/student/drives",
    )
    n2 = await create_notification(
        db=db,
        user_id=user.id,
        title="Test Deadline Alert",
        message="Registration closing in 24 hours.",
        type="DRIVE_DEADLINE_WARNING",
        link="/student/drives",
    )
    await db.commit()

    # 1. Fetch notifications
    res = await client.get("/api/v1/notifications/mine", headers=auth_headers(user))
    assert res.status_code == 200
    data = res.json()
    assert data["unread_count"] >= 2
    item_ids = [item["id"] for item in data["items"]]
    assert str(n1.id) in item_ids
    assert str(n2.id) in item_ids

    # 2. Mark single notification as read
    read_res = await client.patch(
        f"/api/v1/notifications/{n1.id}/read",
        headers=auth_headers(user),
    )
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # 3. Mark all as read
    all_read_res = await client.patch(
        "/api/v1/notifications/read-all",
        headers=auth_headers(user),
    )
    assert all_read_res.status_code == 200

    # 4. Check unread count is now 0
    after_res = await client.get("/api/v1/notifications/mine", headers=auth_headers(user))
    assert after_res.status_code == 200
    assert after_res.json()["unread_count"] == 0
