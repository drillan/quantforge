#!/usr/bin/env python3
"""ドキュメントコードブロックの統計と問題をチェック。"""

import sys
from collections import defaultdict
from pathlib import Path

from tests.doc_tests.code_extractor import DocCodeExtractor


class SimpleCodeExecutor:
    """シンプルなコード実行環境。"""

    def __init__(self):
        """環境を初期化。"""
        import numpy as np
        import pyarrow as pa
        import quantforge
        from quantforge.models import american, black76, black_scholes, merton

        # 基本環境
        self.globals = {
            "quantforge": quantforge,
            "black_scholes": black_scholes,
            "black76": black76,
            "merton": merton,
            "american": american,
            "np": np,
            "numpy": np,
            "pa": pa,
            "pyarrow": pa,
            "time": __import__("time"),
            "math": __import__("math"),
            # モック関数
            "get_market_price": lambda strike: 10.0 * (1.0 - abs(100.0 - strike) / 100.0 * 0.5),
        }
        self.locals = {}

    def execute(self, code):
        """コードを実行。"""
        import io
        import sys

        old_stdout = sys.stdout
        old_stderr = sys.stderr

        try:
            # 標準出力を抑制
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()

            exec(compile(code, "<test>", "exec"), self.globals, self.locals)
            self.globals.update(self.locals)
            return True, "", ""
        except Exception as e:
            return False, "", str(e)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


def main():
    """メイン処理。"""
    # ドキュメントディレクトリ
    project_root = Path(__file__).parent.parent.parent
    doc_dir = project_root / "docs"

    # コード抽出
    extractor = DocCodeExtractor()
    blocks = extractor.extract_from_directory(doc_dir)

    # 統計情報
    stats: defaultdict[str, dict[str, int]] = defaultdict(
        lambda: {"total": 0, "test": 0, "skip": 0, "pass": 0, "fail": 0}
    )
    errors = []

    # 実行環境をセットアップ
    executor = SimpleCodeExecutor()

    print("=" * 80)
    print("ドキュメントコードブロック チェック")
    print("=" * 80)

    # 各ブロックをチェック
    for block in blocks:
        # ファイルごとに集計
        rel_path = Path(block.filename).relative_to(doc_dir)
        file_key = str(rel_path)

        stats[file_key]["total"] += 1

        if block.skip:
            stats[file_key]["skip"] += 1
        else:
            stats[file_key]["test"] += 1

            # 実際に実行してみる
            success, output, error = executor.execute(block.code)

            if success:
                stats[file_key]["pass"] += 1
            else:
                stats[file_key]["fail"] += 1
                errors.append(
                    {
                        "file": rel_path,
                        "line": block.line_number,
                        "name": block.test_name,
                        "error": error[:200],  # エラーメッセージの先頭200文字
                    }
                )

    # 統計表示
    print("\n## ファイル別統計\n")
    print(f"{'File':<50} {'Total':>7} {'Test':>6} {'Skip':>6} {'Pass':>6} {'Fail':>6}")
    print("-" * 80)

    total_all = total_test = total_skip = total_pass = total_fail = 0

    for file_path in sorted(stats.keys()):
        s = stats[file_path]
        print(f"{file_path:<50} {s['total']:>7} {s['test']:>6} {s['skip']:>6} {s['pass']:>6} {s['fail']:>6}")

        total_all += s["total"]
        total_test += s["test"]
        total_skip += s["skip"]
        total_pass += s["pass"]
        total_fail += s["fail"]

    print("-" * 80)
    print(f"{'TOTAL':<50} {total_all:>7} {total_test:>6} {total_skip:>6} {total_pass:>6} {total_fail:>6}")

    # エラー詳細
    if errors:
        print("\n## エラー詳細\n")
        for i, err in enumerate(errors[:10], 1):  # 最初の10個のみ表示
            print(f"{i}. {err['file']}:{err['line']} ({err['name']})")
            print(f"   Error: {err['error']}")
            print()

        if len(errors) > 10:
            print(f"... 他 {len(errors) - 10} 個のエラー")

    # サマリー
    print("\n## サマリー\n")
    print(
        f"✓ 成功率: {total_pass}/{total_test} ({100 * total_pass / total_test:.1f}%)"
        if total_test > 0
        else "テスト対象なし"
    )
    print(f"✗ エラー数: {total_fail}")
    print(f"⊘ スキップ数: {total_skip}")

    # 終了コード
    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
