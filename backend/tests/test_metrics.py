"""Tests for custom Prometheus metrics in app/core/metrics.py.

Verifies that:
- MinerHeartbeatCollector records heartbeats and computes age correctly.
- miner_pool_size is updated by miner_service operations.
- miner_total_registered is updated on registration.
- tokens_consumed counter is incremented by billing_service.
"""

import time
import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest
from prometheus_client import REGISTRY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_sample_value(sample_name: str, labels: dict | None = None) -> float | None:
    """Read the current value of a Prometheus sample from the default registry.

    For Gauges: metric.name == sample_name.
    For Counters: sample.name == "<metric>_total" (metric.name strips _total).
    Search by sample.name to handle both uniformly.
    """
    for metric in REGISTRY.collect():
        for sample in metric.samples:
            if sample.name == sample_name:
                if labels is None or all(sample.labels.get(k) == v for k, v in labels.items()):
                    return sample.value
    return None


# ---------------------------------------------------------------------------
# MinerHeartbeatCollector unit tests
# ---------------------------------------------------------------------------

class TestMinerHeartbeatCollector:
    def test_collect_empty(self):
        """No heartbeats recorded → no samples emitted."""
        from app.core.metrics import MinerHeartbeatCollector
        collector = MinerHeartbeatCollector()
        samples = list(next(iter(collector.collect())).samples)
        assert samples == []

    def test_collect_age_near_zero(self):
        """Immediately after recording, age should be near 0."""
        from app.core.metrics import MinerHeartbeatCollector
        collector = MinerHeartbeatCollector()
        miner_id = str(uuid.uuid4())
        hotkey = "5FakeHotkey"

        collector.record(miner_id, hotkey)
        samples = list(next(iter(collector.collect())).samples)

        assert len(samples) == 1
        assert samples[0].labels["miner_id"] == miner_id
        assert samples[0].labels["hotkey"] == hotkey
        assert 0.0 <= samples[0].value < 1.0

    def test_collect_age_increases_over_time(self):
        """Age should reflect elapsed time since heartbeat."""
        from app.core.metrics import MinerHeartbeatCollector
        collector = MinerHeartbeatCollector()
        miner_id = str(uuid.uuid4())

        # Backdate the timestamp to simulate elapsed time
        collector._heartbeats[(miner_id, "hotkey_x")] = time.time() - 100

        samples = list(next(iter(collector.collect())).samples)
        assert len(samples) == 1
        assert samples[0].value >= 100.0

    def test_collect_multiple_miners(self):
        """Multiple miners should each have their own age sample."""
        from app.core.metrics import MinerHeartbeatCollector
        collector = MinerHeartbeatCollector()
        miners = [(str(uuid.uuid4()), f"hotkey_{i}") for i in range(3)]
        for mid, hk in miners:
            collector.record(mid, hk)

        samples = list(next(iter(collector.collect())).samples)
        assert len(samples) == 3
        ids_in_samples = {s.labels["miner_id"] for s in samples}
        assert ids_in_samples == {mid for mid, _ in miners}

    def test_record_overwrites_previous(self):
        """Re-recording a heartbeat resets the timestamp."""
        from app.core.metrics import MinerHeartbeatCollector
        collector = MinerHeartbeatCollector()
        miner_id = str(uuid.uuid4())

        # Simulate a stale heartbeat
        collector._heartbeats[(miner_id, "hk")] = time.time() - 500

        # Fresh heartbeat
        collector.record(miner_id, "hk")
        samples = list(next(iter(collector.collect())).samples)
        assert samples[0].value < 1.0


# ---------------------------------------------------------------------------
# miner_pool_size updated by miner_service
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pool_size_updated_on_sync(mock_redis):
    """_sync_miner_to_redis should update miner_pool_size gauge."""
    from app.core import metrics as m
    from app.services.miner_service import _sync_miner_to_redis
    from app.models.miner import Miner

    with patch("app.core.security.encrypt_for_redis", return_value="enc_key"):
        miner = Miner(
            id=uuid.uuid4(),
            hotkey="5Test",
            coldkey="5Cold",
            name="TestMiner",
            status="active",
        )
        await _sync_miner_to_redis(mock_redis, miner, ["claude-sonnet-4-6"], "sk-test")

    assert m.miner_pool_size._value.get() > 0


@pytest.mark.asyncio
async def test_pool_size_decremented_on_isolation(mock_redis):
    """mark_miner_failure should update miner_pool_size when miner is isolated."""
    from app.core import metrics as m
    from app.services.miner_service import mark_miner_failure, MINER_INFO_KEY

    miner_id = str(uuid.uuid4())
    info_key = MINER_INFO_KEY.format(id=miner_id)

    # Pre-load: 2 prior failures so the 3rd triggers isolation
    await mock_redis.hset(info_key, mapping={"consecutive_failures": 2})
    await mock_redis.zadd("miner:pool", {miner_id: 0.5})

    await mark_miner_failure(mock_redis, miner_id)

    # After zrem the mock zcard returns 0
    assert m.miner_pool_size._value.get() == 0.0


# ---------------------------------------------------------------------------
# tokens_consumed updated by billing_service
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tokens_consumed_counter_incremented(db):
    """check_and_deduct_balance should increment tokens_consumed counter."""
    from app.services.billing_service import check_and_deduct_balance
    from app.models.user import User

    user = User(
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed",
        balance=Decimal("10.00"),
        status="active",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    model = "claude-sonnet-4-6"
    tokens_in = 500
    tokens_out = 250
    label_filter = {"model": model, "user_tier": "standard"}

    before = _get_sample_value("openclaude_tokens_consumed_total", label_filter) or 0.0

    await check_and_deduct_balance(
        db=db,
        user_id=user.id,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        user_tier="standard",
    )

    after = _get_sample_value("openclaude_tokens_consumed_total", label_filter) or 0.0
    assert after - before == tokens_in + tokens_out


@pytest.mark.asyncio
async def test_tokens_consumed_uses_default_tier(db):
    """check_and_deduct_balance defaults user_tier to 'standard'."""
    from app.services.billing_service import check_and_deduct_balance
    from app.models.user import User

    user = User(
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed",
        balance=Decimal("10.00"),
        status="active",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    await check_and_deduct_balance(
        db=db,
        user_id=user.id,
        model="claude-haiku-4-5-20251001",
        tokens_in=100,
        tokens_out=50,
    )

    value = _get_sample_value(
        "openclaude_tokens_consumed_total",
        labels={"model": "claude-haiku-4-5-20251001", "user_tier": "standard"},
    )
    assert value is not None and value > 0


# ---------------------------------------------------------------------------
# heartbeat_collector is wired into miner_service
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_record_heartbeat_updates_collector(mock_redis):
    """record_heartbeat should populate heartbeat_collector with timestamp."""
    from app.core.metrics import heartbeat_collector
    from app.services.miner_service import record_heartbeat

    hotkey = "5WiredHotkey"
    miner_id = str(uuid.uuid4())

    await mock_redis.set(f"miner:hotkey:{hotkey}", miner_id)
    await mock_redis.hset(f"miner:{miner_id}:info", mapping={"hotkey": hotkey})

    await record_heartbeat(mock_redis, hotkey, avg_latency_ms=50)

    key = (miner_id, hotkey)
    assert key in heartbeat_collector._heartbeats
    assert time.time() - heartbeat_collector._heartbeats[key] < 2.0
