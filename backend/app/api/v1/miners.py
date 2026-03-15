"""Miner management endpoints: registration, heartbeat, pool status."""

import structlog
from fastapi import APIRouter, HTTPException, Request, status

from app.core.deps import CurrentUser, DbDep
from app.schemas.miner import (
    MinerHeartbeatRequest,
    MinerPoolStatus,
    MinerRegisterRequest,
    MinerResponse,
)
from app.services.miner_service import (
    get_miner_by_hotkey,
    get_pool_status,
    list_miners,
    record_heartbeat_by_id,
    register_miner,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/miners", tags=["miners"])


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
        score=0.5,
        created_at=miner.created_at,
    )


@router.post("/heartbeat")
async def heartbeat(payload: MinerHeartbeatRequest, request: Request, db: DbDep) -> dict:
    """Record a miner heartbeat to signal it is online."""
    redis = getattr(request.app.state, "redis", None)
    miner_id = await redis.get(f"miner:hotkey:{payload.hotkey}") if redis else None
    if not miner_id:
        miner = await get_miner_by_hotkey(db, payload.hotkey)
        if not miner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Miner not found. Please register first.",
            )
        miner_id = str(miner.id)
        if redis is not None:
            await redis.set(f"miner:hotkey:{payload.hotkey}", miner_id)

    if redis is not None:
        await record_heartbeat_by_id(
            redis=redis,
            miner_id=str(miner_id),
            avg_latency_ms=payload.avg_latency_ms,
            supported_models=payload.supported_models,
        )
    return {"status": "ok", "miner_id": str(miner_id)}


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
            score=0.0,
            created_at=m.created_at,
        )
        for m in miners
    ]
