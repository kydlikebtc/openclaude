import structlog
from redis.asyncio import Redis
from redis.asyncio.sentinel import Sentinel

from app.core.config import settings

logger = structlog.get_logger(__name__)

_redis_client: Redis | None = None


def _parse_sentinel_hosts(hosts_str: str) -> list[tuple[str, int]]:
    """解析 'host1:26379,host2:26379' 格式的 Sentinel 地址列表。"""
    result = []
    for entry in hosts_str.split(","):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.rsplit(":", 1)
        host = parts[0]
        port = int(parts[1]) if len(parts) == 2 else 26379
        result.append((host, port))
    return result


def _build_redis_client() -> Redis:
    """
    根据配置构建 Redis 客户端。
    - 若 redis_sentinel_hosts 已配置，使用 Sentinel 高可用模式连接主节点。
    - 否则使用普通 URL 模式（单实例或现有连接池）。
    """
    if settings.redis_sentinel_hosts:
        sentinel_nodes = _parse_sentinel_hosts(settings.redis_sentinel_hosts)
        sentinel_kwargs: dict = {}
        connection_kwargs: dict = {"decode_responses": True}
        if settings.redis_sentinel_password:
            sentinel_kwargs["password"] = settings.redis_sentinel_password
            connection_kwargs["password"] = settings.redis_sentinel_password
        sentinel = Sentinel(
            sentinel_nodes,
            sentinel_kwargs=sentinel_kwargs,
            **connection_kwargs,
        )
        client = sentinel.master_for(
            settings.redis_sentinel_master_name,
            decode_responses=True,
        )
        logger.info(
            "Redis Sentinel mode",
            sentinels=settings.redis_sentinel_hosts,
            master=settings.redis_sentinel_master_name,
        )
        return client

    client = Redis.from_url(settings.redis_url, decode_responses=True)
    logger.info("Redis standalone mode", url=settings.redis_url)
    return client


async def get_redis_client() -> Redis | None:  # pragma: no cover
    global _redis_client
    try:
        _redis_client = _build_redis_client()
        await _redis_client.ping()
        logger.info("Redis connected")
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
