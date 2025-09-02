"""
小バッチ最適化のPython側実装サンプル
"""

import time

import numpy as np
import quantforge as qf
from numba import jit

# Phase 3: Bindings層の最適化


class OptimizedBlackScholes:
    """バッチサイズ適応型のBlack-Scholesラッパー"""

    # 閾値定数
    MICRO_BATCH_THRESHOLD = 200
    SMALL_BATCH_THRESHOLD = 1000
    MEDIUM_BATCH_THRESHOLD = 10000

    def __init__(self):
        self.profiler = PerformanceProfiler()

    def call_price_batch(
        self, spots: np.ndarray, strikes: np.ndarray, times: np.ndarray, rates: np.ndarray, sigmas: np.ndarray
    ) -> np.ndarray:
        """バッチサイズに応じた最適化処理"""

        size = len(spots)
        start = time.perf_counter()

        if size <= self.MICRO_BATCH_THRESHOLD:
            # マイクロバッチ: Python側でループ展開
            result = self._process_micro_batch(spots, strikes, times, rates, sigmas)

        elif size <= self.SMALL_BATCH_THRESHOLD:
            # 小バッチ: Numba JITで高速化
            result = self._process_small_batch_jit(spots, strikes, times, rates, sigmas)

        elif size <= self.MEDIUM_BATCH_THRESHOLD:
            # 中バッチ: チャンク処理
            result = self._process_medium_batch(spots, strikes, times, rates, sigmas)

        else:
            # 大バッチ: フル並列化
            result = qf.black_scholes.call_price_batch(
                spots=spots, strikes=strikes, times=times, rates=rates, sigmas=sigmas
            )

        elapsed = time.perf_counter() - start
        self.profiler.record(size, elapsed)

        return result

    def _process_micro_batch(
        self, spots: np.ndarray, strikes: np.ndarray, times: np.ndarray, rates: np.ndarray, sigmas: np.ndarray
    ) -> np.ndarray:
        """マイクロバッチ専用処理（ループ展開）"""

        size = len(spots)
        results = np.empty(size)

        # 4要素ずつ処理（ループ展開）
        i = 0
        while i + 3 < size:
            # 4つの計算を同時に実行
            results[i] = qf.black_scholes.call_price(spots[i], strikes[i], times[i], rates[i], sigmas[i])
            results[i + 1] = qf.black_scholes.call_price(
                spots[i + 1], strikes[i + 1], times[i + 1], rates[i + 1], sigmas[i + 1]
            )
            results[i + 2] = qf.black_scholes.call_price(
                spots[i + 2], strikes[i + 2], times[i + 2], rates[i + 2], sigmas[i + 2]
            )
            results[i + 3] = qf.black_scholes.call_price(
                spots[i + 3], strikes[i + 3], times[i + 3], rates[i + 3], sigmas[i + 3]
            )
            i += 4

        # 残りの要素
        while i < size:
            results[i] = qf.black_scholes.call_price(spots[i], strikes[i], times[i], rates[i], sigmas[i])
            i += 1

        return results

    @staticmethod
    @jit(nopython=True, parallel=False, cache=True)
    def _process_small_batch_jit(
        spots: np.ndarray, strikes: np.ndarray, times: np.ndarray, rates: np.ndarray, sigmas: np.ndarray
    ) -> np.ndarray:
        """Numba JITによる小バッチ処理"""

        size = len(spots)
        results = np.empty(size)

        for i in range(size):
            # Black-Scholes formula (inlined)
            sqrt_t = np.sqrt(times[i])
            d1 = (np.log(spots[i] / strikes[i]) + (rates[i] + sigmas[i] ** 2 / 2) * times[i]) / (sigmas[i] * sqrt_t)
            d2 = d1 - sigmas[i] * sqrt_t

            # 標準正規分布の累積分布関数（簡易近似）
            norm_cdf_d1 = 0.5 * (1 + np.tanh(0.7978845608 * d1))
            norm_cdf_d2 = 0.5 * (1 + np.tanh(0.7978845608 * d2))

            results[i] = spots[i] * norm_cdf_d1 - strikes[i] * np.exp(-rates[i] * times[i]) * norm_cdf_d2

        return results

    def _process_medium_batch(
        self, spots: np.ndarray, strikes: np.ndarray, times: np.ndarray, rates: np.ndarray, sigmas: np.ndarray
    ) -> np.ndarray:
        """中規模バッチのチャンク処理"""

        chunk_size = 256  # L1キャッシュ最適化サイズ
        size = len(spots)
        results = np.empty(size)

        for start in range(0, size, chunk_size):
            end = min(start + chunk_size, size)

            # チャンク単位で処理
            chunk_results = qf.black_scholes.call_price_batch(
                spots=spots[start:end],
                strikes=strikes[start:end],
                times=times[start:end],
                rates=rates[start:end],
                sigmas=sigmas[start:end],
            )

            results[start:end] = chunk_results

        return results


