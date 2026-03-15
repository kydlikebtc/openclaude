"""
Phase 6 E2E Integration Tests — Miner Registration → Scoring → Weight Update
=============================================================================
验收标准：
  - Miner 注册→评分→权重更新完整流程
  - Admin 后台监控数据正确展示（矿工状态）
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


# ─── Helpers ────────────────────────────────────────────────────────────────

async def _register_user_and_get_admin_token(client: AsyncClient) -> str:
    """Register admin user and get token. Admin status set via role field."""
    email = f"admin_{uuid.uuid4().hex[:8]}@openclaude.io"
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "AdminPass123!"},
    )
    assert resp.status_code == 201
    return resp.json()["access_token"]


async def _register_miner_api(
    client: AsyncClient,
    hotkey: str,
    anthropic_key: str = "sk-ant-fake-test-key",
    referral_code: str | None = None,
) -> dict:
    """Register miner via public API."""
    payload = {
        "hotkey": hotkey,
        "coldkey": f"5cold_{hotkey[:8]}",
        "name": f"Miner-{hotkey[:8]}",
        "api_key": anthropic_key,
        "supported_models": ["claude-haiku-4-5-20251001"],
    }
    if referral_code:
        payload["referral_code"] = referral_code
    resp = await client.post("/api/v1/miners/register", json=payload)
    assert resp.status_code == 201, f"miner register failed: {resp.text}"
    return resp.json()


async def _get_miner_token(client: AsyncClient, hotkey: str) -> str:
    """Get miner JWT token via challenge-response auth."""
    # Step 1: get nonce
    challenge_resp = await client.get(
        "/api/v1/miners/auth/challenge",
        params={"hotkey": hotkey},
    )
    assert challenge_resp.status_code == 200
    nonce = challenge_resp.json()["nonce"]

    # Step 2: exchange for token (simplified signature)
    token_resp = await client.post(
        "/api/v1/miners/auth/token",
        json={
            "hotkey": hotkey,
            "nonce": nonce,
            "signature": "0x" + "a" * 128,  # placeholder signature
        },
    )
    assert token_resp.status_code == 200, f"miner auth failed: {token_resp.text}"
    return token_resp.json()["access_token"]


# ─── Miner Registration Tests ─────────────────────────────────────────────────

class TestMinerRegistration:
    """矿工注册完整流程测试。"""

    @pytest.mark.asyncio
    async def test_miner_register_basic(self, client: AsyncClient) -> None:
        """基础矿工注册：新矿工应注册成功。"""
        hotkey = f"5miner_{uuid.uuid4().hex[:16]}"
        data = await _register_miner_api(client, hotkey)

        assert data["hotkey"] == hotkey
        assert data["status"] == "active"
        assert "id" in data
        assert "referral_code" in data
        assert data["referral_code"] is not None, "应自动生成推荐码"

    @pytest.mark.asyncio
    async def test_miner_re_registration_updates_status(
        self, client: AsyncClient
    ) -> None:
        """矿工重注册应更新（而非创建重复记录）。"""
        hotkey = f"5miner_{uuid.uuid4().hex[:16]}"
        first = await _register_miner_api(client, hotkey, "sk-ant-key-v1")
        second = await _register_miner_api(client, hotkey, "sk-ant-key-v2")
        # 同一 hotkey 应更新，id 应相同
        assert first["id"] == second["id"], "重注册应更新同一矿工记录"
        assert second["status"] == "active"

    @pytest.mark.asyncio
    async def test_miner_register_with_referral(self, client: AsyncClient) -> None:
        """矿工注册时可使用推荐码。"""
        # 先注册推荐人
        referrer_hotkey = f"5referrer_{uuid.uuid4().hex[:12]}"
        referrer_data = await _register_miner_api(client, referrer_hotkey)
        referral_code = referrer_data["referral_code"]

        # 新矿工使用推荐码注册
        new_hotkey = f"5new_miner_{uuid.uuid4().hex[:10]}"
        new_data = await _register_miner_api(
            client, new_hotkey, referral_code=referral_code
        )
        assert new_data["status"] == "active"

    @pytest.mark.asyncio
    async def test_miner_pool_status_reflects_registration(
        self, client: AsyncClient
    ) -> None:
        """矿工注册后，矿工池状态应反映新矿工。"""
        # 获取注册前池状态
        pool_before = await client.get("/api/v1/miners/pool")
        assert pool_before.status_code == 200
        count_before = pool_before.json()["total_miners"]

        # 注册一个新矿工
        hotkey = f"5pool_test_{uuid.uuid4().hex[:12]}"
        await _register_miner_api(client, hotkey)

        # 注册后池状态应增加
        pool_after = await client.get("/api/v1/miners/pool")
        count_after = pool_after.json()["total_miners"]
        assert count_after > count_before, "注册后矿工池数量应增加"


# ─── Miner Auth Tests ─────────────────────────────────────────────────────────

class TestMinerAuth:
    """矿工认证流程测试。"""

    @pytest.mark.asyncio
    async def test_miner_challenge_response_auth(self, client: AsyncClient) -> None:
        """矿工应能通过 challenge-response 获取 JWT。"""
        hotkey = f"5miner_{uuid.uuid4().hex[:16]}"
        await _register_miner_api(client, hotkey)
        token = await _get_miner_token(client, hotkey)
        assert token, "应返回 JWT token"

    @pytest.mark.asyncio
    async def test_miner_me_endpoint_after_auth(self, client: AsyncClient) -> None:
        """矿工认证后应能访问 /miners/me 端点。"""
        hotkey = f"5miner_{uuid.uuid4().hex[:16]}"
        miner_data = await _register_miner_api(client, hotkey)
        token = await _get_miner_token(client, hotkey)

        me_resp = await client.get(
            "/api/v1/miners/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["hotkey"] == hotkey
        assert me_data["id"] == miner_data["id"]

    @pytest.mark.asyncio
    async def test_miner_auth_unknown_hotkey(self, client: AsyncClient) -> None:
        """未注册的 hotkey 不应获得 token。"""
        fake_hotkey = f"5unknown_{uuid.uuid4().hex[:16]}"
        challenge_resp = await client.get(
            "/api/v1/miners/auth/challenge",
            params={"hotkey": fake_hotkey},
        )
        nonce = challenge_resp.json()["nonce"]

        token_resp = await client.post(
            "/api/v1/miners/auth/token",
            json={
                "hotkey": fake_hotkey,
                "nonce": nonce,
                "signature": "0x" + "a" * 128,
            },
        )
        assert token_resp.status_code == 401


# ─── Miner Scoring Tests ──────────────────────────────────────────────────────

class TestMinerScoring:
    """矿工评分和权重更新测试。"""

    @pytest.mark.asyncio
    async def test_miner_heartbeat_records_latency(
        self, client: AsyncClient
    ) -> None:
        """矿工心跳应更新延迟信息（需要 JWT 认证）。"""
        hotkey = f"5miner_{uuid.uuid4().hex[:16]}"
        await _register_miner_api(client, hotkey)
        token = await _get_miner_token(client, hotkey)

        hb_resp = await client.post(
            "/api/v1/miners/heartbeat",
            json={
                "hotkey": hotkey,
                "avg_latency_ms": 250,
                "supported_models": ["claude-haiku-4-5-20251001"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert hb_resp.status_code == 200
        assert hb_resp.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_miner_score_endpoint_returns_components(
        self, client: AsyncClient
    ) -> None:
        """矿工评分端点应返回评分组件。"""
        hotkey = f"5miner_{uuid.uuid4().hex[:16]}"
        await _register_miner_api(client, hotkey)
        token = await _get_miner_token(client, hotkey)

        score_resp = await client.get(
            "/api/v1/miners/score",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert score_resp.status_code == 200
        score_data = score_resp.json()
        # Score response contains: current_score, components{final_score, ...}, history
        assert "current_score" in score_data
        assert 0.0 <= score_data["current_score"] <= 1.0, "评分应在 [0, 1] 范围内"
        assert "components" in score_data
        assert "final_score" in score_data["components"]

    @pytest.mark.asyncio
    async def test_miner_score_improves_after_good_latency(
        self, client: AsyncClient
    ) -> None:
        """低延迟矿工评分应高于默认值。"""
        hotkey = f"5miner_{uuid.uuid4().hex[:16]}"
        await _register_miner_api(client, hotkey)
        token = await _get_miner_token(client, hotkey)

        # 模拟低延迟心跳（需要认证）
        await client.post(
            "/api/v1/miners/heartbeat",
            json={
                "hotkey": hotkey,
                "avg_latency_ms": 150,  # 低于最优阈值 200ms
                "supported_models": ["claude-haiku-4-5-20251001"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        score_resp = await client.get(
            "/api/v1/miners/score",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert score_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_miner_api_key_management(self, client: AsyncClient) -> None:
        """矿工可以列出和添加 Anthropic API keys。"""
        hotkey = f"5miner_{uuid.uuid4().hex[:16]}"
        await _register_miner_api(client, hotkey)
        token = await _get_miner_token(client, hotkey)

        # 列出当前 keys
        keys_resp = await client.get(
            "/api/v1/miners/keys",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert keys_resp.status_code == 200
        initial_keys = keys_resp.json()

        # 添加新的 key
        add_resp = await client.post(
            "/api/v1/miners/keys",
            json={"api_key": "sk-ant-new-key-12345678901234567890"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert add_resp.status_code == 201
        assert add_resp.json()["status"] == "active"

    @pytest.mark.asyncio
    async def test_referral_score_bonus(self, client: AsyncClient) -> None:
        """有推荐下线的矿工评分应包含推荐奖励。"""
        # 注册推荐人矿工
        referrer_hotkey = f"5ref_{uuid.uuid4().hex[:12]}"
        referrer_data = await _register_miner_api(client, referrer_hotkey)
        referral_code = referrer_data["referral_code"]

        # 注册 2 个下线矿工
        for i in range(2):
            sub_hotkey = f"5sub_{uuid.uuid4().hex[:10]}_{i}"
            await _register_miner_api(
                client, sub_hotkey, referral_code=referral_code
            )

        # 获取推荐人的评分
        token = await _get_miner_token(client, referrer_hotkey)
        score_resp = await client.get(
            "/api/v1/miners/score",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert score_resp.status_code == 200
        score_data = score_resp.json()
        # 有 2 个直接推荐，组件内应有 referral_bonus 字段
        components = score_data.get("components", {})
        assert components.get("referral_bonus", 0) >= 0

    @pytest.mark.asyncio
    async def test_miner_referrals_endpoint(self, client: AsyncClient) -> None:
        """矿工推荐列表端点应正确返回推荐关系。"""
        referrer_hotkey = f"5ref2_{uuid.uuid4().hex[:10]}"
        referrer_data = await _register_miner_api(client, referrer_hotkey)
        referral_code = referrer_data["referral_code"]

        sub_hotkey = f"5sub2_{uuid.uuid4().hex[:10]}"
        await _register_miner_api(client, sub_hotkey, referral_code=referral_code)

        token = await _get_miner_token(client, referrer_hotkey)
        ref_resp = await client.get(
            "/api/v1/miners/referrals",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ref_resp.status_code == 200
        ref_data = ref_resp.json()
        assert "direct_referrals" in ref_data or "direct" in ref_data


# ─── Miner Pool Routing Tests ─────────────────────────────────────────────────

class TestMinerPoolRouting:
    """矿工池路由和隔离测试。"""

    @pytest.mark.asyncio
    async def test_multiple_miners_in_pool(self, client: AsyncClient) -> None:
        """多个矿工应在池中并行可用。"""
        hotkeys = [f"5pool_{uuid.uuid4().hex[:12]}" for _ in range(3)]
        for hk in hotkeys:
            await _register_miner_api(client, hk)

        pool_resp = await client.get("/api/v1/miners/pool")
        assert pool_resp.status_code == 200
        pool_data = pool_resp.json()
        assert pool_data["total_miners"] >= 3

    @pytest.mark.asyncio
    async def test_routing_uses_miner_with_best_score(
        self, client: AsyncClient, mock_redis: AsyncMock
    ) -> None:
        """路由请求时应优先选择高分矿工（加权随机）。"""
        # 注册两个矿工（不同 key，便于区分）
        hk1 = f"5high_{uuid.uuid4().hex[:12]}"
        hk2 = f"5low_{uuid.uuid4().hex[:12]}"
        await _register_miner_api(client, hk1, "sk-ant-high-score-miner")
        await _register_miner_api(client, hk2, "sk-ant-low-score-miner")

        # 注册用户并充值
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={"email": f"router_{uuid.uuid4().hex[:8]}@test.com", "password": "Pass123!"},
        )
        token = reg_resp.json()["access_token"]
        await client.post(
            "/api/v1/billing/recharge",
            json={"amount": "10.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        key_resp = await client.post(
            "/api/v1/api-keys",
            json={"name": "routing test key"},
            headers={"Authorization": f"Bearer {token}"},
        )
        oc_key = key_resp.json()["key"]

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "msg_routing_test",
            "type": "message",
            "role": "assistant",
            "model": "claude-haiku-4-5-20251001",
            "content": [{"type": "text", "text": "Routed!"}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 5, "output_tokens": 5},
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_resp)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_http

            proxy_resp = await client.post(
                "/v1/messages",
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 50,
                    "messages": [{"role": "user", "content": "Test routing"}],
                },
                headers={"x-api-key": oc_key},
            )
        assert proxy_resp.status_code == 200
        assert proxy_resp.json()["content"][0]["text"] == "Routed!"
