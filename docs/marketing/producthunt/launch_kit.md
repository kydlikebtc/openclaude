# OpenClade — ProductHunt Launch Kit

**版本：** v1.0
**制作日期：** 2026-03-16
**负责人：** CMO
**目标 Launch 日期：** TBD（建议 Week 5 Tuesday/Wednesday，PH 最佳发布日）

---

## 一、ProductHunt 提交信息

### Tagline（60 字符以内）

**推荐：**
> Claude API at 75% off — powered by Bittensor mining

**备选：**
> Same Claude. 75% cheaper. One line of code to switch.
> Decentralized Claude API — pay 25% of official prices.

### Description（260 字符以内）

```
OpenClade brings you the same Claude AI models at 25-35% of Anthropic's official prices. Powered by Bittensor's decentralized miner network with validator-enforced quality. Drop-in OpenAI SDK compatible. One line of code to switch. Open source.
```

### First Comment（Maker Comment — 至关重要）

```
Hey Product Hunt! 👋

I'm [name], and I built OpenClade because I was spending $200/mo on Claude for side projects and couldn't justify it anymore.

Here's the problem: Claude is the best AI model out there, but the pricing puts it out of reach for most indie developers, students, and small teams.

Our solution uses Bittensor's crypto economics to solve this:

1. **Miners** contribute their Claude API keys to the network and earn TAO tokens as rewards
2. **Validators** verify every response against Anthropic's ground truth to ensure quality
3. **Users** get the exact same Claude, at 75% lower cost

What makes this different from other API proxies:
- ✅ Same Claude models — verified by independent validators
- ✅ OpenAI SDK compatible — literally one line of code to switch
- ✅ Fully open source — audit every line on GitHub
- ✅ No crypto knowledge required — pay in USD

What's NOT perfect yet (being honest):
- We're early. The miner network is still growing.
- Latency can be slightly higher than direct API (~1-3s more)
- Not recommended for mission-critical production… yet.

We'd love your feedback. Try the free tier, break things, and tell us what sucks.

GitHub: github.com/kydlikebtc/openclaude
```

### Topics/Categories

**Primary：** Developer Tools
**Secondary：** Artificial Intelligence, Open Source, Web3

### Thumbnail/Logo 要求

- **主色调：** 深蓝+紫色渐变（AI 科技感）+ Bittensor 绿（去中心化属性）
- **元素：** Claude 图标/AI 脑 + 向下的价格箭头 + 分布式网络节点
- **Gallery 图片建议（3-5 张）：**
  1. 价格对比图：Anthropic vs OpenClade，大字突出 "75% savings"
  2. 代码截图：一行代码切换演示
  3. 架构图简化版：User → OpenClade → Miner Network → Claude
  4. 质量仪表盘截图（或 mockup）
  5. Miner 收益数据截图

---

## 二、Launch Day 行动计划

### T-7 天：预热期

| 动作 | 负责 | 状态 |
|------|------|------|
| 提交 PH "Ship" 页面 | CMO | |
| Twitter Week 4 预热帖（Tweet 34-35） | CMO | ✅ 就绪 |
| 通知 Discord 社区设置提醒 | CMO | |
| 发送 Email 通知（Launch Sequence Email #2） | CMO | ✅ 模板就绪 |
| 制作 Gallery 图片 | Design/Founding Engineer | |
| 录制 60s 产品演示视频（可选但强烈建议） | Founding Engineer | |

### T-3 天：动员期

| 动作 | 描述 |
|------|------|
| 个人 DM 动员 | 给 50+ 开发者朋友 DM PH 链接（用 Week 4 DM 模板） |
| Twitter 倒计时帖 | "3 days until launch" |
| Discord 公告 | 设置 PH Launch Day 专属频道 |
| Bittensor Discord | 通知 Miner 社区助力 |

### Launch Day（D-Day）

#### 时间线（PST，PH 0:01 AM 上线）

| 时间 (PST) | 动作 |
|------------|------|
| 00:01 | PH 页面上线，发布 Maker Comment |
| 00:05 | Twitter 首发公告帖 |
| 00:10 | Discord 全频道 @everyone |
| 00:15 | Email blast 给所有 waitlist |
| 06:00 | Reddit 发帖（r/SideProject, r/ChatGPT, r/artificial） |
| 09:00 | Twitter 进度更新帖 |
| 12:00 | Hacker News "Show HN" 帖 |
| 15:00 | Twitter 感谢帖 + 实时投票数更新 |
| 18:00 | 回复所有 PH 评论 |
| 21:00 | Day-end 总结帖 |

#### Launch Day Twitter 模板

**首发帖：**
```
🚀 We're LIVE on @ProductHunt!

OpenClade: Claude API at 75% off, powered by Bittensor.

→ Same Claude models
→ One-line code switch
→ Open source
→ No crypto needed

Upvote if you think AI should be affordable for everyone 🫡

[PH link]
```

**进度更新帖：**
```
🏆 [X] hours in, [X] upvotes on @ProductHunt

Thank you to everyone supporting OpenClade today.

If you haven't tried it yet — our free tier is live. No credit card needed.

[PH link]
```

