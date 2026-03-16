<p align="center">
  <img src="https://img.shields.io/badge/OpenClade-Decentralized%20Claude%20API-8B5CF6?style=for-the-badge&logoColor=white" alt="OpenClade">
</p>

<h1 align="center">OpenClade</h1>

<p align="center">
  <strong>Decentralized Claude API Network on Bittensor</strong>
</p>

<p align="center">
  Use Claude models at 25-35% of the official price, powered by a decentralized miner network and Bittensor's TAO incentives.
</p>

<p align="center">
  <a href="https://github.com/kydlikebtc/openclaude/actions"><img src="https://img.shields.io/github/actions/workflow/status/kydlikebtc/openclaude/ci.yml?branch=main&style=for-the-badge&label=CI" alt="CI"></a>
  <a href="https://github.com/kydlikebtc/openclaude/releases"><img src="https://img.shields.io/github/v/release/kydlikebtc/openclaude?include_prereleases&style=for-the-badge" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License"></a>
  <a href="https://bittensor.com"><img src="https://img.shields.io/badge/Network-Bittensor-000000?style=for-the-badge" alt="Bittensor"></a>
  <a href="https://anthropic.com"><img src="https://img.shields.io/badge/API-Anthropic%20Claude-D97706?style=for-the-badge" alt="Claude API"></a>
</p>

<p align="center">
  <a href="README_CN.md">中文</a> · <a href="docs/Architecture.md">Architecture</a> · <a href="docs/User_Guide.md">User Guide</a> · <a href="docs/Miner_Guide.md">Miner Guide</a> · <a href="docs/API_Reference.md">API Reference</a>
</p>

---

## What is OpenClade?

