# OpenClade Testnet 全链路验证报告

**日期**: 2026-03-15
**任务**: KYD-28 — Testnet 全链路验证: Miner + Validator + Emission
**执行**: Blockchain Engineer Agent
**状态**: 验证完成（代码层） / 部分链上验证待人工执行

---

## 执行摘要

OpenClade 子网代码库经过全面的自动化测试验证，所有核心组件在**模拟链上环境**中全部通过。
实际 Bittensor Testnet 链上操作（注册、质押、Emission 分配）需要运营人员配置真实钱包和 Testnet TAO 后方可执行。

### 验证结果概览

| 验证类别 | 测试项数 | 通过 | 失败 | 状态 |
|---------|--------|------|------|------|
| 子网单元测试 | 121 | 121 | 0 | ✅ 全通过 |
| 后端 E2E 全链路 | 36 | 36 | 0 | ✅ 全通过 |
| 后端单元/集成测试 | 178 | 178 | 0 | ✅ 全通过 (3 skipped) |
| **合计** | **335** | **335** | **0** | ✅ |
| Testnet 链上注册 | 1 | — | — | ⏳ 待人工执行 |
| Testnet TAO 质押 | 1 | — | — | ⏳ 待人工执行 |
| Axon 服务器连通 | 1 | — | — | ⏳ 待部署执行 |
| 链上权重提交 | 1 | — | — | ⏳ 待部署执行 |
| Emission 分配验证 | 1 | — | — | ⏳ 待部署执行 |

---

## 第一部分：Miner 全流程验证

### 1.1 Miner 代码实现

**文件**: `subnet/neurons/miner.py`

| 功能模块 | 实现状态 | 验证方式 |
|--------|---------|---------|
| 钱包初始化 (`bt.wallet`) | ✅ 实现 | 单元测试 |
| Subtensor 连接 | ✅ 实现 | 代码审查 |
| Metagraph 同步 | ✅ 实现 | 代码审查 |
| API Key 池管理 | ✅ 实现 | 17 个单元测试全通过 |
| Axon 服务器启动 | ✅ 实现 | 代码审查 |
| 黑名单过滤（stake 检查） | ✅ 实现 | 单元测试 |
| 请求优先级（stake-weighted） | ✅ 实现 | 单元测试 |
| Claude API 代理转发 | ✅ 实现 | E2E mock 测试 |
| 认证错误处理 | ✅ 实现 | `TestAPIKeyPool::test_release_auth_error_*` |
| 限速错误处理 | ✅ 实现 | API pool 单元测试 |
| 链上注册 (PoW) | ✅ 实现 | 代码审查 |

**关键测试用例验证**:
```
✅ test_acquire_returns_none_when_all_quarantined    # 所有 key 耗尽时拒绝请求
✅ test_round_robin_across_keys                      # 多 key 轮询调度
✅ test_10_failures_marks_exhausted                 # 失败熔断
✅ test_release_auth_error_uses_longer_delay        # Auth 错误隔离时间更长
✅ test_exponential_backoff_increases_delay         # 指数退避
```

### 1.2 Miner 配置（Testnet 准备就绪）

**文件**: `subnet/config/miner.example.yaml`

```yaml
subtensor_network: "test"   # ✅ 已配置为 testnet
axon_port: 8091             # ✅ 默认端口设置
min_stake_tao: 5.0          # ✅ 安全阈值已设置
```

### 1.3 Miner 注册脚本

**文件**: `subnet/scripts/register_subnet.py`

| 功能 | 状态 |
|-----|------|
| 余额检查 | ✅ 已实现 |
| 子网注册 (`register_subnetwork`) | ✅ 已实现 |
| 矿工/验证者热键注册 | ✅ 已实现 |
| 错误处理 + 日志 | ✅ 已实现 |
| 安全审计（不存储私钥）| ✅ 已验证 |

### 1.4 E2E Miner 流程测试结果

```
✅ test_miner_register_basic
✅ test_miner_re_registration_updates_status
✅ test_miner_register_with_referral
✅ test_miner_pool_status_reflects_registration
✅ test_miner_challenge_response_auth
✅ test_miner_me_endpoint_after_auth
✅ test_miner_auth_unknown_hotkey
✅ test_miner_heartbeat_records_latency
✅ test_miner_score_endpoint_returns_components
✅ test_miner_score_improves_after_good_latency
✅ test_miner_api_key_management
✅ test_routing_uses_miner_with_best_score
```

---

## 第二部分：Validator 全流程验证

### 2.1 Validator 代码实现

**文件**: `subnet/neurons/validator.py`

