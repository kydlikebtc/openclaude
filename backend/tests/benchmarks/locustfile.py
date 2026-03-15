"""OpenClade 路由引擎负载测试脚本 — Locust

覆盖端点:
  - POST /v1/messages        (主要负载：路由引擎 + billing)
  - POST /api/v1/auth/login  (认证负载)
  - GET  /api/v1/usage/daily (读取负载)
  - GET  /api/v1/miners      (矿工列表负载)

使用方法 (需要先启动 docker-compose.benchmark.yml):
    # 方式1：Web UI 模式（可视化监控）
    locust -f tests/benchmarks/locustfile.py --host=http://localhost:8000

    # 方式2：无头模式（CI/自动化）— 500 QPS 验收
    locust -f tests/benchmarks/locustfile.py --host=http://localhost:8000 \
        --headless -u 200 -r 50 --run-time 60s --csv=docs/benchmark_results

    # 方式3：1000 QPS 峰值测试
    locust -f tests/benchmarks/locustfile.py --host=http://localhost:8000 \
        --headless -u 500 -r 100 --run-time 120s --csv=docs/benchmark_1000qps

环境变量:
    LOCUST_HOST           — 目标服务地址（默认 http://localhost:8000）
    BENCH_USER_EMAIL      — 复用已有测试用户 email（省略则自动创建）
    BENCH_USER_PASSWORD   — 对应密码
    BENCH_API_KEY         — 复用已有 OpenClade API Key（省略则自动创建）
"""

import os
import random
import uuid

from locust import HttpUser, between, events, task
from locust.runners import MasterRunner

# ─── 全局共享测试凭据（setUp 阶段填充）──────────────────────────────────────────

_shared_credentials: dict = {
    "email": os.getenv("BENCH_USER_EMAIL", ""),
    "password": os.getenv("BENCH_USER_PASSWORD", "benchpass_0xDEAD"),
    "token": "",
    "api_key": os.getenv("BENCH_API_KEY", ""),
}

_MODELS = [
    "claude-haiku-4-5-20251001",
    "claude-sonnet-4-6",
]

_MESSAGES_PAYLOADS = [
    {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 64,
        "messages": [{"role": "user", "content": "Ping. Reply with one word."}],
    },
    {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 128,
        "messages": [{"role": "user", "content": "What is 2+2?"}],
    },
    {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 32,
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ],
    },
]


