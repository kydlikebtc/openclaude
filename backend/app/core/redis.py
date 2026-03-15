import structlog
from redis.asyncio import Redis

from app.core.config import settings

logger = structlog.get_logger(__name__)

_redis_client: Redis | None = None


async def get_redis_client() -> Redis | None:  # pragma: no cover
    global _redis_client
    try:
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        await _redis_client.ping()
        logger.info("Redis connected", url=settings.redis_url)
        return _redis_client
    except Exception as e:
        logger.warning("Redis not available, running without cache/rate limiting", error=str(e))
        return None


async def close_redis_client() -> None:  # pragma: no cover
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis connection closed")
