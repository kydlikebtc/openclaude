# OpenClaude 事件响应流程 (Incident Response)

> 版本：v1.0 | 更新日期：2026-03-15

## 一、事件分级标准

| 级别 | 名称 | 定义 | 响应时间 | 示例 |
|------|------|------|---------|------|
| **P0** | 紧急 | 生产服务完全不可用，影响所有用户 | **15 分钟内** | Backend 宕机、数据库崩溃、所有 Miner 下线 |
| **P1** | 严重 | 核心功能受损，影响 >50% 用户 | **30 分钟内** | API 错误率 >20%、P95 延迟 >10s |
| **P2** | 高 | 部分功能异常，影响 <50% 用户 | **2 小时内** | 单个 Miner 下线、P95 延迟 >3s |
| **P3** | 中 | 性能下降或轻微异常，无明显用户影响 | **24 小时内** | 日志异常增多、缓存命中率下降 |

## 二、响应流程

### 阶段 1：检测与确认（0-5 分钟）

```
Grafana/Alertmanager 告警触发
       ↓
[值班工程师]：确认告警真实性（排除误报）
       ↓
访问 Grafana 仪表盘确认影响范围
       ↓
在内部通知渠道发布初始告警（P0/P1 必须）
```

**快速确认命令**：
```bash
# 检查所有服务健康状态
docker compose -f docker-compose.prod.yml ps

# 检查 backend 健康
curl -s https://api.openclaude.io/health | jq .

# 查看 backend 日志（最近 100 行）
docker compose -f docker-compose.prod.yml logs --tail=100 backend

# 查看错误日志
docker compose -f docker-compose.prod.yml logs --tail=100 backend | grep -E "ERROR|CRITICAL"
```

### 阶段 2：遏制（5-15 分钟）

**根据告警类型执行对应预案**：

- API 延迟/错误率过高 → 检查 [路由服务状态](#路由服务问题处理)
- Miner 下线 → 参考 [key_ban_response.md](./key_ban_response.md)
- 数据库问题 → 检查 PostgreSQL 连接数和慢查询
- Redis 问题 → 检查 Redis 内存和连接数

**通用遏制步骤**：
```bash
# 重启单个服务（不影响其他服务）
docker compose -f docker-compose.prod.yml restart backend

# 强制重新加载 Prometheus 配置（不重启）
curl -X POST http://localhost:9090/-/reload
```

### 阶段 3：诊断（15-30 分钟）

```bash
# 查看 Prometheus 告警状态
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | {alertname: .labels.alertname, state: .state}'

# 检查 API 指标
curl -s http://localhost:8000/metrics | grep http_request

# 数据库连接数
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U openclaude -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Redis 内存使用
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD info memory | grep used_memory_human
```

### 阶段 4：解决与恢复

根据诊断结果，从以下预案中选择：

1. **服务重启**：确认数据安全后，滚动重启受影响服务
2. **回滚部署**：若最近有部署，执行回滚（参考 [scaling.md](./scaling.md) 部署回滚章节）
3. **Miner 切换**：封禁故障 Miner，切换到备用节点
4. **数据库恢复**：从最近备份恢复（P0 级别）

### 阶段 5：验证与收尾

```bash
# 验证服务恢复
curl -s https://api.openclaude.io/health

# 监控 5 分钟确认告警消除
watch -n 30 'curl -s http://localhost:9090/api/v1/alerts | jq ".data.alerts | length"'

# 更新事件日志（必须在 2 小时内完成）
# 包含：根因、时间线、影响范围、解决措施、预防措施
```

## 三、升级流程

```
P3/P2 → 值班工程师自行处理，同步到 Slack #ops
P1    → 通知 Tech Lead，更新 status page
P0    → 立即唤醒 CTO，启动战情室，30 分钟更新一次外部状态页
```

### 联系方式（示例，实际填写真实信息）

| 角色 | 联系方式 | 响应时间 |
|------|---------|---------|
| 值班工程师 | Slack @oncall | 5 分钟 |
| Tech Lead | 电话/Slack | 15 分钟 |
| CTO | 电话（P0 专用） | 30 分钟 |

## 四、路由服务问题处理

```bash
# 查看 Miner 池状态（通过 API）
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.openclaude.io/api/v1/admin/miners | jq '.[] | {id, status, last_heartbeat}'

# 检查路由服务日志
docker compose -f docker-compose.prod.yml logs --tail=50 backend | grep "routing"

# 强制刷新 Redis 中的 Miner 池（谨慎操作）
# 只在确认 Redis 数据不一致时使用
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD DEL "miner:pool"
```

## 五、事后复盘（Post-Mortem）

**P0/P1 事件必须在 48 小时内完成复盘**，记录以下内容：

```markdown
## 事件复盘报告

- **事件编号**：INC-YYYY-MM-DD-NNN
- **严重级别**：P0/P1/P2/P3
- **影响时长**：XX 分钟
- **影响范围**：XX 用户，XX 请求失败

### 时间线
- HH:MM 告警触发
- HH:MM 开始响应
- HH:MM 找到根因
- HH:MM 服务恢复

### 根因分析
[详细描述根因]

### 预防措施
- [ ] 措施 1
- [ ] 措施 2
```
