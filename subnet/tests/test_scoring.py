"""
Tests for the Validator ScoringEngine.

Uses mock Synapses to exercise each dimension scorer independently,
then tests the full score_batch() pipeline and weight normalization.
"""

import pytest

from protocol.synapse import LLMAPISynapse
from validator.probe import ProbeTask
from validator.scoring import (
    EFFICIENCY_BASELINE_TOKENS,
    EMA_ALPHA,
    MinerScore,
    ScoringEngine,
)


def make_synapse(
    response: str = "This is a test response.",
    latency_ms: int = 1000,
    tokens_used: int = 50,
    model: str = "claude-sonnet-4-6",
    miner_model_used: str = "claude-sonnet-4-6",
    error_message: str = "",
) -> LLMAPISynapse:
    s = LLMAPISynapse(
        messages=[{"role": "user", "content": "test"}],
        model=model,
        response=response,
        latency_ms=latency_ms,
        tokens_used=tokens_used,
        miner_model_used=miner_model_used,
        error_message=error_message,
    )
    s.compute_response_hash()
    return s


def make_probe(task_type: str = "open_ended", expected_answer: str = "") -> ProbeTask:
    return ProbeTask(
        messages=[{"role": "user", "content": "Describe an API."}],
        task_type=task_type,
        expected_answer=expected_answer,
    )


class TestScoreAvailability:
    engine = ScoringEngine()

    def test_available_on_success(self):
        s = make_synapse(response="Hello!")
        assert self.engine._score_availability(s) == 1.0

    def test_not_available_on_none_response(self):
        s = make_synapse(response="")
        s.response = None
        assert self.engine._score_availability(s) == 0.0

    def test_not_available_on_error(self):
        s = make_synapse(response="text", error_message="some error")
        assert self.engine._score_availability(s) == 0.0


class TestScoreLatency:
    engine = ScoringEngine()

    def test_excellent_latency(self):
        assert self.engine._score_latency(1000, []) == 1.0

    def test_boundary_excellent(self):
        assert self.engine._score_latency(2000, []) == 1.0

    def test_good_latency_at_boundary(self):
        score = self.engine._score_latency(5000, [])
        assert 0.69 <= score <= 0.71

    def test_poor_latency_at_boundary(self):
        score = self.engine._score_latency(10000, [])
        assert 0.29 <= score <= 0.31

    def test_very_high_latency_approaches_zero(self):
        score = self.engine._score_latency(20000, [])
        assert score >= 0.0
        assert score < 0.3

    def test_zero_latency_returns_zero(self):
        assert self.engine._score_latency(0, []) == 0.0


class TestScoreQuality:
    engine = ScoringEngine()

    def test_good_response(self):
        s = make_synapse(response="This is a helpful and detailed response about APIs.")
        probe = make_probe()
        score = self.engine._score_quality(s, probe)
        assert score >= 0.7

    def test_too_short_penalized(self):
        s = make_synapse(response="hi")
        probe = make_probe()
        score = self.engine._score_quality(s, probe)
        assert score < 1.0

    def test_error_keyword_penalized(self):
        s = make_synapse(response="An error occurred while processing your request.")
        probe = make_probe()
        score = self.engine._score_quality(s, probe)
        # "error" keyword → -0.3 penalty from 1.0 = 0.7 (at most)
        assert score <= 0.7

    def test_deterministic_correct_answer(self):
        s = make_synapse(response="391")
        probe = make_probe(task_type="deterministic", expected_answer="391")
        score = self.engine._score_quality(s, probe)
        assert score >= 1.0  # No penalty

    def test_deterministic_wrong_answer_penalized(self):
        s = make_synapse(response="400")
        probe = make_probe(task_type="deterministic", expected_answer="391")
        score = self.engine._score_quality(s, probe)
        assert score < 0.6


class TestScoreEfficiency:
    engine = ScoringEngine()

    def test_baseline_tokens_full_score(self):
        score = self.engine._score_efficiency(EFFICIENCY_BASELINE_TOKENS)
        assert score == 1.0

    def test_fewer_tokens_higher_efficiency(self):
        score = self.engine._score_efficiency(100)
        assert score == 1.0  # Capped at 1.0

    def test_more_tokens_lower_efficiency(self):
        score = self.engine._score_efficiency(EFFICIENCY_BASELINE_TOKENS * 2)
        assert abs(score - 0.5) < 0.01

    def test_zero_tokens_returns_zero(self):
        assert self.engine._score_efficiency(0) == 0.0


