#!/usr/bin/env bash
# run_benchmark.sh — 一键启动 OpenClade 路由引擎负载测试
#
# 使用方法:
#   bash tests/benchmarks/run_benchmark.sh [500|1000]
#
# 参数:
#   500  — 验收测试（P95 < 500ms，0% 错误率）[默认]
#   1000 — 峰值压测（1000 QPS 极限）
#
# 前置条件:
#   - docker compose 已安装
#   - locust 已安装: pip install locust
#   - 从 backend/ 目录运行

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_ROOT="$(cd "$BACKEND_DIR/.." && pwd)"
DOCS_DIR="$PROJECT_ROOT/docs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TARGET_QPS="${1:-500}"

echo "=============================================="
echo " OpenClade 路由引擎负载测试"
echo " 目标: $TARGET_QPS QPS"
echo " 时间: $TIMESTAMP"
echo "=============================================="

# 1. 启动基础服务 + mock Anthropic server
echo "[1/5] 启动 Docker 环境..."
cd "$PROJECT_ROOT"

docker compose -f docker-compose.yml up -d --wait

# 启动 mock Anthropic server（独立 Docker 容器）
echo "[1/5] 启动 Mock Anthropic server (port 9999)..."
docker compose -f docker-compose.yml -f "$SCRIPT_DIR/docker-compose.benchmark.yml" up mock-anthropic -d

# 等待 mock server 就绪
echo "[1/5] 等待 mock server 就绪..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:9999/health > /dev/null 2>&1; then
        echo "      Mock server 就绪 ✓"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "      ERROR: Mock server 启动超时"
        exit 1
    fi
    sleep 1
done

# 2. 配置后端使用 mock Anthropic
echo "[2/5] 配置后端 ANTHROPIC_BASE_URL..."
# 动态获取 mock server 在 Docker 网络中的地址
MOCK_ANTHROPIC_URL="http://host.docker.internal:9999"
docker compose -f docker-compose.yml exec -T backend \
    sh -c "export ANTHROPIC_BASE_URL=http://host.docker.internal:9999; echo 'ANTHROPIC_BASE_URL configured'" || \
    echo "      NOTE: 若在容器外运行，请手动设置 ANTHROPIC_BASE_URL=http://localhost:9999"

# 3. 验证后端就绪
echo "[3/5] 验证后端就绪..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "      后端就绪 ✓"
        break
    fi
    sleep 1
done

# 4. 运行 locust
echo "[4/5] 运行 Locust 压测..."
mkdir -p "$DOCS_DIR"

cd "$BACKEND_DIR"

if [ "$TARGET_QPS" -eq 1000 ]; then
    USERS=500
    SPAWN_RATE=100
    DURATION="120s"
    LABEL="1000qps"
else
    USERS=200
    SPAWN_RATE=50
    DURATION="60s"
    LABEL="500qps"
fi

CSV_PREFIX="$DOCS_DIR/benchmark_${LABEL}_${TIMESTAMP}"

ANTHROPIC_BASE_URL="http://localhost:9999" \
locust \
    -f tests/benchmarks/locustfile.py \
    --host=http://localhost:8000 \
    --headless \
    -u "$USERS" \
    -r "$SPAWN_RATE" \
    --run-time "$DURATION" \
    --csv="$CSV_PREFIX" \
    --html="$CSV_PREFIX.html" \
    --only-summary \
    2>&1 | tee "$CSV_PREFIX.log"

echo "[4/5] 压测完成 ✓"

# 5. 生成报告
echo "[5/5] 生成 Markdown 报告..."
python3 "$SCRIPT_DIR/generate_report.py" \
    --csv-prefix "$CSV_PREFIX" \
    --target-qps "$TARGET_QPS" \
    --output "$DOCS_DIR/load_test_report_${LABEL}_${TIMESTAMP}.md" \
    || echo "      (generate_report.py 不可用，CSV 结果在 $CSV_PREFIX_*.csv)"

echo ""
echo "=============================================="
echo " 结果文件:"
echo "   HTML 报告: $CSV_PREFIX.html"
echo "   CSV 汇总:  ${CSV_PREFIX}_stats.csv"
echo "   日志:      $CSV_PREFIX.log"
echo "=============================================="
