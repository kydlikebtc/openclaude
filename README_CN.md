<p align="center">
  <img src="https://img.shields.io/badge/OpenClade-%E5%8E%BB%E4%B8%AD%E5%BF%83%E5%8C%96%20Claude%20API-8B5CF6?style=for-the-badge&logoColor=white" alt="OpenClade">
</p>

<h1 align="center">OpenClade</h1>

<p align="center">
  <strong>基于 Bittensor 的去中心化 Claude API 服务网络</strong>
</p>

<p align="center">
  以官方价格 25-35% 的成本使用 Claude 最新模型，由去中心化矿工网络和 Bittensor TAO 激励驱动。
</p>

<p align="center">
  <a href="https://github.com/kydlikebtc/openclaude/actions"><img src="https://img.shields.io/github/actions/workflow/status/kydlikebtc/openclaude/ci.yml?branch=main&style=for-the-badge&label=CI" alt="CI"></a>
  <a href="https://github.com/kydlikebtc/openclaude/releases"><img src="https://img.shields.io/github/v/release/kydlikebtc/openclaude?include_prereleases&style=for-the-badge" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License"></a>
  <a href="https://bittensor.com"><img src="https://img.shields.io/badge/Network-Bittensor-000000?style=for-the-badge" alt="Bittensor"></a>
  <a href="https://anthropic.com"><img src="https://img.shields.io/badge/API-Anthropic%20Claude-D97706?style=for-the-badge" alt="Claude API"></a>
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="docs/Architecture.md">系统架构</a> · <a href="docs/User_Guide.md">用户指南</a> · <a href="docs/Miner_Guide.md">矿工指南</a> · <a href="docs/API_Reference.md">API 参考</a>
</p>

---

## 什么是 OpenClade？

