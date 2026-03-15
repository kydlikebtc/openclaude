# OpenClade Subnet — Testnet 部署报告

**生成时间**: 2026-03-15
**任务**: KYD-22 Phase 7: 真实 Testnet 部署
**状态**: 代码就绪，等待 Testnet TAO 充值

---

## 一、部署摘要

### 已完成工作

| 步骤 | 状态 | 说明 |
|------|------|------|
| Testnet 连接验证 | ✅ 完成 | 成功连接，当前区块 6,689,396 |
| bittensor v10 API 兼容性修复 | ✅ 完成 | `bt.subtensor` → `bt.Subtensor` 等 CamelCase 更新 |
| 钱包创建 | ✅ 完成 | owner / validator / miner 三个钱包 |
| 配置文件创建 | ✅ 完成 | validator.testnet.yaml, miner.testnet.yaml |
| 本地端到端验证 | ✅ 全部通过 | 6/6 验证项通过 |
| 单元测试 | ✅ 121/121 通过 | 0 失败 |
| 子网注册 | ⏳ 等待 TAO | 需要 ~100 testnet TAO |
| Validator 节点启动 | ⏳ 等待注册 | 需要 netuid |
| Miner 节点启动 | ⏳ 等待注册 | 需要 netuid + Anthropic API key |

---

## 二、钱包地址

> 警告：这些是 Testnet 钱包，助记词不应提交到 git。

| 角色 | 钱包名称 | Coldkey SS58 | Hotkey SS58 |
|------|---------|--------------|-------------|
| 子网所有者 | openclaude-owner | `5HgLWLo5BHkQVjRpp7M27p8YCoupdQeYRqz8gUKRqsHtMEkC` | `5Epk2PvePwvqxXXY7XYsS9v3K5jE71h2Z8932i35SEYM6iEy` |
| 验证者 | openclaude-validator/validator | `5DcZeL6VwxB3aTEEdCjyH2TG1d1B1w4xUBYKSMh6MMG1Npgk` | `5F9Sy8xFv31WQ3rmeK37yyc6NGX716mpmdjja2xsB4iqcQCa` |
| 矿工 | openclaude-miner/miner | `5D32sBgdoTqXNbrd89iqfxJsBFY5uF8U7E3aMvycGJ8b8W9G` | `5CtHfKsVfdrAbJk1LHVcS3astwR4RnDV8Qy6gVRjgeUsCvca` |

**当前余额**: 所有钱包 0 TAO（需从 Discord faucet 充值）

---

## 三、Testnet 连接信息

- **网络**: Bittensor Testnet (finney/test)
- **连接成功**: ✅
- **当前区块**: 6,689,396（2026-03-15 21:15）
- **bittensor SDK 版本**: 10.1.0
- **Python 版本**: 3.11.12

---

## 四、代码变更记录

### bittensor v10 API 兼容性修复

| 文件 | 旧 API (v8) | 新 API (v10) |
|------|------------|-------------|
| `neurons/miner.py` | `bt.wallet()` | `bt.Wallet()` |
| `neurons/miner.py` | `bt.subtensor()` | `bt.Subtensor()` |
| `neurons/miner.py` | `bt.metagraph()` | `bt.Metagraph()` |
| `neurons/miner.py` | `bt.axon()` | `bt.Axon()` |
| `neurons/miner.py` | `subtensor.register()` | `subtensor.burned_register()` |
| `neurons/validator.py` | `bt.wallet(config)` | `bt.Wallet(config)` |
| `neurons/validator.py` | `bt.subtensor(config)` | `bt.Subtensor(config)` |
| `neurons/validator.py` | `bt.dendrite()` | `bt.Dendrite()` |
| `neurons/validator.py` | `bt.wallet.add_args()` | `bt.Wallet.add_args()` |
| `neurons/validator.py` | `bt.subtensor.add_args()` | `bt.Subtensor.add_args()` |
| `scripts/register_subnet.py` | `bt.subtensor()` | `bt.Subtensor()` |
| `scripts/register_subnet.py` | `bt.wallet()` | `bt.Wallet()` |

---

## 五、本地验证结果

```
✓ PASS  synapse_protocol       — Synapse 协议创建/哈希/验证
✓ PASS  probe_generator        — 探测任务生成和矿工选择调度
✓ PASS  scoring_engine         — 多维评分引擎（可用性/延迟/质量/一致性/效率）
✓ PASS  trust_weight_calculator — Yuma 共识对齐权重处理
✓ PASS  full_epoch_cycle       — 完整 epoch 循环（探测→评分→权重→提交就绪）
✓ PASS  testnet_connectivity   — Testnet 网络连接 (block=6,689,396)

单元测试: 121/121 PASSED (0 failures)
```

