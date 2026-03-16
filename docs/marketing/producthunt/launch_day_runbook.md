# Launch Day Runbook — 分钟级执行手册

**版本：** v1.0
**创建日期：** 2026-03-16
**负责人：** CMO
**配合文档：** [Launch Coordination](launch_coordination.md) | [Launch Kit](launch_kit.md)

---

> 本文档是 Launch Day 的操作手册，具体到每个时间段的动作、负责人、使用的材料和 checklist。Launch Coordination 定义"谁做什么"，本文档定义"几点几分做什么"。

---

## 时区基准

**所有时间均为 PST（太平洋时间）。** ProductHunt 于 PST 00:01 开始新一天的排名。

---

## D-Day 前夜（D-1 晚上）

### 22:00 PST — Final Check

| # | 动作 | 负责人 | 状态 |
|---|------|--------|------|
| 1 | PH listing 草稿最终审查 | CMO | ☐ |
| 2 | Gallery 图片 5 张确认上传 | CMO | ☐ |
| 3 | Demo 视频确认可播放 | Eng | ☐ |
| 4 | Twitter 7 条定时推文 scheduled（Week 1 内容） | CMO | ☐ |
| 5 | KOL 外联名单确认（预通知已发） | CMO | ☐ |
| 6 | Discord 服务器 channels 就绪 | CMO | ☐ |
| 7 | 服务稳定性确认（Grafana 无告警） | Backend Eng | ☐ |
| 8 | 注册流量承压测试通过 | Backend Eng | ☐ |
| 9 | Landing Page live + 正确跳转 | Frontend Eng | ☐ |
| 10 | 紧急联络表确认（所有人手机在线） | CEO | ☐ |

### 23:00 PST — 全员就位

- CMO：准备 PH 提交页面，等待 00:01
- CEO：待命处理突发
- Eng：监控 dashboard 打开

---

## D-Day 执行

### Phase 1: 凌晨冲刺（00:00 - 06:00 PST）

**目标：** 在亚太和欧洲活跃时段获取初始上票

#### 00:01 — PH 发布

```
ACTION: 提交 ProductHunt listing
WHO: CMO
MATERIAL: docs/marketing/producthunt/launch_kit.md (PH 文案)
CHECKLIST:
  ☐ Tagline: "Claude API at 75% off — powered by Bittensor"
  ☐ 5 gallery images uploaded
  ☐ Demo video attached
  ☐ Maker comment ready (在 PH listing 下发布首条评论)
  ☐ Topics tagged: AI, Developer Tools, APIs
```

#### 00:05 — Twitter 首发公告

```
ACTION: 发布 Launch Day Tweet #1（公告贴）
WHO: CMO
MATERIAL: docs/marketing/social_content/twitter_posts.md → Tweet #1
PLATFORM: Twitter @OpenClade
NOTE: Pin this tweet
```

#### 00:10 — Hacker News 发帖

```
ACTION: 发布 Show HN 帖
WHO: CMO
TITLE: "Show HN: OpenClade – Claude API at 75% off via Bittensor decentralized inference"
URL: https://openclade.io
NOTE:
  - 用户名使用创始人个人账号（非品牌号）
  - 准备好 top-level comment 解释技术原理
  - 不要求赞（HN 禁止 vote manipulation）
```

#### 00:15 — Reddit 多社区发帖

```
ACTION: 发布到 3-4 个 subreddits
WHO: CMO
SUBREDDITS:
  1. r/SideProject — "I built a service that cuts Claude API costs by 75%"
  2. r/LocalLLaMA — "Decentralized Claude inference via Bittensor subnet"
  3. r/ChatGPTCoding — "Cheaper Claude API for dev workflows"
  4. r/bittensor — "New SN[X] — decentralized Claude API marketplace"
MATERIAL: docs/marketing/social_content/community_plans.md
NOTE: 每个 subreddit 定制标题和内容角度，不要交叉发同一篇
```

#### 00:30 — KOL / Influencer 通知

```
ACTION: 发送 "We're live!" DM/Email 给已预通知的 KOL
WHO: CMO
MATERIAL: docs/marketing/partnerships/kol_email_sequences.md → Sequence 响应模板
LIST: docs/marketing/partnerships/kol_target_list.md → Tier 1 优先
```

