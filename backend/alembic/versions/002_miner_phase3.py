"""Miner Phase 3: referred_by_id, score history, miner auth tokens

Revision ID: 002
Revises: 001
Create Date: 2026-03-15

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add referred_by_id to miners (self-referential for referral tree)
    op.add_column(
        "miners",
        sa.Column(
            "referred_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("miners.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_miners_referred_by_id", "miners", ["referred_by_id"])

    # Miner score history table
    op.create_table(
        "miner_score_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("miner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("availability", sa.Float, nullable=False, server_default="0"),
        sa.Column("latency_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("quality", sa.Float, nullable=False, server_default="0"),
        sa.Column("consistency", sa.Float, nullable=False, server_default="0"),
        sa.Column("efficiency", sa.Float, nullable=False, server_default="0"),
        sa.Column("referral_bonus", sa.Float, nullable=False, server_default="0"),
        sa.Column("final_score", sa.Float, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["miner_id"], ["miners.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_miner_score_history_miner_id", "miner_score_history", ["miner_id"])
    op.create_index("ix_miner_score_history_created_at", "miner_score_history", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_miner_score_history_created_at")
    op.drop_index("ix_miner_score_history_miner_id")
    op.drop_table("miner_score_history")
    op.drop_index("ix_miners_referred_by_id", table_name="miners")
    op.drop_column("miners", "referred_by_id")
