"""Scoring engine for Miner quality evaluation.

Formula:
  score = availability × 0.2 + latency × 0.2 + quality × 0.4
          + consistency × 0.1 + efficiency × 0.1

Referral bonus (applied additively, capped at +10%):
  direct referral  → +5%
  second-degree    → +2%
  Capped at +10% total bonus.

Final score = min(score + referral_bonus, 1.0)
"""

import math
import uuid
from dataclasses import dataclass

import structlog
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.miner import MinerScoreHistory
from app.services.miner_service import MINER_INFO_KEY, MINER_POOL_KEY

logger = structlog.get_logger(__name__)

# Scoring weights
WEIGHT_AVAILABILITY = 0.2
WEIGHT_LATENCY = 0.2
WEIGHT_QUALITY = 0.4
WEIGHT_CONSISTENCY = 0.1
WEIGHT_EFFICIENCY = 0.1

# Referral bonus constants
DIRECT_BONUS = 0.05   # +5% per direct referral (level 1)
INDIRECT_BONUS = 0.02  # +2% per indirect referral (level 2-3)
MAX_REFERRAL_BONUS = 0.10  # hard cap

# Latency scoring: sub-200ms → close to 1.0, 2000ms+ → close to 0
LATENCY_OPTIMAL_MS = 200
LATENCY_DECAY_MS = 800


@dataclass
class ScoreComponents:
    availability: float
    latency_score: float
    quality: float
    consistency: float
    efficiency: float
    referral_bonus: float
    final_score: float


def latency_to_score(avg_latency_ms: float) -> float:
    """Convert avg latency in ms to a 0-1 score using exponential decay."""
    if avg_latency_ms <= 0:
        return 0.5  # No data yet — neutral score
    excess = max(0.0, avg_latency_ms - LATENCY_OPTIMAL_MS)
    return math.exp(-excess / LATENCY_DECAY_MS)


def compute_referral_bonus(direct_count: int, indirect_count: int) -> float:
    """Calculate referral bonus percentage (0.0 – MAX_REFERRAL_BONUS)."""
    bonus = direct_count * DIRECT_BONUS + indirect_count * INDIRECT_BONUS
    return min(bonus, MAX_REFERRAL_BONUS)


def compute_score(
    availability: float,
    latency_score: float,
    quality: float,
    consistency: float,
    efficiency: float,
    referral_bonus: float,
) -> ScoreComponents:
    """Compute the weighted score and apply referral bonus."""
    raw = (
        availability * WEIGHT_AVAILABILITY
        + latency_score * WEIGHT_LATENCY
        + quality * WEIGHT_QUALITY
        + consistency * WEIGHT_CONSISTENCY
        + efficiency * WEIGHT_EFFICIENCY
    )
    final = min(raw + referral_bonus, 1.0)
    return ScoreComponents(
        availability=round(availability, 4),
        latency_score=round(latency_score, 4),
        quality=round(quality, 4),
        consistency=round(consistency, 4),
        efficiency=round(efficiency, 4),
        referral_bonus=round(referral_bonus, 4),
        final_score=round(final, 4),
    )


async def get_miner_score_from_redis(redis: Redis, miner_id: str) -> ScoreComponents | None:
    """Read raw metrics from Redis and compute a ScoreComponents snapshot."""
    info_key = MINER_INFO_KEY.format(id=miner_id)
    info = await redis.hgetall(info_key)
    if not info:
        logger.warning("no redis info for miner", miner_id=miner_id)
        return None

    avg_latency_ms = float(info.get("avg_latency_ms", 0) or 0)
    consecutive_failures = int(info.get("consecutive_failures", 0) or 0)

    # Availability: penalise for consecutive failures
    availability = max(0.0, 1.0 - consecutive_failures * 0.2)

    # Latency score
    latency = latency_to_score(avg_latency_ms)

    # Quality / consistency / efficiency: pull from info hash if tracked,
    # otherwise use pool score as a proxy
    quality = float(info.get("quality", 0.5) or 0.5)
    consistency = float(info.get("consistency", 0.5) or 0.5)
    efficiency = float(info.get("efficiency", 0.5) or 0.5)

    # Referral counts stored in hash
    direct = int(info.get("direct_referrals", 0) or 0)
    indirect = int(info.get("indirect_referrals", 0) or 0)
    referral_bonus = compute_referral_bonus(direct, indirect)

    components = compute_score(availability, latency, quality, consistency, efficiency, referral_bonus)
    logger.debug(
        "score computed",
        miner_id=miner_id,
        final=components.final_score,
        latency_ms=avg_latency_ms,
    )
    return components


async def persist_score_snapshot(
    db: AsyncSession,
    miner_id: uuid.UUID,
    components: ScoreComponents,
) -> MinerScoreHistory:
    """Write a score snapshot to the DB for history/trend analysis."""
    snapshot = MinerScoreHistory(
        miner_id=miner_id,
        availability=components.availability,
        latency_score=components.latency_score,
        quality=components.quality,
        consistency=components.consistency,
        efficiency=components.efficiency,
        referral_bonus=components.referral_bonus,
        final_score=components.final_score,
    )
    db.add(snapshot)
    await db.flush()
    logger.info("score snapshot persisted", miner_id=str(miner_id), score=components.final_score)
    return snapshot


async def update_score_in_redis(redis: Redis, miner_id: str, components: ScoreComponents) -> None:
    """Push updated final score into the sorted pool set."""
    await redis.zadd(MINER_POOL_KEY, {miner_id: components.final_score})
    logger.debug("redis pool score updated", miner_id=miner_id, score=components.final_score)


async def update_referral_counts_in_redis(
    redis: Redis,
    miner_id: str,
    direct_count: int,
    indirect_count: int,
) -> None:
    """Persist referral counts into the miner info hash for scoring use."""
    info_key = MINER_INFO_KEY.format(id=miner_id)
    await redis.hset(
        info_key,
        mapping={
            "direct_referrals": direct_count,
            "indirect_referrals": indirect_count,
        },
    )
