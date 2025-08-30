"""Black-Scholesの性能比較（リファクタリング版）."""

from functools import partial
from typing import Any

import numpy as np
from quantforge import models

from benchmarks.baseline.python_baseline import (
    black_scholes_numpy_batch,
    black_scholes_pure_python,
    black_scholes_pure_python_batch,
    black_scholes_scipy_single,
)
from benchmarks.common import (
    BenchmarkBase,
    BenchmarkFormatter,
    BenchmarkIO,
    calculate_speedup,
    calculate_throughput,
)


class BlackScholesBenchmark(BenchmarkBase):
    """Black-Scholesベンチマーク実行クラス."""

    def __init__(
        self,
        warmup_runs: int = 100,
        measure_runs: int = 1000,
        batch_sizes: list[int] | None = None,
    ):
        """初期化.

        Args:
            warmup_runs: ウォームアップ実行回数
            measure_runs: 測定実行回数
            batch_sizes: バッチサイズのリスト
        """
        super().__init__(warmup_runs, measure_runs)
        self.batch_sizes = batch_sizes or [100, 1000, 10000, 100000, 1000000]

    def run(self) -> dict[str, Any]:
        """ベンチマークを実行.

        Returns:
            実行結果の辞書
        """
        self.start_benchmark()

        results = {
            "system_info": self.get_system_info(),
            "single": self.benchmark_single(),
            "batch": self.benchmark_batch(),
        }

        return results

    def benchmark_single(self) -> dict[str, Any]:
        """単一計算のベンチマーク."""
        s, k, t, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.2
        results: dict[str, Any] = {}

        # QuantForge (Rust)
        timing = self.time_function(lambda: models.call_price(s, k, t, r, sigma))
        results["quantforge"] = timing.median

        # Pure Python（外部ライブラリなし）
        timing = self.time_function(
            lambda: black_scholes_pure_python(s, k, t, r, sigma),
            warmup_runs=min(self.warmup_runs, 10),  # 遅いので少なめ
            measure_runs=min(self.measure_runs, 100),
        )
        results["pure_python"] = timing.median

        # NumPy+SciPy（一般的な実装）
        timing = self.time_function(lambda: black_scholes_scipy_single(s, k, t, r, sigma))
        results["numpy_scipy"] = timing.median

        # 相対性能計算
        results["speedup_vs_pure_python"] = calculate_speedup(results["pure_python"], results["quantforge"])
        results["speedup_vs_numpy_scipy"] = calculate_speedup(results["numpy_scipy"], results["quantforge"])

        return results

    def benchmark_batch(self) -> list[dict[str, Any]]:
        """バッチ処理のベンチマーク."""
        batch_results = []

        for size in self.batch_sizes:
            print(f"Testing batch size: {size:,}")

            # データ生成
            s = np.full(size, 100.0)
            k = np.random.uniform(80, 120, size)
            t = np.random.uniform(0.1, 2.0, size)
            r = np.full(size, 0.05)
            sigma = np.random.uniform(0.1, 0.5, size)

            result: dict[str, Any] = {"size": size}

            # QuantForge (Rust)
            # functools.partialを使用してバインディング問題を解決
            qf_func = partial(
                lambda _d, s, k, t, r, sigma: models.call_price_batch(s, k, t, r, sigma),
                s=s,
                k=k,
                t=t,
                r=r,
                sigma=sigma,
            )
            timing = self.time_batch_function(
                qf_func,
                s,  # ダミーデータ（実際はクロージャ内で使用）
            )
            result["quantforge"] = timing.median

            # NumPy（ベクトル化実装）
            np_func = partial(
                lambda _d, s, k, t, r, sigma: black_scholes_numpy_batch(s, k, t, r, sigma),
                s=s,
                k=k,
                t=t,
                r=r,
                sigma=sigma,
            )
            timing = self.time_batch_function(
                np_func,
                s,
            )
            result["numpy_batch"] = timing.median

            # Pure Python（小規模のみ）
            if size <= 1000:
                s_list, k_list, t_list, r_list, sigma_list = (
                    s.tolist(),
                    k.tolist(),
                    t.tolist(),
                    r.tolist(),
                    sigma.tolist(),
                )
                # functools.partialを使用
                batch_func = partial(
                    lambda _d, s_l, k_l, t_l, r_l, sig_l: black_scholes_pure_python_batch(s_l, k_l, t_l, r_l, sig_l),
                    s_l=s_list,
                    k_l=k_list,
                    t_l=t_list,
                    r_l=r_list,
                    sig_l=sigma_list,
                )
                timing = self.time_batch_function(
                    batch_func,  # type: ignore[arg-type]
                    s,
                    warmup_runs=5,
                    measure_runs=10,
                )
                result["pure_python"] = timing.median
                result["speedup_vs_pure_python"] = calculate_speedup(result["pure_python"], result["quantforge"])

            # 相対性能とスループット
            result["speedup_vs_numpy"] = calculate_speedup(result["numpy_batch"], result["quantforge"])
            result["throughput_qf"] = calculate_throughput(size, result["quantforge"])
            result["throughput_np"] = calculate_throughput(size, result["numpy_batch"])

            batch_results.append(result)

        return batch_results


def main() -> dict[str, Any]:
    """メイン実行関数."""
    # ベンチマーク実行
    benchmark = BlackScholesBenchmark()
    results = benchmark.run()

    # 結果保存
    io = BenchmarkIO()
    io.save_result(results)

    # Markdown形式で出力
    formatter = BenchmarkFormatter("Black-Scholes Performance Benchmark")
    markdown = formatter.format_markdown(results)
    print(markdown)

    # CSVエクスポート（オプション）
    # io.export_to_csv()

    return results


if __name__ == "__main__":
    main()
