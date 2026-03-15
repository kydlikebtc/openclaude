#!/usr/bin/env python3
"""
OpenClade Subnet — 本地端到端链路验证脚本.

在不需要真实 TAO 或网络连接的情况下，验证以下完整链路：
  用户请求 → Synapse 协议 → Miner 评分逻辑 → Validator 权重计算 → Yuma 对齐

用途:
  - CI/CD 环境中的快速验证
  - 本地开发调试
  - 在获得 testnet TAO 之前验证代码逻辑

运行:
  uv run python scripts/validate_e2e_local.py
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, List
from unittest.mock import MagicMock, patch

from loguru import logger

# Add subnet root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from protocol.synapse import LLMAPISynapse
from validator.probe import ProbeTaskGenerator
from validator.scoring import MinerScore, ScoringEngine
from validator.trust import TrustWeightCalculator


def build_mock_response(
    uid: int,
    latency_ms: int,
    quality_level: str = "good",
) -> LLMAPISynapse:
    """Create a mock miner response for testing scoring logic."""
    synapse = LLMAPISynapse.create_request(
        messages=[{"role": "user", "content": "What is 2+2?"}],
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
    )
    synapse.latency_ms = latency_ms
    synapse.tokens_used = 50
    synapse.finish_reason = "end_turn"
    synapse.miner_model_used = "claude-haiku-4-5-20251001"

    if quality_level == "good":
        synapse.response = "2+2 equals 4."
        synapse.compute_response_hash()
    elif quality_level == "slow":
        synapse.response = "2+2 equals 4."
        synapse.latency_ms = 4500  # Over P95 target
        synapse.compute_response_hash()
    elif quality_level == "empty":
        synapse.response = ""
        synapse.error_message = "API key exhausted"
    elif quality_level == "wrong_model":
        synapse.response = "2+2 equals 4."
        synapse.miner_model_used = "gpt-4"  # Should be penalized
        synapse.compute_response_hash()

    return synapse


def test_synapse_protocol() -> bool:
    """Test LLMAPISynapse request/response protocol."""
    logger.info("=== Testing Synapse Protocol ===")

    # Create request
    req = LLMAPISynapse.create_request(
        messages=[{"role": "user", "content": "Hello"}],
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        temperature=0.7,
    )
    assert req.request_id, "request_id must be set"
    assert req.model == "claude-haiku-4-5-20251001"
    assert req.max_tokens == 256
    logger.info(f"  ✓ Synapse created | request_id={req.request_id[:8]}...")

    # Simulate response
    req.response = "Hello! I'm Claude."
    req.tokens_used = 25
    req.latency_ms = 450
    req.finish_reason = "end_turn"
    req.miner_model_used = "claude-haiku-4-5-20251001"
    req.compute_response_hash()
    assert req.response_hash, "response_hash must be computed"
    logger.info(f"  ✓ Response hash computed: {req.response_hash[:16]}...")

    # Verify hash integrity
    original_hash = req.response_hash
    req.response = "Tampered response"
    req.compute_response_hash()
    assert req.response_hash != original_hash, "Hash must change with tampered response"
    logger.info("  ✓ Response hash integrity verified (tamper detection works)")

    return True


def test_probe_generator() -> bool:
    """Test ProbeTaskGenerator sampling logic."""
    logger.info("=== Testing Probe Generator ===")

    gen = ProbeTaskGenerator()

    # Test sampling
    tasks = gen.sample(5)
    assert len(tasks) > 0, "Must generate at least 1 probe task"
    for task in tasks:
        assert task.model in ["claude-haiku-4-5-20251001", "claude-sonnet-4-6"], \
            f"Unknown model: {task.model}"
        assert len(task.messages) > 0, "Task must have messages"
    logger.info(f"  ✓ Generated {len(tasks)} probe tasks for 5 miners")

    # Test miner selection
    uids = list(range(20))
    selected = gen.miners_to_probe(uids, len(uids))
    assert len(selected) > 0, "Must select at least 1 miner"
    assert len(selected) <= len(uids), "Cannot probe more miners than exist"
    logger.info(f"  ✓ Selected {len(selected)}/{len(uids)} miners to probe")

    # Test interval scaling: more miners → probe more frequently → shorter interval
    interval_few = gen.probe_interval_sec(1)     # < 20 miners: 5 min
    interval_many = gen.probe_interval_sec(50)   # 20-100 miners: 2 min
    assert interval_few >= interval_many, \
        "Interval should be shorter with more miners (probe more frequently)"
    logger.info(f"  ✓ Probe interval: 1 miner={interval_few}s, 50 miners={interval_many}s (more miners → faster probing)")

    return True


def test_scoring_engine() -> bool:
    """Test ScoringEngine multi-dimensional scoring."""
    logger.info("=== Testing Scoring Engine ===")

    engine = ScoringEngine()
    gen = ProbeTaskGenerator()
    probe = gen.sample(1)[0]

    # Create diverse responses
    uid_responses = {
        0: build_mock_response(0, latency_ms=300, quality_level="good"),
        1: build_mock_response(1, latency_ms=2000, quality_level="slow"),
        2: build_mock_response(2, latency_ms=500, quality_level="empty"),
        3: build_mock_response(3, latency_ms=400, quality_level="wrong_model"),
    }

    scores: Dict[int, MinerScore] = engine.score_batch(uid_responses, probe)

    assert 0 in scores, "UID 0 must have a score"
    assert 2 in scores, "UID 2 must have a score (even with error)"

    # Good miner should score better than slow/empty miners
    score_good = scores[0].smooth_score
    score_slow = scores.get(1, MinerScore(uid=1)).smooth_score
    score_empty = scores.get(2, MinerScore(uid=2)).smooth_score

    logger.info(f"  Scores: good={score_good:.3f}, slow={score_slow:.3f}, empty={score_empty:.3f}")
    assert score_good > score_empty, \
        f"Good miner ({score_good:.3f}) should score > empty ({score_empty:.3f})"
    logger.info("  ✓ Good miner scores better than empty/errored miner")

    # Test weight conversion
    raw_weights = engine.scores_to_weights(scores, list(uid_responses.keys()))
    assert len(raw_weights) > 0, "Must produce weights"
    logger.info(f"  ✓ Weights computed for {len(raw_weights)} miners")

    return True


def test_trust_weight_calculator() -> bool:
    """Test TrustWeightCalculator Yuma-aligned weight processing."""
    logger.info("=== Testing Trust Weight Calculator ===")

    calc = TrustWeightCalculator(netuid=1, exclude_quantile=0.1, max_weight_limit=0.8)

    # Simulate raw weights from scoring
    raw_weights = {0: 0.85, 1: 0.70, 2: 0.60, 3: 0.10, 4: 0.05}

    # Local processing (no SDK required)
    result = calc.process(raw_weights)

    assert len(result.processed_uids) > 0, "Must keep at least 1 miner"
    weight_sum = sum(result.processed_weights)
    assert abs(weight_sum - 1.0) < 0.01, f"Weights must sum to 1.0, got {weight_sum:.4f}"
    logger.info(f"  ✓ {len(result.processed_uids)}/{result.total_miners} miners kept")
    logger.info(f"  ✓ Weights sum to {weight_sum:.4f}")

    # Verify max weight cap
    max_w = max(result.processed_weights)
    assert max_w <= 0.80 + 0.01, f"Max weight {max_w:.3f} exceeds cap 0.80"
    logger.info(f"  ✓ Max weight {max_w:.3f} ≤ 0.80 cap")

    # Viability check
    viable, reason = calc.is_submission_viable(result)
    assert viable, f"Submission should be viable: {reason}"
    logger.info("  ✓ Weight submission is viable")

    return True


async def test_full_epoch_cycle() -> bool:
    """Simulate a full Validator epoch: probe → score → weights."""
    logger.info("=== Testing Full Epoch Cycle (Mock) ===")

    gen = ProbeTaskGenerator()
    engine = ScoringEngine()
    calc = TrustWeightCalculator(netuid=1)

    miner_uids = [0, 1, 2, 3, 4]
    probe_tasks = gen.sample(len(miner_uids))

    epoch_scores: Dict[int, MinerScore] = {}

    for probe in probe_tasks:
        # Simulate Dendrite calling miners (mock responses)
        uid_responses = {
            uid: build_mock_response(
                uid=uid,
                latency_ms=300 + uid * 100,
                quality_level="good" if uid < 4 else "empty",
            )
            for uid in miner_uids
        }

        task_scores = engine.score_batch(uid_responses, probe)

        for uid, score in task_scores.items():
            if uid not in epoch_scores:
                epoch_scores[uid] = score
            else:
                prev = epoch_scores[uid]
                prev.smooth_score = (prev.smooth_score + score.smooth_score) / 2
                epoch_scores[uid] = prev

    raw_weights = engine.scores_to_weights(epoch_scores, miner_uids)
    trust_result = calc.process(raw_weights)
    viable, reason = calc.is_submission_viable(trust_result)

    logger.info(f"  Epoch summary:")
    logger.info(f"    Miners probed: {len(miner_uids)}")
    logger.info(f"    Probe tasks: {len(probe_tasks)}")
    logger.info(f"    Scored miners: {len(epoch_scores)}")
    logger.info(f"    Weights kept: {len(trust_result.processed_uids)}/{trust_result.total_miners}")
    logger.info(f"    Submission viable: {viable}")

    if viable:
        logger.info("  ✓ Full epoch cycle completed successfully")
        logger.info(f"  ✓ Ready for on-chain weight submission via subtensor.set_weights()")
    else:
        logger.warning(f"  ⚠ Submission not viable: {reason}")

    return viable


async def test_testnet_connectivity() -> bool:
    """Verify connectivity to Bittensor testnet."""
    logger.info("=== Testing Testnet Connectivity ===")

    try:
        import bittensor as bt  # type: ignore
        subtensor = bt.Subtensor(network="test")
        block = subtensor.get_current_block()
        logger.info(f"  ✓ Connected to Bittensor testnet | block={block}")

        # Check wallet addresses
        wallets = {
            "owner": bt.Wallet(name="openclaude-owner"),
            "validator": bt.Wallet(name="openclaude-validator", hotkey="validator"),
            "miner": bt.Wallet(name="openclaude-miner", hotkey="miner"),
        }
        for name, wallet in wallets.items():
            balance = subtensor.get_balance(wallet.coldkeypub.ss58_address)
            logger.info(f"  {name}: {wallet.coldkeypub.ss58_address} | balance={balance}")

        return True

    except Exception as e:
        logger.error(f"  ✗ Testnet connectivity failed: {e}")
        return False


def main() -> int:
    """Run all validation tests."""
    logger.info("OpenClade Subnet — Local E2E Validation")
    logger.info("=" * 60)

    results = {}

    # Run sync tests
    results["synapse_protocol"] = test_synapse_protocol()
    results["probe_generator"] = test_probe_generator()
    results["scoring_engine"] = test_scoring_engine()
    results["trust_weight_calculator"] = test_trust_weight_calculator()

    # Run async tests
    results["full_epoch_cycle"] = asyncio.run(test_full_epoch_cycle())
    results["testnet_connectivity"] = asyncio.run(test_testnet_connectivity())

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("VALIDATION RESULTS:")
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"  {status}  {test_name}")
        if not passed:
            all_passed = False

    logger.info("")
    if all_passed:
        logger.info("✓ All local validations PASSED")
        logger.info("")
        logger.info("Next steps for real Testnet deployment:")
        logger.info("  1. Get testnet TAO from Discord faucet (#testnet-faucet)")
        logger.info("     - Target wallet: 5HgLWLo5BHkQVjRpp7M27p8YCoupdQeYRqz8gUKRqsHtMEkC")
        logger.info("     - Need ~100 TAO for subnet registration")
        logger.info("  2. Register subnet:")
        logger.info("     uv run python scripts/register_subnet.py \\")
        logger.info("       --wallet.name openclaude-owner \\")
        logger.info("       --wallet.hotkey default \\")
        logger.info("       --network test \\")
        logger.info("       --register-subnet --verify")
        logger.info("  3. Register validator (use netuid from step 2):")
        logger.info("     uv run python neurons/validator.py \\")
        logger.info("       --wallet.name openclaude-validator \\")
        logger.info("       --wallet.hotkey validator \\")
        logger.info("       --subtensor.network test \\")
        logger.info("       --netuid <NETUID>")
        logger.info("  4. Register miner:")
        logger.info("     export OPENCLAUDE_API_KEYS='sk-ant-api03-...'")
        logger.info("     uv run python neurons/miner.py \\")
        logger.info("       --config config/miner.testnet.yaml")
        return 0
    else:
        logger.error("✗ Some validations FAILED — fix before testnet deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())
