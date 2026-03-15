import uuid
from decimal import Decimal

from sqlalchemy import DECIMAL, Float, VARCHAR, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Miner(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "miners"

    hotkey: Mapped[str] = mapped_column(VARCHAR(100), unique=True, nullable=False, index=True)
    coldkey: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    name: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    status: Mapped[str] = mapped_column(VARCHAR(20), default="active", nullable=False)
    stake_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(20, 8), default=Decimal("0"), nullable=False
    )
    referral_code: Mapped[str] = mapped_column(VARCHAR(20), unique=True, nullable=False, index=True)
    # Self-referential FK: who referred this miner (level-1 relationship)
    referred_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("miners.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    miner_api_keys: Mapped[list["MinerApiKey"]] = relationship(
        "MinerApiKey", back_populates="miner"
    )
    score_history: Mapped[list["MinerScoreHistory"]] = relationship(
        "MinerScoreHistory", back_populates="miner", order_by="MinerScoreHistory.created_at.desc()"
    )
    # Many-to-one: miner that referred this miner (parent)
    referrer: Mapped["Miner | None"] = relationship(
        "Miner",
        foreign_keys="[Miner.referred_by_id]",
        back_populates="referrals",
        remote_side="[Miner.id]",
        lazy="select",
    )
    # One-to-many: miners this miner has directly referred (children)
    referrals: Mapped[list["Miner"]] = relationship(
        "Miner",
        foreign_keys="[Miner.referred_by_id]",
        back_populates="referrer",
        lazy="select",
    )


class MinerApiKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "miner_api_keys"

    miner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("miners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key_encrypted: Mapped[str] = mapped_column(nullable=False)
    provider: Mapped[str] = mapped_column(VARCHAR(50), default="anthropic", nullable=False)
    status: Mapped[str] = mapped_column(VARCHAR(20), default="active", nullable=False)

    miner: Mapped["Miner"] = relationship("Miner", back_populates="miner_api_keys")


class MinerScoreHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persisted scoring snapshots for trend analysis and audit."""

    __tablename__ = "miner_score_history"

    miner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("miners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    availability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    latency_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    consistency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    efficiency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    referral_bonus: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    final_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    miner: Mapped["Miner"] = relationship("Miner", back_populates="score_history")


class Transaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transactions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    miner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("miners.id", ondelete="SET NULL"),
        nullable=True,
    )
    model: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    tokens_in: Mapped[int] = mapped_column(Integer, nullable=False)
    tokens_out: Mapped[int] = mapped_column(Integer, nullable=False)
    cost: Mapped[Decimal] = mapped_column(DECIMAL(20, 8), nullable=False)
