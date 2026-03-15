"""Tests for API key service including authentication."""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.models.user import User
from app.services.api_key_service import (
    authenticate_by_api_key,
    create_api_key,
    list_api_keys,
    revoke_api_key,
)
from app.core.security import hash_password


class TestApiKeyService:
    @pytest_asyncio.fixture(autouse=True)
    async def setup_user(self, db):
        user = User(
            email="apikey_test@example.com",
            password_hash=hash_password("testpass123"),
            status="active",
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        self.user = user
        self.db = db

    @pytest.mark.asyncio
    async def test_create_api_key_returns_plaintext(self):
        api_key, plain_key = await create_api_key(self.db, self.user.id, "test-key")
        assert plain_key.startswith("oc_")
        assert len(plain_key) > 12
        assert api_key.key_prefix == plain_key[:12]

    @pytest.mark.asyncio
    async def test_list_api_keys_returns_active_only(self):
        api_key1, _ = await create_api_key(self.db, self.user.id, "key1")
        api_key2, _ = await create_api_key(self.db, self.user.id, "key2")

        keys = await list_api_keys(self.db, self.user.id)
        assert len(keys) >= 2

    @pytest.mark.asyncio
    async def test_revoke_api_key(self):
        api_key, _ = await create_api_key(self.db, self.user.id, "revoke-test")

        revoked = await revoke_api_key(self.db, api_key.id, self.user.id)
        assert revoked is True

        # Should not appear in active list
        keys = await list_api_keys(self.db, self.user.id)
        key_ids = [k.id for k in keys]
        assert api_key.id not in key_ids

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_key(self):
        import uuid

        revoked = await revoke_api_key(self.db, uuid.uuid4(), self.user.id)
        assert revoked is False

    @pytest.mark.asyncio
    async def test_authenticate_by_api_key_valid(self):
        _, plain_key = await create_api_key(self.db, self.user.id, "auth-test")

        result = await authenticate_by_api_key(self.db, plain_key)
        assert result is not None
        assert result.user_id == self.user.id

    @pytest.mark.asyncio
    async def test_authenticate_by_api_key_invalid(self):
        result = await authenticate_by_api_key(self.db, "oc_invalid_totally_fake_key_xyz")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_wrong_prefix_rejected(self):
        """Keys not starting with oc_ should be rejected immediately."""
        result = await authenticate_by_api_key(self.db, "sk-ant-notanoclaudekey")
        assert result is None

    @pytest.mark.asyncio
    async def test_revoked_key_not_authenticated(self):
        api_key, plain_key = await create_api_key(self.db, self.user.id, "will-revoke")
        await revoke_api_key(self.db, api_key.id, self.user.id)

        result = await authenticate_by_api_key(self.db, plain_key)
        assert result is None
