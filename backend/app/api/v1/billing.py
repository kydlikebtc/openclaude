"""Billing endpoints: balance, recharge, transactions, usage stats."""

import uuid

import structlog
from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DbDep
from app.schemas.billing import (
    BalanceResponse,
    RechargeRequest,
    RechargeResponse,
    TransactionRecord,
    UsageSummary,
)
from app.services.billing_service import (
    get_recent_transactions,
    get_usage_summary,
    recharge_balance,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(current_user: CurrentUser) -> BalanceResponse:
    """Get current user balance."""
    return BalanceResponse(balance=current_user.balance)


@router.post("/recharge", response_model=RechargeResponse, status_code=status.HTTP_201_CREATED)
async def recharge(
    payload: RechargeRequest,
    current_user: CurrentUser,
    db: DbDep,
) -> RechargeResponse:
    """Add funds to user balance (demo: directly credits, no actual payment)."""
    try:
        await recharge_balance(db, user_id=current_user.id, amount=payload.amount)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    logger.info("recharge completed", user_id=str(current_user.id), amount=str(payload.amount))
    return RechargeResponse(
        transaction_id=uuid.uuid4(),
        amount=payload.amount,
        payment_address="DEMO_ADDRESS_NOT_REAL",
        status="completed",
    )


@router.get("/transactions", response_model=list[TransactionRecord])
async def list_transactions(
    current_user: CurrentUser,
    db: DbDep,
    limit: int = 50,
) -> list[TransactionRecord]:
    """List recent transactions."""
    transactions = await get_recent_transactions(db, user_id=current_user.id, limit=limit)
    return [TransactionRecord.model_validate(tx) for tx in transactions]


@router.get("/usage", response_model=UsageSummary)
async def usage_summary(
    current_user: CurrentUser,
    db: DbDep,
    period: str = "month",
) -> UsageSummary:
    """Get usage summary for a time period (today/week/month)."""
    if period not in ("today", "week", "month"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="period must be one of: today, week, month",
        )
    summary = await get_usage_summary(db, user_id=current_user.id, period=period)
    return UsageSummary(**summary)
