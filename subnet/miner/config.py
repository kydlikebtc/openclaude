"""
Miner configuration loader.

Config is stored as YAML on disk (never committed to git).
Sensitive fields (api_keys) are encrypted at rest using the
cryptography library — see encrypt_config.py for the setup tool.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import yaml
from loguru import logger
from pydantic import BaseModel, field_validator


class MinerConfig(BaseModel):
    """Validated miner configuration loaded from YAML."""

    # Bittensor wallet settings
    wallet_name: str = "default"
    wallet_hotkey: str = "default"
    netuid: int = 1  # Subnet UID on the Bittensor network

    # Network settings
    subtensor_network: str = "test"  # "test" | "finney" | "local"
    subtensor_chain_endpoint: Optional[str] = None
    axon_port: int = 8091
    axon_ip: Optional[str] = None  # None = auto-detect

    # Claude API
    api_keys: List[str] = []
    supported_models: List[str] = [
        "claude-haiku-4-5-20251001",
        "claude-sonnet-4-6",
    ]
    default_max_tokens: int = 4096

    # Scoring / safety
    max_concurrent_requests: int = 10
    request_timeout_sec: int = 60
    min_stake_tao: float = 5.0  # Minimum validator stake to accept requests

    @field_validator("api_keys")
    @classmethod
    def api_keys_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one api_key must be configured")
        for key in v:
            if not key.startswith("sk-ant-"):
                raise ValueError(f"Invalid Anthropic API key format: {key[:10]}...")
        return v

    @field_validator("netuid")
    @classmethod
    def netuid_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("netuid must be a positive integer")
        return v

    @classmethod
    def load(cls, path: str | Path) -> "MinerConfig":
        """
        Load and validate configuration from a YAML file.

        Raises FileNotFoundError if the config file doesn't exist.
        Raises ValidationError if any required fields are missing or invalid.
        """
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Miner config not found: {config_path}")

        with open(config_path) as f:
            raw = yaml.safe_load(f)

        # Support environment variable overrides for CI / container deployments
        if "OPENCLAUDE_API_KEYS" in os.environ:
            raw["api_keys"] = os.environ["OPENCLAUDE_API_KEYS"].split(",")
            logger.info("API keys loaded from OPENCLAUDE_API_KEYS environment variable")

        config = cls(**raw)
        logger.info(
            f"MinerConfig loaded: netuid={config.netuid}, "
            f"network={config.subtensor_network}, "
            f"keys={len(config.api_keys)}"
        )
        return config