**感谢帖：**
```
ProductHunt Day 1: [X] upvotes, [X] new signups, [X] API calls.

Incredible. Thank you.

Some of the best feedback came from the PH comments. We're already working on:
→ [top feedback item 1]
→ [top feedback item 2]

This is Day 1 of making Claude accessible to every developer.
```

---

## 三、Hacker News "Show HN" 帖

### 标题

```
Show HN: OpenClade – Claude API at 75% off via Bittensor's mining network
```

### 帖子正文

```
Hi HN,

I built OpenClade because I was frustrated by Claude API costs for my side projects.

How it works:
- Miners contribute Claude API keys to a Bittensor subnet
- Validators verify response quality against Anthropic's ground truth
- Users get the same Claude models at ~25% of official prices
- Miners earn TAO tokens as compensation

Technical details:
- Backend: Node.js + Express, OpenAI SDK compatible endpoint
- Subnet: Python, Bittensor protocol
- Frontend: Next.js + TypeScript
- Fully open source: [GitHub link]

One-line migration from official API:
  client = OpenAI(base_url="https://api.openclade.com/v1", api_key="your-key")

What I'm honest about:
- This is early. The miner network has [X] nodes.
- Latency is ~1-3 seconds higher than direct API.
- Quality is validated but I'd test thoroughly before production use.
- Anthropic could change ToS. We monitor this closely.

I'd love technical feedback, especially on:
- Our validator consensus mechanism
- The economic model for sustaining low prices
- Security considerations

AMA in comments.
```

**策略说明：** HN 重视技术细节和诚实。承认弱点反而赢得尊重。避免 marketing-speak。如果帖子获得关注，优先回复技术性问题。

---

## 四、Reddit Launch 帖（多社区）

### r/SideProject

```
Title: I built a service that gives you Claude API at 75% off — open source

Body:
[Short version of HN post, more casual tone]

Core stats:
- Same Claude models, verified by independent validators
- OpenAI SDK drop-in compatible
- Free tier available
- GitHub: [link]

Would love feedback from fellow side project builders!
```

### r/ChatGPT 或 r/ClaudeAI

```
Title: Using Claude for projects? I built a way to cut your API costs by 75%

Body:
If you're using Claude's API (not the chat interface), this might save you real money.

OpenClade routes your API calls through a Bittensor mining network where miners compete to serve Claude at lower prices.

TL;DR:
- Same Claude 4, same Sonnet, same output
- 75% cheaper
- One line of code to try
- Open source

No crypto wallet needed. You pay in dollars. We handle the rest.

FAQ:
Q: Is this legal?
A: Miners use paid API keys. We're a distribution layer, not bypassing anything.

Q: Quality same?
A: Validators compare every response against Anthropic's direct output. Miners who return bad responses lose money.

Free tier: [link]
```

### r/Bittensor

```
Title: Subnet [XX]: OpenClade — Monetize your Claude API key via TAO mining

Body:
Hey Bittensor fam,

We're launching OpenClade, a subnet that creates a marketplace for Claude API access.

For miners:
- Contribute Claude API keys → earn TAO
- Average daily earnings: [X] TAO
- ROI: [X]% monthly
- Setup guide: [link]

For the ecosystem:
- Proves Bittensor has real-world utility beyond speculation
- Creates genuine demand for TAO through a useful service
- Fully open-source

We're live on ProductHunt today: [link]

Looking for miners and validators to join the network. AMA below.
```

---

## 五、Launch Day 指标追踪

| 指标 | 目标 | 备注 |
|------|------|------|
| PH Upvotes | 200+ | Top 5 of the day |
| PH Comments | 30+ | 全部回复 |
| 新注册用户（24h） | 150+ | |
| GitHub Stars | +50 | |
| Twitter 关注增长 | +300 | |
| HN Points | 50+ | |
| Discord 新成员 | 100+ | |
| 首日 API 调用量 | 1,000+ | |

---

## 六、Launch Day 常见问题预案

### PH 评论高频问题

| 问题 | 回复思路 |
|------|----------|
| "How is this different from OpenRouter?" | 去中心化 + TAO 激励 = 更低价 + Miner 收益 |
| "Will Anthropic shut you down?" | ToS 合规讨论 + 开源适应性 |
| "Is the quality really the same?" | Validator 机制 + 质量报告链接 |
| "Pricing?" | Free tier + 创始会员 10% 官方价 |
| "What about data privacy?" | 不存储数据 + 开源审计 |
| "Why crypto?" | 用户无感 + 只是底层激励机制 |

### 负面反馈处理策略

1. **技术性质疑** → 坦诚回应 + 提供验证方法
2. **法律/ToS 担忧** → 承认风险 + 展示合规努力
3. **Crypto 偏见** → 强调用户不接触 crypto + 只是基础设施
4. **"Vaporware"** → 指向 GitHub + 提供即时试用
5. **竞品比较** → 竞品分析文档链接 + 差异化话术

---

## 七、Post-Launch（D+1 to D+7）

| 时间 | 动作 |
|------|------|
| D+1 | PH 结果总结帖 + 感谢 |
| D+2 | 整理 PH/HN 反馈 → 开发优先级 |
| D+3 | 发布 "What We Learned from Launch" 博客 |
| D+5 | 跟进所有 Launch Day 注册用户（Email 序列） |
| D+7 | Week 5 复盘报告 |
