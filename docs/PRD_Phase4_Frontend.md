# OpenClade Phase 4 PRD：前端开发

**版本：** v1.0
**状态：** 正式
**作者：** Product Manager
**更新：** 2026-03-15
**关联任务：** KYD-12

---

## 一、背景与目标

### 1.1 背景

Phase 1-3 完成了后端能力（API 代理、计费、Miner 管理、评分引擎）。Phase 4 将构建三个前端应用，让用户和 Miner 能通过 Web 界面使用 OpenClade 服务，让管理员能监控全局运营状态。

**技术栈（已在技术架构文档中确定）：**
- 框架：Next.js 14 + TypeScript
- UI：Tailwind CSS + shadcn/ui
- 状态管理：TanStack Query（服务端状态）+ Zustand（客户端状态）
- 图表：Recharts
- Web3：`@polkadot/api`（Miner 钱包连接）

### 1.2 三个前端应用

| 应用 | 域名 | 目标用户 |
|------|------|---------|
| User Portal | `user.openclaude.io` | 开发者、企业（API 使用方） |
| Miner Portal | `miner.openclaude.io` | API Key 提供者 |
| Admin Dashboard | `dash.openclaude.io` | 运营管理员（内部） |

---

## 二、用户端（User Portal）

### 2.1 页面结构

```
user.openclaude.io
│
├── / (Landing Page)          -- 未登录展示
├── /auth
│   ├── /login
│   ├── /register             -- 含推荐码输入
│   └── /forgot-password
│
├── /dashboard (登录后首页)
├── /api-keys                 -- API Key 管理
├── /billing
│   ├── /recharge             -- 充值页面
│   └── /history              -- 充值 + 消费记录
├── /usage                    -- 用量统计
├── /docs                     -- 内嵌 API 文档
│   ├── /quickstart
│   ├── /api-reference
│   └── /examples
└── /settings                 -- 账户设置
```

### 2.2 Landing Page（`/`）

**目标：** 传达核心价值主张，驱动注册转化

**内容模块：**

| 模块 | 内容 |
|------|------|
| Hero | 标题："Claude API，官方价格 25%"，CTA："免费注册 →" |
| 价格对比 | 并列展示官方价格 vs OpenClade 价格，高亮节省百分比 |
| 接入示例 | 一段 Python/JS 代码，只改 `base_url`，零改动接入 |
| 运作机制 | 3 步图示：注册 → 获取 Key → 调用 API |
| 信任背书 | 活跃 Miner 数、处理 Token 数、在线时长（实时数据） |
| 常见问题 | 折叠式 FAQ，解答合规、稳定性、退款等问题 |

**技术要点：**
- 信任数据通过 `/api/v1/public/stats` 拉取（无需登录的公开端点）
- 支持 i18n（先中英双语）

### 2.3 注册页面（`/auth/register`）

**字段：**
- 邮箱（必填，需验证格式）
- 密码（必填，≥8位，含大小写和数字）
- 确认密码
- 推荐码（选填，8位字母数字，格式：`OC-XXXXXXXX`）
- 同意服务条款（checkbox，必填）

**交互逻辑：**
1. 提交后发送邮箱验证码（后端实现 Phase 4）
2. 推荐码实时验证（`GET /api/v1/referral/validate/{code}`，有效则显示绿色）
3. 注册成功 → 自动登录 → 跳转 `/dashboard`
4. 若推荐码有效，注册成功页展示 Miner 推荐奖励说明

### 2.4 Dashboard（`/dashboard`）

**布局：** 左侧导航栏 + 右侧内容区

**核心指标卡（顶部）：**
| 卡片 | 数据 |
|------|------|
| 账户余额 | `$XX.XX` + "充值" 快捷按钮 |
| 今日用量 | `X tokens`（Input + Output 分列） |
| 本月消费 | `$XX.XX` |
| 活跃 Key | `N` 个 |

**快捷操作：**
- 复制当前主 API Key
- 跳转充值
- 查看 API 文档

**用量趋势图（最近7天）：**
- 折线图：每日 Token 消耗
- 按模型分色（Opus/Sonnet/Haiku）

### 2.5 API Key 管理（`/api-keys`）

**Key 列表视图：**

| 字段 | 说明 |
|------|------|
| 名称 | 可编辑 |
| Key 预览 | `oc_...xxxx`（仅显示前4和后4位） |
| 状态 | Active / Disabled |
| 创建时间 | — |
| 最后使用 | — |
| 本月用量 | Token 数 |
| 操作 | 复制、禁用/启用、删除 |

**创建 Key 弹窗：**
- 名称（必填）
- 速率限制（选填，requests/minute）
- 创建成功后**一次性展示完整 Key**，提醒用户保存

