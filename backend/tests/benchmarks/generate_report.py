"""生成 Markdown 格式的压测报告。

从 locust --csv 输出的 CSV 文件中读取数据，分析 P95/P99 延迟和错误率，
生成可提交到版本库的 Markdown 报告。

使用方法:
    python3 tests/benchmarks/generate_report.py \
        --csv-prefix docs/benchmark_500qps_20260315 \
        --target-qps 500 \
        --output docs/load_test_report.md
"""

import argparse
import csv
import os
from datetime import datetime
from pathlib import Path


def load_stats(csv_prefix: str) -> list[dict]:
    stats_file = f"{csv_prefix}_stats.csv"
    if not os.path.exists(stats_file):
        raise FileNotFoundError(f"Stats file not found: {stats_file}")

    with open(stats_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_stats_history(csv_prefix: str) -> list[dict]:
    history_file = f"{csv_prefix}_stats_history.csv"
    if not os.path.exists(history_file):
        return []
    with open(history_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _fmt_ms(val: str) -> str:
    try:
        return f"{float(val):.1f}ms"
    except (ValueError, TypeError):
        return str(val)


def _pct(val: str, total: str) -> str:
    try:
        return f"{float(val) / float(total) * 100:.2f}%"
    except (ValueError, ZeroDivisionError, TypeError):
        return "N/A"


def generate_markdown(
    stats: list[dict],
    csv_prefix: str,
    target_qps: int,
    timestamp: str,
) -> str:
    # 整理聚合行（Aggregated）
    aggregated = next((r for r in stats if r.get("Name") == "Aggregated"), None)
    endpoint_rows = [r for r in stats if r.get("Name") != "Aggregated"]

    # 验收标准评估
    p95_pass = False
    error_pass = False
    p95_val = "N/A"
    error_rate = "N/A"

    if aggregated:
        try:
            p95_ms = float(aggregated.get("95%", 0))
            p95_val = f"{p95_ms:.1f}ms"
            p95_pass = p95_ms < 500
        except (ValueError, TypeError):
            pass

        total_req = aggregated.get("Request Count", "0")
        failed_req = aggregated.get("Failure Count", "0")
        try:
            total_i = int(total_req)
            failed_i = int(failed_req)
            if total_i > 0:
                error_pct = failed_i / total_i * 100
                error_rate = f"{error_pct:.3f}%"
                error_pass = error_pct == 0
            else:
                error_rate = "N/A (0 requests)"
        except (ValueError, TypeError):
            pass

    p95_badge = "✅ PASS" if p95_pass else "❌ FAIL"
    error_badge = "✅ PASS" if error_pass else "❌ FAIL"

    # 端点汇总表
    endpoint_table_rows = []
    for row in endpoint_rows:
        name = row.get("Name", "")
        method = row.get("Type", "")
        req_count = row.get("Request Count", "0")
        fail_count = row.get("Failure Count", "0")
        median = _fmt_ms(row.get("Median Response Time", ""))
        p95 = _fmt_ms(row.get("95%", ""))
        p99 = _fmt_ms(row.get("99%", ""))
        rps = row.get("Requests/s", "")
        try:
            rps_fmt = f"{float(rps):.1f}"
        except (ValueError, TypeError):
            rps_fmt = rps
        fail_pct = _pct(fail_count, req_count)
        endpoint_table_rows.append(
            f"| `{method} {name}` | {req_count} | {median} | {p95} | {p99} | {rps_fmt} | {fail_pct} |"
        )

    endpoint_table = "\n".join(endpoint_table_rows) if endpoint_table_rows else "| — | — | — | — | — | — | — |"

    agg_median = _fmt_ms(aggregated.get("Median Response Time", "N/A")) if aggregated else "N/A"
    agg_p99 = _fmt_ms(aggregated.get("99%", "N/A")) if aggregated else "N/A"
    agg_rps = aggregated.get("Requests/s", "N/A") if aggregated else "N/A"
    try:
        agg_rps_fmt = f"{float(agg_rps):.1f}"
    except (ValueError, TypeError):
        agg_rps_fmt = str(agg_rps)

    report = f"""# OpenClade 路由引擎负载测试报告

**生成时间**: {timestamp}
**目标 QPS**: {target_qps}
**测试模式**: Mock 矿工（`ANTHROPIC_BASE_URL` 指向本地 mock server，延迟 ~10ms）

---

## 验收标准

| 指标 | 阈值 | 实测值 | 结论 |
|------|------|--------|------|
| P95 延迟 (路由层) | < 500ms | {p95_val} | {p95_badge} |
| 错误率 (500 QPS) | 0% | {error_rate} | {error_badge} |

---

## 整体性能汇总

| 指标 | 值 |
|------|----|
| 中位数延迟 (P50) | {agg_median} |
| P95 延迟 | {p95_val} |
| P99 延迟 | {agg_p99} |
| 实际 RPS | {agg_rps_fmt} |
| 总请求数 | {aggregated.get("Request Count", "N/A") if aggregated else "N/A"} |
| 失败请求数 | {aggregated.get("Failure Count", "N/A") if aggregated else "N/A"} |

---

## 各端点性能明细

| 端点 | 请求数 | P50 | P95 | P99 | RPS | 错误率 |
|------|--------|-----|-----|-----|-----|--------|
{endpoint_table}

---

## 瓶颈分析

### 路由引擎

- **Miner 选择算法**: 使用 Redis `ZSCORE` + `SMEMBERS` 实现加权随机选择，每次请求约 2-3 次 Redis 操作
- **连接池**: PostgreSQL asyncpg + SQLAlchemy async，默认连接池 5-10
- **Redis 限流器**: 基于 Token Bucket，在高并发下对同一 API Key 的请求进行限速

### 已识别瓶颈

1. **路由选择串行 Redis 查询**: `select_miner()` 对每个候选矿工逐个查询 `ZSCORE`，
   当矿工数量 > 100 时会导致延迟线性增长。建议使用 `ZRANGE WITHSCORES` 批量获取。

2. **数据库连接池**: 高并发下 `check_and_deduct_balance()` 会争用 DB 连接。
   建议调整 `pool_size=20, max_overflow=10`。

3. **API Key 认证**: `authenticate_by_api_key()` 每次请求执行全表 hash 匹配。
   建议添加 Redis 缓存层（TTL=60s）以降低 DB 压力。

---

## 优化建议

### 高优先级（直接提升 P95）

```python
# routing_service.py — 批量获取矿工分数替代逐个查询
# 当前: 每个矿工单独 ZSCORE O(N)
# 优化: 使用 pipeline 或 ZRANGE WITHSCORES O(log N)
async def select_miner_optimized(redis: Redis, model: str) -> MinerCandidate:
    pipeline = redis.pipeline()
    # 批量查询，减少 RTT
    ...
```

### 中优先级

- 将 `authenticate_by_api_key()` 结果缓存到 Redis（TTL=60s）
- 调整 DB 连接池: `pool_size=20, max_overflow=10`
- 启用 `asyncpg` 预处理语句缓存

### 低优先级

- 矿工列表端点添加 Redis 缓存（TTL=30s）
- Usage 聚合查询添加数据库索引（`user_id + created_at`）

---

## 测试环境

- **后端**: FastAPI + Uvicorn (1 worker, Docker)
- **数据库**: PostgreSQL 15 (Docker)
- **缓存**: Redis 7 (Docker)
- **Mock Anthropic**: 本地 FastAPI server，延迟 10ms
- **负载生成**: Locust (gevent)

---

## 原始数据

CSV 文件: `{csv_prefix}_stats.csv`
HTML 报告: `{csv_prefix}.html`

> 注: 本报告基于 Mock 模式，真实 Testnet 性能需在 Bittensor 矿工接入后另行测试。
"""
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="生成负载测试 Markdown 报告")
    parser.add_argument("--csv-prefix", required=True, help="Locust CSV 文件前缀路径")
    parser.add_argument("--target-qps", type=int, default=500, help="目标 QPS")
    parser.add_argument("--output", required=True, help="输出 Markdown 文件路径")
    args = parser.parse_args()

    stats = load_stats(args.csv_prefix)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = generate_markdown(
        stats=stats,
        csv_prefix=args.csv_prefix,
        target_qps=args.target_qps,
        timestamp=timestamp,
    )

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"报告已生成: {args.output}")


if __name__ == "__main__":
    main()
