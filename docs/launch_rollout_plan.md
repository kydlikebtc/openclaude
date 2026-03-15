# OpenClade 主网灰度发布计划

**版本：** v1.0
**最后更新：** 2026-03-16
**关联 Issue：** KYD-55
**状态：** 草稿 — 待 Engineering 和 CEO 审批

---

## 概述

本文档定义 OpenClade 主网上线的分阶段灰度发布策略。目标是通过受控流量逐步扩展，在每个阶段验证系统稳定性，确保发现问题时可以快速回退，避免一次性全量上线带来的不可控风险。

**发布总历时：** 约 60 天（Month 2+ 进入稳定运营）

---

## 阶段总览

```
Day 0-3     Phase 1: 内部测试   ─ 受邀 5-10 人，QPS 上限 50
Day 4-14    Phase 2: 私测       ─ Waitlist 前 100 名，QPS 上限 500
Day 15-45   Phase 3: 公测       ─ 开放注册，QPS 上限 2,000
Month 2+    Phase 4: 全量       ─ 移除限制，正式 SLA
```

**晋级规则：** 每个阶段达到持续稳定运行的量化标准后，才可进入下一阶段。不强制按时间推进，稳定性优先。

---

## Phase 1：内部测试

**时间：** Day 0-3（可延长至 Day 5）
**目标：** 验证端到端流程正确，暴露明显的配置问题和部署问题

### 用户与流量

| 参数 | 值 |
|------|-----|
| 用户数量 | 5-10 人（内部团队 + 受邀测试者） |
| 每日 QPS 上限 | 50 QPS |
| 单用户 Rate Limit | 10 req/min |
| 单请求 max_tokens 上限 | 4,096 |

### Miner 网络

| 参数 | 值 |
|------|-----|
| 最少 Miner 数量 | 2 个 |
| 最多 Miner 数量 | 5 个 |
| Miner 准入标准 | 团队内部或受信任合作伙伴 |

### 监控阈值（触发暂停晋级）

| 指标 | 正常范围 | 暂停晋级阈值 |
|------|---------|------------|
| API 错误率 | < 1% | **≥ 5%** |
| 503 错误率 | < 5% | **≥ 20%** |
| P95 响应时间（路由层） | < 500ms | **≥ 2,000ms** |
| 计费准确率 | 100% | **< 99%** |

### 验收标准（晋级到 Phase 2 的条件）

- [ ] 连续 24 小时零严重错误（P0/P1）
- [ ] 计费金额与实际 Token 用量误差 < 0.1%
- [ ] API Key 创建、使用、余额扣减完整流程验证通过
- [ ] 所有部署配置确认（域名、SSL、Nginx、数据库备份）

### Feature Flag 配置

```python
# backend 环境变量 / .env.prod
ROLLOUT_PHASE=1
MAX_DAILY_QPS=50
MAX_RPM_PER_USER=10
MAX_TOKENS_PER_REQUEST=4096
ALLOWED_USER_EMAILS=["team@openclade.io", "tester1@...", ...]  # 白名单模式
REGISTRATION_OPEN=false
```

---

## Phase 2：私测（Closed Beta）

**时间：** Day 4-14（约 10 天，可延长）
**目标：** 验证系统在真实用户场景下的稳定性，发现 Miner 网络的早期问题

### 用户与流量

| 参数 | 值 |
|------|-----|
| 用户数量 | Waitlist 前 100 名（批次邀请） |
| 邀请节奏 | Day 4-6: 前 30 人；Day 7-10: 前 70 人；Day 11-14: 前 100 人 |
| 每日 QPS 上限 | 500 QPS |
| 单用户 Rate Limit | 60 req/min（默认值） |
| 单请求 max_tokens 上限 | 8,192 |

> **分批邀请说明：** 不一次性全量邀请，留出 24-48 小时观察窗口，确认每批用户接入正常后再邀请下一批。

### Miner 网络

| 参数 | 值 |
|------|-----|
| 最少 Miner 数量 | 5 个 |
| 推荐 Miner 数量 | 10-15 个 |
| Miner 准入标准 | 正常注册流程（开放 Miner 注册） |

### 监控阈值（触发暂停晋级）

| 指标 | 正常范围 | 暂停晋级阈值 | 立即回退阈值 |
|------|---------|------------|------------|
| API 错误率 | < 2% | **≥ 5%** | **≥ 15%** |
| 503 错误率 | < 5% | **≥ 15%** | **≥ 30%** |
| P95 响应时间 | < 1,000ms | **≥ 3,000ms** | **≥ 8,000ms** |
| 计费异常投诉 | 0 | **≥ 1 起未解决** | — |
| 可用 Miner 数量 | ≥ 5 | **< 3** | **< 2** |

