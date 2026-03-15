# OpenClade 系统架构文档

**版本：** v1.0
**最后更新：** 2026-03-15
**适用对象：** 开发者、集成方、Miner、Validator

---

## 目录

1. [架构总览](#一架构总览)
2. [请求处理流程](#二请求处理流程)
3. [核心组件说明](#三核心组件说明)
4. [Bittensor 子网集成](#四bittensor-子网集成)
5. [Validator 评分机制](#五validator-评分机制)
6. [数据流与安全边界](#六数据流与安全边界)
7. [部署架构](#七部署架构)

---

## 一、架构总览

```
┌──────────────────────────────────────────────────────────────────┐
│                        OpenClade 系统                             │
│                                                                  │
│   用户/开发者                Miner                 Validator      │
│       │                      │                       │           │
│       ▼                      ▼                       ▼           │
│  ┌─────────┐           ┌──────────┐           ┌──────────┐      │
│  │用户 Web │           │Miner Web │           │  链上    │      │
│  │控制台   │           │控制台    │           │  节点    │      │
│  └────┬────┘           └────┬─────┘           └────┬─────┘      │
│       │                     │                      │            │
│       ▼                     ▼                      │            │
│  ┌─────────────────────────────────────┐           │            │
│  │           API Gateway               │           │            │
│  │   认证 | 限流 | 负载均衡 | 日志      │           │            │
│  └─────────────────┬───────────────────┘           │            │
│                    │                               │            │
│                    ▼                               │            │
│  ┌─────────────────────────────────────┐           │            │
│  │           后端服务层                │           │            │
│  │   用户服务 | 计费 | Miner管理       │           │            │
│  └────────────┬────────────────────────┘           │            │
│               │                                    │            │
│               ▼                                    │            │
│  ┌────────────────────────┐                        │            │
│  │      路由引擎           │                        │            │
│  │  智能选择最优 Miner     │◄───────────────────────┘            │
│  └────────┬───────────────┘   Validator 评分数据               │
│           │                                                     │
│    ┌──────┼──────┐                                              │
│    ▼      ▼      ▼                                              │
│  Miner0 Miner1 MinerN                                           │
│    │      │      │                                              │
│    └──────┴──────┘                                              │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │  Anthropic      │                                            │
│  │  Claude API     │                                            │
│  └─────────────────┘                                            │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │   PostgreSQL    │  │    Redis     │  │  Bittensor Chain   │ │
│  │   主数据库      │  │  缓存/会话   │  │  链上评分/Emission │ │
│  └─────────────────┘  └──────────────┘  └────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## 二、请求处理流程

### 2.1 用户 API 调用流程

```
用户代码 → API Gateway → 路由引擎 → Miner → Claude API → 用户代码
    │            │            │          │           │
    │          认证鉴权    Miner选择   转发请求   返回响应
    │          计费扣款    健康检查   Token计量
    │          限流控制    故障切换
```

**详细步骤：**

1. **用户发起请求**
   ```http
   POST https://api.openclaude.io/v1/messages
   x-api-key: oc_your_key_here
   ```

2. **API Gateway 处理**
   - 验证 API Key 有效性
   - 检查账户余额（预扣款）
   - 应用速率限制（60 req/min）

3. **路由引擎选择 Miner**
   - 查询最近 Epoch 的 Miner 评分
   - 加权随机选择（高分 Miner 获得更多流量）
   - 跳过不健康节点（在线率 < 80%）

4. **Miner 代理请求**
   - 使用 Miner 的 Claude API Key 转发请求
   - 记录 Token 使用量（用于评分）
   - 超时/失败时自动 failover 到备用 Miner

5. **计费结算**
   - 实际扣除 Token 费用
   - 记录 Miner 贡献数据（用于下一 Epoch 评分）

### 2.2 Validator 探测流程

```
Validator → 随机选 Miner → 发送标准探针 → 验证响应质量 → 提交链上权重
     │              │              │               │
    每隔           加权           检查准确性      Yuma Consensus
   ~30min         随机           延迟/可用性      计算 Emission
```

---

## 三、核心组件说明

### 3.1 API Gateway（Nginx）

| 职责 | 实现方式 |
|------|---------|
| SSL 终止 | Nginx + Let's Encrypt |
| 认证鉴权 | JWT Token / API Key 验证 |
| 速率限制 | Nginx limit_req_zone |
| 负载均衡 | upstream 多 backend 实例 |
| 日志记录 | 结构化日志 → 监控系统 |

### 3.2 后端服务（FastAPI）

| 模块 | 文件路径 | 职责 |
|------|---------|------|
| 用户认证 | `backend/app/api/auth.py` | 注册、登录、JWT 管理 |
| API Key 管理 | `backend/app/api/api_keys.py` | 用户/Miner Key 的 CRUD |
| 计费服务 | `backend/app/services/billing.py` | Token 计量、余额扣款 |
| 路由引擎 | `backend/app/services/router.py` | Miner 选择算法 |
| 评分服务 | `backend/app/services/scoring.py` | Miner 评分计算 |
| 推荐系统 | `backend/app/api/referrals.py` | 邀请码、推荐追踪 |

### 3.3 Bittensor 子网节点

| 组件 | 文件路径 | 职责 |
|------|---------|------|
| Protocol | `subnet/neurons/protocol.py` | Miner/Validator 通信协议 |
| Miner 节点 | `subnet/neurons/miner.py` | API Key 池管理、代理转发 |
| Validator 节点 | `subnet/neurons/validator.py` | 探测评分、提交链上权重 |
| Router | `subnet/services/router.py` | 智能路由用户请求 |

### 3.4 数据存储

| 存储 | 用途 |
|------|------|
| PostgreSQL | 用户数据、Miner 信息、计费记录、Token 使用历史 |
| Redis | 会话缓存、速率限制计数器、Miner 实时评分缓存 |
| Bittensor 链 | Miner 注册信息、质押状态、链上权重、Emission 记录 |

---

## 四、Bittensor 子网集成

### 4.1 核心概念

OpenClade 在 Bittensor 网络上注册为一个**自定义子网**，实现了标准的 Bittensor 协议：

```
Bittensor 网络
└── OpenClade 子网（netuid: TBD）
    ├── Owner（子网注册者，18% Emission）
    ├── Miners（API Key 提供者，41% Emission）
    └── Validators（服务质量评分者，41% Emission）
```

### 4.2 自定义 Synapse 协议

OpenClade 定义了 `LLMAPISynapse`，在 Miner 和 Validator 之间传递标准化的 API 请求：

```python
class LLMAPISynapse(bt.Synapse):
    # 请求字段
    request_body: dict     # Claude API 请求体
    model: str             # 目标模型

    # 响应字段
    response_body: dict    # Claude API 响应体
    processing_time: float # 处理耗时（毫秒）
    error_message: str     # 错误信息（如有）
```

### 4.3 注册与初始化流程

```bash
# Miner 链上注册（PoW 工作量证明）
btcli subnet register \
  --netuid <OPENCLADE_NETUID> \
  --wallet.name default \
  --wallet.hotkey miner

# Validator 注册
btcli subnet register \
  --netuid <OPENCLADE_NETUID> \
  --wallet.name default \
  --wallet.hotkey validator

# 查看子网状态
btcli subnet metagraph --netuid <OPENCLADE_NETUID>
```

### 4.4 Emission 分发机制

```
Bittensor 网络 → 子网日 Emission（基于网络活跃度动态分配）
    │
    └── OpenClade 子网
          ├── Owner     18%  → 运营方钱包
          ├── Miners    41%  → 按 Yuma Consensus 加权分配
          └── Validators 41% → 按验证质量加权分配
```

**Yuma Consensus：** 所有 Validator 提交的 Miner 权重经过共识算法汇总，防止单一 Validator 操控评分。

---

## 五、Validator 评分机制

### 5.1 评分指标权重

| 指标 | 权重 | 测量方式 |
|------|------|---------|
| 可用性（在线率）| 20% | Miner 响应探针的比例 |
| 响应延迟 | 15% | P50/P95 端到端延迟 |
| 响应质量 | 35% | 语义相似度（vs. 参考响应）|
| 一致性 | 20% | 多次调用相同 prompt 的稳定性 |
| 效率 | 10% | Token 使用效率（避免过度冗余）|

### 5.2 准入门槛（全部满足才参与评分）

| 指标 | 最低要求 |
|------|---------|
| 探测成功率 | ≥ 90% |
| 在线率 | ≥ 80% |
| 平均延迟 | ≤ 3,000ms |
| 链上质押 | ≥ 5 TAO |

任意一项未满足 → 本 Epoch 得分 = 0

### 5.3 最终评分公式

```
最终得分 = 服务分 × (1 + 推荐加成)

服务分 = 贡献分 × W1(动态) + 待命分 × W2(动态)

贡献分 = 该 Miner 处理 Token 数 / 全网 Miner 总 Token 数
待命分 = 在线率 × 0.5 + 探测成功率 × 0.5

推荐加成 = min(推荐用户消费占比 × 2 × 30%, 30%)
```

**动态权重调整（W1/W2）：**

| 网络阶段 | W1（贡献分）| W2（待命分）|
|---------|------------|------------|
| 冷启动期（用户少）| 0.3 | 0.7 |
| 成长期 | 0.5 | 0.5 |
| 成熟期（用户多）| 0.7 | 0.3 |

### 5.4 Validator 探测流程

1. 每隔 ~30 分钟，Validator 向每个 Miner 发送标准探针请求
2. 探针使用**预设 prompt-response 对**（可验证正确答案）
3. 验证维度：响应是否完整、是否使用指定模型、延迟是否达标
4. 汇总本 Epoch 数据，计算各 Miner 权重
5. 通过 `subtensor.set_weights()` 提交链上

---

## 六、数据流与安全边界

### 6.1 API Key 安全

```
用户 API Key（oc_xxx）       Miner API Key（sk-ant-xxx）
       │                              │
       │ AES-256 加密存储             │ AES-256 加密存储
       │ 仅展示首尾几位              │ 仅展示首尾几位
       ▼                              ▼
    PostgreSQL                    PostgreSQL
  (用户身份验证)                 (路由引擎调用)
```

- 两类 Key 均加密存储，数据库管理员无法明文查看
- Miner 的 Claude API Key 只在路由引擎转发请求时临时解密使用
- 所有 API 通信强制 HTTPS

### 6.2 认证边界

| 接口 | 认证方式 | 说明 |
|------|---------|------|
| `/v1/messages` | `x-api-key: oc_xxx` | 用户 Claude 代理请求 |
| `/api/v1/*` | `Authorization: Bearer JWT` | 平台管理接口 |
| `/api/v1/miner/*` | JWT + TAO 钱包签名 | Miner 专属接口 |
| `/health` | 无需认证 | 健康检查 |
| Miner ↔ Validator | Bittensor hotkey 签名 | 链上验证 |

---

## 七、部署架构

### 7.1 Docker Compose 服务拓扑

```
docker-compose.prod.yml
├── nginx          # API Gateway（端口 80/443）
├── backend        # FastAPI 服务（可水平扩容）
├── postgres       # PostgreSQL 主库
├── redis          # Redis 缓存
└── monitoring     # Prometheus + Grafana

subnet/（独立部署）
├── miner.py       # Bittensor Miner 节点
└── validator.py   # Bittensor Validator 节点
```

### 7.2 最小生产配置

| 组件 | 最低规格 | 推荐规格 |
|------|---------|---------|
| Backend | 2 vCPU / 4GB RAM | 4 vCPU / 8GB RAM |
| PostgreSQL | 2 vCPU / 4GB RAM | 4 vCPU / 16GB RAM |
| Redis | 1 vCPU / 2GB RAM | 2 vCPU / 4GB RAM |
| Nginx | 1 vCPU / 1GB RAM | 2 vCPU / 2GB RAM |
| Miner（子网节点）| 2 vCPU / 4GB RAM | 4 vCPU / 8GB RAM |
| Validator（子网节点）| 4 vCPU / 8GB RAM | 8 vCPU / 16GB RAM |

### 7.3 快速部署

**开发环境：**
```bash
# 克隆仓库
git clone https://github.com/kydlikebtc/openclaude.git
cd openclaude

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 .env，填入必要配置

# 启动所有服务
docker-compose up -d

# 验证服务健康
curl http://localhost:8000/health
```

**生产环境：**
```bash
# 使用生产 compose 文件
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f backend
```

详细部署指南见 [运维手册](ops/scaling.md)。

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [完整技术架构](../OpenClade_Technical_Architecture.md) | 产品与技术详细设计规范（711 行）|
| [激励机制设计](incentive_mechanism.md) | 评分算法数学模型详细推导 |
| [API 参考](API_Reference.md) | 所有 API 端点文档 |
| [运维 SOP](ops/) | 生产部署、扩容、故障处理 |
| [Testnet 验证报告](testnet_validation_report.md) | 测试结果和链上验证状态 |

---

*文档版本: v1.0 | 最后更新: 2026-03-15*
