"""
Tests for Placement Drives and Student Applications lifecycle.
Covers:
- TPO drive creation, listing, updating
- Student application submission & duplicate prevention (409)
- Student application history (GET /api/v1/applications/mine)
- TPO shortlisted candidates listing (GET /api/v1/drives/{id}/shortlisted)
"""

import pytest
from httpx import AsyncClient
from app.models.user import User, Student
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_tpo_create_and_list_drives(
    client: AsyncClient,
    seed_tpo: User,
):
    headers = auth_headers(seed_tpo)

    # 1. TPO creates drive
    payload = {
        "company_name": "TestCorp Automated",
        "company_industry": "Technology",
        "company_location": "Bangalore",
        "title": "Software Engineer 2026",
        "description": "Comprehensive full stack hiring drive",
        "drive_date": "2026-11-20",
        "registration_deadline": "2026-11-10T23:59:59",
        "min_cgpa": 7.0,
        "eligible_departments": ["CS", "IT"],
        "max_backlogs": 0,
        "roles_offered": ["SDE-1", "Backend Dev"],
        "salary_ctc": 16.5,
        "academic_year": "2026-27",
    }

    res = await client.post("/api/v1/drives", json=payload, headers=headers)
    assert res.status_code == 201, f"Failed to create drive: {res.text}"
    created = res.json()
    assert created["title"] == "Software Engineer 2026"
    assert created["company"]["name"] == "TestCorp Automated"
    assert created["status"] in ("upcoming", "open")
    drive_id = created["id"]

    # 2. List drives
    list_res = await client.get("/api/v1/drives", headers=headers)
    assert list_res.status_code == 200
    data = list_res.json()["data"]
    drive_ids = [d["id"] for d in data]
    assert drive_id in drive_ids

    # 3. Filter drives by status
    filtered_res = await client.get("/api/v1/drives?status=open", headers=headers)
    assert filtered_res.status_code == 200
    filtered_data = filtered_res.json()["data"]
    assert all(d["status"] == "open" for d in filtered_data)


@pytest.mark.asyncio
async def test_tpo_update_drive(
    client: AsyncClient,
    seed_tpo: User,
):
    headers = auth_headers(seed_tpo)

    # Create a drive to update
    payload = {
        "company_name": "UpdateCorp",
        "title": "Initial Drive Title",
        "salary_ctc": 10.0,
    }
    create_res = await client.post("/api/v1/drives", json=payload, headers=headers)
    assert create_res.status_code == 201
    drive_id = create_res.json()["id"]

    # Update title and salary
    update_payload = {
        "title": "Updated Drive Title 2026",
        "salary_ctc": 14.5,
        "status": "in_progress",
    }
    update_res = await client.patch(f"/api/v1/drives/{drive_id}", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["title"] == "Updated Drive Title 2026"
    assert updated["salary_ctc"] == 14.5
    assert updated["status"] == "in_progress"


@pytest.mark.asyncio
async def test_student_apply_and_applications_pipeline(
    client: AsyncClient,
    seed_tpo: User,
    seed_student: tuple[User, Student],
):
    tpo_headers = auth_headers(seed_tpo)
    student_user, _ = seed_student
    student_headers = auth_headers(student_user)

    # 1. TPO creates an open drive
    create_res = await client.post(
        "/api/v1/drives",
        json={
            "company_name": "PipelineTech",
            "title": "Cloud Engineer Drive",
            "salary_ctc": 22.0,
            "min_cgpa": 6.5,
            "eligible_departments": ["CS"],
        },
        headers=tpo_headers,
    )
    assert create_res.status_code == 201
    drive_id = create_res.json()["id"]

    # 2. Student applies to the drive
    apply_res = await client.post(f"/api/v1/drives/{drive_id}/apply", headers=student_headers)
    assert apply_res.status_code == 201
    assert "submitted successfully" in apply_res.json()["message"]

    # 3. Duplicate application should return 409 Conflict
    dup_res = await client.post(f"/api/v1/drives/{drive_id}/apply", headers=student_headers)
    assert dup_res.status_code == 409

    # 4. Student checks "My Applications" history
    my_apps_res = await client.get("/api/v1/applications/mine", headers=student_headers)
    assert my_apps_res.status_code == 200
    apps = my_apps_res.json()
    assert len(apps) >= 1
    applied_drive_ids = [a["drive_id"] for a in apps]
    assert drive_id in applied_drive_ids

    matching_app = next(a for a in apps if a["drive_id"] == drive_id)
    assert matching_app["company_name"] == "PipelineTech"
    assert matching_app["drive_title"] == "Cloud Engineer Drive"
    assert matching_app["salary_ctc"] == 22.0
    assert matching_app["status"] == "applied"


@pytest.mark.asyncio
async def test_tpo_view_shortlisted_students(
    client: AsyncClient,
    seed_tpo: User,
    seed_student: tuple[User, Student],
):
    tpo_headers = auth_headers(seed_tpo)
    student_user, _ = seed_student
    student_headers = auth_headers(student_user)

    # 1. Create drive
    create_res = await client.post(
        "/api/v1/drives",
        json={"company_name": "ShortlistCorp", "title": "AI Research Intern"},
        headers=tpo_headers,
    )
    assert create_res.status_code == 201
    drive_id = create_res.json()["id"]

    # 2. Shortlisted endpoint returns empty initially
    shortlist_res = await client.get(f"/api/v1/drives/{drive_id}/shortlisted", headers=tpo_headers)
    assert shortlist_res.status_code == 200
    assert shortlist_res.json() == []

    # 3. Student applies
    await client.post(f"/api/v1/drives/{drive_id}/apply", headers=student_headers)

    # Non-TPO access to shortlisted endpoint should be forbidden
    non_tpo_res = await client.get(f"/api/v1/drives/{drive_id}/shortlisted", headers=student_headers)
    assert non_tpo_res.status_code == 403
