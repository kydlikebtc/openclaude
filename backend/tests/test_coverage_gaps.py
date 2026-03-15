"""
覆盖率缺口补充测试
====================
覆盖以下尚未被其他测试触达的分支/行：

- app/services/user_service.py:  无效UUID、用户不存在/未激活认证
- app/services/miner_service.py: record_heartbeat、update_miner_score、list_miners(status)、get_pool_status(无redis)
- app/services/scoring_service.py: 无redis数据、persist_score_snapshot、update_score_in_redis
- app/services/billing_service.py: 用户不存在时的 ValueError
- app/core/deps.py: 无效token、用户未激活、miner token格式错误/UUID非法/矿工不存在
- app/core/logging.py: get_logger
- app/api/v1/billing.py: recharge ValueError (负数金额)
- app/api/v1/admin.py: list_transactions 带 user_id/miner_id 过滤
- app/api/v1/miners.py: miner_auth nonce失效、update_me coldkey、heartbeat hotkey不在redis、get_score redis=None/无数据
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.miner import Miner, MinerScoreHistory
from app.models.user import User
from app.services.scoring_service import ScoreComponents


# ── user_service 缺口测试 ─────────────────────────────────────────────────────

class TestUserServiceGaps:
    """直接调用 user_service 函数，覆盖边界路径。"""

    @pytest.mark.asyncio
    async def test_get_user_by_id_invalid_uuid(self, db: AsyncSession) -> None:
        """无效 UUID 字符串应返回 None（覆盖 except ValueError 分支）。"""
        from app.services.user_service import get_user_by_id

        result = await get_user_by_id(db, "not-a-valid-uuid")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, db: AsyncSession) -> None:
        """邮箱不存在时 authenticate_user 应返回 None。"""
        from app.services.user_service import authenticate_user

        result = await authenticate_user(db, "nonexistent@test.com", "password123")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, db: AsyncSession) -> None:
        """用户状态非 active 时 authenticate_user 应返回 None。"""
        from app.services.user_service import authenticate_user

        # 直接写入未激活用户
        inactive_user = User(
            email=f"inactive_{uuid.uuid4().hex[:8]}@test.com",
            password_hash=hash_password("Password123!"),
            status="suspended",
        )
        db.add(inactive_user)
        await db.flush()

        result = await authenticate_user(db, inactive_user.email, "Password123!")
        assert result is None


# ── miner_service 缺口测试 ────────────────────────────────────────────────────

class TestMinerServiceGaps:
    """直接调用 miner_service 函数，覆盖 redis 操作路径。"""

    @pytest.mark.asyncio
    async def test_record_heartbeat_unknown_miner(self, mock_redis: AsyncMock) -> None:
        """未知 hotkey 的心跳应返回 False。"""
        from app.services.miner_service import record_heartbeat

        result = await record_heartbeat(mock_redis, "unknown-hotkey-xyz", 100)
        assert result is False

    @pytest.mark.asyncio
    async def test_record_heartbeat_known_miner(self, mock_redis: AsyncMock) -> None:
        """已知 miner_id 的心跳应返回 True 并更新 redis。"""
        from app.services.miner_service import record_heartbeat

        miner_id = str(uuid.uuid4())
        hotkey = "known-hotkey-test"
        # 提前存入 hotkey->id 映射
        await mock_redis.set(f"miner:hotkey:{hotkey}", miner_id)

        result = await record_heartbeat(mock_redis, hotkey, 150)
        assert result is True

    @pytest.mark.asyncio
    async def test_update_miner_score_not_isolated(self, mock_redis: AsyncMock) -> None:
        """矿工未被隔离时，应更新排序集合中的分数。"""
        from app.services.miner_service import update_miner_score

        miner_id = str(uuid.uuid4())
        # 不设置 isolation key → 矿工不在隔离状态
        await update_miner_score(mock_redis, miner_id, 0.75)

        # 验证分数被写入 pool
        from app.services.miner_service import MINER_POOL_KEY
        score = await mock_redis.zscore(MINER_POOL_KEY, miner_id)
        assert score == 0.75

    @pytest.mark.asyncio
    async def test_list_miners_with_status_filter(self, db: AsyncSession) -> None:
        """list_miners 带 status 过滤应只返回对应状态的矿工。"""
        from app.services.miner_service import list_miners

        # 创建两个不同状态的矿工
        active_miner = Miner(
            hotkey=f"5active_{uuid.uuid4().hex[:8]}",
            coldkey="5cold_active",
            name="Active Miner",
            status="active",
            referral_code="ACTIVE1",
        )
        inactive_miner = Miner(
            hotkey=f"5inactive_{uuid.uuid4().hex[:8]}",
            coldkey="5cold_inactive",
            name="Inactive Miner",
            status="registered",
            referral_code="INACT01",
        )
        db.add(active_miner)
        db.add(inactive_miner)
        await db.flush()

        active_list = await list_miners(db, status="active")
        assert all(m.status == "active" for m in active_list)

    @pytest.mark.asyncio
    async def test_get_pool_status_no_redis(self) -> None:
        """redis=None 时 get_pool_status 应返回全零默认值。"""
        from app.services.miner_service import get_pool_status

        result = await get_pool_status(None)
        assert result == {"total_miners": 0, "online_miners": 0, "miners_by_model": {}}


# ── scoring_service 缺口测试 ──────────────────────────────────────────────────

class TestScoringServiceGaps:
    """覆盖评分服务中 redis 无数据和 DB 写入路径。"""

    @pytest.mark.asyncio
    async def test_get_miner_score_no_info_returns_none(
        self, mock_redis: AsyncMock
    ) -> None:
        """redis 中无矿工信息时 get_miner_score_from_redis 应返回 None。"""
        from app.services.scoring_service import get_miner_score_from_redis

        # 使用一个不存在于 redis 的 miner_id
        result = await get_miner_score_from_redis(mock_redis, str(uuid.uuid4()))
        assert result is None

    @pytest.mark.asyncio
    async def test_persist_score_snapshot(self, db: AsyncSession) -> None:
        """persist_score_snapshot 应向 DB 写入分数快照。"""
        from app.services.scoring_service import persist_score_snapshot

        # 先创建矿工
        miner = Miner(
            hotkey=f"5score_{uuid.uuid4().hex[:8]}",
            coldkey="5cold_score",
            name="Score Miner",
            status="active",
            referral_code="SCORE01",
        )
        db.add(miner)
        await db.flush()

        components = ScoreComponents(
            availability=0.9,
            latency_score=0.8,
            quality=0.7,
            consistency=0.8,
            efficiency=0.85,
            referral_bonus=0.05,
            final_score=0.82,
        )

        snapshot = await persist_score_snapshot(db, miner.id, components)
        assert snapshot.final_score == pytest.approx(0.82)
        assert snapshot.miner_id == miner.id

    @pytest.mark.asyncio
    async def test_update_score_in_redis(self, mock_redis: AsyncMock) -> None:
        """update_score_in_redis 应向 sorted set 写入最终分数。"""
        from app.services.scoring_service import update_score_in_redis
        from app.services.miner_service import MINER_POOL_KEY

        miner_id = str(uuid.uuid4())
        components = ScoreComponents(
            availability=1.0,
            latency_score=1.0,
            quality=1.0,
            consistency=1.0,
            efficiency=1.0,
            referral_bonus=0.0,
            final_score=0.9,
        )

        await update_score_in_redis(mock_redis, miner_id, components)
        score = await mock_redis.zscore(MINER_POOL_KEY, miner_id)
        assert score == pytest.approx(0.9)


# ── billing_service 缺口测试 ──────────────────────────────────────────────────

class TestBillingServiceGaps:
    """覆盖用户不存在时的 ValueError 路径。"""

    @pytest.mark.asyncio
    async def test_check_deduct_user_not_found(self, db: AsyncSession) -> None:
        """用户不存在时 check_and_deduct_balance 应抛出 ValueError。"""
        from app.services.billing_service import check_and_deduct_balance

        with pytest.raises(ValueError, match="not found"):
            await check_and_deduct_balance(
                db,
                user_id=uuid.uuid4(),
                model="claude-haiku-4-5-20251001",
                tokens_in=100,
                tokens_out=50,
            )

    @pytest.mark.asyncio
    async def test_recharge_user_not_found(self, db: AsyncSession) -> None:
        """用户不存在时 recharge_balance 应抛出 ValueError。"""
        from app.services.billing_service import recharge_balance

        with pytest.raises(ValueError, match="not found"):
            await recharge_balance(db, user_id=uuid.uuid4(), amount=Decimal("10.00"))


# ── logging 缺口测试 ──────────────────────────────────────────────────────────

class TestLoggingGaps:
    def test_get_logger(self) -> None:
        """get_logger 应返回 structlog BoundLogger 实例。"""
        from app.core.logging import get_logger

        logger = get_logger("test.module")
        assert logger is not None


# ── API 端点覆盖率缺口测试 ─────────────────────────────────────────────────────

class TestDepsGaps:
    """FastAPI 依赖注入中的未覆盖分支（通过 HTTP 测试）。"""

    @pytest.mark.asyncio
    async def test_invalid_jwt_token_returns_401(self, client: AsyncClient) -> None:
        """无效 JWT 应触发 get_current_user 中 decode 返回 None 的路径。"""
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer totally.invalid.token"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_inactive_user_returns_401(self, client: AsyncClient, db: AsyncSession) -> None:
        """已暂停用户访问受保护端点应返回 401。"""
        # 创建未激活用户并生成其 JWT
        email = f"suspended_{uuid.uuid4().hex[:8]}@test.com"
        user = User(
            email=email,
            password_hash=hash_password("Password123!"),
            status="suspended",
        )
        db.add(user)
        await db.flush()

        token = create_access_token(str(user.id))
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_miner_endpoint_with_user_jwt_returns_401(
        self, client: AsyncClient
    ) -> None:
        """用户 JWT（subject 无 'miner:' 前缀）调用矿工端点应返回 401。"""
        # 创建用户并获取 token
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"user_on_miner_{uuid.uuid4().hex[:8]}@test.com",
                "password": "Password123!",
            },
        )
        user_token = reg.json()["access_token"]

        resp = await client.get(
            "/api/v1/miners/me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_miner_endpoint_with_malformed_uuid_returns_401(
        self, client: AsyncClient
    ) -> None:
        """'miner:not-a-uuid' JWT 应触发 UUID 解析失败路径。"""
        bad_token = create_access_token("miner:not-a-valid-uuid")
        resp = await client.get(
            "/api/v1/miners/me",
            headers={"Authorization": f"Bearer {bad_token}"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_miner_endpoint_with_nonexistent_miner_returns_401(
        self, client: AsyncClient
    ) -> None:
        """合法格式但不存在的 miner UUID 应返回 401（矿工不存在）。"""
        nonexistent_id = str(uuid.uuid4())
        token = create_access_token(f"miner:{nonexistent_id}")
        resp = await client.get(
            "/api/v1/miners/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401


class TestBillingApiGaps:
    """账单 API 错误路径覆盖。"""

    @pytest.mark.asyncio
    async def test_recharge_service_raises_value_error_returns_400(
        self, client: AsyncClient
    ) -> None:
        """recharge_balance 抛出 ValueError 时应返回 400（覆盖 billing.py lines 41-42）。

        Pydantic schema 有 gt=0 约束，直接传负数会触发 422。
        因此通过 mock 模拟 service 层抛出 ValueError 来覆盖 except 分支。
        """
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"billing_err_{uuid.uuid4().hex[:8]}@test.com",
                "password": "Password123!",
            },
        )
        token = reg.json()["access_token"]

        with patch(
            "app.api.v1.billing.recharge_balance",
            new=AsyncMock(side_effect=ValueError("simulated recharge error")),
        ):
            resp = await client.post(
                "/api/v1/billing/recharge",
                json={"amount": "10.00"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 400
        assert "simulated recharge error" in resp.json()["detail"]


class TestAdminApiGaps:
    """Admin API 过滤路径覆盖。"""

    @pytest.fixture
    async def admin_token(self, client: AsyncClient, db: AsyncSession) -> str:
        """创建并返回管理员用户 JWT。"""
        email = f"admin_gap_{uuid.uuid4().hex[:8]}@test.com"
        user = User(
            email=email,
            password_hash=hash_password("AdminPass123!"),
            status="active",
            is_admin=True,
        )
        db.add(user)
        await db.flush()
        return create_access_token(str(user.id))

    @pytest.mark.asyncio
    async def test_list_transactions_with_user_id_filter(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """带 user_id 过滤的交易列表应正常返回。"""
        random_user_id = str(uuid.uuid4())
        resp = await client.get(
            f"/api/v1/admin/transactions?user_id={random_user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_transactions_with_miner_id_filter(
        self, client: AsyncClient, admin_token: str
    ) -> None:
        """带 miner_id 过滤的交易列表应正常返回（覆盖 admin.py lines 152-153）。"""
        random_miner_id = str(uuid.uuid4())
        resp = await client.get(
            f"/api/v1/admin/transactions?miner_id={random_miner_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] == 0


class TestMinersApiGaps:
    """矿工 API 中未覆盖分支测试。"""

    @pytest.fixture
    async def registered_miner_and_token(
        self, client: AsyncClient
    ) -> tuple[str, str]:
        """注册矿工并返回 (hotkey, miner_jwt)。"""
        hotkey = f"5gap_miner_{uuid.uuid4().hex[:10]}"
        await client.post(
            "/api/v1/miners/register",
            json={
                "hotkey": hotkey,
                "coldkey": f"5cold_{hotkey[:8]}",
                "name": "Gap Test Miner",
                "api_key": "sk-ant-gap-test",
                "supported_models": ["claude-haiku-4-5-20251001"],
            },
        )
        # 获取 miner JWT
        challenge_resp = await client.get("/api/v1/miners/auth/challenge")
        nonce = challenge_resp.json()["nonce"]
        token_resp = await client.post(
            "/api/v1/miners/auth/token",
            json={"hotkey": hotkey, "nonce": nonce, "signature": "sig-placeholder"},
        )
        return hotkey, token_resp.json()["access_token"]

    @pytest.mark.asyncio
    async def test_miner_auth_invalid_nonce_returns_401(
        self, client: AsyncClient
    ) -> None:
        """使用已过期/无效 nonce 应返回 401（覆盖 miners.py line 95）。"""
        hotkey = f"5nonce_test_{uuid.uuid4().hex[:10]}"
        await client.post(
            "/api/v1/miners/register",
            json={
                "hotkey": hotkey,
                "coldkey": "5cold_nonce",
                "name": "Nonce Miner",
                "api_key": "sk-ant-nonce-test",
                "supported_models": ["claude-haiku-4-5-20251001"],
            },
        )

        # 使用一个不存在的 nonce（redis 中无对应记录）
        resp = await client.post(
            "/api/v1/miners/auth/token",
            json={
                "hotkey": hotkey,
                "nonce": "nonexistent_nonce_12345678",
                "signature": "sig-placeholder",
            },
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_update_me_with_coldkey(
        self, client: AsyncClient, registered_miner_and_token: tuple
    ) -> None:
        """PATCH /miners/me 更新 coldkey 应成功（覆盖 miners.py line 200）。"""
        _, miner_token = registered_miner_and_token
        resp = await client.patch(
            "/api/v1/miners/me",
            json={"coldkey": "5cold_new_value"},
            headers={"Authorization": f"Bearer {miner_token}"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_heartbeat_miner_in_db_not_in_redis(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """矿工在 DB 中但不在 redis 时，心跳应自动写入 redis（覆盖 miners.py lines 308-310）。"""
        hotkey = f"5db_only_{uuid.uuid4().hex[:10]}"
        # 直接写入 DB（不经过 register endpoint，故 redis 中无此 hotkey）
        miner = Miner(
            hotkey=hotkey,
            coldkey="5cold_db_only",
            name="DB Only Miner",
            status="active",
            referral_code=f"DB{uuid.uuid4().hex[:4].upper()}",
        )
        db.add(miner)
        await db.flush()

        resp = await client.post(
            "/api/v1/miners/heartbeat",
            json={
                "hotkey": hotkey,
                "avg_latency_ms": 200,
                "supported_models": ["claude-haiku-4-5-20251001"],
            },
        )
        assert resp.status_code == 200
        assert "miner_id" in resp.json()

    @pytest.mark.asyncio
    async def test_get_score_redis_unavailable(
        self, client: AsyncClient, registered_miner_and_token: tuple
    ) -> None:
        """redis=None 时 /miners/score 应返回 503（覆盖 miners.py line 333）。"""
        from app.main import app

        _, miner_token = registered_miner_and_token

        original_redis = app.state.redis
        try:
            app.state.redis = None
            resp = await client.get(
                "/api/v1/miners/score",
                headers={"Authorization": f"Bearer {miner_token}"},
            )
        finally:
            app.state.redis = original_redis

        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_get_score_no_redis_data_returns_defaults(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """redis 中无矿工数据时应返回中性默认分数（覆盖 miners.py line 341）。

        直接在 DB 中创建矿工（跳过 register 端点），redis 中无此矿工 info，
        get_miner_score_from_redis 返回 None → 使用默认值路径。
        """
        from app.main import app

        # 直接在 DB 创建矿工，不走 register 端点 → redis 无 info
        hotkey = f"5score_noredis_{uuid.uuid4().hex[:8]}"
        miner = Miner(
            hotkey=hotkey,
            coldkey="5cold_noredis",
            name="No Redis Score Miner",
            status="active",
            referral_code=f"NR{uuid.uuid4().hex[:4].upper()}",
        )
        db.add(miner)
        await db.flush()

        miner_token = create_access_token(f"miner:{miner.id}")

        resp = await client.get(
            "/api/v1/miners/score",
            headers={"Authorization": f"Bearer {miner_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "current_score" in data
        # 默认值路径：current_score 应为 0.5
        assert data["current_score"] == pytest.approx(0.5)
