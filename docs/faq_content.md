# OpenClade FAQ — 常见问题解答

**版本：** v1.0
**最后更新：** 2026-03-16
**用途：** 供 Founding Engineer 集成到前端 FAQ 组件

---

## 目录

- [用户常见问题（20 条）](#一用户常见问题)
- [Miner 常见问题（15 条）](#二miner-常见问题)
- [技术问题（8 条）](#三技术问题)

---

## 一、用户常见问题

### U-01：OpenClade 是什么？它安全吗？

OpenClade 是一个基于 Bittensor TAO 区块链子网的**分布式 Claude API 服务平台**。你通过 OpenClade 发出的 API 请求，最终会被路由到 Anthropic 官方 Claude API 执行，返回的是真实的 Claude 响应。

安全层面：
- 你的请求内容会经过平台路由层传输给矿工（Miner），再由 Miner 转发给 Anthropic
- 平台不会永久存储你的请求内容，仅记录 Token 用量用于计费
- API Key 以加密形式存储，后台不可见明文

**诚实说明：** 如果你的请求内容涉及高度敏感的商业机密，建议先评估是否适合使用任何第三方代理服务（包括 OpenClade）。

---

### U-02：为什么 OpenClade 比官方 API 便宜那么多？

OpenClade 利用 **Bittensor TAO 子网挖矿机制**来补贴 API 成本。矿工（Miner）通过提供 Claude API Key 处理用户请求，可以获得 TAO 代币的挖矿奖励。这些奖励的价值覆盖了 API 调用成本，因此平台可以大幅降低用户侧的定价。

简而言之：矿工的 TAO 收入补贴了你的使用成本。

---

### U-03：响应质量和官方 API 一样吗？

是的。OpenClade 使用的是真实的 Anthropic Claude 模型 API——不是本地部署的模型，也不是微调版本。Validator（验证节点）会持续监控 Miner 的输出质量，确保没有模型降级或伪造响应的行为。

---

### U-04：支持哪些 Claude 模型？

目前支持以下模型（模型 ID 与官方一致）：

| 模型 | 模型 ID | 建议用途 |
|------|---------|---------|
| Claude Opus 4.6 | `claude-opus-4-6` | 复杂推理、高质量写作 |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | 日常开发、平衡性能与成本 |
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | 高频轻量任务 |

新模型会在 Anthropic 正式发布后，评估 Miner 网络支持情况后陆续接入。

---

### U-05：如何获取 API Key？

1. 访问 [openclaude.io](https://openclaude.io) 注册账户
2. 账户充值（最低 $1）
3. 进入"API Keys"页面，点击"创建 API Key"
4. 为 Key 命名，**立即复制并保存**（格式：`oc_...`，只展示一次）

---

### U-06：充值方式有哪些？最低多少？

目前支持 **USDT（TRC20）** 充值。最低充值金额为 **$1**，推荐首充 **$10-20**。转账后通常 1-5 分钟内余额自动到账。

> 注：余额以美元计，不与 TAO 价格波动挂钩，充值后锁定为美元余额。

---

### U-07：定价是多少？未来会变吗？

当前（创始会员专享价）：

| 模型 | Input | Output | 相比官方 |
|------|-------|--------|---------|
| Claude Opus 4.6 | $2.25/M tokens | $11.25/M tokens | 约 25% 官方价 |
| Claude Sonnet 4.6 | $0.75/M tokens | $3.75/M tokens | 约 25% 官方价 |
| Claude Haiku 4.5 | $0.0625/M tokens | $0.3125/M tokens | 约 25% 官方价 |

**价格稳定性承诺：** 创始期（Phase 1）价格将维持到我们明确公告调整为止。未来价格预计调整至官方价的 35% 左右，**不会超过官方价格**。

---

### U-08：余额会过期吗？

不会。余额永久有效，无时间限制。

---

### U-09：可以申请退款吗？

可以，但有限制：
- **未消费余额**：可在 30 天内申请退款，扣除 10% 手续费（区块链转账成本）
- **已消费部分**：不退款
- 申请方式：通过 Discord 支持频道联系我们

---

### U-10：有速率限制吗？

默认每个 API Key 的速率限制为 **60 次请求/分钟**。如需更高限制，可在创建 Key 时设置自定义 `rate_limit`，或通过 Discord 联系我们升级。

---

### U-11：如果服务出现 503 错误怎么办？

`503 Service Unavailable` 通常意味着当前没有可用的 Miner 节点处理你的请求。这是短暂状态，建议：

1. 等待 2-5 分钟后重试
2. 在代码中实现自动重试逻辑（指数退避）
3. 如果持续超过 30 分钟，请通过 Discord 反馈

---

### U-12：如果 Miner 下线，我的请求会怎样？

OpenClade 路由层会自动从健康的 Miner 节点中选择替代节点。单个 Miner 下线不会影响你的服务，但如果可用 Miner 数量极少（低于阈值），可能触发 503 错误。

目前处于早期阶段，Miner 网络规模仍在成长中，极端情况下可能出现短暂服务不可用。

---

### U-13：我的请求内容会被记录吗？

OpenClade 的计费系统**只记录 Token 使用量**，不记录请求内容本身。但请注意：

- Miner 节点会转发你的完整请求到 Anthropic API，Anthropic 的数据处理政策适用
- 我们不保证 Miner 节点在转发请求时不会留存内容（技术上无法强制阻止）
- **如果你的请求包含敏感信息，请评估风险后使用**

---

### U-14：响应延迟比官方 API 高多少？

通常额外增加 **50-200ms** 延迟（路由层开销）。具体延迟取决于你选中的 Miner 节点质量和网络状况。如果对延迟敏感（如实时语音应用），建议先测试是否满足需求。

---

### U-15：是否支持流式响应（Streaming）？

是的，完整支持 SSE 流式响应，使用方式与官方 API 完全相同：

```python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "写一首诗"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

---

### U-16：如何查看我的用量和消费？

- **Web 端**：登录 → "计费" → "用量统计"，支持按日/周/月查看
- **API**：`GET /api/v1/billing/usage?period=month`

每次 API 调用后，余额实时扣减。

---

### U-17：有推荐码福利吗？

有。如果朋友邀请你注册，填写推荐码可获得**额外余额奖励**（具体金额见当前活动页面）。你的推荐码在注册后可在"账户设置"中找到。

每成功邀请一位用户首充，你将获得对应比例的消费返佣。

---

### U-18：支持哪些编程语言和 SDK？

任何支持 HTTP 请求的语言都可以使用。已验证兼容的方式：

- **Python**：官方 `anthropic` SDK（修改 `base_url` 即可）
- **JavaScript/TypeScript**：官方 `@anthropic-ai/sdk`（修改 `baseURL`）
- **Go、Rust、PHP、Ruby**：通过 HTTP 直接调用
- **OpenAI SDK**：不直接支持（OpenClade 使用 Anthropic 格式，非 OpenAI 格式）

---

### U-19：OpenClade 是否与 Anthropic 有官方合作关系？

没有。OpenClade 是独立运营的第三方平台，与 Anthropic 没有官方合作关系。我们使用 Anthropic 的公开 API，遵守其使用条款。

**重要说明：** Anthropic 的使用条款禁止未经授权的 API 转售行为。OpenClade 的运营模式是否完全符合这些条款存在灰色地带。使用 OpenClade 前，请自行评估合规风险。我们会持续关注并及时与用户沟通任何政策变化。

---

### U-20：如何获得技术支持？

| 渠道 | 适用场景 | 响应时间 |
|------|---------|---------|
| Discord 支持频道 | 技术问题、账户问题 | 通常 2-24 小时 |
| GitHub Issues | Bug 报告、功能请求 | 1-3 工作日 |
| Twitter @OpenClade | 公告、重大问题反馈 | 不保证个人回复 |

---

## 二、Miner 常见问题

### M-01：成为 Miner 需要什么条件？

必须具备：

| 条件 | 说明 |
|------|------|
| Claude API Key | Anthropic 官方账号的 API Key（`sk-ant-api03-...`） |
| TAO 钱包 | Bittensor 兼容钱包（如 Polkadot.js 扩展） |
| 最低 5 TAO 质押 | 当前约 $1,500（价格随 TAO 市场波动） |
| 稳定网络 | 保证在线率 ≥ 80%，延迟 ≤ 3,000ms |

> 推荐在专用 Anthropic 账号上申请 API Key，与个人主账号分开，降低封号风险。

---

### M-02：最低质押是多少 TAO？为什么需要质押？

最低 **5 TAO**。质押的目的是防止低成本注册的垃圾节点，保证 Miner 网络质量。质押量更高（建议 10-20 TAO）有助于在评分时获得更高权重。

质押的 TAO 可以随时取回，但取回需要一段时间（链上解锁周期，通常为几天）。

---

### M-03：我需要运行服务器吗？需要部署代码吗？

**不需要。** 目前 OpenClade 是纯托管模式——你只需在 Web 控制台提交 Claude API Key，平台自动将用户请求路由到你的 Key。无需部署任何代码或维护服务器。

未来可能提供可选的自托管模式，但当前版本不需要。

---

### M-04：收益如何计算？每天能赚多少？

收益来自 **TAO 子网 Emission**，每日分配，分配比例基于你的得分。

基础收益公式：
```
日收益 = 子网日 Emission × (你的得分 / 全网总得分) × Miner 分配比例（41%）
```

**参考数字（仅供估算，随 TAO 价格和网络规模变化）：**

| 场景 | 在线率 | 探测成功率 | 推荐加成 | 日净利润估算 |
|------|--------|------------|---------|------------|
| 新手 Miner | 90% | 90% | 0% | $50-150 |
| 成熟 Miner | 99% | 99% | 12% | $200-500 |
| 顶级 Miner | 99% | 99% | 30% | $500-1,000+ |

> **免责声明：** 以上数字基于 TAO $300/枚、子网 50 TAO/日、50 个活跃 Miner 等假设，实际收益受市场变化影响较大，不构成投资建议。

---

### M-05：收益何时发放？如何提现？

TAO Emission 每 **tempo**（约 360 个区块，约 72 分钟）结算一次，直接发到你的 TAO 钱包地址。平台不托管你的 TAO 收益。

提现方式：直接在 TAO 钱包中操作，与 OpenClade 无关。

---

### M-06：评分机制是什么？哪些因素影响得分？

得分由两部分组成：

**1. 服务分**
- **贡献分**（实际处理的 Token 量占全网比例，上限 100）
- **待命分**（在线率 × 50 + 探测成功率 × 50）
- 动态权重：网络流量低时待命分权重更高，流量高时贡献分权重更高

**2. 推荐加成**
- 每推荐一个活跃用户：+2% 加成
- 推荐加成上限：+30%

**准入门槛（任一不达标则得分为 0）：**
- 在线率 ≥ 80%
- 探测成功率 ≥ 90%
- 平均延迟 ≤ 3,000ms
- 质押 ≥ 5 TAO

---

### M-07：如果我的 API Key 被 Anthropic 封禁怎么办？

如果你的 Key 被封禁：
1. 探测请求会失败，得分降为 0
2. 请立即在 OpenClade 控制台更换新的 API Key
3. 更换后，下一个评分周期起恢复参与评分

建议：
- 使用专用 Anthropic 账号，避免触发 Anthropic 的使用条款风控
- 定期检查 Anthropic 账号的使用告警
- 备好多个 Key 作为切换预备

---

### M-08：Anthropic 是否允许这种 API 转售行为？

**这是 OpenClade 面临的核心政策风险。** Anthropic 的服务条款明确限制未经授权的 API 转售或代理行为。作为 Miner，你将自己的 API Key 提供给第三方平台使用，可能违反 Anthropic 的使用条款，存在账号被封禁的风险。

我们建议：
- 使用专用账号（非主要开发账号）
- 理解并接受相关风险后再参与
- 关注 Anthropic 使用条款的最新变化

OpenClade 不对因违反 Anthropic 使用条款导致的账号封禁承担责任。

---

### M-09：节点下线期间会损失多少收益？

下线期间不会处理请求，贡献分为 0。但待命分仍会根据在线率计算（下线降低在线率得分）。

简单估算：下线 8 小时（约 33%）对新手 Miner 日收益影响约 15-25%，因为待命分有基础托底。保持在线率 ≥ 95% 是最大化收益的关键。

---

### M-10：一个账号可以提交几个 API Key？

目前每个 Miner 账号支持提交 **最多 3 个 API Key**，平台会在多个 Key 之间分配请求（轮询）。多 Key 策略可以降低单个 Key 被封禁的风险，同时提高服务容量。

---

### M-11：如何更换或删除我的 API Key？

登录 Miner Web 控制台 → "API Keys 管理" → 可以添加新 Key、停用旧 Key 或删除 Key。

停用的 Key 立即停止接收新请求，正在处理的请求继续完成。

---

### M-12：有 Miner 数量上限吗？先到先得吗？

目前没有硬性的 Miner 数量上限，但 Bittensor 子网机制会根据链上注册限制（子网 slot 数量）动态控制。随着子网扩展，会逐步开放更多名额。

**注意：** 越早加入，在 Miner 数量少时可以获得更大比例的 Emission 分配。

---

### M-13：如何追踪我的收益记录？

- **OpenClade 控制台**：展示你的得分历史、Token 处理量、探测成功率
- **链上数据**：直接查看 Bittensor 区块链，搜索你的钱包地址
- **Taostats**：使用第三方 TAO 区块链浏览器查看 Emission 记录

---

### M-14：推荐用户奖励是如何计算的？

你拥有专属推荐链接。每推荐一个用户：
- 该用户首次充值后，你获得 **+2% 得分加成**
- 加成上限为 +30%（即最多 15 个有效推荐用户的加成）
- 推荐加成永久有效，只要推荐用户持续活跃

---

### M-15：Validator 是什么？会影响我吗？

Validator（验证节点）是 Bittensor 子网的质量保证机制。Validator 会向 Miner 发送标准探测请求（合规的 Claude API 调用），验证你的节点是否在线、是否正确响应、延迟是否达标。

Validator 的探测本身会消耗你极少量的 Claude API 余额（每次探测约 0.001$），这是正常的运营成本。

你不需要与 Validator 直接交互，只需保持节点稳定在线。

---

## 三、技术问题

### T-01：如何从 OpenAI SDK 迁移？

OpenClade 使用 **Anthropic API 格式**，而非 OpenAI 格式。如果你当前使用 OpenAI，需要：

1. 将 SDK 替换为 `anthropic`（或使用 HTTP 直接调用）
2. 调整消息格式（角色字段、响应结构有所不同）
3. 参考[官方迁移指南](https://docs.anthropic.com)

如果你当前已使用 Anthropic SDK，只需修改 `base_url` 即可：

```python
client = anthropic.Anthropic(
    api_key="oc_your_key",
    base_url="https://api.openclaude.io"
)
```

---

### T-02：Streaming 流式响应如何使用？

与官方 API 完全相同，支持 SSE（Server-Sent Events）格式：

```python
# Python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

```typescript
// TypeScript
const stream = await client.messages.stream({
  model: "claude-sonnet-4-6",
  max_tokens: 1024,
  messages: [{ role: "user", content: "Hello" }],
});
for await (const chunk of stream) {
  process.stdout.write(chunk.type === "content_block_delta" ? chunk.delta.text : "");
}
```

---

### T-03：常见错误码对照

| HTTP 状态码 | 错误原因 | 解决方案 |
|------------|---------|---------|
| 401 | API Key 无效或已过期 | 检查 Key 格式（`oc_...`）；到控制台重新生成 |
| 402 | 账户余额不足 | 登录控制台充值 |
| 403 | 无权限访问该资源 | 检查是否使用了正确的 Key |
| 429 | 触发速率限制 | 降低请求频率；申请提高限制 |
| 503 | 无可用 Miner | 等待 2-5 分钟重试；关注 Discord 状态通知 |
| 400 | 请求参数错误 | 检查模型名称是否正确；检查消息格式 |

---

### T-04：如何在代码中实现自动重试？

推荐使用指数退避策略处理 503 错误：

```python
import time
import anthropic

def call_with_retry(client, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return client.messages.create(**kwargs)
        except anthropic.APIStatusError as e:
            if e.status_code == 503 and attempt < max_retries - 1:
                wait = 2 ** attempt  # 1s, 2s, 4s
                time.sleep(wait)
                continue
            raise
```

---

### T-05：Base URL 是多少？是否支持 HTTPS？

| 环境 | Base URL |
|------|----------|
| 生产环境 | `https://api.openclaude.io` |
| 测试（如有） | 敬请期待 |

仅支持 HTTPS，HTTP 请求会被重定向或拒绝。

---

### T-06：是否支持 System Prompt？

完整支持，与官方 API 格式相同：

```python
client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system="你是一个专业的代码审查助手，只用中文回复。",
    messages=[{"role": "user", "content": "检查这段代码：..."}]
)
```

---

### T-07：是否支持多轮对话（Multi-turn Conversation）？

完整支持。在 `messages` 数组中传入完整的对话历史：

```python
messages = [
    {"role": "user", "content": "我叫小明"},
    {"role": "assistant", "content": "你好，小明！有什么我可以帮你的？"},
    {"role": "user", "content": "你还记得我叫什么吗？"},
]
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=256,
    messages=messages
)
```

**注意：** 每次调用仍需传入完整历史，API 本身是无状态的。

---

### T-08：如何测试接入是否成功？

最快速的验证方式（cURL）：

```bash
curl https://api.openclaude.io/v1/messages \
  -H "x-api-key: oc_your_key_here" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-haiku-4-5-20251001",
    "max_tokens": 32,
    "messages": [{"role": "user", "content": "reply with: ok"}]
  }'
```

成功响应（HTTP 200）表示接入正常。如果收到 401，检查你的 API Key；如果收到 503，稍后重试。

---

*本文档内容基于 OpenClade v1.0 产品状态编写，如有变更将及时更新。*
