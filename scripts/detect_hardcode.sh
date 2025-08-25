#!/bin/bash
# ハードコードされた値を検出するスクリプト
# 
# 使用方法: ./scripts/detect_hardcode.sh
# 
# このスクリプトは、ソースコードとテストコード内の
# ハードコードされた定数を検出します。

set -e

echo "🔍 QuantForge ハードコード検出スクリプト"
echo "========================================="
echo ""

# カラー出力の設定
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 検出結果のカウンタ
TOTAL_ISSUES=0

# 一時ファイル
TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

# 1. 浮動小数点数の検出（0.0, 1.0, 2.0, 0.5, -1.0以外）
echo "📊 浮動小数点数の検出..."
echo "------------------------"

rg '\b\d*\.\d+\b' src/ tests/ \
  --type rust --type python \
  2>/dev/null | \
  grep -v "const\|TOLERANCE\|EPSILON\|Final" | \
  grep -vE '\b(0\.0|1\.0|2\.0|0\.5|-1\.0)\b' | \
  grep -v "//\|#" > $TEMP_FILE || true

if [ -s $TEMP_FILE ]; then
    echo -e "${YELLOW}⚠️  ハードコードされた浮動小数点数:${NC}"
    cat $TEMP_FILE | head -20
    COUNT=$(wc -l < $TEMP_FILE)
    TOTAL_ISSUES=$((TOTAL_ISSUES + COUNT))
    if [ $COUNT -gt 20 ]; then
        echo "  ... 他 $((COUNT - 20)) 件"
    fi
else
    echo -e "${GREEN}✅ 問題なし${NC}"
fi
echo ""

# 2. 科学記法の検出
echo "🔬 科学記法の検出..."
echo "--------------------"

rg '\d+e[+-]\d+' src/ tests/ \
  --type rust --type python \
  2>/dev/null | \
  grep -v "const\|TOLERANCE\|EPSILON\|Final" | \
  grep -v "//\|#" > $TEMP_FILE || true

if [ -s $TEMP_FILE ]; then
    echo -e "${YELLOW}⚠️  ハードコードされた科学記法:${NC}"
    cat $TEMP_FILE | head -20
    COUNT=$(wc -l < $TEMP_FILE)
    TOTAL_ISSUES=$((TOTAL_ISSUES + COUNT))
    if [ $COUNT -gt 20 ]; then
        echo "  ... 他 $((COUNT - 20)) 件"
    fi
else
    echo -e "${GREEN}✅ 問題なし${NC}"
fi
echo ""

# 3. 大きな整数の検出（100以上）
echo "🔢 大きな整数の検出（100以上）..."
echo "---------------------------------"

rg '\b[1-9]\d{2,}\b' src/ tests/ \
  --type rust --type python \
  2>/dev/null | \
  grep -v "const\|MAX\|MIN\|LIMIT" | \
  grep -v "//\|#" | \
  grep -v "benchmark\|example" > $TEMP_FILE || true

if [ -s $TEMP_FILE ]; then
    echo -e "${YELLOW}⚠️  ハードコードされた大きな整数:${NC}"
    cat $TEMP_FILE | head -20
    COUNT=$(wc -l < $TEMP_FILE)
    TOTAL_ISSUES=$((TOTAL_ISSUES + COUNT))
    if [ $COUNT -gt 20 ]; then
        echo "  ... 他 $((COUNT - 20)) 件"
    fi
else
    echo -e "${GREEN}✅ 問題なし${NC}"
fi
echo ""

# 4. 特定のマジックナンバーの検出
echo "🎯 特定のマジックナンバーの検出..."
echo "----------------------------------"

# よく問題になる値のリスト
MAGIC_NUMBERS=(
    "8\.0"      # norm_cdfの境界値
    "0\.001"    # 最小時間
    "100\.0"    # 最大時間
    "0\.005"    # 最小ボラティリティ
    "10\.0"     # 最大ボラティリティ
    "1000"      # 反復回数
)

FOUND_MAGIC=false
for number in "${MAGIC_NUMBERS[@]}"; do
    rg "\b${number}\b" src/ tests/ \
      --type rust --type python \
      2>/dev/null | \
      grep -v "const\|TOLERANCE\|EPSILON" | \
      grep -v "//\|#" > $TEMP_FILE || true
    
    if [ -s $TEMP_FILE ]; then
        if [ "$FOUND_MAGIC" = false ]; then
            echo -e "${YELLOW}⚠️  マジックナンバー検出:${NC}"
            FOUND_MAGIC=true
        fi
        echo "  値 $number:"
        cat $TEMP_FILE | head -5 | sed 's/^/    /'
        COUNT=$(wc -l < $TEMP_FILE)
        TOTAL_ISSUES=$((TOTAL_ISSUES + COUNT))
    fi
done

if [ "$FOUND_MAGIC" = false ]; then
    echo -e "${GREEN}✅ 問題なし${NC}"
fi
echo ""

# 5. 結果サマリー
echo "========================================="
echo "📋 検出結果サマリー"
echo "========================================="

if [ $TOTAL_ISSUES -eq 0 ]; then
    echo -e "${GREEN}✨ 素晴らしい！ハードコードされた値は見つかりませんでした。${NC}"
    echo "技術的負債ゼロの原則が守られています。"
    exit 0
else
    echo -e "${RED}⚠️  警告: ${TOTAL_ISSUES} 件のハードコードされた値が見つかりました。${NC}"
    echo ""
    echo "推奨される対応:"
    echo "1. 精度値 → src/constants.rs または tests/conftest.py に定義"
    echo "2. 数学定数 → 使用箇所の近くで const 定義"
    echo "3. 制限値 → src/validation.rs の InputLimits に追加"
    echo "4. テスト値 → tests/conftest.py に標準値として定義"
    echo ""
    echo "詳細は CLAUDE.md の「🔒 設定値管理の鉄則」セクションを参照してください。"
    exit 1
fi