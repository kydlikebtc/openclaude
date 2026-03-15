import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "securepassword123"},
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "anotherpassword"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "weakpass@example.com", "password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "logintest@example.com", "password": "securepassword123"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "logintest@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpw@example.com", "password": "securepassword123"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpw@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient) -> None:
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "metest@example.com", "password": "securepassword123"},
    )
    token = reg_response.json()["access_token"]
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "metest@example.com"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
