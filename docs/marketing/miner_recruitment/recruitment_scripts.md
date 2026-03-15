# OpenClade Miner 招募话术与 AMA 准备

**版本：** v1.0
**制作日期：** 2026-03-15
**用途：** DM 话术、社区回复模板、AMA 问答准备

---

## 一、招募核心话术

### 话术 A：针对有 Claude API Key 的开发者

**场景：** 在 Twitter/Discord 中看到有人在用 Claude API

```
Hi [Name],

Noticed you're using Claude API — I think you might be interested in something we built.

OpenClade lets you expose your existing Claude API key to our network and earn TAO (Bittensor) while doing it.

The economics: Your API key processes users' requests. You earn 41% of our subnet's daily TAO emissions. That's way more than the cost of the API calls. Early miners (< 20 active now) earn ~$3,300-18,000/month net.

No server to run. Just submit your key in a web UI, stake 5 TAO, and start earning.

Worth 5 minutes? openclaude.io/miner

Happy to answer any questions.
```

---

### 话术 B：针对 Bittensor/TAO 持有者

```
Hey [Name],

You're in the Bittensor ecosystem, so this might interest you.

We launched OpenClade subnet — Claude API capacity as a decentralized network.

What you can do as a Miner:
1. Stake 5 TAO
2. Submit a Claude API key
3. Earn 41% of subnet daily emissions

With 10-15 miners currently, each miner gets a significant share. As the subnet grows, emissions grow too (more users = more value).

At $300/TAO and 50 TAO/day emissions: ~$3,300-18,000/month for a new miner right now.

Early miners have a massive head start on building their referral network too (permanent bonus structure).

Interested? openclaude.io/miner for the full breakdown.
```

---

### 话术 C：针对 TAO 矿工（已在其他子网挖矿）

```
Hi [Name],

You're already mining TAO — have you looked at OpenClade subnet?

The setup is minimal compared to most subnets:
- No GPU needed
- No servers to maintain
- Just submit a Claude API key and stake 5 TAO

You earn TAO based on your uptime and response quality. The validator checks real API responses, so you can't fake it, but as long as your key is active and your connection stable, you earn.

Economics right now (early, few miners):
- New miner: ~$3,300/month
- Good miner: ~$10,000+/month

Your existing TAO infrastructure knowledge is an advantage. You understand the staking/unstaking already.

Worth a look: openclaude.io/miner
```

---

### 话术 D：短版（Twitter DM 或快速回复）

```
OpenClade pays TAO for providing Claude API capacity. No servers needed — submit your key in a UI, stake 5 TAO, earn daily emissions. ~$3,300+/month for early miners right now. openclaude.io/miner
```

---

## 二、常见异议处理

### 异议 1："Anthropic ToS 不允许转售 API"

**应对话术：**
```
You're right that this sits in a grey area with Anthropic's ToS.

Here's our honest take:
1. Miners provide their own keys and are responsible for their own compliance
2. The network is structured as miners contributing capacity, not traditional resale
3. We've designed the system to keep each miner's usage patterns within normal ranges

This risk is real and we disclose it upfront. Miners who are concerned should use a dedicated Anthropic account separate from their main one. The economic upside is significant enough that many miners make this tradeoff knowingly.

We can't guarantee Anthropic won't act on keys, but the distributed nature means no single key loss breaks the network.
```

---

### 异议 2："TAO 价格太不稳定，收益没法算"

**应对话术：**
```
Fair concern. Here's what the numbers look like in a bear case:

Even if TAO dropped 90% from today to $30, a new miner with 2M tokens/day would be near break-even (~$-3/month on API costs).

For context: TAO would need to drop from ~$300 to $29 before you start losing money. That's lower than its price in 2023.

For Miners who want to hedge, the strategy is simple: convert 50-70% of TAO earnings to stablecoins immediately. You keep the upside, limit the downside.

The early-miner advantage is real though — joining when there are 10-15 miners vs 100 miners is a 6-10x difference in monthly earnings. The TAO risk is the same whether you join now or in 6 months.
```

---

### 异议 3："我不懂 Bittensor，设置太复杂"

**应对话术：**
```
OpenClade is actually the simplest Bittensor subnet to participate in as a Miner.

You don't need to:
- Run any servers
- Install any software
- Understand Substrate/Rust

You only need:
1. A TAO wallet (Polkadot.js extension, 5 minute setup)
2. A Claude API key
3. A web browser

The staking is done via our UI. You do need to use Bittensor CLI once to transfer TAO to stake, but our guide walks through it step by step.

If you can transfer USDT, you can become a Miner.
```

