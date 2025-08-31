#!/bin/bash
# ベンチマーク移行スクリプト
# Purpose: 既存のbenchmarksディレクトリから新しい層別ベンチマーク構造への安全な移行

set -e  # エラー時に停止

echo "=== ベンチマーク移行開始 ==="
echo "開始時刻: $(date '+%Y-%m-%d %H:%M:%S')"

# Phase 1: 新構造の作成
echo ""
echo "📁 Creating new benchmark structure..."
mkdir -p bindings/python/tests/benchmarks
mkdir -p benchmark_results/{core,bindings/python,integration}/history
echo "✅ Directory structure created"

# Phase 2: ベンチマークコードの配置
echo ""
echo "📝 Setting up benchmark code..."
# 新しいベンチマークファイルの存在確認
if [ ! -f "bindings/python/tests/benchmarks/__init__.py" ]; then
    touch bindings/python/tests/benchmarks/__init__.py
    echo "✅ Created __init__.py for benchmarks"
fi

# Phase 3: 初回実行（Core層のみ）
echo ""
echo "🚀 Running benchmarks in new structure..."
if command -v cargo &> /dev/null; then
    echo "Running Core layer benchmarks..."
    cargo bench --package quantforge-core 2>&1 | tail -n 20 || true
    echo "✅ Core benchmarks executed"
else
    echo "⚠️  Cargo not found, skipping Core benchmarks"
fi

# Phase 4: 検証
echo ""
echo "✅ Verifying new structure..."
if [ -d "benchmark_results" ]; then
    echo "New benchmark_results directory structure:"
    tree benchmark_results/ 2>/dev/null || ls -la benchmark_results/
fi

# Phase 5: 既存データの確認
echo ""
echo "📊 Checking existing benchmark data..."
if [ -d "benchmarks/results" ]; then
    echo "Found existing benchmark results:"
    ls -la benchmarks/results/ | head -n 10
    
    # resultsディレクトリのサイズ確認
    RESULTS_SIZE=$(du -sh benchmarks/results/ | cut -f1)
    echo "Total size of existing results: $RESULTS_SIZE"
else
    echo "No existing benchmark results found"
fi

echo ""
echo "=== 移行準備完了 ==="
echo "完了時刻: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "次のステップ:"
echo "1. 新形式でベンチマークを実行"
echo "2. 結果を検証"
echo "3. scripts/archive_benchmarks.sh で過去データを退避"
echo "4. benchmarks/ を削除"