# OpenClaude On-Call 响应手册

> 版本：v1.0 | 更新日期：2026-03-16 | 维护者：Operations Manager

**快速导航**：[告警分级](#一告警分级标准) | [接收告警](#二接收告警) | [Runbook 索引](#三告警-runbook) | [Post-mortem 模板](#四post-mortem-模板) | [联系方式](#五联系方式与升级路径)

---

## 一、告警分级标准

系统将所有告警分为两个维度：**严重度**（Severity）和**优先级**（Priority）。

### 1.1 告警严重度 × 响应时间

| 级别 | Severity 标签 | 定义 | 初始响应时间 | 通知渠道 |
|------|--------------|------|------------|---------|
| **P0** | `critical` | 生产完全不可用，影响所有用户 | **5 分钟** | Slack `#openclade-critical` + 电话唤醒 |
| **P1** | `critical` | 核心功能严重降级，影响 >50% 用户 | **15 分钟** | Slack `#openclade-critical` |
| **P2** | `warning` | 部分功能异常，SLO 边界告警 | **1 小时** | Slack `#openclade-alerts` |
| **P3** | `warning` | 性能轻微下降，预警指标 | **下个工作日** | Slack `#openclade-ops` |

### 1.2 告警规则 → 事件级别映射

| 告警名称 | 触发条件 | 默认级别 | 备注 |
|---------|---------|---------|-----|
| `BackendDown` | Backend 宕机 >1min | **P0** | 立即影响所有用户 |
| `MinerPoolEmpty` | 可用 Miner 为 0 | **P0** | 所有请求无法路由 |
| `PostgreSQLDown` | PostgreSQL 宕机 >1min | **P0** | 数据库不可用 |
| `RedisDown` | Redis 宕机 >1min | **P0** | 缓存和路由失效 |
| `HighAPILatencyCritical` | P95 延迟 >5s，持续 1min | **P1** | 严重影响用户体验 |
| `HighErrorRate` | 5xx 错误率 >5%，持续 2min | **P1** | 大量请求失败 |
| `LowMinerAvailabilityCritical` | Miner 在线率 <70%，持续 3min | **P1** | 路由容量严重不足 |
| `HighAPILatencyWarning` | P95 延迟 >2s，持续 2min | **P2** | 接近 SLO 边界 |
| `LowMinerAvailabilityWarning` | Miner 在线率 <90%，持续 5min | **P2** | SLO 目标边界 |
| `MinerOffline` | 单个 Miner 离线 >5min | **P2** | 部分容量损失 |
| `DiskSpaceHigh` | 磁盘使用率 >85% | **P2** | 需计划扩容 |
| `MemoryUsageHigh` | 内存使用率 >90% | **P3** | 预警，暂不影响服务 |
| `CPUUsageHigh` | CPU 使用率 >85%，持续 10min | **P3** | 预警，关注趋势 |
| `TokenUsageSpike` | Token 消耗速率 >均值 3x | **P3** | 可能存在异常使用 |

---

## 二、接收告警

### 2.1 告警通知渠道

所有告警通过 **Grafana Alertmanager** 发送：

- **`#openclade-critical`**：P0/P1 告警，每小时重复，图标 🚨
- **`#openclade-alerts`**：所有告警汇总，图标 🔔
- **`#openclade-backend`**：Backend 团队相关告警，图标 🔧
- **`#openclade-ops`**：运维资源告警（磁盘/内存/CPU），图标 📊

### 2.2 Slack 告警消息格式

```
🚨 [P0 CRITICAL — 立即响应]
标题: Backend 服务宕机
描述: OpenClaude Backend 服务已宕机超过 1 分钟。
严重度: critical | 触发时间: 2026-03-16 03:00:00 UTC
[查看图表] [运维手册]
```

### 2.3 值班工程师首要步骤

收到告警后，**在 Slack 中立即回复确认**（防止团队重复响应）：

```
🔔 ACK — @me 已接收 [BackendDown 03:00 UTC]，开始处理
```

然后访问 **Grafana 仪表盘**确认告警真实性：
```bash
# 仪表盘地址
http://<grafana-host>:3001/d/openclaude-overview

# 快速服务检查
docker compose -f docker-compose.prod.yml ps
curl -s https://api.openclaude.io/health | jq '{status, timestamp}'
```

---

## 三、告警 Runbook

### RB-001：Backend 完全宕机（BackendDown）

**告警**：`BackendDown` | **级别**：P0 | **目标恢复时间**：5 分钟

#### 症状
- Slack `#openclade-critical` 收到 🚨 `Backend 服务宕机`
- `https://api.openclaude.io/health` 返回连接拒绝或 502
- Prometheus 目标状态：`up{job="openclaude-backend"} == 0`

#### 诊断步骤

```bash
# 1. 检查容器状态
docker compose -f docker-compose.prod.yml ps

# 2. 查看 Backend 最近日志（定位崩溃原因）
docker compose -f docker-compose.prod.yml logs --tail=200 backend | grep -E "ERROR|CRITICAL|Exception|Traceback"

# 3. 检查内存/磁盘是否耗尽（OOM Kill 常见原因）
docker stats --no-stream backend
df -h /

# 4. 检查端口是否占用
lsof -i :8000
```

#### 恢复步骤

```bash
# 情况 A：容器崩溃（Exit Code 非 0）
docker compose -f docker-compose.prod.yml restart backend
# 等待 30s 后验证
curl -s https://api.openclaude.io/health | jq .

# 情况 B：OOM Kill（Exit Code 137）
# 临时增加内存限制，重启
docker compose -f docker-compose.prod.yml up -d --scale backend=1 backend

# 情况 C：配置错误（无法启动）
# 回滚到上一个已知正常版本
git -C /Users/kyd/openclaude log --oneline -5  # 查看最近 commit
git -C /Users/kyd/openclaude stash             # 暂存当前修改
docker compose -f docker-compose.prod.yml up -d backend

# 验证恢复
curl -s https://api.openclaude.io/health
```

#### 升级条件
- 5 分钟内无法恢复 → 通知 Tech Lead
- 10 分钟内无法恢复 → 通知 CTO，启动战情室

---

### RB-002：Miner 池为空（MinerPoolEmpty）

**告警**：`MinerPoolEmpty` | **级别**：P0 | **目标恢复时间**：10 分钟

#### 症状
- `openclaude_miner_pool_size == 0`
- 所有用户 API 请求返回 503
- 路由日志出现 `No available miners`

#### 诊断步骤

```bash
# 1. 检查 Miner 池状态
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.openclaude.io/api/v1/admin/miners/stats | jq .

# 2. 查看所有 Miner 状态
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.openclaude.io/api/v1/admin/miners | \
  jq '.[] | {id, hotkey, status, last_heartbeat}'

# 3. 检查 Redis Miner 池
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD ZRANGE "miner:pool" 0 -1 WITHSCORES

# 4. 查看路由服务日志
docker compose -f docker-compose.prod.yml logs --tail=100 backend | grep -i "miner\|routing\|pool"
```

#### 恢复步骤

```bash
# 情况 A：Redis 数据不一致，Miner 实际在线但池为空
# 强制刷新 Miner 池（路由服务将在下次心跳时重建）
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD DEL "miner:pool"
# 等待 60s 让 Miner 重新注册

# 情况 B：所有 Miner Key 被封禁
# 参考 key_ban_response.md 执行应急流程
# 临时措施：联系可信 Miner 注册紧急节点

# 情况 C：网络问题导致心跳丢失
# 检查 Miner 子网连接
docker compose -f docker-compose.prod.yml exec backend ping -c 3 <miner-host>

# 验证恢复
watch -n 10 'curl -s http://localhost:9090/api/v1/query?query=openclaude_miner_pool_size | jq ".data.result[0].value[1]"'
```

> 参考：[key_ban_response.md](./key_ban_response.md) 详细处理 Miner Key 封禁

---

### RB-003：API 延迟严重超标（HighAPILatencyCritical）

**告警**：`HighAPILatencyCritical` | **级别**：P1 | **目标恢复时间**：15 分钟

#### 症状
- P95 延迟 >5s，持续 >1 分钟
- 用户反馈请求超时
- Grafana 延迟图表显示急剧上升

#### 诊断步骤

```bash
# 1. 确认延迟来源（Backend vs Miner）
# 查看 Prometheus 中的延迟分布
curl -s 'http://localhost:9090/api/v1/query' \
  --data-urlencode 'query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="openclaude-backend"}[5m]))' | \
  jq '.data.result[0].value[1]'

# 2. 检查各 Miner 的响应时间
docker compose -f docker-compose.prod.yml logs --tail=200 backend | \
  grep "miner_response_time" | sort -t= -k2 -rn | head -20

# 3. 检查 Backend 处理时间（排除 Miner 影响）
docker compose -f docker-compose.prod.yml logs --tail=100 backend | \
  grep -E "processing_time|handler_time"

# 4. 检查数据库慢查询
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U openclaude -c "SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# 5. 检查 Redis 延迟
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD --latency-history -i 1
```

#### 恢复步骤

```bash
# 情况 A：单个 Miner 响应慢，拉高整体 P95
# 临时封禁慢速 Miner
SLOW_MINER_ID="<miner-id>"
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD ZREM "miner:pool" "$SLOW_MINER_ID"
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD SET "miner:${SLOW_MINER_ID}:isolated" "1" EX 3600

# 情况 B：数据库连接池耗尽
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U openclaude -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle in transaction' AND query_start < now() - interval '5 minutes';"

# 情况 C：Backend 负载过高
# 查看并重启 Backend（滚动重启以避免停机）
docker compose -f docker-compose.prod.yml up -d --no-deps backend

# 验证
watch -n 15 'curl -s "http://localhost:9090/api/v1/query" \
  --data-urlencode "query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job=~\"openclaude-backend\"}[5m]))" | \
  jq -r ".data.result[0].value[1]"'
```

---

### RB-004：API 错误率过高（HighErrorRate）

**告警**：`HighErrorRate` | **级别**：P1 | **目标恢复时间**：15 分钟

#### 症状
- 5xx 错误率 >5%，持续 >2 分钟
- 用户 API 请求大量返回 500/502/503

#### 诊断步骤

```bash
# 1. 定位错误类型和频率
docker compose -f docker-compose.prod.yml logs --tail=300 backend | \
  grep -E "HTTP [5][0-9][0-9]|5xx|error|exception" | \
  sort | uniq -c | sort -rn | head -20

# 2. 检查是否特定端点出错
curl -s 'http://localhost:9090/api/v1/query' \
  --data-urlencode 'query=rate(http_requests_total{status=~"5.."}[5m]) by (endpoint)' | \
  jq '.data.result[] | {endpoint: .metric.endpoint, rate: .value[1]}'

# 3. 确认 Miner 是否在返回错误
docker compose -f docker-compose.prod.yml logs --tail=200 backend | \
  grep -E "miner.*error|upstream.*error|503|502"

# 4. 检查数据库事务是否异常
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U openclaude -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"
```

#### 恢复步骤

```bash
# 情况 A：Miner 批量返回错误（可能 Key 封禁）
# 参考 RB-002 和 key_ban_response.md

# 情况 B：后端代码错误（如最近部署导致）
# 紧急回滚
cd /Users/kyd/openclaude
LAST_GOOD_TAG=$(git tag --sort=-creatordate | head -2 | tail -1)
git checkout $LAST_GOOD_TAG
docker compose -f docker-compose.prod.yml up -d --no-deps backend

# 情况 C：数据库死锁或事务积压
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U openclaude -c "
    SELECT pg_terminate_backend(pid) FROM pg_stat_activity
    WHERE state IN ('idle in transaction', 'idle in transaction (aborted)')
    AND query_start < now() - interval '2 minutes';"

# 验证
watch -n 15 'curl -s "http://localhost:9090/api/v1/query" \
  --data-urlencode "query=rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])" | \
  jq -r ".data.result[0].value[1]"'
```

---

### RB-005：数据库宕机（PostgreSQLDown / RedisDown）

**告警**：`PostgreSQLDown` 或 `RedisDown` | **级别**：P0 | **目标恢复时间**：5 分钟

#### 症状
- `pg_up == 0` 或 `redis_up == 0`
- Backend 日志出现大量连接错误
- 所有 API 请求失败

#### 诊断步骤

```bash
# PostgreSQL 诊断
# 1. 检查容器状态
docker compose -f docker-compose.prod.yml ps postgres

# 2. 查看 PostgreSQL 日志
docker compose -f docker-compose.prod.yml logs --tail=100 postgres | grep -E "ERROR|FATAL|PANIC"

# 3. 测试连接
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U openclaude -c "SELECT 1;" 2>&1

# Redis 诊断
# 1. 检查 Redis 容器
docker compose -f docker-compose.prod.yml ps redis

# 2. 查看 Redis 日志
docker compose -f docker-compose.prod.yml logs --tail=100 redis | grep -E "ERROR|WARNING|Killed"

# 3. 测试 Redis 连接
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD ping
```

#### 恢复步骤

```bash
# PostgreSQL 恢复
# 情况 A：进程崩溃
docker compose -f docker-compose.prod.yml restart postgres
sleep 10
docker compose -f docker-compose.prod.yml exec postgres psql -U openclaude -c "SELECT 1;"

# 情况 B：数据文件损坏（最坏情况）
# 1. 确认损坏
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U openclaude -c "SELECT pg_check_tuple_visible(t_ctid, xmax) FROM pg_class LIMIT 1;" 2>&1

# 2. 从最近备份恢复（P0 场景，需 CTO 批准）
# 备份位置: /var/backups/openclaude/postgres/latest.dump
# docker compose -f docker-compose.prod.yml exec postgres \
#   pg_restore -U openclaude -d openclaude /backup/latest.dump

# Redis 恢复
# Redis 是无状态缓存，直接重启
docker compose -f docker-compose.prod.yml restart redis
sleep 5
docker compose -f docker-compose.prod.yml exec redis redis-cli -a $REDIS_PASSWORD ping

# 验证
curl -s https://api.openclaude.io/health | jq '{status, db_status, redis_status}'
```

> ⚠️ PostgreSQL 数据恢复操作须通知 CTO 并留有书面记录

---

### RB-006：Miner 在线率严重偏低（LowMinerAvailabilityCritical）

**告警**：`LowMinerAvailabilityCritical` | **级别**：P1 | **目标恢复时间**：30 分钟

#### 症状
- Miner 在线率 <70%，持续 >3 分钟
- 路由引擎容量严重不足
- API 延迟开始上升

#### 诊断步骤

```bash
# 1. 获取离线 Miner 列表
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.openclaude.io/api/v1/admin/miners | \
  jq '.[] | select(.status != "active") | {id, hotkey, name, status, last_heartbeat}'

# 2. 检查 Validator 探针状态
# 查看最近一次 Validator 探针结果
docker compose -f docker-compose.prod.yml logs --tail=100 validator 2>/dev/null | \
  grep -E "probe|heartbeat|score" | tail -20

# 3. 检查网络连通性
# 是否是网络问题导致 Miner 无法回连
docker compose -f docker-compose.prod.yml exec backend \
  wget -q --timeout=10 -O - http://<sample-miner-host>/health 2>&1 || echo "连接失败"
```

#### 恢复步骤

```bash
# 情况 A：批量 Key 封禁（参考 key_ban_response.md）
# 通知所有受影响 Miner 更换 API Key

# 情况 B：网络分区或 Bittensor 链问题
# 检查 Bittensor 节点状态，等待链恢复

# 情况 C：Validator 评分异常导致 Miner 被惩罚下线
# 联系 Blockchain Engineer 查看权重提交情况
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.openclaude.io/api/v1/admin/subnet/weights | jq .

# 临时措施：手动提高现有在线 Miner 的请求配额
curl -s -X PATCH \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"max_tpm": 200000}' \
  https://api.openclaude.io/api/v1/admin/routing/config
```

---

### RB-007：磁盘空间不足（DiskSpaceHigh）

**告警**：`DiskSpaceHigh` | **级别**：P2 | **目标恢复时间**：1 小时

#### 诊断步骤

```bash
# 1. 查看各挂载点使用情况
df -h

# 2. 找出最大目录
du -sh /var/lib/docker/volumes/* | sort -rh | head -10

# 3. 查看 Docker 日志文件大小
ls -lh /var/lib/docker/containers/*/
```

#### 恢复步骤

```bash
# 清理 Docker 无用资源（安全操作，不影响运行中容器）
docker system prune -f --volumes

# 清理旧日志文件（保留最近 7 天）
find /var/log -name "*.log" -mtime +7 -delete
find /var/log -name "*.gz" -mtime +30 -delete

# 清理 PostgreSQL WAL 日志（谨慎操作）
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U openclaude -c "SELECT pg_switch_wal();"

# 压缩旧 Prometheus 数据
# Prometheus 会自动清理超过 retention 的数据（默认 15 天）
# 检查当前 retention 设置
docker compose -f docker-compose.prod.yml exec prometheus \
  prometheus --storage.tsdb.retention.time=15d --help 2>&1 | grep retention
```

---

## 四、Post-mortem 模板

P0/P1 事件 **必须在 48 小时内完成复盘**，P2 事件 **建议在 5 个工作日内完成**。

### 4.1 复盘报告模板

```markdown
# 事件复盘报告

**事件编号**：INC-YYYY-MM-DD-NNN
**严重级别**：P0 / P1 / P2
**影响时长**：XX 分钟（HH:MM UTC — HH:MM UTC）
**影响范围**：约 XX 个活跃用户，XX 次请求失败，XX Token 损失
**报告撰写人**：[工程师姓名]
**参与处理人**：[人员列表]
**复盘会议时间**：YYYY-MM-DD HH:MM UTC

---

## 事件摘要

[2-3 句话描述：发生了什么，为什么发生，已采取什么措施]

---

## 时间线

| 时间（UTC） | 事件 | 操作人 |
|------------|------|--------|
| HH:MM | 告警触发：[告警名称] | Alertmanager |
| HH:MM | 值班工程师确认告警 | [姓名] |
| HH:MM | 初步诊断完成，确认根因 | [姓名] |
| HH:MM | 开始执行恢复操作 | [姓名] |
| HH:MM | 服务恢复，告警消除 | [姓名] |
| HH:MM | 用户通知/状态页更新 | [姓名] |

---

## 根因分析（5-Why）

**直接原因**：[导致事件的直接触发因素]

**Why 1**：[为什么直接原因会发生？]
**Why 2**：[为什么 Why 1 的条件存在？]
**Why 3**：[为什么 Why 2 的条件存在？]
**Why 4**：[为什么 Why 3 的条件存在？]
**Why 5**（根因）：[系统性根因]

---

## 影响评估

- **用户影响**：[受影响用户数量和范围]
- **API 调用影响**：[失败请求数量]
- **收入影响**：[Token 损失估算]
- **SLA 合规**：[是否违反 SLO 承诺]

---

## 做得好的地方

- [告警及时触发/响应迅速/沟通清晰等]

---

## 需要改进的地方

- [告警覆盖不足/Runbook 缺失/恢复步骤不清晰等]

---

## 改进措施（Action Items）

| 编号 | 措施描述 | 类型 | 负责人 | 截止日期 | 状态 |
|------|---------|------|--------|---------|------|
| AI-1 | [防止措施] | 预防 | [姓名] | YYYY-MM-DD | ⏳ |
| AI-2 | [检测措施] | 检测 | [姓名] | YYYY-MM-DD | ⏳ |
| AI-3 | [恢复措施] | 减少影响 | [姓名] | YYYY-MM-DD | ⏳ |

---

## 结论

[总结学到了什么，以及对系统可靠性的影响]
```

### 4.2 快速事件记录（P2/P3 简化版）

```markdown
## 快速事件记录 INC-YYYY-MM-DD-NNN

- **告警**：[告警名称]
- **时间**：HH:MM — HH:MM UTC（共 XX 分钟）
- **原因**：[一句话描述]
- **解决**：[执行了什么操作]
- **Action**：[后续改进措施，如有]
```

---

## 五、联系方式与升级路径

### 5.1 升级矩阵

```
P3/P2 → 值班工程师独立处理 → Slack #openclade-ops 同步
P1    → 通知 Tech Lead（15 分钟无响应升级至 P0 流程）
P0    → 立即唤醒 CTO → 启动战情室 → 每 30 分钟状态更新
```

### 5.2 联系方式

| 角色 | 姓名 | Slack | 紧急电话 | 响应时间 |
|------|------|-------|---------|---------|
| On-Call 工程师 | [填写] | @oncall | [填写] | 5 分钟 |
| Tech Lead | [填写] | [填写] | [填写] | 15 分钟 |
| CTO | [填写] | [填写] | [填写] | 30 分钟（P0 专用） |

> ⚠️ **实际联系方式保存在 1Password "On-Call Contacts" 保险库中**，不在代码库里硬编码

### 5.3 外部支持

| 服务 | 支持渠道 | 账号 |
|------|---------|------|
| Anthropic API 支持 | https://support.anthropic.com | [团队账号] |
| 服务器/云平台 | [提供商支持入口] | [账号] |
| 域名/CDN | [提供商支持入口] | [账号] |

---

## 六、常用诊断命令速查

```bash
# 服务状态全览
docker compose -f docker-compose.prod.yml ps

# API 健康检查
curl -s https://api.openclaude.io/health | jq .

# Prometheus 当前触发告警
curl -s http://localhost:9090/api/v1/alerts | \
  jq '.data.alerts[] | select(.state=="firing") | {name: .labels.alertname, severity: .labels.severity}'

# Miner 池大小
curl -s 'http://localhost:9090/api/v1/query?query=openclaude_miner_pool_size' | \
  jq '.data.result[0].value[1]'

# 当前 P95 延迟
curl -s 'http://localhost:9090/api/v1/query' \
  --data-urlencode 'query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="openclaude-backend"}[5m]))' | \
  jq '.data.result[0].value[1]'

# 当前错误率
curl -s 'http://localhost:9090/api/v1/query' \
  --data-urlencode 'query=rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])' | \
  jq '.data.result[0].value[1]'

# 后端实时错误日志
docker compose -f docker-compose.prod.yml logs -f backend | grep -E "ERROR|WARNING|Exception"

# 数据库连接池状态
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U openclaude -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state ORDER BY count DESC;"

# Redis 内存和连接
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD info | grep -E "used_memory_human|connected_clients|keyspace"
```

---

## 七、On-Call 轮班指南

### 7.1 交接 Checklist

每次轮班交接时，离任工程师需确认：

- [ ] 所有告警已消除或已知晓（非噪音）
- [ ] 无未完成的 in-progress 事件
- [ ] Grafana 仪表盘可正常访问
- [ ] Alertmanager 通知正常工作
- [ ] 本班次的快速事件记录已填写

### 7.2 告警噪音调优

发现以下情况时，记录到 Ops 周报并调整阈值：

- **频繁误报**（每天 >3 次）：提高告警阈值或延长持续时间
- **漏报**（事故发生但无告警）：降低阈值或添加新告警规则
- **告警风暴**（一个根因触发 5+ 告警）：配置 Alertmanager 抑制规则

---

*参考文档*：
- [incident_response.md](./incident_response.md) — 详细事件响应流程
- [key_ban_response.md](./key_ban_response.md) — Miner Key 封禁处理
- [scaling.md](./scaling.md) — 扩容和回滚操作
- [monitoring_validation_report.md](./monitoring_validation_report.md) — 监控系统验证记录
