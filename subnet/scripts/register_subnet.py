#!/usr/bin/env python3
"""
OpenClade Subnet Registration Script.

Registers the OpenClade subnet on Bittensor testnet (or mainnet) and
optionally registers validator/miner hotkeys on the new subnet.

Usage:
  # Register subnet only (returns netuid)
  python scripts/register_subnet.py \\
    --wallet.name owner \\
    --wallet.hotkey owner \\
    --network test \\
    --register-subnet

  # Register validator on existing subnet
  python scripts/register_subnet.py \\
    --wallet.name validator \\
    --wallet.hotkey validator \\
    --network test \\
    --netuid 1 \\
    --register-neuron

  # Full flow: register subnet + validator + miner in sequence
  python scripts/register_subnet.py \\
    --wallet.name owner \\
    --wallet.hotkey owner \\
    --network test \\
    --register-subnet \\
    --register-neuron

Prerequisites:
  - Bittensor SDK installed: pip install bittensor>=7.0.0
  - Owner wallet funded with TAO (testnet faucet: test.taostats.io)
  - For testnet: ~100 TAO for subnet creation
  - For mainnet: 1000+ TAO for subnet creation (check current pricing)

Safety notes:
  - Always test on testnet before mainnet.
  - Subnet creation is irreversible — a new netuid will be allocated.
  - Registration transactions burn TAO — ensure wallet has sufficient balance.
  - This script never commits, stores, or logs wallet credentials.
"""

import argparse
import sys
from typing import Optional

from loguru import logger


def register_subnet(subtensor, wallet) -> int:
    """
    Register a new subnet on the Bittensor chain.

    Returns the allocated netuid. Raises RuntimeError if registration fails.
    """
    logger.info(
        f"Registering new subnet | "
        f"network={subtensor.network} | "
        f"hotkey={wallet.hotkey.ss58_address}"
    )

    # Check wallet balance before attempting registration
    balance = subtensor.get_balance(wallet.coldkeypub.ss58_address)
    logger.info(f"Wallet balance: {balance} TAO")

    # Attempt subnet registration
    success = subtensor.register_subnetwork(wallet=wallet, wait_for_inclusion=True)
    if not success:
        raise RuntimeError(
            "Subnet registration failed. Ensure wallet has sufficient TAO balance "
            "and the network is reachable."
        )

    # Get the newly allocated netuid (last registered subnet)
    subnets = subtensor.get_subnets()
    netuid = max(subnets) if subnets else -1

    logger.info(f"Subnet registered successfully | netuid={netuid}")
    return netuid


def register_neuron(subtensor, wallet, netuid: int) -> None:
    """
    Register a hotkey on an existing subnet via Proof-of-Work.

    This burns recycled TAO for testnet. On mainnet it burns TAO directly.
    """
    logger.info(
        f"Registering neuron | "
        f"netuid={netuid} | "
        f"hotkey={wallet.hotkey.ss58_address}"
    )

    is_registered = subtensor.is_hotkey_registered(
        netuid=netuid,
        hotkey_ss58=wallet.hotkey.ss58_address,
    )
    if is_registered:
        logger.info("Hotkey already registered on subnet — skipping")
        return

    logger.info("Starting PoW registration (this may take several minutes)...")
    success = subtensor.register(
        wallet=wallet,
        netuid=netuid,
        wait_for_inclusion=True,
    )

    if not success:
        raise RuntimeError(
            f"Neuron registration failed on subnet {netuid}. "
            "Try increasing num_processes in registration config."
        )

    logger.info(f"Neuron registered successfully on netuid={netuid}")


def verify_subnet_state(subtensor, netuid: int) -> None:
    """Log current subnet state for verification."""
    try:
        metagraph = subtensor.metagraph(netuid=netuid)
        metagraph.sync()
        logger.info(
            f"Subnet state | netuid={netuid} | "
            f"n_neurons={metagraph.n.item()} | "
            f"block={subtensor.get_current_block()}"
        )
    except Exception as e:
        logger.warning(f"Could not fetch subnet state: {e}")


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OpenClade Subnet Registration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Bittensor standard args
    parser.add_argument("--wallet.name", default="default", help="Coldkey wallet name")
    parser.add_argument("--wallet.hotkey", default="default", help="Hotkey name")
    parser.add_argument(
        "--network",
        default="test",
        choices=["test", "local", "finney"],
        help="Bittensor network (default: test)",
    )
    parser.add_argument("--netuid", type=int, default=None, help="Subnet UID (for neuron registration)")

    # Registration flags
    parser.add_argument(
        "--register-subnet",
        action="store_true",
        help="Register a new subnet (allocates a netuid)",
    )
    parser.add_argument(
        "--register-neuron",
        action="store_true",
        help="Register hotkey on the subnet as a neuron",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify and print subnet state after registration",
    )

    return parser.parse_args()


def main() -> None:
    args = build_args()

    try:
        import bittensor as bt
    except ImportError:
        logger.error(
            "Bittensor SDK not installed. Run: pip install bittensor>=7.0.0"
        )
        sys.exit(1)

    logger.info(f"Connecting to Bittensor {args.network} network...")
    subtensor = bt.subtensor(network=args.network)

    wallet_name = getattr(args, "wallet.name", "default")
    wallet_hotkey = getattr(args, "wallet.hotkey", "default")
    wallet = bt.wallet(name=wallet_name, hotkey=wallet_hotkey)

    logger.info(
        f"Using wallet | coldkey={wallet.coldkeypub.ss58_address} | "
        f"hotkey={wallet.hotkey.ss58_address}"
    )

    netuid: Optional[int] = args.netuid

    if args.register_subnet:
        netuid = register_subnet(subtensor, wallet)
        logger.info(f"SUBNET NETUID: {netuid} (save this for your config files)")

    if args.register_neuron:
        if netuid is None:
            logger.error("--netuid required for neuron registration (or use --register-subnet first)")
            sys.exit(1)
        register_neuron(subtensor, wallet, netuid)

    if args.verify and netuid is not None:
        verify_subnet_state(subtensor, netuid)

    if not args.register_subnet and not args.register_neuron:
        logger.warning("No action specified. Use --register-subnet or --register-neuron")
        logger.info("Run with --help for usage information")


if __name__ == "__main__":
    main()
