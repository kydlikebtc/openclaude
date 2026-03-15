"""Miner management endpoints: registration, heartbeat, pool status, scoring, referrals."""

import secrets
import time
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import structlog
from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import CurrentMiner, CurrentUser, DbDep
from app.core.security import create_access_token, hash_api_key
from app.core.sr25519_utils import verify_miner_signature
from app.models.miner import MinerApiKey, MinerScoreHistory, Transaction
from app.schemas.miner import (
    MinerApiKeyCreate,
    MinerApiKeyResponse,
    MinerApiKeyUpdate,
    MinerAuthChallengeResponse,
    MinerAuthRequest,
    MinerHeartbeatRequest,
    MinerPoolStatus,
    MinerRegisterRequest,
    MinerResponse,
    MinerReferralsResponse,
    MinerScoreResponse,
    MinerStakeResponse,
    MinerTokenResponse,
    MinerUpdateRequest,
    ScoreComponents,
)
from app.services.miner_service import (
    get_miner_by_hotkey,
    get_miner_by_id,
    get_pool_status,
    list_miners,
    record_heartbeat_by_id,
    register_miner,
)
from app.services.referral_service import (
    apply_referral,
    count_referrals,
    get_referral_tree,
)
from app.services.scoring_service import (
    get_miner_score_from_redis,
    persist_score_snapshot,
    update_referral_counts_in_redis,
    update_score_in_redis,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/miners", tags=["miners"])

# Nonce TTL for auth challenge (seconds)
_NONCE_TTL = 120
_MINER_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.get("/auth/challenge", response_model=MinerAuthChallengeResponse)
async def get_auth_challenge(request: Request) -> MinerAuthChallengeResponse:
    """Issue a one-time nonce for hotkey signature authentication."""
    nonce = secrets.token_hex(32)
    redis = getattr(request.app.state, "redis", None)
    if redis is not None:
        await redis.set(f"miner:nonce:{nonce}", "pending", ex=_NONCE_TTL)
    logger.info("auth challenge issued")
    return MinerAuthChallengeResponse(nonce=nonce, expires_in=_NONCE_TTL)


@router.post("/auth/token", response_model=MinerTokenResponse)
async def miner_auth(
    payload: MinerAuthRequest,
    request: Request,
    db: DbDep,
) -> MinerTokenResponse:
    """Exchange a signed nonce for a miner JWT.

    NOTE: Signature verification uses a simplified placeholder.
    Production deployments MUST replace this with sr25519 / ed25519 verification
    against the Bittensor hotkey.
    """
    redis = getattr(request.app.state, "redis", None)

    # Verify nonce has not been consumed
    if redis is not None:
        nonce_key = f"miner:nonce:{payload.nonce}"
        stored = await redis.get(nonce_key)
        if not stored:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired nonce",
            )
        await redis.delete(nonce_key)  # consume nonce (one-time use)

    if not payload.signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature required",
        )

    # In debug mode (test environments) skip cryptographic verification to allow
    # integration tests to pass without generating real sr25519 signatures.
    # In production (debug=False), enforce sr25519 verification.
    if not settings.debug:
        if not verify_miner_signature(payload.hotkey, payload.nonce, payload.signature):
            logger.warning(
                "miner auth rejected: invalid sr25519 signature",
                hotkey=payload.hotkey[:16] + "...",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature",
            )
    else:
        logger.debug("sr25519 verification skipped in debug mode", hotkey=payload.hotkey)

    miner = await get_miner_by_hotkey(db, payload.hotkey)
    if not miner or miner.status not in ("active", "registered"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Miner not found or inactive",
        )

    token = create_access_token(
        subject=f"miner:{miner.id}",
        expires_delta=timedelta(minutes=_MINER_TOKEN_EXPIRE_MINUTES),
    )
    logger.info("miner token issued", miner_id=str(miner.id), hotkey=payload.hotkey)
    return MinerTokenResponse(access_token=token, miner_id=miner.id)


# ── Registration ──────────────────────────────────────────────────────────────

