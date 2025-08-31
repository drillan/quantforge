#!/bin/bash
# ベンチマーク結果のアーカイブスクリプト
# Purpose: 過去のベンチマーク結果を安全にアーカイブ

set -e  # エラー時に停止

ARCHIVE_DATE=$(date +%Y%m%d)
ARCHIVE_DIR="archive/benchmarks-legacy-${ARCHIVE_DATE}"

echo "=== ベンチマーク結果のアーカイブ開始 ==="
echo "アーカイブ先: ${ARCHIVE_DIR}"

# アーカイブディレクトリの作成
if [ -d "${ARCHIVE_DIR}" ]; then
    echo "❌ アーカイブディレクトリが既に存在します: ${ARCHIVE_DIR}"
    echo "別の日付またはディレクトリ名を使用してください"
    exit 1
fi

# 新形式のデータ存在確認
if [ ! -d "benchmark_results" ]; then
    echo "❌ 新形式のbenchmark_resultsディレクトリが見つかりません"
    echo "先に新形式でベンチマークを実行してください"
    exit 1
fi

# 新形式データの検証
NEW_DATA_EXISTS=false
for layer in core bindings/python integration; do
    if [ -f "benchmark_results/${layer}/latest.json" ]; then
        echo "✅ 新形式データ確認: benchmark_results/${layer}/latest.json"
        NEW_DATA_EXISTS=true
    fi
done

if [ "$NEW_DATA_EXISTS" = false ]; then
    echo "⚠️  警告: 新形式のデータがまだ記録されていません"
    echo "続行しますか？ (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "アーカイブを中止しました"
        exit 0
    fi
fi

# 既存データのアーカイブ
BENCHMARKS_DIR="/home/driller/repo/quantforge/benchmarks/results"
if [ -d "$BENCHMARKS_DIR" ]; then
    echo ""
    echo "📦 アーカイブ実行中..."
    mkdir -p "${ARCHIVE_DIR}"
    
    # resultsディレクトリのコピー
    cp -r "$BENCHMARKS_DIR" "${ARCHIVE_DIR}/"
    echo "✅ $BENCHMARKS_DIR をアーカイブしました"
    
    # 分析レポートもアーカイブ
    if ls "$BENCHMARKS_DIR"/*.md 2>/dev/null; then
        cp "$BENCHMARKS_DIR"/*.md "${ARCHIVE_DIR}/" 2>/dev/null || true
        echo "✅ 分析レポートをアーカイブしました"
    fi
    
    # アーカイブのメタデータ作成
    cat > "${ARCHIVE_DIR}/ARCHIVE_INFO.md" << EOF
# ベンチマークアーカイブ情報

## アーカイブ日時
$(date '+%Y-%m-%d %H:%M:%S')

## アーカイブ理由
Core + Bindings アーキテクチャへの移行に伴う、旧ベンチマーク構造の退避

## 含まれるデータ
- results/: ベンチマーク結果のJSON形式データ
- *.md: 分析レポート

## 元のパス
benchmarks/results/

## 新形式のデータ場所
benchmark_results/{core,bindings/python,integration}/

## 注意事項
このデータは参照用のアーカイブです。新形式への変換は行われていません。
EOF
    
    echo "✅ アーカイブ情報を記録しました: ${ARCHIVE_DIR}/ARCHIVE_INFO.md"
    
    # アーカイブサイズの確認
    ARCHIVE_SIZE=$(du -sh "${ARCHIVE_DIR}" | cut -f1)
    echo ""
    echo "📊 アーカイブ完了"
    echo "  場所: ${ARCHIVE_DIR}"
    echo "  サイズ: ${ARCHIVE_SIZE}"
    
else
    echo "ℹ️  $BENCHMARKS_DIR が見つかりません（アーカイブ不要）"
fi

echo ""
echo "=== アーカイブ完了 ==="
echo ""
echo "次のステップ:"
echo "1. アーカイブ内容を確認: ls -la ${ARCHIVE_DIR}/"
echo "2. 問題なければ旧構造を削除: rm -rf benchmarks/"