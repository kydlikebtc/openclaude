"""Schemas for Miner management APIs."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class MinerRegisterRequest(BaseModel):
    hotkey: str = Field(..., description="Bittensor hotkey address")
    coldkey: str = Field(..., description="Bittensor coldkey address")
    name: str = Field(..., description="Display name for this miner")
    api_key: str = Field(..., description="Anthropic API key to register")
    supported_models: list[str] = Field(
        default=["claude-3-5-sonnet-20241022"],
        description="List of Claude model IDs this miner supports",
    )


class MinerHeartbeatRequest(BaseModel):
    hotkey: str
    avg_latency_ms: int = Field(default=0, ge=0)
    supported_models: list[str] = Field(default=[])


class MinerResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    hotkey: str
    name: str
    status: str
    stake_amount: Decimal
    referral_code: str
    score: float = 0.0
    created_at: datetime


class MinerApiKeyCreate(BaseModel):
    api_key: str = Field(..., description="Anthropic API key")
    provider: str = Field(default="anthropic")


class MinerApiKeyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    provider: str
    status: str
    created_at: datetime


class MinerPoolStatus(BaseModel):
    total_miners: int
    online_miners: int
    miners_by_model: dict[str, int]