**安全设计：**
- 完整 Key 仅在创建时显示一次
- 列表页显示末4位 Preview
- 删除需二次确认："此操作不可恢复，是否确认删除？"

### 2.6 充值与账单（`/billing`）

**充值页（`/billing/recharge`）：**

| 元素 | 说明 |
|------|------|
| 余额展示 | 当前余额 + 低余额预警（余额 < $5 时黄色警告） |
| 快捷金额 | $10 / $50 / $100 / 自定义 |
| 支付方式 | USDT（TRC20/ERC20）/ USDC（ERC20）/ TAO |
| 支付流程 | 选金额 → 选币种 → 显示收款地址 + QR码 → 等待确认 |
| 状态轮询 | 每 30 秒检查支付状态 |

**交易记录（`/billing/history`）：**

| 字段 | 充值记录 | 消费记录 |
|------|---------|---------|
| 时间 | ✅ | ✅ |
| 类型 | "充值" | "消费" |
| 金额 | +$XX.XX | -$XX.XX |
| 状态 | 待确认/完成/失败 | 完成 |
| 详情 | 链上 TxHash | 模型/Token数 |

### 2.7 用量统计（`/usage`）

**时间范围选择器：** 今日 / 最近7天 / 本月 / 自定义

**统计视图：**

1. **汇总卡片：** 总 Input Token / 总 Output Token / 总费用 / 平均每日
2. **每日趋势图（折线图）：** 按日展示 Token 消耗，可按模型过滤
3. **模型分布（饼图）：** 各模型使用占比
4. **按 Key 明细（表格）：** 各 API Key 的用量汇总

**导出功能：** 导出 CSV（日期、模型、Input Tokens、Output Tokens、费用）

### 2.8 API 文档（`/docs`）

**快速开始（`/docs/quickstart`）：**

```markdown
## 30 秒接入 OpenClade

1. 注册账号，获取 API Key
2. 替换 base_url，代码零改动

```python
import anthropic

client = anthropic.Anthropic(
    api_key="oc_your_key_here",
    base_url="https://api.openclaude.io",
)

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "你好！"}],
)
```
```

**API 参考（`/docs/api-reference`）：**
- 直接嵌入 FastAPI 自动生成的 Swagger UI（`/docs` 端点）
- 或使用 Redoc 提供更好的阅读体验

**代码示例（`/docs/examples`）：**
- Python（含 streaming）
- JavaScript/TypeScript
- cURL
- 每个示例可复制，有实际可运行效果

---

## 三、Miner 端（Miner Portal）

### 3.1 页面结构

```
miner.openclaude.io
│
├── / (Landing Page)           -- Miner 招募页
├── /auth
│   ├── /connect               -- 连接钱包
│   └── /register              -- Miner 注册（质押+提交Key）
│
├── /dashboard (需钱包连接)
├── /keys                      -- Claude API Key 管理
├── /earnings                  -- 收益统计
├── /quality                   -- 服务质量监控
├── /referral                  -- 推荐系统
├── /staking                   -- 质押管理
└── /docs                      -- Miner 接入文档
```

### 3.2 Landing Page（`/`）

**目标：** 吸引 Claude API Key 持有者成为 Miner

**内容模块：**
| 模块 | 内容 |
|------|------|
| Hero | "用闲置 Claude API Key 赚 TAO" |
| 收益计算器 | 输入：持有 API Key 数量 + 预估日调用量；输出：预估日 TAO 收益 |
| 入门流程 | 3 步：连接钱包 → 提交 Key → 开始赚收益 |
| 准入要求 | 展示准入门槛（在线率、延迟等），让 Miner 知道要求 |
| Miner 排行 | 公开排行榜（脱敏 hotkey + 收益数据，激励竞争） |

### 3.3 钱包连接与注册（`/auth/connect` → `/auth/register`）

**步骤1：连接钱包（`/auth/connect`）**

- 支持钱包：Polkadot.js Extension、SubWallet、Talisman
- 检测到钱包扩展 → 请求连接 → 显示账号列表 → 用户选择账号
- 未安装钱包 → 显示安装引导（链接到各钱包官网）
- 连接成功 → 跳转注册或 Dashboard（已注册则直接登录）

**步骤2：Miner 注册（`/auth/register`）**

填写信息：
- Miner 名称（展示名）
- 确认 hotkey 地址（自动从钱包读取）
- 签名验证（调用钱包签名 → 后端验证）
- 提交第一个 Claude API Key（初始必须有至少一个 Key）
- 确认质押要求（5 TAO）

注册流程状态展示（步骤条）：
```
[连接钱包] → [填写信息] → [签名验证] → [提交 Key] → [等待激活]
```

### 3.4 Dashboard（`/dashboard`）

