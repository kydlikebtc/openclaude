"""Integration tests for admin API endpoints."""

from decimal import Decimal

import pytest
from httpx import AsyncClient


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
async def regular_user_headers(client: AsyncClient):
    """Register and login a regular (non-admin) user."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "regular_admin_test@example.com", "password": "securepass123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "regular_admin_test@example.com", "password": "securepass123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def admin_user_headers(client: AsyncClient, db):
    """Register, promote to admin, and return auth headers."""
    from sqlalchemy import select
    from app.models.user import User

    await client.post(
        "/api/v1/auth/register",
        json={"email": "admin_user_test@example.com", "password": "securepass123"},
    )
    # Promote to admin directly in DB
    result = await db.execute(select(User).where(User.email == "admin_user_test@example.com"))
    user = result.scalar_one()
    user.is_admin = True
    await db.flush()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin_user_test@example.com", "password": "securepass123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def second_user_id(client: AsyncClient, db) -> str:
    """Create a second user and return their ID."""
    from sqlalchemy import select
    from app.models.user import User

    await client.post(
        "/api/v1/auth/register",
        json={"email": "second_user_admin_test@example.com", "password": "securepass123"},
    )
    result = await db.execute(select(User).where(User.email == "second_user_admin_test@example.com"))
    user = result.scalar_one()
    return str(user.id)


# ── Admin user list tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_users_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/admin/users")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_users_requires_admin(client: AsyncClient, regular_user_headers: dict):
    resp = await client.get("/api/v1/admin/users", headers=regular_user_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_users_admin_success(client: AsyncClient, admin_user_headers: dict):
    resp = await client.get("/api/v1/admin/users", headers=admin_user_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    # Each item should have required fields
    for item in data["items"]:
        assert "id" in item
        assert "email" in item
        assert "status" in item
        assert "is_admin" in item
        assert "balance" in item


@pytest.mark.asyncio
async def test_list_users_pagination(client: AsyncClient, admin_user_headers: dict):
    resp = await client.get("/api/v1/admin/users?page=1&page_size=1", headers=admin_user_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) <= 1


@pytest.mark.asyncio
async def test_list_users_status_filter(client: AsyncClient, admin_user_headers: dict):
    resp = await client.get("/api/v1/admin/users?status=active", headers=admin_user_headers)
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["status"] == "active"


# ── Admin user update tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_user_requires_admin(
    client: AsyncClient, regular_user_headers: dict, second_user_id: str
):
    resp = await client.patch(
        f"/api/v1/admin/users/{second_user_id}",
        json={"status": "suspended"},
        headers=regular_user_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_user_status_success(
    client: AsyncClient, admin_user_headers: dict, second_user_id: str
):
    resp = await client.patch(
        f"/api/v1/admin/users/{second_user_id}",
        json={"status": "suspended"},
        headers=admin_user_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "suspended"


@pytest.mark.asyncio
async def test_update_user_invalid_status(
    client: AsyncClient, admin_user_headers: dict, second_user_id: str
):
    resp = await client.patch(
        f"/api/v1/admin/users/{second_user_id}",
        json={"status": "invalid_status"},
        headers=admin_user_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_user_not_found(client: AsyncClient, admin_user_headers: dict):
    import uuid
    fake_id = str(uuid.uuid4())
    resp = await client.patch(
        f"/api/v1/admin/users/{fake_id}",
        json={"status": "suspended"},
        headers=admin_user_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_promote_user_to_admin(
    client: AsyncClient, admin_user_headers: dict, second_user_id: str
):
    resp = await client.patch(
        f"/api/v1/admin/users/{second_user_id}",
        json={"is_admin": True},
        headers=admin_user_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["is_admin"] is True


# ── Admin transaction list tests ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_transactions_requires_admin(client: AsyncClient, regular_user_headers: dict):
    resp = await client.get("/api/v1/admin/transactions", headers=regular_user_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_transactions_admin_success(client: AsyncClient, admin_user_headers: dict):
    resp = await client.get("/api/v1/admin/transactions", headers=admin_user_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_transactions_pagination(client: AsyncClient, admin_user_headers: dict):
    resp = await client.get(
        "/api/v1/admin/transactions?page=1&page_size=10", headers=admin_user_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) <= 10
