"""ベンチマーク結果のフォーマット機能."""

from typing import Any


def format_time(seconds: float) -> str:
    """時間を適切な単位でフォーマット.

    Args:
        seconds: 秒単位の時間

    Returns:
        フォーマットされた時間文字列
    """
    if seconds < 1e-9:
        return f"{seconds * 1e12:.1f} ps"
    elif seconds < 1e-6:
        return f"{seconds * 1e9:.1f} ns"
    elif seconds < 1e-3:
        return f"{seconds * 1e6:.2f} μs"
    elif seconds < 1:
        return f"{seconds * 1e3:.2f} ms"
    else:
        return f"{seconds:.2f} s"


def format_throughput(ops_per_second: float) -> str:
    """スループットを適切な単位でフォーマット.

    Args:
        ops_per_second: 秒あたりの操作数

    Returns:
        フォーマットされたスループット文字列
    """
    if ops_per_second < 1e3:
        return f"{ops_per_second:.1f} ops/s"
    elif ops_per_second < 1e6:
        return f"{ops_per_second / 1e3:.1f}K ops/s"
    elif ops_per_second < 1e9:
        return f"{ops_per_second / 1e6:.1f}M ops/s"
    else:
        return f"{ops_per_second / 1e9:.1f}G ops/s"


def format_speedup(speedup: float) -> str:
    """高速化率をフォーマット.

    Args:
        speedup: 高速化率

    Returns:
        フォーマットされた高速化率文字列
    """
    if speedup >= 1:
        return f"{speedup:.2f}x faster"
    else:
        return f"{1 / speedup:.2f}x slower"


class BenchmarkFormatter:
    """ベンチマーク結果のフォーマッタークラス."""

    def __init__(self, title: str = "Benchmark Results"):
        """初期化.

        Args:
            title: レポートのタイトル
        """
        self.title = title

    def format_markdown(self, results: dict[str, Any]) -> str:
        """結果をMarkdown形式にフォーマット.

        Args:
            results: ベンチマーク結果

        Returns:
            Markdown形式の文字列
        """
        md = []

        # ヘッダー
        md.append(f"# {self.title}")
        md.append("")

        # システム情報（存在する場合）
        if "system_info" in results:
            md.append("## 測定環境")
            md.append("")
            info = results["system_info"]
            md.append(f"- **測定日時**: {info.get('timestamp', 'N/A')}")
            md.append(f"- **プラットフォーム**: {info.get('platform', 'N/A')}")
            md.append(f"- **CPU**: {info.get('processor', 'N/A')}")
            md.append(f"- **コア数**: {info.get('cpu_count', 'N/A')} (論理: {info.get('cpu_count_logical', 'N/A')})")
            md.append(f"- **メモリ**: {info.get('memory_gb', 'N/A')} GB")
            md.append(f"- **Python**: {info.get('python_version', 'N/A')}")
            md.append("")

        # 単一計算結果（存在する場合）
        if "single" in results:
            md.extend(self._format_single_results(results["single"]))

        # バッチ計算結果（存在する場合）
        if "batch" in results:
            md.extend(self._format_batch_results(results["batch"]))

        # カスタムセクション
        for key, value in results.items():
            if key not in ["system_info", "single", "batch", "timestamp"]:
                md.extend(self._format_custom_section(key, value))

        return "\n".join(md)

    def _format_single_results(self, single: dict[str, Any]) -> list[str]:
        """単一計算結果のフォーマット."""
        md = []
        md.append("## 単一計算性能")
        md.append("")
        md.append("| 実装 | 時間 | 高速化率 |")
        md.append("|------|------|----------|")

        # 基準となる時間を探す
        baseline_time = single.get("pure_python") or single.get("numpy_scipy")

        for impl, time_val in single.items():
            if impl.startswith("speedup_"):
                continue

            speedup = ""
            if baseline_time and time_val != baseline_time:
                speedup = format_speedup(baseline_time / time_val)

            name = self._format_impl_name(impl)
            md.append(f"| {name} | {format_time(time_val)} | {speedup} |")

        md.append("")
        return md

    def _format_batch_results(self, batch: list[dict[str, Any]]) -> list[str]:
        """バッチ計算結果のフォーマット."""
        md = []
        md.append("## バッチ処理性能")
        md.append("")

        for batch_result in batch:
            size = batch_result.get("size", "N/A")
            md.append(f"### サイズ: {size:,}")
            md.append("")
            md.append("| 実装 | 時間 | スループット | 高速化率 |")
            md.append("|------|------|--------------|----------|")

            # 各実装の結果を表示
            for key, value in batch_result.items():
                if key in ["size", "throughput_qf", "throughput_np"]:
                    continue
                if key.startswith("speedup_"):
                    continue

                name = self._format_impl_name(key)
                time_str = format_time(value) if isinstance(value, int | float) else str(value)

                # スループット計算
                throughput = ""
                if isinstance(value, int | float) and value > 0:
                    ops = size / value if isinstance(size, int | float) else 0
                    if ops > 0:
                        throughput = format_throughput(ops)

                # 高速化率
                speedup = ""
                speedup_key = f"speedup_vs_{key.replace('_batch', '')}"
                if speedup_key in batch_result:
                    speedup = format_speedup(batch_result[speedup_key])

                md.append(f"| {name} | {time_str} | {throughput} | {speedup} |")

            md.append("")

        return md

    def _format_custom_section(self, key: str, value: Any) -> list[str]:
        """カスタムセクションのフォーマット."""
        md = []
        title = key.replace("_", " ").title()
        md.append(f"## {title}")
        md.append("")

        if isinstance(value, dict):
            for k, v in value.items():
                md.append(f"- **{self._format_key(k)}**: {self._format_value(v)}")
        elif isinstance(value, list):
            for item in value:
                md.append(f"- {self._format_value(item)}")
        else:
            md.append(str(value))

        md.append("")
        return md

    @staticmethod
    def _format_impl_name(impl: str) -> str:
        """実装名のフォーマット."""
        name_map = {
            "quantforge": "QuantForge (Rust)",
            "pure_python": "Pure Python",
            "numpy_scipy": "NumPy+SciPy",
            "numpy_batch": "NumPy (Batch)",
        }
        return name_map.get(impl, impl.replace("_", " ").title())

    @staticmethod
    def _format_key(key: str) -> str:
        """キー名のフォーマット."""
        return key.replace("_", " ").title()

    @staticmethod
    def _format_value(value: Any) -> str:
        """値のフォーマット."""
        if isinstance(value, float):
            if value < 0.01 or value > 1000:
                return f"{value:.2e}"
            else:
                return f"{value:.4f}"
        return str(value)
