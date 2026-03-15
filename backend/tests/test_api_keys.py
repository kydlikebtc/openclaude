import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "securepassword123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "securepassword123"},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_create_api_key(client: AsyncClient) -> None:
    token = await get_auth_token(client, "keycreate@example.com")
    response = await client.post(
        "/api/v1/api-keys",
        json={"name": "My Key", "rate_limit": 500},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Key"
    assert data["rate_limit"] == 500
    assert "key" in data
    assert data["key"].startswith("oc_")
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_api_keys(client: AsyncClient) -> None:
    token = await get_auth_token(client, "keylist@example.com")
    await client.post(
        "/api/v1/api-keys",
        json={"name": "Key 1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/api-keys",
        json={"name": "Key 2"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = await client.get(
        "/api/v1/api-keys",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    keys = response.json()
    assert len(keys) == 2
    # Plaintext key is NOT returned in list
    assert all("key" not in k for k in keys)


@pytest.mark.asyncio
async def test_revoke_api_key(client: AsyncClient) -> None:
    token = await get_auth_token(client, "keyrevoke@example.com")
    create_resp = await client.post(
        "/api/v1/api-keys",
        json={"name": "Temp Key"},
        headers={"Authorization": f"Bearer {token}"},
    )
    key_id = create_resp.json()["id"]

    delete_resp = await client.delete(
        f"/api/v1/api-keys/{key_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_resp.status_code == 204

    list_resp = await client.get(
        "/api/v1/api-keys",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_revoke_other_users_key(client: AsyncClient) -> None:
    token1 = await get_auth_token(client, "user1keys@example.com")
    token2 = await get_auth_token(client, "user2keys@example.com")

    create_resp = await client.post(
        "/api/v1/api-keys",
        json={"name": "User1 Key"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    key_id = create_resp.json()["id"]

    # User 2 tries to delete user 1's key
    delete_resp = await client.delete(
        f"/api/v1/api-keys/{key_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert delete_resp.status_code == 404


@pytest.mark.asyncio
async def test_security_verify_api_key(client: AsyncClient) -> None:
    from app.core.security import verify_api_key
    from app.core.security import hash_api_key

    plain = "oc_test_key_12345"
    hashed = hash_api_key(plain)
    assert verify_api_key(plain, hashed) is True
    assert verify_api_key("wrong_key", hashed) is False
