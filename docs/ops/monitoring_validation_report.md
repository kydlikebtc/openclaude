# OpenClaude 监控告警体系 Phase 1 验证报告

> 版本：v1.0 | 审查日期：2026-03-15 | 审查人：Operations Manager

---

## 一、执行摘要

本报告对 KYD-27 中 Backend Engineer 构建的监控基础设施进行全面评审，发现 **1 个关键缺口**、**2 个高优先级问题**和 **3 个中低优先级改进点**。核心问题是：**4 个自定义业务指标未在 Backend 代码中实现**，导致 Miner 相关告警和 Token 消耗告警永远无法触发。

**整体评分：60/100**（基础框架完善，关键业务指标缺失）

---

## 二、基础设施审查结果

### 2.1 Docker Compose 服务清单

| 服务 | 状态 | 备注 |
|------|------|------|
| `prometheus` | ✅ 配置正确 | v2.47.0，30天数据保留 |
| `alertmanager` | ✅ 配置正确 | v0.26.0 |
| `grafana` | ✅ 配置正确 | v10.1.0，预置 Dashboard |
| `postgres-exporter` | ✅ 配置正确 | v0.15.0 |
| `redis-exporter` | ✅ 配置正确 | v1.55.0 |
| `nginx-exporter` | ⚠️ 依赖 nginx stub_status | 需确认 nginx.prod.conf 已开启 `/stub_status` |
| `node-exporter` | ✅ 配置正确 | v1.6.1，系统资源监控 |

### 2.2 Prometheus 采集配置

- ✅ `prometheus.yml` 配置完整，采集 7 个 job
- ✅ 告警规则文件正确挂载 (`/etc/prometheus/alert_rules.yml`)
- ✅ Alertmanager 连接配置正确（Docker 内部 DNS）
- ✅ Backend 抓取间隔 10s（比全局 15s 更频繁，合理）

### 2.3 Backend 指标端点

- ✅ `main.py` 已集成 `prometheus_fastapi_instrumentator`，暴露 `/metrics` 端点
- ✅ 自动收集 `http_requests_total` 和 `http_request_duration_seconds` 指标
- ✅ `status` 标签格式为分组模式（`2xx`、`4xx`、`5xx`），与告警规则 `status=~"5.."` 兼容

---

## 三、告警规则审查

### 3.1 HTTP 指标告警（依赖 prometheus_fastapi_instrumentator）

| 告警名 | PromQL 正确性 | 标签正确性 | SLO 对齐 |
|--------|-------------|----------|---------|
| `HighAPILatency` | ✅ | ✅ | ⚠️ 阈值 3s（SLO 2s，建议双层） |
| `HighErrorRate` | ✅ | ✅ | ✅ |
| `BackendDown` | ✅ | ✅ | ✅ |

### 3.2 Miner 指标告警（依赖自定义指标）

| 告警名 | 所需指标 | 指标是否实现 |
|--------|---------|------------|
| `MinerOffline` | `openclaude_miner_heartbeat_age_seconds` | ❌ **未实现** |
| `MinerPoolEmpty` | `openclaude_miner_pool_size` | ❌ **未实现** |
| `LowMinerAvailability` | `openclaude_miner_pool_size` + `openclaude_miner_total_registered` | ❌ **未实现** |
| `TokenUsageSpike` | `openclaude_tokens_consumed_total` | ❌ **未实现** |

> 🚨 **关键问题**：上述 4 个告警当前永远不会触发，因为依赖的 Prometheus 指标在 Backend 代码中不存在。

### 3.3 基础设施告警（依赖标准 Exporter）

| 告警名 | 所需指标来源 | 状态 |
|--------|-----------|------|
| `PostgreSQLDown` | postgres-exporter | ✅ 当 exporter 启动后有效 |
| `RedisDown` | redis-exporter | ✅ 当 exporter 启动后有效 |
| `DiskSpaceHigh` | node-exporter | ✅ |
| `MemoryUsageHigh` | node-exporter | ✅ |
| `CPUUsageHigh` | node-exporter | ✅ |

### 3.4 告警阈值 vs SLO 对比

| SLO 指标 | 目标值 | 严重阈值 | 当前告警阈值 | 问题 |
|---------|--------|---------|------------|------|
| API Uptime | 99.9% | <99% | BackendDown: 1min | ✅ 合理 |
| P95 Latency | <2s | >5s | HighAPILatency: 3s (warning only) | ⚠️ 缺少 critical 层（>5s） |
| Error Rate | <1% | >5% | HighErrorRate: 5% | ✅ 对齐 critical 阈值（但缺 warning 层） |
| Miner Online Rate | >90% | <70% | LowMinerAvailability: 50% | ⚠️ 阈值过低（应≤70%触发 critical） |

---

## 四、SOP 文档可行性评审

### 4.1 `incident_response.md`

| 项目 | 评估 |
|------|------|
| 事件分级标准 | ✅ 清晰（P0-P3 定义完整） |
| 响应时间承诺 | ✅ P0 15分钟 / P1 30分钟 |
| 快速确认命令 | ✅ 可直接执行 |
| 联系方式 | ⚠️ 全为占位符，需填写真实联系方式 |
| Post-Mortem 模板 | ✅ 格式完整 |

### 4.2 `key_ban_response.md`

