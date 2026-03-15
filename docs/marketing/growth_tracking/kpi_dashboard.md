# OpenClade KPI Dashboard — 实时追踪指引

**版本：** v1.0
**创建日期：** 2026-03-15
**负责人：** CMO

---

## 一、数据源配置

### 产品数据（需 Backend/Admin 支持）

| 指标 | 数据源 | 获取方式 | 频率 |
|------|--------|---------|------|
| 注册用户数 | PostgreSQL `users` 表 | Admin Dashboard / SQL | 每日 |
| DAU | API 网关日志 | Admin Dashboard | 每日 |
| Token 消耗量 | `transactions` 表 | Admin Dashboard | 每日 |
| 注册→充值转化 | `users` JOIN `transactions` | SQL query | 每周 |
| Miner 数量 & 在线率 | `miners` 表 + 心跳 | Admin Monitoring | 每日 |
| API 平均延迟 | Prometheus / 监控系统 | Grafana | 实时 |

**Admin Dashboard URL:** `/admin` (已有页面: users, miners, transactions, monitoring)

### 社交数据（手动 / API）

| 指标 | 数据源 | 获取方式 |
|------|--------|---------|
| Twitter 关注数 | Twitter Analytics | 手动 / API |
| Twitter 互动数据 | Twitter Analytics | 每周导出 |
| Discord 成员数 | Discord Server Insights | 手动 |
| Discord 消息量 | Discord Server Insights | 每周 |
| Reddit Karma | Reddit post pages | 手动 |

### 渠道归因

建议在注册页 URL 添加 UTM 参数追踪来源：

```
openclade.io/register?utm_source=twitter&utm_medium=social&utm_campaign=launch_week2
openclade.io/register?utm_source=reddit&utm_medium=social&utm_campaign=localllama_post
openclade.io/register?utm_source=discord&utm_medium=social&utm_campaign=invite
openclade.io/register?utm_source=hackernews&utm_medium=social&utm_campaign=showhn
openclade.io/register?utm_source=bittensor&utm_medium=social&utm_campaign=miner_recruit
```

**需要 Engineering 支持：** 在注册流程中存储 UTM 参数到 `users` 表。

---

## 二、预警阈值

| 指标 | 正常范围 | 黄色预警 | 红色预警 | 响应人 |
|------|---------|---------|---------|--------|
| 日新增注册 | 5+ | <3 连续 3 天 | 0 连续 2 天 | CMO |
| DAU | 趋势上升 | 下降 >20% WoW | 下降 >50% WoW | CEO + CMO |
| Miner 在线率 | >85% | 75-85% | <75% | CTO / Backend |
| API 平均延迟 | <200ms overhead | 200-500ms | >500ms | CTO / Backend |
| Twitter 互动率 | >2% | 1-2% | <1% | CMO |
| Discord 日活 | 趋势上升 | 下降 >30% WoW | 下降 >50% WoW | CMO |

---

## 三、Phase 1 里程碑追踪

### Month 1（冷启动）

| 里程碑 | 目标 | 当前 | 状态 | 截止日期 |
|--------|------|------|------|---------|
| 注册用户达到 100 | 100 | [填写] | 未开始 | Month 1 末 |
| DAU 达到 10 | 10 | [填写] | 未开始 | Month 1 末 |
| 外部 Miner 5 个 | 5 | [填写] | 未开始 | Month 1 末 |
| Twitter 500 关注 | 500 | [填写] | 未开始 | Month 1 末 |
| Discord 200 成员 | 200 | [填写] | 未开始 | Month 1 末 |
| Hacker News 发布 | 发布 | 未发 | 未开始 | Week 3-4 |
| 首篇博客发布 | 发布 | 已完成 | 完成 | Week 2 |

### Month 2（增长加速）

| 里程碑 | 目标 | 截止日期 |
|--------|------|---------|
| 注册用户达到 300 | 300 | Month 2 末 |
| DAU 达到 30 | 30 | Month 2 末 |
| 外部 Miner 10 个 | 10 | Month 2 末 |
| ProductHunt 发布 | 上线 | Month 2 |
| 推荐计划启动 | 上线 | Month 2 |

### Month 3（产品-市场匹配验证）

| 里程碑 | 目标 | 截止日期 |
|--------|------|---------|
| 注册用户达到 500 | 500 | Month 3 末 |
| DAU 达到 50 | 50 | Month 3 末 |
| 外部 Miner 20 个 | 20 | Month 3 末 |
| 月 Token 消耗 200M | 200M | Month 3 末 |
| 付费用户留存 >60% | 60% | Month 3 末 |

---

## 四、营销实验追踪

| 实验编号 | 假设 | 变量 | 指标 | 状态 | 结果 |
|---------|------|------|------|------|------|
| EXP-001 | Twitter Thread 比单条推文转化高 | Thread vs 单条 | 注册点击 | 待测 | |
| EXP-002 | Reddit 帖子重技术细节效果更好 | 技术帖 vs 简短帖 | Karma + 注册 | 待测 | |
| EXP-003 | Landing Page "savings calculator" 提升转化 | 有/无计算器 | 注册率 | 待测 | |
| EXP-004 | Miner 招募在 Bittensor Discord 效果 > Twitter | 渠道对比 | 新 Miner 数 | 待测 | |

---

## 五、竞品监控列表

| 竞品 | 类型 | 价格（% 官方） | 渠道 | 监控频率 |
|------|------|---------------|------|---------|
| [竞品 A] | API reseller | ~50% | 直接 | 每周 |
| [竞品 B] | API reseller | ~60% | 直接 | 每周 |
| OpenRouter | API aggregator | ~100%（+ markup） | openrouter.ai | 每周 |
| Amazon Bedrock | 云服务 | ~100% | AWS | 每月 |

**监控内容：** 价格变化、新功能、用户评论、融资新闻

---

*Dashboard 版本: v1.0 | 最后更新: 2026-03-15*
