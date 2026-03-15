"""
Test configuration and bittensor mock setup.

Bittensor is heavy and requires chain connectivity. For unit tests,
we mock the bt module so the protocol, scoring, and api_pool modules
can be imported and tested in isolation.

The mock is installed into sys.modules BEFORE any subnet code is imported,
so the `import bittensor as bt` in synapse.py gets our mock instead.
"""

import sys
from unittest.mock import MagicMock

import pytest


def _install_bittensor_mock() -> MagicMock:
    """
    Build a minimal bittensor mock that satisfies subnet module imports.

    Supports bittensor v10 CamelCase API:
    - bt.Synapse (base class for LLMAPISynapse)
    - bt.Wallet, bt.Axon, bt.Dendrite, bt.Subtensor, bt.Metagraph  (v10)
    - bt.Config, bt.logging                                          (v10)
    """
    bt_mock = MagicMock()

    # bt.Synapse must be a real Pydantic BaseModel so LLMAPISynapse's
    # field declarations (messages: List[...] etc.) work correctly.
    from pydantic import BaseModel

    class FakeSynapse(BaseModel):
        """Pydantic-based Synapse base class for testing."""
        model_config = {"arbitrary_types_allowed": True}

    bt_mock.Synapse = FakeSynapse

    # bittensor v10: CamelCase API — explicitly set to catch any misuse
    bt_mock.Wallet = MagicMock()
    bt_mock.Axon = MagicMock()
    bt_mock.Dendrite = MagicMock()
    bt_mock.Subtensor = MagicMock()
    bt_mock.Metagraph = MagicMock()
    bt_mock.Config = MagicMock()
    bt_mock.logging = MagicMock()

    sys.modules["bittensor"] = bt_mock
    return bt_mock


# Install mock immediately when conftest is loaded (before any test collection)
_bt_mock = _install_bittensor_mock()


@pytest.fixture(autouse=True, scope="session")
def bittensor_mock():
    """Expose the bittensor mock to tests that need to inspect it."""
    return _bt_mock