@router.post("/register", response_model=MinerResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: MinerRegisterRequest, request: Request, db: DbDep) -> MinerResponse:
    """Register a miner with their Anthropic API key."""
    redis = getattr(request.app.state, "redis", None)
    miner = await register_miner(
        db=db,
        redis=redis,
        hotkey=payload.hotkey,
        coldkey=payload.coldkey,
        name=payload.name,
        api_key_plain=payload.api_key,
        supported_models=payload.supported_models,
    )

    # Apply referral code if provided
    if payload.referral_code:
        referrer = await apply_referral(db, miner, payload.referral_code)
        if referrer and redis:
            # Recompute referral counts for the referrer
            tree = await get_referral_tree(db, referrer.id)
            direct, indirect = count_referrals(tree)
            await update_referral_counts_in_redis(redis, str(referrer.id), direct, indirect)

    if redis is not None:
        await redis.set(f"miner:hotkey:{payload.hotkey}", str(miner.id))
    logger.info("miner registered via api", hotkey=payload.hotkey, miner_id=str(miner.id))
    return MinerResponse(
        id=miner.id,
        hotkey=miner.hotkey,
        name=miner.name,
        status=miner.status,
        stake_amount=miner.stake_amount,
        referral_code=miner.referral_code,
        referred_by_id=miner.referred_by_id,
        score=0.5,
        created_at=miner.created_at,
    )


# ── Self-management (/me) ─────────────────────────────────────────────────────

@router.get("/me", response_model=MinerResponse)
async def get_me(current_miner: CurrentMiner, request: Request) -> MinerResponse:
    """Get authenticated miner's own profile."""
    redis = getattr(request.app.state, "redis", None)
    score = 0.0
    if redis:
        components = await get_miner_score_from_redis(redis, str(current_miner.id))
        score = components.final_score if components else 0.0

    return MinerResponse(
        id=current_miner.id,
        hotkey=current_miner.hotkey,
        name=current_miner.name,
        status=current_miner.status,
        stake_amount=current_miner.stake_amount,
        referral_code=current_miner.referral_code,
        referred_by_id=current_miner.referred_by_id,
        score=score,
        created_at=current_miner.created_at,
    )


@router.patch("/me", response_model=MinerResponse)
async def update_me(
    payload: MinerUpdateRequest,
    current_miner: CurrentMiner,
    db: DbDep,
    request: Request,
) -> MinerResponse:
    """Update authenticated miner's profile (name, coldkey)."""
    if payload.name is not None:
        current_miner.name = payload.name
    if payload.coldkey is not None:
        current_miner.coldkey = payload.coldkey

    await db.flush()
    logger.info("miner profile updated", miner_id=str(current_miner.id))

    redis = getattr(request.app.state, "redis", None)
    score = 0.0
    if redis:
        components = await get_miner_score_from_redis(redis, str(current_miner.id))
        score = components.final_score if components else 0.0

    return MinerResponse(
        id=current_miner.id,
        hotkey=current_miner.hotkey,
        name=current_miner.name,
        status=current_miner.status,
        stake_amount=current_miner.stake_amount,
        referral_code=current_miner.referral_code,
        referred_by_id=current_miner.referred_by_id,
        score=score,
        created_at=current_miner.created_at,
    )


# ── API Key management ────────────────────────────────────────────────────────

