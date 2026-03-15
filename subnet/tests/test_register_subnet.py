"""
Tests for register_subnet.py — bittensor v10 API compatibility.

These tests mock the bittensor SDK to validate the registration
logic without requiring real TAO or network access.
"""

from unittest.mock import MagicMock, patch, call
import sys
import pytest


# ── Helpers ──────────────────────────────────────────────────────────────────


def make_mock_subtensor(
    network: str = "test",
    block: int = 1000,
    subnets: list = None,
    is_registered: bool = False,
):
    """Create a mock Subtensor with common v10 API methods."""
    mock = MagicMock()
    mock.network = network
    mock.get_current_block.return_value = block
    mock.get_balance.return_value = MagicMock(__str__=lambda s: "τ100.0 TAO")
    mock.register_subnet.return_value = True
    mock.burned_register.return_value = True
    mock.get_all_subnets_netuid.return_value = subnets or [1, 2, 3]
    mock.is_hotkey_registered.return_value = is_registered
    return mock


def make_mock_wallet(coldkey: str = "5COLD", hotkey: str = "5HOT"):
    """Create a mock Wallet with ss58 addresses."""
    mock = MagicMock()
    mock.coldkeypub.ss58_address = coldkey
    mock.hotkey.ss58_address = hotkey
    return mock


# ── Tests for register_subnet() ─────────────────────────────────────────────


class TestRegisterSubnet:
    """Tests for the register_subnet() function."""

    def test_calls_register_subnet_method(self):
        """Should call subtensor.register_subnet (v10 API)."""
        from scripts.register_subnet import register_subnet

        subtensor = make_mock_subtensor(subnets=[1, 2, 5])
        wallet = make_mock_wallet()

        netuid = register_subnet(subtensor, wallet)

        subtensor.register_subnet.assert_called_once_with(
            wallet=wallet, wait_for_inclusion=True
        )

    def test_returns_max_netuid(self):
        """Should return the highest netuid after registration."""
        from scripts.register_subnet import register_subnet

        subtensor = make_mock_subtensor(subnets=[1, 2, 7])
        wallet = make_mock_wallet()

        netuid = register_subnet(subtensor, wallet)
        assert netuid == 7

    def test_raises_on_failure(self):
        """Should raise RuntimeError when registration returns False."""
        from scripts.register_subnet import register_subnet

        subtensor = make_mock_subtensor()
        subtensor.register_subnet.return_value = False
        wallet = make_mock_wallet()

        with pytest.raises(RuntimeError, match="Subnet registration failed"):
            register_subnet(subtensor, wallet)

    def test_checks_balance_before_registration(self):
        """Should check wallet balance before attempting registration."""
        from scripts.register_subnet import register_subnet

        subtensor = make_mock_subtensor()
        wallet = make_mock_wallet()

        register_subnet(subtensor, wallet)

        subtensor.get_balance.assert_called_once_with(wallet.coldkeypub.ss58_address)

    def test_does_not_call_register_subnetwork(self):
        """Must NOT call the old v8 API method register_subnetwork."""
        from scripts.register_subnet import register_subnet

        subtensor = make_mock_subtensor()
        wallet = make_mock_wallet()

        register_subnet(subtensor, wallet)

        subtensor.register_subnetwork.assert_not_called()


# ── Tests for register_neuron() ─────────────────────────────────────────────


class TestRegisterNeuron:
    """Tests for the register_neuron() function."""

    def test_calls_burned_register(self):
        """Should call subtensor.burned_register (v10 API)."""
        from scripts.register_subnet import register_neuron

        subtensor = make_mock_subtensor(is_registered=False)
        wallet = make_mock_wallet()

        register_neuron(subtensor, wallet, netuid=3)

        subtensor.burned_register.assert_called_once_with(
            wallet=wallet, netuid=3, wait_for_inclusion=True
        )

    def test_skips_if_already_registered(self):
        """Should skip registration if hotkey already registered."""
        from scripts.register_subnet import register_neuron

        subtensor = make_mock_subtensor(is_registered=True)
        wallet = make_mock_wallet()

        register_neuron(subtensor, wallet, netuid=3)

        subtensor.burned_register.assert_not_called()

    def test_raises_on_failure(self):
        """Should raise RuntimeError when burned_register returns False."""
        from scripts.register_subnet import register_neuron

        subtensor = make_mock_subtensor(is_registered=False)
        subtensor.burned_register.return_value = False
        wallet = make_mock_wallet()

        with pytest.raises(RuntimeError, match="Neuron registration failed"):
            register_neuron(subtensor, wallet, netuid=3)

    def test_does_not_call_old_register(self):
        """Must NOT call the old v8 btcli PoW register method."""
        from scripts.register_subnet import register_neuron

        subtensor = make_mock_subtensor(is_registered=False)
        wallet = make_mock_wallet()

        register_neuron(subtensor, wallet, netuid=3)

        # The old PoW `register` should NOT be called
        subtensor.register.assert_not_called()


# ── Tests for verify_subnet_state() ─────────────────────────────────────────


class TestVerifySubnetState:
    """Tests for the verify_subnet_state() function (v10 API)."""

    def test_syncs_metagraph(self):
        """Should create and sync a Metagraph for the given netuid."""
        from scripts.register_subnet import verify_subnet_state

        mock_metagraph = MagicMock()
        mock_metagraph.n.item.return_value = 5

        subtensor = make_mock_subtensor()

        with patch("bittensor.Metagraph", return_value=mock_metagraph) as mock_meta_cls:
            verify_subnet_state(subtensor, netuid=3)

        mock_meta_cls.assert_called_once_with(netuid=3, network="test")
        mock_metagraph.sync.assert_called_once_with(subtensor=subtensor)

    def test_does_not_crash_on_error(self):
        """Should catch and log errors without raising."""
        from scripts.register_subnet import verify_subnet_state

        subtensor = make_mock_subtensor()

        with patch("bittensor.Metagraph", side_effect=RuntimeError("chain error")):
            # Should not raise
            verify_subnet_state(subtensor, netuid=99)


# ── Integration: full registration flow mock ─────────────────────────────────


class TestRegistrationFlow:
    """Integration tests for the full registration flow."""

    def test_full_flow_subnet_then_neuron(self):
        """Should register subnet then immediately register validator."""
        from scripts.register_subnet import register_subnet, register_neuron

        subtensor = make_mock_subtensor(subnets=[1, 2, 10])
        wallet_owner = make_mock_wallet("5COLD_OWNER", "5HOT_OWNER")
        wallet_validator = make_mock_wallet("5COLD_VAL", "5HOT_VAL")

        # Step 1: register subnet
        netuid = register_subnet(subtensor, wallet_owner)
        assert netuid == 10

        # Step 2: register validator on new subnet
        register_neuron(subtensor, wallet_validator, netuid=netuid)
        subtensor.burned_register.assert_called_once_with(
            wallet=wallet_validator, netuid=10, wait_for_inclusion=True
        )

    def test_netuid_from_registration_passed_to_neuron_register(self):
        """netuid returned from register_subnet should be used for neuron registration."""
        from scripts.register_subnet import register_subnet, register_neuron

        expected_netuid = 42
        subtensor = make_mock_subtensor(subnets=[1, 5, expected_netuid])
        owner = make_mock_wallet()
        miner = make_mock_wallet("5COLD_MINER", "5HOT_MINER")

        netuid = register_subnet(subtensor, owner)
        assert netuid == expected_netuid

        register_neuron(subtensor, miner, netuid=netuid)
        call_kwargs = subtensor.burned_register.call_args
        assert call_kwargs.kwargs["netuid"] == expected_netuid
