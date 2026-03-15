"""
Trust Weight Calculator for OpenClade Subnet.

Implements Bittensor-aligned weight processing via process_weights_for_netuid(),
which applies the Yuma Consensus rules before on-chain submission:

  - Minimum weight threshold filtering
  - Maximum UID count enforcement
  - Quantile-based pruning of low-weight miners
  - Normalization to [0, 1] range with sum = 1.0

The resulting weights flow into Yuma Consensus on-chain where:
  T (trust)    = stake-weighted average of validator weight agreement
  C (consensus)= alignment of this validator's weights with global consensus
  R (rank)     = stake * consensus
  I (incentive)= trust * rank
  E (emission) = incentive * total_emission

References:
  - Bittensor whitepaper §3: Yuma Consensus
  - bt.utils.weight_utils.process_weights_for_netuid (SDK source)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from loguru import logger


@dataclass
class TrustWeightResult:
    """Output of the trust weight processing pipeline."""

    processed_uids: List[int]
    """Ordered list of miner UIDs after filtering."""

    processed_weights: List[float]
    """Normalized weights corresponding to processed_uids, sum ≈ 1.0."""

    excluded_uids: List[int]
    """UIDs pruned due to quantile filtering or zero weight."""

    total_miners: int
    """Total miners considered before pruning."""


class TrustWeightCalculator:
    """
    Computes trust-aligned weights for Bittensor's Yuma Consensus.

    Wraps process_weights_for_netuid() with fallback logic when the full
    bittensor SDK is unavailable (test/mock environments).

    Usage:
        calc = TrustWeightCalculator(netuid=1)
        result = calc.process(raw_weights, metagraph, subtensor)
        subtensor.set_weights(
            netuid=1, wallet=wallet,
            uids=result.processed_uids,
            weights=result.processed_weights,
        )
    """

    def __init__(
        self,
        netuid: int,
        exclude_quantile: float = 0.1,
        min_allowed_weights: int = 0,
        max_weight_limit: float = 1.0,
    ) -> None:
        """
        Args:
            netuid: Subnet UID.
            exclude_quantile: Bottom fraction of miners to exclude (0.0–1.0).
                The bittensor default is 0.1 (bottom 10% by weight are zeroed).
            min_allowed_weights: Minimum number of non-zero weights required.
                If fewer miners remain after pruning, skip weight submission.
            max_weight_limit: Maximum normalized weight for any single miner.
                Prevents single-miner dominance.
        """
        self.netuid = netuid
        self.exclude_quantile = exclude_quantile
        self.min_allowed_weights = min_allowed_weights
        self.max_weight_limit = max_weight_limit

    def process(
        self,
        raw_weights: Dict[int, float],
        metagraph=None,
        subtensor=None,
    ) -> TrustWeightResult:
        """
        Process raw scorer weights into Bittensor-aligned submission format.

        Attempts to use bt.utils.weight_utils.process_weights_for_netuid when
        bittensor SDK and metagraph are available. Falls back to local normalization
        for test environments.

        Args:
            raw_weights: Mapping of UID → raw weight score (from ScoringEngine).
            metagraph: Live bittensor metagraph for UID count and stake info.
            subtensor: Live subtensor for netuid metadata.

        Returns:
            TrustWeightResult with processed_uids and processed_weights ready for
            subtensor.set_weights().
        """
        logger.info(
            f"TrustWeightCalculator.process | netuid={self.netuid} | "
            f"raw_miners={len(raw_weights)}"
        )

        if metagraph is not None and subtensor is not None:
            return self._process_with_sdk(raw_weights, metagraph, subtensor)

        logger.debug("SDK not available — using local weight normalization")
        return self._process_local(raw_weights)

    def _process_with_sdk(
        self,
        raw_weights: Dict[int, float],
        metagraph,
        subtensor,
    ) -> TrustWeightResult:
        """Use bittensor SDK's process_weights_for_netuid for protocol alignment."""
        try:
            import bittensor as bt

            all_uids = list(range(metagraph.n.item()))
            uid_tensor = np.array(all_uids, dtype=np.int64)
            weight_tensor = np.array(
                [raw_weights.get(uid, 0.0) for uid in all_uids],
                dtype=np.float32,
            )

            # Delegate to SDK for Yuma-compliant processing
            processed_uids, processed_weights = bt.utils.weight_utils.process_weights_for_netuid(
                uids=uid_tensor,
                weights=weight_tensor,
                netuid=self.netuid,
                subtensor=subtensor,
                metagraph=metagraph,
                exclude_quantile=self.exclude_quantile,
            )

            excluded = [
                uid for uid in all_uids
                if uid not in processed_uids.tolist()
            ]

            logger.info(
                f"SDK weight processing | "
                f"kept={len(processed_uids)}/{len(all_uids)} | "
                f"excluded={len(excluded)}"
            )

            return TrustWeightResult(
                processed_uids=processed_uids.tolist(),
                processed_weights=processed_weights.tolist(),
                excluded_uids=excluded,
                total_miners=len(all_uids),
            )

        except (AttributeError, ImportError) as e:
            logger.warning(
                f"bt.utils.weight_utils unavailable ({e}) — falling back to local normalization"
            )
            return self._process_local(raw_weights)

    def _process_local(self, raw_weights: Dict[int, float]) -> TrustWeightResult:
        """
        Fallback weight processing without full SDK.

        Applies:
        1. Quantile-based pruning (bottom exclude_quantile fraction zeroed)
        2. Max weight cap at max_weight_limit
        3. L1 normalization

        This mirrors the logic of process_weights_for_netuid().
        """
        if not raw_weights:
            return TrustWeightResult(
                processed_uids=[], processed_weights=[], excluded_uids=[], total_miners=0
            )

        uids = sorted(raw_weights.keys())
        weights = np.array([raw_weights[uid] for uid in uids], dtype=np.float64)

        # Step 1: quantile pruning — zero out bottom exclude_quantile fraction
        if self.exclude_quantile > 0 and len(weights) > 1:
            threshold = np.quantile(weights[weights > 0], self.exclude_quantile) if any(weights > 0) else 0.0
            weights = np.where(weights < threshold, 0.0, weights)

        # Step 2: cap maximum weight
        total = weights.sum()
        if total > 0:
            weights /= total  # Normalize first
        weights = np.minimum(weights, self.max_weight_limit)

        # Step 3: re-normalize after capping
        total = weights.sum()
        if total > 0:
            weights /= total

        # Separate kept and excluded
        kept_mask = weights > 0
        kept_uids = [uid for uid, kept in zip(uids, kept_mask) if kept]
        kept_weights = [float(w) for w, kept in zip(weights, kept_mask) if kept]
        excluded_uids = [uid for uid, kept in zip(uids, kept_mask) if not kept]

        logger.debug(
            f"Local weight processing | "
            f"kept={len(kept_uids)}/{len(uids)} | excluded={len(excluded_uids)}"
        )

        return TrustWeightResult(
            processed_uids=kept_uids,
            processed_weights=kept_weights,
            excluded_uids=excluded_uids,
            total_miners=len(uids),
        )

    def is_submission_viable(self, result: TrustWeightResult) -> Tuple[bool, str]:
        """
        Check whether the processed weights are suitable for on-chain submission.

        Returns:
            (True, "") if submission should proceed.
            (False, reason) if submission should be skipped this epoch.
        """
        if not result.processed_uids:
            return False, "No miners with non-zero weights"

        if len(result.processed_uids) < self.min_allowed_weights:
            return False, (
                f"Only {len(result.processed_uids)} miners meet weight threshold "
                f"(min={self.min_allowed_weights})"
            )

        weight_sum = sum(result.processed_weights)
        if abs(weight_sum - 1.0) > 0.01:
            return False, f"Weights do not sum to 1.0 (sum={weight_sum:.4f})"

        return True, ""
