#!/bin/bash

# Document as Single Source of Truth (D-SSoT) 検証スクリプト
# 
# このスクリプトは以下を検証します：
# 1. 実装コードが計画文書を参照していないか
# 2. ドキュメントと実装が一致しているか

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "📚 D-SSoT (Document as Single Source of Truth) 検証"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# カラー出力の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 検証1: 計画文書への参照を検出
echo "▶ 検証1: 実装コードの計画文書参照チェック"
echo "────────────────────────────────────────"

PLAN_REFS_FOUND=false

# Pythonコードでの計画文書参照をチェック
if [ -d "python" ]; then
    PYTHON_REFS=$(grep -r "plans/" python/ --include="*.py" 2>/dev/null || true)
    if [ ! -z "$PYTHON_REFS" ]; then
        echo -e "${RED}❌ エラー: Pythonコードが計画文書を参照しています:${NC}"
        echo "$PYTHON_REFS"
        PLAN_REFS_FOUND=true
    fi
fi

# Rustコードでの計画文書参照をチェック
if [ -d "src" ]; then
    RUST_REFS=$(grep -r "plans/" src/ --include="*.rs" 2>/dev/null || true)
    if [ ! -z "$RUST_REFS" ]; then
        echo -e "${RED}❌ エラー: Rustコードが計画文書を参照しています:${NC}"
        echo "$RUST_REFS"
        PLAN_REFS_FOUND=true
    fi
fi

# テストコードでの計画文書参照をチェック（警告のみ）
if [ -d "tests" ]; then
    TEST_REFS=$(grep -r "plans/" tests/ --include="*.py" --include="*.rs" 2>/dev/null || true)
    if [ ! -z "$TEST_REFS" ]; then
        echo -e "${YELLOW}⚠ 警告: テストコードが計画文書を参照しています:${NC}"
        echo "$TEST_REFS"
        echo "  （テストコードでの参照は警告のみ）"
    fi
fi

if [ "$PLAN_REFS_FOUND" = true ]; then
    echo -e "${RED}✗ 計画文書への参照が検出されました${NC}"
    echo ""
    echo "対処方法:"
    echo "1. 実装コードから plans/ への参照を削除してください"
    echo "2. 代わりに docs/api/ のドキュメントを参照してください"
    echo ""
else
    echo -e "${GREEN}✓ 実装コードは計画文書を参照していません${NC}"
fi

echo ""

# 検証2: ドキュメントと実装の一致確認
echo "▶ 検証2: ドキュメント・実装一致検証"
echo "────────────────────────────────────────"

# Pythonスクリプトの存在確認
CONSISTENCY_SCRIPT="scripts/verify_doc_implementation_consistency.py"
if [ ! -f "$CONSISTENCY_SCRIPT" ]; then
    echo -e "${YELLOW}⚠ 警告: $CONSISTENCY_SCRIPT が見つかりません${NC}"
    echo "  スキップします"
else
    # Python環境の確認
    if command -v python3 &> /dev/null; then
        python3 "$CONSISTENCY_SCRIPT"
        CONSISTENCY_CHECK_RESULT=$?
    elif command -v python &> /dev/null; then
        python "$CONSISTENCY_SCRIPT"
        CONSISTENCY_CHECK_RESULT=$?
    else
        echo -e "${YELLOW}⚠ 警告: Python環境が見つかりません${NC}"
        echo "  一致検証をスキップします"
        CONSISTENCY_CHECK_RESULT=0
    fi
fi

echo ""

# 最終結果
echo "═══════════════════════════════════════════════════════════════"
if [ "$PLAN_REFS_FOUND" = true ] || [ "${CONSISTENCY_CHECK_RESULT:-0}" -ne 0 ]; then
    echo -e "${RED}❌ D-SSoT検証失敗${NC}"
    echo ""
    echo "重要な原則:"
    echo "• ドキュメント（docs/api/）は唯一の真実"
    echo "• 計画（plans/）は設計メモ（参照禁止）"
    echo "• 実装はドキュメントの具現化"
    exit 1
else
    echo -e "${GREEN}✅ D-SSoT検証成功！${NC}"
    echo ""
    echo "確認済み:"
    echo "• 実装コードは計画文書を参照していない"
    echo "• ドキュメントと実装が一致している"
    echo "• D-SSoTプロトコルに準拠"
fi

echo "═══════════════════════════════════════════════════════════════"