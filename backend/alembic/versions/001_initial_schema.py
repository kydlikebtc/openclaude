"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # miners table (before users, since users references it)
    op.create_table(
        "miners",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("hotkey", sa.VARCHAR(100), nullable=False),
        sa.Column("coldkey", sa.VARCHAR(100), nullable=False),
        sa.Column("name", sa.VARCHAR(100), nullable=False),
        sa.Column("status", sa.VARCHAR(20), nullable=False, server_default="active"),
        sa.Column("stake_amount", sa.DECIMAL(20, 8), nullable=False, server_default="0"),
        sa.Column("referral_code", sa.VARCHAR(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hotkey"),
        sa.UniqueConstraint("referral_code"),
    )
    op.create_index("ix_miners_hotkey", "miners", ["hotkey"])
    op.create_index("ix_miners_referral_code", "miners", ["referral_code"])

    # users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.VARCHAR(255), nullable=False),
        sa.Column("password_hash", sa.VARCHAR(255), nullable=False),
        sa.Column("balance", sa.DECIMAL(20, 8), nullable=False, server_default="0"),
        sa.Column("referred_by_miner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.VARCHAR(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.ForeignKeyConstraint(["referred_by_miner_id"], ["miners.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # api_keys table
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key_hash", sa.VARCHAR(255), nullable=False),
        sa.Column("key_prefix", sa.VARCHAR(20), nullable=False),
        sa.Column("name", sa.VARCHAR(100), nullable=False),
        sa.Column("rate_limit", sa.Integer, nullable=False, server_default="1000"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_api_keys_user_id", "api_keys", ["user_id"])
    op.create_index("ix_api_keys_key_prefix", "api_keys", ["key_prefix"])

    # miner_api_keys table
    op.create_table(
        "miner_api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("miner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key_encrypted", sa.Text, nullable=False),
        sa.Column("provider", sa.VARCHAR(50), nullable=False, server_default="anthropic"),
        sa.Column("status", sa.VARCHAR(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["miner_id"], ["miners.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_miner_api_keys_miner_id", "miner_api_keys", ["miner_id"])

    # transactions table
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("miner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("model", sa.VARCHAR(100), nullable=False),
        sa.Column("tokens_in", sa.Integer, nullable=False),
        sa.Column("tokens_out", sa.Integer, nullable=False),
        sa.Column("cost", sa.DECIMAL(20, 8), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["miner_id"], ["miners.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_index("ix_transactions_created_at", "transactions", ["created_at"])


def downgrade() -> None:
    op.drop_table("transactions")
    op.drop_table("miner_api_keys")
    op.drop_table("api_keys")
    op.drop_table("users")
    op.drop_table("miners")
