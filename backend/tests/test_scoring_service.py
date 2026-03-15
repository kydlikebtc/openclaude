"""Unit tests for the scoring engine service."""

import pytest

from app.services.scoring_service import (
    compute_referral_bonus,
    compute_score,
    latency_to_score,
)


def test_latency_to_score_optimal():
    """Sub-200ms latency should be close to 1.0."""
    score = latency_to_score(100)
    assert score > 0.85, f"expected >0.85, got {score}"


def test_latency_to_score_high():
    """High latency (2000ms) should give a low score."""
    score = latency_to_score(2000)
    assert score < 0.2, f"expected <0.2, got {score}"


def test_latency_to_score_zero():
    """Zero latency returns neutral 0.5 (no data sentinel)."""
    assert latency_to_score(0) == 0.5


def test_compute_referral_bonus_none():
    assert compute_referral_bonus(0, 0) == 0.0


def test_compute_referral_bonus_one_direct():
    bonus = compute_referral_bonus(1, 0)
    assert bonus == pytest.approx(0.05)


def test_compute_referral_bonus_capped():
    """Many referrals should not exceed 10%."""
    bonus = compute_referral_bonus(10, 10)
    assert bonus == pytest.approx(0.10)


def test_compute_referral_bonus_mixed():
    bonus = compute_referral_bonus(1, 1)
    # 1 * 0.05 + 1 * 0.02 = 0.07
    assert bonus == pytest.approx(0.07)


def test_compute_score_perfect():
    """All 1.0 components → final_score ≈ 1.0 (before bonus)."""
    c = compute_score(1.0, 1.0, 1.0, 1.0, 1.0, 0.0)
    assert c.final_score == pytest.approx(1.0)


def test_compute_score_zero():
    """All 0.0 components → final_score = 0.0."""
    c = compute_score(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    assert c.final_score == pytest.approx(0.0)


def test_compute_score_weights():
    """Quality weight 0.4 dominates; verify formula."""
    # availability=1, others=0, quality=1
    c = compute_score(1.0, 0.0, 1.0, 0.0, 0.0, 0.0)
    expected = 1.0 * 0.2 + 0.0 * 0.2 + 1.0 * 0.4 + 0.0 * 0.1 + 0.0 * 0.1
    assert c.final_score == pytest.approx(expected)


def test_compute_score_with_bonus():
    """Referral bonus is added but capped at 1.0."""
    c = compute_score(1.0, 1.0, 1.0, 1.0, 1.0, 0.05)
    assert c.final_score == pytest.approx(1.0)  # capped


def test_compute_score_bonus_additive():
    """Referral bonus adds to a mid-range score."""
    c = compute_score(0.5, 0.5, 0.5, 0.5, 0.5, 0.05)
    expected = min(0.5 + 0.05, 1.0)
    assert c.final_score == pytest.approx(expected)
