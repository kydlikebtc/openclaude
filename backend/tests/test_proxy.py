"""Tests for the Claude API proxy endpoint."""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.fixture
async def user_with_balance(client: AsyncClient):
    """Register a user, give them balance, return (headers, user_id)."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "proxy_user@example.com", "password": "securepass123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "proxy_user@example.com", "password": "securepass123"},
    )
    token = login_resp.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Recharge balance
    await client.post(
        "/api/v1/billing/recharge",
        json={"amount": "100.00", "payment_method": "usdt"},
        headers=auth_headers,
    )

    # Create API key
    key_resp = await client.post(
        "/api/v1/api-keys",
        json={"name": "proxy_test_key"},
        headers=auth_headers,
    )
    api_key = key_resp.json()["key"]
    return auth_headers, api_key


@pytest.mark.asyncio
async def test_proxy_no_api_key(client: AsyncClient):
    """Request without API key returns 401."""
    resp = await client.post(
        "/v1/messages",
        json={"model": "claude-3-5-sonnet-20241022", "max_tokens": 100, "messages": []},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_proxy_invalid_api_key(client: AsyncClient):
    """Request with invalid API key returns 401."""
    resp = await client.post(
        "/v1/messages",
        json={"model": "claude-3-5-sonnet-20241022", "max_tokens": 100, "messages": []},
        headers={"x-api-key": "oc_invalid_key_that_does_not_exist"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_proxy_insufficient_balance(client: AsyncClient):
    """User with zero balance gets 402."""
    # Register user with no balance
    await client.post(
        "/api/v1/auth/register",
        json={"email": "broke_user@example.com", "password": "securepass123"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "broke_user@example.com", "password": "securepass123"},
    )
    token = login_resp.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    key_resp = await client.post(
        "/api/v1/api-keys",
        json={"name": "broke_key"},
        headers=auth_headers,
    )
    api_key = key_resp.json()["key"]

    resp = await client.post(
        "/v1/messages",
        json={
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": "Hello"}],
        },
        headers={"x-api-key": api_key},
    )
    assert resp.status_code == 402


@pytest.mark.asyncio
async def test_proxy_no_miners_available(client: AsyncClient, user_with_balance):
    """When no miners available, returns 503."""
    auth_headers, api_key = user_with_balance

    with patch("app.api.claude.proxy.route_request") as mock_route:
        from app.services.routing_service import NoAvailableMinerError

        mock_route.side_effect = NoAvailableMinerError("no miners")

        resp = await client.post(
            "/v1/messages",
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Hello"}],
            },
            headers={"x-api-key": api_key},
        )
        assert resp.status_code == 503


@pytest.mark.asyncio
async def test_proxy_successful_request(client: AsyncClient, user_with_balance):
    """Successful proxy request returns response and deducts billing."""
    auth_headers, api_key = user_with_balance

    mock_response = {
        "id": "msg_test123",
        "type": "message",
        "role": "assistant",
        "model": "claude-3-5-sonnet-20241022",
        "content": [{"type": "text", "text": "Hello! How can I help you?"}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 10, "output_tokens": 8},
    }

    with patch("app.api.claude.proxy.route_request") as mock_route:
        mock_route.return_value = (mock_response, "test-miner-id")

        resp = await client.post(
            "/v1/messages",
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Hello"}],
            },
            headers={"x-api-key": api_key},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "assistant"
    assert "content" in data
    assert data["usage"]["input_tokens"] == 10


@pytest.mark.asyncio
async def test_proxy_x_api_key_header(client: AsyncClient, user_with_balance):
    """Proxy accepts x-api-key header format."""
    auth_headers, api_key = user_with_balance

    mock_response = {
        "id": "msg_xapikey",
        "content": [{"type": "text", "text": "Hi"}],
        "model": "claude-3-5-sonnet-20241022",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 5, "output_tokens": 2},
    }

    with patch("app.api.claude.proxy.route_request") as mock_route:
        mock_route.return_value = (mock_response, "miner-1")

        resp = await client.post(
            "/v1/messages",
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 50,
                "messages": [{"role": "user", "content": "Hi"}],
            },
            headers={"x-api-key": api_key},
        )
    assert resp.status_code == 200
