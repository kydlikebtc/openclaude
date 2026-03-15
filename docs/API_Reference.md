# OpenClade API 参考文档

**版本：** v1.0
**基础 URL：** `https://api.openclaude.io`
**最后更新：** 2026-03-15

---

## 概述

OpenClade 提供两类 API：

1. **Claude API 代理**（`/v1/*`）：完全兼容 Anthropic 官方格式，只需替换 `base_url` 即可接入
2. **平台管理 API**（`/api/v1/*`）：用户账户、API Key、计费、Miner 管理等

### 认证方式

**Claude 代理 API（`/v1/messages`）：** 使用 OpenClade API Key

```http
x-api-key: oc_your_api_key_here
# 或
Authorization: Bearer oc_your_api_key_here
```

**平台管理 API（`/api/v1/*`）：** 使用 JWT Token

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

JWT Token 通过登录接口获取，默认有效期 24 小时。

### 请求/响应格式

- 所有请求体使用 `application/json`
- 所有响应为 JSON 格式
- 时间戳使用 ISO 8601 格式（UTC）

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

常见 HTTP 状态码：

| 状态码 | 含义 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无响应体）|
| 400 | 请求参数错误 |
| 401 | 未认证或认证失败 |
| 402 | 余额不足 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 冲突（如邮箱已注册）|
| 429 | 请求过于频繁 |
| 503 | 服务暂不可用（无可用 Miner）|

---

## 第一部分：Claude API 代理

完全兼容 Anthropic 官方 Messages API。如果你已有使用 Anthropic SDK 的代码，**只需修改 `base_url`**，无需任何其他代码改动。

### POST /v1/messages

发送消息并获取 AI 响应。

#### 快速接入示例

**Python（官方 SDK）：**

```python
import anthropic

client = anthropic.Anthropic(
    api_key="oc_your_api_key_here",  # OpenClade API Key
    base_url="https://api.openclaude.io",  # 替换 base_url
)

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "解释一下量子纠缠"}
    ]
)
print(message.content[0].text)
```

**JavaScript/TypeScript（官方 SDK）：**

```typescript
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic({
  apiKey: "oc_your_api_key_here",
  baseURL: "https://api.openclaude.io",
});

const message = await client.messages.create({
  model: "claude-sonnet-4-6",
  max_tokens: 1024,
  messages: [{ role: "user", content: "解释一下量子纠缠" }],
});
console.log(message.content[0].text);
```

**cURL：**

```bash
curl https://api.openclaude.io/v1/messages \
  -H "x-api-key: oc_your_api_key_here" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-6",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | string | ✅ | 模型名称（见支持模型列表） |
| `messages` | array | ✅ | 对话消息数组 |
| `max_tokens` | integer | ✅ | 最大输出 Token 数 |
| `system` | string | — | 系统提示词 |
| `temperature` | float | — | 随机性，0-1，默认 1.0 |
| `stream` | boolean | — | 是否流式返回，默认 false |
| `stop_sequences` | array | — | 停止序列 |
| `top_p` | float | — | Top-p 采样 |
| `top_k` | integer | — | Top-k 采样 |
| `metadata` | object | — | 用户自定义元数据 |

**messages 数组元素：**

```json
{
  "role": "user",       // "user" 或 "assistant"
  "content": "消息内容"  // string 或 content_block 数组
}
```

#### 响应格式

```json
{
  "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
  "type": "message",
  "role": "assistant",
  "model": "claude-sonnet-4-6",
  "content": [
    {
      "type": "text",
      "text": "你好！我是 Claude，很高兴认识你..."
    }
  ],
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 25,
    "output_tokens": 132
  }
}
```

#### 支持的模型

| 模型 ID | 说明 |
|---------|------|
| `claude-opus-4-6` | 最强能力，适合复杂推理 |
| `claude-sonnet-4-6` | 性价比最高，推荐 |
| `claude-haiku-4-5-20251001` | 速度最快，适合简单任务 |

#### 流式响应示例

```python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "写一首关于春天的诗"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

#### 定价

| 模型 | Input | Output | 对比官方 |
|------|-------|--------|---------|
| Claude Opus 4.6 | $2.25/M tokens | $11.25/M tokens | ~25% 官方价 |
| Claude Sonnet 4.6 | $0.75/M tokens | $3.75/M tokens | ~25% 官方价 |
| Claude Haiku 4.5 | $0.0625/M tokens | $0.3125/M tokens | ~25% 官方价 |

---

## 第二部分：用户端 API

所有端点以 `/api/v1/` 开头，需要 JWT 认证（除注册/登录外）。

### 认证

#### POST /api/v1/auth/register

用户注册。

**请求体：**
```json
{
  "email": "developer@example.com",
  "password": "SecurePass123",
  "referral_code": "OC-A1B2C3D4"  // 可选
}
```

**响应（201）：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**错误：**
- `409`：邮箱已注册
- `400`：推荐码不存在

---

#### POST /api/v1/auth/login

