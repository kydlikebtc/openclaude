# OpenClade Email 营销策略

**版本：** v1.0
**制作日期：** 2026-03
**负责人：** CMO
**工具建议：** Resend (开发者友好) 或 Loops (增长导向)

---

## 一、策略概述

Email 是转化率最高的营销渠道（平均 ROI 36:1）。对于 OpenClade，email 服务三个核心目的：

1. **Onboarding drip** — 将注册用户转化为活跃 API 调用者
2. **Retention** — 持续传递价值，防止流失
3. **Expansion** — 推动 referral 和升级

### 核心原则
- **不发废话** — 每封邮件必须有可执行的价值
- **代码优先** — 用代码片段而非营销辞藻说话
- **频率克制** — 宁可少发也不要被标记为垃圾邮件
- **分段精准** — 不同用户看到不同内容

---

## 二、用户分段

| 分段 | 定义 | 邮件策略 |
|------|------|---------|
| **Signed up, no API key** | 注册但未生成 API key | 引导生成 key，降低摩擦 |
| **Has key, no calls** | 有 key 但未发起任何 API 调用 | 提供代码示例，一键复制 |
| **Trial user** | 1-10 次 API 调用 | 展示节省金额，引导增加用量 |
| **Active user** | 每周 100+ API 调用 | 使用报告，referral 激励 |
| **Churned** | 14 天无调用 | Win-back，问原因 |
| **Miner** | Miner 身份用户 | 收益更新，社区活动 |

---

## 三、Launch Email 序列（Pre-launch → Week 2）

### Email 0: Waitlist 确认（注册即发）

**Subject:** You're on the OpenClade waitlist ⚡
**Preview:** Claude API at 75% off — launching soon

```
Hi {first_name},

You're confirmed on the OpenClade waitlist.

One thing you should know: when we launch, the first 100 users
get Founding Member pricing — Claude API at 25% of Anthropic's price.
That's not a typo.

How it works:
→ Same Claude models (Sonnet, Haiku, Opus)
→ OpenAI SDK compatible
→ Pay in USD, no crypto needed
→ Powered by Bittensor TAO subnet economics

We'll email you the moment we're live.

— The OpenClade Team

P.S. Move up the waitlist: share this link and get priority access.
{referral_link}
```

### Email 1: Launch Day（D-Day）

**Subject:** OpenClade is live. Claude API, 75% cheaper.
**Preview:** Your API key is ready.

```
Hi {first_name},

OpenClade is officially live.

Here's your exclusive Founding Member link:
{signup_link}

What you get:
→ Claude Sonnet at $0.75/1M input tokens (vs. $3.00 official)
→ Claude Haiku at $0.06/1M input tokens (vs. $0.25 official)
→ Full OpenAI SDK compatibility
→ Free tier: 10,000 tokens/day to test

Migration takes 60 seconds:

  from openai import OpenAI
  client = OpenAI(
      base_url="https://api.openclaude.io/v1",
      api_key="YOUR_KEY"
  )

That's it. Same prompts. Same models. 75% less cost.

→ Get your API key now: {dashboard_link}

— The OpenClade Team
```

### Email 2: Onboarding Day 1（注册后 24h）

**Subject:** Your first API call in 30 seconds
**Preview:** Copy, paste, save money.

```
Hi {first_name},

You signed up for OpenClade yesterday.

{if no_api_calls}
Looks like you haven't made your first API call yet.
Here's the fastest way to try it:

  curl https://api.openclaude.io/v1/chat/completions \
    -H "Authorization: Bearer {api_key}" \
    -H "Content-Type: application/json" \
    -d '{"model":"claude-sonnet-4-20250514","messages":[{"role":"user","content":"Say hello"}],"max_tokens":100}'

Run that in your terminal. Takes 3 seconds.
{/if}

{if has_api_calls}
Nice — you've already made {call_count} API calls!
You've saved approximately ${savings} compared to Anthropic direct pricing.
Keep going. Your dashboard: {dashboard_link}
{/if}

Quick links:
→ Python quickstart: {docs_link}/python
→ Node.js quickstart: {docs_link}/nodejs
→ Full API reference: {docs_link}/api

Questions? Reply to this email — a human reads every response.

— The OpenClade Team
```

### Email 3: Value Proof（注册后 Day 3）

**Subject:** You've saved ${savings} so far
**Preview:** Here's your OpenClade usage report

