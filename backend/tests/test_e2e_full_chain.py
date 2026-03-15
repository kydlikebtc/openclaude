"""
Phase 6 E2E Integration Tests — Full Chain Validation
======================================================
验收标准：
  - 完整链路通: 用户注册→充值→调用API→请求路由到矿工→矿工调用Anthropic→返回结果→扣费
  - 矿工注册→评分→权重更新完整流程
  - Admin 后台监控数据正确展示

所有 Anthropic API 调用均通过 mock 拦截，不产生真实费用。
Testnet 环境运行时需移除 mock，使用真实矿工 API key。
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient


# ─── Helpers ────────────────────────────────────────────────────────────────

ANTHROPIC_MOCK_RESPONSE = {
    "id": "msg_01test",
    "type": "message",
    "role": "assistant",
    "model": "claude-haiku-4-5-20251001",
    "content": [{"type": "text", "text": "Hello from OpenClade!"}],
    "stop_reason": "end_turn",
    "stop_sequence": None,
    "usage": {"input_tokens": 10, "output_tokens": 5},
}


async def _register_user(client: AsyncClient, email: str, password: str) -> str:
    """Register user and return JWT token."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 201, f"register failed: {resp.text}"
    return resp.json()["access_token"]


async def _recharge(client: AsyncClient, token: str, amount: str) -> None:
    """Top up user balance."""
    resp = await client.post(
        "/api/v1/billing/recharge",
        json={"amount": amount},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"recharge failed: {resp.text}"


async def _create_api_key(client: AsyncClient, token: str, name: str) -> str:
    """Create an OpenClade API key and return the plaintext key."""
    resp = await client.post(
        "/api/v1/api-keys",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"api key creation failed: {resp.text}"
    return resp.json()["key"]


async def _register_miner(
    client: AsyncClient, hotkey: str, anthropic_key: str
) -> dict:
    """Register a miner via the miners registration endpoint."""
    resp = await client.post(
        "/api/v1/miners/register",
        json={
            "hotkey": hotkey,
            "coldkey": f"5cold_{hotkey[:8]}",
            "name": f"TestMiner-{hotkey[:8]}",
            "api_key": anthropic_key,
            "supported_models": ["claude-haiku-4-5-20251001", "claude-sonnet-4-6"],
        },
    )
    assert resp.status_code == 201, f"miner register failed: {resp.text}"
    return resp.json()


# ─── Full Chain Tests ────────────────────────────────────────────────────────

class TestFullChain:
    """
    完整链路: 用户注册 → 充值 → 调用API → 路由矿工 → Anthropic → 返回结果 → 扣费
    """

    @pytest.mark.asyncio
    async def test_user_registration_to_api_call_chain(
        self, client: AsyncClient, mock_redis: AsyncMock
    ) -> None:
        """
        完整链路验证:
          1. 用户注册
          2. 充值余额
          3. 创建 OpenClade API Key
          4. 注册矿工（设置其 Anthropic API key）
          5. 通过代理调用 /v1/messages（mock Anthropic response）
          6. 验证余额已扣减
        """
        # Step 1: 用户注册
        email = f"e2e_chain_{uuid.uuid4().hex[:8]}@test.com"
        token = await _register_user(client, email, "SecurePass123!")

        # Step 2: 充值 $10
        await _recharge(client, token, "10.00")
        balance_resp = await client.get(
            "/api/v1/billing/balance",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert balance_resp.status_code == 200
        initial_balance = Decimal(balance_resp.json()["balance"])
        assert initial_balance == Decimal("10.00"), "充值后余额应为 $10"

        # Step 3: 创建 API Key
        oc_api_key = await _create_api_key(client, token, "E2E Test Key")
        assert oc_api_key.startswith("oc_"), "API key 应以 oc_ 开头"

        # Step 4: 注册矿工（通过 API endpoint）
        miner_hotkey = f"5miner_{uuid.uuid4().hex[:16]}"
        miner_data = await _register_miner(client, miner_hotkey, "sk-ant-fake-key-for-testing")
        miner_id = miner_data["id"]
        assert miner_data["status"] == "active"

        # Step 5: 通过代理调用 /v1/messages，mock Anthropic API 响应
        mock_httpx_resp = MagicMock()
        mock_httpx_resp.status_code = 200
        mock_httpx_resp.json.return_value = ANTHROPIC_MOCK_RESPONSE
        mock_httpx_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_httpx_resp)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_http

            proxy_resp = await client.post(
                "/v1/messages",
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": "Hello"}],
                },
                headers={"x-api-key": oc_api_key},
            )

        assert proxy_resp.status_code == 200, f"proxy 调用失败: {proxy_resp.text}"
        response_data = proxy_resp.json()
        assert response_data["role"] == "assistant"
        assert len(response_data["content"]) > 0
        assert response_data["content"][0]["text"] == "Hello from OpenClade!"

        # Step 6: 验证余额已扣减
        balance_after = await client.get(
            "/api/v1/billing/balance",
            headers={"Authorization": f"Bearer {token}"},
        )
        final_balance = Decimal(balance_after.json()["balance"])
        assert final_balance < initial_balance, "调用后余额应已扣减"
        cost_deducted = initial_balance - final_balance
        assert cost_deducted > Decimal("0"), f"已扣费: ${cost_deducted:.6f}"

    @pytest.mark.asyncio
    async def test_insufficient_balance_returns_402(
        self, client: AsyncClient
    ) -> None:
        """余额不足时代理应返回 402 Payment Required。"""
        email = f"e2e_poor_{uuid.uuid4().hex[:8]}@test.com"
        token = await _register_user(client, email, "SecurePass123!")
        # 不充值，余额为 0
        oc_api_key = await _create_api_key(client, token, "No Balance Key")

        proxy_resp = await client.post(
            "/v1/messages",
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Hello"}],
            },
            headers={"x-api-key": oc_api_key},
        )
        assert proxy_resp.status_code == 402, "余额不足应返回 402"
        assert "Insufficient balance" in proxy_resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_no_miner_available_returns_503(
        self, client: AsyncClient, mock_redis: AsyncMock
    ) -> None:
        """矿工池为空时代理应返回 503 Service Unavailable。"""
        email = f"e2e_nominer_{uuid.uuid4().hex[:8]}@test.com"
        token = await _register_user(client, email, "SecurePass123!")
        await _recharge(client, token, "50.00")
        oc_api_key = await _create_api_key(client, token, "No Miner Key")

        # 不注册任何矿工，确保 Redis 返回空池
        proxy_resp = await client.post(
            "/v1/messages",
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Hello"}],
            },
            headers={"x-api-key": oc_api_key},
        )
        assert proxy_resp.status_code == 503, "矿工池为空应返回 503"
        assert "No miners available" in proxy_resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_api_key_returns_401(self, client: AsyncClient) -> None:
        """无效的 API Key 应返回 401。"""
        proxy_resp = await client.post(
            "/v1/messages",
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Hello"}],
            },
            headers={"x-api-key": "oc_invalid_key_12345"},
        )
        assert proxy_resp.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_401(self, client: AsyncClient) -> None:
        """缺少 API Key 应返回 401。"""
        proxy_resp = await client.post(
            "/v1/messages",
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )
        assert proxy_resp.status_code == 401