**核心指标卡：**
| 卡片 | 内容 |
|------|------|
| 今日收益 | 预估 TAO 数量 |
| 本月总收益 | 预估 TAO + USD 换算 |
| 当前评分 | 服务分 + 推荐加成（可视化进度条） |
| 服务质量 | 在线率 + 探测成功率（绿/黄/红状态灯） |
| 准入状态 | 全部 ✅ 或标出不满足的项 |

**实时状态：** 每 30 秒自动刷新

### 3.5 Claude API Key 管理（`/keys`）

**Key 列表：**
| 字段 | 说明 |
|------|------|
| Key 预览 | 显示末4位 |
| 状态 | Active / Disabled / Banned（被验证方检测为失效） |
| 添加时间 | — |
| 今日调用次数 | — |
| 操作 | 启用/禁用、删除 |

**添加新 Key：**
1. 粘贴 Claude API Key
2. 自动验证可用性（调用探测请求）
3. 验证成功 → 加密存储 → 状态 Active
4. 验证失败 → 提示 Key 无效或已超额

**Key 状态说明：**
- `Active`：正常被路由使用
- `Disabled`：Miner 主动禁用，不参与路由
- `Banned`：Validator 检测到 Key 失效，自动标记（需 Miner 手动删除）

### 3.6 收益统计（`/earnings`）

**汇总视图：**
- 今日预估收益（TAO）
- 本月预估收益（TAO / USD）
- 全部时间累计（TAO / USD）
- 全网排名（第 N 名，共 M 个 Miner）

**每日收益趋势图（折线图）：**
- X轴：日期
- Y轴：预估 TAO 收益
- Tooltip：服务分 + 推荐加成 + 处理 Token 数

**明细表格：**
| 日期 | 服务分 | 推荐加成 | 最终得分 | 处理 Tokens | 预估 TAO |
|------|-------|---------|---------|------------|--------|
| 2026-03-14 | 72.5 | 12% | 81.2 | 2.1M | 0.41 |

### 3.7 服务质量监控（`/quality`）

**实时指标（每30秒刷新）：**

```
在线率         [████████░░] 85%  ✅ (≥80%)
探测成功率     [█████████░] 93%  ✅ (≥90%)
平均延迟       [███░░░░░░░] 1,240ms ✅ (≤3,000ms)
质押量         5.2 TAO           ✅ (≥5 TAO)

准入状态：✅ 全部达标，正在获得 TAO 收益
```

**探测历史（最近 24 小时，折线图）：**
- 延迟趋势
- 成功率趋势

**告警设置：**
- 在线率低于 85% 时发送邮件/Telegram 通知
- 探测成功率低于 92% 时告警

### 3.8 推荐系统（`/referral`）

**我的推荐码展示：**
```
┌─────────────────────────────────────────────────────────┐
│  我的推荐码：OC-A1B2C3D4                                  │
│  推荐链接：https://openclaude.io/r/OC-A1B2C3D4  [复制]  │
└─────────────────────────────────────────────────────────┘
```

**推荐统计：**
| 指标 | 数值 |
|------|------|
| 累计推荐用户 | 23 人 |
| 本期有效用户（消费≥$5）| 8 人 |
| 本期推荐用户消费 | $1,240 |
| 当前推荐加成 | +7.4% |

**推荐用户列表（脱敏）：**
| 用户（脱敏） | 注册时间 | 本期消费 |
|------------|---------|---------|
| u***1 | 2026-03-01 | $340 |
| u***2 | 2026-02-15 | $210 |

**分享辅助：**
- 预置分享文案（中英文）
- 可复制到 Twitter/Discord/WeChat

### 3.9 质押管理（`/staking`）

```
当前质押：5.2 TAO
最低要求：5.0 TAO ✅

[增加质押] [减少质押] [退出 Miner]
```

**说明：** Phase 4 为信息展示页，实际质押操作通过 Polkadot.js 钱包在链上执行。点击按钮跳转到外部教程或辅助工具。

---

## 四、管理后台（Admin Dashboard）

### 4.1 访问控制

- 独立域名：`dash.openclaude.io`
- 账号：特殊管理员账号（`is_admin=True`）
- 不对外公开

### 4.2 核心功能

#### 4.2.1 概览（Overview）

**实时指标（每10秒刷新）：**
| 指标 | 数据 |
|------|------|
| 今日请求数 | X,XXX |
| 当前 QPS | XX |
| 今日 Token | X.X M |
| 今日收入（用户付费） | $XX |
| 今日成本（估算） | $XX |
| 活跃用户 | XX |
| 在线 Miner | XX |
| 合格 Miner（满足准入）| XX |

#### 4.2.2 Miner 管理

**Miner 列表（可排序可筛选）：**

