# OpenClade 社区运营计划

**版本：** v1.0
**制作日期：** 2026-03-15

---

## 一、Discord 频道结构

### 推荐服务器架构

```
OpenClade Discord
│
├── 📢 ANNOUNCEMENTS
│   ├── #announcements          — 产品更新、重要公告（只读）
│   ├── #changelog              — 版本更新记录
│   └── #status                 — 服务状态通知
│
├── 👋 GETTING STARTED
│   ├── #welcome                — 欢迎新成员，自我介绍
│   ├── #rules                  — 社区守则
│   └── #get-api-key            — 快速上手指南
│
├── 💬 COMMUNITY
│   ├── #general                — 通用讨论
│   ├── #show-and-tell          — 展示你用 Claude 构建的项目
│   ├── #feedback               — 产品反馈和建议
│   └── #off-topic              — 非 AI 话题
│
├── 🔧 DEVELOPERS
│   ├── #help                   — 技术支持，SDK 问题
│   ├── #api-discussions        — API 使用技巧
│   ├── #integrations           — 与其他工具集成
│   └── #prompt-sharing         — 高质量 Prompt 分享
│
├── ⛏️ MINERS
│   ├── #miner-general          — Miner 通用讨论
│   ├── #miner-support          — Miner 技术支持
│   ├── #earnings-reports       — 收益分享（匿名）
│   ├── #miner-tips             — 最大化收益技巧
│   └── #miner-announcements    — Miner 专属公告
│
├── 🌐 BITTENSOR
│   ├── #bittensor-general      — TAO/Bittensor 讨论
│   ├── #subnet-updates         — 子网技术更新
│   └── #tao-price-talk         — TAO 市场讨论（不投资建议）
│
└── 🎤 VOICE
    ├── General Voice
    └── AMA Room
```

### 机器人设置建议

| 机器人 | 功能 |
|--------|------|
| MEE6 / Dyno | 欢迎消息、等级系统、规则验证 |
| Carl-bot | 自动角色分配（User / Miner / Builder） |
| 自定义 Bot | API 状态查询、Miner 排行榜查询 |

### 入会流程

1. 新成员进入 `#welcome`，看到欢迎消息和简单规则
2. 在 `#rules` 点击 ✅ 同意获得 Member 角色
3. 自选角色：`🔧 Developer` / `⛏️ Miner` / `👀 Observer`
4. 被引导到对应专属频道

---

## 二、Discord 欢迎消息模板

### 自动欢迎消息

```
👋 Welcome to OpenClade!

You've found the home of affordable Claude API — 75% cheaper, powered by Bittensor's TAO subnet.

**Quick links:**
📖 Docs: openclaude.io/docs
⚡ Get your API key: openclaude.io/register
⛏️ Become a Miner: openclaude.io/miner/register

**Grab your role:**
React below or head to #role-selection:
🔧 Developer — Building with Claude API
⛏️ Miner — Providing API capacity & earning TAO
👀 Observer — Just here to learn

Questions? Ask in #help.

Let's build together 🚀
```

---

## 三、Reddit 社区参与计划

### 目标 Subreddit 优先级

| Subreddit | 成员数 | 投入策略 | 内容类型 |
|-----------|-------|---------|---------|
| r/LocalLLaMA | ~180K | 高优先 | 技术讨论帖，Show HN 风格发布 |
| r/MachineLearning | ~3.2M | 中优先 | 技术文章分享 |
| r/SideProject | ~150K | 高优先 | 创始人故事，项目分享 |
| r/Bittensor | ~25K | 极高优先 | 子网更新，Miner 招募 |
| r/StableDiffusion | ~500K | 低优先 | 跨 AI 工具推广 |
| r/artificial | ~1.2M | 低优先 | 行业动态讨论 |
| r/webdev | ~800K | 低优先 | 开发者工具推广 |

### Reddit 发布规范

**黄金原则：** 先贡献，后推广

1. **前两周**：在目标 subreddit 积累 karma，回答问题，不做推广
2. **Week 3**：发布带技术深度的内容（不硬广）
3. **Week 4+**：在合适时机提及 OpenClade（结合具体问题解答）

**绝对禁止：**
- 不明显广告的纯推广帖
- 多账号刷票（Reddit 会封号）
- 在明确禁止推广的 subreddit 发布

### 发布模板 — r/LocalLLaMA

**标题：** `Show r/LocalLLaMA: I built a decentralized Claude API using Bittensor TAO miners (75% cheaper)`

