"""Integration tests for usage statistics API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.fixture
async def auth_headers(client: AsyncClient):
    """Register and login a user."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "usage_test@example.com", "password": "securepass123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "usage_test@example.com", "password": "securepass123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.asyncio
async def test_daily_usage_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/usage/daily")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_daily_usage_default_range(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/usage/daily", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total_requests" in data
    assert "total_tokens_in" in data
    assert "total_tokens_out" in data
    assert "total_cost" in data
    assert "start" in data
    assert "end" in data


@pytest.mark.asyncio
async def test_daily_usage_with_dates(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        "/api/v1/usage/daily?start=2026-01-01&end=2026-01-31",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["start"] == "2026-01-01"
    assert data["end"] == "2026-01-31"


@pytest.mark.asyncio
async def test_daily_usage_model_filter(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        "/api/v1/usage/daily?model=claude-sonnet-4-6",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # All items should be for the requested model
    for item in data["items"]:
        assert item["model"] == "claude-sonnet-4-6"


@pytest.mark.asyncio
async def test_daily_usage_invalid_date_range(client: AsyncClient, auth_headers: dict):
    # start after end
    resp = await client.get(
        "/api/v1/usage/daily?start=2026-02-01&end=2026-01-01",
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_daily_usage_range_too_large(client: AsyncClient, auth_headers: dict):
    # 91 days > max 90 days
    resp = await client.get(
        "/api/v1/usage/daily?start=2025-11-01&end=2026-01-31",
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_daily_usage_empty_for_new_user(client: AsyncClient, auth_headers: dict):
    # New user with no transactions should get empty items and zero totals
    resp = await client.get("/api/v1/usage/daily", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_requests"] == 0
    assert data["total_tokens_in"] == 0
    assert data["total_tokens_out"] == 0