---

## 六、待执行部署步骤（需要 TAO）

### Step 1: 获取 Testnet TAO

前往 Bittensor Discord → `#testnet-faucet` 频道，请求向以下地址充值：

```
充值地址: 5HgLWLo5BHkQVjRpp7M27p8YCoupdQeYRqz8gUKRqsHtMEkC
需要金额: ~100 TAO（用于子网注册）
网络: Bittensor Testnet
```

### Step 2: 注册子网

```bash
cd /Users/kyd/openclaude/subnet
uv run python scripts/register_subnet.py \
  --wallet.name openclaude-owner \
  --wallet.hotkey default \
  --network test \
  --register-subnet \
  --verify
```

**预期输出**:
```
Subnet registered successfully | netuid=<N>
SUBNET NETUID: <N> (save this for your config files)
Subnet state | netuid=<N> | n_neurons=0 | block=...
```

**操作**: 记录 netuid 并更新以下文件：
- `config/validator.testnet.yaml`: 将 `FILL_IN_AFTER_SUBNET_REGISTRATION` 替换为实际 netuid
- `config/miner.testnet.yaml`: 将 `netuid: 1` 替换为实际 netuid

### Step 3: 启动 Validator 节点

```bash
cd /Users/kyd/openclaude/subnet
uv run python neurons/validator.py \
  --wallet.name openclaude-validator \
  --wallet.hotkey validator \
  --subtensor.network test \
  --netuid <NETUID>
```

**验收标准**:
- [ ] Validator 热密钥注册成功
- [ ] Metagraph 同步成功（n > 0）
- [ ] 权重提交日志出现（每 100 块一次）

### Step 4: 启动 Miner 节点

```bash
cd /Users/kyd/openclaude/subnet
# 更新 config/miner.testnet.yaml 中的 netuid 和 api_keys
# 或使用环境变量
export OPENCLAUDE_API_KEYS="sk-ant-api03-YOUR_KEY_HERE"

uv run python neurons/miner.py --config config/miner.testnet.yaml
```

**验收标准**:
- [ ] Miner 热密钥注册成功
- [ ] Axon 在端口 8091 开始监听
- [ ] 接收到 Validator 探测请求
- [ ] Claude API 调用成功返回
- [ ] 获得评分和 TAO 发放

### Step 5: 端到端链路验证

```bash
# 验证完整链路（在 Validator 和 Miner 都运行时）
uv run python scripts/validate_e2e_local.py
```

**期望结果**:
- Validator → Miner 探测延迟 P95 < 5s
- Miner 评分 > 0.3（基础阈值）
- 权重上链确认（`Weight submission confirmed on chain`）

---

## 七、监控确认

### Prometheus 指标端点

- Validator: `http://localhost:9100/metrics`（如已配置）
- Miner: `http://localhost:9101/metrics`（如已配置）

### 关键日志模式

成功的 Validator 运行：
```
OpenCladeValidator initialized | netuid=<N> | hotkey=5F9Sy8...
Epoch start | miners=1 | probing=1 | tasks=4
Submitting weights | block=... | non-zero=1/1 | sum=1.0000
Weight submission confirmed on chain
```

成功的 Miner 运行：
```
OpenCladeMiner initialized | netuid=<N> | wallet=5CtHfK...
Axon serving on port 8091 | Ctrl+C to stop
forward() success | request_id=... | tokens=... | latency=...ms
```

---

## 八、阻塞项

| 阻塞项 | 描述 | 所有者 | 解决路径 |
|--------|------|-------|---------|
| Testnet TAO | 0 TAO，无法注册子网 | CEO/PM | Discord #testnet-faucet 或通过 Bittensor 团队 |
| Anthropic API Key | 需要真实 API key 运行 Miner | CEO | 在 console.anthropic.com 创建或提供现有 key |

---

## 九、技术架构回顾

```
用户 API 请求
    ↓
OpenClade 后端 (FastAPI)
    ↓
Bittensor Dendrite (Validator 端)
    ↓  [LLMAPISynapse: model, messages, max_tokens]
Miner Axon (端口 8091)
    ↓
Anthropic Claude API
    ↓  [response, tokens_used, latency_ms]
Miner 返回 Synapse
    ↓
Validator 评分 (可用性 20% + 延迟 15% + 质量 35% + 一致性 20% + 效率 10%)
    ↓
Trust Weight Calculator (Yuma 对齐)
    ↓
subtensor.set_weights() — 每 100 块
    ↓
Yuma Consensus → TAO 发放给 Miner
```

---

*本报告由 Blockchain Engineer Agent 生成 | KYD-22 Phase 7*
