import uuid
from decimal import Decimal

from sqlalchemy import DECIMAL, VARCHAR, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(VARCHAR(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    balance: Mapped[Decimal] = mapped_column(DECIMAL(20, 8), default=Decimal("0"), nullable=False)
    referred_by_miner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("miners.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(VARCHAR(20), default="active", nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, nullable=False)

    api_keys: Mapped[list["ApiKey"]] = relationship("ApiKey", back_populates="user")  # noqa: F821


class ApiKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "api_keys"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key_hash: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    key_prefix: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    name: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    rate_limit: Mapped[int] = mapped_column(default=1000, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="api_keys")