OpenClade 是一个基于 [Bittensor](https://bittensor.com) 协议构建的去中心化 Claude API 服务网络。它连接需要低成本 Claude 模型访问的用户和贡献 API Key 赚取 TAO 奖励的矿工。

| 参与方 | 价值 |
|---|---|
| **用户** | 以官方定价 **25-35%** 的成本使用 Claude 最新模型 |
| **矿工** | 将闲置 Claude API Key 变现，获得 TAO 挖矿收益 |
| **验证者** | 评估服务质量，维护网络诚信，获得 TAO 分红 |

---

## 核心特性

- **无缝接入** — 兼容 OpenAI SDK 格式，只需替换 `base_url` 即可接入
- **智能路由** — 基于矿工评分的加权选择引擎，将请求路由至最优节点
- **多维评分** — 从延迟、在线率、探测成功率、贡献量等维度综合评估矿工
- **链上激励** — 通过 Bittensor Yuma Consensus 分发 TAO 收益
- **推荐系统** — 矿工推荐新用户可获得额外权重加成
- **全链路可观测** — Prometheus + Grafana 监控栈，配备 SLO 告警
- **充分测试** — 后端 247 个测试通过，覆盖率 98.61%

---

## 系统架构

```
用户请求（OpenAI 兼容格式）
    │
    ▼
OpenClade API 网关
    │  认证鉴权 · 限流 · 负载均衡
    ▼
智能路由引擎
    │  基于矿工评分的加权选择
    ├──────────────────────────────┐
    ▼                              ▼
矿工节点 0                    矿工节点 N
  Axon 服务器                    Axon 服务器
    │  代理 Claude API 请求        │
    │  API Key 池轮转              │
    ▼                              ▼
Anthropic Claude API          Anthropic Claude API
    │                              │
    └──────────────┬───────────────┘
                   ▼
         验证者节点
           · 定期抽样探测
           · 多维度评分
           · 提交权重到链上
                   │
                   ▼
        Bittensor 区块链
           · Yuma Consensus
           · TAO Emission 分发
```

### TAO 收益分配

```
TAO Emission
├── 子网运营方   18%  — 运营纯利润
├── 矿工        41%  — 按评分比例分配
└── 验证者      41%  — 按验证质量分配
```

---

## 快速开始

### 用户 — API 接入

```python
import anthropic

# 只需替换 base_url，代码零改动
client = anthropic.Anthropic(
    api_key="your-openclade-api-key",
    base_url="https://api.openclade.io",
)

message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "你好！"}],
)
print(message.content[0].text)
```

### 矿工 — 节点部署

```bash
# 1. 克隆仓库
git clone https://github.com/kydlikebtc/openclaude.git
cd openclaude/subnet

# 2. 安装依赖
uv sync

# 3. 配置
cp config/miner.example.yaml config/miner.yaml
# 编辑 miner.yaml：填入 ANTHROPIC_API_KEY 和钱包信息

# 4. 注册到子网（需要 TAO）
uv run python scripts/register_miner.py \
  --netuid <OPENCLADE_NETUID> \
  --wallet.name <your_wallet> \
  --wallet.hotkey <your_hotkey>

# 5. 启动矿工
uv run python neurons/miner.py --config config/miner.yaml
```

### 系统要求

- Python 3.11+
- bittensor >= 10.0.0
- anthropic >= 0.40.0

---

## 矿工评分机制

矿工必须**同时满足**以下所有阈值才能获得收益：

| 指标 | 阈值 |
|---|---|
| 探测成功率 | >= 90% |
| 在线率 | >= 80% |
| 平均延迟 | <= 3,000ms |
| 最低质押 | >= 5 TAO |

**评分公式：**

```
最终得分 = 服务分 × (1 + 推荐加成)

服务分 = 贡献分 × W1 + 待命分 × W2
  贡献分 = Miner 处理的 Token 占全网比例
  待命分 = 在线率 × 0.5 + 探测成功率 × 0.5

推荐加成 = min(推荐用户消费占比 × 2 × 30%, 30%)
```

---

## 开发路线图

| 阶段 | 状态 | 描述 |
|---|---|---|
| **Phase 1** — 基础子网 | 已完成 | Miner/Validator 节点、LLMAPISynapse 协议、Claude API 代理 |
| **Phase 2** — 激励系统 | 已完成 | 多维度评分、Yuma Consensus、API Key 池管理 |
| **Phase 3** — 用户平台 | 已完成 | 注册充值、计费系统、API Key 管理、使用量统计、推荐系统 |
| **Phase 4** — 安全加固 | 已完成 | OWASP Top 10 审计、JWT 认证强化、限流、输入验证 |
| **Phase 5** — 可观测性 | 已完成 | Prometheus + Grafana、SLO 告警、结构化日志、100% 测试覆盖率 |
| **Phase 6** — Testnet 部署 | 进行中 | 钱包创建完成、本地 E2E 验证通过、等待子网注册 |
| **Phase 7** — 主网准备 | 规划中 | 生产部署、矿工招募、正式上线 |

---

## 项目结构

```
openclaude/
├── subnet/                    # Bittensor 子网核心
│   ├── neurons/               # Miner 和 Validator 节点
│   ├── protocol/              # LLMAPISynapse 协议定义
│   ├── miner/                 # Miner 配置与 Key 池
│   ├── validator/             # 评分引擎
│   ├── scripts/               # 注册脚本
│   ├── config/                # 示例配置
│   └── tests/                 # 121 个单元测试（100% 覆盖率）
├── backend/                   # FastAPI 后端
│   └── app/
│       ├── api/v1/            # REST API 路由
│       └── services/          # 业务逻辑层
├── frontend/                  # Next.js 前端
│   └── src/app/
│       ├── (user)/            # 用户控制台
│       ├── (miner)/           # 矿工看板
│       └── (admin)/           # 管理后台
├── monitoring/                # Prometheus + Grafana 配置
├── docs/                      # 文档目录
├── docker-compose.yml
└── docker-compose.prod.yml
```

---

## 相关文档

| 文档 | 描述 |
|---|---|
| [系统架构](docs/Architecture.md) | 系统架构与设计 |
| [API 参考](docs/API_Reference.md) | REST API 文档 |
| [用户入门指南](docs/User_Guide.md) | 用户快速上手 |
| [矿工上手指南](docs/Miner_Guide.md) | 矿工部署与运维 |
| [激励机制详设](docs/incentive_mechanism.md) | 评分与奖励机制设计 |
| [上线检查清单](docs/Launch_Checklist.md) | 上线前验证清单 |
| [商业计划书](OpenClade_Business_Plan.md) | 商业模式与财务预测 |

---

## 参与贡献

欢迎提交 Issue 和 PR！请先阅读 [贡献指南](CONTRIBUTING.md)。

---

## 许可证

[MIT License](LICENSE)