### 验收标准（晋级到 Phase 3 的条件）

- [ ] 连续 7 天 P95 延迟 < 1,500ms
- [ ] API 错误率持续低于 2%
- [ ] Miner 网络稳定维持 ≥ 8 个活跃节点
- [ ] 至少 50 名用户完成首次充值并成功调用 API
- [ ] 推荐系统、计费查询、API Key 管理无已知严重 Bug

### Feature Flag 配置

```python
ROLLOUT_PHASE=2
MAX_DAILY_QPS=500
MAX_RPM_PER_USER=60
MAX_TOKENS_PER_REQUEST=8192
REGISTRATION_OPEN=false           # 仍为白名单
WAITLIST_INVITE_BATCH_SIZE=30     # 每批邀请人数
```

---

## Phase 3：公测（Open Beta）

**时间：** Day 15-45（约 30 天）
**目标：** 验证系统在规模化用户和流量下的性能，为全量做准备

### 用户与流量

| 参数 | 值 |
|------|-----|
| 用户数量 | 无限制（开放注册） |
| 新用户增速限制 | 前 7 天每日最多新增 200 个注册账户 |
| 每日 QPS 上限 | 2,000 QPS |
| 单用户 Rate Limit | 60 req/min（默认）；可申请提升至 300 req/min |
| 单请求 max_tokens 上限 | 32,768（全量开放） |

> **参考依据：** 负载测试在 Docker macOS 环境（受限网络环境）下 100 并发零错误；生产 Linux 裸机环境预计实际可支撑 500+ QPS 无问题，2,000 QPS 作为保守上限。

### Miner 网络

| 参数 | 值 |
|------|-----|
| 最少 Miner 数量 | 15 个 |
| 推荐 Miner 数量 | 30-50 个 |
| 健康度指标 | 探测成功率全网均值 ≥ 90% |

### 监控阈值

| 指标 | 正常范围 | 暂停推进阈值 | 立即触发回退 |
|------|---------|------------|------------|
| API 错误率（5分钟窗口） | < 2% | **≥ 5%** | **≥ 10%，持续 10 分钟** |
| 503 错误率 | < 3% | **≥ 10%** | **≥ 20%，持续 5 分钟** |
| P95 端到端延迟 | < 1,500ms | **≥ 3,000ms** | **≥ 6,000ms，持续 15 分钟** |
| 可用 Miner 数量 | ≥ 15 | **< 10** | **< 5** |
| 数据库连接池使用率 | < 60% | **≥ 80%** | **≥ 95%** |
| Redis 内存使用率 | < 70% | **≥ 85%** | **≥ 95%** |

### 验收标准（晋级到 Phase 4 的条件）

- [ ] 连续 14 天 API 错误率 < 2%
- [ ] P95 延迟持续 < 1,500ms
- [ ] 成功处理单日峰值 ≥ 1,500 QPS 的流量
- [ ] Miner 网络稳定维持 ≥ 25 个活跃节点
- [ ] 没有未解决的计费相关投诉
- [ ] 完成 1 次完整的灾难恢复演练（数据库故障切换）

### Feature Flag 配置

```python
ROLLOUT_PHASE=3
MAX_DAILY_QPS=2000
MAX_RPM_PER_USER=60              # 默认值
MAX_RPM_PER_USER_ELEVATED=300    # 申请后可提升
MAX_TOKENS_PER_REQUEST=32768
REGISTRATION_OPEN=true
NEW_USER_DAILY_CAP=200           # 每日新注册上限（前7天）
NEW_USER_DAILY_CAP_AFTER=1000    # 第8天起放开
```

---

## Phase 4：全量（General Availability）

**时间：** Month 2+（无固定截止日期）
**目标：** 正式生产环境，提供 SLA 保障

### 用户与流量

| 参数 | 值 |
|------|-----|
| 用户数量 | 无限制 |
| QPS 上限 | 无强制限制（依赖 Miner 网络容量） |
| Rate Limit | 用户自定义（按套餐） |

### 正式 SLA

| 指标 | 承诺 |
|------|------|
| 月度可用性 | ≥ 99.0%（允许每月约 7.3 小时停机） |
| P95 延迟（路由层） | < 500ms |
| 故障响应时间 | P0 故障 30 分钟内响应 |

> **注意：** 早期（Phase 4 前 3 个月）可用性目标为"尽力而为"，正式 SLA 在稳定运营 90 天后生效。