| 功能模块 | 实现状态 | 验证方式 |
|--------|---------|---------|
| Dendrite 初始化 | ✅ 实现 | 代码审查 |
| Metagraph 同步 | ✅ 实现 | 单元测试 |
| 探针任务生成 | ✅ 实现 | 8 个单元测试通过 |
| 矿工探测（dendrite.forward）| ✅ 实现 | 代码审查 |
| 评分引擎 | ✅ 实现 | 32 个单元测试通过 |
| Trust 权重计算 | ✅ 实现 | 14 个单元测试通过 |
| Yuma 共识对齐 | ✅ 实现 | `TrustWeightCalculator.process()` |
| 链上权重提交 | ✅ 实现 | 代码审查 |
| 动态探测间隔 | ✅ 实现 | `test_small/medium/large_network_*_interval` |

### 2.2 评分引擎验证

**权重分配** (匹配 `docs/incentive_mechanism.md §4.2`):

| 维度 | 权重 | 验证状态 |
|-----|------|---------|
| 可用性 | 20% | ✅ `TestScoreAvailability` 3 tests passed |
| 延迟 | 15% | ✅ `TestScoreLatency` 6 tests passed |
| 响应质量 | 35% | ✅ `TestScoreQuality` 5 tests passed |
| 一致性 | 20% | ✅ `TestConsistencyScoring` 5 tests passed |
| 效率 | 10% | ✅ `TestScoreEfficiency` 4 tests passed |

**EMA 平滑验证**:
```
✅ test_ema_smoothing_applied    # smooth = 0.7 × raw + 0.3 × prev
```

**模型降级检测**:
```
✅ test_opus_to_haiku_flagged    # Opus → Haiku 降级被检测
✅ test_sonnet_to_haiku_flagged  # Sonnet → Haiku 降级被检测
```

### 2.3 Yuma 共识对齐验证

**文件**: `subnet/validator/trust.py`

| 功能 | 状态 |
|-----|------|
| 本地权重归一化 | ✅ 6 tests passed |
| 分位数剪枝（低分矿工）| ✅ 3 tests passed |
| 最大权重上限 | ✅ 2 tests passed |
| 提交可行性检查 | ✅ 4 tests passed |
| SDK 委托回退 | ✅ 2 tests passed |

### 2.4 探测频率验证

| 网络规模 | 探测间隔 | 验证状态 |
|--------|---------|---------|
| < 20 矿工 | 5 分钟 | ✅ 通过 |
| 20-100 矿工 | 2 分钟 | ✅ 通过 |
| > 100 矿工 | 1 分钟 | ✅ 通过 |

---

## 第三部分：Emission 分配验证

### 3.1 文档规范

**文件**: `docs/incentive_mechanism.md`

| Emission 分配 | 规范值 | 实现状态 |
|-------------|--------|---------|
| Owner (subnet owner) | 18% | 由 Bittensor 协议自动执行 |
| Miner 池 | 41% | 按评分权重分配，代码已实现 |
| Validator 池 | 41% | Yuma 共识处理，代码已实现 |

### 3.2 权重到 Emission 链路

```
评分 → smooth_score → scores_to_weights() → 归一化 → TrustWeightCalculator →
→ subtensor.set_weights() → Yuma Consensus → Emission 分配
```

该链路经过 `test_weights_sum_to_one`、`test_proportional_weights` 等测试验证。

### 3.3 链上 Emission 实际验证（待执行）

> **注意**: Emission 实际分配需要 Testnet 上进行多个 epoch 的运行，需要以下前提条件：
> - 子网已注册（Testnet netuid 已分配）
> - 至少 1 个 Miner + 1 个 Validator 在线
> - Validator 成功提交权重至少 1 次

---

## 第四部分：端到端用户流程验证

### 4.1 完整用户链路

**测试文件**: `backend/tests/test_e2e_full_chain.py`

```
用户注册 → 充值余额 → 创建 API Key → 发送 Claude API 请求 →
→ 路由到 Miner → Miner 代理到 Anthropic → 返回结果 → 扣费记录
```

| 测试用例 | 状态 |
|--------|------|
| 完整链路注册→调用→扣费 | ✅ 通过 |
| 余额不足返回 402 | ✅ 通过 |
| 无可用矿工返回 503 | ✅ 通过 |
| 无效 API Key 返回 401 | ✅ 通过 |
| 缺少 API Key 返回 401 | ✅ 通过 |

### 4.2 计费精度验证

```
✅ test_haiku_billing_rate              # Haiku 计费费率正确
✅ test_transaction_recorded_after_api_call  # 调用后交易记录正确
```

### 4.3 Admin 监控链路