class PerformanceProfiler:
    """実行時性能プロファイラー"""

    def __init__(self, history_size: int = 100):
        self.history = []
        self.history_size = history_size
        self.cost_per_element = 10e-9  # 初期値: 10ns
        self.parallel_overhead = 5e-6  # 初期値: 5μs

    def record(self, size: int, elapsed: float):
        """実行時間を記録"""
        self.history.append((size, elapsed))

        # 履歴サイズを制限
        if len(self.history) > self.history_size:
            self.history.pop(0)

        # 統計を更新
        if len(self.history) >= 10:
            self._update_statistics()

    def _update_statistics(self):
        """線形回帰で性能特性を推定"""

        # 小バッチデータで要素あたりコストを推定
        small_batch_data = [(s, t) for s, t in self.history if s < 1000]

        if len(small_batch_data) >= 5:
            sizes = np.array([s for s, _ in small_batch_data])
            times = np.array([t for _, t in small_batch_data])

            # 最小二乗法
            A = np.vstack([sizes, np.ones(len(sizes))]).T
            slope, intercept = np.linalg.lstsq(A, times, rcond=None)[0]

            self.cost_per_element = max(slope, 1e-9)

        # 並列化オーバーヘッドを推定
        medium_batch_data = [(s, t) for s, t in self.history if 1000 <= s <= 10000]

        if len(medium_batch_data) >= 5:
            overhead_estimates = []

            for size, actual_time in medium_batch_data:
                expected_sequential = size * self.cost_per_element
                # 簡易的な並列化効果の推定
                cpu_cores = 8  # 仮定
                expected_parallel = expected_sequential / cpu_cores
                overhead = actual_time - expected_parallel

                if overhead > 0:
                    overhead_estimates.append(overhead)

            if overhead_estimates:
                # 中央値を採用
                self.parallel_overhead = np.median(overhead_estimates)

    def should_parallelize(self, size: int) -> bool:
        """並列化すべきかを判定"""

        sequential_cost = size * self.cost_per_element
        cpu_cores = 8  # 仮定
        parallel_cost = (size / cpu_cores) * self.cost_per_element + self.parallel_overhead

        # 20%以上の改善が見込める場合のみ並列化
        return parallel_cost < sequential_cost * 0.8

    def get_optimal_batch_size(self) -> int:
        """最適なバッチサイズを推定"""

        if self.parallel_overhead > 0 and self.cost_per_element > 0:
            # 並列化が有効になる最小サイズを計算
            # sequential_cost = parallel_cost を解く
            cpu_cores = 8
            optimal = self.parallel_overhead / (self.cost_per_element * (1 - 1 / cpu_cores))
            return int(optimal * 1.2)  # 20%のマージン

        return 1000  # デフォルト値