### Miner 网络

| 参数 | 值 |
|------|-----|
| 最少 Miner 数量 | 30 个 |
| 健康度指标 | 探测成功率全网均值 ≥ 95% |

### Feature Flag 配置

```python
ROLLOUT_PHASE=4
MAX_DAILY_QPS=0             # 0 = 不限制
MAX_RPM_PER_USER=0          # 依赖用户套餐配置
MAX_TOKENS_PER_REQUEST=0    # 不限制
REGISTRATION_OPEN=true
NEW_USER_DAILY_CAP=0        # 不限制
```

---

## 回退策略

### 回退触发条件

任意以下条件触发**立即回退**到上一阶段：

| 条件 | 说明 |
|------|------|
| API 错误率 > 10%，持续 10 分钟 | 严重服务质量问题 |
| 503 错误率 > 20%，持续 5 分钟 | Miner 网络严重不足 |
| 计费系统错误 | 任何导致用户多扣费/少扣费的 Bug |
| 数据库不可用 | 主库崩溃且自动切换失败 |
| 安全事件 | 数据泄露、未授权访问等 |

### 回退操作

```bash
# 回退到 Phase 2（示例）
# 1. 更新环境变量
ROLLOUT_PHASE=2
MAX_DAILY_QPS=500
REGISTRATION_OPEN=false

# 2. 重启后端服务（零停机重启）
docker compose -f docker-compose.prod.yml up -d --no-deps backend

# 3. 更新 Nginx 配置（如需关闭注册入口）
# 在 Nginx config 中添加 /register 302 到 /waitlist

# 4. 通知（按优先级）
# - Discord 公告（1 分钟内）
# - 正在处理中的请求等待自然结束（不强制中断）
```

### 回退决策树

```
检测到告警
    │
    ├─ 是否影响计费准确性？
    │       ├─ 是 → 立即暂停所有新充值入口，通知 CEO
    │       └─ 否 → 继续评估
    │
    ├─ 错误持续时间 < 5 分钟？
    │       ├─ 是 → 观察，记录日志，等待
    │       └─ 否 → 进入回退流程
    │
    ├─ 是否有 Miner 扩容能力？
    │       ├─ 是 → 紧急联系 Miner，等待扩容（30 分钟窗口）
    │       └─ 否 → 立即回退到上一阶段
    │
    └─ 回退到上一阶段后是否恢复？
            ├─ 是 → 维持回退状态，分析根因，制定修复计划
            └─ 否 → 考虑完全关闭服务，通知 CEO 和用户
```

---

## Backend 实现指南

> 本节供 Backend Engineer 参考，直接实现流量控制机制。

### 1. 阶段配置通过环境变量控制

```python
# backend/app/core/config.py 新增字段
class Settings(BaseSettings):
    # Rollout 控制
    rollout_phase: int = 1              # 当前阶段：1, 2, 3, 4
    max_daily_qps: int = 50             # 0 = 不限制
    max_rpm_per_user: int = 10          # 每用户每分钟请求数
    max_tokens_per_request: int = 4096  # 单请求 token 上限，0 = 不限制
    registration_open: bool = False     # 是否开放注册
    new_user_daily_cap: int = 0         # 每日新注册上限，0 = 不限制
```

### 2. 全局 QPS 限制（Redis 滑动窗口）

```python
# backend/app/middleware/rate_limit.py
async def check_global_qps(redis_client, settings):
    """全局 QPS 限制，使用 Redis 滑动窗口计数"""
    if settings.max_daily_qps == 0:
        return True  # Phase 4 不限制

    key = f"global:qps:{datetime.utcnow().strftime('%Y%m%d%H%M')}"  # 按分钟
    current = await redis_client.incr(key)
    await redis_client.expire(key, 120)  # 2分钟 TTL

    # 换算：max_daily_qps → 每分钟上限（乘以60，但不做平滑）
    per_minute_limit = settings.max_daily_qps * 60 / 1000  # 保守估计

    if current > per_minute_limit:
        raise HTTPException(status_code=503, detail="Service temporarily at capacity")
    return True
```

### 3. 用户级 Rate Limit（已有基础，需增加动态配置）

现有路由引擎已有 Rate Limit 机制，需将 `max_rpm_per_user` 从硬编码改为从 `settings` 读取：

```python
# 现有代码中找到 rate limit 逻辑，替换硬编码值
# 修改前：if request_count > 60:
# 修改后：if request_count > settings.max_rpm_per_user:
```

### 4. 注册开关