用户登录。

**请求体：**
```json
{
  "email": "developer@example.com",
  "password": "SecurePass123"
}
```

**响应（200）：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**错误：**
- `401`：邮箱或密码错误

---

#### GET /api/v1/auth/me

获取当前登录用户信息。

**响应（200）：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "developer@example.com",
  "status": "active"
}
```

---

### API Key 管理

#### GET /api/v1/api-keys

获取当前用户的所有 API Key。

**响应（200）：**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "生产环境",
    "key_preview": "oc_...abcd",
    "status": "active",
    "rate_limit": 60,
    "created_at": "2026-03-01T10:00:00Z"
  }
]
```

---

#### POST /api/v1/api-keys

创建新 API Key。

**请求体：**
```json
{
  "name": "测试环境",
  "rate_limit": 60  // 可选，每分钟请求数上限
}
```

**响应（201）：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "测试环境",
  "key_preview": "oc_...efgh",
  "key": "oc_abcdefghijklmnopqrstuvwxyz012345",  // ⚠️ 仅此一次展示，请妥善保存
  "status": "active",
  "rate_limit": 60,
  "created_at": "2026-03-15T08:00:00Z"
}
```

> ⚠️ **重要：** `key` 字段仅在创建响应中返回一次，后续无法再查看完整 Key。请立即保存。

---

#### DELETE /api/v1/api-keys/{key_id}

删除 API Key（不可恢复）。

**路径参数：** `key_id`（UUID）

**响应（204）：** 无响应体

**错误：**
- `404`：Key 不存在或不属于当前用户

---

### 计费

#### GET /api/v1/billing/balance

获取当前余额。

**响应（200）：**
```json
{
  "balance": "12.345678"  // USD，精度到小数点后6位
}
```

---

#### POST /api/v1/billing/recharge

发起充值请求。

**请求体：**
```json
{
  "amount": "50.00"  // USD 金额，最小 $1
}
```

**响应（201）：**
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": "50.00",
  "payment_address": "TRx...",  // 收款地址（USDT TRC20）
  "status": "pending"
}
```

> 📝 **注意：** 充值到账通常需要 1-5 分钟（等待区块确认）

---

#### GET /api/v1/billing/transactions

获取交易记录（充值 + 消费）。

**查询参数：**
- `limit`：返回条数，默认 50，最大 200

**响应（200）：**
```json
[
  {
    "id": "550e8400-...",
    "type": "charge",     // "charge"(消费) 或 "recharge"(充值)
    "model": "claude-sonnet-4-6",
    "tokens_in": 1500,
    "tokens_out": 800,
    "cost": "0.002475",  // USD
    "created_at": "2026-03-15T09:30:00Z"
  }
]
```

---

#### GET /api/v1/billing/usage

获取用量统计汇总。

**查询参数：**
- `period`：`today` | `week` | `month`，默认 `month`

**响应（200）：**
```json
{
  "total_input_tokens": 1500000,
  "total_output_tokens": 800000,
  "total_cost": "4.125",
  "request_count": 450,
  "period": "month"
}
```

---

## 第三部分：Miner 端 API

> 📝 以下 API 在 Phase 3 实现，当前为规格定义。

所有 Miner API 以 `/api/v1/miner/` 开头，需要 Miner JWT Token 认证。

### 认证

#### GET /api/v1/miner/auth/challenge

获取签名挑战。

**查询参数：**
- `hotkey`：Miner 的 hotkey 地址

**响应（200）：**
```json
{
  "message": "Sign in to OpenClade: abc123def456",
  "nonce": "abc123def456",
  "expires_at": "2026-03-15T09:05:00Z"
}
```

---

#### POST /api/v1/miner/auth/verify

验证钱包签名，获取 JWT。

**请求体：**
```json
{
  "hotkey": "5GrwvaEF...",
  "nonce": "abc123def456",
  "signature": "0x1234abcd..."  // Substrate SR25519 签名
}
```

**响应（200）：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

### Claude Key 管理

#### GET /api/v1/miner/keys

获取 Miner 的 Claude API Key 列表（不返回完整 Key）。

**响应（200）：**
```json
[
  {
    "id": "550e8400-...",
    "key_preview": "sk-ant-...abcd",
    "provider": "anthropic",
    "status": "active",
    "created_at": "2026-03-01T10:00:00Z",
    "last_used_at": "2026-03-15T08:45:00Z"
  }
]
```

---

#### POST /api/v1/miner/keys

添加新的 Claude API Key（自动验证可用性）。

**请求体：**
```json
{
  "api_key": "sk-ant-api03-..."
}
```

**响应（201）：**
```json
{
  "id": "550e8400-...",
  "key_preview": "sk-ant-...efgh",
  "provider": "anthropic",
  "status": "active",
  "created_at": "2026-03-15T09:00:00Z"
}
```

**错误：**
- `400`：Key 格式无效或验证请求失败（Key 不可用）

---

#### PATCH /api/v1/miner/keys/{key_id}

