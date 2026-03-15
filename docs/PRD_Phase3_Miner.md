# OpenClade Phase 3 PRD：Miner 系统完善

**版本：** v1.0
**状态：** 正式
**作者：** Product Manager
**更新：** 2026-03-15
**关联任务：** KYD-12

---

## 一、背景与目标

### 1.1 背景

Phase 1-2 已完成后端基础设施：用户认证、API Key 管理、计费基础、Miner 注册、心跳机制和智能路由引擎。但目前 Miner 评分（`score`）硬编码为 `0.5`，推荐系统、收益统计、质量指标查询等核心功能尚未实现。

**现有代码状态：**

| 功能 | 状态 | 文件 |
|------|------|------|
| Miner 注册 | ✅ 已实现 | `api/v1/miners.py` |
| 心跳上报 | ✅ 已实现 | `api/v1/miners.py` |
| 路由引擎 | ✅ 已实现（评分固定 0.5） | `services/routing_service.py` |
| 评分引擎 | ❌ 未实现 | — |
| 收益查询 API | ❌ 未实现 | — |
| 质量指标 API | ❌ 未实现 | — |
| 推荐系统 | ❌ 未实现（DB 字段存在） | — |
| 质押管理 | ❌ 未实现 | — |
| Miner 认证（钱包签名）| ❌ 未实现 | — |
| Validator 探测器 | ❌ 未实现 | — |

### 1.2 目标

Phase 3 目标是让 Miner 系统**可运营**：
1. 基于真实数据的动态评分，驱动路由引擎公平分配流量
2. Miner 能通过 API 查看自己的收益、质量指标和推荐情况
3. Validator 探测机制上线，防止 Miner 作弊
4. 推荐系统完整可用（推荐码绑定 → 消费计入 → 加成计算）

---

## 二、用户故事

### Miner 视角

| ID | 用户故事 | 验收标准 |
|----|---------|---------|
| US-M01 | 作为 Miner，我希望通过钱包签名验证身份，而不是用邮箱密码 | 使用 Polkadot 钱包签名消息，后端验证签名，返回 JWT |
| US-M02 | 作为 Miner，我希望能查看今日/本月我的 TAO 收益 | API 返回：得分分布、处理 token 数、预估 TAO 收益 |
| US-M03 | 作为 Miner，我希望看到我的服务质量指标 | API 返回：在线率、探测成功率、平均延迟、准入门槛状态 |
| US-M04 | 作为 Miner，我希望分享推荐码，并看到推荐带来的加成 | 推荐码唯一、统计推荐用户数量和消费金额、计算当前推荐加成 |
| US-M05 | 作为 Miner，我希望添加/删除/暂停我的 Claude API Key | Key 增删改查，Key 状态可控（active/disabled） |
| US-M06 | 作为 Miner，我希望看到我的质押情况 | 返回当前质押量、是否满足准入门槛 |

### 系统视角

| ID | 用户故事 | 验收标准 |
|----|---------|---------|
| US-V01 | 作为系统，我需要每分钟探测所有在线 Miner | Validator 发送标准测试请求，记录延迟、成功率、响应质量 |
| US-V02 | 作为系统，我需要每个 Epoch（1小时）计算一次 Miner 评分 | 评分结果写入数据库，并更新 Redis 路由权重 |
| US-V03 | 作为系统，我需要检测模型降级作弊 | 响应质量低于阈值时，本轮评分归零 |
| US-V04 | 作为系统，我需要计算推荐加成并纳入最终评分 | 统计当期推荐用户有效消费，按公式计算加成 |

---

## 三、功能规格

### 3.1 Miner 身份认证

**方式：** 钱包签名验证（Substrate/Polkadot 标准）

**流程：**

```
1. Miner 请求 Challenge：GET /api/v1/miner/auth/challenge?hotkey={hotkey}
2. 后端生成随机 nonce（有效期 5 分钟），返回待签名消息：
   "Sign in to OpenClade: {nonce}"
3. Miner 使用 hotkey 对应的 coldkey 私钥签名
4. Miner 提交：POST /api/v1/miner/auth/verify { hotkey, signature }
5. 后端验证签名，返回 JWT（有效期 24 小时）
```

**API：**

```
GET /api/v1/miner/auth/challenge
  参数：hotkey (string)
  返回：{ message: string, nonce: string, expires_at: datetime }

POST /api/v1/miner/auth/verify
  Body：{ hotkey: string, signature: string, nonce: string }
  返回：{ access_token: string, token_type: "bearer" }
```

**注意事项：**
- nonce 使用后立即失效（防重放攻击）
- Miner 必须已在数据库中注册才能获得 challenge
- JWT 中包含 `miner_id` 和 `hotkey`，用于后续 API 鉴权

