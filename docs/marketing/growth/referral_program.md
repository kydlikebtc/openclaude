# OpenClade Referral Program Design

**版本：** v1.0
**创建日期：** 2026-03-16
**负责人：** CMO
**实施优先级：** P0 — Launch Week 2 上线

---

## 一、策略定位

Referral 是 API SaaS 中 CAC 最低的增长引擎。OpenClade 的价格优势天然适合 word-of-mouth 传播：用户省了钱，自然愿意分享。我们的 referral loop 设计原则：

- **双向激励** — 推荐人和被推荐人都获得奖励
- **即时兑现** — 奖励直接变成 API credits，无提现摩擦
- **病毒系数 > 1** — 每个用户平均邀请 > 1 个新用户

---

## 二、奖励结构

### Tier 1: Standard Referral（所有用户）

| 角色 | 奖励 | 条件 |
|------|------|------|
| **推荐人** | $5 API credit | 被推荐人首次充值 ≥ $10 |
| **被推荐人** | $5 API credit + 首充 10% bonus | 使用推荐链接注册并充值 |

### Tier 2: Power Referrer（累计推荐 ≥ 10 人）

| 角色 | 奖励 | 条件 |
|------|------|------|
| **推荐人** | $10 credit + 永久 5% 佣金 | 被推荐人每月消费的 5% |
| **被推荐人** | $10 credit + 首月 15% 额外折扣 | 使用 Power Referrer 链接 |

### Tier 3: Ambassador（累计推荐 ≥ 50 人）

| 角色 | 奖励 | 条件 |
|------|------|------|
| **推荐人** | $25 credit + 永久 8% 佣金 + 专属 badge | 被推荐人月消费的 8% |
| **被推荐人** | $15 credit + 首月 20% 额外折扣 | 使用 Ambassador 链接 |

### Miner Referral（独立通道）

| 角色 | 奖励 | 条件 |
|------|------|------|
| **推荐人** | $50 credit | 被推荐 Miner 在线 ≥ 7 天 |
| **新 Miner** | 首月手续费减免 50% | 使用推荐链接注册矿工 |

---

## 三、技术实现

### 3.1 Referral Link 格式

```
https://openclade.io/ref/{referral_code}

# 示例
https://openclade.io/ref/abc123
https://openclade.io/ref/alice-dev
```

**referral_code 规则：**
- 默认：6 位随机字母数字
- 自定义：允许用户设置自定义 code（唯一性校验）
- 格式：小写字母 + 数字 + 连字符，3-20 字符

### 3.2 数据库 Schema

