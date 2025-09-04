"""Generate benchmark comparison report in Markdown and CSV formats.

This script reads benchmark results from history.jsonl and generates:
1. A comprehensive Markdown report for standalone viewing
2. CSV files for Sphinx documentation integration
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class BenchmarkReportGenerator:
    """Generate Markdown and CSV reports from benchmark results."""

    def __init__(self):
        self.results_dir = Path("benchmark_results")
        self.history_file = self.results_dir / "history.jsonl"
        self.latest_file = self.results_dir / "latest.json"
        self.csv_output_dir = Path("docs/ja/_static/benchmark_data")
        # Create CSV output directory if it doesn't exist
        self.csv_output_dir.mkdir(parents=True, exist_ok=True)

    def load_latest_results(self) -> dict[str, Any] | None:
        """Load the most recent benchmark results."""
        if self.latest_file.exists():
            with open(self.latest_file) as f:
                result: dict[str, Any] = json.load(f)
                return result
        elif self.history_file.exists():
            # Read last line from history
            with open(self.history_file) as f:
                lines = f.readlines()
                if lines:
                    last_result: dict[str, Any] = json.loads(lines[-1])
                    return last_result
        return None

    def format_time(self, seconds: float) -> str:
        """Format time in appropriate units."""
        if seconds < 1e-6:
            return f"{seconds * 1e9:.2f} ns"
        elif seconds < 1e-3:
            return f"{seconds * 1e6:.2f} μs"
        elif seconds < 1:
            return f"{seconds * 1e3:.2f} ms"
        else:
            return f"{seconds:.2f} s"

    def calculate_speedup(self, baseline: float, compared: float) -> str:
        """Calculate relative speedup."""
        if compared == 0:
            return "∞"
        ratio = baseline / compared
        if ratio > 1:
            return f"{ratio:.1f}倍速い"
        else:
            return f"{1 / ratio:.1f}倍遅い"

    def extract_benchmark_times(self, benchmarks: list[dict]) -> dict[str, dict[str, float]]:
        """Extract benchmark times organized by test type."""
        results: dict[str, dict[str, float]] = {}

        for bench in benchmarks:
            name = bench["name"]
            mean_time = bench["stats"].get("mean", 0)

            # Parse test name to categorize (handle both full and short names)
            if "test_quantforge_single" in name:
                results.setdefault("single", {})["quantforge"] = mean_time
            elif "test_pure_python_single" in name:
                results.setdefault("single", {})["pure_python"] = mean_time
            elif "test_numpy_scipy_single" in name:
                results.setdefault("single", {})["numpy_scipy"] = mean_time
            elif "test_quantforge_batch" in name:
                size = self._extract_size(name)
                key = f"batch_{size}"
                results.setdefault(key, {})["quantforge"] = mean_time
            elif "test_pure_python_batch" in name:
                size = self._extract_size(name)
                key = f"batch_{size}"
                results.setdefault(key, {})["pure_python"] = mean_time
            elif "test_numpy_scipy_batch" in name:
                size = self._extract_size(name)
                key = f"batch_{size}"
                results.setdefault(key, {})["numpy_scipy"] = mean_time

        return results

    def _extract_size(self, name: str) -> int:
        """Extract batch size from test name."""
        # Look for pattern like [100] or [1000] in parameterized test names
        import re

        match = re.search(r"\[(\d+)\]", name)
        if match:
            return int(match.group(1))
        return 0

    def generate_report(self) -> str:
        """Generate comprehensive benchmark report."""
        data = self.load_latest_results()
        if not data:
            return (
                "# ベンチマーク結果\n\n"
                "No benchmark data available. Run `pytest tests/performance/ -m benchmark` first.\n"
            )

        lines = []
        lines.append("# ベンチマーク結果")
        lines.append("")
        lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Environment info
        env = data.get("environment", {})
        lines.append("## テスト環境")
        lines.append(f"- **Python**: {env.get('python_version', 'unknown')}")
        lines.append(f"- **Platform**: {env.get('platform', 'unknown')}")
        lines.append(f"- **CPU Count**: {env.get('cpu_count', 'unknown')}")
        lines.append(f"- **Memory**: {env.get('memory_gb', 'unknown')} GB")
        lines.append(f"- **QuantForge Version**: {data.get('version', 'unknown')}")
        lines.append(f"- **Git Commit**: {data.get('git_commit', 'unknown')}")
        lines.append("")

        # Extract benchmark times
        if "benchmarks" not in data:
            lines.append("No benchmark results found in data.")
            return "\n".join(lines)

        times = self.extract_benchmark_times(data["benchmarks"])

        # Single calculation comparison
        if "single" in times:
            lines.append("## 単一計算の比較")
            lines.append("")
            lines.append("| 実装方式 | 実行時間 | vs QuantForge | vs Pure Python |")
            lines.append("|---------|----------|---------------|----------------|")

            single = times["single"]
            qf_time = single.get("quantforge", 0)
            py_time = single.get("pure_python", 0)
            np_time = single.get("numpy_scipy", 0)

            speedup_py_qf = self.calculate_speedup(py_time, qf_time)
            lines.append(f"| **QuantForge** (Rust) | {self.format_time(qf_time)} | - | {speedup_py_qf} |")
            speedup_qf_py = self.calculate_speedup(qf_time, py_time)
            lines.append(f"| **Pure Python** (math) | {self.format_time(py_time)} | {speedup_qf_py} | - |")
            speedup_qf_np = self.calculate_speedup(qf_time, np_time)
            speedup_py_np = self.calculate_speedup(py_time, np_time)
            lines.append(f"| **NumPy+SciPy** | {self.format_time(np_time)} | {speedup_qf_np} | {speedup_py_np} |")
            lines.append("")

        # Batch calculations
        batch_sizes = [100, 1000, 10000]
        for size in batch_sizes:
            key = f"batch_{size}"
            if key in times:
                lines.append(f"## バッチ処理（{size:,}件）")
                lines.append("")
                lines.append("| 実装方式 | 実行時間 | スループット | vs QuantForge |")
                lines.append("|---------|----------|-------------|---------------|")

                batch = times[key]
                qf_time = batch.get("quantforge", 0)
                py_time = batch.get("pure_python", 0)
                np_time = batch.get("numpy_scipy", 0)

                # Calculate throughput (ops/sec)
                qf_throughput = size / qf_time if qf_time > 0 else 0
                py_throughput = size / py_time if py_time > 0 else 0
                np_throughput = size / np_time if np_time > 0 else 0

                lines.append(
                    f"| **QuantForge** | {self.format_time(qf_time)} | {qf_throughput / 1000:.1f}K ops/sec | - |"
                )
                speedup_qf_py = self.calculate_speedup(qf_time, py_time)
                py_ops = f"{py_throughput / 1000:.1f}K ops/sec"
                lines.append(f"| **Pure Python** | {self.format_time(py_time)} | {py_ops} | {speedup_qf_py} |")
                speedup_qf_np = self.calculate_speedup(qf_time, np_time)
                np_ops = f"{np_throughput / 1000:.1f}K ops/sec"
                lines.append(f"| **NumPy+SciPy** | {self.format_time(np_time)} | {np_ops} | {speedup_qf_np} |")
                lines.append("")

        # Performance summary
        lines.append("## パフォーマンス要約")
        lines.append("")

        if "single" in times:
            single = times["single"]
            qf_time = single.get("quantforge", 0)
            py_time = single.get("pure_python", 0)
            np_time = single.get("numpy_scipy", 0)

            lines.append("### 対Pure Python")
            if py_time > 0 and qf_time > 0:
                speedup = py_time / qf_time
                lines.append(f"- 単一計算: {speedup:.1f}倍の処理速度")

            for size in [100, 1000, 10000]:
                key = f"batch_{size}"
                if key in times:
                    batch = times[key]
                    qf_time = batch.get("quantforge", 0)
                    py_time = batch.get("pure_python", 0)
                    if py_time > 0 and qf_time > 0:
                        speedup = py_time / qf_time
                        lines.append(f"- バッチ処理（{size:,}件）: {speedup:.1f}倍の処理速度")

            lines.append("")
            lines.append("### 対NumPy+SciPy")

            single = times.get("single", {})
            qf_time = single.get("quantforge", 0)
            np_time = single.get("numpy_scipy", 0)
            if np_time > 0 and qf_time > 0:
                speedup = np_time / qf_time
                lines.append(f"- 単一計算: {speedup:.1f}倍の処理速度")

            for size in [100, 1000, 10000]:
                key = f"batch_{size}"
                if key in times:
                    batch = times[key]
                    qf_time = batch.get("quantforge", 0)
                    np_time = batch.get("numpy_scipy", 0)
                    if np_time > 0 and qf_time > 0:
                        speedup = np_time / qf_time
                        if speedup > 1:
                            lines.append(f"- バッチ処理（{size:,}件）: {speedup:.2f}倍の処理速度")
                        else:
                            lines.append(f"- バッチ処理（{size:,}件）: {1 / speedup:.2f}倍遅い")

        lines.append("")
        lines.append("## 測定コマンド")
        lines.append("")
        lines.append("```bash")
        lines.append("# ベンチマーク実行")
        lines.append("pytest tests/performance/ -m benchmark")
        lines.append("")
        lines.append("# レポート生成")
        lines.append("python tests/performance/generate_benchmark_report.py")
        lines.append("```")

        return "\n".join(lines)

    def format_time_for_csv(self, seconds: float) -> str:
        """Format time in appropriate units for CSV output."""
        if seconds < 1e-6:
            return f"{seconds * 1e9:.2f}"
        elif seconds < 1e-3:
            return f"{seconds * 1e6:.2f}"
        elif seconds < 1:
            return f"{seconds * 1e3:.2f}"
        else:
            return f"{seconds:.2f}"

    def get_time_unit(self, seconds: float) -> str:
        """Get appropriate time unit for the given seconds."""
        if seconds < 1e-6:
            return "ns"
        elif seconds < 1e-3:
            return "μs"
        elif seconds < 1:
            return "ms"
        else:
            return "s"

    def calculate_speedup_ratio(self, baseline: float, compared: float) -> float:
        """Calculate speedup ratio (positive if faster, negative if slower)."""
        if compared == 0:
            return float("inf")
        ratio = baseline / compared
        return ratio if ratio >= 1 else -compared / baseline

    def generate_csv_reports(self) -> dict[str, Path]:
        """Generate CSV files for Sphinx documentation integration."""
        data = self.load_latest_results()
        if not data:
            return {}

        csv_files = {}

        # Extract benchmark times
        times = self.extract_benchmark_times(data.get("benchmarks", []))

        # 1. Environment CSV
        env_file = self.csv_output_dir / "environment.csv"
        env = data.get("environment", {})
        with open(env_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["項目", "値"])
            writer.writerow(["Python", env.get("python_version", "unknown")])
            writer.writerow(["Platform", env.get("platform", "unknown")])
            writer.writerow(["CPU Count", env.get("cpu_count", "unknown")])
            writer.writerow(["Memory (GB)", env.get("memory_gb", "unknown")])
            writer.writerow(["QuantForge Version", data.get("version", "unknown")])
            writer.writerow(["測定日時", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        csv_files["environment"] = env_file

        # 2. Single calculation CSV
        if "single" in times:
            single_file = self.csv_output_dir / "single_calculation.csv"
            single = times["single"]
            qf_time = single.get("quantforge", 0)
            py_time = single.get("pure_python", 0)
            np_time = single.get("numpy_scipy", 0)

            # Determine common time unit based on fastest time
            min_time = min(t for t in [qf_time, py_time, np_time] if t > 0)
            unit = self.get_time_unit(min_time)

            with open(single_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["実装方式", f"実行時間 ({unit})", "vs QuantForge", "vs Pure Python"])

                # QuantForge row
                qf_formatted = self.format_time_for_csv(qf_time)
                py_speedup = self.calculate_speedup_ratio(py_time, qf_time)
                py_speedup_str = f"{py_speedup:.1f}x" if py_speedup > 0 else f"{-py_speedup:.1f}x遅い"
                writer.writerow(["QuantForge (Rust)", qf_formatted, "-", py_speedup_str])

                # Pure Python row
                py_formatted = self.format_time_for_csv(py_time)
                qf_speedup = self.calculate_speedup_ratio(qf_time, py_time)
                qf_speedup_str = f"{qf_speedup:.1f}x" if qf_speedup > 0 else f"{-qf_speedup:.1f}x遅い"
                writer.writerow(["Pure Python (math)", py_formatted, qf_speedup_str, "-"])

                # NumPy+SciPy row
                np_formatted = self.format_time_for_csv(np_time)
                qf_speedup_np = self.calculate_speedup_ratio(qf_time, np_time)
                qf_speedup_np_str = f"{qf_speedup_np:.1f}x" if qf_speedup_np > 0 else f"{-qf_speedup_np:.1f}x遅い"
                py_speedup_np = self.calculate_speedup_ratio(py_time, np_time)
                py_speedup_np_str = f"{py_speedup_np:.1f}x" if py_speedup_np > 0 else f"{-py_speedup_np:.1f}x遅い"
                writer.writerow(["NumPy+SciPy", np_formatted, qf_speedup_np_str, py_speedup_np_str])

            csv_files["single"] = single_file

        # 3. Batch processing CSV files
        batch_sizes = [100, 1000, 10000]
        for size in batch_sizes:
            key = f"batch_{size}"
            if key in times:
                batch_file = self.csv_output_dir / f"batch_{size}.csv"
                batch = times[key]
                qf_time = batch.get("quantforge", 0)
                py_time = batch.get("pure_python", 0)
                np_time = batch.get("numpy_scipy", 0)

                # Calculate throughput
                qf_throughput = size / qf_time if qf_time > 0 else 0
                py_throughput = size / py_time if py_time > 0 else 0
                np_throughput = size / np_time if np_time > 0 else 0

                with open(batch_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["実装方式", "実行時間", "スループット (K ops/sec)", "vs QuantForge"])

                    # QuantForge row
                    writer.writerow(["QuantForge", self.format_time(qf_time), f"{qf_throughput / 1000:.1f}", "-"])

                    # Pure Python row
                    speedup_py = self.calculate_speedup_ratio(qf_time, py_time)
                    speedup_py_str = f"{speedup_py:.1f}x" if speedup_py > 0 else f"{-speedup_py:.1f}x遅い"
                    writer.writerow(
                        ["Pure Python", self.format_time(py_time), f"{py_throughput / 1000:.1f}", speedup_py_str]
                    )

                    # NumPy+SciPy row
                    speedup_np = self.calculate_speedup_ratio(qf_time, np_time)
                    speedup_np_str = f"{speedup_np:.1f}x" if speedup_np > 0 else f"{-speedup_np:.1f}x遅い"
                    writer.writerow(
                        ["NumPy+SciPy", self.format_time(np_time), f"{np_throughput / 1000:.1f}", speedup_np_str]
                    )

                csv_files[f"batch_{size}"] = batch_file

        # 4. Performance summary CSV - vs Pure Python
        summary_py_file = self.csv_output_dir / "performance_summary_python.csv"
        self._generate_performance_summary_csv(summary_py_file, times, "pure_python")
        csv_files["performance_summary_python"] = summary_py_file

        # 5. Performance summary CSV - vs NumPy+SciPy
        summary_np_file = self.csv_output_dir / "performance_summary_numpy.csv"
        self._generate_performance_summary_csv(summary_np_file, times, "numpy_scipy")
        csv_files["performance_summary_numpy"] = summary_np_file

        # 4. Summary CSV for README
        summary_file = self.csv_output_dir / "summary.csv"
        self._generate_summary_csv(summary_file, times)
        csv_files["summary"] = summary_file

        # 5. Comparison CSV (3 implementations)
        comparison_file = self.csv_output_dir / "comparison.csv"
        self._generate_comparison_csv(comparison_file, times)
        csv_files["comparison"] = comparison_file

        return csv_files

    def _generate_summary_csv(self, file_path: Path, times: dict) -> None:
        """Generate summary CSV for README files."""
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["指標", "QuantForge", "Pure Python", "NumPy+SciPy", "最速"])

            # Single calculation
            if "single" in times:
                single = times["single"]
                qf = single.get("quantforge", 0)
                py = single.get("pure_python", 0)
                np = single.get("numpy_scipy", 0)
                fastest = "QuantForge" if qf <= min(py, np) else ("Pure Python" if py < np else "NumPy+SciPy")
                writer.writerow(["単一計算", self.format_time(qf), self.format_time(py), self.format_time(np), fastest])

            # Batch 10,000
            if "batch_10000" in times:
                batch = times["batch_10000"]
                qf = batch.get("quantforge", 0)
                py = batch.get("pure_python", 0)
                np = batch.get("numpy_scipy", 0)
                fastest = "QuantForge" if qf <= min(py, np) else ("Pure Python" if py < np else "NumPy+SciPy")
                writer.writerow(
                    ["バッチ10,000件", self.format_time(qf), self.format_time(py), self.format_time(np), fastest]
                )

    def _generate_performance_summary_csv(self, file_path: Path, times: dict, baseline: str) -> None:
        """Generate performance summary CSV comparing against baseline implementation."""
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            baseline_name = "Pure Python" if baseline == "pure_python" else "NumPy+SciPy"
            writer.writerow(["計算タイプ", "データサイズ", f"vs {baseline_name}"])
            
            # Single calculation
            if "single" in times:
                single = times["single"]
                qf_time = single.get("quantforge", 0)
                base_time = single.get(baseline, 0)
                if base_time > 0 and qf_time > 0:
                    speedup = base_time / qf_time
                    writer.writerow(["単一計算", "1件", f"{speedup:.1f}倍の処理速度"])
            
            # Batch calculations
            for size in [100, 1000, 10000]:
                key = f"batch_{size}"
                if key in times:
                    batch = times[key]
                    qf_time = batch.get("quantforge", 0)
                    base_time = batch.get(baseline, 0)
                    if base_time > 0 and qf_time > 0:
                        speedup = base_time / qf_time
                        if speedup >= 1:
                            writer.writerow(["バッチ処理", f"{size:,}件", f"{speedup:.1f}倍の処理速度"])
                        else:
                            writer.writerow(["バッチ処理", f"{size:,}件", f"{1/speedup:.2f}倍遅い"])

    def _generate_comparison_csv(self, file_path: Path, times: dict) -> None:
        """Generate comparison table CSV."""
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["データサイズ", "QuantForge", "Pure Python", "NumPy+SciPy", "QF vs Py", "QF vs NumPy"])

            # Single
            if "single" in times:
                single = times["single"]
                qf = single.get("quantforge", 0)
                py = single.get("pure_python", 0)
                np = single.get("numpy_scipy", 0)
                qf_py_ratio = py / qf if qf > 0 else 0
                qf_np_ratio = np / qf if qf > 0 else 0
                writer.writerow(
                    [
                        "単一",
                        self.format_time(qf),
                        self.format_time(py),
                        self.format_time(np),
                        f"{qf_py_ratio:.1f}x",
                        f"{qf_np_ratio:.1f}x",
                    ]
                )

            # Batch sizes
            for size in [100, 1000, 10000]:
                key = f"batch_{size}"
                if key in times:
                    batch = times[key]
                    qf = batch.get("quantforge", 0)
                    py = batch.get("pure_python", 0)
                    np = batch.get("numpy_scipy", 0)
                    qf_py_ratio = py / qf if qf > 0 else 0
                    qf_np_ratio = np / qf if qf > 0 else 0
                    writer.writerow(
                        [
                            f"{size:,}件",
                            self.format_time(qf),
                            self.format_time(py),
                            self.format_time(np),
                            f"{qf_py_ratio:.1f}x",
                            f"{qf_np_ratio:.1f}x" if qf_np_ratio > 1 else f"{1 / qf_np_ratio:.1f}x遅い",
                        ]
                    )

    def save_report(self, output_file: Path | None = None) -> Path:
        """Save Markdown report to file."""
        report = self.generate_report()

        if output_file is None:
            output_file = Path("benchmark_report.md")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)

        return output_file


def main():
    """Main entry point."""
    generator = BenchmarkReportGenerator()

    # Generate CSV files for Sphinx integration
    csv_files = generator.generate_csv_reports()
    if csv_files:
        print("\n📊 CSV files generated for Sphinx:", file=sys.stderr)
        for name, path in csv_files.items():
            print(f"   - {name}: {path}", file=sys.stderr)

    # Generate and print Markdown report
    report = generator.generate_report()
    print(report)

    # Optionally save Markdown to file
    if len(sys.argv) > 1:
        output_file = Path(sys.argv[1])
        saved_path = generator.save_report(output_file)
        print(f"\n✅ Markdown report saved to: {saved_path}", file=sys.stderr)
    else:
        print("\n💡 Tip: Pass a filename to save the Markdown report:", file=sys.stderr)
        print("   python tests/performance/generate_benchmark_report.py report.md", file=sys.stderr)


if __name__ == "__main__":
    main()