**正文：**
```
Hey r/LocalLLaMA,

Been lurking here for ages, finally built something worth sharing.

**What:** OpenClade — Claude API access at 25-35% of official price
**How:** Bittensor TAO subnet miners provide Claude API keys, get paid in TAO emissions, the economics make cheaper pricing sustainable
**Migration:** Change one line (base_url), everything else stays the same

---

**The technical bit:**

Miners stake TAO, submit Claude API keys, get scored by validators on:
- Response latency
- Uptime
- Actual Claude response verification (validators check it's not a fake model)

Miners earn 41% of subnet emissions. At $300/TAO, that's more than enough to cover their API costs. So they can charge users 25% of official.

---

**Pricing:**
- Sonnet 4.6: $0.75/M input (vs $3 official), $3.75/M output (vs $15 official)
- Founding members get extra 10% off

---

**Risks I should mention honestly:**
1. Anthropic ToS risk — API key resale is technically against ToS. Miners acknowledge this.
2. TAO price volatility — though even at $30/TAO, miners are near breakeven
3. It's beta — uptime is good but not enterprise-SLA level

---

Happy to answer any technical questions. The subnet code is [link] if you want to dig in.
```

---

### 发布模板 — r/Bittensor

**标题：** `OpenClade subnet: earning TAO by providing Claude API capacity [Early Miner Spots Open]`

**正文：**
```
Hey Bittensor community,

Launching a new subnet I think fits well here: OpenClade.

**The concept:** Miners provide Claude API keys, get scored by validators on real API quality, earn TAO emissions proportional to their score.

**Why this subnet makes sense economically:**
- Claude API is expensive ($3/M input tokens officially)
- Miners earn enough TAO to more than cover their API costs
- Users get Claude at 25-35% of official price
- Network grows → more miners → better coverage → more users → more TAO value

**Early Miner opportunity:**
- Currently < [N] miners total
- Each miner gets proportionally more emissions with fewer competitors
- Now is the time to join before it gets crowded

**Requirements:**
- Claude API key (from Anthropic account)
- 5 TAO minimum stake
- Stable internet connection

**Monthly earnings estimate (early phase, 50 TAO/day emissions):**
- New miner (2M tokens/day): ~$3,300/month net profit
- Top miner (10M tokens/day + referrals): ~$24,000/month net profit

Subnet is live. DM or drop questions below.

More details: openclaude.io/miner
```

---

## 四、Bittensor Discord 推广文案

### 版本 A：子网公告频道

```
🚀 New Subnet Alert: OpenClade — Decentralized Claude API

OpenClade is now live on Bittensor as a dedicated AI API subnet.

**What it does:**
→ Miners provide Claude API key capacity
→ Validators score latency, uptime, and response authenticity
→ Users access Claude at 25-35% of official price
→ 41% of daily emissions go to Miners

**Why join as Miner:**
→ TAO rewards > API costs (even at TAO = $30)
→ No technical setup beyond submitting your API key
→ Referral system: bring users, earn bonus on top

**Early Miner advantage:**
Right now there are very few miners. First movers capture the most emissions.

More info: openclaude.io/miner
Discord: [link]
```

### 版本 B：Miner Discussion 频道

```
Hey miners 👋

Have a Claude API key? This subnet might interest you.

OpenClade subnet:
- You submit a Claude API key
- Validators probe it (latency, success rate, real Claude verification)
- You earn TAO proportional to your score (41% of emissions pool)
- Users pay you through the platform routing

Monthly numbers (current network, 50 TAO/day, $300/TAO):
- 2M tokens/day: ~$3,300 net monthly
- 5M tokens/day with referrals: ~$11,500 net

Requirements: Claude API key + 5 TAO stake + stable connection.

Main risk: Anthropic ToS compliance. Miners are responsible for their own keys.

openclaude.io/miner for onboarding guide.
```

### 版本 C：技术讨论频道（英文）

```
Working on something the Bittensor community might find interesting: a subnet for Claude API access.

The core mechanism:
- Miners stake TAO and provide Claude API keys
- Our validator runs probing requests every minute, scoring latency/uptime/accuracy
- Scoring formula: Final Score = Service Score × (1 + Referral Bonus)
- 41% of daily emissions distributed proportionally to scores

It handles the key challenge of API key usage — we verify validators aren't gaming the system (minimum $5 consumption threshold for referral counting, etc.)

Currently live and processing real requests. Happy to discuss the economics or technical design. Subnet code at [link].
```

---

*内容版本: v1.0 | 最后更新: 2026-03-15*
