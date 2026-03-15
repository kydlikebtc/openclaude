"""Custom Prometheus metrics for OpenClade.

Defines 4 metrics referenced in alert_rules.yml:
- openclaude_miner_heartbeat_age_seconds (custom collector, computed at scrape time)
- openclaude_miner_pool_size (Gauge)
- openclaude_miner_total_registered (Gauge)
- openclaude_tokens_consumed_total (Counter)
"""

import time
from collections.abc import Generator

import structlog
from prometheus_client import Counter, Gauge
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.registry import Collector, REGISTRY

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Static metrics (set by service functions)
# ---------------------------------------------------------------------------

miner_pool_size = Gauge(
    "openclaude_miner_pool_size",
    "Number of miners currently active in the routing pool",
)

miner_total_registered = Gauge(
    "openclaude_miner_total_registered",
    "Total number of miners registered in the database",
)

tokens_consumed = Counter(
    "openclaude_tokens_consumed_total",
    "Total tokens consumed through the OpenClade proxy",
    ["model", "user_tier"],
)


# ---------------------------------------------------------------------------
# Dynamic heartbeat age collector
# ---------------------------------------------------------------------------

class MinerHeartbeatCollector(Collector):
    """Computes miner heartbeat age at Prometheus scrape time.

    Storing the raw timestamp and computing ``now - ts`` on each scrape
    ensures the gauge always reflects the true age even between heartbeats,
    which is what ``alert_rules.yml`` needs (``> 360`` threshold).
    """

    def __init__(self) -> None:
        # (miner_id, hotkey) -> last heartbeat unix timestamp
        self._heartbeats: dict[tuple[str, str], float] = {}

    def record(self, miner_id: str, hotkey: str) -> None:
        """Call this every time a miner heartbeat is received."""
        self._heartbeats[(miner_id, hotkey)] = time.time()
        logger.debug(
            "heartbeat timestamp recorded",
            miner_id=miner_id,
            hotkey=hotkey,
        )

    def collect(self) -> Generator:
        gauge = GaugeMetricFamily(
            "openclaude_miner_heartbeat_age_seconds",
            "Seconds elapsed since the miner last sent a heartbeat",
            labels=["miner_id", "hotkey"],
        )
        now = time.time()
        for (miner_id, hotkey), ts in list(self._heartbeats.items()):
            gauge.add_metric([miner_id, hotkey], now - ts)
        yield gauge


heartbeat_collector = MinerHeartbeatCollector()
REGISTRY.register(heartbeat_collector)
