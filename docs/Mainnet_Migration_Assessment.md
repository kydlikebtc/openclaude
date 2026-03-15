# OpenClaude Phase 7 Mainnet 迁移评估报告

**版本:** 1.0
**日期:** 2026-03-15
**负责人:** Founding Engineer
**关联 Issue:** KYD-24

---

## 执行摘要

本报告评估 OpenClaude 从 Bittensor Testnet 迁移至 Mainnet (Finney) 的技术路径、基础设施需求及成本模型。基于代码库全面分析，识别出 **7 个必须变更的配置项**，以及生产基础设施的 **3 个关键差距**。

**总体风险评级：MEDIUM** — 代码架构已针对 Mainnet 做了良好设计，主要工作集中在配置参数更新和 HA 基础设施搭建上。

---

## 一、Testnet vs Mainnet 差异分析

### 1.1 必须修改的硬编码配置

| 文件 | 参数 | Testnet 值 | Mainnet 值 | 优先级 |
|------|------|-----------|-----------|--------|
| `subnet/miner/config.py:29` | `subtensor_network` | `"test"` | `"finney"` | **CRITICAL** |
| `subnet/config/miner.example.yaml:11` | `subtensor_network` | `"test"` | `"finney"` | **CRITICAL** |
| `subnet/miner/config.py:26` | `netuid` default | `1` | 实际分配的 subnet UID | **CRITICAL** |
| `subnet/config/miner.example.yaml:8` | `netuid` | `1` | 实际分配的 subnet UID | **CRITICAL** |
| `subnet/neurons/validator.py:219` | `--netuid` default | `1` | 实际分配的 subnet UID | HIGH |
| `backend/app/core/config.py:14` | `secret_key` default | `"changeme-..."` | 生产密钥（已有 .env.prod 处理） | HIGH |
| `backend/app/core/config.py:24` | `cors_origins` | localhost | `["https://openclaude.io"]` | MEDIUM |

### 1.2 良好的配置设计（无需修改）

代码已正确支持环境变量覆盖：
- `MinerConfig.load()` 支持 `OPENCLAUDE_API_KEYS` 环境变量（`config.py:73`）
- `subtensor_network` 在 Miner 中完全通过 YAML 配置驱动（`neurons/miner.py:48`）
- Validator 通过 `bt.subtensor(config=config)` 读取 argparse 参数（`neurons/validator.py:45`）
- Backend 通过 `pydantic_settings` 读取 `.env` 文件，生产模板已存在（`.env.prod.example`）
- Docker Compose 生产配置（`docker-compose.prod.yml`）已完善，所有敏感值使用环境变量

### 1.3 Mainnet 特有限制（需了解）

- **Mainnet `finney` 网络端点**: `wss://entrypoint-finney.opentensor.ai:443`
- **每个 Subnet 最多 256 个 UID**（64 Validators + 192 Miners）
- **权重提交间隔**: 生产中建议 `WEIGHT_SUBMISSION_INTERVAL_BLOCKS = 100`（当前代码已正确设置，`validator.py:21`）
- **dTAO 影响（2025-02 起）**: 每个子网现有独立 alpha token，TAO 发行基于净质押流量而非代币价格

### 1.4 需要新增的 Mainnet 配置项

```yaml
# 需要在 miner.example.yaml 新增的生产配置
subtensor_network: "finney"
netuid: <ASSIGNED_UID>          # 注册后填入
axon_ip: "<PUBLIC_IP>"          # 生产环境必须显式指定公网 IP
min_stake_tao: 1000.0           # Mainnet 验证者质押门槛为 1000 TAO
max_concurrent_requests: 50     # 生产负载增加
request_timeout_sec: 120        # 生产超时适当延长
```

---

## 二、TAO 质押准备

### 2.1 Subnet 注册成本（子网所有者）

Bittensor 使用**动态定价**机制：每次注册后费用翻倍，若无人注册则每 4 天减半至底线。

| 场景 | TAO 需求 | USD 估算（@$300/TAO） |
|------|---------|---------------------|
| **当前底线（低需求时）** | ~100 TAO | ~$30,000 |
| **当前市场估算（2026 Q1）** | ~300–500 TAO | ~$90,000–$150,000 |
| **高峰期（历史 2024 峰值）** | 3,000–5,000 TAO | $900K–$1.5M |
| **建议预备资金（保守）** | **500 TAO** | **~$150,000** |

