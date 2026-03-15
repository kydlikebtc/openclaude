"""Integration tests for billing API endpoints."""

from decimal import Decimal

import pytest
from httpx import AsyncClient


@pytest.fixture
async def auth_headers(client: AsyncClient):
    """Register and login a user, return auth headers."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "billing_user@example.com", "password": "securepass123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "billing_user@example.com", "password": "securepass123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_balance_authenticated(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/billing/balance", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "balance" in data
    assert data["currency"] == "USD"


@pytest.mark.asyncio
async def test_get_balance_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/billing/balance")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_recharge_success(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/billing/recharge",
        json={"amount": "10.00", "payment_method": "usdt"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(data["amount"]) == Decimal("10.00")
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_recharge_zero_amount_rejected(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/billing/recharge",
        json={"amount": "0", "payment_method": "usdt"},
        headers=auth_headers,
    )
    assert resp.status_code in (400, 422)


@pytest.mark.asyncio
async def test_recharge_increases_balance(client: AsyncClient, auth_headers: dict):
    # Get initial balance
    balance_resp = await client.get("/api/v1/billing/balance", headers=auth_headers)
    initial = Decimal(balance_resp.json()["balance"])

    # Recharge
    await client.post(
        "/api/v1/billing/recharge",
        json={"amount": "5.00", "payment_method": "usdt"},
        headers=auth_headers,
    )

    # Check new balance
    balance_resp = await client.get("/api/v1/billing/balance", headers=auth_headers)
    new_balance = Decimal(balance_resp.json()["balance"])
    assert new_balance == initial + Decimal("5.00")


@pytest.mark.asyncio
async def test_list_transactions(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/billing/transactions", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_usage_summary_valid_period(client: AsyncClient, auth_headers: dict):
    for period in ("today", "week", "month"):
        resp = await client.get(f"/api/v1/billing/usage?period={period}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data
        assert "total_cost" in data


@pytest.mark.asyncio
async def test_usage_summary_invalid_period(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/billing/usage?period=all_time", headers=auth_headers)
    assert resp.status_code == 400
