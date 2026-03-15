import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_api_key, hash_api_key, verify_api_key
from app.models.user import ApiKey

logger = structlog.get_logger(__name__)


async def create_api_key(
    db: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    rate_limit: int = 1000,
) -> tuple[ApiKey, str]:
    """Create a new API key. Returns (model, plaintext_key). Key is only accessible once."""
    plain_key = generate_api_key()
    key_prefix = plain_key[:12]  # "oc_" + 9 chars

    api_key = ApiKey(
        user_id=user_id,
        key_hash=hash_api_key(plain_key),
        key_prefix=key_prefix,
        name=name,
        rate_limit=rate_limit,
        is_active=True,
    )
    db.add(api_key)
    await db.flush()
    await db.refresh(api_key)
    logger.info("API key created", key_id=str(api_key.id), user_id=str(user_id), name=name)
    return api_key, plain_key


async def list_api_keys(db: AsyncSession, user_id: uuid.UUID) -> list[ApiKey]:
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == user_id, ApiKey.is_active == True)  # noqa: E712
        .order_by(ApiKey.created_at.desc())
    )
    return list(result.scalars().all())


async def revoke_api_key(db: AsyncSession, key_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        return False
    api_key.is_active = False
    logger.info("API key revoked", key_id=str(key_id), user_id=str(user_id))
    return True


async def authenticate_by_api_key(db: AsyncSession, plain_key: str) -> ApiKey | None:
    """Authenticate a request using an API key. O(n) but keys per user are few."""
    if not plain_key.startswith("oc_"):
        return None
    prefix = plain_key[:12]
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_prefix == prefix, ApiKey.is_active == True)  # noqa: E712
    )
    candidates = result.scalars().all()
    for key in candidates:
        if verify_api_key(plain_key, key.key_hash):
            return key
    return None
