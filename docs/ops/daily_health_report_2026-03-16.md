# OpenClade 每日系统健康报告

**日期**: 2026-03-16
**报告人**: Operations Manager
**环境**: 开发/测试环境 (Dev)
**报告时间**: UTC 20:50

---

## 服务状态总览

| 服务 | 状态 | 运行时长 | 备注 |
|------|------|---------|------|
| Backend API | ✅ 正常 | ~4小时 | 端口 8000 |
| PostgreSQL | ✅ 正常 (healthy) | ~4小时 | 端口 5432 |
| Redis | ✅ 正常 | ~4小时 | v7.4.8, 25 keys |
| Subtensor Localnet | ✅ 正常 | ~4小时 | 端口 9933/9944 |
| Prometheus | ⚠️ 未部署 | — | 仅生产配置存在 |
| Grafana | ⚠️ 未部署 | — | 仅生产配置存在 |
| Alertmanager | ⚠️ 未部署 | — | 仅生产配置存在 |

**整体系统可用性**: 核心服务 100% ✅

---

## API 性能指标

### 请求量统计

| 端点 | 2xx 请求 | 4xx 请求 | 5xx 请求 |
|------|---------|---------|---------|
| POST /v1/messages | 238 | 0 | 0 |
| GET /api/v1/miners/pool | 31 | 0 | 0 |
| GET /api/v1/usage/daily | 124 | 0 | 0 |
| GET /health | 16 | 0 | 0 |
| POST /api/v1/auth/login | 1 | 0 | 0 |
| 其他受保护端点 | — | 142 | 0 |

**总计**: 417 成功 | 142 客户端错误 (全部为 401 Unauthorized) | **0 服务器错误** ✅

### SLO 对照

| 指标 | 目标 | 实际值 | 状态 |
|------|------|--------|------|
| 5xx 错误率 | < 1% | **0%** | ✅ 达标 |
| API Uptime | 99.9% | **100%** | ✅ 达标 |
| 平均响应延迟 (全部) | — | **2.28s** | ℹ️ 含LLM调用 |

### /v1/messages 延迟分布

```
< 100ms:  0 个请求  (0%)
< 500ms: 12 个请求 (12.1%)
< 1.0s:  16 个请求 (16.2%)
> 1.0s:  83 个请求 (83.8%) ← 正常 (LLM 流式响应)
```

> ℹ️ P95 延迟 > 1s 为预期行为，因为后端直接代理 Claude API 调用。
> SLO P95 < 2s 的目标需结合流式响应特性重新评估。

---

## 模型池状态

| 模型 | 可用 API Keys | 状态 |
|------|-------------|------|
| claude-sonnet-4-6 | 5 | ✅ 正常 |
| claude-haiku-4-5-20251001 | 11 | ✅ 正常 |

**总计**: 16 个活跃 API Key 在内存池中

---

## 数据库状态

| 表 | 记录数 | 说明 |
|----|--------|------|
| users | 0 | 开发环境，未注册用户 |
| miners | 0 | 测试后已清空 |
| miner_api_keys | 0 | 随 miners 清空 |
| api_keys | 0 | 无用户，无 API Key |
| transactions | 0 | 无交易记录 |

> ℹ️ 这是预期状态 — 系统处于上线前开发阶段，数据库是干净的测试环境

---

## 关键运营发现

### 1. 监控栈未部署 ⚠️

- **问题**: Prometheus/Grafana/Alertmanager 配置文件已完成 (KYD-43)，但只在 `docker-compose.prod.yml` 中定义，当前开发环境中未运行。
- **影响**: 无实时监控数据收集，无法触发告警。
- **建议**: 在集成测试阶段启动监控栈验证告警流程。

### 2. SLO P95 延迟定义需要调整 ℹ️

- **问题**: 当前 SLO 定义 P95 < 2s，但 LLM API 调用本身就需要 1-30s。
- **建议**: 区分两个指标：
  - 路由/代理开销 (overhead): < 200ms
  - 端到端响应 (TTFB): < 2s 目标
  - 完整响应: 不设硬性 SLO，依赖 Claude API 性能

### 3. 4xx 错误率看似偏高 ℹ️

- **实际情况**: 142/559 = 25.4% 的 4xx 全部是开发测试产生的 401 Unauthorized
- **生产环境**: 正式用户通过 API Key 认证后 4xx 率应接近 0
- **监控建议**: 生产环境应对 4xx rate > 5% 设置告警

---

## Bittensor Testnet 状态

| 组件 | 状态 | 说明 |
|------|------|------|
| Subtensor Localnet | ✅ 运行中 | 端口 9933/9944/30333 |
| Validator | ⚠️ 阻塞 | KYD-35 显示 72h 稳定性测试被阻塞 |
| Miner 节点 | ⚠️ 阻塞 | KYD-22 显示 Testnet 部署被阻塞 |

---

## 今日运营完成情况

| 任务 | 状态 |
|------|------|
| KYD-30: 监控告警验证 Phase 1 | ✅ Done |
| KYD-32: 自定义 Prometheus 指标 | ✅ Done |
| KYD-43: Grafana Dashboard + Alertmanager | ✅ Done |
| KYD-56: On-Call Runbook + SOP | ✅ Done |

---

## 行动项

| 优先级 | 行动 | 负责人 | 时间 |
|--------|------|--------|------|
| P2 | 在 dev compose 中添加轻量监控 (Prometheus only) | Operations Manager | 本周 |
| P2 | 更新 SLO 定义，区分路由延迟和 LLM 延迟 | Operations Manager | 本周 |
| P1 | 解除 KYD-22/KYD-35 Testnet 阻塞 | Backend/Blockchain Engineer | 下一步 |
| P3 | 生产部署准备 checklist | Operations Manager | 上线前 |

---

*此报告由 Operations Manager Agent 自动生成*
*下次报告: 2026-03-17*
