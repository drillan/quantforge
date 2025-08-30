"""ArrayLike性能測定ベンチマーク.

list, tuple, np.ndarrayの性能差を測定。
Broadcasting機能の効率性も検証。
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

# プロジェクトルートからの相対パスでresultsディレクトリを定義
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = BASE_DIR / "benchmarks" / "results"


class ArrayLikeBenchmark:
    """ArrayLike（list, tuple, ndarray）性能測定."""

    def __init__(self, warmup_runs: int = 10, measure_runs: int = 100):
        """ベンチマークランナーを初期化.

        Args:
            warmup_runs: ウォームアップ実行回数
            measure_runs: 測定実行回数
        """
        self.warmup_runs = warmup_runs
        self.measure_runs = measure_runs

        # QuantForgeモデルのインポート（エラー処理付き）
        try:
            from quantforge import models

            self.black_scholes = models
            self.black76 = models.black76
            self.merton = models.merton
            self.models_available = True
        except ImportError as e:
            print(f"Warning: QuantForge models not available: {e}")
            self.models_available = False

    def benchmark_arraylike_types(self, size: int = 10000) -> dict[str, Any]:
        """異なる配列型での性能比較.

        Args:
            size: テストデータサイズ

        Returns:
            配列型別の性能結果
        """
        if not self.models_available:
            return {"error": "QuantForge models not available"}

        # データ準備
        np.random.seed(42)
        spots_array = np.random.uniform(80, 120, size).astype(np.float64)
        spots_list = spots_array.tolist()
        spots_tuple = tuple(spots_list)

        # 他のパラメータ（スカラー）
        k, t, r = 100.0, 1.0, 0.05
        sigma = 0.2

        results: dict[str, Any] = {"size": size}

        # ウォームアップ
        if hasattr(self.black_scholes, "call_price_batch"):
            for _ in range(self.warmup_runs):
                _ = self.black_scholes.call_price_batch(spots_array[:100], k, t, r, sigma)

        # NumPy配列
        times = []
        for _ in range(self.measure_runs):
            start = time.perf_counter()
            self.black_scholes.call_price_batch(spots_array, k, t, r, sigma)
            times.append(time.perf_counter() - start)
        array_time = np.median(times)
        results["numpy_ms"] = float(array_time * 1000)

        # Python list
        times = []
        for _ in range(self.measure_runs):
            start = time.perf_counter()
            self.black_scholes.call_price_batch(spots_list, k, t, r, sigma)
            times.append(time.perf_counter() - start)
        list_time = np.median(times)
        results["list_ms"] = list_time * 1000

        # Python tuple
        times = []
        for _ in range(self.measure_runs):
            start = time.perf_counter()
            self.black_scholes.call_price_batch(spots_tuple, k, t, r, sigma)
            times.append(time.perf_counter() - start)
        tuple_time = np.median(times)
        results["tuple_ms"] = tuple_time * 1000

        # 相対性能（オーバーヘッド）
        results["list_overhead_pct"] = ((list_time / array_time) - 1) * 100
        results["tuple_overhead_pct"] = ((tuple_time / array_time) - 1) * 100

        # スループット
        results["numpy_throughput_mops"] = size / array_time / 1e6
        results["list_throughput_mops"] = size / list_time / 1e6
        results["tuple_throughput_mops"] = size / tuple_time / 1e6

        return results

    def benchmark_broadcasting(self, size: int = 10000) -> dict[str, Any]:
        """Broadcasting機能の性能測定.

        Args:
            size: テストデータサイズ

        Returns:
            Broadcasting性能結果
        """
        if not self.models_available:
            return {"error": "QuantForge models not available"}

        np.random.seed(42)
        spots = np.random.uniform(80, 120, size).astype(np.float64)
        strikes = np.random.uniform(80, 120, size).astype(np.float64)

        results: dict[str, Any] = {"size": size}

        if not hasattr(self.black_scholes, "call_price_batch"):
            return {"error": "Batch API not available"}

        # ケース1: 全パラメータが配列
        times = []
        full_arrays_t = np.full(size, 1.0, dtype=np.float64)
        full_arrays_r = np.full(size, 0.05, dtype=np.float64)
        full_arrays_sigma = np.full(size, 0.2, dtype=np.float64)

        for _ in range(self.measure_runs):
            start = time.perf_counter()
            self.black_scholes.call_price_batch(spots, strikes, full_arrays_t, full_arrays_r, full_arrays_sigma)
            times.append(time.perf_counter() - start)
        full_array_time = np.median(times)
        results["full_array_ms"] = full_array_time * 1000

        # ケース2: 一部スカラー（Broadcasting利用）
        times = []
        for _ in range(self.measure_runs):
            start = time.perf_counter()
            self.black_scholes.call_price_batch(
                spots,
                strikes,
                1.0,
                0.05,
                0.2,  # t, r, sigmaはスカラー
            )
            times.append(time.perf_counter() - start)
        broadcast_time = np.median(times)
        results["broadcasting_ms"] = broadcast_time * 1000

        # Broadcasting効率性
        results["broadcast_efficiency_pct"] = (full_array_time / broadcast_time - 1) * 100

        # メモリ効率性の推定
        # フル配列: size * 5 * 8 bytes (5配列、各float64)
        # Broadcasting: size * 2 * 8 bytes (2配列のみ)
        full_memory_estimate = size * 5 * 8 / 1024  # KB
        broadcast_memory_estimate = size * 2 * 8 / 1024  # KB
        results["full_array_memory_kb"] = full_memory_estimate
        results["broadcast_memory_kb"] = broadcast_memory_estimate
        results["memory_saving_pct"] = (1 - broadcast_memory_estimate / full_memory_estimate) * 100

        return results

    def benchmark_mixed_types(self, size: int = 1000) -> dict[str, Any]:
        """混合型入力の性能測定.

        異なる型を混在させた場合の性能を測定。

        Args:
            size: テストデータサイズ

        Returns:
            混合型の性能結果
        """
        if not self.models_available:
            return {"error": "QuantForge models not available"}

        np.random.seed(42)
        results: dict[str, Any] = {"size": size}

        # データ準備
        spots_array = np.random.uniform(80, 120, size)
        strikes_list = np.random.uniform(80, 120, size).tolist()
        times_tuple = tuple(np.random.uniform(0.1, 2.0, size))
        rates_scalar = 0.05
        sigmas_array = np.random.uniform(0.1, 0.4, size)

        if not hasattr(self.black_scholes, "call_price_batch"):
            return {"error": "Batch API not available"}

        # 混合型テスト
        times = []
        for _ in range(self.measure_runs):
            start = time.perf_counter()
            self.black_scholes.call_price_batch(
                spots_array,  # numpy array
                strikes_list,  # list
                times_tuple,  # tuple
                rates_scalar,  # scalar
                sigmas_array,  # numpy array
            )
            times.append(time.perf_counter() - start)

        mixed_time = np.median(times)
        results["mixed_types_ms"] = mixed_time * 1000
        results["throughput_mops"] = size / mixed_time / 1e6

        # 全numpy配列との比較
        strikes_array = np.array(strikes_list)
        times_array = np.array(times_tuple)
        rates_array = np.full(size, rates_scalar)

        times = []
        for _ in range(self.measure_runs):
            start = time.perf_counter()
            self.black_scholes.call_price_batch(
                spots_array,
                strikes_array,
                times_array,
                rates_array,
                sigmas_array,
            )
            times.append(time.perf_counter() - start)

        all_array_time = np.median(times)
        results["all_numpy_ms"] = all_array_time * 1000
        results["mixed_overhead_pct"] = ((mixed_time / all_array_time) - 1) * 100

        return results

    def benchmark_different_models(self, size: int = 10000) -> dict[str, Any]:
        """異なるモデルでのArrayLike性能比較.

        Args:
            size: テストデータサイズ

        Returns:
            モデル別のArrayLike性能
        """
        if not self.models_available:
            return {"error": "QuantForge models not available"}

        np.random.seed(42)
        results: dict[str, Any] = {"size": size}

        # 共通データ
        spots_array = np.random.uniform(80, 120, size)
        spots_list = spots_array.tolist()
        k, t, r = 100.0, 1.0, 0.05
        sigma = 0.2

        # Black-Scholes
        if hasattr(self.black_scholes, "call_price_batch"):
            # NumPy配列
            start = time.perf_counter()
            _ = self.black_scholes.call_price_batch(spots_array, k, t, r, sigma)
            bs_array_time = time.perf_counter() - start

            # List
            start = time.perf_counter()
            _ = self.black_scholes.call_price_batch(spots_list, k, t, r, sigma)
            bs_list_time = time.perf_counter() - start

            results["black_scholes"] = {
                "numpy_ms": bs_array_time * 1000,
                "list_ms": bs_list_time * 1000,
                "list_overhead_pct": ((bs_list_time / bs_array_time) - 1) * 100,
            }

        # Black76
        if hasattr(self.black76, "call_price_batch"):
            # Forward価格として使用
            forwards_array = spots_array
            forwards_list = spots_list

            # NumPy配列
            start = time.perf_counter()
            _ = self.black76.call_price_batch(forwards_array, k, t, r, sigma)
            b76_array_time = time.perf_counter() - start

            # List
            start = time.perf_counter()
            _ = self.black76.call_price_batch(forwards_list, k, t, r, sigma)
            b76_list_time = time.perf_counter() - start

            results["black76"] = {
                "numpy_ms": b76_array_time * 1000,
                "list_ms": b76_list_time * 1000,
                "list_overhead_pct": ((b76_list_time / b76_array_time) - 1) * 100,
            }

        # Merton
        if hasattr(self.merton, "call_price_batch"):
            q = 0.02  # 配当利回り

            # NumPy配列
            start = time.perf_counter()
            _ = self.merton.call_price_batch(spots_array, k, t, r, q, sigma)
            merton_array_time = time.perf_counter() - start

            # List
            start = time.perf_counter()
            _ = self.merton.call_price_batch(spots_list, k, t, r, q, sigma)
            merton_list_time = time.perf_counter() - start

            results["merton"] = {
                "numpy_ms": merton_array_time * 1000,
                "list_ms": merton_list_time * 1000,
                "list_overhead_pct": ((merton_list_time / merton_array_time) - 1) * 100,
            }

        return results

    def run_all_benchmarks(self) -> dict[str, Any]:
        """全ArrayLikeベンチマークを実行.

        Returns:
            全ベンチマーク結果
        """
        print("🚀 ArrayLikeベンチマーク開始...")

        results: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "arraylike_types": {},
            "broadcasting": {},
            "mixed_types": {},
            "model_comparison": {},
        }

        # ArrayLike型の性能測定
        print("📊 ArrayLike型性能測定...")
        for size in [1000, 10000, 100000]:
            print(f"  - サイズ {size:,} ...")
            results["arraylike_types"][f"size_{size}"] = self.benchmark_arraylike_types(size)

        # Broadcasting性能測定
        print("📊 Broadcasting性能測定...")
        for size in [1000, 10000, 100000]:
            print(f"  - サイズ {size:,} ...")
            results["broadcasting"][f"size_{size}"] = self.benchmark_broadcasting(size)

        # 混合型性能測定
        print("📊 混合型性能測定...")
        results["mixed_types"] = self.benchmark_mixed_types(10000)

        # モデル別比較
        print("📊 モデル別ArrayLike性能測定...")
        results["model_comparison"] = self.benchmark_different_models(10000)

        # 結果を保存
        self.save_results(results)

        print("✅ ArrayLikeベンチマーク完了")
        return results

    def save_results(self, results: dict[str, Any]) -> None:
        """結果をファイルに保存.

        Args:
            results: ベンチマーク結果
        """
        RESULTS_DIR.mkdir(exist_ok=True, parents=True)

        # 最新結果を保存
        with open(RESULTS_DIR / "arraylike_latest.json", "w") as f:
            json.dump(results, f, indent=2)

        # 履歴に追加
        with open(RESULTS_DIR / "arraylike_history.jsonl", "a") as f:
            json.dump(results, f)
            f.write("\n")

        print(f"📝 結果を保存: {RESULTS_DIR}/arraylike_latest.json")


def main() -> None:
    """メインエントリーポイント."""
    runner = ArrayLikeBenchmark()
    results = runner.run_all_benchmarks()

    # 簡易結果表示
    print("\n=== ArrayLike性能サマリ ===")

    # 10000件での結果表示
    if "size_10000" in results["arraylike_types"]:
        data = results["arraylike_types"]["size_10000"]
        if "numpy_ms" in data:
            print("\n10,000件処理時間:")
            print(f"  NumPy配列: {data['numpy_ms']:.2f} ms")
            print(f"  Python list: {data['list_ms']:.2f} ms (+{data['list_overhead_pct']:.1f}%)")
            print(f"  Python tuple: {data['tuple_ms']:.2f} ms (+{data['tuple_overhead_pct']:.1f}%)")

    # Broadcasting効率性
    if "size_10000" in results["broadcasting"]:
        data = results["broadcasting"]["size_10000"]
        if "broadcast_efficiency_pct" in data:
            print("\nBroadcasting効率性 (10,000件):")
            print(f"  パフォーマンス改善: {data['broadcast_efficiency_pct']:.1f}%")
            print(f"  メモリ削減: {data['memory_saving_pct']:.1f}%")


if __name__ == "__main__":
    main()
