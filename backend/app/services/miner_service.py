"""Miner management service: registration, heartbeat, pool management."""

import secrets
import string
import uuid

import structlog
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.miner import Miner, MinerApiKey

logger = structlog.get_logger(__name__)

# Redis key constants
MINER_POOL_KEY = "miner:pool"  # Sorted set, score = miner quality score
MINER_INFO_KEY = "miner:{id}:info"  # Hash, miner metadata
MINER_KEYS_KEY = "miner:{id}:keys"  # List, api key IDs
MINER_MODEL_KEY = "miner:model:{model}"  # Set, miner IDs supporting this model
MINER_HEARTBEAT_KEY = "miner:{id}:heartbeat"  # Timestamp of last heartbeat
HEARTBEAT_TTL = 120  # seconds — miner is considered offline after this
ISOLATION_KEY = "miner:{id}:isolated"
ISOLATION_TTL = 300  # 5 minutes isolation on 3+ consecutive failures


def _generate_referral_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "OC" + "".join(secrets.choice(alphabet) for _ in range(6))


async def register_miner(
    db: AsyncSession,
    redis: Redis,
    hotkey: str,
    coldkey: str,
    name: str,
    api_key_plain: str,
    supported_models: list[str],
) -> Miner:
    """Register a new miner and add it to the Redis pool."""
    result = await db.execute(select(Miner).where(Miner.hotkey == hotkey))
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing miner
        miner = existing
        miner.name = name
        miner.status = "active"
        logger.info("miner re-registered", miner_id=str(miner.id), hotkey=hotkey)
    else:
        miner = Miner(
            hotkey=hotkey,
            coldkey=coldkey,
            name=name,
            status="active",
            referral_code=_generate_referral_code(),
        )
        db.add(miner)
        await db.flush()
        await db.refresh(miner)
        logger.info("miner registered", miner_id=str(miner.id), hotkey=hotkey)

    # Store the encrypted API key
    from app.core.security import hash_api_key

    miner_key = MinerApiKey(
        miner_id=miner.id,
        key_encrypted=hash_api_key(api_key_plain),
        provider="anthropic",
        status="active",
    )
    db.add(miner_key)
    await db.flush()

    # Sync to Redis pool
    await _sync_miner_to_redis(redis, miner, supported_models, api_key_plain)

    return miner


async def _sync_miner_to_redis(
    redis: Redis,
    miner: Miner,
    supported_models: list[str],
    api_key_plain: str,
) -> None:
    """Push miner state into Redis pool structures.

    API keys are stored AES-256-GCM encrypted, not as plaintext.
    """
    from app.core.security import encrypt_for_redis

    miner_id = str(miner.id)

    # Store miner info hash — API key encrypted at rest in Redis
    info_key = MINER_INFO_KEY.format(id=miner_id)
    await redis.hset(
        info_key,
        mapping={
            "id": miner_id,
            "hotkey": miner.hotkey,
            "name": miner.name,
            "api_key": encrypt_for_redis(api_key_plain),
            "consecutive_failures": 0,
            "avg_latency_ms": 0,
        },
    )

    # Add to sorted pool with initial score of 0.5
    await redis.zadd(MINER_POOL_KEY, {miner_id: 0.5})

    # Register supported models
    for model in supported_models:
        model_key = MINER_MODEL_KEY.format(model=model)
        await redis.sadd(model_key, miner_id)

    logger.info("miner synced to redis", miner_id=miner_id, models=supported_models)


async def record_heartbeat(redis: Redis, hotkey: str, avg_latency_ms: int) -> bool:
    """Record a miner heartbeat. Returns True if miner is known, False otherwise."""
    import time

    # Find miner_id by hotkey via Redis scan (in production: maintain hotkey->id map)
    hb_key = f"miner:hotkey:{hotkey}"
    miner_id = await redis.get(hb_key)

    if not miner_id:
        logger.warning("heartbeat from unknown miner", hotkey=hotkey)
        return False

    heartbeat_key = MINER_HEARTBEAT_KEY.format(id=miner_id)
    await redis.set(heartbeat_key, str(time.time()), ex=HEARTBEAT_TTL)

    # Update latency in miner info
    info_key = MINER_INFO_KEY.format(id=miner_id)
    await redis.hset(info_key, "avg_latency_ms", avg_latency_ms)

    logger.info("heartbeat recorded", miner_id=miner_id, avg_latency_ms=avg_latency_ms)
    return True


