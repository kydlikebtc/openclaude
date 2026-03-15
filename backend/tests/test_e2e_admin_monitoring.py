"""
Phase 6 E2E Integration Tests — Admin Dashboard Monitoring
===========================================================
验收标准：
  - Admin 后台监控数据正确展示（矿工状态、用量统计）
  - Admin 可以查看所有用户列表和交易记录
  - 用量统计数据在 API 调用后正确更新
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
async def admin_token(client: AsyncClient, db: AsyncSession) -> str:
    """注册用户并通过 DB 直接提升为 Admin。"""
    email = f"e2e_admin_{uuid.uuid4().hex[:8]}@openclaude.io"
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "AdminPass123!"},
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]

    # 直接提升为 admin（通过 DB）
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    user.is_admin = True
    await db.flush()

    return token


@pytest.fixture
async def regular_token(client: AsyncClient) -> str:
    """注册普通用户并返回 token。"""
    email = f"e2e_user_{uuid.uuid4().hex[:8]}@test.com"
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "UserPass123!"},
    )
    assert resp.status_code == 201
    return resp.json()["access_token"]


# ─── Admin User Monitoring Tests ──────────────────────────────────────────────

class TestAdminUserMonitoring:
    """Admin 用户监控功能验证。"""

    @pytest.mark.asyncio
    async def test_admin_can_see_all_users(
        self, client: AsyncClient, admin_token: str, regular_token: str
    ) -> None:
        """Admin 可以查看所有用户列表，包括普通用户。"""
        resp = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2, "应至少有 admin 和 regular 两个用户"
        # 每个用户记录应有关键字段
        for user in data["items"]:
            assert "id" in user
            assert "email" in user
            assert "status" in user
            assert "balance" in user
            assert "is_admin" in user

    @pytest.mark.asyncio
    async def test_regular_user_cannot_access_admin(
        self, client: AsyncClient, regular_token: str
    ) -> None:
        """普通用户不能访问 Admin 端点（403 Forbidden）。"""
        resp = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {regular_token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_filter_users_by_status(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """Admin 可以按状态过滤用户列表。"""
        resp = await client.get(
            "/api/v1/admin/users?status=active",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for user in data["items"]:
            assert user["status"] == "active"

    @pytest.mark.asyncio
    async def test_admin_can_suspend_user(
        self, client: AsyncClient, admin_token: str, regular_token: str, db: AsyncSession
    ) -> None:
        """Admin 可以暂停用户账户。"""
        # 获取普通用户 ID
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {regular_token}"},
        )
        user_id = me_resp.json()["id"]

        # Admin 暂停该用户
        suspend_resp = await client.patch(
            f"/api/v1/admin/users/{user_id}",
            json={"status": "suspended"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert suspend_resp.status_code == 200
        assert suspend_resp.json()["status"] == "suspended"

    @pytest.mark.asyncio
    async def test_admin_user_pagination(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """Admin 用户列表支持分页。"""
        resp = await client.get(
            "/api/v1/admin/users?page=1&page_size=5",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 5


# ─── Admin Transaction Monitoring Tests ──────────────────────────────────────

class TestAdminTransactionMonitoring:
    """Admin 交易监控功能验证。"""

    @pytest.mark.asyncio
    async def test_admin_sees_transactions_after_api_call(
        self,
        client: AsyncClient,
        admin_token: str,
        mock_redis: AsyncMock,
    ) -> None:
        """API 调用产生的交易应在 Admin 交易列表中可见。"""
        # 注册用户并充值
        email = f"e2e_pay_{uuid.uuid4().hex[:8]}@test.com"
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Pass123!"},
        )
        user_token = reg_resp.json()["access_token"]
        await client.post(
            "/api/v1/billing/recharge",
            json={"amount": "5.00"},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # 创建 API key 和注册矿工
        key_resp = await client.post(
            "/api/v1/api-keys",
            json={"name": "admin monitoring key"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        oc_key = key_resp.json()["key"]

        hotkey = f"5admin_miner_{uuid.uuid4().hex[:12]}"
        await client.post(
            "/api/v1/miners/register",
            json={
                "hotkey": hotkey,
                "coldkey": f"5cold_{hotkey[:8]}",
                "name": "AdminTestMiner",
                "api_key": "sk-ant-fake-admin-test",
                "supported_models": ["claude-haiku-4-5-20251001"],
            },
        )

        # Mock Anthropic call
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "msg_admin_test",
            "type": "message",
            "role": "assistant",
            "model": "claude-haiku-4-5-20251001",
            "content": [{"type": "text", "text": "Admin monitoring test"}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 15, "output_tokens": 8},
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
                    "messages": [{"role": "user", "content": "admin test"}],
                },
                headers={"x-api-key": oc_key},
            )
        assert proxy_resp.status_code == 200

        # Admin 查看交易记录
        txn_resp = await client.get(
            "/api/v1/admin/transactions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert txn_resp.status_code == 200
        data = txn_resp.json()
        assert data["total"] >= 1, "交易应已记录"
        # 验证交易字段
        if data["items"]:
            txn = data["items"][0]
            assert "model" in txn
            assert "tokens_in" in txn
            assert "tokens_out" in txn
            assert "cost" in txn

    @pytest.mark.asyncio
    async def test_admin_transaction_filter_by_user(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """Admin 可以按用户 ID 过滤交易记录。"""
        user_id = str(uuid.uuid4())  # 不存在的 ID
        resp = await client.get(
            f"/api/v1/admin/transactions?user_id={user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_admin_transaction_pagination(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """Admin 交易列表支持分页。"""
        resp = await client.get(
            "/api/v1/admin/transactions?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 10


# ─── Admin Miner Monitoring Tests ─────────────────────────────────────────────

class TestAdminMinerMonitoring:
    """Admin 矿工状态监控验证。"""

    @pytest.mark.asyncio
    async def test_admin_can_view_miner_pool_status(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """Admin 可以查看矿工池状态（公开端点）。"""
        # 注册几个矿工
        for i in range(2):
            await client.post(
                "/api/v1/miners/register",
                json={
                    "hotkey": f"5admin_monitor_{uuid.uuid4().hex[:12]}",
                    "coldkey": f"5cold_{i}",
                    "name": f"MonitorMiner{i}",
                    "api_key": f"sk-ant-monitor-{i}",
                    "supported_models": ["claude-haiku-4-5-20251001"],
                },
            )

        pool_resp = await client.get("/api/v1/miners/pool")
        assert pool_resp.status_code == 200
        pool_data = pool_resp.json()
        assert "total_miners" in pool_data
        assert pool_data["total_miners"] >= 2

    @pytest.mark.asyncio
    async def test_admin_can_list_miners(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """Admin 可以查看矿工列表（需认证端点）。"""
        miners_resp = await client.get(
            "/api/v1/miners",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert miners_resp.status_code == 200
        miners = miners_resp.json()
        assert isinstance(miners, list)

    @pytest.mark.asyncio
    async def test_miner_status_shown_correctly(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """矿工注册后状态应为 active。"""
        hotkey = f"5status_test_{uuid.uuid4().hex[:12]}"
        register_resp = await client.post(
            "/api/v1/miners/register",
            json={
                "hotkey": hotkey,
                "coldkey": f"5cold_{hotkey[:8]}",
                "name": "StatusTestMiner",
                "api_key": "sk-ant-status-test",
                "supported_models": ["claude-haiku-4-5-20251001"],
            },
        )
        miner_id = register_resp.json()["id"]

        # 通过 miners 列表验证状态（需认证）
        miners_resp = await client.get(
            "/api/v1/miners",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        miners = miners_resp.json()
        miner = next((m for m in miners if m["id"] == miner_id), None)
        assert miner is not None, "矿工应在列表中"
        assert miner["status"] == "active", "矿工状态应为 active"


# ─── Usage Statistics Monitoring Tests ────────────────────────────────────────

class TestUsageStatsMonitoring:
    """用量统计监控验证。"""

    @pytest.mark.asyncio
    async def test_usage_summary_reflects_api_calls(
        self, client: AsyncClient, mock_redis: AsyncMock
    ) -> None:
        """API 调用后用量统计应正确更新。"""
        email = f"e2e_usage_{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Pass123!"},
        )
        token = reg.json()["access_token"]
        await client.post(
            "/api/v1/billing/recharge",
            json={"amount": "10.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        key = (await client.post(
            "/api/v1/api-keys",
            json={"name": "usage test key"},
            headers={"Authorization": f"Bearer {token}"},
        )).json()["key"]

        hotkey = f"5usage_miner_{uuid.uuid4().hex[:10]}"
        await client.post(
            "/api/v1/miners/register",
            json={
                "hotkey": hotkey,
                "coldkey": f"5cold_{hotkey[:8]}",
                "name": "UsageMiner",
                "api_key": "sk-ant-usage-test",
                "supported_models": ["claude-haiku-4-5-20251001"],
            },
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "msg_usage",
            "type": "message",
            "role": "assistant",
            "model": "claude-haiku-4-5-20251001",
            "content": [{"type": "text", "text": "usage test"}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 20, "output_tokens": 10},
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
                    "messages": [{"role": "user", "content": "usage test"}],
                },
                headers={"x-api-key": key},
            )
        assert proxy_resp.status_code == 200

        # 验证用量统计
        usage_resp = await client.get(
            "/api/v1/billing/usage?period=today",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert usage_resp.status_code == 200
        usage = usage_resp.json()
        assert usage["total_requests"] >= 1, "应至少有 1 次请求记录"
        assert usage["total_tokens_in"] >= 20, "输入 token 应已记录"
        assert usage["total_tokens_out"] >= 10, "输出 token 应已记录"
        assert Decimal(usage["total_cost"]) > Decimal("0"), "应有费用记录"

    @pytest.mark.asyncio
    async def test_daily_usage_breakdown_structure(
        self, client: AsyncClient
    ) -> None:
        """每日用量分解端点应返回正确结构（新用户无数据时返回空列表）。"""
        email = f"e2e_daily_{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Pass123!"},
        )
        token = reg.json()["access_token"]

        daily_resp = await client.get(
            "/api/v1/usage/daily",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert daily_resp.status_code == 200
        daily_data = daily_resp.json()
        # 验证响应结构
        assert "items" in daily_data
        assert "total_requests" in daily_data
        assert "total_cost" in daily_data
        assert "start" in daily_data
        assert "end" in daily_data
        # 新用户无交易
        assert daily_data["total_requests"] == 0
        assert Decimal(daily_data["total_cost"]) == Decimal("0")

    @pytest.mark.asyncio
    async def test_daily_usage_filter_by_model(
        self, client: AsyncClient
    ) -> None:
        """每日用量端点支持按模型过滤。"""
        email = f"e2e_model_{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Pass123!"},
        )
        token = reg.json()["access_token"]

        resp = await client.get(
            "/api/v1/usage/daily?model=claude-haiku-4-5-20251001",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # 过滤后的结果中每条记录模型应匹配
        for item in data["items"]:
            assert item["model"] == "claude-haiku-4-5-20251001"
