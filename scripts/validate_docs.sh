#!/bin/bash
# docs/scripts/validate_docs.sh

echo "=========================================="
echo "ドキュメント検証スクリプト"
echo "=========================================="

echo ""
echo "1. 主観的表現のチェック..."
echo "-------------------------------------------"
violations=$(grep -r "超高速\|次世代\|画期的\|革新的\|圧倒的\|最先端\|驚異的\|劇的\|飛躍的\|究極の\|完璧な" docs/ --include="*.md" --exclude-dir=internal 2>/dev/null | wc -l)
if [ $violations -eq 0 ]; then
    echo "✅ 主観的表現なし"
else
    echo "⚠️ 主観的表現を検出: $violations 件"
    grep -r "超高速\|次世代\|画期的\|革新的\|圧倒的\|最先端\|驚異的\|劇的\|飛躍的\|究極の\|完璧な" docs/ --include="*.md" --exclude-dir=internal 2>/dev/null | head -5
fi

echo ""
echo "2. バージョン番号のチェック..."
echo "-------------------------------------------"
versions=$(grep -r "v[0-9]\+\.[0-9]\+\.[0-9]\+" docs/ --include="*.md" --exclude-dir=internal 2>/dev/null | wc -l)
if [ $versions -eq 0 ]; then
    echo "✅ バージョン番号なし"
else
    echo "⚠️ バージョン番号を検出: $versions 件"
    grep -r "v[0-9]\+\.[0-9]\+\.[0-9]\+" docs/ --include="*.md" --exclude-dir=internal 2>/dev/null | head -5
fi

echo ""
echo "3. 警告の太字表記チェック..."
echo "-------------------------------------------"
bold_warnings=$(grep -r "^\*\*警告\*\*\|^\*\*注意\*\*" docs/ --include="*.md" 2>/dev/null | wc -l)
if [ $bold_warnings -eq 0 ]; then
    echo "✅ 太字警告なし（MyST Admonitions使用）"
else
    echo "⚠️ 太字警告を検出: $bold_warnings 件"
    grep -r "^\*\*警告\*\*\|^\*\*注意\*\*" docs/ --include="*.md" 2>/dev/null | head -5
fi

echo ""
echo "4. MyST Admonitionsの使用状況..."
echo "-------------------------------------------"
admonitions=$(grep -r ":::{note}\|:::{warning}\|:::{tip}\|:::{important}\|:::{danger}" docs/ --include="*.md" 2>/dev/null | wc -l)
echo "ℹ️ MyST Admonitions使用数: $admonitions 件"

echo ""
echo "5. 測定条件の記載チェック..."
echo "-------------------------------------------"
# パフォーマンス記述で測定条件が明記されているか
perf_with_conditions=$(grep -B2 -A2 "倍高速\|倍の処理速度\|ms\|μs\|ns" docs/ --include="*.md" 2>/dev/null | grep -c "測定\|Intel\|AMD\|環境" 2>/dev/null)
echo "ℹ️ 測定条件付きパフォーマンス記述: $perf_with_conditions 件"

echo ""
echo "=========================================="
echo "検証完了"
echo "=========================================="