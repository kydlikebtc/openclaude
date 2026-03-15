# OpenClade Mainnet 上线检查清单

**版本：** v1.0
**最后更新：** 2026-03-15
**关联 Issue：** KYD-36
**状态：** 🚧 进行中（Phase 6 Testnet 阶段）

---

## 使用说明

本文档是 OpenClade 主网上线前的完整检查清单，分为六大维度。
每个条目完成后由负责人打勾并标注日期。

**状态图例：**
- ✅ 已完成
- 🚧 进行中
- ⏳ 待启动
- ❌ 阻塞

---

## 一、技术就绪（Technical Readiness）

### 1.1 子网核心

| 检查项 | 状态 | 负责人 | 完成日期 | 备注 |
|--------|------|--------|----------|------|
| Miner 节点代码完成并通过单元测试 | ✅ | Engineering | 2026-03-15 | 121/121 通过 |
| Validator 节点代码完成并通过单元测试 | ✅ | Engineering | 2026-03-15 | 121/121 通过 |
| LLMAPISynapse 协议验证 | ✅ | Engineering | 2026-03-15 | 本地 E2E 6/6 通过 |
| bittensor v10 API 兼容性 | ✅ | Engineering | 2026-03-15 | CamelCase API 已适配 |
| Testnet 连接验证 | ✅ | Engineering | 2026-03-15 | 区块 6,689,396 |
| Testnet 子网注册 | ⏳ | Engineering | — | 需要 ~100 testnet TAO |
| Testnet Validator 节点稳定运行 ≥ 48h | ⏳ | Engineering | — | 依赖子网注册 |
| Testnet Miner 节点稳定运行 ≥ 48h | ⏳ | Engineering | — | 依赖子网注册 |
| Mainnet 配置参数更新（netuid、网络、IP） | ⏳ | Engineering | — | 见迁移评估报告 |
| Mainnet 子网注册 | ⏳ | CEO/Owner | — | 需要 300 TAO |

### 1.2 后端服务

| 检查项 | 状态 | 负责人 | 完成日期 | 备注 |
|--------|------|--------|----------|------|
| FastAPI 后端所有 API 路由测试通过 | ✅ | Engineering | 2026-03-15 | — |
| 用户认证（注册/登录/JWT）正常 | ✅ | Engineering | 2026-03-15 | — |
| API Key 管理功能完整 | ✅ | Engineering | 2026-03-15 | — |
| 计费/充值系统完整 | ✅ | Engineering | 2026-03-15 | — |
| 使用量统计与账单准确 | ✅ | Engineering | 2026-03-15 | — |
| 推荐系统（Referral）功能完整 | ✅ | Engineering | 2026-03-15 | — |
| 路由引擎接入 Testnet Miner | ⏳ | Engineering | — | 依赖 Testnet 上线 |
| 路由引擎压力测试（1000 QPS） | ⏳ | Engineering | — | — |
| 数据库迁移脚本验证 | ⏳ | Engineering | — | 生产环境执行前必须测试 |
| Redis 缓存配置（生产集群） | ⏳ | Engineering | — | — |

### 1.3 前端

| 检查项 | 状态 | 负责人 | 完成日期 | 备注 |
|--------|------|--------|----------|------|
| 用户控制台功能完整 | ✅ | Engineering | 2026-03-15 | — |
| Miner 看板功能完整 | ✅ | Engineering | 2026-03-15 | — |
| 管理后台功能完整 | ✅ | Engineering | 2026-03-15 | — |
| 跨浏览器兼容性测试 | ⏳ | Engineering | — | Chrome/Firefox/Safari |
| 移动端响应式测试 | ⏳ | Engineering | — | — |
| 前端性能优化（LCP < 2.5s） | ⏳ | Engineering | — | — |

### 1.4 基础设施

| 检查项 | 状态 | 负责人 | 完成日期 | 备注 |
|--------|------|--------|----------|------|
| Docker Compose 生产配置验证 | ✅ | Engineering | 2026-03-15 | docker-compose.prod.yml |
| 域名 api.openclaude.io 配置 | ⏳ | DevOps | — | — |
| SSL 证书（Let's Encrypt / Cloudflare） | ⏳ | DevOps | — | — |
| CDN/反向代理配置（Nginx/Cloudflare） | ⏳ | DevOps | — | — |
| 数据库高可用（PostgreSQL 主从） | ⏳ | DevOps | — | — |
| 备份策略（每日自动备份 + 异地存储） | ⏳ | DevOps | — | — |
| 灾难恢复演练 | ⏳ | DevOps | — | — |

---

## 二、安全（Security）

| 检查项 | 状态 | 负责人 | 完成日期 | 备注 |
|--------|------|--------|----------|------|
| OWASP Top 10 安全审计 | ✅ | Security | 2026-03-15 | KYD-21 |
| SQL 注入防护（参数化查询） | ✅ | Engineering | 2026-03-15 | — |
| XSS 防护 | ✅ | Engineering | 2026-03-15 | — |
| CSRF 防护 | ✅ | Engineering | 2026-03-15 | — |
| Rate Limiting（API 限流） | ✅ | Engineering | 2026-03-15 | — |
| JWT 密钥安全（生产密钥轮换） | ⏳ | DevOps | — | 不可使用默认值 |
| 生产环境 Secret 管理（非硬编码） | ⏳ | DevOps | — | 使用 Vault 或云 KMS |
| 所有 API Key 加密存储 | ✅ | Engineering | 2026-03-15 | — |
| Miner API Key 访问权限最小化 | ✅ | Engineering | 2026-03-15 | — |
| 第三方依赖安全扫描 | ⏳ | Engineering | — | 使用 Snyk 或 pip-audit |
| 渗透测试（上线前） | ⏳ | Security | — | 可委托第三方 |
| 安全响应头配置 | ✅ | Engineering | 2026-03-15 | X-Frame-Options 等 |
| CORS 配置（仅允许生产域名） | ⏳ | Engineering | — | 当前含 localhost |

