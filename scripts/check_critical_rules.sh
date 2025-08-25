#!/bin/bash
# critical-rules.xml の遵守状況を検証するスクリプト
# 
# 使用方法: ./scripts/check_critical_rules.sh
# 
# このスクリプトは、.claude/critical-rules.xml で定義された
# ルールの遵守状況を検証します。

set -e

# カラー出力の設定
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 結果カウンタ
TOTAL_VIOLATIONS=0
PASSED_RULES=0
FAILED_RULES=0

echo "======================================================"
echo "🔍 Critical Rules Compliance Check for QuantForge"
echo "======================================================"
echo ""
echo "Checking compliance with .claude/critical-rules.xml..."
echo ""

# 一時ファイル
TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

# ========================================
# C002: エラー迂回絶対禁止
# ========================================
echo -e "${BLUE}[C002]${NC} エラー迂回絶対禁止・主観判断排除"
echo "--------------------------------------"

# "問題ない" "軽微" "たぶん" などの主観的表現をチェック
rg '(問題ない|軽微|たぶん|おそらく|多分|はず|だろう)' \
   --type rust --type python \
   src/ tests/ 2>/dev/null | \
   grep -v "comment\|doc\|#\|//" > $TEMP_FILE || true

if [ -s $TEMP_FILE ]; then
    echo -e "${RED}❌ 違反: 主観的判断の表現が見つかりました${NC}"
    head -5 $TEMP_FILE | sed 's/^/  /'
    TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + $(wc -l < $TEMP_FILE)))
    FAILED_RULES=$((FAILED_RULES + 1))
else
    echo -e "${GREEN}✅ 合格: 主観的判断の排除を確認${NC}"
    PASSED_RULES=$((PASSED_RULES + 1))
fi
echo ""

# ========================================
# C004 & C014: 理想実装ファースト・妥協実装禁止
# ========================================
echo -e "${BLUE}[C004/C014]${NC} 理想実装ファースト・妥協実装絶対禁止"
echo "--------------------------------------"

# TODO, FIXME, HACK, XXX などのコメントをチェック
rg '(TODO|FIXME|HACK|XXX|後で|あとで|暫定|仮|temporary|temp)' \
   --type rust --type python \
   src/ tests/ 2>/dev/null | \
   grep -v ".git" > $TEMP_FILE || true

if [ -s $TEMP_FILE ]; then
    echo -e "${YELLOW}⚠️  警告: 技術的負債を示唆するコメントが見つかりました${NC}"
    head -5 $TEMP_FILE | sed 's/^/  /'
    TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + $(wc -l < $TEMP_FILE)))
    FAILED_RULES=$((FAILED_RULES + 1))
else
    echo -e "${GREEN}✅ 合格: 妥協実装なし${NC}"
    PASSED_RULES=$((PASSED_RULES + 1))
fi
echo ""

# ========================================
# C010: テスト駆動開発必須
# ========================================
echo -e "${BLUE}[C010]${NC} テスト駆動開発必須"
echo "--------------------------------------"

# テストファイルの存在確認
# Rustは#[cfg(test)]モジュール内のテストもカウント
RUST_SRC_COUNT=$(find src/ -name "*.rs" 2>/dev/null | wc -l)
RUST_TEST_MODULE_COUNT=$(grep -r "#\[cfg(test)\]" src/ 2>/dev/null | wc -l)
RUST_TEST_FILE_COUNT=$(find src/ tests/ -name "*test*.rs" -o -name "*_test.rs" 2>/dev/null | wc -l)
RUST_TEST_COUNT=$((RUST_TEST_MODULE_COUNT + RUST_TEST_FILE_COUNT))

PY_SRC_COUNT=$(find . -name "*.py" -not -path "*/test*" -not -path "./.venv/*" 2>/dev/null | wc -l)
PY_TEST_COUNT=$(find tests/ -name "test_*.py" -o -name "*_test.py" 2>/dev/null | wc -l)

if [ $RUST_TEST_COUNT -eq 0 ] && [ $RUST_SRC_COUNT -gt 0 ]; then
    echo -e "${RED}❌ 違反: Rustテストが存在しません${NC}"
    FAILED_RULES=$((FAILED_RULES + 1))
elif [ $PY_TEST_COUNT -eq 0 ] && [ $PY_SRC_COUNT -gt 0 ]; then
    echo -e "${RED}❌ 違反: Pythonテストが存在しません${NC}"
    FAILED_RULES=$((FAILED_RULES + 1))
else
    echo -e "${GREEN}✅ 合格: テストファイル確認 (Rust: $RUST_TEST_COUNT, Python: $PY_TEST_COUNT)${NC}"
    PASSED_RULES=$((PASSED_RULES + 1))
fi
echo ""

# ========================================
# C011-3: 設定値ハードコード禁止
# ========================================
echo -e "${BLUE}[C011-3]${NC} 設定値ハードコード禁止"
echo "--------------------------------------"

