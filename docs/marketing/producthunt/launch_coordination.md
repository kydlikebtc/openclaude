# OpenClade — Launch Coordination Plan

**版本：** v1.0
**制作日期：** 2026-03-16
**负责人：** CMO
**目标 Launch 日期：** Week 5 Tuesday（需 Board 确认）

---

## 一、Launch 时间线总览

### T-14 至 T-0（两周倒计时）

```
T-14  准备期开始
  │
  ├─ T-14: 确认 Launch 日期，通知全团队
  ├─ T-12: PH Gallery 图片启动制作（5张）
  ├─ T-10: 60s 产品演示视频启动录制
  ├─ T-7:  PH "Coming Soon" 页面上线
  ├─ T-7:  Twitter 开始倒计时系列帖（7 天 7 帖）
  ├─ T-5:  KOL/Influencer 预通知发出
  ├─ T-3:  所有 Launch 文案终审
  ├─ T-2:  Hunter 确认（如有外部 Hunter）
  ├─ T-1:  Pre-launch Checklist 全部 ✅
  │
  ├─ D-Day: Launch Day
  │
  ├─ D+1:  Launch Day +1 跟进
  ├─ D+3:  Launch 数据复盘
  ├─ D+7:  Post-Launch 全面回顾
  │
  T+14  进入稳态增长
```

---

## 二、角色分工

| 角色 | 负责人 | Launch Day 职责 |
|------|--------|----------------|
| Launch Coordinator | CMO | 统筹全局，实时指挥 |
| Product Demo | Founding Engineer | 准备演示视频 + 处理技术问题 |
| PH 评论回复 | CMO + CEO | 前 2 小时高密度回复 |
| Twitter 实时发布 | CMO | 按计划发推 + 实时互动 |
| Reddit/HN 发帖 | CMO | 发布 Show HN + Reddit 帖 |
| 社区支持 | Product Manager | Discord 实时答疑 |
| 基础设施监控 | Backend Engineer | 确保服务稳定 |
| 紧急响应 | CEO | 负面反馈、宕机、ToS 问题 |

---

## 三、Pre-Launch Checklist

### 产品就绪（Engineering 负责）

- [ ] API 服务稳定运行 72+ 小时无重大故障
- [ ] 注册 + onboarding 流程测试通过（3 种浏览器）
- [ ] Free tier 配额配置正确
- [ ] 监控告警就绪（延迟、错误率、注册数实时看板）
- [ ] 扩容方案准备（预计 Launch Day 流量 10x）
- [ ] 质量 Dashboard 公开可访问

### 营销就绪（CMO 负责）

- [ ] PH 提交信息完成（Tagline, Description, Maker Comment）
- [ ] Gallery 5 张图完成：
  1. 价格对比图（vs Anthropic Direct）
  2. 代码截图（一行切换演示）
  3. 架构图（User → OpenClade → Miner → Claude）
  4. 质量仪表盘截图
  5. Miner 收益展示
- [ ] 60s 产品演示视频
- [ ] Twitter 倒计时 7 帖已排期
- [ ] Reddit 帖子草稿完成（r/SideProject, r/ChatGPT, r/Bittensor）
- [ ] Show HN 帖子草稿完成
- [ ] Email Launch 序列就绪（Waitlist 用户）
- [ ] KOL 已预通知并确认转发
- [ ] 负面评论应对预案就绪

### 社区就绪

- [ ] Discord 服务器开放 + 欢迎频道配置
- [ ] Twitter @OpenClade 账号活跃（已有 7 天内容）
- [ ] FAQ 页面上线

---

## 四、Launch Day 分钟级行动计划

### Phase 1: 发布（00:01 PT — PH 重置时间）

| 时间 (PT) | 行动 | 执行人 |
|-----------|------|--------|
| 00:01 | 提交 ProductHunt（精确到重置时刻） | CMO |
| 00:05 | 发布 Maker Comment（已准备好的版本） | CEO/Maker |
| 00:10 | Twitter 发布 Launch 公告推文 | CMO |
| 00:15 | 通知 KOL 已上线，请求转发支持 | CMO |
| 00:20 | 发送 Launch Day 邮件给 Waitlist 用户 | 自动化 |
| 00:30 | 在 Bittensor Discord 发布公告 | CMO |

### Phase 2: 高密度互动（01:00 - 06:00 PT）

| 时间段 | 行动 | 执行人 |
|--------|------|--------|
| 01:00-03:00 | PH 评论高频回复（5 分钟内响应） | CMO + CEO |
| 01:00-02:00 | Reddit 发帖：r/SideProject | CMO |
| 02:00-03:00 | Reddit 发帖：r/ChatGPT, r/Bittensor | CMO |
| 03:00 | Hacker News "Show HN" 发帖 | CEO |
| 03:00-06:00 | 持续 PH 评论回复 + 社交互动 | 轮班 |

### Phase 3: 持续推动（06:00 - 18:00 PT）

| 时间段 | 行动 | 执行人 |
|--------|------|--------|
| 06:00 | 发布 "感谢社区" Twitter Thread | CMO |
| 09:00 | 发布实时注册数据截图 | CMO |
| 12:00 | Mid-day 数据检查 + 策略调整 | 全团队 |
| 15:00 | 发布 "我们在 PH 排名 #X" Twitter | CMO |
| 18:00 | Day 1 结束总结 + 社区感谢 | CMO |

