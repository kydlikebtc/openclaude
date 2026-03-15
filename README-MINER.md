# OpenClade Miner 快速接入指南

> 5 分钟上手，将你的 Claude API Key 转化为 TAO 挖矿收益

[![Join Miners](https://img.shields.io/badge/成为%20Miner-立即加入-brightgreen)](https://openclaude.io/miner)
[![TAO Subnet](https://img.shields.io/badge/Bittensor-子网-blue)](https://bittensor.com)

---

## 什么是 OpenClade Miner？

作为 OpenClade Miner，你：
- **提供**：你拥有的 Claude API Key
- **赚取**：TAO 子网 Emission（挖矿奖励）
- **无需**：部署服务器或编写代码

**盈利逻辑：** TAO Emission 收入 > Claude API 调用成本 = 净利润

### 月收益预估

| 参与程度 | 月净利润（参考值）|
|---------|----------------|
| 新手（1 个 Key，90% 在线）| ~$3,300/月 |
| 成熟（多 Key，99% 在线）| ~$11,520/月 |
| 顶级（高在线 + 推荐网络）| ~$24,300/月 |

> 基于 TAO $300 / 子网 50 个 Miner 场景测算。收益受 TAO 价格和网络规模影响。

---

## 5 步快速上手

### 第 1 步：准备条件（15 分钟）

**你需要：**

| 准备项 | 说明 |
|-------|------|
| Claude API Key | 来自 [Anthropic Console](https://console.anthropic.com)，格式 `sk-ant-api03-...` |
| TAO 钱包（hotkey）| 通过 `btcli wallet new_hotkey` 创建 |
| ≥ 5 TAO | 用于链上质押，防止垃圾节点 |

```bash
# 安装 Bittensor CLI
pip install bittensor

# 创建钱包（如已有可跳过）
btcli wallet new_coldkey --wallet.name default
btcli wallet new_hotkey --wallet.name default --wallet.hotkey miner

# 查看钱包地址
btcli wallet overview
```

---

### 第 2 步：注册 OpenClade 账号

1. 访问 [openclaude.io](https://openclaude.io)
2. 点击 **"成为 Miner"**
3. 用邮箱完成注册
4. 进入 **Miner 控制台**

---

### 第 3 步：连接 TAO 钱包

1. 在 Miner 控制台点击 **"连接钱包"**
2. 复制页面显示的签名挑战（Challenge）
3. 使用 CLI 签名：

```bash
# 替换 <challenge> 为页面显示的挑战字符串
btcli wallet sign \
  --message "Sign in to OpenClade: <challenge>" \
  --wallet.name default \
  --wallet.hotkey miner
```

4. 将签名结果粘贴回控制台完成验证

---

### 第 4 步：质押 TAO 并提交 API Key

**质押 TAO：**

```bash
# 向你的 hotkey 质押 TAO（最少 5 TAO）
btcli stake add \
  --wallet.name default \
  --wallet.hotkey miner \
  --amount 5
```

**提交 Claude API Key：**

1. 进入控制台 → **API Keys 管理**
2. 点击 **"添加 API Key"**
3. 粘贴你的 `sk-ant-api03-...` Key
4. 等待系统自动验证（5-10 秒）
5. 状态变为 `✅ 已激活`

---

### 第 5 步：确认节点上线并开始盈利

在 **服务质量** 面板确认所有指标达标：

| 指标 | 要求 | 说明 |
|------|------|------|
| 在线率 | ≥ 80% | Key 可正常响应请求 |
| 探测成功率 | ≥ 90% | Validator 探测通过率 |
| 平均延迟 | ≤ 3,000ms | 端到端响应时间 |
| 质押 TAO | ≥ 5 TAO | 链上质押确认 |

出现 **"准入资格：已获得"** 后，你的节点开始参与 Emission 分配。

**首次结算：** 下一个 Epoch（通常每小时）后开始显示收益。

---

## 评分机制速览

```
最终得分 = 服务分 × (1 + 推荐加成)

服务分 = 贡献分 × W1 + 待命分 × W2
  贡献分 = 你处理的 Token 占全网比例
  待命分 = 在线率 × 0.5 + 探测成功率 × 0.5

推荐加成 = 最高 30%（通过推荐码引入用户）
```

**子网 Emission 分配：**

```
日 Emission
├── 18% → 平台运营方
├── 41% → Miners（按评分比例）
└── 41% → Validators
```

---

## 提高收益的关键行动

| 优先级 | 行动 | 效果 |
|--------|------|------|
| 🔴 高 | 维持在线率 ≥ 95% | 待命分核心指标 |
| 🔴 高 | 确保 Key 余额充足 | 余额不足 = 探测失败 = 失去资格 |
| 🟡 中 | 分享推荐码给开发者 | 最高 +30% Emission 加成 |
| 🟡 中 | 质押超过 5 TAO | 提高安全边际 |
| 🟢 低 | 添加多个 API Key | 提高处理容量 |

**冷启动加成：** 早期（Miner 数 < 20 个）参与可获得 30-50% 额外加成！**现在是最佳时机。**

---

## 常见问题

**Q: 我需要运行服务器吗？**
A: 不需要。只需在 Web 控制台提交 API Key，平台负责路由和代理。

**Q: 我的 API Key 安全吗？**
A: Key 加密存储，界面仅显示首尾几位。建议使用独立 Anthropic 账号专门用于 Mining。

**Q: Key 被封禁怎么办？**
A: 立即在控制台禁用该 Key，添加新 Key 后恢复。

**Q: 结算周期是多久？**
A: 评分每 Epoch（约每小时）更新，TAO Emission 每日汇总分配。

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [完整 Miner 指南](docs/Miner_Guide.md) | 收益机制、推荐系统、高级配置详解 |
| [API 参考](docs/API_Reference.md) | Claude API 代理 + 平台 API 完整文档 |
| [用户指南](docs/User_Guide.md) | 用户端使用说明（分享给你推荐的用户）|
| [激励机制设计](docs/incentive_mechanism.md) | 评分算法技术细节 |
| [运维 SOP](docs/ops/) | 生产运维手册 |

---

## 联系与支持

- **Discord**: [discord.gg/openclaude](#)（链接待补充）
- **GitHub Issues**: [github.com/kydlikebtc/openclaude/issues](https://github.com/kydlikebtc/openclaude/issues)
- **Twitter**: [@OpenClade](#)（待补充）

---

*版本: v1.0 | 最后更新: 2026-03-15 | 详细文档见 [docs/Miner_Guide.md](docs/Miner_Guide.md)*
