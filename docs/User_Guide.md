# OpenClade 用户入门指南

**版本：** v1.0
**最后更新：** 2026-03-15
**适用对象：** 希望以极低成本使用 Claude API 的开发者和团队

---

## 目录

1. [OpenClade 是什么？](#一openclade-是什么)
2. [定价说明：能帮你省多少钱](#二定价说明能帮你省多少钱)
3. [5 分钟快速上手](#三5-分钟快速上手)
4. [接入 Claude API](#四接入-claude-api)
5. [账户充值](#五账户充值)
6. [使用推荐码](#六使用推荐码)
7. [代码示例](#七代码示例)
8. [常见问题](#八常见问题)

---

## 一、OpenClade 是什么？

OpenClade 是一个**分布式 Claude API 服务平台**，基于 Bittensor TAO 区块链子网运行。

**一句话解释：** 你使用 Claude，但只需要支付官方价格的 10-35%。

### 技术上为什么能这么便宜？

OpenClade 利用 **TAO 子网挖矿机制**来补贴 API 成本。矿工（Miner）通过提供 API Key 获得 TAO 代币奖励，他们的收入覆盖了 API 调用成本，因此可以大幅降低用户端的价格。

### 兼容性

OpenClade 完全兼容 **Anthropic 官方 API 格式**。如果你已有使用 Claude API 的代码，**只需修改 `base_url`**，无需任何其他改动。

---

## 二、定价说明：能帮你省多少钱

### 2.1 当前定价（创始会员专享价）

目前处于**冷启动期（Phase 1）**，我们以极低的创始价格回馈早期支持者：

| 模型 | Input 价格 | Output 价格 | 相比官方 | 节省比例 |
|------|-----------|------------|---------|---------|
| Claude Opus 4.6 | $2.25/M tokens | $11.25/M tokens | 25% 官方价 | **节省 75%** |
| Claude Sonnet 4.6 | $0.75/M tokens | $3.75/M tokens | 25% 官方价 | **节省 75%** |
| Claude Haiku 4.5 | $0.0625/M tokens | $0.3125/M tokens | 25% 官方价 | **节省 75%** |

> 💡 **创始会员特惠**：现在注册并充值，锁定最低价格。未来价格将逐步调整至 35% 官方价。

### 2.2 实际省钱计算

**以每月使用 Claude Sonnet 4.6、100M input + 50M output tokens 为例：**

| 平台 | 费用 | 对比 |
|------|------|------|
| Anthropic 官方 | $3×100 + $15×50 = **$1,050** | 基准 |
| OpenClade（25%价） | $0.75×100 + $3.75×50 = **$262.5** | **节省 $787.5（75%）** |

**典型用户月成本对比：**

| 用户类型 | 官方月成本 | OpenClade 月成本 | 月节省 |
|---------|----------|-----------------|--------|
| 个人开发者 | $50-200 | $12.5-50 | $37.5-150 |
| 小型团队 | $500-2,000 | $125-500 | $375-1,500 |
| 中型企业 | $5,000-20,000 | $1,250-5,000 | $3,750-15,000 |

---

## 三、5 分钟快速上手

### 步骤 1：注册账户（1 分钟）

1. 访问 **[openclaude.io](https://openclaude.io)**
2. 点击 **"免费注册"**
3. 输入邮箱和密码完成注册

> 如果有推荐码，在注册页面填写可获得额外福利（见[第六节](#六使用推荐码)）。

### 步骤 2：充值余额（2 分钟）

1. 登录后，进入 **"账户充值"**
2. 输入充值金额（最低 $1，推荐首充 $10-20）
3. 使用 **USDT（TRC20）** 转账到指定地址
4. 等待 1-5 分钟，余额自动到账

### 步骤 3：获取 API Key（1 分钟）

1. 进入 **"API Keys"** 页面
2. 点击 **"创建 API Key"**
3. 为 Key 命名（如 "生产环境"）
4. **立即复制并保存 Key**（格式：`oc_...`，只展示一次）

### 步骤 4：替换代码中的 base_url（1 分钟）

```python
# 修改前（官方 API）
client = anthropic.Anthropic(
    api_key="sk-ant-your-official-key",
)

# 修改后（OpenClade）
client = anthropic.Anthropic(
    api_key="oc_your_openclade_key",   # 换成你的 OpenClade Key
    base_url="https://api.openclaude.io",  # 添加这一行
)
```

**就这一个改动，其他代码完全不变。**

---

## 四、接入 Claude API

### 4.1 接入方式一览

| 方式 | 适用场景 | 改动量 |
|------|---------|-------|
| Python SDK（官方库） | Python 项目 | 仅改 base_url |
| Node.js SDK（官方库） | JavaScript/TypeScript 项目 | 仅改 baseURL |
| HTTP 直接请求（cURL） | 任意语言 | 替换 URL 和 Key |
| OpenAI SDK 兼容模式 | 已有 OpenAI 代码的迁移 | 改 baseURL 和 Key |

### 4.2 支持的模型

| 模型 ID | 能力级别 | 适用场景 |
|---------|---------|---------|
| `claude-opus-4-6` | 最强 | 复杂推理、代码审查、创作 |
| `claude-sonnet-4-6` | 高（推荐） | 日常开发、内容生成、问答 |
| `claude-haiku-4-5-20251001` | 快速 | 简单任务、高频批处理 |

### 4.3 API 端点

```
Base URL:  https://api.openclaude.io
Messages:  POST /v1/messages
```

---

## 五、账户充值

### 5.1 充值方式

目前支持 **USDT（TRC20）** 充值：

1. 登录 → **计费** → **充值**
2. 输入充值金额（USD）
3. 系统生成专属收款地址
4. 在你的钱包 App 发送对应金额的 USDT 到该地址
5. 等待区块链确认（通常 1-5 分钟，3 个区块确认）

### 5.2 充值注意事项

> ⚠️ **重要：**
> - 每次充值会生成新的收款地址
> - 请勿向同一地址转账多次
> - 最小充值金额：$1
> - 仅支持 TRC20 网络（Tron）的 USDT，请勿使用 ERC20 或其他网络

### 5.3 余额查询

- **Web 端：** 登录后右上角显示当前余额
- **API：** `GET /api/v1/billing/balance`

---

## 六、使用推荐码

### 6.1 推荐码福利

注册时填写 Miner 的推荐码（格式：`OC-XXXXXXXX`）可享受：

| 福利 | 说明 |
|------|------|
| **首充额外 10% 赠送** | 充 $100，账户到账 $110 |
| **前 30 天 95 折** | 前 30 天内所有 API 调用额外 5% 折扣 |

### 6.2 在哪里找到推荐码？

如果你是通过别人的推荐链接注册，推荐码会自动填写。
也可以从以下渠道获取推荐码：
- OpenClade Discord 社区
- Twitter 上的 OpenClade 用户分享
- 直接向已有 Miner 索取

### 6.3 填写推荐码

推荐码只能在**注册时**填写，注册完成后无法更改。

---

## 七、代码示例

### 7.1 Python（使用官方 Anthropic SDK）

```python
import anthropic

# 初始化客户端（只需改这里）
client = anthropic.Anthropic(
    api_key="oc_your_api_key_here",          # 你的 OpenClade API Key
    base_url="https://api.openclaude.io",    # OpenClade API 地址
)

# 普通请求
message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "帮我写一个快速排序的 Python 实现"}
    ]
)
print(message.content[0].text)
```

### 7.2 Python（流式返回）

```python
import anthropic

client = anthropic.Anthropic(
    api_key="oc_your_api_key_here",
    base_url="https://api.openclaude.io",
)

# 流式返回（实时显示生成内容）
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=2048,
    system="你是一个专业的 Python 开发助手",
    messages=[
        {"role": "user", "content": "写一个完整的 REST API 示例，使用 FastAPI"}
    ]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### 7.3 Python（多轮对话）

```python
import anthropic

client = anthropic.Anthropic(
    api_key="oc_your_api_key_here",
    base_url="https://api.openclaude.io",
)

# 维护对话历史
conversation_history = []

def chat(user_message: str) -> str:
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="你是一个友好的 AI 助手",
        messages=conversation_history
    )

    assistant_message = response.content[0].text
    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })

    return assistant_message

# 使用
print(chat("你好，我想学习 Python"))
print(chat("可以给我一些入门资源吗？"))
```

### 7.4 Node.js / TypeScript

```typescript
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic({
  apiKey: "oc_your_api_key_here",            // 你的 OpenClade API Key
  baseURL: "https://api.openclaude.io",      // OpenClade API 地址
});

async function main() {
  // 普通请求
  const message = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 1024,
    messages: [
      {
        role: "user",
        content: "解释一下 TypeScript 中的泛型",
      },
    ],
  });

  console.log(message.content[0].text);
}

main();
```

### 7.5 Node.js（流式返回）

```typescript
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic({
  apiKey: "oc_your_api_key_here",
  baseURL: "https://api.openclaude.io",
});

async function streamExample() {
  const stream = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 1024,
    stream: true,
    messages: [
      {
        role: "user",
        content: "写一首关于代码的诗",
      },
    ],
  });

  for await (const event of stream) {
    if (
      event.type === "content_block_delta" &&
      event.delta.type === "text_delta"
    ) {
      process.stdout.write(event.delta.text);
    }
  }
}

streamExample();
```

### 7.6 cURL

```bash
# 普通请求
curl https://api.openclaude.io/v1/messages \
  -H "x-api-key: oc_your_api_key_here" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-6",
    "max_tokens": 1024,
    "messages": [
      {
        "role": "user",
        "content": "你好，请介绍一下自己"
      }
    ]
  }'
```

```bash
# 流式返回
curl https://api.openclaude.io/v1/messages \
  -H "x-api-key: oc_your_api_key_here" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-6",
    "max_tokens": 1024,
    "stream": true,
    "messages": [
      {
        "role": "user",
        "content": "写一首诗"
      }
    ]
  }'
```

### 7.7 使用系统提示词（System Prompt）

```python
import anthropic

client = anthropic.Anthropic(
    api_key="oc_your_api_key_here",
    base_url="https://api.openclaude.io",
)

# 使用系统提示词定义角色
message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=2048,
    system="""你是一位资深的软件架构师，专注于：
    - 微服务架构设计
    - 高可用系统
    - 性能优化

    请用专业但易懂的语言回答问题，必要时提供具体代码示例。""",
    messages=[
        {
            "role": "user",
            "content": "如何设计一个支持每秒 10 万请求的 API 网关？"
        }
    ]
)