OpenClade is a decentralized Claude API service network built on the [Bittensor](https://bittensor.com) protocol. It connects users who need affordable access to Claude models with miners who contribute their API keys to earn TAO rewards.

| Participant | Value |
|---|---|
| **Users** | Access Claude latest models at **25-35%** of official pricing |
| **Miners** | Monetize idle Claude API keys, earn TAO mining rewards |
| **Validators** | Assess service quality, maintain network integrity, earn TAO dividends |

---

## Highlights

- **Drop-in compatible** — OpenAI SDK-compatible API. Switch `base_url` and you're done.
- **Smart routing** — requests are routed to the highest-scoring miners via a weighted selection engine.
- **Multi-dimensional scoring** — miners are rated on latency, uptime, probe success rate, and contribution volume.
- **On-chain incentives** — TAO emission is distributed via Bittensor's Yuma Consensus.
- **Referral system** — miners earn bonus weight for bringing new users to the network.
- **Full observability** — Prometheus + Grafana monitoring stack with SLO alerting.
- **Battle-tested** — 247 backend tests passing at 98.61% coverage.

---

## Architecture

```
User Request (OpenAI-compatible format)
    │
    ▼
OpenClade API Gateway
    │  Authentication · Rate Limiting · Load Balancing
    ▼
Smart Router
    │  Weighted selection based on miner scores
    ├──────────────────────────────┐
    ▼                              ▼
Miner Node 0                 Miner Node N
  Axon Server                   Axon Server
    │  Claude API proxy            │
    │  API Key pool rotation       │
    ▼                              ▼
Anthropic Claude API          Anthropic Claude API
    │                              │
    └──────────────┬───────────────┘
                   ▼
         Validator Node
           · Periodic probe sampling
           · Multi-dimensional scoring
           · Weight submission to chain
                   │
                   ▼
        Bittensor Blockchain
           · Yuma Consensus
           · TAO Emission Distribution
```

### TAO Emission Split

```
TAO Emission
├── Owner       18%  — Subnet operator revenue
├── Miners      41%  — Distributed by score
└── Validators  41%  — Distributed by validation quality
```

---

## Quick Start

### For Users — API Access

```python
import anthropic

# Just change the base_url — zero code changes needed
client = anthropic.Anthropic(
    api_key="your-openclade-api-key",
    base_url="https://api.openclade.io",
)

message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}],
)
print(message.content[0].text)
```

### For Miners — Node Setup

```bash
# 1. Clone
git clone https://github.com/kydlikebtc/openclaude.git
cd openclaude/subnet

# 2. Install dependencies
uv sync

# 3. Configure
cp config/miner.example.yaml config/miner.yaml
# Edit miner.yaml: add your ANTHROPIC_API_KEY and wallet info

# 4. Register on the subnet (requires TAO)
uv run python scripts/register_miner.py \
  --netuid <OPENCLADE_NETUID> \
  --wallet.name <your_wallet> \
  --wallet.hotkey <your_hotkey>

# 5. Start mining
uv run python neurons/miner.py --config config/miner.yaml
```

### Requirements

- Python 3.11+
- bittensor >= 10.0.0
- anthropic >= 0.40.0

---

## Miner Scoring

Miners must meet **all** thresholds to earn rewards:

| Metric | Threshold |
|---|---|
| Probe Success Rate | >= 90% |
| Uptime | >= 80% |
| Average Latency | <= 3,000ms |
| Minimum Stake | >= 5 TAO |

**Score formula:**

```
Final Score = Service Score × (1 + Referral Bonus)

Service Score = Contribution Score × W1 + Standby Score × W2
  Contribution = Miner's token share of total network volume
  Standby = Uptime × 0.5 + Probe Success Rate × 0.5

Referral Bonus = min(referred_user_spend_ratio × 2 × 30%, 30%)
```

---

## Roadmap

| Phase | Status | Description |
|---|---|---|
| **Phase 1** — Core Subnet | Done | Miner/Validator nodes, LLMAPISynapse protocol, Claude API proxy |
| **Phase 2** — Incentive System | Done | Multi-dimensional scoring, Yuma Consensus, API key pool management |
| **Phase 3** — User Platform | Done | Registration, billing, API key management, usage analytics, referrals |
| **Phase 4** — Security Hardening | Done | OWASP Top 10 audit, JWT hardening, rate limiting, input validation |
| **Phase 5** — Observability | Done | Prometheus + Grafana, SLO alerting, structured logging, 100% test coverage |
| **Phase 6** — Testnet | In Progress | Wallet creation, local E2E verified, subnet registration pending |
| **Phase 7** — Mainnet | Planned | Production deployment, miner recruitment, public launch |

---

## Project Structure

```
openclaude/
├── subnet/                    # Bittensor subnet core
│   ├── neurons/               # Miner & Validator nodes
│   ├── protocol/              # LLMAPISynapse protocol
│   ├── miner/                 # Miner config & key pool
│   ├── validator/             # Scoring engine
│   ├── scripts/               # Registration scripts
│   ├── config/                # Example configs
│   └── tests/                 # 121 unit tests (100% coverage)
├── backend/                   # FastAPI backend
│   └── app/
│       ├── api/v1/            # REST API routes
│       └── services/          # Business logic
├── frontend/                  # Next.js frontend
│   └── src/app/
│       ├── (user)/            # User console
│       ├── (miner)/           # Miner dashboard
│       └── (admin)/           # Admin panel
├── monitoring/                # Prometheus + Grafana configs
├── docs/                      # Documentation
├── docker-compose.yml
└── docker-compose.prod.yml
```

---

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/Architecture.md) | System architecture and design |
| [API Reference](docs/API_Reference.md) | REST API documentation |
| [User Guide](docs/User_Guide.md) | Getting started for users |
| [Miner Guide](docs/Miner_Guide.md) | Miner setup and operations |
| [Incentive Mechanism](docs/incentive_mechanism.md) | Detailed scoring and reward design |
| [Launch Checklist](docs/Launch_Checklist.md) | Pre-launch verification list |
| [Business Plan](OpenClade_Business_Plan.md) | Business model and projections |

---

## Contributing

Issues and PRs are welcome. Please read the [Contributing Guide](CONTRIBUTING.md) before submitting.

---

## License

[MIT License](LICENSE)
