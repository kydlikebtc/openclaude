# OpenClaude 生产回滚 SOP

> 版本：v1.0 | 创建日期：2026-03-16 | 维护者：Backend Engineer
> 参考文档：[incident_response.md](./incident_response.md) | [oncall_runbook.md](./oncall_runbook.md)

**快速导航**：[决策树](#一回滚决策树) | [应用回滚](#二应用代码回滚) | [数据库回滚](#三数据库迁移回滚) | [配置回滚](#四配置变更回滚) | [全量回滚](#五全量回滚最坏情况) | [通知模板](#六用户通知模板)

---

## 一、回滚决策树

```
生产出现问题
      │
      ▼
[步骤 0] 评估影响范围（见 incident_response.md）
      │
      ├── P0/P1（服务不可用或严重降级）
      │         │
      │         ▼
      │   立刻通知用户（见通知模板 6.1）
      │   15 分钟内启动回滚
      │
      └── P2/P3（部分异常、性能下降）
                │
                ▼
          评估是否回滚还是热修复
          ├── 热修复可 15 分钟内完成 → 优先热修复
          └── 否 → 启动回滚

回滚类型选择：
      │
      ├── 最新部署引入 bug？
      │     → [应用代码回滚](#二应用代码回滚) (目标：< 2 分钟停机)
      │
      ├── 数据库迁移引入问题？
      │     → [数据库迁移回滚](#三数据库迁移回滚) (必须先备份)
      │
      ├── 配置/环境变量变更引入问题？
      │     → [配置变更回滚](#四配置变更回滚)
      │
      └── 多层面问题 / 无法快速定位？
            → [全量回滚](#五全量回滚最坏情况) (目标：< 10 分钟)
```

---

## 二、应用代码回滚

**目标停机时间：< 2 分钟**

### 2.1 前提条件

- 知道上一个稳定版本的 Docker 镜像 tag 或 git commit hash
- 具有生产服务器 SSH 访问权限

### 2.2 快速确认当前版本

```bash
# 查看当前运行的镜像标签
docker compose -f docker-compose.prod.yml ps --format json | jq '.[].Image'

# 查看 git 历史（找到上一个稳定 commit）
git log --oneline -10

# 查看当前后端版本（如果 health endpoint 返回版本号）
curl -s https://api.openclaude.io/health | jq .
```

### 2.3 回滚步骤

```bash
# 1. 进入部署目录
cd /path/to/openclaude

# 2. 获取上一个稳定 commit hash
ROLLBACK_COMMIT=<上一个稳定的 git commit hash>

# 3. 切换代码
git checkout $ROLLBACK_COMMIT

# 4. 重新构建并启动（backend + frontend）
docker compose -f docker-compose.prod.yml up --build -d backend frontend

# 5. 验证服务健康（等待健康检查通过）
watch -n 2 'docker compose -f docker-compose.prod.yml ps'

# 6. 验证 API 可访问
curl -s https://api.openclaude.io/health | jq .
```

### 2.4 仅回滚后端（推荐，更快）

```bash
# 重新构建并重启 backend 服务（不影响 frontend）
docker compose -f docker-compose.prod.yml up --build -d backend

# 观察启动日志
docker compose -f docker-compose.prod.yml logs -f backend
```

### 2.5 验证 Checklist

- [ ] `docker compose -f docker-compose.prod.yml ps` 显示所有服务 `Up (healthy)`
- [ ] `curl -s https://api.openclaude.io/health` 返回 `{"status": "ok"}`
- [ ] `/v1/models` 接口返回正常
- [ ] Grafana 监控中 5xx 错误率恢复到 <1%
- [ ] P95 延迟恢复到 <500ms
- [ ] 在 Slack `#openclade-ops` 发布恢复通知

---

## 三、数据库迁移回滚

> **警告：数据库回滚可能导致数据丢失。回滚前必须备份。**

### 3.1 回滚前必须备份

```bash
# 进入生产服务器
# 创建时间戳备份（在执行任何 downgrade 之前）
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker exec openclaude_postgres_1 pg_dump \
  -U ${POSTGRES_USER:-openclaude} \
  -d ${POSTGRES_DB:-openclaude} \
  > /backup/openclaude_pre_rollback_${TIMESTAMP}.sql

# 验证备份文件大小（确保不是空文件）
ls -lh /backup/openclaude_pre_rollback_${TIMESTAMP}.sql
```

### 3.2 查看当前迁移状态

```bash
# 查看当前 alembic 版本
cd /path/to/openclaude
docker compose -f docker-compose.prod.yml run --rm backend \
  alembic current

# 查看迁移历史
docker compose -f docker-compose.prod.yml run --rm backend \
  alembic history --verbose
```

### 3.3 回滚一个版本（常见场景）

```bash
# 回滚到上一个迁移版本（-1 表示降一级）
docker compose -f docker-compose.prod.yml run --rm backend \
  alembic downgrade -1

# 或指定目标版本（例如回滚到 revision 002）
docker compose -f docker-compose.prod.yml run --rm backend \
  alembic downgrade 002
```

### 3.4 已知迁移版本

| Revision | 描述 | 是否可逆 |
|----------|------|---------|
| `003` | 添加 `users.is_admin` 字段 | ✅ 可逆 |
| `002` | Miner Phase 3：referred_by_id, score history, auth tokens | ✅ 可逆 |
| `001` | 初始 Schema | ⚠️ 不建议回滚（初始化） |

### 3.5 不可逆迁移的处理方案

如果迁移包含以下操作，**不可直接 downgrade**：

- `DROP TABLE`（已在 downgrade 函数中删除的表）
- `DROP COLUMN`（删除了含数据的列）
- 数据类型不兼容变更

**处理方案：**
1. 从备份恢复（见 3.1 备份 + 下方恢复命令）
2. 或写专项补偿迁移（不 downgrade，而是向前修复）

```bash
# 从备份恢复（仅在必要时使用，会覆盖当前数据）
docker exec -i openclaude_postgres_1 psql \
  -U ${POSTGRES_USER:-openclaude} \
  -d ${POSTGRES_DB:-openclaude} \
  < /backup/openclaude_pre_rollback_${TIMESTAMP}.sql
```

### 3.6 迁移回滚后验证 Checklist

- [ ] `alembic current` 显示目标版本
- [ ] 重启 backend 服务（确保 ORM 与 Schema 一致）
- [ ] `curl -s https://api.openclaude.io/health` 返回正常
- [ ] 检查关键数据表完整性：`SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM requests;`
- [ ] 确认应用日志中无 SQLAlchemy 错误

---

## 四、配置变更回滚

### 4.1 环境变量回滚

**情况：** 修改了 `.env.prod` 或 Docker Compose 中的环境变量导致异常。

```bash
# 1. 查看当前环境变量（脱敏）
docker compose -f docker-compose.prod.yml config | grep -E "environment|env_file" -A 20

# 2. 恢复上一个版本的 .env.prod（从 git 或备份恢复）
git checkout HEAD~1 -- .env.prod

# 3. 重启受影响的服务（通常是 backend）
docker compose -f docker-compose.prod.yml up -d backend

# 4. 确认新配置生效
docker compose -f docker-compose.prod.yml exec backend env | grep -E "SECRET_KEY|DATABASE_URL|REDIS_URL" | sed 's/=.*/=<REDACTED>/'
```

### 4.2 Redis 数据清理（必要时）

> 仅在 Redis 中存储了错误配置或脏数据时执行。

```bash
# 连接到 Redis
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli -a ${REDIS_PASSWORD}

# 查看当前 key 数量（操作前确认）
INFO keyspace

# 清理特定前缀的 key（例如路由缓存）
SCAN 0 MATCH "miner:*" COUNT 100
# 确认后批量删除
redis-cli -a ${REDIS_PASSWORD} --scan --pattern "miner:*" | xargs redis-cli -a ${REDIS_PASSWORD} DEL

# 极端情况：清空整个 Redis（会清除所有会话和缓存，谨慎！）
# FLUSHALL  # 注释保留，需要时取消注释并三次确认
```

### 4.3 配置回滚验证 Checklist

- [ ] 重启服务后所有容器状态为 `Up (healthy)`
- [ ] 检查 backend 启动日志中无 `ERROR` 级别配置错误
- [ ] 验证 API 认证正常（JWT 签名有效）
- [ ] 验证 Redis 连接正常（health endpoint 中 redis 状态为 ok）

---

## 五、全量回滚（最坏情况）

**目标时间：< 10 分钟**
**适用场景：** 多层面问题、无法快速定位根因、P0 事件且常规回滚无效。

### 5.1 全量回滚步骤

```bash
# 1. 立刻发布用户通知（见 6.1 降级通知模板）

# 2. 停止所有服务（保留数据卷）
cd /path/to/openclaude
docker compose -f docker-compose.prod.yml down

# 3. 切换到上一个稳定标签（从 git tags 或已知稳定 commit）
STABLE_VERSION=<稳定版本 tag 或 commit hash>
git checkout $STABLE_VERSION

# 4. 创建数据库备份（即使是出问题的版本，也要留存现场）
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker compose -f docker-compose.prod.yml up -d postgres
sleep 5
docker exec openclaude_postgres_1 pg_dump \
  -U ${POSTGRES_USER:-openclaude} \
  ${POSTGRES_DB:-openclaude} \
  > /backup/openclaude_incident_${TIMESTAMP}.sql

# 5. 如果数据库 Schema 需要回滚
docker compose -f docker-compose.prod.yml run --rm backend \
  alembic downgrade <目标版本>

# 6. 重建并启动所有服务
docker compose -f docker-compose.prod.yml up --build -d

# 7. 等待健康检查通过（通常 30-60 秒）
watch -n 3 'docker compose -f docker-compose.prod.yml ps'
```

### 5.2 影响评估

| 层面 | 影响 | 恢复时间估计 |
|------|------|------------|
| 应用代码回滚 | 新功能不可用，可能触发 API 不兼容 | ~2 分钟 |
| 数据库迁移回滚 | 新 Schema 字段丢失，可能丢失新增数据 | ~5 分钟（含备份） |
| 配置回滚 | 可能影响第三方集成 | ~1 分钟 |
| 全量回滚 | 上述所有影响之和 | ~10 分钟 |

### 5.3 全量回滚验证 Checklist

- [ ] `docker compose -f docker-compose.prod.yml ps` 所有服务 `Up (healthy)`
- [ ] `curl -s https://api.openclaude.io/health` 返回 `{"status": "ok", ...}`
- [ ] `alembic current` 返回预期版本
- [ ] `/v1/models` 接口返回正常
- [ ] `/v1/messages` 接口可以成功路由到 Miner
- [ ] Grafana 中错误率、延迟恢复正常
- [ ] 在 `#openclade-ops` 发布恢复通知（见 6.2 恢复通知模板）
- [ ] 在 issue 追踪系统中记录事件，触发 Post-mortem 流程

---

## 六、用户通知模板

### 6.1 服务降级通知（回滚开始时发送）

```
【OpenClaude 服务通知】

我们检测到生产环境出现异常，正在进行紧急修复。

- 影响：API 访问可能出现短暂中断或响应延迟
- 预计恢复时间：约 XX 分钟
- 当前状态：工程团队正在处理

对此造成的不便，我们深表歉意。我们将在问题解决后发布更新通知。

如需紧急支持，请联系：support@openclaude.io
```

### 6.2 服务恢复通知（回滚完成后发送）

```
【OpenClaude 服务恢复通知】

感谢您的耐心等待。

- 恢复时间：[北京时间 YYYY-MM-DD HH:MM]
- 影响时长：约 XX 分钟
- 根本原因：[简要说明，详细 Post-mortem 报告稍后发布]

所有服务已完全恢复正常运行。

如仍遇到问题，请联系：support@openclaude.io
```

### 6.3 内部 Slack 通知格式

```
🚨 [ROLLBACK IN PROGRESS]
- 触发人：@xxx
- 原因：[简要说明]
- 回滚类型：[应用/数据库/配置/全量]
- 目标版本：[commit hash 或 revision]
- 预计完成：[HH:MM]

进展更新将每 5 分钟在此线程发布。
```

---

## 七、事后处理

回滚完成后，必须在 24 小时内：

1. **记录事件**：在 issue 追踪中创建 Incident 记录
2. **根因分析**：识别导致需要回滚的根本原因
3. **Post-mortem**：按照 [oncall_runbook.md](./oncall_runbook.md#四post-mortem-模板) 的模板填写
4. **预防措施**：制定具体的改进措施，防止同类事件重发

---

*最后更新：2026-03-16 | 如有改进建议，请在 KYD project 创建 issue*
