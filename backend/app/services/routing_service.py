"""Intelligent routing engine for selecting and managing Miner requests.

Architecture:
  - Miner pool stored in Redis Sorted Set, scored by quality score
  - Weighted random selection (higher score = higher probability)
  - Automatic failover with exponential backoff
  - Isolation of miners with ≥3 consecutive failures
"""

import asyncio
import random
import time
from dataclasses import dataclass

import structlog
from redis.asyncio import Redis

from app.services.miner_service import (
    ISOLATION_KEY,
    MINER_INFO_KEY,
    MINER_MODEL_KEY,
    MINER_POOL_KEY,
    mark_miner_failure,
    reset_miner_failures,
)

logger = structlog.get_logger(__name__)

MAX_RETRIES = 3
BASE_BACKOFF_SEC = 1.0


@dataclass
class MinerCandidate:
    miner_id: str
    api_key: str
    score: float
    avg_latency_ms: int


class NoAvailableMinerError(Exception):
    """Raised when no miner can serve the request."""


async def select_miner(redis: Redis, model: str) -> MinerCandidate:
    """Select a miner using weighted random selection based on score.

    1. Get miners supporting the requested model
    2. Filter to those in the active pool (not isolated)
    3. Weighted random selection by score^2
    """
    # Get miners that support this model
    model_key = MINER_MODEL_KEY.format(model=model)
    model_miners = await redis.smembers(model_key)

    if not model_miners:
        # Fall back to any miner in pool
        logger.warning("no model-specific miners, using pool fallback", model=model)
        pool_entries = await redis.zrange(MINER_POOL_KEY, 0, -1, withscores=True)
        if not pool_entries:
            raise NoAvailableMinerError(f"no miners available for model={model}")
        model_miners = {entry[0] for entry in pool_entries}

    # Get scores from pool for candidates
    candidates: list[MinerCandidate] = []
    for miner_id in model_miners:
        # Skip isolated miners
        isolation_key = ISOLATION_KEY.format(id=miner_id)
        if await redis.exists(isolation_key):
            logger.debug("skipping isolated miner", miner_id=miner_id)
            continue

        # Get score from sorted set
        score = await redis.zscore(MINER_POOL_KEY, miner_id)
        if score is None:
            continue  # Not in active pool

        # Get api key and metadata
        info_key = MINER_INFO_KEY.format(id=miner_id)
        info = await redis.hgetall(info_key)
        if not info or not info.get("api_key"):
            logger.warning("miner missing api_key in redis", miner_id=miner_id)
            continue

        # Decrypt the API key — stored encrypted in Redis
        from app.core.security import decrypt_from_redis

        try:
            api_key_plain = decrypt_from_redis(info["api_key"])
        except Exception:
            logger.warning("failed to decrypt miner api_key, skipping miner", miner_id=miner_id)
            continue

        candidates.append(
            MinerCandidate(
                miner_id=miner_id,
                api_key=api_key_plain,
                score=float(score),
                avg_latency_ms=int(info.get("avg_latency_ms", 0)),
            )
        )

    if not candidates:
        raise NoAvailableMinerError(f"no active miners for model={model}")

    # Weighted random selection: weight = score^2 (favors higher-scoring miners)
    weights = [max(c.score**2, 0.001) for c in candidates]
    selected = random.choices(candidates, weights=weights, k=1)[0]

    logger.info(
        "miner selected",
        miner_id=selected.miner_id,
        score=selected.score,
        model=model,
        candidates_count=len(candidates),
    )
    return selected


async def route_request(
    redis: Redis,
    model: str,
    request_payload: dict,
    request_id: str,
) -> tuple[dict, str]:
    """Route a request through available miners with retry/failover.

    Returns:
        (response_body, miner_id)

    Raises:
        NoAvailableMinerError: if all miners fail
    """
    import httpx

    tried_miners: set[str] = set()
    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            candidate = await _select_excluding(redis, model, tried_miners)
        except NoAvailableMinerError:
            break

        tried_miners.add(candidate.miner_id)

        try:
            response = await _forward_to_miner(
                api_key=candidate.api_key,
                payload=request_payload,
                request_id=request_id,
            )
            # Success: reset failure counter
            await reset_miner_failures(redis, candidate.miner_id)
            return response, candidate.miner_id

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            logger.warning(
                "miner request failed",
                miner_id=candidate.miner_id,
                status_code=status_code,
                attempt=attempt,
                request_id=request_id,
            )

            if status_code in (401, 403):
                # API key invalid — mark as failure and immediately discard
                await mark_miner_failure(redis, candidate.miner_id)
                logger.error("miner api_key rejected, miner penalized", miner_id=candidate.miner_id)
            else:
                await mark_miner_failure(redis, candidate.miner_id)

            last_error = exc

        except (httpx.RequestError, asyncio.TimeoutError) as exc:
            logger.warning(
                "miner connection error",
                miner_id=candidate.miner_id,
                error=str(exc),
                attempt=attempt,
            )
            await mark_miner_failure(redis, candidate.miner_id)
            last_error = exc

        # Exponential backoff before next attempt
        if attempt < MAX_RETRIES - 1:
            backoff = BASE_BACKOFF_SEC * (2**attempt)
            logger.info("retry backoff", seconds=backoff, attempt=attempt + 1)
            await asyncio.sleep(backoff)

    raise NoAvailableMinerError(
        f"all {len(tried_miners)} miners failed for model={model}"
    ) from last_error


async def _select_excluding(
    redis: Redis,
    model: str,
    excluded: set[str],
) -> MinerCandidate:
    """Select a miner excluding already-tried ones."""
    model_key = MINER_MODEL_KEY.format(model=model)
    model_miners = await redis.smembers(model_key)
    if not model_miners:
        pool_entries = await redis.zrange(MINER_POOL_KEY, 0, -1, withscores=True)
        model_miners = {entry[0] for entry in pool_entries}

    candidates: list[MinerCandidate] = []
    for miner_id in model_miners:
        if miner_id in excluded:
            continue

        isolation_key = ISOLATION_KEY.format(id=miner_id)
        if await redis.exists(isolation_key):
            continue

        score = await redis.zscore(MINER_POOL_KEY, miner_id)
        if score is None:
            continue

        info_key = MINER_INFO_KEY.format(id=miner_id)
        info = await redis.hgetall(info_key)
        if not info or not info.get("api_key"):
            continue

        # Decrypt the API key — stored encrypted in Redis
        from app.core.security import decrypt_from_redis

        try:
            api_key_plain = decrypt_from_redis(info["api_key"])
        except Exception:
            logger.warning("failed to decrypt miner api_key, skipping miner", miner_id=miner_id)
            continue

        candidates.append(
            MinerCandidate(
                miner_id=miner_id,
                api_key=api_key_plain,
                score=float(score),
                avg_latency_ms=int(info.get("avg_latency_ms", 0)),
            )
        )

    if not candidates:
        raise NoAvailableMinerError("no candidates left after exclusion")

    weights = [max(c.score**2, 0.001) for c in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


async def _forward_to_miner(api_key: str, payload: dict, request_id: str) -> dict:
    """Forward request to Anthropic API using the miner's API key."""
    import httpx

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "x-request-id": request_id,
    }

    start_time = time.monotonic()
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()

    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    logger.info("miner request successful", elapsed_ms=elapsed_ms, request_id=request_id)
    return resp.json()
