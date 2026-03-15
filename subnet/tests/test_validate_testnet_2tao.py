"""
Tests for validate_testnet_2tao.py — unit tests with mocked bittensor SDK.

These tests verify the validation logic without real TAO or network access.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


# ── Fixtures ──────────────────────────────────────────────────────────────────


def make_mock_subtensor(
    block: int = 7000000,
    balance_tao: float = 2.0,
    reg_cost: float = 0.0005,
    hotkey_registered: bool = False,
):
    mock = MagicMock()
    mock.get_current_block.return_value = block
    bal_mock = MagicMock()
    bal_mock.__str__ = lambda s: f"τ{balance_tao:.9f}"
    mock.get_balance.return_value = bal_mock
    mock.recycle.return_value = MagicMock(__str__=lambda s: f"τ{reg_cost:.9f}")
    mock.is_hotkey_registered.return_value = hotkey_registered

    # Successful burned_register response
    reg_response = MagicMock()
    reg_response.success = True
    mock.burned_register.return_value = reg_response

    # Weight submission
    weight_response = MagicMock()
    weight_response.success = True
    mock.set_weights.return_value = weight_response

    return mock


def make_mock_wallet(name: str = "test", hotkey: str = "test-hotkey"):
    mock = MagicMock()
    mock.coldkeypub.ss58_address = f"5COLD_{name}"
    mock.hotkey.ss58_address = f"5HOT_{hotkey}"
    return mock


# ── check_connectivity ────────────────────────────────────────────────────────


class TestCheckConnectivity:
    def test_passes_when_balance_sufficient(self):
        with (
            patch("validate_testnet_2tao.bt.Subtensor", return_value=make_mock_subtensor(balance_tao=2.0)),
            patch("validate_testnet_2tao.bt.Wallet", return_value=make_mock_wallet()),
        ):
            from validate_testnet_2tao import check_connectivity
            result = check_connectivity()
        assert result["passed"] is True
        assert result["details"]["block"] == 7000000

    def test_fails_when_balance_zero(self):
        with (
            patch("validate_testnet_2tao.bt.Subtensor", return_value=make_mock_subtensor(balance_tao=0.0)),
            patch("validate_testnet_2tao.bt.Wallet", return_value=make_mock_wallet()),
        ):
            from validate_testnet_2tao import check_connectivity
            result = check_connectivity()
        assert result["passed"] is False

    def test_fails_on_connection_error(self):
        with patch("validate_testnet_2tao.bt.Subtensor", side_effect=ConnectionError("refused")):
            from validate_testnet_2tao import check_connectivity
            result = check_connectivity()
        assert result["passed"] is False
        assert "error" in result["details"]

    def test_includes_registration_cost(self):
        sub = make_mock_subtensor(balance_tao=1.0, reg_cost=0.0005)
        with (
            patch("validate_testnet_2tao.bt.Subtensor", return_value=sub),
            patch("validate_testnet_2tao.bt.Wallet", return_value=make_mock_wallet()),
        ):
            from validate_testnet_2tao import check_connectivity
            result = check_connectivity()
        assert "reg_cost" in result["details"]


# ── register_miner ────────────────────────────────────────────────────────────


class TestRegisterMiner:
    def test_registers_when_not_registered(self):
        sub = make_mock_subtensor(hotkey_registered=False, balance_tao=1.0)
        wallet = make_mock_wallet("openclaude-miner", "miner")
        with (
            patch("validate_testnet_2tao.bt.Subtensor", return_value=sub),
            patch("validate_testnet_2tao.bt.Wallet", return_value=wallet),
        ):
            from validate_testnet_2tao import register_miner
            result = register_miner(netuid=1)
        assert result["passed"] is True
        sub.burned_register.assert_called_once()

    def test_skips_if_already_registered(self):
        sub = make_mock_subtensor(hotkey_registered=True)
        wallet = make_mock_wallet()
        with (
            patch("validate_testnet_2tao.bt.Subtensor", return_value=sub),
            patch("validate_testnet_2tao.bt.Wallet", return_value=wallet),
        ):
            from validate_testnet_2tao import register_miner
            result = register_miner(netuid=1)
        assert result["passed"] is True
        assert result["details"].get("already_registered") is True
        sub.burned_register.assert_not_called()

    def test_fails_when_registration_fails(self):
        sub = make_mock_subtensor(hotkey_registered=False, balance_tao=1.0)
        sub.burned_register.return_value = MagicMock(success=False)
        wallet = make_mock_wallet()
        with (
            patch("validate_testnet_2tao.bt.Subtensor", return_value=sub),
            patch("validate_testnet_2tao.bt.Wallet", return_value=wallet),
        ):
            from validate_testnet_2tao import register_miner
            result = register_miner(netuid=1)
        assert result["passed"] is False

    def test_handles_exception_gracefully(self):
        with (
            patch("validate_testnet_2tao.bt.Subtensor", side_effect=RuntimeError("network error")),
            patch("validate_testnet_2tao.bt.Wallet", return_value=make_mock_wallet()),
        ):
            from validate_testnet_2tao import register_miner
            result = register_miner(netuid=1)
        assert result["passed"] is False
        assert "error" in result["details"]


# ── register_validator ────────────────────────────────────────────────────────


class TestRegisterValidator:
    def test_registers_when_not_registered(self):
        sub = make_mock_subtensor(hotkey_registered=False, balance_tao=1.0)
        wallet = make_mock_wallet()
        with (
            patch("validate_testnet_2tao.bt.Subtensor", return_value=sub),
            patch("validate_testnet_2tao.bt.Wallet", return_value=wallet),
        ):
            from validate_testnet_2tao import register_validator
            result = register_validator(netuid=1)
        assert result["passed"] is True

    def test_skips_if_already_registered(self):
        sub = make_mock_subtensor(hotkey_registered=True)
        wallet = make_mock_wallet()
        with (
            patch("validate_testnet_2tao.bt.Subtensor", return_value=sub),
            patch("validate_testnet_2tao.bt.Wallet", return_value=wallet),
        ):
            from validate_testnet_2tao import register_validator
            result = register_validator(netuid=1)
        assert result["passed"] is True
        sub.burned_register.assert_not_called()


# ── verify_axon_discoverability ───────────────────────────────────────────────


class TestVerifyAxonDiscoverability:
    def test_skips_if_miner_not_registered(self):
        sub = make_mock_subtensor(hotkey_registered=False)
        wallet = make_mock_wallet()
        with (
            patch("validate_testnet_2tao.bt.Subtensor", return_value=sub),
            patch("validate_testnet_2tao.bt.Wallet", return_value=wallet),
        ):
            from validate_testnet_2tao import verify_axon_discoverability
            result = verify_axon_discoverability(netuid=1)
        assert result["passed"] is None  # inconclusive
        assert result["details"].get("skipped") == "miner_not_registered"

    def test_passes_when_axon_serving(self):
        sub = make_mock_subtensor(hotkey_registered=True)
        neuron_mock = MagicMock()
        neuron_mock.axon_info.ip = "192.168.1.1"
        neuron_mock.axon_info.port = 8091
        neuron_mock.axon_info.hotkey = "5HOT_miner"
        sub.get_neuron_for_pubkey_and_subnet.return_value = neuron_mock
        wallet = make_mock_wallet()
        with (
            patch("validate_testnet_2tao.bt.Subtensor", return_value=sub),
            patch("validate_testnet_2tao.bt.Wallet", return_value=wallet),
        ):
            from validate_testnet_2tao import verify_axon_discoverability
            result = verify_axon_discoverability(netuid=1)
        assert result["passed"] is True
        assert result["details"]["axon"]["ip"] == "192.168.1.1"

    def test_fails_when_axon_not_serving(self):
        sub = make_mock_subtensor(hotkey_registered=True)
        neuron_mock = MagicMock()
        neuron_mock.axon_info.ip = "0.0.0.0"
        neuron_mock.axon_info.port = 0
        sub.get_neuron_for_pubkey_and_subnet.return_value = neuron_mock
        wallet = make_mock_wallet()
        with (
            patch("validate_testnet_2tao.bt.Subtensor", return_value=sub),
            patch("validate_testnet_2tao.bt.Wallet", return_value=wallet),
        ):
            from validate_testnet_2tao import verify_axon_discoverability
            result = verify_axon_discoverability(netuid=1)
        assert result["passed"] is False
        assert result["details"]["axon"] == "not_serving"


# ── verify_weight_submission ──────────────────────────────────────────────────


class TestVerifyWeightSubmission:
    def test_skips_when_validator_not_registered(self):
        sub = make_mock_subtensor(hotkey_registered=False)
        wallet = make_mock_wallet()
        with (
            patch("validate_testnet_2tao.bt.Subtensor", return_value=sub),
            patch("validate_testnet_2tao.bt.Wallet", return_value=wallet),
        ):
            from validate_testnet_2tao import verify_weight_submission
            result = verify_weight_submission(netuid=1)
        assert result["passed"] is None
        assert result["details"]["skipped"] == "validator_not_registered"

    def test_passes_when_weights_submitted(self):
        sub = make_mock_subtensor(hotkey_registered=True)
        sub.metagraph.side_effect = Exception("no metagraph")  # fallback to test UIDs
        wallet = make_mock_wallet()
        with (
            patch("validate_testnet_2tao.bt.Subtensor", return_value=sub),
            patch("validate_testnet_2tao.bt.Wallet", return_value=wallet),
        ):
            from validate_testnet_2tao import verify_weight_submission
            result = verify_weight_submission(netuid=1)
        assert result["passed"] is True

    def test_reports_weight_count_and_sum(self):
        sub = make_mock_subtensor(hotkey_registered=True)
        sub.metagraph.side_effect = Exception("no metagraph")
        wallet = make_mock_wallet()
        with (
            patch("validate_testnet_2tao.bt.Subtensor", return_value=sub),
            patch("validate_testnet_2tao.bt.Wallet", return_value=wallet),
        ):
            from validate_testnet_2tao import verify_weight_submission
            result = verify_weight_submission(netuid=1)
        assert "uids_count" in result["details"]
        assert abs(result["details"]["weights_sum"] - 1.0) < 0.01  # should sum to ~1.0
