"""
Phase 6 Performance Benchmark Tests
=====================================
验收标准：
  - P95 延迟 < 5秒（含 Anthropic API 调用）

测试分层：
  1. 路由层性能：矿工选择+认证耗时（应 < 100ms）
  2. API 端点吞吐量：并发请求处理能力
  3. 端到端延迟基准（含 mock Anthropic）

注意：真实 Testnet 性能测试在 KYD-15/KYD-16 完成后执行。
本测试验证路由引擎和 API 层不引入额外高延迟。
"""

import asyncio
import statistics
import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

# 性能基准阈值
MAX_P95_LATENCY_MS = 5000   # 5秒（含 Anthropic API）
MAX_ROUTING_LATENCY_MS = 500  # 路由+认证 < 500ms
MAX_CONCURRENT_REQUESTS = 10   # 并发请求数


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
async def perf_setup(client: AsyncClient, mock_redis: AsyncMock):
    """性能测试基础环境：用户、API Key、矿工。"""
    email = f"perf_{uuid.uuid4().hex[:8]}@test.com"
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "PerfPass123!"},
    )
    token = reg.json()["access_token"]

    await client.post(
        "/api/v1/billing/recharge",
        json={"amount": "100.00"},
        headers={"Authorization": f"Bearer {token}"},
    )

    key_resp = await client.post(
        "/api/v1/api-keys",
        json={"name": "perf test key"},
        headers={"Authorization": f"Bearer {token}"},
    )
    oc_key = key_resp.json()["key"]

    # 注册 3 个矿工（模拟真实池）
    miners = []
    for i in range(3):
        hotkey = f"5perf_miner_{uuid.uuid4().hex[:10]}"
        resp = await client.post(
            "/api/v1/miners/register",
            json={
                "hotkey": hotkey,
                "coldkey": f"5cold_{hotkey[:8]}",
                "name": f"PerfMiner{i}",
                "api_key": f"sk-ant-perf-{i}",
                "supported_models": ["claude-haiku-4-5-20251001"],
            },
        )
        miners.append(resp.json())

    return {"token": token, "oc_key": oc_key, "miners": miners}