```
Hi {first_name},

Your first 3 days on OpenClade:

📊 Your Usage Report
─────────────────────
API calls:        {total_calls}
Tokens processed: {total_tokens}
Models used:      {models_list}
Avg latency:      {avg_latency}ms

💰 Your Savings
─────────────────────
Anthropic cost:   ${anthropic_cost}
OpenClade cost:   ${openclade_cost}
You saved:        ${savings} ({savings_pct}%)

{if savings > 0}
At this rate, you'll save ${monthly_projection} per month.
That's ${yearly_projection} per year.
{/if}

{if zero_calls}
You haven't made any API calls yet.
The fastest way to start: {quickstart_link}
Or reply to this email — we'll help you set up.
{/if}

— The OpenClade Team
```

### Email 4: Social Proof（注册后 Day 7）

**Subject:** How developers are using OpenClade
**Preview:** Real use cases from real teams

```
Hi {first_name},

One week in, here's what OpenClade developers are building:

🔹 Legal document summarization SaaS — saving $300+/mo
🔹 AI-powered code review tool — 10x more prompts for same budget
🔹 Customer support chatbot — serving 5x more conversations
🔹 Content generation pipeline — ROI turned positive after migration

Common pattern we see:
1. Start with a test project
2. Validate quality for 48 hours
3. Move production traffic
4. Reallocate savings to growth

Where are you in this journey?

→ Still testing? Here's our quality benchmark: {benchmark_link}
→ Ready for production? Upgrade your plan: {pricing_link}
→ Need help migrating? Book 15 min with us: {calendly_link}

— The OpenClade Team
```

---

## 四、持续运营邮件

### 周报（Active users，每周一）

**Subject:** Your weekly OpenClade report — ${savings} saved
**内容：** 使用量统计、节省金额、质量评分、新功能预告

### 月报（All users，每月 1 日）

**Subject:** OpenClade Monthly: {month} highlights
**内容：** 平台里程碑、新模型支持、社区活动、Miner 生态更新

### Miner 周报（Miner 分段，每周五）

**Subject:** Your mining report — {tao_earned} TAO earned this week
**内容：** TAO 收益、质量评分、排名变化、优化建议

### 流失挽回（14 天无活动触发）

**Subject:** We miss your API calls 👋
**Preview:** Everything okay?

```
Hi {first_name},

It's been 14 days since your last OpenClade API call.

No hard feelings if you've moved on — but if something went wrong,
we'd love to fix it.

Quick question (reply with the number):

1. I had technical issues
2. Quality wasn't good enough
3. Pricing changed and it's no longer worth it
4. I found an alternative
5. My project is on pause
6. Other

If it's #1 or #2, reply and we'll personally look into it.

Your account is still active. Your API key still works.

— The OpenClade Team
```

---

## 五、Referral Program 邮件

### Invite（Active users，Day 14 触发）

**Subject:** Give $10, get $10 — share OpenClade
**Preview:** You've saved ${savings}. Help a friend do the same.

```
Hi {first_name},

You've saved ${total_savings} with OpenClade so far.

Want to help a friend save too?

Share your referral link:
{referral_link}

For every developer who signs up and makes their first API call:
→ They get $10 in free API credits
→ You get $10 in API credits

No limit. The more you share, the more you earn.

— The OpenClade Team
```

---

## 六、技术实现建议

### 邮件服务商选择

| 工具 | 优点 | 适合阶段 |
|------|------|---------|
| **Resend** | 开发者 API 友好，React Email 模板 | MVP ~ 1,000 用户 |
| **Loops** | 内置分段和自动化，增长导向 | 1,000+ 用户 |
| **Postmark** | 极高送达率，事务邮件专精 | 事务邮件（密码重置等） |

### 推荐架构

```
用户行为事件 → Backend webhook → Email service API
                                    ↓
                              用户分段引擎
                                    ↓
                           邮件模板 + 个性化
                                    ↓
                              发送 + 追踪
```

### 关键指标追踪

| 指标 | 目标 | 红线 |
|------|------|------|
| Open rate | 35%+ | < 20% |
| Click rate | 5%+ | < 2% |
| Unsubscribe rate | < 0.5% | > 1% |
| Bounce rate | < 2% | > 5% |
| Spam complaint rate | < 0.05% | > 0.1% |

### 送达率优化
- 配置 SPF、DKIM、DMARC
- 使用专用发送域名（如 mail.openclaude.io）
- 新域名先发送少量邮件「预热」IP
- 文字版和 HTML 版同时提供
- 避免垃圾邮件触发词（free、unlimited、act now）
