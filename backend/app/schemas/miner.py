"""Schemas for Miner management APIs."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ── Registration & basic ──────────────────────────────────────────────────────

class MinerRegisterRequest(BaseModel):
    hotkey: str = Field(..., description="Bittensor hotkey address")
    coldkey: str = Field(..., description="Bittensor coldkey address")
    name: str = Field(..., description="Display name for this miner")
    api_key: str = Field(..., description="Anthropic API key to register")
    supported_models: list[str] = Field(
        default=["claude-3-5-sonnet-20241022"],
        description="List of Claude model IDs this miner supports",
    )
    referral_code: str | None = Field(None, description="Referral code of an existing miner")


class MinerUpdateRequest(BaseModel):
    name: str | None = Field(None, description="Updated display name")
    coldkey: str | None = Field(None, description="Updated coldkey address")


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
    referred_by_id: uuid.UUID | None = None
    created_at: datetime


# ── Authentication ────────────────────────────────────────────────────────────

class MinerAuthRequest(BaseModel):
    hotkey: str = Field(..., description="Bittensor hotkey (public key)")
    signature: str = Field(..., description="Hotkey signature of the challenge nonce")
    nonce: str = Field(..., description="Challenge nonce obtained from /miners/auth/challenge")


class MinerAuthChallengeResponse(BaseModel):
    nonce: str
    expires_in: int = Field(description="Seconds until nonce expires")


class MinerTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    miner_id: uuid.UUID


# ── API Key management ────────────────────────────────────────────────────────

class MinerApiKeyCreate(BaseModel):
    api_key: str = Field(..., description="Anthropic API key")
    provider: str = Field(default="anthropic")


class MinerApiKeyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    provider: str
    status: str
    created_at: datetime


class MinerApiKeyUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|disabled)$")


# ── Scoring ───────────────────────────────────────────────────────────────────

class ScoreComponents(BaseModel):
    availability: float = Field(ge=0.0, le=1.0)
    latency_score: float = Field(ge=0.0, le=1.0)
    quality: float = Field(ge=0.0, le=1.0)
    consistency: float = Field(ge=0.0, le=1.0)
    efficiency: float = Field(ge=0.0, le=1.0)
    referral_bonus: float = Field(ge=0.0)
    final_score: float = Field(ge=0.0, le=1.0)


class MinerScoreResponse(BaseModel):
    miner_id: uuid.UUID
    current_score: float
    components: ScoreComponents
    history: list[ScoreComponents] = Field(default_factory=list, description="Last 10 score snapshots")


# ── Referral ──────────────────────────────────────────────────────────────────

class MinerReferralInfo(BaseModel):
    miner_id: uuid.UUID
    hotkey: str
    name: str
    level: int = Field(description="1 = direct, 2 = second-degree, 3 = third-degree")
    joined_at: datetime


class MinerReferralsResponse(BaseModel):
    referral_code: str
    total_referrals: int
    direct_referrals: int
    indirect_referrals: int
    referral_bonus_pct: float = Field(description="Current bonus percentage applied to score")
    referrals: list[MinerReferralInfo]


# ── Stake ─────────────────────────────────────────────────────────────────────

class MinerStakeResponse(BaseModel):
    miner_id: uuid.UUID
    hotkey: str
    stake_amount: Decimal
    minimum_stake: Decimal = Decimal("1000")
    meets_minimum: bool
    last_synced_at: datetime | None = None


# ── Pool ──────────────────────────────────────────────────────────────────────

class MinerPoolStatus(BaseModel):
    total_miners: int
    online_miners: int
    miners_by_model: dict[str, int]