| 列 | 说明 |
|----|------|
| Hotkey（缩写） | — |
| 状态 | Active/Inactive |
| 当前评分 | — |
| 在线率 | — |
| 探测成功率 | — |
| 平均延迟 | — |
| 今日收益（估算 TAO）| — |
| Key 数量 | 活跃/总数 |
| 操作 | 查看详情、强制下线、封禁 |

**Miner 详情页：**
- 所有质量指标历史图表
- 评分历史
- 推荐用户列表
- API Key 状态

#### 4.2.3 用户管理

**用户列表：**
- 搜索（邮箱/ID）
- 余额显示
- 今日消费
- 注册来源（推荐码）
- 操作：查看、封禁、人工调整余额

**充值审核（人工确认支付，MVP 阶段）：**
- 待确认充值请求列表
- 核对链上 TX → 确认 → 到账

#### 4.2.4 财务报表

**收入支出汇总（可按日/周/月查看）：**

| 项目 | 数值 |
|------|------|
| 用户付费收入 | $XX,XXX |
| 运营成本（服务器等）| $X,XXX |
| 用户付费利润 | $X,XXX |
| Owner TAO Emission | XX TAO ≈ $XX,XXX |
| 月度总收益 | $XX,XXX |

**Token 经济图：**
- 用户付费 vs 运营成本趋势
- TAO Emission 价值趋势

#### 4.2.5 告警中心

告警规则（可配置）：
- 合格 Miner < 3 → 红色告警
- 在线率整体下降 > 20% → 黄色告警
- 用户充值失败率 > 10% → 黄色告警
- 单用户异常消费（1小时内 > $50）→ 安全告警

---

## 五、公共端点（新增后端需求）

Phase 4 前端需要以下后端 API，在 Phase 3 中补充实现：

```
GET /api/v1/public/stats
  说明：无需登录的公开统计数据（用于 Landing Page）
  返回：
  {
    active_miners: int,
    total_requests_today: int,
    total_tokens_processed: int,
    uptime_percent: float
  }

GET /api/v1/referral/validate/{code}
  说明：验证推荐码是否有效
  返回：{ valid: bool, miner_name: string | null }

GET /api/v1/admin/overview (需管理员权限)
  返回：全局运营指标

GET /api/v1/admin/miners?page=1&limit=20
GET /api/v1/admin/users?page=1&limit=20
GET /api/v1/admin/finance/summary
```

---

## 六、非功能性需求

### 6.1 性能

| 指标 | 要求 |
|------|------|
| 首屏加载时间（LCP） | < 2.5 秒 |
| 交互响应时间（INP） | < 200ms |
| Dashboard 数据刷新 | 不阻塞 UI |
| 移动端适配 | 响应式，支持常见移动尺寸 |

### 6.2 安全

- 所有 API 调用通过 HTTPS
- JWT Token 存储在 httpOnly Cookie（非 localStorage）
- API Key 完整值仅在创建时展示一次，不缓存
- 钱包私钥永远不离开用户设备

### 6.3 用户体验

- 加载状态：所有异步操作有 Loading 指示器
- 错误处理：友好错误页面，非技术语言描述问题
- 空状态：列表为空时有引导性提示（而非空白页面）
- 关键操作二次确认：删除 Key、退出 Miner 等操作

---

## 七、验收标准

### User Portal
- [ ] 注册流程：含推荐码绑定、注册成功自动登录
- [ ] API Key 创建时完整 Key 只展示一次
- [ ] 充值页面支持 USDT/USDC，含收款地址和 QR 码
- [ ] 用量统计图表正确显示
- [ ] Landing Page 在 GTmetrix 评分 ≥ B 级

### Miner Portal
- [ ] Polkadot.js 钱包连接和签名验证流程完整
- [ ] Claude API Key 添加时自动验证可用性
- [ ] 收益统计和质量指标数据实时刷新
- [ ] 推荐码可正确复制，推荐统计数据准确

### Admin Dashboard
- [ ] Miner 列表可排序筛选，状态实时
- [ ] 财务报表数据与后端一致
- [ ] 告警规则触发时正确显示告警

---

## 八、开发排期估算

| 模块 | 估算（工作日） |
|------|--------------|
| 项目脚手架（Next.js + shadcn/ui 初始化）| 1天 |
| User Portal：Landing + Auth | 3天 |
| User Portal：Dashboard + API Keys | 3天 |
| User Portal：Billing + Usage | 3天 |
| User Portal：Docs 页面 | 2天 |
| Miner Portal：Auth（钱包连接）| 3天 |
| Miner Portal：Dashboard + Keys | 3天 |
| Miner Portal：Earnings + Quality | 3天 |
| Miner Portal：Referral + Staking | 2天 |
| Admin Dashboard | 4天 |
| 响应式适配 + 测试 | 3天 |
| **合计** | **~30天** |

---

*文档版本: v1.0 | 最后更新: 2026-03-15*
