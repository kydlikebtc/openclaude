"""Usage statistics endpoints: daily usage breakdown by model and date."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import cast, func, select
from sqlalchemy import Date as SADate

from app.core.deps import CurrentUser, DbDep
from app.models.miner import Transaction

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/usage", tags=["usage"])

_MAX_DATE_RANGE_DAYS = 90


class DailyUsageRecord(BaseModel):
    date: str  # ISO date string YYYY-MM-DD
    model: str
    requests: int
    tokens_in: int
    tokens_out: int
    cost: Decimal


class DailyUsageResponse(BaseModel):
    items: list[DailyUsageRecord]
    total_requests: int
    total_tokens_in: int
    total_tokens_out: int
    total_cost: Decimal
    start: str
    end: str


@router.get("/daily", response_model=DailyUsageResponse)
async def daily_usage(
    current_user: CurrentUser,
    db: DbDep,
    model: str | None = Query(default=None, description="Filter by model name"),
    start: date | None = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end: date | None = Query(default=None, description="End date (YYYY-MM-DD)"),
) -> DailyUsageResponse:
    """Get daily usage breakdown, optionally filtered by model and date range.

    Returns per-day, per-model aggregates within the requested window.
    Maximum window is 90 days; defaults to the last 30 days.
    """
    today = datetime.now(UTC).date()

    if end is None:
        end = today
    if start is None:
        start = end - timedelta(days=29)

    if start > end:
        raise HTTPException(status_code=400, detail="start must be before end")

    delta = (end - start).days
    if delta > _MAX_DATE_RANGE_DAYS:
        raise HTTPException(
            status_code=400,
            detail=f"Date range cannot exceed {_MAX_DATE_RANGE_DAYS} days",
        )

    start_dt = datetime(start.year, start.month, start.day, tzinfo=UTC)
    end_dt = datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=UTC)

    # Group by day (date portion) and model
    day_col = cast(Transaction.created_at, SADate).label("day")
    query = (
        select(
            day_col,
            Transaction.model,
            func.count(Transaction.id).label("requests"),
            func.sum(Transaction.tokens_in).label("tokens_in"),
            func.sum(Transaction.tokens_out).label("tokens_out"),
            func.sum(Transaction.cost).label("cost"),
        )
        .where(
            Transaction.user_id == current_user.id,
            Transaction.created_at >= start_dt,
            Transaction.created_at <= end_dt,
        )
        .group_by(day_col, Transaction.model)
        .order_by(day_col, Transaction.model)
    )

    if model:
        query = query.where(Transaction.model == model)

    result = await db.execute(query)
    rows = result.all()

    items = [
        DailyUsageRecord(
            date=str(row.day),
            model=row.model,
            requests=row.requests or 0,
            tokens_in=row.tokens_in or 0,
            tokens_out=row.tokens_out or 0,
            cost=row.cost or Decimal("0"),
        )
        for row in rows
    ]

    total_requests = sum(r.requests for r in items)
    total_tokens_in = sum(r.tokens_in for r in items)
    total_tokens_out = sum(r.tokens_out for r in items)
    total_cost = sum((r.cost for r in items), Decimal("0"))

    logger.info(
        "daily usage query",
        user_id=str(current_user.id),
        start=str(start),
        end=str(end),
        model=model,
        row_count=len(items),
    )

    return DailyUsageResponse(
        items=items,
        total_requests=total_requests,
        total_tokens_in=total_tokens_in,
        total_tokens_out=total_tokens_out,
        total_cost=total_cost,
        start=str(start),
        end=str(end),
    )
