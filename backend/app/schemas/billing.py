"""Schemas for billing and usage APIs."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class BalanceResponse(BaseModel):
    balance: Decimal
    currency: str = "USD"


class RechargeRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Amount in USD to recharge")
    payment_method: str = Field(default="usdt", description="Payment method: usdt, usdc, tao")


class RechargeResponse(BaseModel):
    transaction_id: uuid.UUID
    amount: Decimal
    payment_address: str
    status: str = "pending"


class TransactionRecord(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    model: str
    tokens_in: int
    tokens_out: int
    cost: Decimal
    created_at: datetime


class UsageSummary(BaseModel):
    total_requests: int
    total_tokens_in: int
    total_tokens_out: int
    total_cost: Decimal
    period: str  # "today", "week", "month"


class DailyUsage(BaseModel):
    date: str
    requests: int
    tokens_in: int
    tokens_out: int
    cost: Decimal


class ModelUsage(BaseModel):
    model: str
    requests: int
    tokens_in: int
    tokens_out: int
    cost: Decimal