class TestConsistencyScoring:
    engine = ScoringEngine()

    def test_deterministic_correct_answer_full_score(self):
        s = make_synapse(response="The answer is 391.")
        probe = make_probe(task_type="deterministic", expected_answer="391")
        score = self.engine._score_consistency(1, s, probe, {})
        assert score == 1.0

    def test_deterministic_wrong_answer_zero_score(self):
        s = make_synapse(response="I don't know.")
        probe = make_probe(task_type="deterministic", expected_answer="391")
        score = self.engine._score_consistency(1, s, probe, {})
        assert score == 0.0

    def test_no_peers_returns_neutral(self):
        s = make_synapse(response="Some open-ended answer.")
        probe = make_probe(task_type="open_ended")
        score = self.engine._score_consistency(1, s, probe, {})
        assert score == 1.0

    def test_identical_peer_response_high_similarity(self):
        response = "An API is a way for programs to talk to each other."
        s = make_synapse(response=response)
        probe = make_probe(task_type="open_ended")
        peers = {2: response}  # Identical response
        score = self.engine._score_consistency(1, s, probe, peers)
        assert score > 0.8

    def test_completely_different_peer_low_similarity(self):
        s = make_synapse(response="quantum physics relativity")
        probe = make_probe(task_type="open_ended")
        peers = {2: "hello world foo bar"}
        score = self.engine._score_consistency(1, s, probe, peers)
        assert score < 0.3


class TestDowngradeDetection:
    engine = ScoringEngine()

    def test_no_downgrade_same_family(self):
        s = make_synapse(model="claude-sonnet-4-6", miner_model_used="claude-sonnet-4-6")
        assert not self.engine._detect_downgrade(s)

    def test_opus_to_haiku_flagged(self):
        s = make_synapse(model="claude-opus-4-6", miner_model_used="claude-haiku-4-5-20251001")
        assert self.engine._detect_downgrade(s)

    def test_sonnet_to_haiku_flagged(self):
        s = make_synapse(model="claude-sonnet-4-6", miner_model_used="claude-haiku-4-5-20251001")
        assert self.engine._detect_downgrade(s)

    def test_empty_model_used_no_flag(self):
        s = make_synapse(model="claude-opus-4-6", miner_model_used="")
        assert not self.engine._detect_downgrade(s)


class TestScoreBatch:
    def test_score_batch_returns_all_uids(self):
        engine = ScoringEngine()
        probe = make_probe()
        responses = {
            0: make_synapse(response="Good response here.", latency_ms=800),
            1: make_synapse(response="Also a fine response.", latency_ms=1200),
        }
        scores = engine.score_batch(responses, probe)
        assert set(scores.keys()) == {0, 1}

    def test_score_batch_downgrade_zeroes_score(self):
        engine = ScoringEngine()
        probe = make_probe()
        responses = {
            0: make_synapse(
                model="claude-sonnet-4-6",
                miner_model_used="claude-haiku-4-5-20251001",
                response="Nice answer",
            ),
        }
        scores = engine.score_batch(responses, probe)
        assert scores[0].raw_score == 0.0
        assert scores[0].downgrade_detected

    def test_score_batch_failed_synapse_gets_zero_availability(self):
        engine = ScoringEngine()
        probe = make_probe()
        s = LLMAPISynapse(error_message="API error", latency_ms=500)
        scores = engine.score_batch({0: s}, probe)
        assert scores[0].availability == 0.0

    def test_ema_smoothing_applied(self):
        engine = ScoringEngine()
        probe = make_probe()

        # First epoch — prev score is 0
        responses = {0: make_synapse(response="Great answer!", latency_ms=500)}
        scores1 = engine.score_batch(responses, probe)
        first_smooth = scores1[0].smooth_score
        first_raw = scores1[0].raw_score
        assert abs(first_smooth - EMA_ALPHA * first_raw) < 0.01

        # Second epoch — prev score feeds into EMA
        scores2 = engine.score_batch(responses, probe)
        expected_smooth = EMA_ALPHA * scores2[0].raw_score + (1 - EMA_ALPHA) * first_smooth
        assert abs(scores2[0].smooth_score - expected_smooth) < 0.01


class TestScoresToWeights:
    def test_weights_sum_to_one(self):
        engine = ScoringEngine()
        scores = {
            0: MinerScore(uid=0, smooth_score=0.8),
            1: MinerScore(uid=1, smooth_score=0.2),
        }
        weights = engine.scores_to_weights(scores, [0, 1])
        assert abs(sum(weights.values()) - 1.0) < 1e-6

    def test_missing_uid_gets_zero_weight(self):
        engine = ScoringEngine()
        scores = {0: MinerScore(uid=0, smooth_score=0.9)}
        weights = engine.scores_to_weights(scores, [0, 1, 2])
        assert weights[1] == 0.0
        assert weights[2] == 0.0

    def test_all_zero_scores_returns_uniform(self):
        engine = ScoringEngine()
        scores = {}
        weights = engine.scores_to_weights(scores, [0, 1, 2])
        for w in weights.values():
            assert abs(w - 1 / 3) < 1e-6

    def test_proportional_weights(self):
        engine = ScoringEngine()
        scores = {
            0: MinerScore(uid=0, smooth_score=0.6),
            1: MinerScore(uid=1, smooth_score=0.4),
        }
        weights = engine.scores_to_weights(scores, [0, 1])
        assert abs(weights[0] - 0.6) < 1e-6
        assert abs(weights[1] - 0.4) < 1e-6
