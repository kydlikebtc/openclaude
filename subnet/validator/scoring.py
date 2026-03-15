"""
OpenClade Validator Scoring Engine.

Implements the multi-dimensional scoring formula from incentive_mechanism.md:

  综合评分 = 可用性 × 20% + 延迟 × 15% + 响应质量 × 35% + 一致性 × 20% + 效率 × 10%

Each dimension is normalized to [0.0, 1.0].
Final scores are EMA-smoothed to prevent single-probe jitter:
  smooth_score = 0.7 × raw_score + 0.3 × prev_smooth_score
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from loguru import logger

from protocol.synapse import LLMAPISynapse
from validator.probe import ProbeTask

# ── Weight constants (matches incentive_mechanism.md §4.2) ──────────────
W_AVAILABILITY = 0.20
W_LATENCY = 0.15
W_QUALITY = 0.35
W_CONSISTENCY = 0.20
W_EFFICIENCY = 0.10

# EMA smoothing factor
EMA_ALPHA = 0.7

# Efficiency baseline: tokens considered "ideal" for a typical response
EFFICIENCY_BASELINE_TOKENS = 500

# Latency breakpoints in milliseconds
LATENCY_EXCELLENT_MS = 2_000
LATENCY_GOOD_MS = 5_000
LATENCY_POOR_MS = 10_000

# Model downgrade quality thresholds (minimum quality score per model)
MODEL_QUALITY_THRESHOLDS: Dict[str, float] = {
    "claude-opus-4-6": 0.95,
    "claude-sonnet-4-6": 0.85,
    "claude-haiku-4-5-20251001": 0.70,
}

# Error keywords that reduce quality score
ERROR_KEYWORDS = ["error", "exception", "traceback", "cannot", "unable to"]


@dataclass
class MinerScore:
    """Aggregated score for a single Miner UID in one scoring epoch."""

    uid: int
    availability: float = 0.0
    latency: float = 0.0
    quality: float = 0.0
    consistency: float = 0.0
    efficiency: float = 0.0
    raw_score: float = 0.0
    smooth_score: float = 0.0
    downgrade_detected: bool = False
    error_message: str = ""

    def compute_raw(self) -> float:
        """Compute weighted raw score from dimension scores."""
        self.raw_score = (
            self.availability * W_AVAILABILITY
            + self.latency * W_LATENCY
            + self.quality * W_QUALITY
            + self.consistency * W_CONSISTENCY
            + self.efficiency * W_EFFICIENCY
        )
        return self.raw_score

    def apply_ema(self, prev_smooth: float) -> float:
        """Apply EMA smoothing and update smooth_score."""
        self.smooth_score = EMA_ALPHA * self.raw_score + (1 - EMA_ALPHA) * prev_smooth
        return self.smooth_score


class ScoringEngine:
    """
    Computes per-Miner scores from a batch of Synapse responses.

    Usage:
        engine = ScoringEngine()
        scores = engine.score_batch(uid_responses, probe_task)
        weights = engine.scores_to_weights(scores, all_uids)
    """

    def __init__(self) -> None:
        # Stores previous smooth scores for EMA continuity across epochs
        self._prev_scores: Dict[int, float] = {}

    def score_batch(
        self,
        responses: Dict[int, LLMAPISynapse],
        probe: ProbeTask,
    ) -> Dict[int, MinerScore]:
        """
        Score all Miner responses for a single probe task.

        Args:
            responses: Mapping of UID → Synapse response.
            probe: The ProbeTask that was sent.

        Returns:
            Mapping of UID → MinerScore with smooth scores applied.
        """
        scores: Dict[int, MinerScore] = {}

        # First pass: compute individual dimension scores
        all_latencies = [
            r.latency_ms for r in responses.values()
            if r.is_success() and r.latency_ms > 0
        ]

        for uid, synapse in responses.items():
            score = MinerScore(uid=uid)
            score.availability = self._score_availability(synapse)

            if score.availability > 0:
                score.latency = self._score_latency(synapse.latency_ms, all_latencies)
                score.quality = self._score_quality(synapse, probe)
                score.efficiency = self._score_efficiency(synapse.tokens_used)
                score.downgrade_detected = self._detect_downgrade(synapse)
                if score.downgrade_detected:
                    logger.warning(
                        f"UID {uid}: model downgrade detected "
                        f"(claimed={probe.model}, actual={synapse.miner_model_used})"
                    )
                    score.raw_score = 0.0
                    score.smooth_score = 0.0
                    scores[uid] = score
                    continue

            scores[uid] = score

        # Second pass: consistency scoring requires all responses to be available
        all_responses = {
            uid: responses[uid].response
            for uid, score in scores.items()
            if score.availability > 0 and responses[uid].response is not None
        }
        for uid, score in scores.items():
            if score.availability > 0:
                score.consistency = self._score_consistency(
                    uid, responses[uid], probe, all_responses
                )

        # Third pass: compute raw scores and apply EMA
        for uid, score in scores.items():
            if not score.downgrade_detected:
                score.compute_raw()
            score.apply_ema(self._prev_scores.get(uid, 0.0))
            self._prev_scores[uid] = score.smooth_score
            logger.debug(
                f"UID {uid}: availability={score.availability:.2f} "
                f"latency={score.latency:.2f} quality={score.quality:.2f} "
                f"consistency={score.consistency:.2f} efficiency={score.efficiency:.2f} "
                f"→ raw={score.raw_score:.4f} smooth={score.smooth_score:.4f}"
            )

        return scores

    def scores_to_weights(
        self,
        scores: Dict[int, MinerScore],
        all_uids: List[int],
    ) -> Dict[int, float]:
        """
        Convert MinerScore objects to normalized weight values [0.0, 1.0].

        UIDs not in scores (offline miners) receive weight 0.0.
        Weights are normalized so they sum to 1.0 across all UIDs.
        """
        raw_weights = {uid: scores[uid].smooth_score if uid in scores else 0.0
                       for uid in all_uids}
        total = sum(raw_weights.values())
        if total == 0.0:
            logger.warning("All miner scores are 0 — returning uniform weights")
            n = len(all_uids)
            return {uid: 1.0 / n for uid in all_uids}
        return {uid: w / total for uid, w in raw_weights.items()}

    # ── Dimension scorers ────────────────────────────────────────────────

    @staticmethod
    def _score_availability(synapse: LLMAPISynapse) -> float:
        """1.0 if response is non-empty; 0.0 on timeout or error."""
        if synapse.is_success() and synapse.response:
            return 1.0
        return 0.0

    @staticmethod
    def _score_latency(latency_ms: int, all_latencies: List[int]) -> float:
        """
        Score latency on an absolute scale per incentive_mechanism.md §4.2.

        < 2s → 1.0
        2-5s → 0.7 - 1.0 (linear)
        5-10s → 0.3 - 0.7 (linear)
        > 10s → 0 - 0.3 (linear decay)
        """
        if latency_ms <= 0:
            return 0.0
        if latency_ms <= LATENCY_EXCELLENT_MS:
            return 1.0
        if latency_ms <= LATENCY_GOOD_MS:
            t = (latency_ms - LATENCY_EXCELLENT_MS) / (LATENCY_GOOD_MS - LATENCY_EXCELLENT_MS)
            return 1.0 - t * 0.3
        if latency_ms <= LATENCY_POOR_MS:
            t = (latency_ms - LATENCY_GOOD_MS) / (LATENCY_POOR_MS - LATENCY_GOOD_MS)
            return 0.7 - t * 0.4
        # > 10s: linear decay to 0
        excess = latency_ms - LATENCY_POOR_MS
        decay = min(excess / 10_000, 1.0) * 0.3
        return max(0.3 - decay, 0.0)

    @staticmethod
    def _score_quality(synapse: LLMAPISynapse, probe: ProbeTask) -> float:
        """
        Multi-heuristic quality score.

        Checks: length reasonableness, error keywords, expected answer match.
        """
        response = synapse.response or ""
        lower = response.lower()
        score = 1.0

        # For deterministic tasks: correct answer overrides length penalty
        deterministic_correct = False
        if probe.task_type == "deterministic" and probe.expected_answer:
            expected = probe.expected_answer.strip().lower()
            if expected in lower:
                deterministic_correct = True
            else:
                score -= 0.5

        # Length check — skip for short correct deterministic answers
        if not deterministic_correct:
            word_count = len(response.split())
            if word_count < 3:
                score -= 0.4
            elif word_count > 50_000:
                score -= 0.2

        # Error keyword detection
        if any(kw in lower for kw in ERROR_KEYWORDS):
            score -= 0.3

        return max(score, 0.0)

    @staticmethod
    def _score_consistency(
        uid: int,
        synapse: LLMAPISynapse,
        probe: ProbeTask,
        all_responses: Dict[int, Optional[str]],
    ) -> float:
        """
        Consistency score: how similar is this Miner's response to peers?

        For deterministic tasks: strict matching against expected answer.
        For open-ended tasks: character-level Jaccard similarity (cheap proxy).
        A full embedding-based approach is tracked in incentive_mechanism.md §9.
        """
        if probe.task_type == "deterministic" and probe.expected_answer:
            expected = probe.expected_answer.strip().lower()
            response = (synapse.response or "").lower()
            return 1.0 if expected in response else 0.0

        # Open-ended: Jaccard similarity against all peer responses
        peers = [
            r for peer_uid, r in all_responses.items()
            if peer_uid != uid and r is not None
        ]
        if not peers:
            return 1.0  # No peers to compare against — neutral

        my_words = set((synapse.response or "").lower().split())
        similarities = []
        for peer_response in peers:
            peer_words = set(peer_response.lower().split())
            union = my_words | peer_words
            if not union:
                similarities.append(1.0)
            else:
                inter = my_words & peer_words
                similarities.append(len(inter) / len(union))

        return sum(similarities) / len(similarities)

    @staticmethod
    def _score_efficiency(tokens_used: int) -> float:
        """
        Efficiency score: min(baseline / tokens_used, 1.0).

        Rewards concise, information-dense responses.
        """
        if tokens_used <= 0:
            return 0.0
        return min(EFFICIENCY_BASELINE_TOKENS / tokens_used, 1.0)

    @staticmethod
    def _detect_downgrade(synapse: LLMAPISynapse) -> bool:
        """
        Return True if the Miner appears to have used a lower-tier model.

        Checks: miner_model_used doesn't match the requested model family.
        Quality-threshold check is deferred to the caller (needs quality score).
        """
        if not synapse.miner_model_used:
            return False
        # Simple family comparison: if claimed opus but used haiku, flag it
        requested = synapse.model.lower()
        actual = synapse.miner_model_used.lower()
        if "opus" in requested and "haiku" in actual:
            return True
        if "sonnet" in requested and "haiku" in actual:
            return True
        return False