def _make_mock_anthropic_response(latency_ms: int = 100) -> MagicMock:
    """创建模拟 Anthropic API 响应（含可配置延迟）。"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": f"msg_{uuid.uuid4().hex[:8]}",
        "type": "message",
        "role": "assistant",
        "model": "claude-haiku-4-5-20251001",
        "content": [{"type": "text", "text": "Performance test response"}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 10, "output_tokens": 20},
    }
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ─── Routing Performance Tests ────────────────────────────────────────────────

class TestRoutingPerformance:
    """路由引擎性能测试。"""

    @pytest.mark.asyncio
    async def test_single_request_routing_latency(
        self, client: AsyncClient, perf_setup: dict
    ) -> None:
        """单次请求端到端延迟（含 mock Anthropic 但不含真实 API 网络）应 < 500ms。"""
        oc_key = perf_setup["oc_key"]

        mock_resp = _make_mock_anthropic_response()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_resp)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_http

            start_time = time.monotonic()
            resp = await client.post(
                "/v1/messages",
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": "Latency test"}],
                },
                headers={"x-api-key": oc_key},
            )
            elapsed_ms = (time.monotonic() - start_time) * 1000

        assert resp.status_code == 200
        assert elapsed_ms < MAX_ROUTING_LATENCY_MS, (
            f"路由延迟 {elapsed_ms:.1f}ms 超过阈值 {MAX_ROUTING_LATENCY_MS}ms"
        )

    @pytest.mark.asyncio
    async def test_p95_latency_over_20_requests(
        self, client: AsyncClient, perf_setup: dict
    ) -> None:
        """20 次连续请求的 P95 延迟（mock Anthropic）应 < 500ms。"""
        oc_key = perf_setup["oc_key"]
        latencies: list[float] = []

        mock_resp = _make_mock_anthropic_response()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_resp)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_http

            for i in range(20):
                start = time.monotonic()
                resp = await client.post(
                    "/v1/messages",
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 50,
                        "messages": [{"role": "user", "content": f"P95 test {i}"}],
                    },
                    headers={"x-api-key": oc_key},
                )
                elapsed_ms = (time.monotonic() - start) * 1000
                if resp.status_code == 200:
                    latencies.append(elapsed_ms)

        assert len(latencies) >= 18, "应至少有 18 次成功请求"
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        avg = statistics.mean(latencies)
        p99 = sorted(latencies)[int(len(latencies) * 0.99)]

        print(f"\n性能基准（mock，不含真实 Anthropic API）:")
        print(f"  平均延迟: {avg:.1f}ms")
        print(f"  P95 延迟: {p95:.1f}ms")
        print(f"  P99 延迟: {p99:.1f}ms")
        print(f"  请求数: {len(latencies)}")

        assert p95 < MAX_ROUTING_LATENCY_MS, (
            f"P95 延迟 {p95:.1f}ms 超过本地路由阈值 {MAX_ROUTING_LATENCY_MS}ms"
        )

    @pytest.mark.asyncio
    async def test_sequential_throughput(
        self, client: AsyncClient, perf_setup: dict
    ) -> None:
        """顺序吞吐量测试：10 次请求总耗时应合理（< 5s）。"""
        oc_key = perf_setup["oc_key"]
        mock_resp = _make_mock_anthropic_response()
        successes = 0
        total_start = time.monotonic()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_resp)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_http

            for i in range(10):
                resp = await client.post(
                    "/v1/messages",
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 20,
                        "messages": [{"role": "user", "content": f"Throughput {i}"}],
                    },
                    headers={"x-api-key": oc_key},
                )
                if resp.status_code == 200:
                    successes += 1

        total_ms = (time.monotonic() - total_start) * 1000
        print(f"\n顺序吞吐量: {successes}/10 成功, 总耗时 {total_ms:.1f}ms")
        print(f"平均每请求: {total_ms/max(successes,1):.1f}ms")

        assert successes >= 8, f"成功率 {successes}/10 < 80%"
        assert total_ms < 5000, f"10 次请求总耗时 {total_ms:.1f}ms > 5000ms"


# ─── Auth Performance Tests ───────────────────────────────────────────────────

class TestAuthPerformance:
    """认证性能测试。"""

    @pytest.mark.asyncio
    async def test_jwt_auth_endpoint_latency(self, client: AsyncClient) -> None:
        """JWT 认证端点延迟应 < 100ms。"""
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": f"auth_perf_{uuid.uuid4().hex[:8]}@test.com", "password": "Pass123!"},
        )
        token = reg.json()["access_token"]

        latencies = []
        for _ in range(10):
            start = time.monotonic()
            await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            latencies.append((time.monotonic() - start) * 1000)

        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        assert p95 < 100, f"认证端点 P95 延迟 {p95:.1f}ms 超过 100ms 阈值"

    @pytest.mark.asyncio
    async def test_api_key_auth_latency(
        self, client: AsyncClient, perf_setup: dict
    ) -> None:
        """API Key 认证（余额检查）延迟应 < 200ms。"""
        oc_key = perf_setup["oc_key"]

        latencies = []
        for _ in range(5):
            start = time.monotonic()
            # 余额不足触发 402，但仍需完成认证和余额检查
            # 单独测试余额检查路径
            await client.get(
                "/api/v1/billing/balance",
                headers={"Authorization": f"Bearer {perf_setup['token']}"},
            )
            latencies.append((time.monotonic() - start) * 1000)

        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        assert p95 < 200, f"余额查询 P95 延迟 {p95:.1f}ms 超过 200ms 阈值"


# ─── Miner Selection Performance ──────────────────────────────────────────────

class TestMinerSelectionPerformance:
    """矿工选择性能测试（Redis 查询）。"""

    @pytest.mark.asyncio
    async def test_miner_pool_query_latency(self, client: AsyncClient) -> None:
        """矿工池状态查询延迟应 < 50ms（缓存命中）。"""
        latencies = []
        for _ in range(20):
            start = time.monotonic()
            await client.get("/api/v1/miners/pool")
            latencies.append((time.monotonic() - start) * 1000)

        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        assert p95 < 50, f"矿工池查询 P95 延迟 {p95:.1f}ms 超过 50ms"

    @pytest.mark.asyncio
    async def test_miner_registration_latency(self, client: AsyncClient) -> None:
        """矿工注册（DB + Redis 写入）延迟应 < 500ms。"""
        latencies = []
        for _ in range(5):
            hotkey = f"5perf_reg_{uuid.uuid4().hex[:12]}"
            start = time.monotonic()
            await client.post(
                "/api/v1/miners/register",
                json={
                    "hotkey": hotkey,
                    "coldkey": f"5cold_{hotkey[:8]}",
                    "name": "PerfRegMiner",
                    "api_key": "sk-ant-perf-reg",
                    "supported_models": ["claude-haiku-4-5-20251001"],
                },
            )
            latencies.append((time.monotonic() - start) * 1000)

        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        assert p95 < 500, f"矿工注册 P95 延迟 {p95:.1f}ms 超过 500ms"


# ─── Testnet Performance Checklist ────────────────────────────────────────────

class TestTestnetPerformanceChecklist:
    """
    Testnet 性能验证清单（依赖 KYD-15 + KYD-16）

    以下测试在 Testnet 环境中运行（真实 Anthropic API），
    当前以占位 pass 形式存在，待 KYD-15/16 完成后启用。
    """

    @pytest.mark.skip(reason="需要 KYD-15（部署准备）和 KYD-16（Testnet 注册）完成后启用")
    @pytest.mark.asyncio
    async def test_real_anthropic_p95_under_5s(self) -> None:
        """
        [Testnet] 真实 Anthropic API 调用 P95 延迟 < 5s

        启用条件：
          1. KYD-15 完成 — 服务已部署到 Testnet
          2. KYD-16 完成 — 至少 1 个矿工已在 Testnet 注册并有效

        测试步骤：
          1. 连接 Testnet 环境 API (https://api.openclaude.io/v1)
          2. 使用真实 OpenClade API Key
          3. 发送 50 次 claude-haiku 请求
          4. 计算 P95 延迟
          5. 断言 P95 < 5000ms
        """
        pass

    @pytest.mark.skip(reason="需要 KYD-15（部署准备）和 KYD-16（Testnet 注册）完成后启用")
    @pytest.mark.asyncio
    async def test_real_miner_routing_works(self) -> None:
        """
        [Testnet] 请求成功路由到矿工并返回有效响应

        测试步骤：
          1. 发送请求到 /v1/messages
          2. 验证响应来自真实矿工（miner_id 在响应头中）
          3. 验证余额已扣减
        """
        pass

    @pytest.mark.skip(reason="需要 KYD-15（部署准备）和 KYD-16（Testnet 注册）完成后启用")
    @pytest.mark.asyncio
    async def test_real_bittensor_weight_update(self) -> None:
        """
        [Testnet] Bittensor 子网权重更新验证

        测试步骤：
          1. 矿工提交心跳后，评分更新到 Redis
          2. 验证器定期运行 set_weights
          3. 通过 Bittensor API 确认链上权重已更新
          4. 验证矿工权重与 Redis 评分一致
        """
        pass