---

### 3.2 Miner API Key 管理

Miner 可管理其 Claude API Key 池。当前 Phase 1-2 已有 `MinerApiKey` 数据模型，本阶段补全 CRUD API。

**API：**

```
GET  /api/v1/miner/keys
  返回：List<MinerKeyResponse>
  MinerKeyResponse: { id, provider, status, key_preview (末4位), created_at, last_used_at }

POST /api/v1/miner/keys
  Body: { api_key: string, provider: "anthropic" }
  行为：加密存储、验证 Key 有效性（发一次探测请求）
  返回：MinerKeyResponse

PATCH /api/v1/miner/keys/{id}
  Body: { status: "active" | "disabled" }
  返回：MinerKeyResponse

DELETE /api/v1/miner/keys/{id}
  返回：204 No Content
```

**Key 验证逻辑：**
1. 提交 Key 后，后台发送一个 `claude-haiku` 最小请求验证 Key 可用性
2. 验证失败：返回 400，Key 不入库
3. 验证成功：加密存储，状态 `active`，写入 Redis Miner 池

**数据模型（已有，确认字段）：**

```sql
-- miner_api_keys 表（已存在）
CREATE TABLE miner_api_keys (
    id           UUID PRIMARY KEY,
    miner_id     UUID NOT NULL,
    key_encrypted TEXT NOT NULL,  -- AES-256-GCM 加密
    provider     VARCHAR(50) DEFAULT 'anthropic',
    status       VARCHAR(20) DEFAULT 'active',
    created_at   TIMESTAMP,
    updated_at   TIMESTAMP,
    last_used_at TIMESTAMP  -- 新增：需加 migration
);
```

---

### 3.3 收益查询 API

**业务逻辑：**
- 收益以 TAO 计价，但实际 TAO 分配在链上
- 后端记录的是**评分**和**处理 Token 量**，TAO 收益为估算值
- 估算公式：`预估日 TAO 收益 = 日 Emission × 41% × (Miner 评分 / 全网总分)`

**API：**

```
GET /api/v1/miner/earnings/summary
  返回：
  {
    today_score: float,
    today_tokens: int,
    today_estimated_tao: float,
    month_total_score: float,
    month_total_tokens: int,
    month_estimated_tao: float,
    current_rank: int,      // 当前评分排名
    total_miners: int       // 全网活跃 Miner 数
  }

GET /api/v1/miner/earnings/daily
  参数：days=30（最近 N 天）
  返回：List<DailyEarning>
  DailyEarning: { date, service_score, referral_bonus, final_score, tokens_processed, estimated_tao }
```

---

### 3.4 质量指标 API

**API：**

```
GET /api/v1/miner/quality/current
  返回：
  {
    online_rate: float,          // 过去 24 小时在线率
    probe_success_rate: float,   // 探测成功率
    avg_latency_ms: int,         // 平均延迟
    stake_amount: float,         // 当前质押量（TAO）

    // 准入门槛状态
    eligibility: {
      online_rate_ok: bool,      // ≥ 80%
      probe_success_ok: bool,    // ≥ 90%
      latency_ok: bool,          // ≤ 3000ms
      stake_ok: bool,            // ≥ 5 TAO
      is_eligible: bool          // 全部满足
    },

    last_updated_at: datetime
  }
```

**数据来源：** Redis（实时指标）+ 数据库（历史计算）

---

### 3.5 推荐系统

**推荐码机制（已有 `referral_code` 字段）：**
- Miner 注册时自动生成唯一推荐码（格式：`OC-XXXXXXXX`，8 位大写字母数字）
- 用户注册时可填写推荐码，绑定推荐关系（永久，不可更改）
- 每个计费 Epoch（1小时）统计推荐用户有效消费

**新增 DB 表：**

```sql
-- 推荐关系表（Phase 3 新增）
CREATE TABLE referrals (
    id         UUID PRIMARY KEY,
    user_id    UUID NOT NULL REFERENCES users(id) UNIQUE,
    miner_id   UUID NOT NULL REFERENCES miners(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 推荐统计缓存表（Epoch 级）
CREATE TABLE referral_epoch_stats (
    id         UUID PRIMARY KEY,
    miner_id   UUID NOT NULL REFERENCES miners(id),
    epoch_id   INTEGER NOT NULL,
    ref_users  INTEGER DEFAULT 0,      -- 有效推荐用户数（消费≥$5）
    ref_spend  DECIMAL(20,8) DEFAULT 0, -- 推荐用户当期消费额
    total_spend DECIMAL(20,8) DEFAULT 0,-- 全网当期消费额（冗余，便于查询）
    bonus_rate DECIMAL(10,4) DEFAULT 0, -- 计算出的推荐加成
    UNIQUE(miner_id, epoch_id)
);
```