# detect_hardcode.sh が存在する場合は実行
if [ -f "./scripts/detect_hardcode.sh" ]; then
    echo "Running detect_hardcode.sh..."
    if ./scripts/detect_hardcode.sh > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 合格: ハードコードなし${NC}"
        PASSED_RULES=$((PASSED_RULES + 1))
    else
        echo -e "${RED}❌ 違反: ハードコードが検出されました${NC}"
        echo "  詳細は ./scripts/detect_hardcode.sh を実行してください"
        FAILED_RULES=$((FAILED_RULES + 1))
        TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + 1))
    fi
else
    echo -e "${YELLOW}⚠️  スキップ: detect_hardcode.sh が見つかりません${NC}"
fi
echo ""

# ========================================
# C012: DRY原則（コード重複禁止）
# ========================================
echo -e "${BLUE}[C012]${NC} DRY原則絶対遵守"
echo "--------------------------------------"

# 同じ関数名やクラス名の重複をチェック
echo "Checking for duplicate function/class definitions..."

# Rust関数の重複チェック
rg '^(pub )?fn \w+' --type rust src/ 2>/dev/null | \
    sed 's/.*fn \(\w\+\).*/\1/' | \
    sort | uniq -d > $TEMP_FILE || true

if [ -s $TEMP_FILE ]; then
    echo -e "${YELLOW}⚠️  警告: 重複した関数名が見つかりました（Rust）${NC}"
    cat $TEMP_FILE | sed 's/^/  /'
    TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + $(wc -l < $TEMP_FILE)))
fi

# Pythonクラス/関数の重複チェック
rg '^(class |def )\w+' --type python . 2>/dev/null | \
    grep -v ".venv" | \
    sed 's/.*\(class\|def\) \(\w\+\).*/\2/' | \
    sort | uniq -d > $TEMP_FILE || true

if [ -s $TEMP_FILE ]; then
    echo -e "${YELLOW}⚠️  警告: 重複した関数/クラス名が見つかりました（Python）${NC}"
    cat $TEMP_FILE | sed 's/^/  /'
    TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + $(wc -l < $TEMP_FILE)))
    FAILED_RULES=$((FAILED_RULES + 1))
else
    echo -e "${GREEN}✅ 合格: 明らかな重複なし${NC}"
    PASSED_RULES=$((PASSED_RULES + 1))
fi
echo ""

# ========================================
# C013: 破壊的リファクタリング推奨（V2クラス禁止）
# ========================================
echo -e "${BLUE}[C013]${NC} 破壊的リファクタリング推奨"
echo "--------------------------------------"

# V2, v2, V3などのバージョニングされたファイル/クラスをチェック
find . -type f \( -name "*V2*" -o -name "*_v2*" -o -name "*V3*" -o -name "*_v3*" \) \
    -not -path "./.git/*" -not -path "./.venv/*" > $TEMP_FILE 2>/dev/null || true

# クラス名でのV2チェック
rg 'class \w+V[0-9]' --type python . 2>/dev/null | grep -v ".venv" >> $TEMP_FILE || true
rg 'struct \w+V[0-9]' --type rust src/ 2>/dev/null >> $TEMP_FILE || true

if [ -s $TEMP_FILE ]; then
    echo -e "${RED}❌ 違反: V2/V3クラスが見つかりました${NC}"
    head -5 $TEMP_FILE | sed 's/^/  /'
    TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + $(wc -l < $TEMP_FILE)))
    FAILED_RULES=$((FAILED_RULES + 1))
else
    echo -e "${GREEN}✅ 合格: V2クラスなし${NC}"
    PASSED_RULES=$((PASSED_RULES + 1))
fi
echo ""

# ========================================
# 結果サマリー
# ========================================
echo "======================================================"
echo "📊 Compliance Report Summary"
echo "======================================================"
echo ""

TOTAL_RULES=$((PASSED_RULES + FAILED_RULES))

if [ $FAILED_RULES -eq 0 ]; then
    echo -e "${GREEN}✨ 完璧！すべてのCritical Rulesに準拠しています${NC}"
    echo ""
    echo "  チェック済みルール: $TOTAL_RULES"
    echo "  合格: $PASSED_RULES"
    echo "  違反: 0"
    echo ""
    echo "技術的負債ゼロの原則が守られています！"
    exit 0
else
    echo -e "${RED}⚠️  Critical Rules違反が検出されました${NC}"
    echo ""
    echo "  チェック済みルール: $TOTAL_RULES"
    echo -e "  ${GREEN}合格: $PASSED_RULES${NC}"
    echo -e "  ${RED}違反: $FAILED_RULES${NC}"
    echo "  総違反件数: $TOTAL_VIOLATIONS"
    echo ""
    echo "対応方法:"
    echo "1. 各違反を即座に修正してください（C002）"
    echo "2. 修正不可能な場合は作業を停止し、計画を見直してください"
    echo "3. 詳細は CLAUDE.md の「🤖 AI 動作制御ルール」を参照"
    echo ""
    echo "参照: .claude/critical-rules.xml"
    exit 1
fi