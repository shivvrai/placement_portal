"""
Unit and integration tests for Sprint 2:
- Institutional Audit Trail (SystemLog/AuditLog)
- Accreditation & NIRF Reporting (preview, json, csv)
- Drive and Application audit event triggers
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import auth_headers
from app.models.system import AuditLog
from app.models.placement import PlacementDrive, Application

pytestmark = pytest.mark.asyncio


async def test_accreditation_preview_endpoint(client: AsyncClient, seed_tpo):
    """TPO can preview NIRF 1A accreditation metrics."""
    response = await client.get(
        "/api/v1/analytics/accreditation/preview?academic_year=2026-27",
        headers=auth_headers(seed_tpo),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["academic_year"] == "2026-27"
    assert "total_graduating" in data
    assert "placed_count" in data
    assert "placement_pct" in data
    assert "median_ctc_lpa" in data
    assert "avg_ctc_lpa" in data
    assert "gender_breakdown" in data


async def test_accreditation_report_json_and_audit(client: AsyncClient, seed_tpo, db: AsyncSession):
    """Exporting accreditation report in JSON format returns full report and writes audit log."""
    response = await client.get(
        "/api/v1/analytics/accreditation/report?academic_year=2026-27&format=json",
        headers=auth_headers(seed_tpo),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["report_type"] == "NIRF_NAAC_Placement_Report"
    assert "nirf_1a_placement" in data
    assert "nirf_1c_sector_diversity" in data
    assert "naac_1_1_3_remediation" in data

    # Verify audit log was recorded
    logs = (await db.execute(
        select(AuditLog).where(AuditLog.action == "ACCREDITATION_REPORT_EXPORTED")
    )).scalars().all()
    assert len(logs) > 0


async def test_accreditation_report_csv(client: AsyncClient, seed_tpo):
    """Exporting accreditation report in CSV format returns valid text/csv attachment."""
    response = await client.get(
        "/api/v1/analytics/accreditation/report?academic_year=2026-27&format=csv",
        headers=auth_headers(seed_tpo),
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers.get("content-disposition", "")
    assert "NIRF" in response.text
    assert "Placement Statistics" in response.text


async def test_audit_logs_viewer(client: AsyncClient, seed_tpo):
    """TPO can fetch paginated audit logs."""
    response = await client.get(
        "/api/v1/system/audit-logs",
        headers=auth_headers(seed_tpo),
    )
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert "meta" in body
    assert isinstance(body["data"], list)


async def test_drive_creation_and_application_status_audit(client: AsyncClient, seed_tpo, seed_student, db: AsyncSession):
    """Drive creation and application status update write audit log entries."""
    _, student = seed_student

    # 1. Create a drive
    drive_payload = {
        "company_name": "Acme Corp",
        "company_industry": "Technology",
        "company_location": "Bangalore",
        "title": "Software Engineer",
        "salary_ctc": 18.0,
        "academic_year": "2026-27",
    }
    create_res = await client.post(
        "/api/v1/drives",
        json=drive_payload,
        headers=auth_headers(seed_tpo),
    )
    assert create_res.status_code == 201
    drive_id = create_res.json()["id"]

    # 2. Student applies
    student_user, _ = seed_student
    apply_res = await client.post(
        f"/api/v1/drives/{drive_id}/apply",
        headers=auth_headers(student_user),
    )
    assert apply_res.status_code == 201

    # Get application ID
    app_record = (await db.execute(
        select(Application).where(Application.drive_id == uuid.UUID(drive_id))
    )).scalar_one()

    # 3. TPO updates application status
    patch_res = await client.patch(
        f"/api/v1/drives/{drive_id}/applications/{app_record.id}",
        json={"status": "selected", "offer_ctc_lpa": 18.0},
        headers=auth_headers(seed_tpo),
    )
    assert patch_res.status_code == 200

    # 4. Verify audit entries for DRIVE_CREATE and APPLICATION_STATUS_CHANGE
    res = await client.get(
        f"/api/v1/system/audit-logs?event_type=APPLICATION_STATUS_CHANGE",
        headers=auth_headers(seed_tpo),
    )
    assert res.status_code == 200
    events = res.json()["data"]
    assert any(e["resource_id"] == str(app_record.id) for e in events)