---

### 异议 4："收益数字看起来太好了，有什么陷阱？"

**应对话术：**
```
Healthy skepticism — good.

The numbers are real, and here's why they're high right now:
- Very early stage (~10-15 miners)
- Daily emissions split 50 ways → large per-miner share
- TAO price currently favorable

What changes over time:
- More miners join → each gets smaller share
- If the subnet fails to attract users → emissions stay low
- TAO price goes down → USD equivalent drops

We model all these scenarios in our docs. The $3,300/month figure is the most conservative scenario at current conditions.

The "risk" isn't hidden — it's disclosed on our website:
1. More miners = less per-miner earnings (but network earns more overall)
2. TAO volatility
3. Anthropic key risk (we covered this above)

Early adopter opportunity with real (not crypto-hype) economics. That's genuinely what this is.
```

---

## 三、社区 AMA 准备

### 主题：OpenClade 子网 AMA — 开发者 & Miner

**推荐 AMA 时机：** 上线后 2-3 周，有早期数据可分享时

---

### 准备问题池

**产品与技术类**

Q: How does OpenClade verify that miners are actually using real Claude models and not fake responses?
A: Validators send test prompts with deterministic answers (e.g., math problems). Correct answer + Claude API response format = verified. Any deviation lowers the miner's score immediately.

---

Q: What happens if a miner's API key gets banned by Anthropic?
A: The miner's score drops to 0 (failed probes). Traffic routes to other miners automatically. The miner should deactivate that key in the dashboard and submit a new one. The network's resilience comes from having 20+ independent miners.

---

Q: What's the routing algorithm? How do you pick which miner handles a request?
A: Validators maintain real-time scores. The router uses a weighted random selection that favors higher-scored miners while providing some diversification. High-score miners get more traffic, which leads to more earnings, which incentivizes quality.

---

Q: What latency penalty do users see versus direct Anthropic API?
A: Average additional latency is 50-100ms from our routing layer. Miner-to-Anthropic latency depends on the miner's location and internet speed. Total end-to-end is typically 100-300ms added vs direct API.

---

**收益与经济类**

Q: Show us real earnings from actual miners.
A: [Prepare to share anonymized real screenshots from earliest miners' dashboards]

---

Q: When do emissions start? Do I earn from day 1?
A: Emissions are calculated per Epoch (hourly). First earnings start within the hour of passing the qualification threshold (90% probe success rate, 80% uptime, 5 TAO staked, <3s latency).

---

Q: Can I stake more TAO to earn more?
A: Currently staking doesn't directly affect the scoring formula — it's a qualification threshold, not a multiplier. More staking = lower chance of falling below the minimum threshold if TAO price drops. This may change in future subnet versions.

---

Q: What happens to my staked TAO if I want to exit?
A: You can unstake at any time. There's a 7-day unbonding period (standard Bittensor). Your key stops receiving traffic immediately upon unstaking. There's no fee to exit.

---

**Bittensor 生态类**

Q: How does OpenClade fit into the broader Bittensor ecosystem?
A: Bittensor's vision is specialized intelligence markets. We're building the Claude API capacity market — essentially a decentralized Anthropic API proxy optimized by economic incentives. It demonstrates that real-world AI services can be decentralized.

---

Q: Why Claude specifically and not GPT-4 or Gemini?
A: Claude has strong API demand from developers and comparatively high pricing, making the cost arbitrage most attractive. We plan to expand to other models in Phase 2 based on user demand.

---

Q: What's the path to mainstream adoption?
A: (1) Get 50+ active users to prove the model works → (2) Attract 20+ independent miners → (3) Get listed/mentioned in developer newsletters → (4) Build integrations with popular AI development tools. We're at step 1 now.

---

### AMA 开场白

```
Hi everyone! I'm [Name], the founder of OpenClade.

OpenClade is a decentralized Claude API service built on Bittensor's TAO subnet. Users get Claude at 25-35% of official price, and Miners earn TAO for providing API capacity.

We launched [X] days ago, and so far:
- [N] registered users
- [Y] tokens processed
- [Z] active miners
- [%] average uptime

I'm here to answer anything — technical details, economic model, risks, how Bittensor works, etc. No question is too basic or too hard.

AMA!
```

---

*文档版本: v1.0 | 最后更新: 2026-03-15*
