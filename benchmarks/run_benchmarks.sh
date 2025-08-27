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

# 結果をMarkdown形式で出力
echo ""
echo "📝 結果をMarkdown形式で保存中..."
uv run python format_results.py > "$PROJECT_ROOT/docs/performance/benchmarks_$(date +%Y%m%d).md"

echo ""
echo "✅ ベンチマーク完了"
echo "結果: docs/performance/benchmarks_$(date +%Y%m%d).md"