**API：**

```
GET /api/v1/miner/referral/stats
  返回：
  {
    my_referral_code: string,
    referral_link: string,        // https://openclaude.io/r/{code}
    total_referred_users: int,    // 累计推荐用户数
    active_users_this_epoch: int, // 本期有效用户（消费≥$5）
    this_epoch_spend: float,      // 本期推荐用户消费额（USD）
    current_bonus_rate: float,    // 当前推荐加成（如 0.12 = 12%）
    top_users: List<ReferredUser> // 脱敏用户列表
  }

GET /api/v1/miner/referral/history
  参数：limit=30
  返回：List<EpochReferralStat>
```

**用户注册时绑定推荐关系：**

```
POST /api/v1/auth/register
  新增字段：referral_code (optional, string)
  行为：验证推荐码存在，写入 referrals 表
```

---

### 3.6 质押管理 API

**说明：** Phase 3 实现链下记录，Phase 5（主网）对接真实 TAO 链上质押。

```
GET /api/v1/miner/staking/info
  返回：
  {
    current_stake: float,   // 当前质押量（TAO）
    min_required: 5.0,      // 最低门槛
    is_eligible: bool,      // 是否满足质押门槛
    last_updated_at: datetime
  }

POST /api/v1/miner/staking/update
  Body: { stake_amount: float }
  说明：Phase 3 为手动更新（管理员审核），Phase 5 对接链上事件自动更新
  返回：{ stake_amount: float, updated_at: datetime }
```

---

### 3.7 评分引擎（后台服务）

**触发时机：** 每个 Epoch（60 分钟）执行一次

**计算流程：**

```python
# 伪代码，实际实现在 tasks/scoring_task.py

async def run_scoring_epoch(epoch_id: int):
    """每小时运行一次的评分任务"""

    # 1. 获取当期数据
    daily_tokens_total = await get_total_tokens_processed(period="epoch")
    all_miners = await get_active_miners()

    # 2. 动态权重
    w1, w2 = calculate_dynamic_weights(daily_tokens_total)

    # 3. 对每个 Miner 计算分数
    scores = {}
    for miner in all_miners:
        stats = await get_miner_stats(miner.id)

        # 准入检查
        if not check_eligibility(stats):
            scores[miner.id] = 0.0
            continue

        # 贡献分
        contribution = (stats.epoch_tokens / daily_tokens_total) * 100

        # 待命分
        standby = stats.online_rate * 50 + stats.probe_success_rate * 50

        # 服务分
        service_score = contribution * w1 + standby * w2

        # 推荐加成
        referral_bonus = calculate_referral_bonus(miner.id, epoch_id)

        # 最终得分（EMA 平滑）
        raw_score = service_score * (1 + referral_bonus)
        prev_score = await get_last_score(miner.id)
        final_score = 0.7 * raw_score + 0.3 * prev_score

        scores[miner.id] = final_score

    # 4. 归一化 [0, 1]
    normalized = normalize_scores(scores)

    # 5. 写入 DB + 更新 Redis 路由权重
    await save_epoch_scores(epoch_id, normalized)
    await update_redis_pool_scores(normalized)

    # 6. 计算推荐加成统计并缓存
    await aggregate_referral_stats(epoch_id)
```

**关键参数（可配置）：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `min_probe_success_rate` | 0.90 | 准入：探测成功率 |
| `min_online_rate` | 0.80 | 准入：在线率 |
| `max_avg_latency_ms` | 3000 | 准入：最大延迟 |
| `min_stake_tao` | 5.0 | 准入：最低质押 |
| `max_referral_bonus` | 0.30 | 推荐加成上限 |
| `ema_alpha` | 0.7 | EMA 平滑因子 |
| `low_usage_threshold` | 10_000_000 | W1/W2 切换下界（tokens/天） |
| `high_usage_threshold` | 500_000_000 | W1/W2 切换上界 |

---

### 3.8 Validator 探测系统

**触发时机：** 每 1-5 分钟（根据 Miner 数量动态调整）

**探测流程：**

```
1. 从 Redis Miner 池中随机选取 Miner
2. 从标准测试题库中随机选取题目
3. 发送探测请求（使用 Validator 自己的 API Key）
4. 记录：延迟、响应内容、是否超时
5. 计算响应质量分（可用性+延迟+质量+一致性+效率）
6. 将结果写入 Redis（时序数据，TTL 25 小时）
7. 每个 Epoch 汇总到数据库
```

**标准测试题库（`validator/probe_questions.json`）：**

