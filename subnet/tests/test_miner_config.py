"""
Tests for MinerConfig — loading, validation, and environment variable overrides.
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from miner.config import MinerConfig


def write_config(data: dict) -> str:
    """Write a temp YAML config file and return its path."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(data, f)
        return f.name


VALID_CONFIG = {
    "wallet_name": "test-wallet",
    "wallet_hotkey": "test-hotkey",
    "netuid": 1,
    "subtensor_network": "test",
    "api_keys": ["sk-ant-api03-validkey0000000000000000"],
    "supported_models": ["claude-sonnet-4-6"],
}


class TestMinerConfigLoading:
    def test_load_valid_config(self):
        path = write_config(VALID_CONFIG)
        config = MinerConfig.load(path)
        assert config.wallet_name == "test-wallet"
        assert config.netuid == 1
        assert len(config.api_keys) == 1

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            MinerConfig.load("/nonexistent/path/config.yaml")

    def test_defaults_applied(self):
        minimal = {
            "api_keys": ["sk-ant-api03-minimal000000000000000"],
        }
        path = write_config(minimal)
        config = MinerConfig.load(path)
        assert config.wallet_name == "default"
        assert config.subtensor_network == "test"
        assert config.max_concurrent_requests == 10


class TestMinerConfigValidation:
    def test_empty_api_keys_raises(self):
        data = {**VALID_CONFIG, "api_keys": []}
        path = write_config(data)
        with pytest.raises(Exception):  # ValidationError
            MinerConfig.load(path)

    def test_invalid_api_key_format_raises(self):
        data = {**VALID_CONFIG, "api_keys": ["not-a-valid-key"]}
        path = write_config(data)
        with pytest.raises(Exception):
            MinerConfig.load(path)

    def test_zero_netuid_raises(self):
        data = {**VALID_CONFIG, "netuid": 0}
        path = write_config(data)
        with pytest.raises(Exception):
            MinerConfig.load(path)

    def test_negative_netuid_raises(self):
        data = {**VALID_CONFIG, "netuid": -1}
        path = write_config(data)
        with pytest.raises(Exception):
            MinerConfig.load(path)


class TestMinerConfigEnvOverride:
    def test_env_var_overrides_api_keys(self, monkeypatch):
        monkeypatch.setenv(
            "OPENCLAUDE_API_KEYS",
            "sk-ant-api03-envkey0000000000000001,sk-ant-api03-envkey0000000000000002",
        )
        path = write_config(VALID_CONFIG)
        config = MinerConfig.load(path)
        assert len(config.api_keys) == 2
        assert "sk-ant-api03-envkey0000000000000001" in config.api_keys

    def test_no_env_var_uses_yaml_keys(self, monkeypatch):
        monkeypatch.delenv("OPENCLAUDE_API_KEYS", raising=False)
        path = write_config(VALID_CONFIG)
        config = MinerConfig.load(path)
        assert config.api_keys == ["sk-ant-api03-validkey0000000000000000"]
