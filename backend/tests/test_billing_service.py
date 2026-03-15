"""Tests for billing service: cost calculation and balance management."""

from decimal import Decimal

import pytest
import pytest_asyncio

from app.models.user import User
from app.services.billing_service import (
    calculate_cost,
    check_and_deduct_balance,
    get_recent_transactions,
    get_usage_summary,
    recharge_balance,
)


class TestCalculateCost:
    def test_known_model_pricing(self):
        """Sonnet: $3/M input, $15/M output, at 25% price ratio."""
        cost = calculate_cost("claude-3-5-sonnet-20241022", tokens_in=1_000_000, tokens_out=1_000_000)
        # input: 1M * $3 * 0.25 = $0.75, output: 1M * $15 * 0.25 = $3.75 → $4.50
        assert cost == Decimal("4.50000000")

    def test_haiku_cheaper_than_sonnet(self):
        cost_haiku = calculate_cost("claude-haiku-4-5-20251001", tokens_in=1000, tokens_out=1000)
        cost_sonnet = calculate_cost("claude-3-5-sonnet-20241022", tokens_in=1000, tokens_out=1000)
        assert cost_haiku < cost_sonnet

    def test_zero_tokens(self):
        cost = calculate_cost("claude-3-5-sonnet-20241022", tokens_in=0, tokens_out=0)
        assert cost == Decimal("0")

    def test_unknown_model_uses_default(self):
        cost_unknown = calculate_cost("some-unknown-model", tokens_in=1000, tokens_out=1000)
        cost_default = calculate_cost("claude-3-5-sonnet-20241022", tokens_in=1000, tokens_out=1000)
        assert cost_unknown == cost_default

    def test_rounding_up(self):
        """Very small amounts should round up, not down."""
        cost = calculate_cost("claude-3-5-sonnet-20241022", tokens_in=1, tokens_out=1)
        # Should not be zero
        assert cost > Decimal("0")

    def test_price_ratio_applied(self):
        """25% price_ratio means cost should be 1/4 of Anthropic price."""
        from app.core.config import settings
        assert settings.price_ratio == 0.25

        full_cost = calculate_cost("claude-3-5-sonnet-20241022", tokens_in=1_000_000, tokens_out=0)
        # $3.00 * 0.25 = $0.75
        assert full_cost == Decimal("0.75000000")


class TestBalanceManagement:
    @pytest_asyncio.fixture(autouse=True)
    async def setup_user(self, db):
        """Create a test user with $1.00 balance."""
        from app.core.security import hash_password

        user = User(
            email="billing_test@example.com",
            password_hash=hash_password("testpass123"),
            balance=Decimal("1.00000000"),
            status="active",
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        self.user = user
        self.db = db

    @pytest.mark.asyncio
    async def test_recharge_increases_balance(self):
        original = self.user.balance
        new_balance = await recharge_balance(self.db, self.user.id, Decimal("10.00"))
        assert new_balance == original + Decimal("10.00")

    @pytest.mark.asyncio
    async def test_recharge_zero_raises(self):
        with pytest.raises(ValueError, match="positive"):
            await recharge_balance(self.db, self.user.id, Decimal("0"))

    @pytest.mark.asyncio
    async def test_recharge_negative_raises(self):
        with pytest.raises(ValueError):
            await recharge_balance(self.db, self.user.id, Decimal("-5.00"))

    @pytest.mark.asyncio
    async def test_deduct_balance_creates_transaction(self):
        cost = await check_and_deduct_balance(
            db=self.db,
            user_id=self.user.id,
            model="claude-3-5-sonnet-20241022",
            tokens_in=1000,
            tokens_out=500,
        )
        assert cost > Decimal("0")
        # Balance should be reduced
        await self.db.refresh(self.user)
        assert self.user.balance < Decimal("1.00000000")

    @pytest.mark.asyncio
    async def test_deduct_insufficient_balance_raises(self):
        """Deducting more than available balance should raise."""
        with pytest.raises(ValueError, match="Insufficient balance"):
            await check_and_deduct_balance(
                db=self.db,
                user_id=self.user.id,
                model="claude-opus-4-6",
                tokens_in=100_000_000,  # huge token count
                tokens_out=100_000_000,
            )

    @pytest.mark.asyncio
    async def test_get_usage_summary_empty(self):
        summary = await get_usage_summary(self.db, self.user.id, period="today")
        assert summary["total_requests"] == 0
        assert summary["total_cost"] == 0

    @pytest.mark.asyncio
    async def test_get_recent_transactions_empty(self):
        txs = await get_recent_transactions(self.db, self.user.id)
        assert txs == []

    @pytest.mark.asyncio
    async def test_get_usage_invalid_period(self):
        # Should default to month behavior — just runs without error
        summary = await get_usage_summary(self.db, self.user.id, period="all_time")
        assert "total_requests" in summary