更新 Key 状态（启用/禁用）。

**请求体：**
```json
{
  "status": "disabled"  // "active" 或 "disabled"
}
```

---

#### DELETE /api/v1/miner/keys/{key_id}

删除 Claude API Key。

**响应（204）：** 无响应体

---

### 收益查询

#### GET /api/v1/miner/earnings/summary

获取收益汇总。

**响应（200）：**
```json
{
  "today_score": 72.5,
  "today_tokens": 2150000,
  "today_estimated_tao": 0.41,
  "month_total_score": 1890.3,
  "month_total_tokens": 55000000,
  "month_estimated_tao": 10.2,
  "current_rank": 5,
  "total_miners": 23
}
```

---

#### GET /api/v1/miner/earnings/daily

获取每日收益明细。

**查询参数：**
- `days`：最近 N 天，默认 30

**响应（200）：**
```json
[
  {
    "date": "2026-03-14",
    "service_score": 70.2,
    "referral_bonus": 0.12,
    "final_score": 78.6,
    "tokens_processed": 2100000,
    "estimated_tao": 0.41
  }
]
```

---

### 服务质量

#### GET /api/v1/miner/quality/current

获取当前服务质量指标。

**响应（200）：**
```json
{
  "online_rate": 0.87,
  "probe_success_rate": 0.94,
  "avg_latency_ms": 1240,
  "stake_amount": 5.2,
  "eligibility": {
    "online_rate_ok": true,
    "probe_success_ok": true,
    "latency_ok": true,
    "stake_ok": true,
    "is_eligible": true
  },
  "last_updated_at": "2026-03-15T09:00:00Z"
}
```

---

### 推荐系统

#### GET /api/v1/miner/referral/stats

获取推荐系统统计。

**响应（200）：**
```json
{
  "my_referral_code": "OC-A1B2C3D4",
  "referral_link": "https://openclaude.io/r/OC-A1B2C3D4",
  "total_referred_users": 23,
  "active_users_this_epoch": 8,
  "this_epoch_spend": 1240.5,
  "current_bonus_rate": 0.074,
  "top_users": [
    {
      "user_masked": "u***1",
      "joined_at": "2026-03-01T10:00:00Z",
      "this_epoch_spend": 340.0
    }
  ]
}
```

---

### 质押管理

#### GET /api/v1/miner/staking/info

获取质押信息。

**响应（200）：**
```json
{
  "current_stake": 5.2,
  "min_required": 5.0,
  "is_eligible": true,
  "last_updated_at": "2026-03-14T12:00:00Z"
}
```

---

## 第四部分：公开数据 API

无需认证，用于 Landing Page 等公开场景。

#### GET /api/v1/public/stats

获取网络统计数据。

**响应（200）：**
```json
{
  "active_miners": 18,
  "total_requests_today": 12450,
  "total_tokens_processed": 45600000,
  "uptime_percent": 99.2
}
```

---

#### GET /api/v1/referral/validate/{code}

验证推荐码是否有效。

**路径参数：** `code`（推荐码，格式 `OC-XXXXXXXX`）

**响应（200）：**
```json
{
  "valid": true,
  "miner_name": "Alice's Miner"  // 推荐码对应的 Miner 名称
}
```

或：
```json
{
  "valid": false,
  "miner_name": null
}
```

---

## 第五部分：基础设施端点

#### GET /health

健康检查端点（无需认证）。

**响应（200）：**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

#### GET /docs

Swagger UI（OpenAPI 交互式文档）

#### GET /redoc

ReDoc 格式的 API 文档

---

## 附录

### 速率限制

| 端点类别 | 默认限制 |
|---------|---------|
| Claude API（`/v1/messages`）| 60 requests/minute |
| 平台 API（`/api/v1/*`）| 120 requests/minute |
| 公开 API | 30 requests/minute |

超过限制时返回 `429 Too Many Requests`，响应头包含：
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1710484800
```

### SDK 兼容性

OpenClade Claude 代理完全兼容以下 SDK：

| SDK | 版本 | 接入方式 |
|-----|------|---------|
| `anthropic` (Python) | ≥ 0.40.0 | 设置 `base_url` |
| `@anthropic-ai/sdk` (Node.js) | ≥ 0.27.0 | 设置 `baseURL` |
| `claude-3-opus` 等第三方 | 任意 | 设置 API Base URL |

### 错误码详解

| 错误 | 说明 | 解决方案 |
|------|------|---------|
| `401 Invalid API key` | API Key 无效或已撤销 | 在用户后台重新生成 Key |
| `402 Insufficient balance` | 余额不足 | 充值后重试 |
| `503 No miners available` | 当前无可用 Miner | 通常为短暂状态，几分钟后重试 |
| `429 Too Many Requests` | 请求频率超限 | 减慢请求速率或升级套餐 |

---

*文档版本: v1.0 | 最后更新: 2026-03-15 | 有疑问请通过 Discord 或 GitHub Issues 联系我们*
