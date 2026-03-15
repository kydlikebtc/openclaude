"""
Tests for APIKeyPool — round-robin selection, quarantine, and recovery.
"""

import time

import pytest

from miner.api_pool import APIKeyEntry, APIKeyPool, APIKeyStatus


class TestAPIKeyEntry:
    def test_new_key_is_active(self):
        entry = APIKeyEntry(key="sk-ant-test-0001")
        assert entry.status == APIKeyStatus.ACTIVE
        assert entry.is_available()

    def test_quarantine_sets_status(self):
        entry = APIKeyEntry(key="sk-ant-test-0002")
        entry.quarantine(base_delay_sec=100.0)
        assert entry.status == APIKeyStatus.QUARANTINED
        assert not entry.is_available()

    def test_quarantine_expired_restores_active(self):
        entry = APIKeyEntry(key="sk-ant-test-0003")
        # Set quarantine to expire immediately
        entry.status = APIKeyStatus.QUARANTINED
        entry.quarantine_until = time.time() - 1  # already past
        assert entry.is_available()
        assert entry.status == APIKeyStatus.ACTIVE

    def test_10_failures_marks_exhausted(self):
        entry = APIKeyEntry(key="sk-ant-test-0004", failure_count=9)
        entry.quarantine(base_delay_sec=2.0)
        assert entry.status == APIKeyStatus.EXHAUSTED
        assert not entry.is_available()

    def test_exhausted_not_available(self):
        entry = APIKeyEntry(key="sk-ant-test-0005", status=APIKeyStatus.EXHAUSTED)
        assert not entry.is_available()

    def test_record_success_resets_failure_count(self):
        entry = APIKeyEntry(key="sk-ant-test-0006", failure_count=3)
        entry.record_success(tokens_used=100)
        assert entry.failure_count == 0
        assert entry.status == APIKeyStatus.ACTIVE
        assert entry.total_tokens == 100
        assert entry.total_requests == 1

    def test_exponential_backoff_increases_delay(self):
        entry = APIKeyEntry(key="sk-ant-test-0007")
        entry.quarantine(base_delay_sec=2.0)
        first_delay = entry.quarantine_until - time.time()
        assert first_delay > 0

        entry2 = APIKeyEntry(key="sk-ant-test-0008", failure_count=3)
        entry2.quarantine(base_delay_sec=2.0)
        second_delay = entry2.quarantine_until - time.time()
        assert second_delay > first_delay

    def test_quarantine_capped_at_3600(self):
        entry = APIKeyEntry(key="sk-ant-test-0009", failure_count=5)
        entry.quarantine(base_delay_sec=1000.0)
        delay = entry.quarantine_until - time.time()
        assert delay <= 3601  # max 1 hour + 1 sec tolerance


class TestAPIKeyPool:
    def test_init_requires_at_least_one_key(self):
        with pytest.raises(ValueError):
            APIKeyPool([])

    def test_acquire_returns_entry(self):
        pool = APIKeyPool(["sk-ant-a001", "sk-ant-b002"])
        entry = pool.acquire()
        assert entry is not None
        assert entry.key in ["sk-ant-a001", "sk-ant-b002"]

    def test_round_robin_across_keys(self):
        pool = APIKeyPool(["sk-ant-key-1", "sk-ant-key-2", "sk-ant-key-3"])
        seen_keys = set()
        for _ in range(6):
            entry = pool.acquire()
            seen_keys.add(entry.key)
        assert seen_keys == {"sk-ant-key-1", "sk-ant-key-2", "sk-ant-key-3"}

    def test_acquire_returns_none_when_all_quarantined(self):
        pool = APIKeyPool(["sk-ant-only-key"])
        entry = pool.acquire()
        pool.release(entry, success=False, is_auth_error=False)
        # Manually set quarantine far in future
        pool._keys[0].quarantine_until = time.time() + 9999
        pool._keys[0].status = APIKeyStatus.QUARANTINED
        result = pool.acquire()
        assert result is None

    def test_release_success_resets_failure_count(self):
        pool = APIKeyPool(["sk-ant-reset-test"])
        entry = pool.acquire()
        entry.failure_count = 3
        pool.release(entry, success=True, tokens_used=50)
        assert entry.failure_count == 0
        assert entry.total_tokens == 50

    def test_release_failure_quarantines_key(self):
        pool = APIKeyPool(["sk-ant-fail-key"])
        entry = pool.acquire()
        pool.release(entry, success=False, is_auth_error=False)
        assert entry.status == APIKeyStatus.QUARANTINED

    def test_release_auth_error_uses_longer_delay(self):
        pool = APIKeyPool(["sk-ant-auth-key"])
        entry = pool.acquire()
        pool.release(entry, success=False, is_auth_error=True)
        # Base delay is 30s for auth errors vs 2s for other errors
        assert entry.quarantine_until > time.time() + 20

    def test_active_count_decreases_on_quarantine(self):
        pool = APIKeyPool(["sk-ant-k1", "sk-ant-k2"])
        assert pool.active_count() == 2
        pool._keys[0].status = APIKeyStatus.QUARANTINED
        pool._keys[0].quarantine_until = time.time() + 9999
        assert pool.active_count() == 1

    def test_stats_returns_redacted_keys(self):
        pool = APIKeyPool(["sk-ant-mykey1234"])
        stats = pool.stats()
        assert len(stats) == 1
        assert stats[0]["key_suffix"] == "...1234"
        assert "key" not in stats[0]  # Full key never exposed