### Phase 4: 收尾（18:00 - 23:59 PT）

| 时间段 | 行动 | 执行人 |
|--------|------|--------|
| 18:00-23:59 | 低频 PH 评论回复 | CMO |
| 20:00 | 整理 Launch Day 数据快照 | CMO |
| 23:00 | 发布 "Day 1 by the Numbers" Twitter | CMO |

---

## 五、多平台同步发布方案

### ProductHunt（主战场）

- 00:01 PT 精确提交
- 前 4 小时 = 关键窗口，决定当日排名
- 目标：进入 Top 5
- 策略：高密度回复 + KOL upvote

### Hacker News — Show HN

**标题：**
```
Show HN: OpenClade – Claude API at 75% off, powered by Bittensor mining
```

**帖子正文：**
```
I built OpenClade because I was spending $200/mo on Claude for side projects.

OpenClade uses Bittensor's mining economics to offer the same Claude models
at 25-35% of Anthropic's prices.

How it works:
- Miners contribute Claude API keys, earn TAO tokens
- Validators verify every response against ground truth
- Users get same Claude, 75% cheaper
- One line of code to switch (OpenAI SDK compatible)

Tech: Next.js frontend, Python backend, Bittensor Subnet
Source: https://github.com/kydlikebtc/openclaude

Trade-offs I'm honest about:
- Latency is 1-3s higher than direct API
- Network is still small (growing daily)
- Not recommended for production-critical yet

Would love feedback, especially on the quality verification approach.
```

### Reddit 发帖矩阵

| Subreddit | 角度 | 最佳时间 (ET) |
|-----------|------|---------------|
| r/SideProject | 个人项目 + 省钱故事 | 9:00 AM |
| r/ChatGPT | AI 开发者替代方案 | 10:00 AM |
| r/Bittensor | Miner 收益 + 子网创新 | 11:00 AM |
| r/MachineLearning | 技术架构讨论 | 下午 |
| r/webdev | 开发者工具 | 下午 |

---

## 六、负面反馈应对预案

### 预期攻击向量 & 回应

| 攻击 | 回应策略 |
|------|----------|
| "This violates Anthropic ToS" | 承认风险存在，强调 Miner 自愿提供 key，我们不直接违反 ToS。开源可审计。 |
| "Quality can't be the same" | 指向公开质量 Dashboard，邀请对方实际测试免费 tier |
| "Just another crypto scam" | 展示开源代码、透明定价、真实用户数据。不辩论，用事实回应。 |
| "What about data privacy?" | 解释请求路由机制，强调不存储用户数据，所有内容通过标准 HTTPS。 |
| "Why not just use Haiku?" | 不同模型不同能力，Sonnet/Opus 有不可替代的推理能力。省钱不等于降级。 |

### 危机升级流程

```
Level 1: 个别负面评论 → CMO 直接回应
Level 2: 多条负面 + 有影响力账号 → CEO 参与回应
Level 3: Anthropic 官方声明/行动 → 全团队应急会议 → Board 决策
Level 4: 服务宕机 → Engineering 优先恢复 → CMO 发布状态更新
```

---

## 七、Launch KPI 目标

| 指标 | Day 1 目标 | Week 1 目标 |
|------|-----------|-------------|
| PH Upvotes | 200+ | — |
| PH 评论数 | 50+ | — |
| PH 排名 | Top 5 | — |
| 新注册用户 | 500+ | 2,000+ |
| Twitter Impressions | 50K+ | 200K+ |
| HN 积分 | 100+ | — |
| GitHub Stars | 100+ | 300+ |
| API 调用量 | 10,000+ | 50,000+ |

### 数据追踪工具

- **PH 排名：** 手动刷新 + PH API（如有）
- **注册数：** 后端 Admin Dashboard
- **Twitter：** Twitter Analytics
- **GitHub：** GitHub Insights
- **API 调用：** 内部监控面板

---

## 八、Post-Launch 一周计划

| 天数 | 行动 |
|------|------|
| D+1 | 发布 Launch 结果 Twitter Thread + 感谢帖 |
| D+1 | 回复所有未回复的 PH 评论 |
| D+2 | 整理用户反馈，生成 Feature Request 优先级 |
| D+3 | 发布数据复盘博客（"Our PH Launch: Numbers & Lessons"） |
| D+4 | 根据反馈调整 Landing Page 和定价页面 |
| D+5 | 跟进 KOL 合作（长期合作讨论） |
| D+7 | 全团队 Post-Launch Retro + 策略调整 |

---

## 九、应急联系方式

| 角色 | 通知方式 | 响应时间 |
|------|----------|----------|
| CMO | Discord DM / Issue | 5 分钟 |
| CEO | Discord DM / Issue | 10 分钟 |
| Engineering | Discord #alerts | 5 分钟 |
| Board | Issue Escalation | 30 分钟 |

---

*Launch Day 是最重要的一天，但只是开始。真正的增长来自 Launch 后的持续执行。*
