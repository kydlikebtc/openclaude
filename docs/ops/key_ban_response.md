# Miner Key 封禁应急预案

> 版本：v1.0 | 更新日期：2026-03-15

## 一、背景

OpenClaude 通过 Miner 节点池代理 Claude API 请求。当某个 Miner 的 API Key 被 Anthropic 封禁或限流时，需要快速识别、隔离并切换到健康节点，确保服务连续性。

## 二、检测方法

### 2.1 自动检测（Prometheus 告警）

以下告警触发即表示可能存在 Key 封禁：
- `MinerOffline`：Miner 节点超过 360 秒未发送心跳
- `HighErrorRate`：API 5xx 错误率 >5%（特别是 429 Too Many Requests 或 401 Unauthorized）

### 2.2 手动检测

```bash
# 查看实时错误日志，识别 403/429/401 错误
docker compose -f docker-compose.prod.yml logs -f backend | grep -E "403|429|401|banned|rate_limit"

# 通过管理 API 查看 Miner 健康状态
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.openclaude.io/api/v1/admin/miners | \
  jq '.[] | select(.status != "active") | {id, hotkey, status, last_heartbeat}'

# 检查 Redis 中 Miner 的心跳时间
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD --scan --pattern "miner:*:heartbeat" | \
  while read key; do
    miner_id=$(echo $key | sed 's/miner://;s/:heartbeat//')
    ts=$(redis-cli -a $REDIS_PASSWORD GET $key)
    echo "Miner $miner_id last heartbeat: $ts"
  done

# 检查 Miner 隔离状态
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD --scan --pattern "miner:*:isolated"
```

### 2.3 Prometheus 查询（Grafana 面板）

```promql
# 查看各 Miner 的请求错误率
rate(http_requests_total{status=~"4..|5.."}[5m]) by (miner_id)

# Miner 心跳年龄（超过 120s 的认为离线）
openclaude_miner_heartbeat_age_seconds > 120
```

## 三、自动切换机制验证

OpenClaude 路由引擎在以下情况下会自动切换 Miner：

1. **Miner 心跳超时**（`HEARTBEAT_TTL=120s`）：自动从 Redis 池中降低其优先级
2. **请求失败**：路由引擎检测到连续失败后，将 Miner 标记为隔离状态

**验证自动切换是否生效**：
```bash
# 监控 Miner 池大小变化
watch -n 10 'curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.openclaude.io/api/v1/admin/miners/stats | jq .'

# 查看路由日志，确认请求被路由到其他 Miner
docker compose -f docker-compose.prod.yml logs -f backend | grep "routing\|miner_id"
```

## 四、手动封禁步骤

当自动检测确认某个 Miner Key 已被封禁时，执行手动封禁：

### Step 1：确认受影响的 Miner

```bash
# 获取 Miner 列表，找到状态异常的节点
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.openclaude.io/api/v1/admin/miners | jq '.[] | {id, hotkey, name, status}'
```

### Step 2：隔离故障 Miner

```bash
# 通过管理 API 封禁 Miner（设置为 isolated 状态）
MINER_ID="<受影响的 Miner ID>"
curl -s -X PATCH \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "suspended"}' \
  https://api.openclaude.io/api/v1/admin/miners/$MINER_ID

# 从 Redis 池中移除（立即生效）
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD ZREM "miner:pool" "$MINER_ID"

# 设置隔离标志（路由引擎将跳过此节点）
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD SET "miner:${MINER_ID}:isolated" "1" EX 86400
```

### Step 3：验证路由切换

```bash
# 发送测试请求，观察是否路由到健康 Miner
curl -s -X POST \
  -H "Authorization: Bearer $TEST_USER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-haiku-4-5-20251001","max_tokens":100,"messages":[{"role":"user","content":"ping"}]}' \
  https://api.openclaude.io/v1/messages | jq '{id, model, stop_reason}'

# 确认 Miner 池中仍有健康节点
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.openclaude.io/api/v1/admin/miners/stats
```

### Step 4：通知受影响的 Miner

```
通知内容模板：

主题：[OpenClaude] 您的节点 {hotkey} 已被临时暂停

您好，

我们检测到您的 Miner 节点 {hotkey} 的 API Key 可能已遭遇以下情况：
- API Key 被限流（429 Too Many Requests）
- API Key 被封禁（401/403 错误）

为保护整体服务稳定性，我们已临时暂停您的节点。

请检查您的 Anthropic API Key 状态，并在问题解决后：
1. 重新注册您的节点（使用新的有效 API Key）
2. 或联系我们的支持团队

感谢您的理解！
OpenClaude 团队
```

## 五、恢复流程

```bash
# 当 Miner 提供新的有效 Key 后，恢复节点
curl -s -X PATCH \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}' \
  https://api.openclaude.io/api/v1/admin/miners/$MINER_ID

# 清除 Redis 隔离标志
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD DEL "miner:${MINER_ID}:isolated"

# 触发 Miner 重新注册（Miner 侧操作）
# 或手动添加回 Miner 池
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD ZADD "miner:pool" 0.5 "$MINER_ID"
```

## 六、预防措施

1. **多 Key 配置**：鼓励 Miner 配置多个 API Key 以提高容错性
2. **定期健康检查**：Prometheus 监控 Miner 心跳，30 分钟内必须检测到异常
3. **限流保护**：路由引擎应实现每个 Miner Key 的 TPM（每分钟 Token）限制，避免触发 Anthropic 限流
4. **告警升级**：`MinerPoolEmpty` 告警触发时，立即升级为 P0 事件