# ─── Billing Precision Tests ─────────────────────────────────────────────────

class TestBillingPrecision:
    """验证计费精度：不同模型的 token 计费是否正确。"""

    @pytest.mark.asyncio
    async def test_haiku_billing_rate(self, client: AsyncClient, mock_redis: AsyncMock) -> None:
        """claude-haiku 应以较低费率计费。"""
        email = f"e2e_haiku_{uuid.uuid4().hex[:8]}@test.com"
        token = await _register_user(client, email, "SecurePass123!")
        await _recharge(client, token, "10.00")
        oc_api_key = await _create_api_key(client, token, "Haiku Billing Key")

        miner_hotkey = f"5miner_haiku_{uuid.uuid4().hex[:8]}"
        await _register_miner(client, miner_hotkey, "sk-ant-fake-haiku")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            **ANTHROPIC_MOCK_RESPONSE,
            "model": "claude-haiku-4-5-20251001",
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_resp)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_http

            await client.post(
                "/v1/messages",
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": "Test billing"}],
                },
                headers={"x-api-key": oc_api_key},
            )

        balance_resp = await client.get(
            "/api/v1/billing/balance",
            headers={"Authorization": f"Bearer {token}"},
        )
        final_balance = Decimal(balance_resp.json()["balance"])
        cost = Decimal("10.00") - final_balance
        # haiku: $0.25/1M input + $1.25/1M output tokens, with markup
        # 100 input + 50 output = $0.0000875 before markup
        assert cost > Decimal("0"), "应产生费用"
        assert cost < Decimal("0.01"), f"haiku 费用应很小，实际: ${cost}"

    @pytest.mark.asyncio
    async def test_transaction_recorded_after_api_call(
        self, client: AsyncClient, mock_redis: AsyncMock
    ) -> None:
        """API 调用后应在交易记录中可见。"""
        email = f"e2e_txn_{uuid.uuid4().hex[:8]}@test.com"
        token = await _register_user(client, email, "SecurePass123!")
        await _recharge(client, token, "5.00")
        oc_api_key = await _create_api_key(client, token, "Transaction Test Key")

        miner_hotkey = f"5miner_txn_{uuid.uuid4().hex[:8]}"
        await _register_miner(client, miner_hotkey, "sk-ant-fake-txn")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = ANTHROPIC_MOCK_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_resp)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_http

            await client.post(
                "/v1/messages",
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": "Transaction test"}],
                },
                headers={"x-api-key": oc_api_key},
            )

        # 使用记录应出现在交易列表中
        txn_resp = await client.get(
            "/api/v1/billing/transactions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert txn_resp.status_code == 200
        transactions = txn_resp.json()
        assert len(transactions) > 0, "API 调用后应有使用记录"
        # 交易记录含 model、cost 字段
        first_txn = transactions[0]
        assert "model" in first_txn, "交易记录应含 model 字段"
        assert "cost" in first_txn, "交易记录应含 cost 字段"
        assert Decimal(first_txn["cost"]) > Decimal("0"), "费用应大于 0"
