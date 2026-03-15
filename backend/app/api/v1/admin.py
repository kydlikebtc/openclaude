"""Admin management endpoints: user management, transaction overview."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.core.deps import AdminUser, DbDep
from app.models.miner import Transaction
from app.models.user import User

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class AdminUserRecord(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    status: str
    is_admin: bool
    balance: Decimal
    created_at: datetime


class AdminUserListResponse(BaseModel):
    items: list[AdminUserRecord]
    total: int


class AdminUserUpdate(BaseModel):
    status: str | None = None
    is_admin: bool | None = None


class AdminTransactionRecord(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID | None
    miner_id: uuid.UUID | None
    model: str
    tokens_in: int
    tokens_out: int
    cost: Decimal
    created_at: datetime


class AdminTransactionListResponse(BaseModel):
    items: list[AdminTransactionRecord]
    total: int


# ── User management ───────────────────────────────────────────────────────────

@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    _admin: AdminUser,
    db: DbDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
) -> AdminUserListResponse:
    """List all users with pagination. Admin only."""
    offset = (page - 1) * page_size
    base_query = select(User)
    count_query = select(func.count(User.id))

    if status_filter:
        base_query = base_query.where(User.status == status_filter)
        count_query = count_query.where(User.status == status_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    result = await db.execute(
        base_query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()
    logger.info("admin list users", count=len(users), page=page, admin_id=str(_admin.id))
    return AdminUserListResponse(
        items=[AdminUserRecord.model_validate(u) for u in users],
        total=total,
    )


@router.patch("/users/{user_id}", response_model=AdminUserRecord)
async def update_user(
    user_id: uuid.UUID,
    payload: AdminUserUpdate,
    _admin: AdminUser,
    db: DbDep,
) -> AdminUserRecord:
    """Update user status or admin flag. Admin only."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.status is not None:
        allowed_statuses = {"active", "suspended", "banned"}
        if payload.status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"status must be one of: {', '.join(allowed_statuses)}",
            )
        user.status = payload.status

    if payload.is_admin is not None:
        user.is_admin = payload.is_admin

    await db.flush()
    logger.info(
        "admin updated user",
        target_user_id=str(user_id),
        admin_id=str(_admin.id),
        changes=payload.model_dump(exclude_none=True),
    )
    return AdminUserRecord.model_validate(user)


# ── Transaction management ────────────────────────────────────────────────────

@router.get("/transactions", response_model=AdminTransactionListResponse)
async def list_transactions(
    _admin: AdminUser,
    db: DbDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    user_id: uuid.UUID | None = None,
    miner_id: uuid.UUID | None = None,
    days: int = Query(default=30, ge=1, le=365),
) -> AdminTransactionListResponse:
    """List all transactions with pagination and filters. Admin only."""
    offset = (page - 1) * page_size
    since = datetime.now(UTC) - timedelta(days=days)

    base_query = select(Transaction).where(Transaction.created_at >= since)
    count_query = select(func.count(Transaction.id)).where(Transaction.created_at >= since)

    if user_id:
        base_query = base_query.where(Transaction.user_id == user_id)
        count_query = count_query.where(Transaction.user_id == user_id)
    if miner_id:
        base_query = base_query.where(Transaction.miner_id == miner_id)
        count_query = count_query.where(Transaction.miner_id == miner_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    result = await db.execute(
        base_query.order_by(Transaction.created_at.desc()).offset(offset).limit(page_size)
    )
    transactions = result.scalars().all()
    logger.info(
        "admin list transactions",
        count=len(transactions),
        page=page,
        days=days,
        admin_id=str(_admin.id),
    )
    return AdminTransactionListResponse(
        items=[AdminTransactionRecord.model_validate(tx) for tx in transactions],
        total=total,
    )