```
✅ test_admin_can_see_all_users
✅ test_regular_user_cannot_access_admin
✅ test_admin_can_suspend_user
✅ test_admin_sees_transactions_after_api_call
✅ test_admin_can_view_miner_pool_status
✅ test_usage_summary_reflects_api_calls
```

---

## 第五部分：代码质量与安全审计

### 5.1 安全检查

| 安全项 | 状态 |
|------|------|
| 私钥不硬编码 | ✅ 使用环境变量 / YAML 配置 |
| 注册脚本不记录私钥 | ✅ 已验证 |
| API Key 存储安全（哈希）| ✅ 已实现 |
| Validator Blacklist（stake 最低限制）| ✅ min_stake_tao=5.0 |
| 模型降级惩罚（分数归零）| ✅ 已实现 |
| 响应完整性校验（SHA-256 hash）| ✅ 已实现 |

### 5.2 协议版本控制

```python
PROTOCOL_VERSION = "1.0.0"  # 版本不兼容时 Validator 拒绝旧响应
```

```
✅ test_default_protocol_version
✅ test_validate_response_hash_fails_on_tamper
```

---

## 第六部分：Mainnet 就绪度评估

### 6.1 技术就绪度

| 组件 | 就绪度 | 说明 |
|-----|--------|------|
| Miner 节点代码 | 95% | 待真实 Testnet 端到端验证 |
| Validator 节点代码 | 95% | 待真实 Testnet 端到端验证 |
| 评分机制 | 100% | 121 tests all pass |
| 后端 API | 95% | 178 tests pass，覆盖率 68% (低于80%目标) |
| 协议定义 | 100% | 完整实现，版本控制 |
| 注册脚本 | 90% | 代码完备，待 Testnet 实际执行 |
| 监控/报警 | 80% | Prometheus 配置就绪，待部署验证 |

### 6.2 需要人工执行的 Testnet 验证步骤

以下步骤需运营团队在有实际 Testnet TAO 的环境中执行：

```bash
# Step 1: 注册子网（消耗约 100 Testnet TAO）
python scripts/register_subnet.py \
  --wallet.name owner --wallet.hotkey owner \
  --network test --register-subnet

# Step 2: 复制配置文件并填入真实 API Key
cp config/miner.example.yaml config/miner.yaml
# 编辑 miner.yaml: 填入 api_keys, wallet_name, wallet_hotkey, netuid

# Step 3: 启动 Miner
python neurons/miner.py --config config/miner.yaml

# Step 4: 启动 Validator
python neurons/validator.py --netuid <netuid> \
  --wallet.name validator --wallet.hotkey validator \
  --subtensor.network test

# Step 5: 观察 Validator 日志确认权重提交
# 等待 100+ 个区块后检查 Emission 分配
```

### 6.3 已知风险与缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|-----|------|------|---------|
| Testnet TAO 不足 | 低 | 高 | 从 test.taostats.io 申请 |
| 网络端口封锁（Axon 8091）| 中 | 高 | 确保 VPS 防火墙开放 8091 |
| API Key 耗尽时服务中断 | 中 | 中 | 多 key 轮询 + 熔断已实现 |
| Validator 权重提交失败 | 低 | 中 | 重试机制 + 日志告警已实现 |
| 模型降级（Miner 作弊）| 低 | 高 | 检测 + 分数归零已实现 |

---

## 附录：测试命令

```bash
# 子网单元测试（121 tests）
cd subnet && uv run pytest tests/ -v

# 后端单元/集成测试（178 tests）
cd backend && .venv311/bin/python -m pytest tests/ --no-cov

# 后端 E2E 全链路（36 tests）
cd backend && .venv311/bin/python -m pytest \
  tests/test_e2e_full_chain.py \
  tests/test_e2e_miner_flow.py \
  tests/test_e2e_admin_monitoring.py -v --no-cov
```

---

## 结论

**OpenClade 子网代码库通过了所有 335 个自动化测试，代码层全链路验证完成。**

主要成就：
1. **协议层**: LLMAPISynapse 完整定义，版本控制，完整性校验
2. **Miner**: Axon 服务器、Claude API 代理、黑名单、API 池管理全部就绪
3. **Validator**: 多维度评分、Yuma 共识对齐、权重提交链路完整
4. **后端**: 用户→API Key→代理→计费→监控全链路通过 E2E 测试
5. **安全**: 模型降级检测、响应完整性校验、私钥保护均已实现

**下一步行动**: 运营团队在配备 Testnet TAO 的服务器上按"需要人工执行的步骤"完成链上验证，预期 1-2 天可完成 Mainnet 就绪度认证。
