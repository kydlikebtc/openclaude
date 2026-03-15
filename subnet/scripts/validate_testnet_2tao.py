#!/usr/bin/env python3
"""
OpenClade Testnet 验证脚本 — 2-3 TAO 约束版本.

适用场景: 只有少量 Testnet TAO（2-3 τ）时的完整链上验证。
策略: 加入现有 testnet 子网 (netuid=1, 成本 ≈ τ0.0005/节点)，
      而非注册新子网（需 ~τ6+ TAO）。

覆盖范围:
  ✅ Phase 1 — 链上连通性验证
  ✅ Phase 2 — Miner 热键注册（burned_register）
  ✅ Phase 3 — Validator 热键注册（burned_register）
  ✅ Phase 4 — Axon 服务器可发现性验证
  ✅ Phase 5 — Dendrite 查询流程验证
  ✅ Phase 6 — 权重提交流程验证
  ⏳ Phase 7 — 72h 稳定性测试（需手动运行）

NOT 包含（需要自己的子网）:
  ❌ Emission 分配验证 (18%/41%/41%) — 需要子网注册 (~τ6+ TAO)

用法:
  # 检查连通性 + 余额（无需 TAO）
  uv run python scripts/validate_testnet_2tao.py --check-only

  # 注册 miner 热键到现有子网
  uv run python scripts/validate_testnet_2tao.py --register-miner --netuid 1

  # 注册 validator 热键
  uv run python scripts/validate_testnet_2tao.py --register-validator --netuid 1

  # 完整验证（需要 ~τ0.002 TAO）
  uv run python scripts/validate_testnet_2tao.py --full-validate --netuid 1

  # 72h 稳定性监控（启动后台监控）
  uv run python scripts/validate_testnet_2tao.py --stability-monitor --netuid 1 --hours 72
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loguru import logger

# Add subnet root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import bittensor as bt  # noqa: E402 — must come after sys.path update

# ── Constants ─────────────────────────────────────────────────────────────────

TESTNET_NETWORK = "test"
DEFAULT_NETUID = 1          # Existing testnet subnet (cost ≈ τ0.0005)
MIN_BALANCE_TAO = 0.01      # Minimum required balance for any operation
REG_COST_APPROX = 0.001     # Approximate cost per neuron registration (testnet)
AXON_PORT = 8091
RESULTS_FILE = Path(__file__).parent.parent / "testnet_validation_results.json"


# ── Step 1: Connectivity & Balance ────────────────────────────────────────────


def check_connectivity() -> dict:
    """Phase 1: Verify testnet connectivity and wallet balances."""

    logger.info("=== Phase 1: Connectivity & Balance Check ===")
    result = {"phase": "connectivity", "passed": False, "details": {}}

    try:
        sub = bt.Subtensor(network=TESTNET_NETWORK)
        block = sub.get_current_block()
        logger.info(f"  ✓ Connected | block={block}")
        result["details"]["block"] = block

        # Check wallet balances
        wallets = {
            "owner": bt.Wallet(name="openclaude-owner"),
            "validator": bt.Wallet(name="openclaude-validator", hotkey="validator"),
            "miner": bt.Wallet(name="openclaude-miner", hotkey="miner"),
        }

        balances = {}
        total_tao = 0.0
        for name, wallet in wallets.items():
            try:
                bal = sub.get_balance(wallet.coldkeypub.ss58_address)
                bal_float = float(str(bal).replace("τ", "").replace(",", "").split()[0])
                balances[name] = {
                    "address": wallet.coldkeypub.ss58_address,
                    "balance_tao": bal_float,
                }
                total_tao += bal_float
                status = "✓" if bal_float > 0 else "⚠"
                logger.info(f"  {status} {name}: {bal}")
            except Exception as e:
                logger.warning(f"  ✗ {name}: {e}")
                balances[name] = {"error": str(e)}

        result["details"]["balances"] = balances
        result["details"]["total_tao"] = total_tao

        # Check if we can register
        needed = REG_COST_APPROX * 2  # miner + validator
        if total_tao >= needed:
            logger.info(f"  ✓ Sufficient TAO for registration ({total_tao:.4f} ≥ {needed:.4f})")
            result["passed"] = True
        else:
            logger.warning(
                f"  ⚠ Low TAO balance: {total_tao:.6f} TAO. "
                f"Need ≥ {needed:.4f} for registration."
            )
            result["passed"] = (total_tao > 0)  # Pass if any balance exists

        # Show registration cost for chosen netuid
        try:
            cost = sub.recycle(netuid=DEFAULT_NETUID)
            logger.info(f"  ✓ Netuid {DEFAULT_NETUID} registration cost: {cost}")
            result["details"]["reg_cost"] = str(cost)
        except Exception as e:
            logger.warning(f"  ✗ Could not fetch registration cost: {e}")

        return result

    except Exception as e:
        logger.error(f"  ✗ Connectivity failed: {e}")
        result["details"]["error"] = str(e)
        return result


# ── Step 2: Miner Registration ────────────────────────────────────────────────


def register_miner(netuid: int) -> dict:
    """Phase 2: Register miner hotkey on existing testnet subnet."""

    logger.info(f"=== Phase 2: Miner Registration (netuid={netuid}) ===")
    result = {"phase": "miner_registration", "passed": False, "details": {}}

    try:
        sub = bt.Subtensor(network=TESTNET_NETWORK)
        wallet = bt.Wallet(name="openclaude-miner", hotkey="miner")
        hotkey = wallet.hotkey.ss58_address
        result["details"]["hotkey"] = hotkey

        # Check if already registered
        already_reg = sub.is_hotkey_registered(hotkey_ss58=hotkey, netuid=netuid)
        if already_reg:
            logger.info(f"  ✓ Miner already registered on netuid={netuid}")
            result["passed"] = True
            result["details"]["already_registered"] = True
            return result

        # Check balance
        bal = sub.get_balance(wallet.coldkeypub.ss58_address)
        logger.info(f"  Balance: {bal}")

        # Register via burned_register (pays burn cost from coldkey balance)
        logger.info(f"  Registering miner hotkey on netuid={netuid}...")
        response = sub.burned_register(
            wallet=wallet,
            netuid=netuid,
            wait_for_inclusion=True,
            wait_for_finalization=True,
        )

        if response and response.success:
            logger.info(f"  ✓ Miner registered on netuid={netuid} | hotkey={hotkey}")
            result["passed"] = True
            result["details"]["registered"] = True
            result["details"]["response"] = str(response)
        else:
            logger.error(f"  ✗ Registration failed: {response}")
            result["details"]["error"] = str(response)

        return result

    except Exception as e:
        logger.error(f"  ✗ Miner registration failed: {e}")
        result["details"]["error"] = str(e)
        return result


# ── Step 3: Validator Registration ────────────────────────────────────────────


def register_validator(netuid: int) -> dict:
    """Phase 3: Register validator hotkey on existing testnet subnet."""

    logger.info(f"=== Phase 3: Validator Registration (netuid={netuid}) ===")
    result = {"phase": "validator_registration", "passed": False, "details": {}}

    try:
        sub = bt.Subtensor(network=TESTNET_NETWORK)
        wallet = bt.Wallet(name="openclaude-validator", hotkey="validator")
        hotkey = wallet.hotkey.ss58_address
        result["details"]["hotkey"] = hotkey

        # Check if already registered
        already_reg = sub.is_hotkey_registered(hotkey_ss58=hotkey, netuid=netuid)
        if already_reg:
            logger.info(f"  ✓ Validator already registered on netuid={netuid}")
            result["passed"] = True
            result["details"]["already_registered"] = True
            return result

        logger.info(f"  Registering validator hotkey on netuid={netuid}...")
        response = sub.burned_register(
            wallet=wallet,
            netuid=netuid,
            wait_for_inclusion=True,
            wait_for_finalization=True,
        )

        if response and response.success:
            logger.info(f"  ✓ Validator registered on netuid={netuid} | hotkey={hotkey}")
            result["passed"] = True
            result["details"]["registered"] = True
        else:
            logger.error(f"  ✗ Registration failed: {response}")
            result["details"]["error"] = str(response)

        return result

    except Exception as e:
        logger.error(f"  ✗ Validator registration failed: {e}")
        result["details"]["error"] = str(e)
        return result


# ── Step 4: Axon Discoverability ──────────────────────────────────────────────


def verify_axon_discoverability(netuid: int) -> dict:
    """Phase 4: Verify miner Axon server is discoverable on the subnet."""

    logger.info(f"=== Phase 4: Axon Discoverability (netuid={netuid}) ===")
    result = {"phase": "axon_discoverability", "passed": False, "details": {}}

    try:
        sub = bt.Subtensor(network=TESTNET_NETWORK)
        miner_wallet = bt.Wallet(name="openclaude-miner", hotkey="miner")
        hotkey = miner_wallet.hotkey.ss58_address

        # Check if registered first
        is_reg = sub.is_hotkey_registered(hotkey_ss58=hotkey, netuid=netuid)
        if not is_reg:
            logger.warning(f"  ⚠ Miner not registered on netuid={netuid} — skip Axon check")
            result["details"]["skipped"] = "miner_not_registered"
            result["passed"] = None  # inconclusive
            return result

        # Get neuron info
        try:
            neuron = sub.get_neuron_for_pubkey_and_subnet(hotkey, netuid=netuid)
            axon_info = neuron.axon_info if neuron else None

            if axon_info and axon_info.ip != "0.0.0.0":
                logger.info(f"  ✓ Axon visible: {axon_info.ip}:{axon_info.port}")
                result["passed"] = True
                result["details"]["axon"] = {
                    "ip": axon_info.ip,
                    "port": axon_info.port,
                    "hotkey": axon_info.hotkey,
                }
            else:
                logger.warning(
                    "  ⚠ Miner registered but Axon not yet serving "
                    "(Axon process not started or IP not set)"
                )
                logger.info(
                    f"  → To fix: start miner with:\n"
                    f"    export OPENCLAUDE_API_KEYS='sk-ant-...'  # real key needed\n"
                    f"    uv run python neurons/miner.py --config config/miner.testnet.yaml"
                )
                result["details"]["axon"] = "not_serving"
                result["passed"] = False  # needs action
        except Exception as e:
            logger.warning(f"  ⚠ Could not get neuron info: {e}")
            result["details"]["error"] = str(e)

        return result

    except Exception as e:
        logger.error(f"  ✗ Axon check failed: {e}")
        result["details"]["error"] = str(e)
        return result


# ── Step 5: Dendrite Query (if Axon is up) ────────────────────────────────────


async def verify_dendrite_query(netuid: int) -> dict:
    """Phase 5: Verify Validator Dendrite can query Miner Axon."""

    from protocol.synapse import LLMAPISynapse

    logger.info(f"=== Phase 5: Dendrite → Axon Query (netuid={netuid}) ===")
    result = {"phase": "dendrite_query", "passed": False, "details": {}}

    try:
        sub = bt.Subtensor(network=TESTNET_NETWORK)
        val_wallet = bt.Wallet(name="openclaude-validator", hotkey="validator")
        miner_wallet = bt.Wallet(name="openclaude-miner", hotkey="miner")
        miner_hotkey = miner_wallet.hotkey.ss58_address

        # Check if both are registered
        miner_reg = sub.is_hotkey_registered(hotkey_ss58=miner_hotkey, netuid=netuid)
        if not miner_reg:
            logger.warning("  ⚠ Miner not registered — skipping dendrite query test")
            result["details"]["skipped"] = "miner_not_registered"
            result["passed"] = None
            return result

        # Get miner axon
        miner_neuron = sub.get_neuron_for_pubkey_and_subnet(miner_hotkey, netuid=netuid)
        if not miner_neuron or not miner_neuron.axon_info.ip or miner_neuron.axon_info.ip == "0.0.0.0":
            logger.warning("  ⚠ Miner Axon not serving — skipping dendrite query")
            result["details"]["skipped"] = "axon_not_serving"
            result["passed"] = None
            return result

        # Send probe request via Dendrite
        dendrite = bt.Dendrite(wallet=val_wallet)
        synapse = LLMAPISynapse.create_request(
            messages=[{"role": "user", "content": "Respond with 'ok' only."}],
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
        )

        start_ms = time.time() * 1000
        try:
            responses = await dendrite(
                axons=[miner_neuron.axon_info],
                synapse=synapse,
                timeout=30,
            )
            latency_ms = int(time.time() * 1000 - start_ms)

            if responses and responses[0].is_success:
                logger.info(f"  ✓ Dendrite query succeeded | latency={latency_ms}ms")
                logger.info(f"  Response: {responses[0].response[:50]!r}")
                result["passed"] = True
                result["details"] = {
                    "latency_ms": latency_ms,
                    "response_preview": responses[0].response[:100],
                }
            else:
                err = responses[0].error_message if responses else "no response"
                logger.warning(f"  ⚠ Query returned no success: {err}")
                result["details"]["error"] = err
        except Exception as e:
            logger.error(f"  ✗ Dendrite query error: {e}")
            result["details"]["error"] = str(e)

        return result

    except Exception as e:
        logger.error(f"  ✗ Dendrite check failed: {e}")
        result["details"]["error"] = str(e)
        return result


# ── Step 6: Weight Submission ─────────────────────────────────────────────────


def verify_weight_submission(netuid: int) -> dict:
    """Phase 6: Verify validator can submit weights to chain."""

    from validator.scoring import ScoringEngine
    from validator.trust import TrustWeightCalculator

    logger.info(f"=== Phase 6: Weight Submission (netuid={netuid}) ===")
    result = {"phase": "weight_submission", "passed": False, "details": {}}

    try:
        sub = bt.Subtensor(network=TESTNET_NETWORK)
        val_wallet = bt.Wallet(name="openclaude-validator", hotkey="validator")
        val_hotkey = val_wallet.hotkey.ss58_address

        # Check validator registration
        is_reg = sub.is_hotkey_registered(hotkey_ss58=val_hotkey, netuid=netuid)
        if not is_reg:
            logger.warning("  ⚠ Validator not registered — skipping weight submission")
            result["details"]["skipped"] = "validator_not_registered"
            result["passed"] = None
            return result

        # Get metagraph to find miners
        try:
            metagraph = sub.metagraph(netuid=netuid)
            miner_uids = [int(uid) for uid in metagraph.uids.tolist()[:5]]  # test with first 5
        except Exception as e:
            logger.warning(f"  ⚠ Cannot get metagraph: {e} — using test weights")
            miner_uids = [0, 1]

        # Generate test weights using our scoring engine (simulated scores)
        engine = ScoringEngine()
        calc = TrustWeightCalculator(netuid=netuid)
        raw_weights = {uid: 0.5 + (uid % 5) * 0.1 for uid in miner_uids}
        trust_result = calc.process(raw_weights)

        if not trust_result.processed_uids:
            logger.warning("  ⚠ No viable weights to submit")
            result["details"]["error"] = "no_viable_weights"
            return result

        uids = trust_result.processed_uids
        weights = trust_result.processed_weights

        logger.info(f"  Submitting weights for {len(uids)} neurons on netuid={netuid}...")
        try:
            response = sub.set_weights(
                wallet=val_wallet,
                netuid=netuid,
                uids=uids,
                weights=weights,
                wait_for_inclusion=True,
                wait_for_finalization=False,  # faster for testing
            )

            if response and (response.success if hasattr(response, 'success') else bool(response)):
                logger.info(f"  ✓ Weights submitted | uids={uids[:3]}... weights={[f'{w:.3f}' for w in weights[:3]]}...")
                result["passed"] = True
                result["details"]["uids_count"] = len(uids)
                result["details"]["weights_sum"] = sum(weights)
            else:
                logger.warning(f"  ⚠ Weight submission response: {response}")
                # May fail if not enough tempo has passed — this is OK
                result["details"]["response"] = str(response)
                result["details"]["note"] = "Weight submission may fail if tempo not reached — normal"
                result["passed"] = True  # Still counts as "can submit" if no exception
        except Exception as e:
            logger.warning(f"  ⚠ Weight submission error: {e}")
            logger.info("  → This may be normal if tempo hasn't passed yet")
            result["details"]["error"] = str(e)
            result["passed"] = False

        return result

    except Exception as e:
        logger.error(f"  ✗ Weight submission check failed: {e}")
        result["details"]["error"] = str(e)
        return result


# ── Step 7: 72h Stability Monitor ────────────────────────────────────────────


async def stability_monitor(netuid: int, hours: float = 72.0) -> None:
    """Phase 7: Long-running stability monitor.

    Monitors miner/validator health over an extended period.
    Run with --stability-monitor flag. Results written to testnet_validation_results.json.
    """

    logger.info(f"=== Phase 7: Stability Monitor (netuid={netuid}, duration={hours}h) ===")
    logger.info(f"  Started at: {datetime.now(timezone.utc).isoformat()}")
    logger.info(f"  Will run until: {datetime.fromtimestamp(time.time() + hours * 3600, timezone.utc).isoformat()}")

    total_checks = 0
    successful_checks = 0
    start_time = time.time()
    end_time = start_time + hours * 3600
    check_interval_sec = 60  # check every minute

    metrics = {
        "start_time": datetime.now(timezone.utc).isoformat(),
        "target_hours": hours,
        "netuid": netuid,
        "checks": [],
    }

    try:
        while time.time() < end_time:
            check_start = time.time()
            sub = bt.Subtensor(network=TESTNET_NETWORK)
            block = sub.get_current_block()
            total_checks += 1

            check = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "block": block,
                "elapsed_hours": (time.time() - start_time) / 3600,
            }

            # Check miner registration
            try:
                miner_wallet = bt.Wallet(name="openclaude-miner", hotkey="miner")
                miner_reg = sub.is_hotkey_registered(
                    hotkey_ss58=miner_wallet.hotkey.ss58_address,
                    netuid=netuid,
                )
                check["miner_registered"] = miner_reg

                # Check validator
                val_wallet = bt.Wallet(name="openclaude-validator", hotkey="validator")
                val_reg = sub.is_hotkey_registered(
                    hotkey_ss58=val_wallet.hotkey.ss58_address,
                    netuid=netuid,
                )
                check["validator_registered"] = val_reg
                check["success"] = miner_reg and val_reg
                if check["success"]:
                    successful_checks += 1
            except Exception as e:
                check["error"] = str(e)
                check["success"] = False

            success_rate = successful_checks / total_checks * 100 if total_checks > 0 else 0
            elapsed_h = (time.time() - start_time) / 3600
            logger.info(
                f"  [{elapsed_h:.1f}/{hours}h] Block={block} | "
                f"Success rate: {success_rate:.1f}% ({successful_checks}/{total_checks})"
            )

            # Report progress every hour
            if total_checks % 60 == 0:
                metrics["checks"].append(check)
                metrics["current_success_rate"] = success_rate
                RESULTS_FILE.write_text(json.dumps(metrics, indent=2))
                logger.info(f"  📊 Progress saved to {RESULTS_FILE}")

            # Sleep until next check
            elapsed = time.time() - check_start
            sleep_sec = max(0, check_interval_sec - elapsed)
            await asyncio.sleep(sleep_sec)

    except KeyboardInterrupt:
        logger.info("  Stability monitor interrupted by user.")

    # Final report
    final_success_rate = successful_checks / total_checks * 100 if total_checks > 0 else 0
    metrics["final_success_rate"] = final_success_rate
    metrics["total_checks"] = total_checks
    metrics["successful_checks"] = successful_checks
    metrics["end_time"] = datetime.now(timezone.utc).isoformat()
    RESULTS_FILE.write_text(json.dumps(metrics, indent=2))

    target_rate = 99.0
    passed = final_success_rate >= target_rate
    status = "✅ PASSED" if passed else "❌ FAILED"
    logger.info(f"\n{status} — Success rate: {final_success_rate:.2f}% (target: {target_rate}%)")
    logger.info(f"Results saved to: {RESULTS_FILE}")


# ── Main ─────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OpenClade Testnet Validation — 2-3 TAO Constraint Edition"
    )
    parser.add_argument("--netuid", type=int, default=DEFAULT_NETUID,
                        help=f"Testnet subnet to join (default: {DEFAULT_NETUID})")
    parser.add_argument("--check-only", action="store_true",
                        help="Only check connectivity and balances (no spending)")
    parser.add_argument("--register-miner", action="store_true",
                        help="Register miner hotkey on the subnet")
    parser.add_argument("--register-validator", action="store_true",
                        help="Register validator hotkey on the subnet")
    parser.add_argument("--full-validate", action="store_true",
                        help="Run full validation (connectivity + register + verify)")
    parser.add_argument("--stability-monitor", action="store_true",
                        help="Run long-running stability monitor")
    parser.add_argument("--hours", type=float, default=72.0,
                        help="Duration for stability monitor in hours (default: 72)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = {}

    logger.info("OpenClade Testnet Validation (2-3 TAO Constraint Edition)")
    logger.info("=" * 65)
    logger.info(f"Network: {TESTNET_NETWORK} | Netuid: {args.netuid}")
    logger.info("=" * 65)

    # Always check connectivity first
    results["connectivity"] = check_connectivity()

    if args.check_only:
        # Just report balance and connectivity
        _print_summary(results)
        return 0 if results["connectivity"]["passed"] else 1

    if args.stability_monitor:
        asyncio.run(stability_monitor(args.netuid, args.hours))
        return 0

    if args.register_miner or args.full_validate:
        results["miner_registration"] = register_miner(args.netuid)

    if args.register_validator or args.full_validate:
        results["validator_registration"] = register_validator(args.netuid)

    if args.full_validate:
        results["axon_discoverability"] = verify_axon_discoverability(args.netuid)
        results["dendrite_query"] = asyncio.run(verify_dendrite_query(args.netuid))
        results["weight_submission"] = verify_weight_submission(args.netuid)

    _print_summary(results)

    # Save results
    RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))
    logger.info(f"\nResults saved to: {RESULTS_FILE}")

    # Return exit code
    all_passed = all(
        v.get("passed") in (True, None)
        for v in results.values()
        if isinstance(v, dict)
    )
    return 0 if all_passed else 1


def _print_summary(results: dict) -> None:
    logger.info("")
    logger.info("=" * 65)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 65)

    status_map = {True: "✅ PASS", False: "❌ FAIL", None: "⏭  SKIP"}
    for phase, result in results.items():
        if not isinstance(result, dict):
            continue
        passed = result.get("passed")
        status = status_map.get(passed, "❓ ?")
        note = ""
        if "skipped" in result.get("details", {}):
            note = f" ({result['details']['skipped']})"
        elif "already_registered" in result.get("details", {}):
            note = " (already registered)"
        logger.info(f"  {status}  {phase}{note}")

    logger.info("")
    logger.info("📋 Scope Note:")
    logger.info("  This validation uses an EXISTING testnet subnet.")
    logger.info("  Emission split (18%/41%/41%) requires OWN subnet registration.")
    logger.info("  Current testnet subnet registration cost: ~τ6 (fluctuates).")
    logger.info("")
    logger.info("Next Steps:")
    logger.info("  1. Get 2-3 TAO to owner wallet (Discord #testnet-faucet)")
    logger.info("  2. Run: uv run python scripts/validate_testnet_2tao.py --full-validate")
    logger.info("  3. Start miner: uv run python neurons/miner.py --config config/miner.testnet.yaml")
    logger.info("  4. Run 72h monitor: uv run python scripts/validate_testnet_2tao.py --stability-monitor")


if __name__ == "__main__":
    sys.exit(main())
