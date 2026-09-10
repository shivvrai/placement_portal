"""
Tests for Analytics API endpoints and TPO dashboard functionality.
"""

import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


async def test_get_placement_stats(client: AsyncClient, seed_tpo):
    """TPO can get overall placement stats."""
    response = await client.get(
        "/api/v1/analytics/placement",
        headers=auth_headers(seed_tpo),
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_students" in data
    assert "placed" in data
    assert "placement_pct" in data


async def test_get_dept_placement_stats(client: AsyncClient, seed_tpo):
    """TPO can get department placement breakdown."""
    res1 = await client.get("/api/v1/analytics/departments", headers=auth_headers(seed_tpo))
    res2 = await client.get("/api/v1/analytics/placement/departments", headers=auth_headers(seed_tpo))
    assert res1.status_code == 200
    assert res2.status_code == 200
    assert isinstance(res1.json(), list)
    assert isinstance(res2.json(), list)


async def test_get_top_recruiters(client: AsyncClient, seed_tpo):
    """TPO can get top recruiters."""
    response = await client.get("/api/v1/analytics/top-recruiters", headers=auth_headers(seed_tpo))
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_get_trends(client: AsyncClient, seed_tpo):
    """TPO can get monthly placement trends."""
    response = await client.get("/api/v1/analytics/trends", headers=auth_headers(seed_tpo))
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "month" in data[0]
    assert "placed" in data[0]
    assert "offers" in data[0]


async def test_get_package_distribution(client: AsyncClient, seed_tpo):
    """TPO can get package distribution bands."""
    response = await client.get("/api/v1/analytics/package-distribution", headers=auth_headers(seed_tpo))
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 6


async def test_get_yoy_stats(client: AsyncClient, seed_tpo):
    """TPO can get YoY stats."""
    response = await client.get("/api/v1/analytics/yoy", headers=auth_headers(seed_tpo))
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


async def test_get_sectors(client: AsyncClient, seed_tpo):
    """TPO can get sector breakdown."""
    response = await client.get("/api/v1/analytics/sectors", headers=auth_headers(seed_tpo))
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_get_skill_demand(client: AsyncClient, seed_tpo):
    """TPO can get skill demand vs supply."""
    response = await client.get("/api/v1/analytics/skill-demand", headers=auth_headers(seed_tpo))
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_ums_sync_body_endpoint(client: AsyncClient, seed_tpo, seed_student):
    """TPO can sync UMS using POST /ums/sync with roll_number body."""
    _, student = seed_student
    response = await client.post(
        "/api/v1/ums/sync",
        json={"roll_number": student.roll_number},
        headers=auth_headers(seed_tpo),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["roll_number"] == student.roll_number
