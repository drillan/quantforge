"""包括的インプライドボラティリティベンチマーク.

全モデル（Black-Scholes, Black76, Merton, American）のIV計算性能を測定。
単一計算とバッチ処理の両方で、Python基準実装との比較を実施。
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

try:
    from benchmarks.iv_baseline import (
        american_iv_scipy,
        black76_iv_scipy,
        implied_volatility_batch_newton,
        implied_volatility_batch_scipy,
        implied_volatility_newton,
        implied_volatility_scipy,
        merton_iv_scipy,
    )
except ImportError:
    from iv_baseline import (  # type: ignore[no-redef]
        american_iv_scipy,
        black76_iv_scipy,
        implied_volatility_batch_newton,
        implied_volatility_batch_scipy,
        implied_volatility_newton,
        implied_volatility_scipy,
        merton_iv_scipy,
    )


class ComprehensiveIVBenchmark:
    """包括的IV計算ベンチマーク."""

    def __init__(self, warmup_runs: int = 100, measure_runs: int = 1000):
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

            self.models: dict[str, Any] = {
                "black_scholes": models,
                "black76": models.black76,
                "merton": models.merton,
                "american": models.american,
            }
        except ImportError as e:
            print(f"Warning: QuantForge models not available: {e}")
            self.models = {}

    def benchmark_single_iv_all_models(self) -> dict[str, Any]:
        """全モデルで単一IV計算ベンチマーク.

        Returns:
            モデル別のベンチマーク結果
        """
        if not self.models:
            return {"error": "QuantForge models not available"}

        results = {}

        # Black-Scholes
        if "black_scholes" in self.models:
            model = self.models["black_scholes"]
            s, k, t, r = 100.0, 100.0, 1.0, 0.05
            true_sigma = 0.2

            # 価格を計算
            price = model.call_price(s, k, t, r, true_sigma)

            # QuantForge実装
            times_qf = []
            for _ in range(self.measure_runs):
                start = time.perf_counter()
                model.implied_volatility(price, s, k, t, r, is_call=True)
                times_qf.append(time.perf_counter() - start)
            qf_time = np.median(times_qf)

            # SciPy Brent実装
            times_scipy = []
            for _ in range(self.measure_runs):
                start = time.perf_counter()
                implied_volatility_scipy(price, s, k, t, r, is_call=True)
                times_scipy.append(time.perf_counter() - start)
            scipy_time = np.median(times_scipy)

            # Newton-Raphson実装
            times_newton = []
            for _ in range(min(self.measure_runs, 100)):  # Newton法は遅いので少なめ
                start = time.perf_counter()
                implied_volatility_newton(price, s, k, t, r, is_call=True)
                times_newton.append(time.perf_counter() - start)
            newton_time = np.median(times_newton)

            results["black_scholes"] = {
                "quantforge_us": qf_time * 1e6,
                "scipy_us": scipy_time * 1e6,
                "newton_us": newton_time * 1e6,
                "speedup_vs_scipy": scipy_time / qf_time,
                "speedup_vs_newton": newton_time / qf_time,
            }

        # Black76
        if "black76" in self.models:
            model = self.models["black76"]
            f, k, t, r = 100.0, 100.0, 1.0, 0.05
            true_sigma = 0.2

            # 価格を計算
            price = model.call_price(f, k, t, r, true_sigma)

            # QuantForge実装
            times_qf = []
            for _ in range(self.measure_runs):
                start = time.perf_counter()
                model.implied_volatility(price, f, k, t, r, is_call=True)
                times_qf.append(time.perf_counter() - start)
            qf_time = np.median(times_qf)

            # SciPy実装
            times_scipy = []
            for _ in range(self.measure_runs):
                start = time.perf_counter()
                black76_iv_scipy(price, f, k, t, r, is_call=True)
                times_scipy.append(time.perf_counter() - start)
            scipy_time = np.median(times_scipy)

            results["black76"] = {
                "quantforge_us": qf_time * 1e6,
                "scipy_us": scipy_time * 1e6,
                "speedup": scipy_time / qf_time,
            }

        # Merton
        if "merton" in self.models:
            model = self.models["merton"]
            s, k, t, r, q = 100.0, 100.0, 1.0, 0.05, 0.02
            true_sigma = 0.2

            # 価格を計算
            price = model.call_price(s, k, t, r, q, true_sigma)

            # QuantForge実装
            times_qf = []
            for _ in range(self.measure_runs):
                start = time.perf_counter()
                model.implied_volatility(price, s, k, t, r, q, is_call=True)
                times_qf.append(time.perf_counter() - start)
            qf_time = np.median(times_qf)

            # SciPy実装
            times_scipy = []
            for _ in range(self.measure_runs):
                start = time.perf_counter()
                merton_iv_scipy(price, s, k, t, r, q, is_call=True)
                times_scipy.append(time.perf_counter() - start)
            scipy_time = np.median(times_scipy)

            results["merton"] = {
                "quantforge_us": qf_time * 1e6,
                "scipy_us": scipy_time * 1e6,
                "speedup": scipy_time / qf_time,
            }

        # American
        if "american" in self.models:
            model = self.models["american"]
            s, k, t, r, q = 100.0, 100.0, 1.0, 0.05, 0.02
            true_sigma = 0.2

            # 価格を計算
            price = model.call_price(s, k, t, r, q, true_sigma)

            # QuantForge実装
            times_qf = []
            for _ in range(min(self.measure_runs, 100)):  # Americanは遅いので少なめ
                start = time.perf_counter()
                model.implied_volatility(price, s, k, t, r, q, is_call=True)
                times_qf.append(time.perf_counter() - start)
            qf_time = np.median(times_qf)

            # SciPy実装（簡略版）
            times_scipy = []
            for _ in range(min(self.measure_runs, 100)):
                start = time.perf_counter()
                american_iv_scipy(price, s, k, t, r, q, is_call=True)
                times_scipy.append(time.perf_counter() - start)
            scipy_time = np.median(times_scipy)

            results["american"] = {
                "quantforge_us": qf_time * 1e6,
                "scipy_us": scipy_time * 1e6,
                "speedup": scipy_time / qf_time,
            }

        return results

    def benchmark_batch_iv_all_models(self, size: int) -> dict[str, Any]:
        """全モデルでバッチIV計算ベンチマーク.

        Args:
            size: バッチサイズ

        Returns:
            モデル別のバッチ処理ベンチマーク結果
        """
        if not self.models:
            return {"error": "QuantForge models not available"}

        results = {}

        # 共通データ生成
        np.random.seed(42)
        spots = np.random.uniform(80, 120, size)
        strikes = np.random.uniform(80, 120, size)
        times = np.random.uniform(0.1, 2.0, size)
        rates = np.full(size, 0.05)
        true_sigmas = np.random.uniform(0.1, 0.4, size)
        is_calls = np.random.choice([True, False], size)

        # Black-Scholes
        if "black_scholes" in self.models:
            model = self.models["black_scholes"]

            # 価格を計算
            prices = np.array(
                [
                    model.call_price(s, k, t, r, sigma) if is_call else model.put_price(s, k, t, r, sigma)
                    for s, k, t, r, sigma, is_call in zip(
                        spots, strikes, times, rates, true_sigmas, is_calls, strict=False
                    )
                ]
            )

            # QuantForge バッチ処理
            if hasattr(model, "implied_volatility_batch"):
                start = time.perf_counter()
                model.implied_volatility_batch(prices, spots, strikes, times, rates, is_calls)
                qf_time = time.perf_counter() - start
            else:
                qf_time = None

            # SciPy バッチ処理（小サイズのみ）
            if size <= 1000:
                start = time.perf_counter()
                implied_volatility_batch_scipy(prices, spots, strikes, times, rates, is_calls)
                scipy_time = time.perf_counter() - start
            else:
                scipy_time = None

            # Newton-Raphson バッチ処理（小サイズのみ）
            if size <= 100:
                start = time.perf_counter()
                implied_volatility_batch_newton(prices, spots, strikes, times, rates, is_calls)
                newton_time = time.perf_counter() - start
            else:
                newton_time = None

            results["black_scholes"] = {
                "size": size,
                "quantforge_ms": qf_time * 1000 if qf_time else None,
                "scipy_ms": scipy_time * 1000 if scipy_time else None,
                "newton_ms": newton_time * 1000 if newton_time else None,
                "speedup_vs_scipy": scipy_time / qf_time if scipy_time and qf_time else None,
                "speedup_vs_newton": newton_time / qf_time if newton_time and qf_time else None,
                "throughput_mops": size / qf_time / 1e6 if qf_time else None,
            }

        # Black76
        if "black76" in self.models:
            model = self.models["black76"]

            # Forward価格として使用
            forwards = spots  # 簡略化のため

            # 価格を計算
            prices = np.array(
                [
                    model.call_price(f, k, t, r, sigma) if is_call else model.put_price(f, k, t, r, sigma)
                    for f, k, t, r, sigma, is_call in zip(
                        forwards, strikes, times, rates, true_sigmas, is_calls, strict=False
                    )
                ]
            )

            # QuantForge バッチ処理
            if hasattr(model, "implied_volatility_batch"):
                start = time.perf_counter()
                model.implied_volatility_batch(prices, forwards, strikes, times, rates, is_calls)
                qf_time = time.perf_counter() - start

                results["black76"] = {
                    "size": size,
                    "quantforge_ms": qf_time * 1000,
                    "throughput_mops": size / qf_time / 1e6,
                }

        # Merton
        if "merton" in self.models:
            model = self.models["merton"]

            # 配当利回り追加
            q_values = np.full(size, 0.02)

            # 価格を計算
            prices = np.array(
                [
                    model.call_price(s, k, t, r, q, sigma) if is_call else model.put_price(s, k, t, r, q, sigma)
                    for s, k, t, r, q, sigma, is_call in zip(
                        spots, strikes, times, rates, q_values, true_sigmas, is_calls, strict=False
                    )
                ]
            )

            # QuantForge バッチ処理
            if hasattr(model, "implied_volatility_batch"):
                start = time.perf_counter()
                model.implied_volatility_batch(prices, spots, strikes, times, rates, q_values, is_calls)
                qf_time = time.perf_counter() - start
            else:
                qf_time = None

            # SciPy バッチ処理（小サイズのみ）
            if size <= 100:
                start = time.perf_counter()
                implied_volatility_batch_scipy(prices, spots, strikes, times, rates, is_calls)
                scipy_time = time.perf_counter() - start
            else:
                scipy_time = None

            results["merton"] = {
                "size": size,
                "quantforge_ms": qf_time * 1000 if qf_time else None,
                "scipy_ms": scipy_time * 1000 if scipy_time else None,
                "speedup_vs_scipy": scipy_time / qf_time if scipy_time and qf_time else None,
                "throughput_mops": size / qf_time / 1e6 if qf_time else None,
            }

        # American
        if "american" in self.models:
            model = self.models["american"]

            # 配当利回り
            q_values = np.full(size, 0.02)

            # サイズを制限（Americanは計算が重い）
            test_size = min(size, 1000)

            # 価格を計算
            prices = np.array(
                [
                    model.call_price(s, k, t, r, q, sigma) if is_call else model.put_price(s, k, t, r, q, sigma)
                    for s, k, t, r, q, sigma, is_call in zip(
                        spots[:test_size],
                        strikes[:test_size],
                        times[:test_size],
                        rates[:test_size],
                        q_values[:test_size],
                        true_sigmas[:test_size],
                        is_calls[:test_size],
                        strict=False,
                    )
                ]
            )

            # QuantForge バッチ処理
            if hasattr(model, "implied_volatility_batch"):
                start = time.perf_counter()
                model.implied_volatility_batch(
                    prices,
                    spots[:test_size],
                    strikes[:test_size],
                    times[:test_size],
                    rates[:test_size],
                    q_values[:test_size],
                    is_calls[:test_size],
                )
                qf_time = time.perf_counter() - start

                results["american"] = {
                    "size": test_size,
                    "quantforge_ms": qf_time * 1000,
                    "throughput_mops": test_size / qf_time / 1e6,
                }

        return results

    def run_comprehensive_benchmark(self) -> dict[str, Any]:
        """包括的ベンチマークを実行.

        Returns:
            全ベンチマーク結果
        """
        print("🚀 包括的IVベンチマーク開始...")

        results: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "single_iv": {},
            "batch_iv": [],
        }

        # 単一IV計算ベンチマーク
        print("📊 単一IV計算ベンチマーク実行中...")
        results["single_iv"] = self.benchmark_single_iv_all_models()

        # バッチIV計算ベンチマーク
        print("📊 バッチIV計算ベンチマーク実行中...")
        for size in [100, 1000, 10000, 100000]:
            print(f"  - サイズ {size:,} ...")
            batch_result = self.benchmark_batch_iv_all_models(size)
            results["batch_iv"].append(batch_result)

        # 結果を保存
        self.save_results(results)

        print("✅ ベンチマーク完了")
        return results

    def save_results(self, results: dict[str, Any]) -> None:
        """結果をファイルに保存.

        Args:
            results: ベンチマーク結果
        """
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True, parents=True)

        # 最新結果を保存
        with open(results_dir / "iv_latest.json", "w") as f:
            json.dump(results, f, indent=2)

        # 履歴に追加（JSON Lines形式）
        with open(results_dir / "iv_history.jsonl", "a") as f:
            json.dump(results, f)
            f.write("\n")

        print(f"📝 結果を保存: {results_dir}/iv_latest.json")


def main() -> None:
    """メインエントリーポイント."""
    runner = ComprehensiveIVBenchmark()
    results = runner.run_comprehensive_benchmark()

    # 簡易結果表示
    print("\n=== 結果サマリ ===")

    if "black_scholes" in results["single_iv"]:
        bs = results["single_iv"]["black_scholes"]
        print("Black-Scholes単一IV:")
        print(f"  QuantForge: {bs['quantforge_us']:.1f} μs")
        print(f"  SciPy: {bs['scipy_us']:.1f} μs")
        print(f"  改善率: {bs['speedup_vs_scipy']:.1f}倍")

    # バッチ処理結果（100万件）
    for batch in results["batch_iv"]:
        if "black_scholes" in batch and batch["black_scholes"]["size"] == 100000:
            bs_batch = batch["black_scholes"]
            if bs_batch.get("quantforge_ms"):
                print("\nBlack-Scholes 10万件バッチ:")
                print(f"  QuantForge: {bs_batch['quantforge_ms']:.1f} ms")
                if bs_batch.get("throughput_mops"):
                    print(f"  スループット: {bs_batch['throughput_mops']:.1f} M ops/sec")


if __name__ == "__main__":
    main()
