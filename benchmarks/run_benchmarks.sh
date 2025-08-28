#!/bin/bash
set -e

echo "🚀 QuantForge Black-Scholesベンチマーク実行"
echo "==========================================="
date

# スクリプトのディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Rustベンチマーク実行（プロジェクトルートから）
echo ""
echo "📊 Rustネイティブベンチマーク"
echo "------------------------------"
cd "$PROJECT_ROOT"
cargo bench --bench benchmark -- black_scholes 2>&1 | grep -E "time:|throughput:" || true

# Python比較ベンチマーク（benchmarksディレクトリから）
echo ""
echo "📊 Python比較ベンチマーク"
echo "------------------------"
cd "$SCRIPT_DIR"
uv run python run_comparison.py

# 結果をMarkdown形式で出力（resultsディレクトリに保存）
echo ""
echo "📝 結果をMarkdown形式で保存中..."
RESULTS_DIR="$SCRIPT_DIR/results"
mkdir -p "$RESULTS_DIR"
uv run python format_results.py > "$RESULTS_DIR/benchmark_$(date +%Y%m%d_%H%M%S).md"

echo ""
echo "✅ ベンチマーク完了"
echo "結果: benchmarks/results/benchmark_$(date +%Y%m%d_%H%M%S).md"