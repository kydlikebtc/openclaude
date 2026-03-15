"""
Tests for the TrustWeightCalculator.

Covers:
- Local weight normalization fallback (no SDK)
- Quantile pruning behavior
- Max weight capping
- is_submission_viable() guards
- SDK delegation path (mocked)
"""

import pytest
from unittest.mock import MagicMock, patch

from validator.trust import TrustWeightCalculator, TrustWeightResult


# ── Helpers ──────────────────────────────────────────────────────────────────


def make_raw_weights(*scores: float) -> dict:
    """Build uid→weight dict from positional scores."""
    return {uid: score for uid, score in enumerate(scores)}


# ── TrustWeightResult ─────────────────────────────────────────────────────────


class TestTrustWeightResult:
    def test_fields_stored_correctly(self):
        result = TrustWeightResult(
            processed_uids=[0, 1],
            processed_weights=[0.7, 0.3],
            excluded_uids=[2],
            total_miners=3,
        )
        assert result.processed_uids == [0, 1]
        assert result.processed_weights == [0.7, 0.3]
        assert result.excluded_uids == [2]
        assert result.total_miners == 3


# ── Local normalization ───────────────────────────────────────────────────────


class TestLocalNormalization:
    def test_empty_weights_returns_empty_result(self):
        calc = TrustWeightCalculator(netuid=1)
        result = calc.process({})
        assert result.processed_uids == []
        assert result.processed_weights == []
        assert result.total_miners == 0

    def test_single_miner_gets_weight_one(self):
        calc = TrustWeightCalculator(netuid=1, exclude_quantile=0.0)
        result = calc.process({0: 0.8})
        assert result.processed_uids == [0]
        assert abs(result.processed_weights[0] - 1.0) < 1e-6

    def test_two_equal_miners_get_half_each(self):
        calc = TrustWeightCalculator(netuid=1, exclude_quantile=0.0)
        result = calc.process({0: 0.5, 1: 0.5})
        assert len(result.processed_uids) == 2
        for w in result.processed_weights:
            assert abs(w - 0.5) < 1e-6

    def test_weights_sum_to_one(self):
        calc = TrustWeightCalculator(netuid=1, exclude_quantile=0.0)
        raw = make_raw_weights(0.3, 0.5, 0.1, 0.8, 0.2)
        result = calc.process(raw)
        assert abs(sum(result.processed_weights) - 1.0) < 1e-6

    def test_zero_weight_miners_excluded(self):
        calc = TrustWeightCalculator(netuid=1, exclude_quantile=0.0)
        result = calc.process({0: 0.0, 1: 0.7, 2: 0.0})
        assert 0 not in result.processed_uids
        assert 2 not in result.processed_uids
        assert 1 in result.processed_uids
        assert 0 in result.excluded_uids
        assert 2 in result.excluded_uids

    def test_proportional_weights_preserved(self):
        """A miner with 3× the score gets 3× the weight."""
        calc = TrustWeightCalculator(netuid=1, exclude_quantile=0.0)
        result = calc.process({0: 0.75, 1: 0.25})
        w = {uid: wt for uid, wt in zip(result.processed_uids, result.processed_weights)}
        assert abs(w[0] / w[1] - 3.0) < 1e-5


# ── Quantile pruning ──────────────────────────────────────────────────────────


class TestQuantilePruning:
    def test_bottom_quantile_miners_excluded(self):
        """With exclude_quantile=0.25, the bottom 25% of positive weights are zeroed."""
        calc = TrustWeightCalculator(netuid=1, exclude_quantile=0.25)
        # 4 miners with weights 0.1, 0.2, 0.6, 0.8
        result = calc.process({0: 0.1, 1: 0.2, 2: 0.6, 3: 0.8})
        # The lowest (uid=0) should be pruned
        assert 0 in result.excluded_uids

    def test_no_pruning_with_zero_quantile(self):
        calc = TrustWeightCalculator(netuid=1, exclude_quantile=0.0)
        result = calc.process({0: 0.1, 1: 0.5, 2: 0.9})
        # All non-zero miners should be kept
        assert set(result.processed_uids) == {0, 1, 2}

    def test_all_equal_weights_no_pruning(self):
        """All miners with identical positive weights — none should be pruned."""
        calc = TrustWeightCalculator(netuid=1, exclude_quantile=0.1)
        result = calc.process({i: 0.5 for i in range(5)})
        assert len(result.processed_uids) == 5


