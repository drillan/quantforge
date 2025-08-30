"""QuantForge Benchmarks Package - Main Entry Point."""

import sys


def main() -> None:
    """Main entry point for benchmarks package."""
    print("=" * 60)
    print("QuantForge Benchmarks Package")
    print("=" * 60)
    print("\n利用可能なコマンド:")
    print("\n📊 ベンチマーク実行:")
    print("  python -m benchmarks.runners.comparison")
    print("    比較ベンチマークを実行（QuantForge vs SciPy vs Pure Python）")
    print()
    print("  python -m benchmarks.runners.practical")
    print("    実践シナリオベンチマークを実行（ボラティリティサーフェス等）")
    print()
    print("  python -m benchmarks.runners.arraylike")
    print("    ArrayLike互換性テストを実行")
    print()
    print("\n📈 分析ツール:")
    print("  python -m benchmarks.analysis.analyze")
    print("    パフォーマンストレンドを分析")
    print()
    print("  python -m benchmarks.analysis.format")
    print("    結果をMarkdown形式でフォーマット")
    print()
    print("\n💻 プログラムからの使用:")
    print("  from benchmarks.baseline import python_baseline")
    print("  from benchmarks.analysis import analyze")
    print()
    print("詳細はドキュメントを参照:")
    print("  docs/ja/internal/benchmark_management_guide.md")
    print("=" * 60)

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ["--help", "-h"]:
            return
        elif arg == "comparison":
            print("\n比較ベンチマークを実行中...")
            from benchmarks.runners import comparison

            comparison.main()
        elif arg == "practical":
            print("\n実践シナリオを実行中...")
            from benchmarks.runners import practical

            practical.main()
        elif arg == "analyze":
            print("\n分析を実行中...")
            from benchmarks.analysis import analyze

            analyze.main()
        else:
            print(f"\n不明なコマンド: {arg}")
            print("--help オプションで使用方法を確認してください")
            sys.exit(1)


if __name__ == "__main__":
    main()
