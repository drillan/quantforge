"""ベンチマーク結果をMarkdown形式にフォーマット."""

import json
from typing import Any


def format_time(seconds: float) -> str:
    """時間を適切な単位でフォーマット."""
    if seconds < 1e-6:
        return f"{seconds * 1e9:.1f} ns"
    elif seconds < 1e-3:
        return f"{seconds * 1e6:.2f} μs"
    elif seconds < 1:
        return f"{seconds * 1e3:.2f} ms"
    else:
        return f"{seconds:.2f} s"


def format_markdown(results: dict[str, Any]) -> str:
    """結果をMarkdown形式にフォーマット."""
    md = []

    # ヘッダー
    md.append("# Black-Scholesベンチマーク結果")
    md.append("")
    md.append(f"測定日時: {results['system_info']['timestamp']}")
    md.append("")

    # システム情報
    md.append("## 測定環境")
    md.append("")
    info = results["system_info"]
    md.append(f"- **プラットフォーム**: {info['platform']}")
    md.append(f"- **CPU**: {info['processor']}")
    md.append(f"- **コア数**: {info['cpu_count']} (論理: {info['cpu_count_logical']})")
    md.append(f"- **メモリ**: {info['memory_gb']} GB")
    md.append(f"- **Python**: {info['python_version']}")
    md.append("")

    # 単一計算結果
    md.append("## 単一計算性能")
    md.append("")
    md.append("### 実測値")
    single = results["single"]
    md.append("| 実装 | 時間 | 説明 |")
    md.append("|------|------|------|")
    md.append(f"| QuantForge (Rust) | {format_time(single['quantforge'])} | 最適化されたRust実装 |")
    md.append(f"| NumPy+SciPy | {format_time(single['numpy_scipy'])} | NumPy+SciPy実装 |")
    md.append(f"| Pure Python | {format_time(single['pure_python'])} | 外部ライブラリなし |")
    md.append("")

    md.append("### 相対性能")
    md.append("| 比較 | 高速化率 |")
    md.append("|------|----------|")
    md.append(f"| QuantForge vs Pure Python | **{single['speedup_vs_pure_python']:.0f}倍** 高速 |")
    md.append(f"| QuantForge vs NumPy+SciPy | **{single['speedup_vs_numpy_scipy']:.1f}倍** 高速 |")
    md.append("")

    # バッチ処理結果
    md.append("## バッチ処理性能")
    md.append("")
    md.append("| データサイズ | QuantForge | NumPy | Pure Python | QF高速化率 | QFスループット |")
    md.append("|-------------|------------|-------|-------------|-----------|----------------|")

    for batch in results["batch"]:
        size = batch["size"]
        qf_time = format_time(batch["quantforge"])
        np_time = format_time(batch["numpy_batch"])

        py_time = format_time(batch["pure_python"]) if "pure_python" in batch else "N/A"

        np_speedup = batch["speedup_vs_numpy"]
        throughput = batch["throughput_qf"] / 1e6

        md.append(
            f"| {size:,} | {qf_time} | {np_time} | {py_time} | NumPy: {np_speedup:.1f}x | {throughput:.1f}M ops/sec |"
        )

    md.append("")

    # 要約
    md.append("## パフォーマンス要約")
    md.append("")

    # 単一計算の要約
    md.append("### 単一計算")
    md.append(f"- QuantForgeはPure Pythonより**{results['single']['speedup_vs_pure_python']:.0f}倍**高速")
    md.append(f"- QuantForgeはSciPyより**{results['single']['speedup_vs_numpy_scipy']:.1f}倍**高速")
    md.append("")

    # バッチ処理の要約
    md.append("### バッチ処理（100万件）")
    batch_1m = next((b for b in results["batch"] if b["size"] == 1000000), None)
    if batch_1m:
        md.append(f"- QuantForgeはNumPyより**{batch_1m['speedup_vs_numpy']:.0f}倍**高速")
        md.append(f"- 実測スループット: **{batch_1m['throughput_qf'] / 1e6:.1f}M ops/sec**")
        md.append(f"- 処理時間: {format_time(batch_1m['quantforge'])}")
    md.append("")

    # 注記
    md.append("## 測定方法")
    md.append("")
    md.append("- **測定回数**: ウォームアップ100回後、1000回測定の中央値")
    md.append("- **Pure Python**: 外部ライブラリを使用しない実装")
    md.append("- **SciPy**: scipy.stats.normを使用した一般的な実装")
    md.append("- **NumPy**: ベクトル化されたバッチ処理実装")
    md.append("- **QuantForge**: Rust + SIMD最適化実装")
    md.append("")

    md.append("## 再現方法")
    md.append("")
    md.append("```bash")
    md.append("# ベンチマーク実行（推奨）")
    md.append("cd benchmarks")
    md.append("./run_benchmarks.sh")
    md.append("")
    md.append("# または個別実行")
    md.append("cd benchmarks")
    md.append("uv run python run_comparison.py")
    md.append("uv run python format_results.py")
    md.append("```")
    md.append("")

    return "\n".join(md)


if __name__ == "__main__":
    from pathlib import Path
    
    # プロジェクトルートからの相対パスでresultsディレクトリを定義
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    RESULTS_DIR = BASE_DIR / "benchmarks" / "results"

    # 最新結果を読み込み
    latest_file = RESULTS_DIR / "latest.json"
    if latest_file.exists():
        with open(latest_file) as f:
            results = json.load(f)
    else:
        print("Error: No benchmark results found at", latest_file)
        print("Run 'python -m benchmarks.runners.comparison' first")
        exit(1)

    # Markdown形式で出力
    print(format_markdown(results))