| 项目 | 评估 |
|------|------|
| 自动检测方法 | ✅ Prometheus + 手动 |
| 手动封禁步骤 | ✅ Redis ZREM + API 双路径 |
| 恢复流程 | ✅ 完整 |
| Miner 通知模板 | ✅ 中文模板完整 |
| 验证自动切换 | ⚠️ 依赖 Admin API（需确认 `/api/v1/admin/miners` 已实现） |

### 4.3 `scaling.md`

| 项目 | 评估 |
|------|------|
| 扩容触发条件 | ✅ 量化阈值明确 |
| Backend 水平扩容 | ✅ Docker Compose scale 命令 |
| 数据库扩容 | ✅ 连接池优化 → 只读副本路径 |
| 部署回滚 | ✅ Alembic downgrade + git revert |
| 容量规划表 | ✅ 按 DAU 级别分档 |
| Nginx 负载均衡 | ⚠️ 当前 nginx.prod.conf 需验证 upstream 配置是否支持多实例 |

---

## 五、关键问题 & 行动计划

### P0 — 关键（必须在本周修复）

**[OPS-001] 实现 4 个自定义 Prometheus 指标**

需要 Backend Engineer 在 `backend/app/` 中添加以下 Prometheus Gauge/Counter：

```python
from prometheus_client import Gauge, Counter

# Miner 心跳年龄（每个 miner_id 独立，由路由引擎更新）
miner_heartbeat_age = Gauge(
    'openclaude_miner_heartbeat_age_seconds',
    'Seconds since last miner heartbeat',
    ['miner_id', 'hotkey']
)

# Miner 池当前活跃数
miner_pool_size = Gauge(
    'openclaude_miner_pool_size',
    'Number of active miners in the routing pool'
)

# 注册的 Miner 总数
miner_total_registered = Gauge(
    'openclaude_miner_total_registered',
    'Total number of registered miners'
)

# 累计消耗 Token 数
tokens_consumed = Counter(
    'openclaude_tokens_consumed_total',
    'Total tokens consumed',
    ['model', 'user_tier']
)
```

这些指标应在 `miner_service.py` 和 `billing_service.py` 中的关键路径上更新。

### P1 — 高优先级（本周完成）

**[OPS-002] 告警阈值双层化**

当前 `HighAPILatency` 只有一个 warning 层。应添加 critical 层：

```yaml
# Warning: P95 > 2s（SLO 目标边界）
- alert: HighAPILatencyWarning
  expr: histogram_quantile(0.95, ...) > 2
  for: 2m
  labels: {severity: warning}

# Critical: P95 > 5s（SLO 严重阈值）
- alert: HighAPILatencyCritical
  expr: histogram_quantile(0.95, ...) > 5
  for: 1m
  labels: {severity: critical}
```

**[OPS-003] 修正 LowMinerAvailability 阈值**

当前阈值 50% 远低于 SLO 严重阈值（70%）：

```yaml
# 应改为：在线率 < 90% 告警（warning），< 70% 告警（critical）
```

**[OPS-004] 配置 Alertmanager 实际通知渠道**

当前所有接收者指向 `localhost:9999/webhook`（占位符）。需配置真实通知：
- 飞书/钉钉 Webhook（推荐，团队常用）
- 或 Slack Webhook

### P2 — 中优先级（下周完成）

**[OPS-005] 补充 Grafana Miner 专属 Dashboard 面板**

自定义指标实现后，添加：
- Miner 在线率趋势
- 各 Miner 响应成功率
- Token 消耗速率

**[OPS-006] 填写 SOP 联系方式**

`incident_response.md` 中的联系方式需填写真实信息。

**[OPS-007] 验证 nginx stub_status 配置**

确认 `nginx/nginx.prod.conf` 中已启用：
```nginx
location /stub_status {
    stub_status on;
    allow 172.0.0.0/8;  # 只允许 Docker 内网
    deny all;
}
```

---

## 六、生产就绪检查清单

```
基础设施
  [x] Prometheus + Grafana + Alertmanager 配置完整
  [x] 所有标准 Exporter 已配置
  [x] Backend /metrics 端点已暴露
  [ ] 自定义业务指标实现（OPS-001）
  [ ] Alertmanager 通知渠道配置（OPS-004）

告警规则
  [x] HTTP 指标告警（BackendDown, HighErrorRate, HighAPILatency）
  [x] 基础设施告警（DB/Redis/磁盘/内存/CPU）
  [ ] Miner 告警需自定义指标支撑（OPS-001）
  [ ] 告警阈值与 SLO 对齐（OPS-002, OPS-003）

SOP 文档
  [x] 事件响应流程（P0-P3 分级）
  [x] Miner Key 封禁预案
  [x] 系统扩容流程
  [ ] 联系方式待填写（OPS-006）
```

---

## 七、下一步行动

| 优先级 | 负责人 | 任务 | 截止日期 |
|--------|--------|------|---------|
| P0 | Backend Engineer | 实现 4 个自定义 Prometheus 指标 | 3天内 |
| P1 | Operations Manager | 更新告警规则（双层阈值 + Miner 阈值） | 本周 |
| P1 | Operations Manager | 配置飞书/Slack Webhook 通知 | 本周 |
| P2 | Operations Manager | 补充 Miner Grafana Dashboard | 下周 |
| P2 | Operations Manager | 验证 Nginx stub_status | 下周 |