#### 01:00 - 06:00 — PH 评论轮岗

```
ACTION: 每 30 分钟刷新 PH listing，回复所有评论
WHO: CMO（01:00-03:00）→ CEO（03:00-06:00）
TONE: 技术性 + 真诚，不要用营销腔
KEY QUESTIONS TO PREPARE:
  - "How is this different from just using Anthropic?" → 价格优势 + Bittensor 生态
  - "Is this against Anthropic's ToS?" → 透明回答 + 风险告知
  - "Quality guarantee?" → 指向 quality dashboard
  - "How do miners make money?" → 指向 Miner Guide
```

---

### Phase 2: 美国醒来（06:00 - 12:00 PST）

**目标：** 抓住美国东海岸上班流量高峰

#### 06:00 — 状态检查

```
CHECK:
  ☐ PH 当前排名 #?（目标：Top 10）
  ☐ 当前 upvotes 数量
  ☐ Twitter 互动数据（likes, retweets, replies）
  ☐ HN/Reddit 帖子状态（是否被 flagged/removed）
  ☐ 注册用户数
  ☐ 服务稳定性（Grafana 无告警）
```

#### 06:30 — Twitter Thread 发布

```
ACTION: 发布 5-tweet 技术 thread 解释 OpenClade 工作原理
WHO: CMO
MATERIAL: docs/marketing/social_content/twitter_posts.md → Launch Thread
ANGLE: "Here's how we made Claude 75% cheaper without sacrificing quality 🧵"
```

#### 08:00 — Email Blast（已注册 waitlist 用户）

```
ACTION: 发送 "We're live!" email
WHO: CMO
MATERIAL: docs/marketing/email/email_strategy.md → Launch Day email
SUBJECT LINE A/B:
  A: "OpenClade is live — your 75% cheaper Claude API awaits"
  B: "We're live! $5 free credit inside 🚀"
```

#### 09:00 — Bittensor Discord 推广

```
ACTION: 在 Bittensor Discord #subnets 频道发布公告
WHO: CMO
MATERIAL: docs/marketing/social_content/community_plans.md → Bittensor section
ANGLE: Miner 招募导向 — "New subnet live, estimated miner earnings $3,300-$11,500/mo"
```

#### 10:00 — Dev.to / Medium 博客发布

```
ACTION: 发布首篇博客的跨渠道版本
WHO: CMO
MATERIAL: docs/marketing/blog/01_bittensor_claude_cheaper_devto.md
PLATFORM: Dev.to (first), then Medium (delay 2 hours for canonical)
TAGS: #ai #webdev #tutorial #bittensor
```

#### 11:00 — Twitter 互动回复

```
ACTION: 回复所有 mentions 和 DMs
WHO: CMO
PRIORITY:
  1. 技术问题（立即回复）
  2. 合作意向（收集信息 → 后续跟进）
  3. 正面评价（RT + 感谢）
  4. 负面/质疑（真诚回应 + 指向文档）
```

---

### Phase 3: 下午冲刺（12:00 - 18:00 PST）

**目标：** 最后 12 小时排名冲刺

#### 12:00 — 中场数据快照

```
REPORT TO CEO:
  - PH 排名: #?
  - PH upvotes: ?
  - 新注册用户: ?
  - Twitter 新增关注: ?
  - Discord 新成员: ?
  - 服务状态: ✅/❌

DECISION POINT:
  - 排名 Top 5 → 保持节奏
  - 排名 6-15 → 激活 backup KOL 推广
  - 排名 15+ → CEO 发个人 tweet 号召
```

#### 13:00 — Twitter 午间推文

```
ACTION: 发布成果更新推文
TEMPLATE: "6 hours in and we're already #X on @ProductHunt!
{current_signups} developers have saved on their Claude API costs today.
If you haven't tried it yet → {link}"
```

#### 15:00 — Reddit AMA 准备

```
ACTION: 如果 Reddit 帖有热度，进行非正式 AMA
WHO: CMO + CEO
PLATFORM: r/SideProject 或 r/LocalLLaMA（哪个有更多评论）
DURATION: 1 小时
```

#### 17:00 — 最后冲刺推文

