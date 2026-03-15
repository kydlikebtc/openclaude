"""Integration tests for miner earnings endpoint."""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient


@pytest.fixture
async def user_auth_headers(client: AsyncClient):
    """Register and login a user."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "earnings_user@example.com", "password": "securepass123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "earnings_user@example.com", "password": "securepass123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def registered_miner_id(client: AsyncClient) -> str:
    """Register a miner and return its ID."""
    resp = await client.post(
        "/api/v1/miners/register",
        json={
            "hotkey": "5EarningsTestHotkey",
            "coldkey": "5EarningsTestColdkey",
            "name": "Earnings Test Miner",
            "api_key": "sk-ant-test-earnings-key",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_earnings_requires_auth(client: AsyncClient, registered_miner_id: str):
    resp = await client.get(f"/api/v1/miners/{registered_miner_id}/earnings")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_earnings_miner_not_found(client: AsyncClient, user_auth_headers: dict):
    fake_id = str(uuid.uuid4())
    resp = await client.get(
        f"/api/v1/miners/{fake_id}/earnings",
        headers=user_auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_earnings_success(
    client: AsyncClient, user_auth_headers: dict, registered_miner_id: str
):
    resp = await client.get(
        f"/api/v1/miners/{registered_miner_id}/earnings",
        headers=user_auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["miner_id"] == registered_miner_id
    assert "hotkey" in data
    assert "stake_amount" in data
    assert "revenue_share_pct" in data
    assert "total_gross_revenue" in data
    assert "total_earnings" in data
    assert "daily" in data
    assert "start" in data
    assert "end" in data


@pytest.mark.asyncio
async def test_earnings_revenue_share_is_30_pct(
    client: AsyncClient, user_auth_headers: dict, registered_miner_id: str
):
    resp = await client.get(
        f"/api/v1/miners/{registered_miner_id}/earnings",
        headers=user_auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["revenue_share_pct"] == pytest.approx(30.0)


@pytest.mark.asyncio
async def test_earnings_no_transactions_returns_zeros(
    client: AsyncClient, user_auth_headers: dict, registered_miner_id: str
):
    resp = await client.get(
        f"/api/v1/miners/{registered_miner_id}/earnings",
        headers=user_auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(data["total_gross_revenue"]) == Decimal("0")
    assert Decimal(data["total_earnings"]) == Decimal("0")
    assert data["daily"] == []


@pytest.mark.asyncio
async def test_earnings_custom_days(
    client: AsyncClient, user_auth_headers: dict, registered_miner_id: str
):
    resp = await client.get(
        f"/api/v1/miners/{registered_miner_id}/earnings?days=7",
        headers=user_auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "daily" in data
