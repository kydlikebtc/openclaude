"""
OpenClade Validator Neuron.

Probes Miners periodically, scores their responses using the multi-dimensional
ScoringEngine, and submits on-chain weights for Yuma Consensus.

Entry point:
  python neurons/validator.py --netuid 1 --wallet.name default --wallet.hotkey validator
"""

import argparse
import asyncio
import time
from typing import Dict, List

import bittensor as bt
import numpy as np
from loguru import logger

from protocol.synapse import LLMAPISynapse
from validator.probe import ProbeTaskGenerator
from validator.scoring import MinerScore, ScoringEngine
from validator.trust import TrustWeightCalculator

# How many blocks to wait between weight submissions
WEIGHT_SUBMISSION_INTERVAL_BLOCKS = 100


class OpenCladeValidator:
    """
    Bittensor Validator for the OpenClade subnet.

    Responsibilities:
    - Maintain an up-to-date metagraph view.
    - Periodically probe a sample of Miners using ProbeTaskGenerator.
    - Score responses with ScoringEngine.
    - Submit aggregated weights to the Bittensor chain.

    Weights flow into Yuma Consensus, which determines Miner emissions.
    """

    def __init__(self, config: bt.config) -> None:
        self.config = config
        self.wallet = bt.wallet(config=config)
        self.subtensor = bt.subtensor(config=config)
        self.dendrite = bt.dendrite(wallet=self.wallet)
        self.metagraph = bt.metagraph(
            netuid=config.netuid,
            network=config.subtensor.network,
        )
        self.scoring_engine = ScoringEngine()
        self.probe_generator = ProbeTaskGenerator()
        self.trust_calculator = TrustWeightCalculator(netuid=config.netuid)
        self._last_weight_block: int = 0
        logger.info(
            f"OpenCladeValidator initialized | "
            f"netuid={config.netuid} | "
            f"hotkey={self.wallet.hotkey.ss58_address}"
        )

    # ── Main loop ────────────────────────────────────────────────────────

    async def run(self) -> None:
        """Main validator event loop."""
        self._ensure_registered()
        logger.info("Validator starting main loop")

        while True:
            try:
                await self._run_epoch()
            except Exception:
                logger.exception("Error in validator epoch — will retry")
            await asyncio.sleep(self._probe_interval())

    async def _run_epoch(self) -> None:
        """One full probe-score-submit cycle."""
        self._sync_metagraph()
        miner_uids = self._active_miner_uids()
        if not miner_uids:
            logger.warning("No active miners found — skipping epoch")
            return

        num_miners = len(miner_uids)
        uids_to_probe = self.probe_generator.miners_to_probe(miner_uids, num_miners)
        probe_tasks = self.probe_generator.sample(num_miners)

        logger.info(
            f"Epoch start | miners={num_miners} | probing={len(uids_to_probe)} | "
            f"tasks={len(probe_tasks)}"
        )

        # Aggregate scores across all probe tasks in this epoch
        epoch_scores: Dict[int, MinerScore] = {}

        for probe in probe_tasks:
            synapses = [
                LLMAPISynapse.create_request(
                    messages=probe.messages,
                    model=probe.model,
                    max_tokens=probe.max_tokens,
                    temperature=probe.temperature,
                )
                for _ in uids_to_probe
            ]

            axons = [self.metagraph.axons[uid] for uid in uids_to_probe]
            responses: List[LLMAPISynapse] = await self.dendrite.forward(
                axons=axons,
                synapse=synapses[0],
                timeout=60,
            )

            uid_to_response = {
                uid: resp for uid, resp in zip(uids_to_probe, responses)
            }
            task_scores = self.scoring_engine.score_batch(uid_to_response, probe)

            for uid, score in task_scores.items():
                if uid not in epoch_scores:
                    epoch_scores[uid] = score
                else:
                    # Average smooth scores across tasks
                    prev = epoch_scores[uid]
                    prev.smooth_score = (prev.smooth_score + score.smooth_score) / 2
                    epoch_scores[uid] = prev

        # Convert scores to raw weights, then process through Yuma Consensus alignment
        raw_weights = self.scoring_engine.scores_to_weights(epoch_scores, miner_uids)
        trust_result = self.trust_calculator.process(
            raw_weights, self.metagraph, self.subtensor
        )
        viable, reason = self.trust_calculator.is_submission_viable(trust_result)
        if not viable:
            logger.warning(f"Skipping weight submission this epoch: {reason}")
            return
        await self._submit_weights(trust_result.processed_uids, trust_result.processed_weights)

    # ── Weight submission ────────────────────────────────────────────────

    async def _submit_weights(
        self,
        uids: List[int],
        weights: List[float],
    ) -> None:
        """Submit Yuma-aligned weights to the Bittensor chain."""
        current_block = self.subtensor.get_current_block()
        if current_block - self._last_weight_block < WEIGHT_SUBMISSION_INTERVAL_BLOCKS:
            logger.debug(
                f"Skipping weight submission: only "
                f"{current_block - self._last_weight_block} blocks since last submit"
            )
            return

        uid_array = np.array(uids, dtype=np.int64)
        weight_array = np.array(weights, dtype=np.float32)

        logger.info(
            f"Submitting weights | block={current_block} | "
            f"non-zero={np.count_nonzero(weight_array)}/{len(uid_array)} | "
            f"sum={weight_array.sum():.4f}"
        )

        try:
            result = self.subtensor.set_weights(
                netuid=self.config.netuid,
                wallet=self.wallet,
                uids=uid_array,
                weights=weight_array,
                wait_for_inclusion=True,
            )
            if result:
                self._last_weight_block = current_block
                logger.info("Weight submission confirmed on chain")
            else:
                logger.error("Weight submission returned False (check subtensor logs)")
        except Exception:
            logger.exception("Failed to submit weights to chain")

    # ── Helpers ──────────────────────────────────────────────────────────

    def _ensure_registered(self) -> None:
        """Register this hotkey on the subnet if not already registered."""
        if not self.subtensor.is_hotkey_registered(
            netuid=self.config.netuid,
            hotkey_ss58=self.wallet.hotkey.ss58_address,
        ):
            logger.info("Validator hotkey not registered. Registering...")
            self.subtensor.register(wallet=self.wallet, netuid=self.config.netuid)

    def _sync_metagraph(self) -> None:
        """Pull fresh metagraph state from the chain."""
        try:
            self.metagraph.sync(subtensor=self.subtensor)
            logger.debug(f"Metagraph synced | n={self.metagraph.n.item()}")
        except Exception:
            logger.exception("Metagraph sync failed")

    def _active_miner_uids(self) -> List[int]:
        """Return UIDs of registered Miners with a valid axon endpoint."""
        uids = []
        for uid in range(self.metagraph.n.item()):
            axon = self.metagraph.axons[uid]
            if axon.ip != "0.0.0.0" and axon.port != 0:
                uids.append(uid)
        return uids

    def _probe_interval(self) -> int:
        """Dynamic probe interval based on current miner count."""
        n = len(self._active_miner_uids())
        return self.probe_generator.probe_interval_sec(n)


def build_config() -> bt.config:
    """Build Bittensor config from CLI args."""
    parser = argparse.ArgumentParser(description="OpenClade Validator Node")
    bt.wallet.add_args(parser)
    bt.subtensor.add_args(parser)
    bt.logging.add_args(parser)
    parser.add_argument("--netuid", type=int, default=1, help="Subnet UID")
    return bt.config(parser)


def main() -> None:
    config = build_config()
    bt.logging(config=config)
    validator = OpenCladeValidator(config)
    asyncio.run(validator.run())


if __name__ == "__main__":
    main()
