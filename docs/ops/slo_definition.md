# OpenClade SLO 定义

> 版本：v1.1 | 更新日期：2026-03-16 | 维护者：Operations Manager
> v1.0 → v1.1 变更：根据运营数据（2026-03-16 健康报告），拆分延迟 SLO 为三层体系

---

## 一、SLO 总览

| SLO | 指标 | 目标 | 严重阈值 | 说明 |
|-----|------|------|---------|------|
| **API 可用性** | 5xx 错误率 | < 1% | > 5% | 服务级别 |
| **API Uptime** | 正常运行时间 | 99.9% | < 99% | 月度统计 |
| **路由开销 P95** | `openclaude_routing_overhead_seconds` P95 | < 200ms | > 500ms | 系统效率 |
| **TTFB P95** | `http_request_duration_seconds` P95 | < 2s | > 5s | 用户体验 |
| **完整响应时间** | — | 无硬性 SLO | — | 依赖 Claude API |
| **Miner 在线率** | 活跃 Miner / 注册 Miner | > 90% | < 70% | 供给侧可用性 |
| **Validator 探测成功率** | 探测成功数 / 总探测数 | > 95% | < 85% | 链上健康 |

---

## 二、延迟 SLO 三层体系

### 背景

OpenClade 是 Claude API 的代理层。完整请求的端到端时间 = **路由开销** + **LLM 处理时间**，而 LLM 处理时间由 Claude API 决定（通常 1-30s），不在 OpenClade 控制范围内。因此，使用单一 P95 < 2s 的 SLO 既不合理也无法达成。

### 三层定义

#### 层 1：路由/代理开销 (Routing Overhead)

- **定义**：从收到请求到转发给 Miner 的时间，不含 LLM 处理等待
- **SLO 目标**：P95 < **200ms**
- **严重阈值**：P95 > **500ms**（触发 P1 告警）
- **指标**：`openclaude_routing_overhead_seconds`（需 Backend 实现自定义 Histogram）
- **状态**：⚠️ 指标待实现（Backend Engineer 任务）
- **超标可能原因**：Miner 选择算法慢、Redis 连接超时、数据库查询慢

#### 层 2：端到端 TTFB (Time to First Byte)

- **定义**：从收到请求到向客户端发出第一个字节的时间
- **SLO 目标**：P95 < **2s**（适用于流式响应场景）
- **严重阈值**：P95 > **5s**（触发 P1 告警）
- **指标**：`http_request_duration_seconds`（`prometheus_fastapi_instrumentator` 自动采集）
- **状态**：✅ 已实现
- **说明**：该指标在流式响应场景下记录的是首字节时间，不是完整响应时间
- **超标可能原因**：Claude API 上游延迟高、所有 Miner 繁忙、网络问题

#### 层 3：完整响应时间 (Full Response Time)

- **定义**：从收到请求到响应完全传输完毕
- **SLO**：**无硬性 SLO** — 完全依赖 Claude API 的生成速度
- **监控方式**：记录 P50/P95/P99 供趋势分析，不触发告警
- **说明**：长文档生成可能需要 30s+，属正常行为

---

## 三、SLO 告警映射

| 触发条件 | 告警名 | 级别 | 响应时间 |
|---------|--------|------|---------|
| 路由开销 P95 > 200ms 持续 2min | `HighRoutingOverheadWarning` | P2 | 1小时 |
| 路由开销 P95 > 500ms 持续 1min | `HighRoutingOverheadCritical` | P1 | 15分钟 |
| TTFB P95 > 2s 持续 2min | `HighAPILatencyWarning` | P2 | 1小时 |
| TTFB P95 > 5s 持续 1min | `HighAPILatencyCritical` | P1 | 15分钟 |
| 5xx 错误率 > 5% 持续 2min | `HighErrorRate` | P1 | 15分钟 |
| Backend 宕机 > 1min | `BackendDown` | P0 | 5分钟 |

---

## 四、SLO 计算方法

### 月度可用性计算

```
可用性 = (月度总分钟数 - 5xx 错误超标分钟数) / 月度总分钟数 × 100%
```

5xx 超标：在任意 5min 窗口内，5xx 错误率 > 1%

### P95 延迟计算（Prometheus PromQL）

```promql
# 路由开销 P95（7天窗口）
histogram_quantile(0.95,
  rate(openclaude_routing_overhead_seconds_bucket[7d])
)

# TTFB P95（7天窗口）
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket{job="openclaude-backend"}[7d])
)
```

### Miner 在线率

```promql
openclaude_miner_pool_size / openclaude_miner_total_registered
```

---

## 五、待办事项（SLO 完整化路径）

| 优先级 | 任务 | 负责人 | 状态 |
|--------|------|--------|------|
| P1 | 实现 `openclaude_routing_overhead_seconds` 自定义 Histogram 指标 | Backend Engineer | 待分配 |
| P1 | 实现 Miner 心跳指标 `openclaude_miner_heartbeat_age_seconds` | Backend Engineer | 待分配 |
| P2 | Grafana 面板添加三层延迟对比图表 | Operations Manager | 待实现 |
| P2 | 在 oncall_runbook.md 中更新延迟 SLO 响应流程 | Operations Manager | 待更新 |

---

*此文档是 OpenClade 运营准备计划的一部分，参见 KYD-20*