def benchmark_optimization():
    """最適化効果のベンチマーク"""

    import pandas as pd

    # テストサイズ
    sizes = [10, 50, 100, 200, 500, 1000, 5000, 10000]

    # 標準実装
    standard = qf.black_scholes

    # 最適化実装
    optimized = OptimizedBlackScholes()

    results = []

    for size in sizes:
        # テストデータ生成
        np.random.seed(42)
        spots = np.random.uniform(80, 120, size)
        strikes = np.full(size, 100.0)
        times = np.full(size, 1.0)
        rates = np.full(size, 0.05)
        sigmas = np.random.uniform(0.15, 0.35, size)

        # 標準実装の測定
        start = time.perf_counter()
        for _ in range(100):
            _ = standard.call_price_batch(spots=spots, strikes=strikes, times=times, rates=rates, sigmas=sigmas)
        standard_time = (time.perf_counter() - start) / 100

        # 最適化実装の測定
        start = time.perf_counter()
        for _ in range(100):
            _ = optimized.call_price_batch(spots, strikes, times, rates, sigmas)
        optimized_time = (time.perf_counter() - start) / 100

        # NumPy実装の測定（比較用）
        from scipy.stats import norm

        start = time.perf_counter()
        for _ in range(100):
            sqrt_t = np.sqrt(times)
            d1 = (np.log(spots / strikes) + (rates + sigmas**2 / 2) * times) / (sigmas * sqrt_t)
            d2 = d1 - sigmas * sqrt_t
            _ = spots * norm.cdf(d1) - strikes * np.exp(-rates * times) * norm.cdf(d2)
        numpy_time = (time.perf_counter() - start) / 100

        results.append(
            {
                "size": size,
                "standard_μs": standard_time * 1e6,
                "optimized_μs": optimized_time * 1e6,
                "numpy_μs": numpy_time * 1e6,
                "speedup_vs_standard": standard_time / optimized_time,
                "speedup_vs_numpy": numpy_time / optimized_time,
                "standard_throughput": size / standard_time,
                "optimized_throughput": size / optimized_time,
            }
        )

    df = pd.DataFrame(results)

    print("=== 小バッチ最適化ベンチマーク結果 ===\n")
    print(df.to_string(index=False))

    print("\n=== 100件バッチでの改善 ===")
    row_100 = df[df["size"] == 100].iloc[0]
    print(f"標準実装: {row_100['standard_μs']:.2f}μs")
    print(f"最適化版: {row_100['optimized_μs']:.2f}μs")
    print(f"NumPy: {row_100['numpy_μs']:.2f}μs")
    print(f"改善率: {row_100['speedup_vs_standard']:.2f}x")
    print(f"NumPy比: {row_100['speedup_vs_numpy']:.2f}x")

    # プロファイラーの統計を表示
    print("\n=== プロファイラー統計 ===")
    print(f"要素あたりコスト: {optimized.profiler.cost_per_element * 1e9:.2f}ns")
    print(f"並列化オーバーヘッド: {optimized.profiler.parallel_overhead * 1e6:.2f}μs")
    print(f"最適バッチサイズ: {optimized.profiler.get_optimal_batch_size()}")

    return df


if __name__ == "__main__":
    # ベンチマーク実行
    results = benchmark_optimization()

    # 結果をプロット
    try:
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # 実行時間
        ax1.plot(results["size"], results["standard_μs"], "o-", label="Standard")
        ax1.plot(results["size"], results["optimized_μs"], "s-", label="Optimized")
        ax1.plot(results["size"], results["numpy_μs"], "^-", label="NumPy")
        ax1.set_xlabel("Batch Size")
        ax1.set_ylabel("Execution Time (μs)")
        ax1.set_xscale("log")
        ax1.set_yscale("log")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_title("Execution Time Comparison")

        # スピードアップ
        ax2.plot(results["size"], results["speedup_vs_standard"], "o-", label="vs Standard")
        ax2.plot(results["size"], results["speedup_vs_numpy"], "s-", label="vs NumPy")
        ax2.axhline(y=1.0, color="k", linestyle="--", alpha=0.3)
        ax2.set_xlabel("Batch Size")
        ax2.set_ylabel("Speedup")
        ax2.set_xscale("log")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_title("Speedup Ratio")

        plt.tight_layout()
        plt.savefig("small_batch_optimization.png", dpi=150)
        print("\n図を small_batch_optimization.png に保存しました")

    except ImportError:
        print("\nmatplotlibがインストールされていないため、グラフは作成されませんでした")