```
ACTION: 发布 "最后几小时" 倒计时推文
TEMPLATE: "Last few hours of our @ProductHunt launch!
We're #X and every upvote helps us reach more developers who overpay for Claude API.
→ {ph_link}"
```

---

### Phase 4: 收尾（18:00 - 24:00 PST）

#### 18:00 — 晚间数据汇总

```
COMPILE D-Day report:
  - PH 最终排名
  - 总 upvotes
  - 总评论数 + 回复数
  - 新注册用户数
  - 新 Miner 申请数
  - Twitter 增长（关注、互动、impression）
  - Reddit/HN 流量贡献
  - 服务稳定性总结
  - 转化漏斗: 访问 → 注册 → 生成 API key → 首次调用
```

#### 19:00 — 感谢推文

```
ACTION: 发布 Launch Day 感谢推文
TEMPLATE: "What a day! 🙏
{final_ranking} on @ProductHunt
{total_signups} new developers joined
{total_api_calls} API calls served

Thank you to everyone who supported us.
This is just the beginning — much more coming this week.

Special thanks to: [tag KOLs who helped]"
```

#### 20:00 — PH 感谢评论

```
ACTION: 在 PH listing 发布总结评论
CONTENT: 感谢投票者 + 回答未回复的问题 + 预告下周计划
```

#### 22:00 — 内部复盘

```
ACTION: 写 Launch Day 内部复盘文档
TEMPLATE:
  1. 目标 vs 实际（KPI 对比）
  2. 什么做得好
  3. 什么可以改进
  4. 第二天优先事项
```

---

## 紧急响应预案

### 场景 1: 服务宕机

```
TRIGGER: Grafana 告警 / 用户报告
RESPONSE:
  1. Backend Eng 立即排查（< 5 分钟）
  2. CMO 在 Twitter 发布状态："We're experiencing high demand! Working on it."
  3. PH listing 更新评论："Known issue, fixing now"
  4. 恢复后发布 "We're back!" 推文
ESCALATION: CEO（> 15 分钟未恢复）
```

### 场景 2: Anthropic ToS 质疑

```
TRIGGER: PH/HN/Reddit 高赞评论质疑合规性
RESPONSE:
  1. CEO 亲自回复（技术权威性）
  2. 准备回复模板：
     "Great question. OpenClade operates as a decentralized marketplace
     on Bittensor. Miners run their own Claude API keys and sell
     inference capacity. We facilitate the marketplace — similar to how
     cloud GPU marketplaces work. We're transparent about this model
     and users can evaluate the trade-offs."
  3. 不要删除质疑评论
  4. 如果持续发酵 → 发布独立透明声明帖
```

### 场景 3: PH Listing 被 Flag

```
TRIGGER: PH 通知 listing 被举报
RESPONSE:
  1. 立即联系 PH support（ph_support@producthunt.com）
  2. 提供合规说明
  3. 不要在公开渠道讨论此问题
  4. CEO 负责处理
```

### 场景 4: 注册量超预期

```
TRIGGER: 注册速度 > 100/小时
RESPONSE:
  1. Backend Eng 确认 DB / API 无瓶颈
  2. 加大 Twitter 互动频率
  3. CMO 发布 "Breaking: X signups in Y hours" 推文
  4. 考虑延长 Founding Member 优惠窗口
```

---

## 材料速查表

| 需要什么 | 文件位置 |
|---------|---------|
| PH Tagline + Description | `producthunt/launch_kit.md` |
| PH Gallery 图片需求 | `producthunt/launch_readiness_audit.md` |
| Twitter 内容（Week 1-8） | `social_content/twitter_posts.md` ~ `twitter_week8.md` |
| Reddit/Discord 文案 | `social_content/community_plans.md` |
| Email 内容 | `email/email_strategy.md` |
| KOL 联络名单 | `partnerships/kol_target_list.md` |
| KOL 邮件模板 | `partnerships/kol_email_sequences.md` |
| 博客文章（Dev.to） | `blog/01_bittensor_claude_cheaper_devto.md` |
| 竞品对比回复 | `competitive_analysis.md` |
| Miner 招募 FAQ | `miner_recruitment/recruitment_scripts.md` |
| GTM 策略全局 | `gtm_strategy.md` |
