"""
API Key Pool Manager for OpenClade Miners.

Manages a pool of Claude API keys with:
- Round-robin load balancing across available keys
- Soft quarantine on authentication failures (exponential backoff)
- Automatic key restoration after quarantine period expires
- Thread-safe operations for concurrent request handling

Design: Keys are never permanently deleted — they're soft-quarantined.
This handles transient 429/503 errors gracefully without losing valid keys.
"""

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from loguru import logger


class APIKeyStatus(str, Enum):
    ACTIVE = "active"
    QUARANTINED = "quarantined"
    EXHAUSTED = "exhausted"  # hard-failed, requires manual intervention


@dataclass
class APIKeyEntry:
    """Represents a single API key with health tracking metadata."""

    key: str
    status: APIKeyStatus = APIKeyStatus.ACTIVE
    failure_count: int = 0
    quarantine_until: float = 0.0  # Unix timestamp
    total_requests: int = 0
    total_tokens: int = 0
    last_used_at: float = 0.0

    def is_available(self) -> bool:
        """Return True if this key can accept a new request right now."""
        if self.status == APIKeyStatus.EXHAUSTED:
            return False
        if self.status == APIKeyStatus.QUARANTINED:
            if time.time() >= self.quarantine_until:
                # Quarantine expired — restore to active
                logger.info(
                    f"API key ...{self.key[-4:]} quarantine expired, restoring to active"
                )
                self.status = APIKeyStatus.ACTIVE
                return True
            return False
        return True

    def quarantine(self, base_delay_sec: float = 2.0) -> None:
        """
        Soft-quarantine this key with exponential backoff.

        Backoff: 2^failure_count seconds, capped at 1 hour.
        After 10 consecutive failures, key is marked EXHAUSTED.
        """
        self.failure_count += 1
        if self.failure_count >= 10:
            logger.error(
                f"API key ...{self.key[-4:]} exhausted after {self.failure_count} failures"
            )
            self.status = APIKeyStatus.EXHAUSTED
            return

        delay = min(base_delay_sec ** self.failure_count, 3600.0)
        self.quarantine_until = time.time() + delay
        self.status = APIKeyStatus.QUARANTINED
        logger.warning(
            f"API key ...{self.key[-4:]} quarantined for {delay:.0f}s "
            f"(failure #{self.failure_count})"
        )

    def record_success(self, tokens_used: int = 0) -> None:
        """Reset failure counter and update usage stats on success."""
        self.failure_count = 0
        self.status = APIKeyStatus.ACTIVE
        self.total_requests += 1
        self.total_tokens += tokens_used
        self.last_used_at = time.time()


class APIKeyPool:
    """
    Thread-safe round-robin API key pool with quarantine support.

    Usage:
        pool = APIKeyPool(["sk-ant-...", "sk-ant-..."])
        key_entry = pool.acquire()
        try:
            result = call_claude(key_entry.key)
            pool.release(key_entry, success=True, tokens_used=150)
        except AuthenticationError:
            pool.release(key_entry, success=False, is_auth_error=True)
    """

    def __init__(self, api_keys: List[str]) -> None:
        if not api_keys:
            raise ValueError("APIKeyPool requires at least one API key")
        self._keys: List[APIKeyEntry] = [APIKeyEntry(key=k) for k in api_keys]
        self._index: int = 0
        self._lock = threading.Lock()
        logger.info(f"APIKeyPool initialized with {len(self._keys)} key(s)")

    def acquire(self) -> Optional[APIKeyEntry]:
        """
        Return the next available key in round-robin order.

        Returns None if ALL keys are quarantined or exhausted.
        Callers should handle None gracefully (e.g., return error to Validator).
        """
        with self._lock:
            available = [k for k in self._keys if k.is_available()]
            if not available:
                logger.error("APIKeyPool: no available keys")
                return None
            # Simple round-robin among available keys only
            entry = available[self._index % len(available)]
            self._index = (self._index + 1) % len(available)
            return entry

    def release(
        self,
        entry: APIKeyEntry,
        success: bool,
        tokens_used: int = 0,
        is_auth_error: bool = False,
    ) -> None:
        """
        Update key health after a request attempt.

        Args:
            entry: The key entry returned by acquire().
            success: True if Claude API call succeeded.
            tokens_used: Tokens consumed (for billing/stats tracking).
            is_auth_error: True when the failure was an AuthenticationError.
                           Auth errors use a longer initial backoff.
        """
        with self._lock:
            if success:
                entry.record_success(tokens_used)
                logger.debug(
                    f"API key ...{entry.key[-4:]} success, "
                    f"tokens={tokens_used}, total_requests={entry.total_requests}"
                )
            else:
                base_delay = 30.0 if is_auth_error else 2.0
                entry.quarantine(base_delay_sec=base_delay)

    def stats(self) -> List[dict]:
        """Return health stats for all keys (redacted)."""
        with self._lock:
            return [
                {
                    "key_suffix": f"...{e.key[-4:]}",
                    "status": e.status.value,
                    "failure_count": e.failure_count,
                    "total_requests": e.total_requests,
                    "total_tokens": e.total_tokens,
                    "quarantine_until": e.quarantine_until,
                }
                for e in self._keys
            ]

    def active_count(self) -> int:
        """Return the number of currently active (non-quarantined) keys."""
        return sum(1 for k in self._keys if k.is_available())

    @classmethod
    def from_config(cls, config: "MinerConfig") -> "APIKeyPool":  # noqa: F821
        """Create a pool from a MinerConfig instance."""
        return cls(config.api_keys)