---

## 三、文档（Documentation）

| 检查项 | 状态 | 负责人 | 完成日期 | 备注 |
|--------|------|--------|----------|------|
| 用户入门指南（User_Guide.md） | ✅ | PM | 2026-03-15 | — |
| Miner 上手指南（Miner_Guide.md） | ✅ | PM | 2026-03-15 | — |
| API 参考文档（API_Reference.md） | ✅ | PM | 2026-03-15 | 需定期与代码同步 |
| 系统架构文档（Architecture.md） | ✅ | Engineering | 2026-03-15 | — |
| README.md 路线图更新 | ✅ | PM | 2026-03-15 | KYD-36 |
| 本上线检查清单 | ✅ | PM | 2026-03-15 | 当前文件 |
| Testnet 部署报告 | ✅ | Engineering | 2026-03-15 | — |
| Mainnet 迁移评估报告 | ✅ | Engineering | 2026-03-15 | — |
| FAQ 页面（网站内） | ⏳ | PM | — | 基于 Miner/User FAQ |
| 隐私政策（Privacy Policy） | ⏳ | Legal/PM | — | 上线必须 |
| 服务条款（Terms of Service） | ⏳ | Legal/PM | — | 上线必须 |

---

## 四、运营（Operations）

### 4.1 监控与告警

| 检查项 | 状态 | 负责人 | 完成日期 | 备注 |
|--------|------|--------|----------|------|
| Prometheus 监控部署 | ✅ | DevOps | 2026-03-15 | — |
| Grafana 看板配置 | ✅ | DevOps | 2026-03-15 | — |
| SLO 告警阈值配置 | ✅ | DevOps | 2026-03-15 | KYD 监控验证 |
| P99 延迟告警（> 3000ms） | ✅ | DevOps | 2026-03-15 | — |
| 错误率告警（> 1%） | ✅ | DevOps | 2026-03-15 | — |
| Miner 离线告警 | ⏳ | DevOps | — | 依赖 Testnet 运行 |
| 业务指标监控（DAU、充值额、API 调用量） | ⏳ | DevOps | — | — |
| On-call 响应流程 | ⏳ | CEO | — | 定义 P0/P1 响应 SLA |

### 4.2 上线计划

| 检查项 | 状态 | 负责人 | 完成日期 | 备注 |
|--------|------|--------|----------|------|
| 灰度发布计划（内测 → 公测 → 全量） | ⏳ | CEO/PM | — | — |
| Rollback 方案准备 | ⏳ | Engineering | — | — |
| 上线时间窗口选择（低峰期） | ⏳ | CEO | — | — |
| 客服/支持渠道就绪（Discord/Telegram） | ⏳ | CEO | — | — |
| 用户反馈收集机制 | ⏳ | PM | — | — |

---

## 五、社区与推广（Community & Growth）

| 检查项 | 状态 | 负责人 | 完成日期 | 备注 |
|--------|------|--------|----------|------|
| 矿工招募帖（Bittensor Discord） | ⏳ | CEO | — | — |
| 首批矿工激励方案 | ⏳ | CEO/PM | — | — |
| 官网上线（openclaude.io） | ⏳ | Engineering | — | — |
| Twitter/X 账号建立 | ⏳ | CEO | — | — |
| Bittensor 社区公告 | ⏳ | CEO | — | 子网注册后发布 |
| GitHub 仓库公开（代码开源） | ⏳ | CEO | — | — |
| 初始流动性/种子用户计划 | ⏳ | CEO | — | — |

---

## 六、合规（Compliance）

| 检查项 | 状态 | 负责人 | 完成日期 | 备注 |
|--------|------|--------|----------|------|
| Anthropic 使用政策合规确认 | ⏳ | CEO/Legal | — | 转售/代理是否合规 |
| KYC/AML 需求评估 | ⏳ | Legal | — | 视司法管辖区而定 |
| 用户数据隐私合规（GDPR/CCPA） | ⏳ | Legal | — | — |
| TAO 代币法律地位确认 | ⏳ | Legal | — | 视运营地区而定 |
| 开源许可证合规（MIT 兼容依赖） | ✅ | Engineering | 2026-03-15 | — |

---

## 上线就绪评估

```
当前状态（2026-03-15）

技术就绪：  ████████░░  80%  （Testnet 上线待 TAO）
安全：      ████████░░  80%  （生产密钥管理待完成）
文档：      █████████░  90%  （法律文档待补充）
运营：      ████░░░░░░  40%  （监控已就绪，上线流程待定）
社区：      ██░░░░░░░░  20%  （矿工招募待启动）
合规：      ███░░░░░░░  30%  （法律评估待完成）

综合就绪度：█████████░  60%  — 预计 Phase 6 完成后达 80%
```

---

## 附：关键阻塞项（Critical Blockers）

以下条目未完成则**不得进行主网上线**：

1. **Testnet 完整验证**（≥ 48h 稳定运行）
2. **Anthropic 使用政策合规确认**
3. **隐私政策 + 服务条款** 发布
4. **生产密钥管理** 就绪（不使用默认值）
5. **主网子网注册** 完成（300 TAO）

---

*本文档由 PM 维护，随项目进展持续更新。*
