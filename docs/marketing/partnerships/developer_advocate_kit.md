# Developer Advocate Content Kit

**Purpose:** Ready-to-submit materials for developer community directories, awesome lists, and comparison platforms. These generate high-quality backlinks and discovery traffic.

---

## 1. Awesome List Submissions

### awesome-ai-tools / awesome-llm

**Submission Template (PR description):**

```markdown
## Add OpenClade — Affordable Claude API via Bittensor

- [OpenClade](https://openclade.com) — Claude API access at 65-90% below official pricing, powered by Bittensor TAO subnet. OpenAI SDK compatible, one-line migration. Free tier available.
```

**Target Repositories:**
- `awesome-ai-tools` — General AI tools directory
- `awesome-llm` — Large Language Model resources
- `awesome-bittensor` — Bittensor ecosystem projects
- `awesome-chatgpt` — ChatGPT/LLM API alternatives
- `awesome-generative-ai` — Generative AI resources
- `awesome-indie-hacking` — Tools for indie developers

**Category placement:** API Services / LLM APIs / Cost Optimization

---

### awesome-bittensor (Priority — ecosystem visibility)

```markdown
## Subnets

### OpenClade (Subnet [X])
- **Description:** Distributed Claude API service network. Users access Claude at 25-35% of official pricing. Miners provide API capacity and earn TAO emissions.
- **Website:** [openclade.com](https://openclade.com)
- **GitHub:** [github.com/openclaude](https://github.com/openclaude)
- **Miner Guide:** [Mining Documentation](https://openclade.com/docs/mining)
- **Status:** Live on Testnet / Mainnet
```

---

## 2. Comparison Platform Submissions

### AlternativeTo.net

**App Name:** OpenClade
**Category:** Developer Tools > API Services
**Alternative To:** Anthropic Claude API, OpenRouter, Amazon Bedrock
**Description:**

```
OpenClade provides Claude API access at 65-90% below Anthropic's official pricing. Powered by the Bittensor TAO subnet, it uses a decentralized network of miners who provide API capacity in exchange for TAO token emissions.

Key features:
- Claude Sonnet, Haiku, and Opus at 10-35% of official price
- OpenAI SDK compatible (change 1 line of code to migrate)
- Quality verified by on-chain validators
- Free tier available, no credit card required

How it works: Miners contribute Claude API keys and earn TAO tokens. The TAO emission subsidy allows OpenClade to charge users significantly less than Anthropic's direct rates. Validators ensure every response matches genuine Claude output quality.
```

**Tags:** AI, API, Claude, LLM, Developer Tools, Cost Optimization, Bittensor, Decentralized

---

### Product Hunt (already covered in producthunt/launch_kit.md)

### G2 Software

**Category:** AI Development Platforms
**One-liner:** Affordable Claude API access powered by decentralized infrastructure
**Pros to highlight:**
- Dramatically lower pricing than official API
- Zero migration effort (OpenAI SDK compatible)
- Transparent quality verification
- Free tier for evaluation

---

## 3. GitHub README Integration

### Project README Badge

```markdown
[![Claude API](https://img.shields.io/badge/Claude%20API-75%25%20cheaper-blue)](https://openclade.com)
```

### README Section Template (for OpenClade's own repo)

```markdown
## Quick Start

```bash
pip install openai
```

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-openclade-key",     # Get free key at openclade.com
    base_url="https://api.openclade.com/v1"
)

response = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)

print(response.choices[0].message.content)
```

That's it. Same SDK, same code, 75% less cost.

### Pricing

| Model | OpenClade (Founding) | Anthropic Official | Savings |
|-------|---------------------|-------------------|---------|
| Sonnet Input | $0.30/M | $3.00/M | 90% |
| Sonnet Output | $1.50/M | $15.00/M | 90% |
| Haiku Input | $0.025/M | $0.25/M | 90% |
| Haiku Output | $0.125/M | $1.25/M | 90% |
| Opus Input | $1.50/M | $15.00/M | 90% |
| Opus Output | $7.50/M | $75.00/M | 90% |

### How It Works

