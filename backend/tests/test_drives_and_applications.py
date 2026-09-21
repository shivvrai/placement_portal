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


@pytest.mark.asyncio
async def test_tpo_review_applicants_and_stage_transitions(
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
        json={"company_name": "StageTech", "title": "DevOps Hiring 2026"},
        headers=tpo_headers,
    )
    assert create_res.status_code == 201
    drive_id = create_res.json()["id"]

    # 2. Student applies
    await client.post(f"/api/v1/drives/{drive_id}/apply", headers=student_headers)

    # 3. TPO reviews all applicants
    applicants_res = await client.get(f"/api/v1/drives/{drive_id}/applicants", headers=tpo_headers)
    assert applicants_res.status_code == 200
    applicants = applicants_res.json()
    assert len(applicants) == 1
    app_id = applicants[0]["application_id"]
    assert applicants[0]["status"] == "applied"

    # 4. TPO advances stage to Tech Round 1 with interview schedule
    stage_payload = {
        "current_stage": "Technical Interview 1",
        "status": "in_progress",
        "stage_status": "scheduled",
        "scheduled_at": "2026-11-15T10:30:00",
        "meeting_link": "https://meet.google.com/stage-tech-interview",
        "venue": "CS Lab 2",
        "feedback": "Strong coding profile, testing DSA skills.",
    }
    patch_res = await client.patch(
        f"/api/v1/drives/{drive_id}/applications/{app_id}",
        json=stage_payload,
        headers=tpo_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "in_progress"
    assert patch_res.json()["current_stage"] == "Technical Interview 1"

    # 5. Check student received notification
    notif_res = await client.get("/api/v1/notifications/mine", headers=student_headers)
    assert notif_res.status_code == 200
    notifs = notif_res.json()["items"]
    assert any("StageTech" in n["title"] or "StageTech" in n["message"] for n in notifs)


@pytest.mark.asyncio
async def test_tpo_record_official_offer(
    client: AsyncClient,
    seed_tpo: User,
    seed_student: tuple[User, Student],
):
    tpo_headers = auth_headers(seed_tpo)
    student_user, _ = seed_student
    student_headers = auth_headers(student_user)

    # 1. Create drive & apply
    create_res = await client.post(
        "/api/v1/drives",
        json={"company_name": "OfferCorp", "title": "SDE Graduate 2026"},
        headers=tpo_headers,
    )
    drive_id = create_res.json()["id"]
    await client.post(f"/api/v1/drives/{drive_id}/apply", headers=student_headers)

    applicants_res = await client.get(f"/api/v1/drives/{drive_id}/applicants", headers=tpo_headers)
    app_id = applicants_res.json()[0]["application_id"]

    # 2. Record official offer
    offer_payload = {
        "offer_ctc_lpa": 24.0,
        "offer_fixed_lpa": 20.0,
        "offer_variable_lpa": 4.0,
        "offer_designation": "Associate Software Engineer",
        "offer_joining_date": "2027-07-01",
        "offer_reference_number": "OFFER/2026/AMZ/423",
    }
    offer_res = await client.post(
        f"/api/v1/drives/{drive_id}/applications/{app_id}/offer",
        json=offer_payload,
        headers=tpo_headers,
    )
    assert offer_res.status_code == 200
    offer_data = offer_res.json()
    assert offer_data["offer_ctc_lpa"] == 24.0
    assert offer_data["offer_designation"] == "Associate Software Engineer"

    # 3. Verify student application history reflects offer
    my_apps_res = await client.get("/api/v1/applications/mine", headers=student_headers)
    assert my_apps_res.status_code == 200
    my_app = next(a for a in my_apps_res.json() if a["drive_id"] == drive_id)
    assert my_app["status"] == "selected"
    assert my_app["offer_ctc_lpa"] == 24.0
    assert my_app["offer_designation"] == "Associate Software Engineer"

    # 4. Verify student received celebratory offer notification
    notif_res = await client.get("/api/v1/notifications/mine", headers=student_headers)
    assert notif_res.status_code == 200
    notifs = notif_res.json()["items"]
    assert any("Offer Letter" in n["title"] and "OfferCorp" in n["title"] for n in notifs)


@pytest.mark.asyncio
async def test_drive_announcements_broadcast(
    client: AsyncClient,
    seed_tpo: User,
    seed_student: tuple[User, Student],
):
    tpo_headers = auth_headers(seed_tpo)
    student_user, _ = seed_student
    student_headers = auth_headers(student_user)

    # 1. Create drive and student applies
    create_res = await client.post(
        "/api/v1/drives",
        json={"company_name": "BroadcastCorp", "title": "Data Analyst 2026"},
        headers=tpo_headers,
    )
    drive_id = create_res.json()["id"]
    await client.post(f"/api/v1/drives/{drive_id}/apply", headers=student_headers)

    # 2. TPO posts announcement
    ann_payload = {
        "title": "Venue changed for Tech Round 2",
        "message": "Interview venue has been shifted to CS Seminar Hall 2. Bring hard copy resume.",
        "urgency": "important",
    }
    post_res = await client.post(
        f"/api/v1/drives/{drive_id}/announcements",
        json=ann_payload,
        headers=tpo_headers,
    )
    assert post_res.status_code == 201
    ann = post_res.json()
    assert ann["title"] == "Venue changed for Tech Round 2"
    assert ann["urgency"] == "important"

    # 3. Read announcements endpoint
    get_res = await client.get(f"/api/v1/drives/{drive_id}/announcements", headers=student_headers)
    assert get_res.status_code == 200
    anns = get_res.json()
    assert len(anns) >= 1
    assert anns[0]["title"] == "Venue changed for Tech Round 2"

    # 4. Verify broadcast notification delivered to student
    notif_res = await client.get("/api/v1/notifications/mine", headers=student_headers)
    assert notif_res.status_code == 200
    notifs = notif_res.json()["items"]
    assert any("Announcement" in n["title"] and "Venue changed" in n["message"] for n in notifs)
