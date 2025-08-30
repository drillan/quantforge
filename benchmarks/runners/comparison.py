"""Black-Scholesの性能比較."""

import platform
import time
from typing import Any

import numpy as np
import psutil
from quantforge import models

from benchmarks.baseline.python_baseline import (
    black_scholes_numpy_batch,
    black_scholes_pure_python,
    black_scholes_pure_python_batch,
    black_scholes_scipy_single,
)


class BenchmarkRunner:
    """ベンチマーク実行クラス."""

    def __init__(self, warmup_runs: int = 100, measure_runs: int = 1000):
        self.warmup_runs = warmup_runs
        self.measure_runs = measure_runs

    def get_system_info(self) -> dict[str, Any]:
        """システム情報を取得."""
        return {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(logical=False),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "python_version": platform.python_version(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def benchmark_single(self) -> dict[str, Any]:
        """単一計算のベンチマーク."""
        s, k, t, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.2

        results: dict[str, Any] = {}

        # QuantForge (Rust)
        for _ in range(self.warmup_runs):
            models.call_price(s, k, t, r, sigma)

        times = []
        for _ in range(self.measure_runs):
            start = time.perf_counter()
            models.call_price(s, k, t, r, sigma)
            times.append(time.perf_counter() - start)
        qf_time = np.median(times)  # 中央値を使用（外れ値の影響を軽減）
        results["quantforge"] = qf_time

        # Pure Python（外部ライブラリなし）
        for _ in range(min(self.warmup_runs, 10)):  # 遅いので少なめ
            black_scholes_pure_python(s, k, t, r, sigma)

        times = []
        for _ in range(min(self.measure_runs, 100)):  # 遅いので少なめ
            start = time.perf_counter()
            black_scholes_pure_python(s, k, t, r, sigma)
            times.append(time.perf_counter() - start)
        py_time = np.median(times)
        results["pure_python"] = py_time

        # NumPy+SciPy（一般的な実装）
        for _ in range(self.warmup_runs):
            black_scholes_scipy_single(s, k, t, r, sigma)

        times = []
        for _ in range(self.measure_runs):
            start = time.perf_counter()
            black_scholes_scipy_single(s, k, t, r, sigma)
            times.append(time.perf_counter() - start)
        numpy_scipy_time = np.median(times)
        results["numpy_scipy"] = numpy_scipy_time

        # 相対性能計算
        results["speedup_vs_pure_python"] = py_time / qf_time
        results["speedup_vs_numpy_scipy"] = numpy_scipy_time / qf_time

        return results

    def benchmark_batch(self, size: int) -> dict[str, Any]:
        """バッチ処理のベンチマーク."""
        spots = np.random.uniform(50, 150, size).astype(np.float64)
        spots_list = spots.tolist()  # Pure Python用
        k, t, r, sigma = 100.0, 1.0, 0.05, 0.2

        results: dict[str, Any] = {"size": size}

        # 測定回数をサイズに応じて調整（適切な実行時間を確保）
        if size <= 100:
            n_runs = 500  # 小さいサイズは多めに測定
        elif size <= 1000:
            n_runs = 200
        elif size <= 10000:
            n_runs = 100
        elif size <= 100000:
            n_runs = 50
        else:
            n_runs = 30  # 100万件でも30回測定

        # QuantForge
        if hasattr(models, "call_price_batch"):
            # Warmup (十分なウォームアップで安定した測定)
            for _ in range(20):
                _ = models.call_price_batch(spots[: min(100, size)], k, t, r, sigma)

            # Measure
            times = []
            for _ in range(n_runs):
                start = time.perf_counter()
                _ = models.call_price_batch(spots, k, t, r, sigma)
                times.append(time.perf_counter() - start)
            qf_time = float(np.median(times))
        else:
            qf_time = float("inf")
        results["quantforge"] = qf_time

        # NumPy Batch
        # Warmup (十分なウォームアップで安定した測定)
        for _ in range(20):
            _ = black_scholes_numpy_batch(spots[: min(100, size)], k, t, r, sigma)

        # Measure
        times = []
        for _ in range(n_runs):
            start = time.perf_counter()
            _ = black_scholes_numpy_batch(spots, k, t, r, sigma)
            times.append(time.perf_counter() - start)
        np_time = np.median(times)
        results["numpy_batch"] = np_time

        # Pure Python (小さいサイズのみ)
        if size <= 1000:
            # Warmup
            for _ in range(3):  # Pure Pythonは遅いので少なめ
                _ = black_scholes_pure_python_batch(spots_list[: min(10, size)], k, t, r, sigma)

            # Measure
            times = []
            py_runs = min(n_runs // 10, 20) if size <= 100 else min(n_runs // 20, 10)
            for _ in range(py_runs):  # Pure Pythonは遅いので回数制限
                start = time.perf_counter()
                _ = black_scholes_pure_python_batch(spots_list, k, t, r, sigma)
                times.append(time.perf_counter() - start)
            py_time = np.median(times)
            results["pure_python"] = py_time
            results["speedup_vs_pure_python"] = py_time / qf_time

        # 相対性能とスループット
        results["speedup_vs_numpy"] = np_time / qf_time
        results["throughput_qf"] = size / qf_time
        results["throughput_np"] = size / np_time

        return results

    def run_all(self) -> dict[str, Any]:
        """全ベンチマークを実行."""
        print("🚀 ベンチマーク開始...")

        results: dict[str, Any] = {"system_info": self.get_system_info(), "single": {}, "batch": []}

        print("📊 単一計算ベンチマーク実行中...")
        results["single"] = self.benchmark_single()

        print("📊 バッチ処理ベンチマーク実行中...")
        for size in [100, 1000, 10000, 100000, 1000000]:
            print(f"  - サイズ {size:,} ...")
            results["batch"].append(self.benchmark_batch(size))

        # 結果を構造化データとして保存
        from benchmarks.analysis.save import save_benchmark_result

        save_benchmark_result(results)

        print("✅ ベンチマーク完了")
        return results


def main() -> None:
    """Main entry point for comparison benchmarks."""
    runner = BenchmarkRunner()
    results = runner.run_all()

    # 簡易結果表示
    print("\n=== 結果サマリ ===")
    single = results["single"]
    print(f"単一計算: QuantForgeはPure Pythonより{single['speedup_vs_pure_python']:.0f}倍高速")

    batch_1m = next((b for b in results["batch"] if b["size"] == 1000000), None)
    if batch_1m:
        print(f"100万件バッチ: QuantForgeはNumPyより{batch_1m['speedup_vs_numpy']:.1f}倍高速")
        print(f"スループット: {batch_1m['throughput_qf'] / 1e6:.1f}M ops/sec")


if __name__ == "__main__":
    main()
