"""Referral system service.

Manages 3-level referral trees:
  Level 1 (direct):   miner A referred miner B           → A gets +5%
  Level 2 (indirect): miner B referred miner C           → A gets +2%
  Level 3 (distant):  miner C referred miner D           → A gets +2%

Referral counts are cached in Redis for fast scoring access.
"""

import uuid
from dataclasses import dataclass

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.miner import Miner

logger = structlog.get_logger(__name__)

MAX_REFERRAL_DEPTH = 3


@dataclass
class ReferralInfo:
    miner_id: uuid.UUID
    hotkey: str
    name: str
    level: int
    joined_at: object  # datetime


async def resolve_referrer(db: AsyncSession, referral_code: str) -> Miner | None:
    """Look up a miner by referral code."""
    result = await db.execute(select(Miner).where(Miner.referral_code == referral_code))
    return result.scalar_one_or_none()


async def get_referral_tree(
    db: AsyncSession,
    miner_id: uuid.UUID,
    max_depth: int = MAX_REFERRAL_DEPTH,
) -> list[ReferralInfo]:
    """BFS traverse up to `max_depth` levels of direct referrals made by this miner."""
    results: list[ReferralInfo] = []
    current_level_ids: list[uuid.UUID] = [miner_id]

    for depth in range(1, max_depth + 1):
        if not current_level_ids:
            break
        stmt = select(Miner).where(Miner.referred_by_id.in_(current_level_ids))
        rows = (await db.execute(stmt)).scalars().all()
        next_level_ids: list[uuid.UUID] = []
        for m in rows:
            results.append(
                ReferralInfo(
                    miner_id=m.id,
                    hotkey=m.hotkey,
                    name=m.name,
                    level=depth,
                    joined_at=m.created_at,
                )
            )
            next_level_ids.append(m.id)
        current_level_ids = next_level_ids

    logger.info(
        "referral tree fetched",
        miner_id=str(miner_id),
        total=len(results),
        max_depth=max_depth,
    )
    return results


def count_referrals(referrals: list[ReferralInfo]) -> tuple[int, int]:
    """Return (direct_count, indirect_count) from a referral list."""
    direct = sum(1 for r in referrals if r.level == 1)
    indirect = sum(1 for r in referrals if r.level > 1)
    return direct, indirect


async def apply_referral(db: AsyncSession, miner: Miner, referral_code: str) -> Miner | None:
    """Link miner to their referrer if the referral_code is valid.

    Returns the referrer Miner on success, None if code is invalid or miner already referred.
    """
    if miner.referred_by_id is not None:
        logger.info("miner already has a referrer", miner_id=str(miner.id))
        return None

    referrer = await resolve_referrer(db, referral_code)
    if not referrer:
        logger.warning("invalid referral code", code=referral_code)
        return None

    if referrer.id == miner.id:
        logger.warning("self-referral attempt blocked", miner_id=str(miner.id))
        return None

    miner.referred_by_id = referrer.id
    logger.info(
        "referral applied",
        miner_id=str(miner.id),
        referrer_id=str(referrer.id),
        code=referral_code,
    )
    return referrer