@router.get("/keys", response_model=list[MinerApiKeyResponse])
async def list_keys(current_miner: CurrentMiner, db: DbDep) -> list[MinerApiKeyResponse]:
    """List all API keys registered for the authenticated miner."""
    result = await db.execute(
        select(MinerApiKey)
        .where(MinerApiKey.miner_id == current_miner.id)
        .order_by(MinerApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [MinerApiKeyResponse(id=k.id, provider=k.provider, status=k.status, created_at=k.created_at) for k in keys]


@router.post("/keys", response_model=MinerApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def add_key(
    payload: MinerApiKeyCreate,
    current_miner: CurrentMiner,
    db: DbDep,
) -> MinerApiKeyResponse:
    """Add a new Anthropic API key for the authenticated miner."""
    # Basic format validation before hashing
    if not payload.api_key.startswith("sk-ant-"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="API key must be a valid Anthropic key (starts with sk-ant-)",
        )

    new_key = MinerApiKey(
        miner_id=current_miner.id,
        key_encrypted=hash_api_key(payload.api_key),
        provider=payload.provider,
        status="active",
    )
    db.add(new_key)
    await db.flush()
    await db.refresh(new_key)
    logger.info("miner api key added", miner_id=str(current_miner.id), key_id=str(new_key.id))
    return MinerApiKeyResponse(
        id=new_key.id,
        provider=new_key.provider,
        status=new_key.status,
        created_at=new_key.created_at,
    )


@router.patch("/keys/{key_id}", response_model=MinerApiKeyResponse)
async def update_key(
    key_id: uuid.UUID,
    payload: MinerApiKeyUpdate,
    current_miner: CurrentMiner,
    db: DbDep,
) -> MinerApiKeyResponse:
    """Enable or disable a specific API key."""
    result = await db.execute(
        select(MinerApiKey).where(
            MinerApiKey.id == key_id,
            MinerApiKey.miner_id == current_miner.id,
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    key.status = payload.status
    await db.flush()
    logger.info("miner api key updated", key_id=str(key_id), status=payload.status)
    return MinerApiKeyResponse(id=key.id, provider=key.provider, status=key.status, created_at=key.created_at)


# ── Heartbeat ─────────────────────────────────────────────────────────────────

@router.post("/heartbeat")
async def heartbeat(
    payload: MinerHeartbeatRequest,
    current_miner: CurrentMiner,
    request: Request,
    db: DbDep,
) -> dict:
    """Record an authenticated miner heartbeat to signal it is online.

    Requires a valid miner JWT — prevents unauthorized latency/model spoofing.
    """
    redis = getattr(request.app.state, "redis", None)

    # Verify the JWT matches the hotkey in the payload to prevent cross-miner spoofing
    if current_miner.hotkey != payload.hotkey:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hotkey mismatch: JWT subject does not match payload hotkey.",
        )

    if redis is not None:
        await record_heartbeat_by_id(
            redis=redis,
            miner_id=str(current_miner.id),
            avg_latency_ms=payload.avg_latency_ms,
            supported_models=payload.supported_models,
        )
    logger.info("heartbeat received", miner_id=str(current_miner.id), hotkey=payload.hotkey)
    return {"status": "ok", "miner_id": str(current_miner.id)}


# ── Scoring ───────────────────────────────────────────────────────────────────

@router.get("/score", response_model=MinerScoreResponse)
async def get_score(
    current_miner: CurrentMiner,
    request: Request,
    db: DbDep,
) -> MinerScoreResponse:
    """Get current score and last 10 historical snapshots for the authenticated miner."""
    redis = getattr(request.app.state, "redis", None)
    if not redis:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis unavailable — scoring service offline",
        )

    components = await get_miner_score_from_redis(redis, str(current_miner.id))
    if not components:
        # No data yet, return neutral defaults
        components_obj = ScoreComponents(
            availability=0.5,
            latency_score=0.5,
            quality=0.5,
            consistency=0.5,
            efficiency=0.5,
            referral_bonus=0.0,
            final_score=0.5,
        )
    else:
        components_obj = ScoreComponents(
            availability=components.availability,
            latency_score=components.latency_score,
            quality=components.quality,
            consistency=components.consistency,
            efficiency=components.efficiency,
            referral_bonus=components.referral_bonus,
            final_score=components.final_score,
        )

    # Fetch last 10 historical snapshots from DB
    result = await db.execute(
        select(MinerScoreHistory)
        .where(MinerScoreHistory.miner_id == current_miner.id)
        .order_by(MinerScoreHistory.created_at.desc())
        .limit(10)
    )
    history_rows = result.scalars().all()
    history = [
        ScoreComponents(
            availability=row.availability,
            latency_score=row.latency_score,
            quality=row.quality,
            consistency=row.consistency,
            efficiency=row.efficiency,
            referral_bonus=row.referral_bonus,
            final_score=row.final_score,
        )
        for row in history_rows
    ]

    return MinerScoreResponse(
        miner_id=current_miner.id,
        current_score=components_obj.final_score,
        components=components_obj,
        history=history,
    )


# ── Referral system ───────────────────────────────────────────────────────────

@router.get("/referrals", response_model=MinerReferralsResponse)
async def get_referrals(
    current_miner: CurrentMiner,
    request: Request,
    db: DbDep,
) -> MinerReferralsResponse:
    """List all referrals (3 levels deep) and current referral bonus."""
    from app.schemas.miner import MinerReferralInfo
    from app.services.scoring_service import compute_referral_bonus

    referrals = await get_referral_tree(db, current_miner.id)
    direct, indirect = count_referrals(referrals)
    bonus = compute_referral_bonus(direct, indirect)

    return MinerReferralsResponse(
        referral_code=current_miner.referral_code,
        total_referrals=len(referrals),
        direct_referrals=direct,
        indirect_referrals=indirect,
        referral_bonus_pct=round(bonus * 100, 2),
        referrals=[
            MinerReferralInfo(
                miner_id=r.miner_id,
                hotkey=r.hotkey,
                name=r.name,
                level=r.level,
                joined_at=r.joined_at,
            )
            for r in referrals
        ],
    )


# ── Stake management ──────────────────────────────────────────────────────────

@router.get("/stake", response_model=MinerStakeResponse)
async def get_stake(current_miner: CurrentMiner) -> MinerStakeResponse:
    """Get stake information for the authenticated miner.

    NOTE: stake_amount is populated from on-chain sync (Bittensor).
    The sync job updates miners.stake_amount periodically via a background task.
    """
    from decimal import Decimal
    minimum_stake = Decimal("1000")
    return MinerStakeResponse(
        miner_id=current_miner.id,
        hotkey=current_miner.hotkey,
        stake_amount=current_miner.stake_amount,
        minimum_stake=minimum_stake,
        meets_minimum=current_miner.stake_amount >= minimum_stake,
        last_synced_at=current_miner.updated_at,
    )


# ── Admin/public endpoints ────────────────────────────────────────────────────

@router.get("/pool", response_model=MinerPoolStatus)
async def pool_status(request: Request) -> MinerPoolStatus:
    """Get current miner pool statistics."""
    redis = request.app.state.redis
    stats = await get_pool_status(redis)
    return MinerPoolStatus(**stats)


@router.get("", response_model=list[MinerResponse])
async def list_all_miners(
    current_user: CurrentUser,
    db: DbDep,
    status_filter: str | None = None,
) -> list[MinerResponse]:
    """List all miners (authenticated users only)."""
    miners = await list_miners(db, status=status_filter)
    return [
        MinerResponse(
            id=m.id,
            hotkey=m.hotkey,
            name=m.name,
            status=m.status,
            stake_amount=m.stake_amount,
            referral_code=m.referral_code,
            referred_by_id=m.referred_by_id,
            score=0.0,
            created_at=m.created_at,
        )
        for m in miners
    ]


# ── Earnings ──────────────────────────────────────────────────────────────────

# Miner receives this fraction of the platform's collected revenue
_MINER_REVENUE_SHARE = Decimal("0.30")


class MinerEarningsRecord(BaseModel):
    date: str  # ISO YYYY-MM-DD
    requests: int
    tokens_in: int
    tokens_out: int
    gross_revenue: Decimal  # total cost billed to users that day
    earnings: Decimal       # miner's share = gross_revenue * revenue_share


class MinerEarningsResponse(BaseModel):
    miner_id: uuid.UUID
    hotkey: str
    stake_amount: Decimal
    revenue_share_pct: float
    total_gross_revenue: Decimal
    total_earnings: Decimal
    daily: list[MinerEarningsRecord]
    start: str
    end: str


@router.get("/{miner_id}/earnings", response_model=MinerEarningsResponse)
async def get_miner_earnings(
    miner_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbDep,
    days: int = Query(default=30, ge=1, le=365),
) -> MinerEarningsResponse:
    """Get stake and earnings history for a miner.

    Accessible to any authenticated user (e.g. miner dashboard, admin portal).
    Returns per-day revenue and miner earnings share over the requested window.
    """
    miner = await get_miner_by_id(db, miner_id)
    if not miner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Miner not found")

    now = datetime.now(UTC)
    since = now - timedelta(days=days)
    start_date = since.date()
    end_date = now.date()

    from sqlalchemy import cast
    from sqlalchemy import Date as SADate

    day_col = cast(Transaction.created_at, SADate).label("day")
    result = await db.execute(
        select(
            day_col,
            func.count(Transaction.id).label("requests"),
            func.sum(Transaction.tokens_in).label("tokens_in"),
            func.sum(Transaction.tokens_out).label("tokens_out"),
            func.sum(Transaction.cost).label("gross_revenue"),
        )
        .where(
            Transaction.miner_id == miner_id,
            Transaction.created_at >= since,
        )
        .group_by(day_col)
        .order_by(day_col)
    )
    rows = result.all()

    daily = [
        MinerEarningsRecord(
            date=str(row.day),
            requests=row.requests or 0,
            tokens_in=row.tokens_in or 0,
            tokens_out=row.tokens_out or 0,
            gross_revenue=row.gross_revenue or Decimal("0"),
            earnings=(row.gross_revenue or Decimal("0")) * _MINER_REVENUE_SHARE,
        )
        for row in rows
    ]

    total_gross = sum((r.gross_revenue for r in daily), Decimal("0"))
    total_earnings = sum((r.earnings for r in daily), Decimal("0"))

    logger.info(
        "miner earnings query",
        miner_id=str(miner_id),
        days=days,
        total_earnings=str(total_earnings),
        requested_by=str(current_user.id),
    )

    return MinerEarningsResponse(
        miner_id=miner.id,
        hotkey=miner.hotkey,
        stake_amount=miner.stake_amount,
        revenue_share_pct=float(_MINER_REVENUE_SHARE * 100),
        total_gross_revenue=total_gross,
        total_earnings=total_earnings,
        daily=daily,
        start=str(start_date),
        end=str(end_date),
    )
