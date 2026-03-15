"""
OpenClade Miner Neuron.

Registers on the Bittensor subnet and serves Claude API requests forwarded
by Validators via the LLMAPISynapse protocol.

Architecture:
  Validator (dendrite) → [LLMAPISynapse request] → Miner Axon
  Miner Axon → [Claude API call] → Anthropic
  Miner Axon → [LLMAPISynapse response] → Validator

Entry point:
  python neurons/miner.py --config config/miner.yaml
"""

import argparse
import asyncio
import time
from pathlib import Path
from typing import Tuple

import anthropic
import bittensor as bt
from loguru import logger

from miner.api_pool import APIKeyPool
from miner.config import MinerConfig
from protocol.synapse import LLMAPISynapse


class OpenCladeMiner:
    """
    Bittensor Miner that proxies Claude API requests for the OpenClade subnet.

    Lifecycle:
        1. Load config, connect wallet and subtensor.
        2. Start Axon, register on chain if needed.
        3. Loop: run_epoch() — refresh metagraph, handle requests.
        4. On shutdown: gracefully stop Axon.
    """

    def __init__(self, config_path: str) -> None:
        self.config = MinerConfig.load(config_path)
        self.wallet = bt.Wallet(
            name=self.config.wallet_name,
            hotkey=self.config.wallet_hotkey,
        )
        self.subtensor = bt.Subtensor(network=self.config.subtensor_network)
        self.metagraph = bt.Metagraph(
            netuid=self.config.netuid,
            network=self.config.subtensor_network,
        )
        self.api_pool = APIKeyPool(self.config.api_keys)
        self.axon = bt.Axon(
            wallet=self.wallet,
            port=self.config.axon_port,
            ip=self.config.axon_ip,
        )
        self._register_axon_handlers()
        logger.info(
            f"OpenCladeMiner initialized | "
            f"netuid={self.config.netuid} | "
            f"wallet={self.wallet.hotkey.ss58_address}"
        )

    def _register_axon_handlers(self) -> None:
        """Attach blacklist, priority, and forward handlers to the Axon."""
        self.axon.attach(
            forward_fn=self.forward,
            blacklist_fn=self.blacklist,
            priority_fn=self.priority,
        )

    # ── Axon handler: blacklist ──────────────────────────────────────────

    async def blacklist(self, synapse: LLMAPISynapse) -> Tuple[bool, str]:
        """
        Reject requests from unknown or under-staked Validators.

        Returns:
            (True, reason)  — reject the request
            (False, "")     — allow the request through
        """
        hotkey = synapse.dendrite.hotkey
        uid = self._uid_for_hotkey(hotkey)

        if uid is None:
            logger.warning(f"Blacklisted: unknown hotkey {hotkey}")
            return True, "Hotkey not registered in subnet metagraph"

        stake = self.metagraph.S[uid].item()
        if stake < self.config.min_stake_tao:
            logger.warning(
                f"Blacklisted: hotkey {hotkey} stake={stake:.2f} < "
                f"min={self.config.min_stake_tao}"
            )
            return True, f"Insufficient stake: {stake:.2f} TAO < {self.config.min_stake_tao} TAO"

        requested_model = synapse.model
        if requested_model not in self.config.supported_models:
            logger.warning(f"Blacklisted: unsupported model {requested_model}")
            return True, f"Model not supported: {requested_model}"

        return False, ""

    # ── Axon handler: priority ───────────────────────────────────────────

    async def priority(self, synapse: LLMAPISynapse) -> float:
        """
        Assign request priority based on Validator stake.

        Higher stake → higher priority → processed first in the queue.
        """
        hotkey = synapse.dendrite.hotkey
        uid = self._uid_for_hotkey(hotkey)
        if uid is None:
            return 0.0
        stake = self.metagraph.S[uid].item()
        logger.debug(f"Priority for {hotkey}: stake={stake:.2f}")
        return float(stake)

    # ── Axon handler: forward ────────────────────────────────────────────

    async def forward(self, synapse: LLMAPISynapse) -> LLMAPISynapse:
        """
        Core request handler: forward the LLM request to Claude API.

        Steps:
          1. Acquire an available API key from the pool.
          2. Call Claude API (anthropic SDK).
          3. Record success/failure and return populated synapse.

        Error handling:
          - Pool exhausted → return error synapse (don't crash Axon).
          - AuthenticationError → quarantine key, retry with next key once.
          - RateLimitError → quarantine key briefly.
          - All other errors → log and return error synapse.
        """
        start_time = time.time()
        logger.info(
            f"forward() | model={synapse.model} | "
            f"messages={len(synapse.messages)} | "
            f"request_id={synapse.request_id}"
        )

        key_entry = self.api_pool.acquire()
        if key_entry is None:
            synapse.error_message = "All API keys exhausted or quarantined"
            logger.error(f"request_id={synapse.request_id} | {synapse.error_message}")
            return synapse

        try:
            client = anthropic.AsyncAnthropic(api_key=key_entry.key)
            message = await client.messages.create(
                model=synapse.model,
                max_tokens=synapse.max_tokens,
                temperature=synapse.temperature,
                messages=synapse.messages,  # type: ignore[arg-type]
            )

            synapse.response = message.content[0].text if message.content else ""
            synapse.tokens_used = (
                message.usage.input_tokens + message.usage.output_tokens
            )
            synapse.finish_reason = message.stop_reason or "end_turn"
            synapse.miner_model_used = message.model
            synapse.latency_ms = int((time.time() - start_time) * 1000)
            synapse.compute_response_hash()

            self.api_pool.release(key_entry, success=True, tokens_used=synapse.tokens_used)
            logger.info(
                f"forward() success | request_id={synapse.request_id} | "
                f"tokens={synapse.tokens_used} | latency={synapse.latency_ms}ms"
            )

        except anthropic.AuthenticationError as e:
            logger.error(f"AuthenticationError for key ...{key_entry.key[-4:]}: {e}")
            self.api_pool.release(key_entry, success=False, is_auth_error=True)
            synapse.error_message = "API key authentication failed"
            synapse.latency_ms = int((time.time() - start_time) * 1000)

        except anthropic.RateLimitError as e:
            logger.warning(f"RateLimitError for key ...{key_entry.key[-4:]}: {e}")
            self.api_pool.release(key_entry, success=False, is_auth_error=False)
            synapse.error_message = "Claude API rate limit exceeded"
            synapse.latency_ms = int((time.time() - start_time) * 1000)

        except Exception as e:
            logger.exception(
                f"Unexpected error in forward() | request_id={synapse.request_id}"
            )
            self.api_pool.release(key_entry, success=False)
            synapse.error_message = f"Internal miner error: {type(e).__name__}"
            synapse.latency_ms = int((time.time() - start_time) * 1000)

        return synapse

    # ── Lifecycle ────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start the Miner: register on chain and serve requests."""
        self._ensure_registered()
        self.axon.start()
        logger.info(
            f"Axon serving on port {self.config.axon_port} | "
            f"Ctrl+C to stop"
        )
        try:
            while True:
                self._sync_metagraph()
                time.sleep(30)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        finally:
            self.axon.stop()
            logger.info("Axon stopped. Goodbye.")

    def _ensure_registered(self) -> None:
        """Register this hotkey on the subnet if not already registered."""
        if not self.subtensor.is_hotkey_registered(
            netuid=self.config.netuid,
            hotkey_ss58=self.wallet.hotkey.ss58_address,
        ):
            logger.info("Hotkey not registered. Registering (burned_register)...")
            self.subtensor.burned_register(
                wallet=self.wallet,
                netuid=self.config.netuid,
            )
            logger.info("Registration successful")
        else:
            logger.info("Hotkey already registered on subnet")

    def _sync_metagraph(self) -> None:
        """Refresh metagraph state from chain."""
        try:
            self.metagraph.sync(subtensor=self.subtensor)
            logger.debug("Metagraph synced")
        except Exception:
            logger.exception("Failed to sync metagraph (will retry)")

    def _uid_for_hotkey(self, hotkey: str) -> int | None:
        """Return the UID for a hotkey, or None if not in metagraph."""
        hotkeys = self.metagraph.hotkeys
        if hotkey in hotkeys:
            return hotkeys.index(hotkey)
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenClade Miner Node")
    parser.add_argument(
        "--config",
        type=str,
        default="config/miner.yaml",
        help="Path to miner YAML config file",
    )
    args = parser.parse_args()
    miner = OpenCladeMiner(config_path=args.config)
    miner.run()


if __name__ == "__main__":
    main()
