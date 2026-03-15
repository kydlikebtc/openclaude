"""Integration tests for miner management endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_pool_status_public(client: AsyncClient):
    """Pool status endpoint is public."""
    resp = await client.get("/api/v1/miners/pool")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_miners" in data
    assert "online_miners" in data


@pytest.mark.asyncio
async def test_register_miner(client: AsyncClient):
    """Miner registration creates a new miner."""
    resp = await client.post(
        "/api/v1/miners/register",
        json={
            "hotkey": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            "coldkey": "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty",
            "name": "Test Miner",
            "api_key": "sk-ant-test-key-xxxx",
            "supported_models": ["claude-3-5-sonnet-20241022"],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["hotkey"] == "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"
    assert data["name"] == "Test Miner"
    assert "referral_code" in data


@pytest.mark.asyncio
async def test_register_miner_duplicate_re_registers(client: AsyncClient):
    """Registering the same hotkey again should succeed (re-registration)."""
    payload = {
        "hotkey": "5E4xREDuplicateHotkey",
        "coldkey": "5E4xREDuplicateColdkey",
        "name": "Miner V1",
        "api_key": "sk-ant-key-1",
        "supported_models": ["claude-3-5-sonnet-20241022"],
    }
    r1 = await client.post("/api/v1/miners/register", json=payload)
    assert r1.status_code == 201

    payload["name"] = "Miner V2"
    r2 = await client.post("/api/v1/miners/register", json=payload)
    assert r2.status_code == 201
    assert r2.json()["name"] == "Miner V2"


@pytest.mark.asyncio
async def test_heartbeat_unauthenticated_returns_401(client: AsyncClient):
    """Heartbeat without JWT returns 401 (auth required)."""
    resp = await client.post(
        "/api/v1/miners/heartbeat",
        json={
            "hotkey": "unknown-hotkey-xxxxxx",
            "avg_latency_ms": 100,
            "supported_models": [],
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_heartbeat_known_miner(client: AsyncClient):
    """Heartbeat from authenticated registered miner returns 200 with miner_id."""
    hotkey = "heartbeat-hotkey-test"
    # Register first
    await client.post(
        "/api/v1/miners/register",
        json={
            "hotkey": hotkey,
            "coldkey": "some-coldkey",
            "name": "Heartbeat Miner",
            "api_key": "sk-ant-hb-key",
            "supported_models": ["claude-3-5-sonnet-20241022"],
        },
    )

    # Get JWT
    challenge = await client.get("/api/v1/miners/auth/challenge")
    nonce = challenge.json()["nonce"]
    token_resp = await client.post(
        "/api/v1/miners/auth/token",
        json={"hotkey": hotkey, "nonce": nonce, "signature": "sig-placeholder"},
    )
    miner_token = token_resp.json()["access_token"]

    # Send authenticated heartbeat
    resp = await client.post(
        "/api/v1/miners/heartbeat",
        json={
            "hotkey": hotkey,
            "avg_latency_ms": 250,
            "supported_models": ["claude-3-5-sonnet-20241022"],
        },
        headers={"Authorization": f"Bearer {miner_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "miner_id" in data


@pytest.mark.asyncio
async def test_list_miners_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/miners")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_miners_authenticated(client: AsyncClient):
    # Register a user
    await client.post(
        "/api/v1/auth/register",
        json={"email": "miners_user@example.com", "password": "testpass123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "miners_user@example.com", "password": "testpass123"},
    )
    token = login_resp.json()["access_token"]

    resp = await client.get("/api/v1/miners", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
