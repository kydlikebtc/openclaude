"""Integration tests for Phase 3 Miner API endpoints."""

import pytest
from httpx import AsyncClient


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _register_miner(client: AsyncClient, hotkey: str, name: str = "Test Miner") -> dict:
    resp = await client.post(
        "/api/v1/miners/register",
        json={
            "hotkey": hotkey,
            "coldkey": f"coldkey-{hotkey}",
            "name": name,
            "api_key": "sk-ant-test-key-xxxx",
            "supported_models": ["claude-3-5-sonnet-20241022"],
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _get_miner_token(client: AsyncClient, hotkey: str) -> str:
    """Get a JWT for a registered miner via the auth endpoint."""
    # Get nonce
    challenge_resp = await client.get("/api/v1/miners/auth/challenge")
    assert challenge_resp.status_code == 200
    nonce = challenge_resp.json()["nonce"]

    # Exchange for token
    token_resp = await client.post(
        "/api/v1/miners/auth/token",
        json={"hotkey": hotkey, "signature": "test-sig", "nonce": nonce},
    )
    assert token_resp.status_code == 200, token_resp.text
    return token_resp.json()["access_token"]


# ── Auth tests ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_auth_challenge_returns_nonce(client: AsyncClient):
    resp = await client.get("/api/v1/miners/auth/challenge")
    assert resp.status_code == 200
    data = resp.json()
    assert "nonce" in data
    assert data["expires_in"] == 120


@pytest.mark.asyncio
async def test_auth_token_success(client: AsyncClient):
    await _register_miner(client, "auth-hotkey-001")
    token = await _get_miner_token(client, "auth-hotkey-001")
    assert token.startswith("ey")  # JWT format


@pytest.mark.asyncio
async def test_auth_token_unknown_miner(client: AsyncClient):
    challenge_resp = await client.get("/api/v1/miners/auth/challenge")
    nonce = challenge_resp.json()["nonce"]
    resp = await client.post(
        "/api/v1/miners/auth/token",
        json={"hotkey": "nonexistent-hotkey", "signature": "sig", "nonce": nonce},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_auth_token_empty_signature(client: AsyncClient):
    await _register_miner(client, "auth-hotkey-empty-sig")
    challenge_resp = await client.get("/api/v1/miners/auth/challenge")
    nonce = challenge_resp.json()["nonce"]
    resp = await client.post(
        "/api/v1/miners/auth/token",
        json={"hotkey": "auth-hotkey-empty-sig", "signature": "", "nonce": nonce},
    )
    assert resp.status_code == 401


# ── /me tests ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/miners/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient):
    await _register_miner(client, "me-hotkey-001", "My Miner")
    token = await _get_miner_token(client, "me-hotkey-001")

    resp = await client.get("/api/v1/miners/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["hotkey"] == "me-hotkey-001"
    assert data["name"] == "My Miner"
    assert "score" in data


@pytest.mark.asyncio
async def test_update_me(client: AsyncClient):
    await _register_miner(client, "me-update-001", "Old Name")
    token = await _get_miner_token(client, "me-update-001")

    resp = await client.patch(
        "/api/v1/miners/me",
        json={"name": "New Name"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


# ── API Keys tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_keys_empty(client: AsyncClient):
    await _register_miner(client, "keys-hotkey-001")
    token = await _get_miner_token(client, "keys-hotkey-001")

    # Registration adds one key; list should have 1 entry
    resp = await client.get("/api/v1/miners/keys", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_add_key_success(client: AsyncClient):
    await _register_miner(client, "keys-add-001")
    token = await _get_miner_token(client, "keys-add-001")

    resp = await client.post(
        "/api/v1/miners/keys",
        json={"api_key": "sk-ant-new-key-001", "provider": "anthropic"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["provider"] == "anthropic"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_add_key_invalid_format(client: AsyncClient):
    await _register_miner(client, "keys-invalid-001")
    token = await _get_miner_token(client, "keys-invalid-001")

    resp = await client.post(
        "/api/v1/miners/keys",
        json={"api_key": "invalid-key-format"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_key_status(client: AsyncClient):
    await _register_miner(client, "keys-status-001")
    token = await _get_miner_token(client, "keys-status-001")

    # Add a key
    add_resp = await client.post(
        "/api/v1/miners/keys",
        json={"api_key": "sk-ant-status-test-key"},
        headers={"Authorization": f"Bearer {token}"},
    )
    key_id = add_resp.json()["id"]

    # Disable it
    resp = await client.patch(
        f"/api/v1/miners/keys/{key_id}",
        json={"status": "disabled"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "disabled"


@pytest.mark.asyncio
async def test_update_key_not_found(client: AsyncClient):
    await _register_miner(client, "keys-notfound-001")
    token = await _get_miner_token(client, "keys-notfound-001")

    import uuid
    fake_id = uuid.uuid4()
    resp = await client.patch(
        f"/api/v1/miners/keys/{fake_id}",
        json={"status": "disabled"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ── Score tests ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_score_endpoint(client: AsyncClient):
    await _register_miner(client, "score-hotkey-001")
    token = await _get_miner_token(client, "score-hotkey-001")

    resp = await client.get("/api/v1/miners/score", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "current_score" in data
    assert "components" in data
    assert "history" in data
    assert isinstance(data["history"], list)


# ── Referral tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_referrals_endpoint_empty(client: AsyncClient):
    await _register_miner(client, "ref-empty-001")
    token = await _get_miner_token(client, "ref-empty-001")

    resp = await client.get("/api/v1/miners/referrals", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_referrals"] == 0
    assert data["direct_referrals"] == 0
    assert "referral_code" in data


@pytest.mark.asyncio
async def test_register_with_referral_code(client: AsyncClient):
    """Registering with a referral code links the miner to the referrer."""
    referrer = await _register_miner(client, "ref-parent-001", "Referrer")
    ref_code = referrer["referral_code"]

    # Register a child using the referral code
    resp = await client.post(
        "/api/v1/miners/register",
        json={
            "hotkey": "ref-child-001",
            "coldkey": "coldkey-ref-child",
            "name": "Child Miner",
            "api_key": "sk-ant-child-key",
            "referral_code": ref_code,
        },
    )
    assert resp.status_code == 201
    child_data = resp.json()
    assert child_data["referred_by_id"] == referrer["id"]

    # Referrer should now have 1 direct referral
    token = await _get_miner_token(client, "ref-parent-001")
    refs_resp = await client.get("/api/v1/miners/referrals", headers={"Authorization": f"Bearer {token}"})
    refs_data = refs_resp.json()
    assert refs_data["direct_referrals"] == 1
    assert refs_data["total_referrals"] == 1


# ── Stake tests ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stake_endpoint(client: AsyncClient):
    await _register_miner(client, "stake-hotkey-001")
    token = await _get_miner_token(client, "stake-hotkey-001")

    resp = await client.get("/api/v1/miners/stake", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "stake_amount" in data
    assert "minimum_stake" in data
    assert "meets_minimum" in data
    assert data["meets_minimum"] is False  # new miner has 0 stake