> ⚠️ **注意：** Subnet 注册费用为 **不可退还的沉没成本**（TAO 被销毁/循环利用）。
> 实时费用查询：`btcli subnet list` 或访问 [taostats.io/subnets](https://taostats.io/subnets)

### 2.2 Validator 节点运营质押

| 需求 | TAO 量 | 备注 |
|------|--------|------|
| 神经元注册（每个 UID） | 0.05–100 TAO | 动态，通常 < 2 TAO |
| 验证者许可门槛 | **≥ 1,000 TAO 质押权重** | 进入 Top 64 UID 竞争 |
| 建议初始运营质押 | **1,500 TAO** | 包含缓冲，应对波动 |

**质押权重公式**：
`stake_weight = alpha_stake + tao_stake × tao_weight(0.18)`

### 2.3 时间窗口建议

```
W13 (当前周):   确认 TAO 持仓和钱包准备
W14:            监控 Mainnet 注册成本，在合理窗口期执行注册
W15-16:         Validator 质押，等待 Top 64 确认
W17+:           正式开放 Miner 注册
```

---

## 三、生产基础设施规划

### 3.1 当前架构缺口评估

当前 `docker-compose.prod.yml` **存在以下生产缺口**：

| 缺口 | 风险 | 建议 |
|------|------|------|
| 单 Backend 实例 | 单点故障 | 水平扩展至 3+ 副本 |
| 单 PostgreSQL 节点 | 数据丢失风险 | 主从复制 + 自动备份 |
| 单 Redis 节点 | 缓存不可用 | Redis Sentinel 或 Cluster |
| 无 SSL 证书管理 | 部署摩擦 | Let's Encrypt + cert-manager |
| Nginx 无上游 HA | 前端单点 | 多 backend 轮询 |
| 监控数据保留 30d | 历史分析有限 | 90d + 冷备 |

### 3.2 推荐服务器规格

#### **Validator 节点（推荐 3 节点 HA）**

| 规格项 | 最低配置 | 推荐配置 |
|--------|---------|---------|
| CPU | 4 核 | 8 核 |
| 内存 | 16 GB | 32 GB |
| 存储 | 200 GB SSD | 500 GB NVMe SSD |
| 带宽 | 100 Mbps | 1 Gbps |
| 网络延迟（到 Finney 链） | < 100ms | < 50ms |
| 操作系统 | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

#### **Miner 节点（按需扩展）**

| 规格项 | 单节点配置 | 备注 |
|--------|----------|------|
| CPU | 4 核 | 高并发需 8+ 核 |
| 内存 | 8 GB | 支持 10+ 并发请求 |
| 存储 | 50 GB SSD | 日志和缓存 |
| 带宽 | 100 Mbps | Claude API 调用延迟优先 |
| 公网 IP | 必须 | Bittensor axon 需要 |

#### **Backend API 集群（Web 服务层）**

| 组件 | 规格 | 节点数 |
|------|------|--------|
| API Server | 4 核 8G | 3（负载均衡） |
| PostgreSQL Primary | 8 核 32G + 500G SSD | 1 |
| PostgreSQL Replica | 4 核 16G + 500G SSD | 2 |
| Redis | 4 核 8G | 3（Sentinel 模式） |
| Nginx/LB | 2 核 4G | 2（主备） |

### 3.3 云服务商成本对比（月度估算）

| 云厂商 | 方案 | 月度成本 | 优劣 |
|--------|------|---------|------|
| **AWS（推荐）** | EC2 c5.2xlarge × 3 API + RDS Multi-AZ + ElastiCache | $1,800–$2,500 | 全球覆盖，文档完善 |
| **GCP** | Compute Engine n2-standard-8 × 3 + Cloud SQL HA | $1,600–$2,200 | 亚洲区延迟好 |
| **Digital Ocean** | Droplet 8GB × 5 + Managed DB + Redis | $600–$900 | 低成本，简单易用 |
| **Hetzner（欧洲/亚洲）** | CX51 × 5 + Managed DB | $300–$500 | 极低成本，裸金属 |

> 💡 **建议**: 初期使用 **Digital Ocean + Hetzner 组合**（成本低，易管理），待流量稳定后迁移 AWS 实现 SLA 保证。

### 3.4 高可用配置方案

Nginx 需要更新以支持 Backend 多副本：

```nginx
# 将 docker-compose.prod.yml 中的 nginx 配置修改为：
upstream backend {
    server backend_1:8000;
    server backend_2:8000;
    server backend_3:8000;
    keepalive 64;
}
```

---

## 四、性能瓶颈分析

### 4.1 当前架构瓶颈

| 组件 | 潜在瓶颈 | 优化建议 |
|------|---------|---------|
| FastAPI (`Dockerfile.prod:CMD`) | 4 workers 固定 | 使用 `$(nproc)` 动态配置 workers |
| DB 连接池 (`database.py:13-16`) | pool_size=10, overflow=20 | Mainnet 流量增加需调整为 20/40 |
| nginx rate limit (`nginx.prod.conf`) | API: 30r/m, Auth: 5r/m | 生产需调整为 300r/m |
| Redis 单点 (`docker-compose.prod.yml`) | 单 Redis 节点 | 切换 Redis Sentinel |

### 4.2 Claude API 调用链路

```
Miner → Anthropic API (延迟 500ms–5s)
         └─ min_stake_tao 验证（已实现）
         └─ 并发限制 max_concurrent_requests=10（生产需增加至 50）
         └─ 超时 request_timeout_sec=60（生产建议 120s）
```

---

## 五、安全加固（基础设施层）

### 5.1 已完成项 ✅

- Backend 运行非 root 用户（`Dockerfile.prod:34-38`）
- nginx 安全 Header（X-Frame-Options, X-XSS-Protection 等）
- API Rate Limiting（nginx 层 + Redis 中间件）
- JWT 认证（`config.py:21-23`）
- 生产环境变量隔离（`.env.prod.example`）

### 5.2 需要实施的安全措施

| 措施 | 优先级 | 工作量 |
|------|--------|--------|
| Bittensor 钱包密钥加密存储（HSM/Vault） | **CRITICAL** | 中 |
| 防火墙规则：Axon 端口 8091 仅对 Validators 开放 | HIGH | 小 |
| DDoS 防护（Cloudflare/AWS Shield） | HIGH | 小 |
| 数据库加密备份（至少每日，保留 30 天） | HIGH | 中 |
| SSL/TLS 证书自动续期（cert-manager） | MEDIUM | 小 |
| 网络隔离：VPC 内部通信，不暴露 DB | HIGH | 中 |

---

## 六、迁移执行计划

### 6.1 迁移前置条件 Checklist

- [ ] Testnet 上验证完整的 Validator-Miner 评分周期（KYD-22 完成）
- [ ] TAO 资金到位（Subnet 注册 + Validator 质押共 ~2,000 TAO）
- [ ] 生产服务器预配置完成（VPC、安全组、SSH 密钥）
- [ ] 生产 `.env.prod` 所有变量填写完毕
- [ ] SSL 证书部署完成
- [ ] 监控告警配置完毕（Grafana Dashboard）

### 6.2 迁移执行步骤

```
阶段 1 — 子网注册（W14）
├─ 1.1 实时查询 Mainnet 注册成本（btcli subnet list）
├─ 1.2 选择成本低谷窗口执行注册
├─ 1.3 记录分配到的 netuid（保存至文档和 Secrets Manager）
└─ 1.4 更新所有配置文件中的 netuid 值

阶段 2 — 基础设施部署（W14-15）
├─ 2.1 创建生产服务器（Validator × 3，Backend × 3，DB 主从）
├─ 2.2 部署 docker-compose.prod.yml 全栈
├─ 2.3 配置 SSL 证书（Let's Encrypt）
├─ 2.4 配置 DNS（api.openclaude.io → Backend LB）
└─ 2.5 验证健康检查端点（/health）

阶段 3 — Validator 注册（W15）
├─ 3.1 Validator 节点使用 finney 网络注册（register_subnet.py --network finney）
├─ 3.2 质押 ≥ 1,000 TAO 到 Validator hotkey
├─ 3.3 等待并验证进入 Top 64 Validator
└─ 3.4 启动 Validator 主循环，验证权重提交

阶段 4 — 灰度 Miner 开放（W16）
├─ 4.1 发布 Miner 配置模板（miner.example.yaml with finney + actual netuid）
├─ 4.2 邀请 5–10 名测试 Miner 注册
├─ 4.3 监控 Validator 评分结果（7 天观察期）
└─ 4.4 全面开放 Miner 注册

阶段 5 — 稳定性验证（W17-18）
├─ 5.1 持续监控 Yuma Consensus 权重分布
├─ 5.2 验证 Miner 收益分配正确性
├─ 5.3 性能压测（目标：100+ 并发请求）
└─ 5.4 发布 Mainnet 公告
```

### 6.3 回滚方案

如 Mainnet 出现关键问题：
1. **立即**: Validator 停止权重提交（停止 `validator.py` 进程）
2. **短期**: 子网进入"维护模式"，发布公告说明
3. **资金保护**: Validator 质押可按需解押（等待 unbonding 期）
4. **注意**: Subnet 注册费用**不可退还**，但 Validator 质押可恢复

---

## 七、成本汇总模型

### 7.1 上线成本（一次性）

| 项目 | 最低 | 建议 |
|------|------|------|
| Subnet 注册（TAO） | 100 TAO | 500 TAO 预备 |
| Validator 质押（TAO） | 1,000 TAO | 1,500 TAO |
| 神经元注册（TAO × 3 nodes） | 6 TAO | 10 TAO |
| 服务器初始化 | $500 | $1,000 |
| **小计（TAO）** | **~1,100 TAO** | **~2,010 TAO** |
| **小计（USD @ $300/TAO）** | **~$330,000** | **~$603,000** |

### 7.2 月度运营成本（稳定运行）

| 项目 | 月度成本（USD） |
|------|----------------|
| 服务器（Digital Ocean + Hetzner 方案） | $600–$900 |
| 监控工具（Grafana Cloud 等） | $50–$200 |
| Anthropic API 费用（转发成本） | 按用量（25% 报价比） |
| **固定月度成本** | **$650–$1,100** |

---

## 八、关键风险矩阵

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Subnet 注册成本高于预算 | 中 | 高 | 监控成本，选择低谷窗口注册 |
| 进不了 Top 64 Validators | 低 | 高 | 初始质押 1,500 TAO，留充足缓冲 |
| dTAO 机制变化影响收益 | 中 | 中 | 持续跟踪 Bittensor 官方公告 |
| Miner 注册踊跃导致 netuid 占用 | 低 | 低 | 先注册子网，再公开招募 |
| 生产 DB 故障 | 低 | 极高 | 主从复制 + 每日备份 |

---

## 附录：代码修改清单

执行 Mainnet 迁移时，需要对以下文件进行修改：

```bash
# 1. 更新默认网络和 netuid（获得实际 netuid 后执行）
# subnet/miner/config.py
# - subtensor_network: str = "test"  →  "finney"
# - netuid: int = 1  →  <ACTUAL_NETUID>

# 2. 更新配置示例文件
# subnet/config/miner.example.yaml
# - subtensor_network: "test"  →  "finney"
# - netuid: 1  →  <ACTUAL_NETUID>
# - axon_ip: "1.2.3.4"  # 取消注释，填入实际公网 IP

# 3. 更新 validator 默认 netuid
# subnet/neurons/validator.py:219
# - parser.add_argument("--netuid", type=int, default=1  →  default=<ACTUAL_NETUID>

# 4. 更新 nginx rate limits（生产流量）
# nginx/nginx.prod.conf
# - rate=30r/m  →  rate=300r/m（API）
# - rate=5r/m   →  rate=20r/m（Auth）

# 5. 更新 Backend worker 数量
# backend/Dockerfile.prod
# - "--workers", "4"  →  "--workers", "$(nproc)"
```

---

*报告由 Founding Engineer 基于代码库分析和链上数据生成。*
*TAO 价格参考：$300/TAO（估算，请以实际市场价为准）。*