print(message.content[0].text)
```

### 7.8 批量处理（异步）

```python
import asyncio
import anthropic

client = anthropic.AsyncAnthropic(
    api_key="oc_your_api_key_here",
    base_url="https://api.openclaude.io",
)

async def process_batch(prompts: list[str]) -> list[str]:
    tasks = []
    for prompt in prompts:
        task = client.messages.create(
            model="claude-haiku-4-5-20251001",  # 用 Haiku 进行批量处理，成本更低
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        tasks.append(task)

    responses = await asyncio.gather(*tasks)
    return [r.content[0].text for r in responses]

# 批量翻译示例
prompts = [
    "将以下内容翻译成英文：你好世界",
    "将以下内容翻译成英文：人工智能正在改变世界",
    "将以下内容翻译成英文：代码是未来的语言",
]

results = asyncio.run(process_batch(prompts))
for i, result in enumerate(results):
    print(f"[{i+1}] {result}")
```

---

## 八、常见问题

**Q1: OpenClade 与 Anthropic 官方 API 有什么区别？**

A: 在功能上几乎相同：
- ✅ 支持所有 Claude 模型
- ✅ 完全兼容官方 API 格式（drop-in replacement）
- ✅ 支持流式响应
- ✅ 支持系统提示词
- ✅ 支持多轮对话
- ⚠️ 响应时间可能略长（因路由层增加了约 50-100ms 延迟）
- ⚠️ 稳定性依赖 Miner 网络（有少量备用机制）

---

**Q2: 响应质量和官方一样吗？**

A: 是的。OpenClade 使用的是真实的 Anthropic Claude API，Validator（验证节点）会持续监控 Miner 的响应质量，确保没有模型降级或伪造响应。

---

**Q3: 有 API 速率限制吗？**

A: 默认限制为 **60 次请求/分钟**。如需更高限制，可在创建 API Key 时自定义 `rate_limit` 参数，或联系我们升级套餐。

---

**Q4: 如果遇到 "503 No miners available"？**

A: 这表示当前没有可用的 Miner，通常是短暂状态（几分钟内）。建议：
- 等待 2-5 分钟后重试
- 如果持续出现，请通过 Discord 反馈

---

**Q5: 我的余额会过期吗？**

A: 不会。充值余额永久有效，不会过期。

---

**Q6: 可以发票吗？**

A: 目前暂不提供发票。我们是加密货币原生平台，目前专注于服务个人开发者和小型团队。企业合规需求请通过 Discord 联系我们协商。

---

**Q7: 如何查看我的使用量？**

A:
- **Web 端：** 登录 → **计费** → **用量统计**，可按今天/本周/本月查看
- **API：** `GET /api/v1/billing/usage?period=month`

---

**Q8: 支持哪些编程语言？**

A: 任何能发 HTTP 请求的语言都可以。我们已验证以下语言的集成：
- Python（通过官方 Anthropic SDK）
- Node.js / TypeScript（通过官方 SDK）
- Go、Rust、PHP、Ruby 等（通过 HTTP 直接调用）

---

**Q9: 如何获得技术支持？**

A:
- **Discord**：加入我们的 Discord 服务器（最快响应）
- **GitHub Issues**：提交 Bug 或功能请求
- **Twitter**：@OpenClade（通知类）

---

**Q10: 如何删除我的账户？**

A: 请联系 Discord 支持频道，告知你的账号邮箱，我们会在 3 个工作日内处理。删除账户前请确保余额已使用完毕（余额不退还）。

---

## 快速链接

- [API 参考文档](./API_Reference.md)
- [Miner 上手指南](./Miner_Guide.md)（想赚 TAO？）
- [商业计划书](../OpenClade_Business_Plan.md)

---

*文档版本: v1.0 | 最后更新: 2026-03-15 | 有问题请加入 Discord 联系我们*