# ── Max weight cap ────────────────────────────────────────────────────────────


class TestMaxWeightCap:
    def test_dominant_miner_capped(self):
        """A single miner with all weight should be capped near max_weight_limit.

        The iterative convergence algorithm approximates the cap limit;
        allow 1e-3 tolerance for floating-point convergence error.
        """
        calc = TrustWeightCalculator(
            netuid=1, exclude_quantile=0.0, max_weight_limit=0.7
        )
        result = calc.process({0: 100.0, 1: 1.0})
        w = {uid: wt for uid, wt in zip(result.processed_uids, result.processed_weights)}
        assert w[0] <= 0.7 + 1e-3

    def test_cap_at_one_is_noop(self):
        """max_weight_limit=1.0 should not change any weights."""
        calc = TrustWeightCalculator(netuid=1, exclude_quantile=0.0, max_weight_limit=1.0)
        result = calc.process({0: 0.8, 1: 0.2})
        for w in result.processed_weights:
            assert w <= 1.0 + 1e-6


# ── is_submission_viable ──────────────────────────────────────────────────────


class TestSubmissionViability:
    def test_viable_with_good_result(self):
        calc = TrustWeightCalculator(netuid=1)
        result = TrustWeightResult(
            processed_uids=[0, 1],
            processed_weights=[0.6, 0.4],
            excluded_uids=[],
            total_miners=2,
        )
        viable, reason = calc.is_submission_viable(result)
        assert viable
        assert reason == ""

    def test_not_viable_with_empty_uids(self):
        calc = TrustWeightCalculator(netuid=1)
        result = TrustWeightResult(
            processed_uids=[], processed_weights=[], excluded_uids=[], total_miners=0
        )
        viable, reason = calc.is_submission_viable(result)
        assert not viable
        assert "No miners" in reason

    def test_not_viable_below_min_allowed(self):
        calc = TrustWeightCalculator(netuid=1, min_allowed_weights=3)
        result = TrustWeightResult(
            processed_uids=[0, 1],
            processed_weights=[0.6, 0.4],
            excluded_uids=[],
            total_miners=2,
        )
        viable, reason = calc.is_submission_viable(result)
        assert not viable
        assert "min=" in reason

    def test_not_viable_weights_dont_sum_to_one(self):
        calc = TrustWeightCalculator(netuid=1)
        result = TrustWeightResult(
            processed_uids=[0, 1],
            processed_weights=[0.3, 0.3],  # Sums to 0.6, not 1.0
            excluded_uids=[],
            total_miners=2,
        )
        viable, reason = calc.is_submission_viable(result)
        assert not viable
        assert "sum=" in reason


# ── SDK delegation path ───────────────────────────────────────────────────────


class TestSDKDelegation:
    def test_falls_back_to_local_when_sdk_missing(self):
        """If bt.utils.weight_utils is unavailable, local normalization is used."""
        import sys
        fake_metagraph = MagicMock()
        fake_metagraph.n.item.return_value = 2
        fake_subtensor = MagicMock()

        # Patch bittensor to raise AttributeError on weight_utils
        with patch.dict(sys.modules, {"bittensor": MagicMock(
            utils=MagicMock(weight_utils=MagicMock(
                process_weights_for_netuid=MagicMock(side_effect=AttributeError("no attr"))
            ))
        )}):
            calc = TrustWeightCalculator(netuid=1, exclude_quantile=0.0)
            result = calc.process(
                {0: 0.7, 1: 0.3},
                metagraph=fake_metagraph,
                subtensor=fake_subtensor,
            )
            # Should still return valid results from local fallback
            assert len(result.processed_uids) > 0
            assert abs(sum(result.processed_weights) - 1.0) < 1e-6

    def test_no_metagraph_uses_local(self):
        """Passing metagraph=None forces local processing without SDK call."""
        calc = TrustWeightCalculator(netuid=1, exclude_quantile=0.0)
        result = calc.process({0: 0.6, 1: 0.4}, metagraph=None, subtensor=None)
        assert set(result.processed_uids) == {0, 1}
        assert abs(sum(result.processed_weights) - 1.0) < 1e-6
