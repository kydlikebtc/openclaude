"""Billing service: token metering, cost calculation, balance management."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import ROUND_UP, Decimal

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.miner import Transaction
from app.models.user import User

logger = structlog.get_logger(__name__)

# Anthropic model pricing (per million tokens, in USD)
# Source: https://www.anthropic.com/pricing
MODEL_PRICING: dict[str, dict[str, Decimal]] = {
    "claude-opus-4-6": {"input": Decimal("15.00"), "output": Decimal("75.00")},
    "claude-sonnet-4-6": {"input": Decimal("3.00"), "output": Decimal("15.00")},
    "claude-haiku-4-5-20251001": {"input": Decimal("0.80"), "output": Decimal("4.00")},
    "claude-3-5-sonnet-20241022": {"input": Decimal("3.00"), "output": Decimal("15.00")},
    "claude-3-5-haiku-20241022": {"input": Decimal("0.80"), "output": Decimal("4.00")},
    "claude-3-opus-20240229": {"input": Decimal("15.00"), "output": Decimal("75.00")},
}
DEFAULT_PRICING = {"input": Decimal("3.00"), "output": Decimal("15.00")}


def calculate_cost(model: str, tokens_in: int, tokens_out: int) -> Decimal:
    """Calculate USD cost for a request.

    Cost = (input_tokens / 1_000_000 * input_price + output_tokens / 1_000_000 * output_price)
           * price_ratio (OpenClade discount)
    """
    pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)
    input_cost = Decimal(tokens_in) / Decimal("1000000") * pricing["input"]
    output_cost = Decimal(tokens_out) / Decimal("1000000") * pricing["output"]
    total = (input_cost + output_cost) * Decimal(str(settings.price_ratio))
    # Round up to nearest satoshi (8 decimal places)
    return total.quantize(Decimal("0.00000001"), rounding=ROUND_UP)


async def check_and_deduct_balance(
    db: AsyncSession,
    user_id: uuid.UUID,
    model: str,
    tokens_in: int,
    tokens_out: int,
    miner_id: uuid.UUID | None = None,
) -> Decimal:
    """Deduct usage cost from user balance. Returns cost deducted.

    Raises:
        ValueError: if user balance is insufficient
    """
    cost = calculate_cost(model, tokens_in, tokens_out)

    # Fetch user with row-level lock to prevent race conditions
    result = await db.execute(
        select(User).where(User.id == user_id).with_for_update()
    )
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError(f"User {user_id} not found")

    if user.balance < cost:
        raise ValueError(
            f"Insufficient balance: have {user.balance:.8f}, need {cost:.8f}"
        )

    user.balance = user.balance - cost
    logger.info(
        "balance deducted",
        user_id=str(user_id),
        cost=str(cost),
        new_balance=str(user.balance),
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )

    # Record transaction
    tx = Transaction(
        user_id=user_id,
        miner_id=miner_id,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost=cost,
    )
    db.add(tx)
    await db.flush()

    return cost


async def recharge_balance(
    db: AsyncSession,
    user_id: uuid.UUID,
    amount: Decimal,
) -> Decimal:
    """Add funds to user balance. Returns new balance."""
    if amount <= 0:
        raise ValueError("Recharge amount must be positive")

    result = await db.execute(
        select(User).where(User.id == user_id).with_for_update()
    )
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError(f"User {user_id} not found")

    user.balance = user.balance + amount
    logger.info(
        "balance recharged",
        user_id=str(user_id),
        amount=str(amount),
        new_balance=str(user.balance),
    )
    return user.balance


async def get_usage_summary(
    db: AsyncSession,
    user_id: uuid.UUID,
    period: str = "month",
) -> dict:
    """Return aggregated usage for a time period."""
    now = datetime.now(UTC)
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = now - timedelta(days=7)
    else:  # month
        start = now - timedelta(days=30)

    from app.models.miner import Transaction

    result = await db.execute(
        select(
            func.count(Transaction.id).label("total_requests"),
            func.sum(Transaction.tokens_in).label("total_tokens_in"),
            func.sum(Transaction.tokens_out).label("total_tokens_out"),
            func.sum(Transaction.cost).label("total_cost"),
        ).where(
            Transaction.user_id == user_id,
            Transaction.created_at >= start,
        )
    )
    row = result.one()
    return {
        "total_requests": row.total_requests or 0,
        "total_tokens_in": row.total_tokens_in or 0,
        "total_tokens_out": row.total_tokens_out or 0,
        "total_cost": row.total_cost or Decimal("0"),
        "period": period,
    }


async def get_recent_transactions(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[Transaction]:
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
