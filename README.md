# OpenClade

> 基于 Bittensor TAO 子网的分布式 Claude API 服务网络

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Bittensor](https://img.shields.io/badge/Network-Bittensor-blue)](https://bittensor.com)
[![Claude API](https://img.shields.io/badge/API-Anthropic%20Claude-orange)](https://anthropic.com)

---

## 项目愿景

OpenClade 是一个去中心化的 Claude API 服务网络，基于 Bittensor 协议构建。

**核心主张：**
- **用户**：以官方价格 25-35% 的成本使用 Claude 最新模型
- **矿工（Miner）**：将闲置 Claude API Key 变现，获得 TAO 挖矿收益
- **验证者（Validator）**：评估服务质量，维护网络诚信，获得 TAO 分红
- **生态**：推动 AI API 服务的去中心化与普惠化

---

## 技术架构

### 系统总览

```
用户请求 (OpenAI 兼容格式)
    │
    ▼
OpenClade API Gateway
    │  • 认证鉴权 • 限流 • 负载均衡
    ▼
路由引擎 (Smart Router)
    │  • 基于 Miner 历史评分 • 加权随机选择
    ├──────────────────────────────────┐
    ▼                                  ▼
Miner 节点 0                     Miner 节点 N
  Axon 服务器                      Axon 服务器
    │  • 调用 Claude API              │
    │  • API Key 池轮转               │
    ▼                                  ▼
Anthropic Claude API             Anthropic Claude API
    │                                  │
    └──────────────┬───────────────────┘
                   ▼
         Validator 验证节点
           • 定期抽样验证
           • 多维度评分
           • 提交权重到链上
                   │
                   ▼
        Bittensor 区块链
           • Yuma Consensus
           • TAO Emission 分发
```

### Bittensor 子网协议层

OpenClade 实现了一个自定义的 `LLMAPISynapse`，兼容 Bittensor 标准协议：

| 组件 | 文件 | 职责 |
|------|------|------|
| Protocol | `neurons/protocol.py` | 定义 Miner/Validator 间的通信 Synapse |
| Miner | `neurons/miner.py` | 代理 Claude API 请求，管理 API Key 池 |
| Validator | `neurons/validator.py` | 评分 Miner 响应质量，提交链上权重 |
| Router | `services/router.py` | 智能路由用户请求到最优 Miner |

### 激励机制

子网日 Emission 三方分配：

```
TAO Emission
├── Owner   18%  — 子网运营方纯利润
├── Miners  41%  — 按评分比例分配给矿工
└── Validators 41% — 按验证质量分配给验证者
```

**矿工评分公式：**

```
最终得分 = 服务分 × (1 + 推荐加成)

服务分 = 贡献分 × W1 + 待命分 × W2
  贡献分 = Miner处理的Token占全网比例（动态权重，随网络使用量上升）
  待命分 = 在线率 × 0.5 + 探测成功率 × 0.5

推荐加成 = min(推荐用户消费占比 × 2 × 30%, 30%)
```

**准入门槛（全部满足才可获得收益）：**

| 指标 | 阈值 |
|------|------|
| 探测成功率 | ≥ 90% |
| 在线率 | ≥ 80% |
| 平均延迟 | ≤ 3,000ms |
| 最低质押 | ≥ 5 TAO |

---

## 快速开始

### 系统要求

- Python 3.10+
- bittensor >= 7.0.0
- anthropic >= 0.40.0

### 矿工节点部署

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_ORG/openclaude.git
cd openclaude

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 Claude API Key
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY

# 4. 注册到子网（需要有 TAO）
python scripts/register_miner.py \
  --netuid <OPENCLADE_NETUID> \
  --wallet.name <your_wallet> \
  --wallet.hotkey <your_hotkey>

# 5. 启动矿工
python neurons/miner.py \
  --netuid <OPENCLADE_NETUID> \
  --wallet.name <your_wallet> \
  --wallet.hotkey <your_hotkey> \
  --subtensor.network finney
```

### 用户 API 接入

OpenClade 提供完全兼容 Anthropic 官方格式的 API：

```python
import anthropic

# 只需替换 base_url，代码零改动
client = anthropic.Anthropic(
    api_key="your-openclaude-api-key",
    base_url="https://api.openclaude.io",
)

message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "你好！"}],
)
print(message.content[0].text)
```

---

## 开发路线图

### Phase 1 — 基础子网（M1-M2）
- [x] 商业计划与技术架构设计
- [ ] Bittensor 子网注册（测试网）
- [ ] 基础 Miner/Validator 实现
- [ ] LLMAPISynapse 协议定义
- [ ] Claude API 代理核心逻辑

### Phase 2 — 激励系统（M3-M4）
- [ ] 多维度评分引擎
- [ ] 权重提交与 Yuma Consensus 集成
- [ ] API Key 池分布式管理
- [ ] Miner 收益追踪看板

### Phase 3 — 用户平台（M4-M5）
- [ ] 用户注册/充值/计费系统
- [ ] API Key 管理界面
- [ ] 使用量统计与账单
- [ ] 推荐系统（Referral）

### Phase 4 — 主网上线（M6）
- [ ] 安全审计
- [ ] 主网子网注册（300 TAO）
- [ ] 矿工招募计划
- [ ] 正式上线

---

## 项目结构

```
openclaude/
├── neurons/
│   ├── miner.py          # 矿工启动脚本
│   ├── validator.py      # 验证者启动脚本
│   └── protocol.py       # Synapse 协议定义
├── services/
│   ├── router.py         # 智能路由引擎
│   ├── scorer.py         # Miner 评分系统
│   └── key_pool.py       # API Key 池管理
├── api/
│   └── gateway.py        # 用户 API 网关
├── scripts/
│   ├── register_subnet.py
│   ├── register_miner.py
│   └── register_validator.py
├── tests/
├── docs/
│   ├── incentive_mechanism.md  # 激励机制详细设计
│   └── api_reference.md
├── OpenClade_Business_Plan.md
├── OpenClade_Technical_Architecture.md
├── requirements.txt
└── .env.example
```

---

## 相关文档

- [商业计划书](./OpenClade_Business_Plan.md)
- [技术架构设计](./OpenClade_Technical_Architecture.md)
- [激励机制详细设计](./docs/incentive_mechanism.md)（即将发布）
- [Bittensor 官方文档](https://docs.bittensor.com/)
- [子网创建指南](https://docs.learnbittensor.org/subnets/create-a-subnet)

---

## 参与贡献

欢迎提交 Issue 和 PR！请先阅读 [贡献指南](./CONTRIBUTING.md)。

---

## 许可证

MIT License — 详见 [LICENSE](./LICENSE)
