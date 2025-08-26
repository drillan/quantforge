#!/usr/bin/env python
"""
ドキュメントと実装の一致を検証（計画文書は無視）

D-SSoT (Document as Single Source of Truth) プロトコルに基づき、
docs/api/ のドキュメントと実装コードの完全一致を確認します。
計画文書（plans/）は意図的に無視します。
"""

import ast
import re
import sys
from pathlib import Path


def extract_apis_from_docs() -> dict[str, str]:
    """ドキュメントから現在有効なAPI仕様を抽出"""
    apis: dict[str, str] = {}
    docs_dir = Path("docs/api")

    if not docs_dir.exists():
        print(f"警告: {docs_dir} が存在しません")
        return apis

    for doc in docs_dir.rglob("*.md"):
        content = doc.read_text()

        # 関数定義パターン（`function_name(` の形式）
        pattern = r"`(\w+)\("
        for match in re.finditer(pattern, content):
            func_name = match.group(1)
            # calculate などの汎用的な名前は除外
            if func_name not in ["calculate", "benchmark"]:
                apis[func_name] = str(doc)

    return apis


def extract_apis_from_implementation() -> dict[str, str]:
    """実装からAPI名を抽出"""
    apis: dict[str, str] = {}

    # Python実装（__init__.py）
    init_file = Path("python/quantforge/__init__.py")
    if init_file.exists():
        content = init_file.read_text()

        # __all__ リストから公開APIを抽出
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if hasattr(target, "id") and target.id == "__all__" and isinstance(node.value, ast.List):
                            for item in node.value.elts:
                                if (
                                    isinstance(item, ast.Constant)
                                    and isinstance(item.value, str)
                                    and item.value not in ["models"]
                                ):
                                    apis[item.value] = str(init_file)
        except SyntaxError as e:
            print(f"警告: {init_file} の解析エラー: {e}")

    return apis


def main() -> int:
    """メイン検証処理"""
    print("📚 Document-Implementation Consistency Check (D-SSoT)")
    print("=" * 60)
    print("計画文書（plans/）は意図的に無視しています")
    print("ドキュメント（docs/api/）を唯一の真実の源として検証します\n")

    # API抽出
    documented = extract_apis_from_docs()
    implemented = extract_apis_from_implementation()

    print(f"ドキュメント定義API数: {len(documented)}")
    print(f"実装済みAPI数: {len(implemented)}")
    print()

    errors = []

    # ドキュメントにあって実装にない（契約違反）
    missing_impl = set(documented.keys()) - set(implemented.keys())
    for api in sorted(missing_impl):
        errors.append(f"❌ ドキュメント定義済みだが未実装: {api} ({documented[api]})")

    # 実装にあってドキュメントにない（不正な実装）
    undocumented = set(implemented.keys()) - set(documented.keys())
    for api in sorted(undocumented):
        errors.append(f"❌ ドキュメント化されていない実装: {api} ({implemented[api]})")

    # 結果出力
    if errors:
        print("❌ ドキュメント・実装不一致を検出:")
        print("-" * 60)
        for error in errors:
            print(f"  {error}")
        print()
        print(f"合計 {len(errors)} 件の不一致があります")
        print("\n対処方法:")
        print("1. ドキュメント未実装: docs/api/ の仕様通りに実装してください")
        print("2. ドキュメント化されていない実装: docs/api/ にドキュメントを追加してください")
        sys.exit(1)
    else:
        print("✅ ドキュメントと実装が完全一致しています！")
        print()
        print(f"検証済みAPI数: {len(documented)}")
        print("D-SSoTプロトコル準拠が確認されました")

    return 0


if __name__ == "__main__":
    sys.exit(main())