```sql
-- Referral codes
CREATE TABLE referral_codes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  code VARCHAR(20) UNIQUE NOT NULL,
  tier VARCHAR(20) DEFAULT 'standard', -- standard / power / ambassador
  total_referrals INT DEFAULT 0,
  total_earnings_cents INT DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Referral events
CREATE TABLE referral_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  referrer_id UUID NOT NULL REFERENCES users(id),
  referee_id UUID NOT NULL REFERENCES users(id),
  referral_code_id UUID NOT NULL REFERENCES referral_codes(id),
  status VARCHAR(20) DEFAULT 'pending', -- pending / qualified / paid / expired
  referrer_reward_cents INT,
  referee_reward_cents INT,
  qualified_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Recurring commissions (Tier 2+)
CREATE TABLE referral_commissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  referrer_id UUID NOT NULL REFERENCES users(id),
  referee_id UUID NOT NULL REFERENCES users(id),
  month VARCHAR(7) NOT NULL, -- '2026-03'
  referee_spend_cents INT NOT NULL,
  commission_rate DECIMAL(4,3) NOT NULL, -- 0.05 or 0.08
  commission_cents INT NOT NULL,
  paid_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 3.3 API Endpoints

```
POST   /api/referral/code          — 生成/自定义 referral code
GET    /api/referral/code          — 获取当前用户的 referral code
GET    /api/referral/stats         — 推荐统计（总推荐数、收益、tier）
GET    /api/referral/history       — 推荐历史明细
POST   /api/referral/validate/:code — 验证 referral code（注册时调用）
```

### 3.4 注册流程集成

```
1. 用户点击 referral link → 跳转注册页
2. URL 参数 ?ref=abc123 自动填入
3. 注册成功 → 创建 referral_event (status: pending)
4. 用户首次充值 ≥ $10 → 触发 qualification
5. qualification → 双方账户加 credit + 发送通知邮件
6. 推荐人 total_referrals++ → 检查 tier 升级
```

---

## 四、反作弊机制

| 风险 | 对策 |
|------|------|
| 自推自 | 同一 IP / device fingerprint 注册不计入 |
| 批量虚假注册 | 必须首充 ≥ $10 才算有效推荐 |
| Credit 洗劫 | 单用户每月推荐奖励上限 $500 |
| 佣金刷量 | 异常消费模式检测（短时间大量 API 调用后停止） |
| 多 code 滥用 | 每个新用户只能使用一个推荐码 |

---

## 五、营销话术集成

### Dashboard 内嵌推荐入口

```
┌─────────────────────────────────────────────────┐
│ 💰 Share OpenClade, Earn Credits                │
│                                                  │
│ Your referral link:                              │
│ [https://openclade.io/ref/abc123] [📋 Copy]     │
│                                                  │
│ Referred: 3 users  │  Earned: $15 credit        │
│                                                  │
│ Invite 7 more to become a Power Referrer →      │
│ (unlock 5% recurring commissions!)               │
└─────────────────────────────────────────────────┘
```

### Twitter 分享模板（一键分享）

```
I just saved 75% on my Claude API costs with @OpenClade 🤯

If you're spending $100+/mo on Anthropic API, check this out — same API, fraction of the price.

Sign up with my link and we both get $5 free credit:
{referral_link}

#AI #Claude #Bittensor
```

### Email 签名 Banner

```
───────────────────────────────
Powered by OpenClade — Claude API at 75% off
Get $5 free: {referral_link}
───────────────────────────────
```

---

## 六、成效预测

### 保守估计（病毒系数 k=0.3）

| 月份 | 自然注册 | Referral 注册 | 总注册 | Referral 成本 |
|------|----------|---------------|--------|---------------|
| Month 1 | 200 | 60 | 260 | $300 |
| Month 2 | 300 | 140 | 440 | $700 |
| Month 3 | 400 | 250 | 650 | $1,250 |

### 乐观估计（病毒系数 k=0.8）

| 月份 | 自然注册 | Referral 注册 | 总注册 | Referral 成本 |
|------|----------|---------------|--------|---------------|
| Month 1 | 200 | 160 | 360 | $800 |
| Month 2 | 300 | 440 | 740 | $2,200 |
| Month 3 | 400 | 800 | 1,200 | $4,000 |

### CAC 对比

| 渠道 | 预估 CAC | LTV/CAC |
|------|---------|---------|
| Organic (SEO/Twitter) | $0 | ∞ |
| **Referral** | **$5-10** | **10-20x** |
| KOL Partnership | $15-30 | 3-7x |
| Paid Ads (later) | $20-50 | 2-5x |

---

## 七、Launch Timeline

| 时间 | 里程碑 |
|------|--------|
| Launch Day | 基础 referral 系统上线（Tier 1 only） |
| Week 2 | Dashboard 推荐入口 + 一键分享 |
| Week 3 | Tier 2 (Power Referrer) 解锁 |
| Month 2 | Tier 3 (Ambassador) 解锁 + Miner Referral |
| Month 3 | Leaderboard + 月度推荐之星活动 |

---

## 八、Engineering 需求摘要

**最小可行版本（Launch Day）：**
- 数据库 migration（3 tables）
- 3 个 API endpoints（generate code, validate, stats）
- 注册流程 `?ref=` 参数处理
- Credit 发放 webhook

**预估工时：** 1-2 天后端 + 0.5 天前端

**进阶功能（Week 2-4）：**
- Dashboard referral widget
- 一键分享按钮（Twitter/Email）
- Tier 自动升级逻辑
- 佣金月结算定时任务
- 反作弊检测