```python
# backend/app/api/v1/auth.py
@router.post("/register")
async def register(user_data: UserCreate, settings: Settings = Depends(get_settings)):
    if not settings.registration_open:
        raise HTTPException(
            status_code=403,
            detail="Registration is currently by invitation only. Join our waitlist."
        )
    # ... 现有注册逻辑
```

### 5. max_tokens 限制

```python
# backend/app/api/v1/proxy.py
async def proxy_to_claude(request_body: dict, settings: Settings = Depends(get_settings)):
    max_tokens_limit = settings.max_tokens_per_request
    if max_tokens_limit > 0 and request_body.get("max_tokens", 0) > max_tokens_limit:
        raise HTTPException(
            status_code=400,
            detail=f"max_tokens exceeds current limit of {max_tokens_limit}. Contact support to increase."
        )
    # ... 现有代理逻辑
```

---

## 监控与告警配置

### Grafana 告警规则（对应 KYD-43 已有 Grafana 配置）

每个阶段应激活以下告警：

| 告警名称 | 表达式 | 阈值（Phase 2/3） | 触发行动 |
|---------|--------|-----------------|---------|
| `HighErrorRate` | 5 分钟滚动错误率 | ≥ 5% / ≥ 10% | Slack #alerts + PagerDuty |
| `HighLatency` | P95 端到端延迟 | ≥ 3s / ≥ 6s | Slack #alerts |
| `LowMinerCount` | 活跃 Miner 数 | < 3 / < 5 | Slack #alerts + 紧急联系 Miner |
| `BillingAnomaly` | 每小时计费异常率 | ≥ 0.1% | 立即通知 CEO |
| `DBConnectionSaturation` | 连接池使用率 | ≥ 80% / ≥ 95% | Slack #alerts |

### 状态页

所有阶段均应维护公开状态页（推荐 statuspage.io 或自建），在回退时第一时间更新状态。

---

## Miner 扩容节奏

| 时间节点 | 目标 Miner 数 | 主要来源 | 行动 |
|---------|--------------|---------|------|
| Phase 1 Day 0 | 2-5 | 团队内部 | 团队成员提交 API Key 测试 |
| Phase 2 Day 4 | ≥ 5 | 受邀 Miner | 向 TAO 社区定向邀请 5-10 名早期 Miner |
| Phase 2 Day 7 | ≥ 10 | 早期社区 | Discord 公告 Miner 招募，发放前 20 名 Miner 奖励 |
| Phase 3 Day 15 | ≥ 20 | 公开招募 | 正式开放 Miner 注册，发布 Miner Guide |
| Phase 3 Day 30 | ≥ 35 | 自然增长 | 推荐奖励激励现有 Miner 拉新 Miner |
| Phase 4 | ≥ 50 | 持续招募 | 通过 TAO 社区、KOL 合作持续扩张 |

**Miner 扩容应急预案：**
如果可用 Miner 数量低于阶段最低要求，按以下顺序操作：
1. 立即在 Discord Miner 频道发出"急需 Miner"公告
2. 联系前 10 名已注册但不活跃的 Miner，了解原因
3. 临时提高 Miner Emission 分配比例（需链上操作，联系 CEO）
4. 如果 30 分钟内无法补充，启动阶段回退流程

---

## 沟通计划

### 用户沟通（每次晋级时）

- Discord 公告（提前 24 小时通知晋级时间）
- 邮件通知 Waitlist 用户（Phase 2 邀请时）
- 官网状态页更新

### 回退沟通（立即）

```
[OpenClade Status] We're temporarily reducing traffic limits due to [reason].
Current status: Phase X → Phase Y
Estimated resolution: [time estimate or TBD]
All existing API calls are unaffected. New requests may receive 503.
Updates: discord.gg/openclade
```

---

## 附录：Phase 对照速查表

| 维度 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|------|---------|---------|---------|---------|
| 用户入口 | 白名单 | Waitlist 邀请 | 开放注册 | 开放注册 |
| 日 QPS 上限 | 50 | 500 | 2,000 | 无限制 |
| Rate Limit | 10 req/min | 60 req/min | 60 req/min | 按套餐 |
| max_tokens | 4,096 | 8,192 | 32,768 | 无限制 |
| 最少 Miner | 2 | 5 | 15 | 30 |
| SLA | 无 | 无 | 尽力而为 | 99.0% |
| 持续时间 | 3-5 天 | 10-14 天 | 30 天 | 持续 |

---

*本文档需要 CEO 和 Founding Engineer 审批后方可作为执行依据。*
