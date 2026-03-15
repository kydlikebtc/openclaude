# OpenClaude 系统扩容流程

> 版本：v1.0 | 更新日期：2026-03-15

## 一、扩容触发条件

| 指标 | 阈值 | 建议操作 |
|------|------|---------|
| CPU 持续 >70% (10min) | 警告 | 准备水平扩容 |
| CPU 持续 >85% (10min) | 立即 | 执行水平扩容 |
| 内存使用 >80% | 警告 | 检查内存泄漏或增加实例 |
| API P95 延迟 >2s | 警告 | 检查瓶颈（DB/Redis/Backend） |
| PostgreSQL 连接数 >80% max | 立即 | 增加连接池或 PgBouncer |
| Miner 请求队列积压 >100 | 立即 | 通知更多 Miner 加入 |

## 二、水平扩容步骤

### 2.1 Backend 服务扩容

Backend 服务设计为无状态（Session 存 Redis），可以直接水平扩展。

```bash
# 查看当前 Backend 实例数量
docker compose -f docker-compose.prod.yml ps backend

# 扩容到 3 个实例（需确保 Nginx 配置了负载均衡）
docker compose -f docker-compose.prod.yml up -d --scale backend=3 --no-recreate

# 验证新实例健康
docker compose -f docker-compose.prod.yml ps backend
for i in $(docker compose -f docker-compose.prod.yml ps -q backend); do
  docker inspect $i | jq '.[0].NetworkSettings.IPAddress'
done
```

**前置条件**：Nginx 必须配置 upstream 负载均衡（而非硬编码单个 backend 地址）。

修改 `nginx/nginx.prod.conf` 中的 upstream 配置：
```nginx
upstream backend_pool {
    server backend:8000;
    # 扩容后由 Docker DNS 自动发现多个实例
    keepalive 32;
}
```

### 2.2 负载均衡配置

```bash
# 验证 Nginx 负载均衡配置
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# 动态重载 Nginx 配置（零停机）
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload

# 查看 Nginx 连接状态
curl -s http://localhost:8080/stub_status
```

### 2.3 Redis 扩容

Redis 采用单节点 + AOF 持久化，短期内无需分片。当内存接近 4GB 时考虑迁移。

```bash
# 查看 Redis 内存使用
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD info memory | grep -E "used_memory_human|maxmemory"

# 调整 Redis 最大内存（在线修改，重启后失效）
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD CONFIG SET maxmemory 4gb

# 持久化配置修改，需更新 docker-compose.prod.yml 中的 Redis command
```

## 三、数据库扩容

### 3.1 连接池优化（优先于添加实例）

```bash
# 查看当前连接数
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U openclaude -c "SELECT count(*), state, wait_event_type, wait_event
  FROM pg_stat_activity GROUP BY state, wait_event_type, wait_event ORDER BY count DESC;"

# 查看最大连接数限制
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U openclaude -c "SHOW max_connections;"

# 调整 Backend 连接池大小（在 backend 环境变量中配置）
# DATABASE_POOL_SIZE=20（默认），DATABASE_MAX_OVERFLOW=10
```

### 3.2 添加只读副本

```bash
# 在 docker-compose.prod.yml 中添加 PostgreSQL 副本
# 1. 主库开启 WAL 日志
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U openclaude -c "ALTER SYSTEM SET wal_level = replica;"

# 2. 创建副本服务（添加到 docker-compose.prod.yml）
# postgres-replica:
#   image: postgres:15-alpine
#   environment:
#     - POSTGRES_USER=${POSTGRES_USER}
#     - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
#   command: |
#     postgres -c primary_conninfo="host=postgres port=5432 user=replicator"

# 3. Backend 读写分离配置（需代码支持）
# DATABASE_READ_URL=postgresql+asyncpg://...@postgres-replica:5432/openclaude
```

### 3.3 数据库性能优化

```bash
# 识别慢查询（运行时间 >1s）
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U openclaude -c "
  SELECT pid, now() - query_start AS duration, query, state
  FROM pg_stat_activity
  WHERE state != 'idle' AND now() - query_start > interval '1 second'
  ORDER BY duration DESC LIMIT 10;"

# 查看缺失索引建议
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U openclaude -c "
  SELECT schemaname, tablename, attname, n_distinct, correlation
  FROM pg_stats
  WHERE tablename IN ('requests', 'billing_records', 'miners')
  ORDER BY n_distinct DESC;"

# VACUUM 分析（维护操作）
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U openclaude -c "VACUUM ANALYZE;"
```

## 四、部署回滚

### 4.1 快速回滚步骤

```bash
# 查看最近的镜像标签
docker images | grep openclaude | head -10

# 回滚 Backend 到上一个版本
PREVIOUS_IMAGE="openclaude-backend:$(git rev-parse HEAD~1 | head -c 8)"
docker compose -f docker-compose.prod.yml stop backend
docker compose -f docker-compose.prod.yml \
  run --rm -d --name backend-rollback \
  -e "IMAGE=$PREVIOUS_IMAGE" backend

# 或者通过 git 回滚代码后重新构建
git log --oneline -10  # 查看最近提交
git revert HEAD        # 创建回滚提交（推荐，保留历史）
# 或
git reset --hard HEAD~1  # 直接回退（谨慎使用，会丢失历史）

# 重新构建并部署
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend
```

### 4.2 数据库迁移回滚

```bash
# 查看当前迁移版本
docker compose -f docker-compose.prod.yml exec backend \
  alembic current

# 回滚最近一次迁移
docker compose -f docker-compose.prod.yml exec backend \
  alembic downgrade -1

# 回滚到指定版本
docker compose -f docker-compose.prod.yml exec backend \
  alembic downgrade <revision_id>
```

## 五、扩容后验证清单

```bash
# 1. 检查所有服务状态
docker compose -f docker-compose.prod.yml ps

# 2. API 健康检查
curl -s https://api.openclaude.io/health | jq .

# 3. 端到端测试（发送测试请求）
curl -s -X POST \
  -H "Authorization: Bearer $TEST_USER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-haiku-4-5-20251001","max_tokens":50,"messages":[{"role":"user","content":"测试连通性"}]}' \
  https://api.openclaude.io/v1/messages | jq '{stop_reason, usage}'

# 4. 监控指标确认（等待 5 分钟后检查）
# - Grafana: API QPS 和延迟是否恢复正常
# - Prometheus: 所有告警是否已消除

# 5. 日志检查
docker compose -f docker-compose.prod.yml logs --tail=50 backend | grep -v INFO
```

## 六、容量规划参考

| 日活用户 (DAU) | 峰值 QPS | Backend 实例 | PostgreSQL | Redis 内存 |
|--------------|---------|------------|-----------|----------|
| < 1,000 | < 10 | 1 | 2 Core / 4GB | 512MB |
| 1,000 - 10,000 | 10 - 100 | 2-3 | 4 Core / 8GB | 2GB |
| 10,000 - 100,000 | 100 - 1,000 | 5-10 | 8 Core / 32GB + 副本 | 8GB |
| > 100,000 | > 1,000 | K8s 自动扩缩 | 托管 RDS | Redis Cluster |

> **注意**：Miner 池的扩容通过吸引更多 Miner 节点加入来实现，无需运营方直接扩容。