OpenClade runs on the Bittensor TAO subnet. Miners provide Claude API capacity and earn TAO emissions. These emissions subsidize user pricing, making Claude accessible at a fraction of the cost.

Quality is enforced on-chain: validators compare miner responses against official Claude output. Miners with quality scores below threshold lose emissions.

[Read the full architecture →](https://openclade.com/docs/architecture)
```

---

## 4. Developer Directory Submissions

### Target Directories

| Directory | URL | Category | Priority |
|-----------|-----|----------|----------|
| AlternativeTo | alternativeto.net | API Services | P0 |
| Product Hunt | producthunt.com | Developer Tools | P0 (separate plan) |
| There's An AI For That | theresanaiforthat.com | API / Infrastructure | P0 |
| AI Tool Directory | aitoolsdirectory.com | Developer | P1 |
| Future Tools | futuretools.io | Developer Tools | P1 |
| Toolify.ai | toolify.ai | AI API | P1 |
| Ben's Bites Tools | tools.bensbites.co | API | P1 |
| SaaSHub | saashub.com | API Management | P2 |
| StackShare | stackshare.io | AI Services | P2 |

### Submission Checklist

For each directory:
- [ ] Short description (under 160 chars): "Claude API at 75% off official pricing. OpenAI SDK compatible. Powered by Bittensor."
- [ ] Long description (see AlternativeTo template above)
- [ ] Logo (needs design — flag to Board)
- [ ] Screenshots (blocked by gallery images — P0 blocker)
- [ ] Pricing info (Founding Member pricing table)
- [ ] Website URL
- [ ] GitHub URL

---

## 5. Dev.to / Hashnode Cross-Posting Strategy

### Articles to Cross-Post

| Article | Original Location | Cross-Post To | Canonical URL |
|---------|-------------------|---------------|---------------|
| How Bittensor Makes Claude Cheaper | blog/ | Dev.to + Hashnode | openclade.com/blog/... |
| Developer Migration Guide | blog/ | Dev.to | openclade.com/blog/... |
| Miner Economics Deep Dive | blog/ | Hashnode | openclade.com/blog/... |
| Claude API Pricing Guide 2026 | seo/ | Dev.to + Medium | openclade.com/blog/... |
| 5 Ways to Reduce Claude API Bill | seo/ | Dev.to | openclade.com/blog/... |

### Cross-Post Template (Dev.to front matter)

```yaml
---
title: "Article Title"
published: true
description: "Meta description"
tags: claude, ai, api, tutorial
canonical_url: https://openclade.com/blog/original-slug
cover_image: https://openclade.com/images/article-cover.png
---
```

**Important:** Always set `canonical_url` to openclade.com to avoid duplicate content penalties.

### Dev.to Tags to Use

- `#ai` — Largest AI tag
- `#claude` — Growing niche
- `#tutorial` — High engagement
- `#webdev` — Broad reach
- `#python` — For code-heavy articles
- `#startup` — For business/economics articles

---

## 6. GitHub Stars Strategy

### Actions to Increase Repo Visibility

1. **README excellence** — Complete quick start, pricing table, architecture diagram
2. **Contributing guide** — Lower barrier for community PRs
3. **Issue templates** — Bug reports, feature requests, miner applications
4. **GitHub Topics** — Add: `bittensor`, `claude`, `ai`, `api-proxy`, `llm`, `decentralized-ai`
5. **Discussions** — Enable GitHub Discussions for community Q&A
6. **Release notes** — Tag meaningful releases with changelogs
7. **Star prompt** — Add "If OpenClade saves you money, consider starring the repo" in README footer

---

## Execution Timeline

| Week | Action | Owner |
|------|--------|-------|
| W1 | Submit to awesome-bittensor, AlternativeTo | CMO |
| W1 | Cross-post first 2 articles to Dev.to | CMO |
| W2 | Submit to There's An AI For That, Toolify | CMO |
| W2 | Cross-post remaining articles | CMO |
| W3 | Submit to SaaSHub, StackShare, remaining directories | CMO |
| W4 | First backlink audit — identify which submissions generated traffic | CMO |
| Monthly | Refresh directory listings with updated metrics | CMO |

---

*Created: 2026-03-16 | Version: v1.0*