async def record_heartbeat_by_id(
    redis: Redis, miner_id: str, avg_latency_ms: int, supported_models: list[str]
) -> None:
    """Record heartbeat by miner_id directly."""
    import time

    heartbeat_key = MINER_HEARTBEAT_KEY.format(id=miner_id)
    await redis.set(heartbeat_key, str(time.time()), ex=HEARTBEAT_TTL)

    info_key = MINER_INFO_KEY.format(id=miner_id)
    await redis.hset(info_key, "avg_latency_ms", avg_latency_ms)

    # Update model support
    for model in supported_models:
        model_key = MINER_MODEL_KEY.format(model=model)
        await redis.sadd(model_key, miner_id)

    logger.info("heartbeat recorded", miner_id=miner_id, avg_latency_ms=avg_latency_ms)


async def mark_miner_failure(redis: Redis, miner_id: str) -> int:
    """Increment failure count. Isolate miner if ≥3 consecutive failures."""
    info_key = MINER_INFO_KEY.format(id=miner_id)
    failures = await redis.hincrby(info_key, "consecutive_failures", 1)

    if failures >= 3:
        isolation_key = ISOLATION_KEY.format(id=miner_id)
        await redis.set(isolation_key, "1", ex=ISOLATION_TTL)
        # Remove from active pool
        await redis.zrem(MINER_POOL_KEY, miner_id)
        logger.warning("miner isolated due to failures", miner_id=miner_id, failures=failures)
    else:
        logger.info("miner failure recorded", miner_id=miner_id, failures=failures)

    return int(failures)


async def reset_miner_failures(redis: Redis, miner_id: str) -> None:
    """Reset failure counter after a successful request."""
    info_key = MINER_INFO_KEY.format(id=miner_id)
    await redis.hset(info_key, "consecutive_failures", 0)


async def update_miner_score(redis: Redis, miner_id: str, score: float) -> None:
    """Update miner score in the sorted pool set."""
    isolation_key = ISOLATION_KEY.format(id=miner_id)
    is_isolated = await redis.exists(isolation_key)

    if not is_isolated:
        await redis.zadd(MINER_POOL_KEY, {miner_id: score})
        logger.info("miner score updated", miner_id=miner_id, score=score)


async def get_miner_by_hotkey(db: AsyncSession, hotkey: str) -> Miner | None:
    result = await db.execute(select(Miner).where(Miner.hotkey == hotkey))
    return result.scalar_one_or_none()


async def get_miner_by_id(db: AsyncSession, miner_id: uuid.UUID) -> Miner | None:
    result = await db.execute(select(Miner).where(Miner.id == miner_id))
    return result.scalar_one_or_none()


async def list_miners(db: AsyncSession, status: str | None = None) -> list[Miner]:
    query = select(Miner)
    if status:
        query = query.where(Miner.status == status)
    result = await db.execute(query.order_by(Miner.created_at.desc()))
    return list(result.scalars().all())


async def get_pool_status(redis: Redis | None) -> dict:
    """Return current pool statistics from Redis. Returns defaults if Redis unavailable."""
    if redis is None:
        return {"total_miners": 0, "online_miners": 0, "miners_by_model": {}}
    total_in_pool = await redis.zcard(MINER_POOL_KEY)

    # Count online by heartbeat (approximate — only pool members)
    online = total_in_pool  # Simplified; in production check heartbeat TTL

    return {
        "total_miners": int(total_in_pool),
        "online_miners": int(online),
        "miners_by_model": {},  # TODO: iterate model keys
    }