# ─── 测试环境初始化 ─────────────────────────────────────────────────────────────

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """在负载测试开始前，创建测试用户、充值、生成 API Key、注册 mock 矿工。"""
    if isinstance(environment.runner, MasterRunner):
        # Locust 分布式模式：仅 master 初始化
        return

    host = environment.host or "http://localhost:8000"

    import requests

    # 1. 创建/复用测试用户
    if not _shared_credentials["email"]:
        _shared_credentials["email"] = f"bench_{uuid.uuid4().hex[:8]}@benchmark.openclaude.io"

    email = _shared_credentials["email"]
    password = _shared_credentials["password"]

    # 尝试注册（已存在则跳过）
    reg_resp = requests.post(
        f"{host}/api/v1/auth/register",
        json={"email": email, "password": password},
        timeout=10,
    )
    if reg_resp.status_code == 201:
        _shared_credentials["token"] = reg_resp.json()["access_token"]
        print(f"[benchmark] 创建测试用户: {email}")
    elif reg_resp.status_code == 409:
        # 已存在，直接登录
        login_resp = requests.post(
            f"{host}/api/v1/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        _shared_credentials["token"] = login_resp.json()["access_token"]
        print(f"[benchmark] 复用测试用户: {email}")
    else:
        print(f"[benchmark] WARNING: 用户创建失败 {reg_resp.status_code}: {reg_resp.text[:200]}")
        return

    token = _shared_credentials["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 充值（确保余额足够）
    recharge_resp = requests.post(
        f"{host}/api/v1/billing/recharge",
        json={"amount": "10000.00"},
        headers=headers,
        timeout=10,
    )
    if recharge_resp.status_code == 200:
        balance = recharge_resp.json().get("balance", "?")
        print(f"[benchmark] 充值成功，余额: {balance}")
    else:
        print(f"[benchmark] WARNING: 充值失败 {recharge_resp.status_code}")

    # 3. 创建/复用 API Key
    if not _shared_credentials["api_key"]:
        key_resp = requests.post(
            f"{host}/api/v1/api-keys",
            json={"name": f"benchmark_{uuid.uuid4().hex[:6]}"},
            headers=headers,
            timeout=10,
        )
        if key_resp.status_code == 201:
            _shared_credentials["api_key"] = key_resp.json()["key"]
            print(f"[benchmark] API Key 创建成功: {_shared_credentials['api_key'][:12]}...")
        else:
            print(f"[benchmark] WARNING: API Key 创建失败 {key_resp.status_code}")

    # 4. 注册 mock 矿工（确保路由引擎有可用矿工）
    for i in range(5):
        hotkey = f"5bench_miner_{uuid.uuid4().hex[:12]}"
        miner_resp = requests.post(
            f"{host}/api/v1/miners/register",
            json={
                "hotkey": hotkey,
                "coldkey": f"5cold_{hotkey[:8]}",
                "name": f"BenchMiner{i}",
                "api_key": f"sk-ant-benchmark-mock-{i:03d}",
                "supported_models": _MODELS,
            },
            timeout=10,
        )
        if miner_resp.status_code in (200, 201):
            print(f"[benchmark] 注册矿工 {i}: {hotkey[:20]}...")
        else:
            print(f"[benchmark] WARNING: 矿工注册失败 {i}: {miner_resp.status_code}")

    print(f"[benchmark] 初始化完成 — 目标: {host}")


# ─── User 类 ────────────────────────────────────────────────────────────────────

class ProxyUser(HttpUser):
    """主要负载: POST /v1/messages — 路由引擎 + 计费路径。

    权重 70%（最重要的端点）。
    """
    weight = 7
    wait_time = between(0.05, 0.2)  # 快速请求模拟高 QPS

    def on_start(self) -> None:
        self.api_key = _shared_credentials.get("api_key", "")

    @task(5)
    def post_messages_short(self) -> None:
        """短消息请求（低 token）— 高频。"""
        if not self.api_key:
            return
        payload = random.choice(_MESSAGES_PAYLOADS[:2])
        self.client.post(
            "/v1/messages",
            json=payload,
            headers={"x-api-key": self.api_key},
            name="/v1/messages [short]",
        )

    @task(2)
    def post_messages_multi_turn(self) -> None:
        """多轮对话（中等 token）— 中频。"""
        if not self.api_key:
            return
        self.client.post(
            "/v1/messages",
            json=_MESSAGES_PAYLOADS[2],
            headers={"x-api-key": self.api_key},
            name="/v1/messages [multi-turn]",
        )


class AuthUser(HttpUser):
    """认证负载: POST /api/v1/auth/login — JWT 发放路径。

    权重 10%。
    """
    weight = 1
    wait_time = between(0.5, 2.0)

    @task
    def login(self) -> None:
        """测试登录端点响应时间。

        注: 登录端点有限流保护，测试中的 429 响应被标记为预期行为（不计入错误）。
        """
        resp = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": _shared_credentials.get("email", "bench@benchmark.openclaude.io"),
                "password": _shared_credentials.get("password", "benchpass"),
            },
            name="/api/v1/auth/login",
            catch_response=True,
        )
        with resp:
            # 429 是预期行为（限流正常工作），不计为错误
            if resp.status_code in (200, 429):
                resp.success()
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")


class UsageUser(HttpUser):
    """读取负载: GET /api/v1/usage/daily — DB 聚合查询。

    权重 10%。
    """
    weight = 1
    wait_time = between(0.5, 1.5)

    def on_start(self) -> None:
        token = _shared_credentials.get("token", "")
        self.headers = {"Authorization": f"Bearer {token}"}

    @task(3)
    def get_daily_usage_default(self) -> None:
        """默认 30 天范围。"""
        if not self.headers.get("Authorization", "").strip("Bearer "):
            return
        self.client.get(
            "/api/v1/usage/daily",
            headers=self.headers,
            name="/api/v1/usage/daily",
        )

    @task(1)
    def get_daily_usage_filtered(self) -> None:
        """按模型过滤。"""
        if not self.headers.get("Authorization", "").strip("Bearer "):
            return
        self.client.get(
            "/api/v1/usage/daily?model=claude-haiku-4-5-20251001",
            headers=self.headers,
            name="/api/v1/usage/daily?model=...",
        )


class MinersUser(HttpUser):
    """矿工列表负载: GET /api/v1/miners — Redis + DB 读取。

    权重 10%。
    """
    weight = 1
    wait_time = between(1.0, 3.0)

    def on_start(self) -> None:
        token = _shared_credentials.get("token", "")
        self.headers = {"Authorization": f"Bearer {token}"}

    @task(2)
    def get_miner_pool(self) -> None:
        """矿工池状态（Redis 缓存读取）。"""
        self.client.get("/api/v1/miners/pool", name="/api/v1/miners/pool")

    @task(1)
    def health_check(self) -> None:
        """Health check（基线延迟参考）。"""
        self.client.get("/health", name="/health")
