"""Generate benchmark comparison report in Markdown format.

This script reads benchmark results from history.jsonl and generates
a comprehensive comparison report of Pure Python, NumPy+SciPy, and QuantForge.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import statistics


class BenchmarkReportGenerator:
    """Generate Markdown reports from benchmark results."""
    
    def __init__(self):
        self.results_dir = Path("benchmark_results")
        self.history_file = self.results_dir / "history.jsonl"
        self.latest_file = self.results_dir / "latest.json"
        
    def load_latest_results(self) -> Optional[Dict[str, Any]]:
        """Load the most recent benchmark results."""
        if self.latest_file.exists():
            with open(self.latest_file, 'r') as f:
                return json.load(f)
        elif self.history_file.exists():
            # Read last line from history
            with open(self.history_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    return json.loads(lines[-1])
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
            return f"{1/ratio:.1f}倍遅い"
    
    def extract_benchmark_times(self, benchmarks: List[Dict]) -> Dict[str, Dict[str, float]]:
        """Extract benchmark times organized by test type."""
        results = {}
        
        for bench in benchmarks:
            name = bench['name']
            mean_time = bench['stats'].get('mean', 0)
            
            # Parse test name to categorize (handle both full and short names)
            if 'test_quantforge_single' in name:
                results.setdefault('single', {})['quantforge'] = mean_time
            elif 'test_pure_python_single' in name:
                results.setdefault('single', {})['pure_python'] = mean_time
            elif 'test_numpy_scipy_single' in name:
                results.setdefault('single', {})['numpy_scipy'] = mean_time
            elif 'test_quantforge_batch' in name:
                size = self._extract_size(name)
                key = f'batch_{size}'
                results.setdefault(key, {})['quantforge'] = mean_time
            elif 'test_pure_python_batch' in name:
                size = self._extract_size(name)
                key = f'batch_{size}'
                results.setdefault(key, {})['pure_python'] = mean_time
            elif 'test_numpy_scipy_batch' in name:
                size = self._extract_size(name)
                key = f'batch_{size}'
                results.setdefault(key, {})['numpy_scipy'] = mean_time
                
        return results
    
    def _extract_size(self, name: str) -> int:
        """Extract batch size from test name."""
        # Look for pattern like [100] or [1000] in parameterized test names
        import re
        match = re.search(r'\[(\d+)\]', name)
        if match:
            return int(match.group(1))
        return 0
    
    def generate_report(self) -> str:
        """Generate comprehensive benchmark report."""
        data = self.load_latest_results()
        if not data:
            return "# ベンチマーク結果\n\nNo benchmark data available. Run `pytest tests/performance/ -m benchmark` first.\n"
        
        lines = []
        lines.append("# ベンチマーク結果")
        lines.append("")
        lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Environment info
        env = data.get('environment', {})
        lines.append("## テスト環境")
        lines.append(f"- **Python**: {env.get('python_version', 'unknown')}")
        lines.append(f"- **Platform**: {env.get('platform', 'unknown')}")
        lines.append(f"- **CPU Count**: {env.get('cpu_count', 'unknown')}")
        lines.append(f"- **Memory**: {env.get('memory_gb', 'unknown')} GB")
        lines.append(f"- **QuantForge Version**: {data.get('version', 'unknown')}")
        lines.append(f"- **Git Commit**: {data.get('git_commit', 'unknown')}")
        lines.append("")
        
        # Extract benchmark times
        if 'benchmarks' not in data:
            lines.append("No benchmark results found in data.")
            return '\n'.join(lines)
            
        times = self.extract_benchmark_times(data['benchmarks'])
        
        # Single calculation comparison
        if 'single' in times:
            lines.append("## 単一計算の比較")
            lines.append("")
            lines.append("| 実装方式 | 実行時間 | vs QuantForge | vs Pure Python |")
            lines.append("|---------|----------|---------------|----------------|")
            
            single = times['single']
            qf_time = single.get('quantforge', 0)
            py_time = single.get('pure_python', 0)
            np_time = single.get('numpy_scipy', 0)
            
            lines.append(f"| **QuantForge** (Rust) | {self.format_time(qf_time)} | - | {self.calculate_speedup(py_time, qf_time)} |")
            lines.append(f"| **Pure Python** (math) | {self.format_time(py_time)} | {self.calculate_speedup(qf_time, py_time)} | - |")
            lines.append(f"| **NumPy+SciPy** | {self.format_time(np_time)} | {self.calculate_speedup(qf_time, np_time)} | {self.calculate_speedup(py_time, np_time)} |")
            lines.append("")
        
        # Batch calculations
        batch_sizes = [100, 1000, 10000]
        for size in batch_sizes:
            key = f'batch_{size}'
            if key in times:
                lines.append(f"## バッチ処理（{size:,}件）")
                lines.append("")
                lines.append("| 実装方式 | 実行時間 | スループット | vs QuantForge |")
                lines.append("|---------|----------|-------------|---------------|")
                
                batch = times[key]
                qf_time = batch.get('quantforge', 0)
                py_time = batch.get('pure_python', 0)
                np_time = batch.get('numpy_scipy', 0)
                
                # Calculate throughput (ops/sec)
                qf_throughput = size / qf_time if qf_time > 0 else 0
                py_throughput = size / py_time if py_time > 0 else 0
                np_throughput = size / np_time if np_time > 0 else 0
                
                lines.append(f"| **QuantForge** | {self.format_time(qf_time)} | {qf_throughput/1000:.1f}K ops/sec | - |")
                lines.append(f"| **Pure Python** | {self.format_time(py_time)} | {py_throughput/1000:.1f}K ops/sec | {self.calculate_speedup(qf_time, py_time)} |")
                lines.append(f"| **NumPy+SciPy** | {self.format_time(np_time)} | {np_throughput/1000:.1f}K ops/sec | {self.calculate_speedup(qf_time, np_time)} |")
                lines.append("")
        
        # Performance summary
        lines.append("## パフォーマンス要約")
        lines.append("")
        
        if 'single' in times:
            single = times['single']
            qf_time = single.get('quantforge', 0)
            py_time = single.get('pure_python', 0)
            np_time = single.get('numpy_scipy', 0)
            
            lines.append("### 対Pure Python")
            if py_time > 0 and qf_time > 0:
                speedup = py_time / qf_time
                lines.append(f"- 単一計算: {speedup:.1f}倍の処理速度")
            
            for size in [100, 1000, 10000]:
                key = f'batch_{size}'
                if key in times:
                    batch = times[key]
                    qf_time = batch.get('quantforge', 0)
                    py_time = batch.get('pure_python', 0)
                    if py_time > 0 and qf_time > 0:
                        speedup = py_time / qf_time
                        lines.append(f"- バッチ処理（{size:,}件）: {speedup:.1f}倍の処理速度")
            
            lines.append("")
            lines.append("### 対NumPy+SciPy")
            
            single = times.get('single', {})
            qf_time = single.get('quantforge', 0)
            np_time = single.get('numpy_scipy', 0)
            if np_time > 0 and qf_time > 0:
                speedup = np_time / qf_time
                lines.append(f"- 単一計算: {speedup:.1f}倍の処理速度")
            
            for size in [100, 1000, 10000]:
                key = f'batch_{size}'
                if key in times:
                    batch = times[key]
                    qf_time = batch.get('quantforge', 0)
                    np_time = batch.get('numpy_scipy', 0)
                    if np_time > 0 and qf_time > 0:
                        speedup = np_time / qf_time
                        if speedup > 1:
                            lines.append(f"- バッチ処理（{size:,}件）: {speedup:.2f}倍の処理速度")
                        else:
                            lines.append(f"- バッチ処理（{size:,}件）: {1/speedup:.2f}倍遅い")
        
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
        
        return '\n'.join(lines)
    
    def save_report(self, output_file: Optional[Path] = None) -> Path:
        """Save report to file."""
        report = self.generate_report()
        
        if output_file is None:
            output_file = Path("benchmark_report.md")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return output_file


def main():
    """Main entry point."""
    generator = BenchmarkReportGenerator()
    
    # Generate and print report
    report = generator.generate_report()
    print(report)
    
    # Optionally save to file
    if len(sys.argv) > 1:
        output_file = Path(sys.argv[1])
        saved_path = generator.save_report(output_file)
        print(f"\n✅ Report saved to: {saved_path}", file=sys.stderr)
    else:
        print("\n💡 Tip: Pass a filename to save the report:", file=sys.stderr)
        print("   python tests/performance/generate_benchmark_report.py report.md", file=sys.stderr)


if __name__ == "__main__":
    main()