#!/usr/bin/env python3
"""残存エラーの詳細分析。"""

import sys
from pathlib import Path
from collections import Counter
sys.path.insert(0, str(Path(__file__).parent))

from code_extractor import DocCodeExtractor
from check_doc_codes import SimpleCodeExecutor


def main():
    """エラーを分析。"""
    # 初期化
    extractor = DocCodeExtractor()
    executor = SimpleCodeExecutor()
    doc_dir = Path(__file__).parent.parent.parent / 'docs'

    # エラーを収集
    error_types = Counter()
    file_errors = Counter()
    specific_errors = []

    blocks = extractor.extract_from_directory(doc_dir)

    for block in blocks:
        if not block.skip:
            success, _, error = executor.execute(block.code)
            if not success:
                # エラーの種類を分類
                if 'is not defined' in error:
                    error_types['未定義変数'] += 1
                    if len(specific_errors) < 5:
                        specific_errors.append(('未定義変数', block, error))
                elif 'invalid syntax' in error or 'expected' in error:
                    error_types['構文エラー'] += 1
                    if len(specific_errors) < 10:
                        specific_errors.append(('構文エラー', block, error))
                elif 'No module named' in error:
                    error_types['モジュール不在'] += 1
                elif 'got an unexpected keyword' in error:
                    error_types['パラメータエラー'] += 1
                elif 'has no attribute' in error:
                    error_types['属性エラー'] += 1
                else:
                    error_types['その他'] += 1

                # ファイル別集計
                rel_path = Path(block.filename).relative_to(doc_dir)
                file_key = str(rel_path.parts[0]) if len(rel_path.parts) > 0 else 'root'
                file_errors[file_key] += 1

    # 結果表示
    print("=" * 60)
    print("残存エラーの詳細分析")
    print("=" * 60)

    print("\n## エラータイプ別分布\n")
    total_errors = sum(error_types.values())
    for error_type, count in error_types.most_common():
        percentage = count / total_errors * 100
        print(f"  {error_type:15} : {count:3} ({percentage:5.1f}%)")
    print(f"  {'合計':15} : {total_errors:3}")

    print("\n## ディレクトリ別エラー数\n")
    for dir_name, count in file_errors.most_common(10):
        print(f"  {dir_name:20} : {count:3}")

    print("\n## 具体的なエラー例\n")
    for i, (error_type, block, error) in enumerate(specific_errors[:5], 1):
        rel_path = Path(block.filename).relative_to(doc_dir)
        print(f"{i}. {error_type} - {rel_path}:{block.line_number}")
        print(f"   エラー: {error[:100]}")
        print(f"   コード: {block.code[:100]}...")
        print()

    print("\n## 推奨される次のステップ\n")
    print("1. 構文エラーの手動修正（bashコマンドの適切な分類）")
    print("2. 未定義変数の解決（import文の追加、前提コードの統合）")
    print("3. コードブロックの独立性確保（各ブロックで完結するよう修正）")
    print("4. CI/CDパイプラインへの統合（自動テストの定期実行）")


if __name__ == "__main__":
    main()