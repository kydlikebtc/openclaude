# OpenClade 产品与技术架构设计

## 完整技术规划文档

---

## 目录

1. [系统总体架构](#一系统总体架构)
2. [用户端 Web 应用](#二用户端-web-应用)
3. [Miner 端 Web 应用](#三miner-端-web-应用)
4. [Dashboard 数据大盘](#四dashboard-数据大盘)
5. [核心后端系统](#五核心后端系统)
6. [API 撮合与路由系统](#六api-撮合与路由系统)
7. [子网链上逻辑](#七子网链上逻辑)
8. [数据库设计](#八数据库设计)
9. [部署架构](#九部署架构)
10. [开发计划与排期](#十开发计划与排期)

---

## 一、系统总体架构

### 1.1 架构总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        OpenClade 系统架构                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      前端层 (Frontend)                              │ │
│  │                                                                     │ │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │ │
│  │   │ User Portal │  │Miner Portal │  │  Dashboard  │               │ │
│  │   │  用户端     │  │  Miner端    │  │   管理后台  │               │ │
│  │   └─────────────┘  └─────────────┘  └─────────────┘               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      网关层 (API Gateway)                           │ │
│  │                                                                     │ │
│  │   • SSL终止  • 认证鉴权  • 限流熔断  • 负载均衡  • 日志记录        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      服务层 (Services)                              │ │
│  │                                                                     │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│ │
│  │  │用户服务  │ │Miner服务 │ │计费服务  │ │评分服务  │ │推荐服务  ││ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘│ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                   核心层 (Routing Engine)                           │ │
│  │                                                                     │ │
│  │  ┌──────────────────────────────────────────────────────────────┐ │ │
│  │  │              API 撮合与路由引擎                                │ │ │
│  │  │                                                               │ │ │
│  │  │  请求接收 → 智能路由 → Miner选择 → 请求转发 → 响应聚合      │ │ │
│  │  │                                                               │ │ │
│  │  │  • Miner池管理  • 健康检查  • 故障切换  • 指标收集           │ │ │
│  │  └──────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│           ┌────────────────────────┼────────────────────────┐           │
│           │                        │                        │           │
│           ▼                        ▼                        ▼           │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐       │
│  │   PostgreSQL    │   │     Redis       │   │   消息队列      │       │
│  │   主数据库      │   │   缓存/会话     │   │  Redis Streams  │       │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘       │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    链上层 (Blockchain)                              │ │
│  │                                                                     │ │
│  │  ┌──────────────────────────────────────────────────────────────┐ │ │
│  │  │                  TAO Subnet (Bittensor)                       │ │ │
│  │  │                                                               │ │ │
│  │  │  • Miner注册  • Validator评分  • Emission分发  • 质押管理    │ │ │
│  │  └──────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     外部层 (External)                               │ │
│  │                                                                     │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │ │
│  │  │ Claude API  │  │  支付网关   │  │  通知服务   │               │ │
│  │  │ (Anthropic) │  │(Crypto/Fiat)│  │ (Email/TG)  │               │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈选型

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| **前端** | Next.js 14 + TypeScript | SSR支持，SEO友好 |
| **UI组件** | Tailwind CSS + shadcn/ui | 快速开发，美观统一 |
| **后端框架** | Python FastAPI | 高性能异步，OpenAPI支持 |
| **数据库** | PostgreSQL 15 | 可靠，功能丰富 |
| **缓存** | Redis 7 | 高性能KV存储 |
| **消息队列** | Redis Streams | 轻量级消息处理 |
| **API网关** | Nginx | 反向代理，限流 |
| **容器化** | Docker + Compose | 开发部署一致性 |
| **监控** | Prometheus + Grafana | 指标监控可视化 |
| **链上** | Python + Bittensor SDK | TAO子网开发 |

---

## 二、用户端 Web 应用

### 2.1 功能模块

#### 1. 认证模块
- 邮箱注册 (含推荐码)
- 邮箱登录
- 找回密码
- 邮箱验证

#### 2. API Key 管理
- 创建 API Key (命名，可设过期时间)
- 查看 Key 列表
- 复制 Key
- 删除/禁用 Key
- 查看单个 Key 用量

#### 3. 充值与账单
- 当前余额显示
- 快捷充值 ($10/$50/$100/自定义)
- 支付方式: USDT, USDC, TAO
- 充值记录
- 消费明细

#### 4. 用量统计
- 用量趋势图 (最近30天)
- 今日/本月/总计用量
- 按模型用量明细
- 按 Key 用量明细
- 导出功能

#### 5. API 文档
- 快速开始指南
- API 参考 (兼容 Claude 官方格式)
- 代码示例 (Python, JavaScript, cURL)
- SDK 下载

#### 6. 账户设置
- 个人信息修改
- 密码修改
- 通知设置 (余额预警)
- 推荐信息

### 2.2 页面结构

```
user.openclade.io
│
├── / (首页/Landing)
├── /auth
│   ├── /login
│   ├── /register (含推荐码)
│   └── /forgot-password
├── /dashboard (需登录)
├── /api-keys
├── /billing
│   ├── /recharge
│   └── /history
├── /usage
├── /docs
│   ├── /quickstart
│   ├── /api-reference
│   └── /examples
└── /settings
```

### 2.3 用户端 API 接口

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **认证** | POST | `/api/v1/auth/register` | 用户注册 |
| | POST | `/api/v1/auth/login` | 用户登录 |
| | POST | `/api/v1/auth/logout` | 退出登录 |
| | GET | `/api/v1/auth/me` | 获取当前用户 |
| **API Key** | GET | `/api/v1/api-keys` | 获取Key列表 |
| | POST | `/api/v1/api-keys` | 创建新Key |
| | DELETE | `/api/v1/api-keys/{id}` | 删除Key |
| **充值** | GET | `/api/v1/billing/balance` | 获取余额 |
| | POST | `/api/v1/billing/recharge` | 发起充值 |
| | GET | `/api/v1/billing/transactions` | 交易记录 |
| **用量** | GET | `/api/v1/usage/summary` | 用量汇总 |
| | GET | `/api/v1/usage/daily` | 每日用量 |
| | GET | `/api/v1/usage/by-model` | 按模型统计 |

---

## 三、Miner 端 Web 应用

### 3.1 功能模块

#### 1. Miner 注册与认证
- 钱包连接 (Polkadot.js, SubWallet, Talisman)
- 质押 TAO (≥5 TAO)
- 提交 Claude API Key
- 等待验证

#### 2. API Key 管理
- 添加 Claude API Key
- Key 状态监控 (活跃/已封禁)
- Key 验证
- 并发限制设置

#### 3. 收益与统计
- 今日收益 / 总收益
- 今日处理请求数 / Token数
- 收益趋势图
- 收益明细 (日期, 服务分, 推荐加成, 最终得分, TAO)

#### 4. 服务质量监控
- 在线率
- 探测成功率
- 平均延迟
- 准入门槛状态

#### 5. 推荐系统
- 我的推荐码
- 推荐链接
- 推荐用户数 / 活跃用户数
- 当期推荐消费 / 占比
- 当前推荐加成
- 推荐用户列表 (脱敏)

#### 6. 质押管理
- 当前质押
- 增加/减少质押
- 退出 Miner
- 质押历史

### 3.2 页面结构

```
miner.openclade.io
│
├── / (首页/Landing)
├── /auth
│   ├── /connect-wallet
│   └── /register
├── /dashboard (需连接钱包)
├── /keys
├── /earnings
├── /quality
├── /referral
├── /staking
└── /docs
```

### 3.3 Miner 端 API 接口

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **认证** | POST | `/api/v1/miner/auth/connect` | 钱包签名验证 |
| | POST | `/api/v1/miner/auth/register` | Miner 注册 |
| **Key管理** | GET | `/api/v1/miner/keys` | 获取 Key 列表 |
| | POST | `/api/v1/miner/keys` | 添加 Key |
| | DELETE | `/api/v1/miner/keys/{id}` | 删除 Key |
| **收益** | GET | `/api/v1/miner/earnings/summary` | 收益汇总 |
| | GET | `/api/v1/miner/earnings/daily` | 每日收益 |
| **质量** | GET | `/api/v1/miner/quality/current` | 当前质量指标 |
| **推荐** | GET | `/api/v1/miner/referral/code` | 获取推荐码 |
| | GET | `/api/v1/miner/referral/stats` | 推荐统计 |
| **质押** | GET | `/api/v1/miner/staking/balance` | 质押余额 |
| | POST | `/api/v1/miner/staking/increase` | 增加质押 |

---

## 四、Dashboard 数据大盘

### 4.1 功能模块

#### 1. 核心指标概览
- 今日请求数 / Token数 / 收入 / 成本
- 活跃用户 / 活跃Miner / 日Emission / TAO价格

#### 2. 实时流量监控
- 请求量实时曲线
- 当前QPS / 峰值QPS / 平均延迟

#### 3. Miner 状态监控
- Miner 列表 (状态, 在线率, 成功率, 延迟, 得分, 收益)
- 总Miner / 合格Miner / 不合格Miner

#### 4. 用户统计
- 用户增长趋势
- 用户消费分布
- 总用户 / 付费用户 / 新增用户 / 留存率

#### 5. 财务报表
- 收入支出趋势
- 本月收入 / 支出 / 利润 / 利润率
- TAO Emission 收入明细

#### 6. 推荐系统统计
- 推荐用户总数 / 推荐消费总额
- Top 10 推荐 Miner 排行榜

#### 7. 告警中心
- 最近告警列表
- 告警确认

### 4.2 Dashboard API 接口

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **概览** | GET | `/api/v1/admin/overview` | 核心指标 |
| **流量** | GET | `/api/v1/admin/traffic/realtime` | 实时流量 |
| **Miner** | GET | `/api/v1/admin/miners` | Miner列表 |
| | GET | `/api/v1/admin/miners/stats` | Miner统计 |
| **用户** | GET | `/api/v1/admin/users/stats` | 用户统计 |
| **财务** | GET | `/api/v1/admin/finance/summary` | 财务汇总 |
| **告警** | GET | `/api/v1/admin/alerts` | 告警列表 |

---

## 五、核心后端系统

### 5.1 目录结构

```
backend/
├── app/
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置管理
│   │
│   ├── api/v1/                 # API 路由
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── api_keys.py
│   │   ├── billing.py
│   │   ├── miners.py
│   │   ├── referral.py
│   │   └── admin.py
│   │
│   ├── api/claude/             # Claude API 代理
│   │   └── proxy.py
│   │
│   ├── services/               # 业务服务
│   │   ├── user_service.py
│   │   ├── miner_service.py
│   │   ├── billing_service.py
│   │   ├── scoring_service.py
│   │   └── referral_service.py
│   │
│   ├── models/                 # 数据模型
│   │   ├── user.py
│   │   ├── api_key.py
│   │   ├── miner.py
│   │   └── ...
│   │
│   └── db/                     # 数据库
│       ├── database.py
│       └── redis.py
│
├── routing_engine/             # 路由引擎
│   ├── router.py
│   ├── pool_manager.py
│   ├── health_checker.py
│   └── failover.py
│
├── validator/                  # Validator
│   ├── prober.py
│   ├── verifier.py
│   └── scorer.py
│
└── tasks/                      # 定时任务
    ├── scoring_task.py
    └── stats_aggregation.py
```

---

## 六、API 撮合与路由系统

### 6.1 系统架构

```
用户请求 → API Gateway → 认证验证 → 余额检查 → 路由引擎 → Miner选择 → 请求转发 → Claude API
                                                                              ↓
用户响应 ← 格式转换 ← 响应聚合 ← 计费记录 ←─────────────────────────────── 响应结果
```

### 6.2 智能路由算法

```python
class SmartRouter:
    async def select_miner(self, request):
        # 1. 获取支持该模型的在线 Miner
        candidates = await self.get_model_miners(request.model)
        
        # 2. 筛选合格 Miner (在线, 有余量, 心跳正常)
        qualified = [m for m in candidates if self.is_qualified(m)]
        
        # 3. 加权随机选择 (评分高的概率大)
        weights = [m.score ** 2 for m in qualified]
        selected = random.choices(qualified, weights=weights)[0]
        
        return selected
```

### 6.3 Miner 池 Redis 结构

```
miner:pool (Sorted Set)      - 按评分排序的在线 Miner
miner:{id}:info (Hash)       - Miner 详细信息
miner:{id}:keys (List)       - Miner 的 API Key 列表
miner:model:{name} (Set)     - 按模型分类的 Miner
```

### 6.4 故障处理

- 最多重试 3 次
- 每次选择不同的 Miner
- 指数退避重试间隔
- Key 失效自动标记

---

## 七、子网链上逻辑

### 7.1 代码结构

```
subnet/
├── openclade/
│   ├── base/
│   │   └── neuron.py
│   ├── miner/
│   │   ├── miner.py
│   │   └── forward.py
│   ├── validator/
│   │   ├── validator.py
│   │   ├── prober.py
│   │   └── scorer.py
│   └── protocol/
│       └── synapse.py
│
├── neurons/
│   ├── miner.py
│   └── validator.py
│
└── scripts/
    ├── register_subnet.py
    └── register_miner.py
```

### 7.2 评分计算核心逻辑

```python
class Scorer:
    ELIGIBILITY = {
        'min_probe_success_rate': 0.90,
        'min_online_rate': 0.80,
        'max_avg_latency_ms': 3000,
        'min_stake': 5.0,
    }
    MAX_REFERRAL_BONUS = 0.30
    
    def calculate_scores(self, miner_stats):
        scores = {}
        for uid, stats in miner_stats.items():
            # 1. 准入检查
            if not self._check_eligibility(stats):
                scores[uid] = 0.0
                continue
            
            # 2. 服务分
            service_score = self._calculate_service_score(stats)
            
            # 3. 推荐加成
            referral_bonus = self._calculate_referral_bonus(stats)
            
            # 4. 最终得分
            scores[uid] = service_score * (1 + referral_bonus)
        
        return self._normalize_scores(scores)
```

---

## 八、数据库设计

### 8.1 核心表结构

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    balance DECIMAL(20, 8) DEFAULT 0,
    referred_by_miner_id UUID,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Key 表
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Miner 表
CREATE TABLE miners (
    id UUID PRIMARY KEY,
    wallet_address VARCHAR(100) UNIQUE NOT NULL,
    hotkey VARCHAR(100) UNIQUE NOT NULL,
    stake DECIMAL(20, 8) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    referral_code VARCHAR(20) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Claude Key 表
CREATE TABLE claude_keys (
    id UUID PRIMARY KEY,
    miner_id UUID REFERENCES miners(id),
    key_encrypted TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    supported_models TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用量日志表 (按天分区)
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    api_key_id UUID REFERENCES api_keys(id),
    miner_id UUID REFERENCES miners(id),
    model VARCHAR(50) NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost DECIMAL(20, 8) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Miner 评分表
CREATE TABLE miner_scores (
    id UUID PRIMARY KEY,
    miner_id UUID REFERENCES miners(id),
    epoch INTEGER NOT NULL,
    service_score DECIMAL(10, 4),
    referral_bonus DECIMAL(10, 4),
    final_score DECIMAL(10, 4),
    UNIQUE(miner_id, epoch)
);

-- 推荐关系表
CREATE TABLE referrals (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) UNIQUE,
    miner_id UUID REFERENCES miners(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 九、部署架构

### 9.1 Docker Compose 配置

```yaml
version: '3.8'

services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [postgres, redis]
    deploy:
      replicas: 2

  routing-engine:
    build: ./routing_engine
    ports: ["8001:8001"]
    depends_on: [redis]

  postgres:
    image: postgres:15
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    volumes: [redis_data:/data]

  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    depends_on: [api, routing-engine]

  prometheus:
    image: prom/prometheus

  grafana:
    image: grafana/grafana
```

---

## 十、开发计划与排期

### 10.1 MVP 开发计划 (8周)

| 阶段 | 时间 | 内容 |
|------|------|------|
| **Phase 1** | Week 1-2 | 基础设施: 项目搭建, 数据库设计, 认证系统 |
| **Phase 2** | Week 3-4 | 核心功能: Claude API 代理, 路由引擎, 计费系统 |
| **Phase 3** | Week 5-6 | Miner系统: 注册管理, 健康检查, 评分系统, 推荐系统 |
| **Phase 4** | Week 7-8 | 前端开发: 用户端, Miner端, Dashboard, 测试部署 |

### 10.2 子网开发计划 (4周)

| 阶段 | 时间 | 内容 |
|------|------|------|
| **Week 9-10** | 子网基础 | 注册子网, Protocol定义, Miner节点开发 |
| **Week 11-12** | Validator | 探测器, 评分器, 权重设置, 链上链下集成 |

### 10.3 功能优先级

**P0 (必须有)**
- Claude API 代理
- 用户注册登录
- API Key 管理
- 基础计费
- Miner 注册
- 基础路由
- 基础评分

**P1 (应该有)**
- 推荐系统
- Dashboard
- 详细统计报表
- 告警系统

**P2 (可以有)**
- 信用卡支付
- 高级分析
- 导出功能

---

## 附录

### A. 核心配置参数

```python
class Settings:
    # 定价
    price_ratio: float = 0.25  # 25% of official price
    
    # Miner 评分参数
    min_probe_success_rate: float = 0.90
    min_online_rate: float = 0.80
    max_avg_latency_ms: int = 3000
    min_stake_tao: float = 5.0
    max_referral_bonus: float = 0.30
    
    # 路由参数
    max_retries: int = 3
    request_timeout: int = 300
```

### B. Claude API 代理接口

```
POST /v1/messages

Request:
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 1024,
  "messages": [{"role": "user", "content": "Hello!"}]
}

Response: 完全兼容 Claude 官方格式
```

---

## 总结

| 维度 | 内容 |
|------|------|
| **产品** | 用户端 + Miner端 + Dashboard |
| **后端** | FastAPI + PostgreSQL + Redis |
| **前端** | Next.js + TypeScript + Tailwind |
| **子网** | Bittensor SDK |
| **开发周期** | MVP 8周 + 子网 4周 = 12周 |

---

*文档版本: v1.0*