```json
[
  {
    "type": "math",
    "prompt": "What is 847 × 293? Only output the number.",
    "expected": "248171"
  },
  {
    "type": "code",
    "prompt": "Write a Python function to reverse a string. Only code, no explanation.",
    "expected_contains": ["def", "return", "[::-1]"]
  },
  {
    "type": "fact",
    "prompt": "What is the capital of France? One word only.",
    "expected": "Paris"
  }
]
```

**Redis 存储（Validator 写入）：**

```
miner:{id}:probes (List, TTL=25h)  -- 最近探测结果
  元素：{ ts, latency_ms, success, quality_score, question_id }

miner:{id}:stats (Hash, TTL=25h)   -- 实时统计
  probe_success_rate, avg_latency_ms, online_rate
```

---

### 3.9 新增数据表（Migration 计划）

| 表名 | 用途 | 优先级 |
|------|------|--------|
| `referrals` | 推荐关系绑定 | P0 |
| `miner_epoch_scores` | 每 Epoch 评分记录 | P0 |
| `referral_epoch_stats` | 推荐统计缓存 | P1 |
| `validator_probe_logs` | 探测日志（按天分区） | P1 |

---

## 四、非功能性需求

### 4.1 性能

| 指标 | 要求 |
|------|------|
| 评分接口响应时间 | < 200ms |
| 探测任务延迟 | 不影响正常请求路由 |
| Redis 写入吞吐量 | 支持 100+ Miner 同时心跳 |

### 4.2 安全

- Miner API Key 使用 AES-256-GCM 加密存储，密钥从环境变量读取
- 钱包签名验证使用 SR25519/ED25519（Substrate 标准）
- 推荐码绑定后不可更改，防止恶意竞争
- 探测请求使用独立 Validator API Key，与 Miner 完全隔离

### 4.3 可靠性

- 评分任务失败时，保持上一 Epoch 评分（EMA 自然处理）
- 探测失败不阻塞路由（路由引擎使用 Redis 缓存评分）
- 数据库事务保证评分写入和 Redis 更新的最终一致性

---

## 五、验收标准

### Miner 认证
- [ ] 未注册 hotkey 请求 Challenge 返回 404
- [ ] nonce 5 分钟后过期，重复使用返回 401
- [ ] 签名验证失败返回 401
- [ ] 验证成功返回有效 JWT，可访问后续 Miner API

### 评分引擎
- [ ] 每小时定时任务执行，评分写入 `miner_epoch_scores`
- [ ] 准入门槛不满足的 Miner 得分为 0
- [ ] Redis 中 Miner 评分在评分任务完成后更新（路由权重同步）
- [ ] 推荐加成不超过 30%
- [ ] EMA 平滑：当期得分权重 70%，上期权重 30%

### 推荐系统
- [ ] 注册时使用无效推荐码，返回 400
- [ ] 推荐关系一旦绑定，再次绑定不同推荐码返回 409
- [ ] 消费 < $5 的推荐用户不计入推荐加成统计
- [ ] 推荐加成 API 返回正确的当期数值

### Validator 探测
- [ ] 探测任务每 5 分钟（≤20 Miner 时）执行
- [ ] 探测成功率和延迟数据正确写入 Redis
- [ ] 超时（>30 秒）的请求被标记为失败

---

## 六、技术决策

### 6.1 钱包签名库

- 使用 `py-substrate-interface` 验证 Substrate SR25519 签名
- Phase 3 先支持 Polkadot.js/SubWallet 生成的签名格式
- 后续根据 Miner 反馈扩展支持 Talisman

### 6.2 定时任务

- 使用 `apscheduler` 在 FastAPI 应用内运行定时任务
- 评分任务：`AsyncIOScheduler`，每 60 分钟
- 探测任务：`AsyncIOScheduler`，每 1-5 分钟（动态）
- 生产环境可迁移到 Celery + Redis Broker

### 6.3 推荐关系链上化

Phase 3 使用数据库记录，Phase 5 主网上线时：
- 在 Bittensor 链上通过自定义 extrinsic 记录推荐关系
- 链上记录作为最终权威，链下数据库作为缓存

---

## 七、开发排期估算

| 模块 | 估算（工作日） | 依赖 |
|------|--------------|------|
| Miner 钱包认证 | 3天 | `py-substrate-interface` |
| Miner Key CRUD API | 2天 | — |
| 收益/质量 API | 2天 | 评分引擎 |
| 推荐系统 DB + API | 3天 | — |
| 质押管理 API | 1天 | — |
| 评分引擎（定时任务） | 4天 | Validator 探测数据 |
| Validator 探测器 | 4天 | — |
| 数据库 Migrations | 1天 | — |
| 测试 | 3天 | 所有模块 |
| **合计** | **~23天** | |

---

*文档版本: v1.0 | 最后更新: 2026-03-15*
