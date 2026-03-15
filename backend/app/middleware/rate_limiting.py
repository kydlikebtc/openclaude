"""Redis sliding window rate limiting middleware.

Each API key gets an independent rate limit window.
Default: 1000 RPM (requests per minute).
"""

import time

import structlog
from fastapi import Request, Response
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.core.config import settings

logger = structlog.get_logger(__name__)

RATE_LIMIT_WINDOW_SEC = 60  # 1 minute sliding window
GLOBAL_RPM_LIMIT = 10_000  # global safety cap
GLOBAL_RATE_KEY = "rate:global"

# Auth endpoint brute-force protection
AUTH_RATE_LIMIT_WINDOW_SEC = 300  # 5 minute window for auth endpoints
AUTH_RPM_LIMIT = 20  # max 20 login attempts per 5 minutes per IP
AUTH_PATHS = ("/api/v1/auth/login", "/api/v1/auth/register")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter using Redis sorted sets.

    - Per API-key limit based on the key's configured rate_limit
    - Global limit as safety cap
    - Auth endpoint brute-force protection (per IP)
    - Proxy paths only (skips health/docs)
    """

    BYPASS_PREFIXES = ("/health", "/docs", "/redoc", "/openapi")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # Skip health/docs entirely
        if any(path.startswith(prefix) for prefix in self.BYPASS_PREFIXES):
            return await call_next(request)

        redis: Redis | None = getattr(request.app.state, "redis", None)
        if redis is None:
            logger.warning("redis not available, skipping rate limit")
            return await call_next(request)

        # Auth endpoint brute-force protection (per IP, tighter window)
        if any(path.startswith(auth_path) for auth_path in AUTH_PATHS):
            client_ip = request.client.host if request.client else "unknown"
            auth_rate_key = f"rate:auth:{client_ip}"
            if not await self._check_limit_with_window(
                redis, auth_rate_key, AUTH_RPM_LIMIT, AUTH_RATE_LIMIT_WINDOW_SEC
            ):
                logger.warning("auth brute-force rate limit exceeded", client_ip=client_ip, path=path)
                return JSONResponse(
                    status_code=429,
                    content={
                        "type": "error",
                        "error": {
                            "type": "rate_limit_error",
                            "message": "Too many authentication attempts. Please wait before trying again.",
                        },
                    },
                    headers={"Retry-After": str(AUTH_RATE_LIMIT_WINDOW_SEC)},
                )
            return await call_next(request)

        # Check global limit first
        if not await self._check_limit(redis, GLOBAL_RATE_KEY, GLOBAL_RPM_LIMIT):
            logger.warning("global rate limit exceeded")
            return JSONResponse(
                status_code=429,
                content={
                    "type": "error",
                    "error": {"type": "rate_limit_error", "message": "Global rate limit exceeded"},
                },
                headers={"Retry-After": str(RATE_LIMIT_WINDOW_SEC)},
            )

        # Per API key limit (if API key provided)
        api_key = self._extract_api_key(request)
        if api_key:
            key_prefix = api_key[:12] if len(api_key) >= 12 else api_key
            rate_key = f"rate:key:{key_prefix}"

            # Get key-specific limit from Redis cache (default 1000 RPM)
            limit = await self._get_key_limit(redis, key_prefix)
            if not await self._check_limit(redis, rate_key, limit):
                logger.warning("api key rate limit exceeded", key_prefix=key_prefix)
                return JSONResponse(
                    status_code=429,
                    content={
                        "type": "error",
                        "error": {
                            "type": "rate_limit_error",
                            "message": f"Rate limit exceeded. Max {limit} requests per minute.",
                        },
                    },
                    headers={
                        "Retry-After": str(RATE_LIMIT_WINDOW_SEC),
                        "X-RateLimit-Limit": str(limit),
                    },
                )

        return await call_next(request)

    async def _check_limit(self, redis: Redis, key: str, limit: int) -> bool:
        """Sliding window check using default 60s window: True if request is allowed."""
        return await self._check_limit_with_window(redis, key, limit, RATE_LIMIT_WINDOW_SEC)

    async def _check_limit_with_window(
        self, redis: Redis, key: str, limit: int, window_sec: int
    ) -> bool:
        """Sliding window check with configurable window: True if request is allowed."""
        now = time.time()
        window_start = now - window_sec

        pipe = redis.pipeline()
        # Remove expired entries
        pipe.zremrangebyscore(key, 0, window_start)
        # Count current window entries
        pipe.zcard(key)
        # Add this request
        pipe.zadd(key, {str(now): now})
        # Set TTL to avoid key accumulation
        pipe.expire(key, window_sec * 2)
        results = await pipe.execute()

        current_count = results[1]  # count before adding current request
        return int(current_count) < limit

    def _extract_api_key(self, request: Request) -> str | None:
        """Extract API key from Authorization or x-api-key header."""
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            if token.startswith("oc_"):
                return token

        x_api_key = request.headers.get("x-api-key", "")
        if x_api_key.startswith("oc_"):
            return x_api_key

        return None

    async def _get_key_limit(self, redis: Redis, key_prefix: str) -> int:
        """Get cached rate limit for an API key prefix."""
        cached = await redis.get(f"rate:limit:{key_prefix}")
        if cached:
            return int(cached)
        return 1000  # default
