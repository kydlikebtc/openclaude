"""Tests for the intelligent routing engine."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.routing_service import (
    NoAvailableMinerError,
    select_miner,
)


class TestSelectMiner:
    @pytest.fixture
    def redis_with_miners(self, mock_redis):
        """Pre-populate mock Redis with two active miners."""
        import asyncio

        async def setup():
            # Register model support
            await mock_redis.sadd("miner:model:claude-3-5-sonnet-20241022", "miner-1", "miner-2")
            # Add to pool with scores
            await mock_redis.zadd("miner:pool", {"miner-1": 0.8, "miner-2": 0.5})
            # Store miner info
            await mock_redis.hset(
                "miner:miner-1:info",
                mapping={"id": "miner-1", "api_key": "sk-ant-test-1", "avg_latency_ms": 200},
            )
            await mock_redis.hset(
                "miner:miner-2:info",
                mapping={"id": "miner-2", "api_key": "sk-ant-test-2", "avg_latency_ms": 400},
            )

        asyncio.get_event_loop().run_until_complete(setup())
        return mock_redis

    @pytest.mark.asyncio
    async def test_select_returns_candidate(self, redis_with_miners):
        candidate = await select_miner(redis_with_miners, "claude-3-5-sonnet-20241022")
        assert candidate.miner_id in ("miner-1", "miner-2")
        assert candidate.api_key.startswith("sk-ant-test")
        assert candidate.score > 0

    @pytest.mark.asyncio
    async def test_no_miners_raises(self, mock_redis):
        with pytest.raises(NoAvailableMinerError):
            await select_miner(mock_redis, "claude-3-5-sonnet-20241022")

    @pytest.mark.asyncio
    async def test_isolated_miners_excluded(self, redis_with_miners):
        """Isolated miners should not be selected."""
        # Isolate miner-1
        await redis_with_miners.set("miner:miner-1:isolated", "1")

        # Should always select miner-2
        for _ in range(10):
            candidate = await select_miner(redis_with_miners, "claude-3-5-sonnet-20241022")
            assert candidate.miner_id == "miner-2"

    @pytest.mark.asyncio
    async def test_all_isolated_raises(self, redis_with_miners):
        """If all miners isolated, should raise."""
        await redis_with_miners.set("miner:miner-1:isolated", "1")
        await redis_with_miners.set("miner:miner-2:isolated", "1")

        with pytest.raises(NoAvailableMinerError):
            await select_miner(redis_with_miners, "claude-3-5-sonnet-20241022")

    @pytest.mark.asyncio
    async def test_fallback_to_pool_when_no_model_set(self, mock_redis):
        """If no model-specific set, fall back to general pool."""
        await mock_redis.zadd("miner:pool", {"miner-fallback": 0.7})
        await mock_redis.hset(
            "miner:miner-fallback:info",
            mapping={"id": "miner-fallback", "api_key": "sk-ant-fallback", "avg_latency_ms": 100},
        )

        candidate = await select_miner(mock_redis, "unknown-model-xyz")
        assert candidate.miner_id == "miner-fallback"


class TestMinerFailures:
    @pytest.mark.asyncio
    async def test_mark_failure_increments_counter(self, mock_redis):
        from app.services.miner_service import mark_miner_failure

        await mock_redis.hset("miner:test-id:info", mapping={"consecutive_failures": 0})
        failures = await mark_miner_failure(mock_redis, "test-id")
        assert failures == 1

    @pytest.mark.asyncio
    async def test_three_failures_isolates_miner(self, mock_redis):
        from app.services.miner_service import mark_miner_failure

        # Pre-add to pool
        await mock_redis.zadd("miner:pool", {"test-id": 0.5})
        await mock_redis.hset("miner:test-id:info", mapping={"consecutive_failures": 2})

        failures = await mark_miner_failure(mock_redis, "test-id")
        assert failures == 3

        # Should be isolated
        isolated = await mock_redis.exists("miner:test-id:isolated")
        assert isolated == 1

    @pytest.mark.asyncio
    async def test_reset_failures(self, mock_redis):
        from app.services.miner_service import reset_miner_failures

        await mock_redis.hset("miner:test-id:info", mapping={"consecutive_failures": 2})
        await reset_miner_failures(mock_redis, "test-id")

        info = await mock_redis.hgetall("miner:test-id:info")
        assert info["consecutive_failures"] == 0
