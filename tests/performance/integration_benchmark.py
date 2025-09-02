"""エンドツーエンド統合ベンチマーク

実際のユースケースに基づく統合性能測定:
- ポートフォリオ価格計算
- リスク指標計算
- 大規模バッチ処理
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import quantforge as qf


class IntegrationBenchmark:
    """統合レベルのベンチマーク"""

    def __init__(self):
        self.layer = "integration"

    def benchmark_portfolio_valuation(self, portfolio_size: int = 10000) -> dict[str, Any]:
        """ポートフォリオ全体の評価"""

        # リアルなポートフォリオデータを生成
        np.random.seed(42)  # 再現性のため

        # 多様なオプションパラメータ
        spots = np.random.uniform(50, 200, portfolio_size)
        strikes = spots * np.random.uniform(0.8, 1.2, portfolio_size)
        times = np.random.uniform(0.1, 3.0, portfolio_size)
        rates = np.random.uniform(0.01, 0.06, portfolio_size)
        sigmas = np.random.uniform(0.1, 0.5, portfolio_size)
        is_calls = np.random.choice([True, False], portfolio_size)

        results = {}

        # 価格計算
        start = time.perf_counter()
        call_mask = is_calls
        put_mask = ~is_calls

        prices = np.zeros(portfolio_size)
        if np.any(call_mask):
            prices[call_mask] = qf.black_scholes.call_price_batch(
                spots=spots[call_mask],
                strikes=strikes[call_mask],
                times=times[call_mask],
                rates=rates[call_mask],
                sigmas=sigmas[call_mask],
            )

        if np.any(put_mask):
            prices[put_mask] = qf.black_scholes.put_price_batch(
                spots=spots[put_mask],
                strikes=strikes[put_mask],
                times=times[put_mask],
                rates=rates[put_mask],
                sigmas=sigmas[put_mask],
            )

        end = time.perf_counter()
        results["valuation_time"] = end - start

        # ポートフォリオ統計
        results["total_value"] = np.sum(prices)
        results["mean_price"] = np.mean(prices)
        results["portfolio_size"] = portfolio_size
        results["throughput"] = portfolio_size / results["valuation_time"]

        return results

    def benchmark_risk_calculation(self, positions: int = 5000) -> dict[str, Any]:
        """リスク指標の計算"""

        # テストデータ
        spots = np.random.uniform(80, 120, positions)
        strikes = np.full(positions, 100.0)
        times = np.random.uniform(0.1, 2.0, positions)
        rates = np.full(positions, 0.05)
        sigmas = np.random.uniform(0.15, 0.35, positions)

        results = {}

        # Greeks計算（全リスク指標）
        start = time.perf_counter()

        # Call options
        call_greeks = qf.black_scholes.greeks_batch(
            spots=spots, strikes=strikes, times=times, rates=rates, sigmas=sigmas, is_calls=True
        )

        # Put options
        put_greeks = qf.black_scholes.greeks_batch(
            spots=spots, strikes=strikes, times=times, rates=rates, sigmas=sigmas, is_calls=False
        )

        end = time.perf_counter()
        results["greeks_time"] = end - start

        # ポートフォリオレベルのリスク集計
        start = time.perf_counter()

        # デルタ集計
        total_delta = np.sum(call_greeks["delta"]) + np.sum(put_greeks["delta"])
        # ガンマ集計
        total_gamma = np.sum(call_greeks["gamma"]) + np.sum(put_greeks["gamma"])
        # ベガ集計
        total_vega = np.sum(call_greeks["vega"]) + np.sum(put_greeks["vega"])

        end = time.perf_counter()
        results["aggregation_time"] = end - start

        results["total_time"] = results["greeks_time"] + results["aggregation_time"]
        results["positions"] = positions
        results["throughput"] = positions * 2 / results["total_time"]  # calls + puts

        return results

    def benchmark_scenario_analysis(self, scenarios: int = 100) -> dict[str, Any]:
        """シナリオ分析（ストレステスト）"""

        # ベースケース
        base_spot = 100.0
        k = 100.0
        t = 1.0
        r = 0.05
        base_sigma = 0.2

        # シナリオ生成
        spot_shocks = np.linspace(0.7, 1.3, scenarios) * base_spot
        vol_shocks = np.linspace(0.5, 1.5, scenarios) * base_sigma

        results = {}

        # シナリオ計算
        start = time.perf_counter()

        scenario_results = []
        for spot in spot_shocks:
            for vol in vol_shocks:
                price = qf.black_scholes.call_price(spot, k, t, r, vol)
                scenario_results.append(price)

        end = time.perf_counter()
        results["calculation_time"] = end - start

        results["total_scenarios"] = len(scenario_results)
        results["scenarios_per_second"] = results["total_scenarios"] / results["calculation_time"]
        results["min_price"] = np.min(scenario_results)
        results["max_price"] = np.max(scenario_results)
        results["price_range"] = results["max_price"] - results["min_price"]

        return results

    def benchmark_implied_volatility_surface(self, grid_size: int = 50) -> dict[str, Any]:
        """インプライドボラティリティサーフェス構築"""

        # グリッド生成
        spot = 100.0
        strikes = np.linspace(70, 130, grid_size)
        maturities = np.linspace(0.1, 3.0, grid_size)

        # マーケット価格をシミュレート（実際はマーケットデータ）
        market_prices = np.zeros((grid_size, grid_size))
        for i, k in enumerate(strikes):
            for j, t in enumerate(maturities):
                # ATMからの距離に応じてvolを調整（スマイル効果）
                moneyness = np.log(spot / k)
                vol_smile = 0.2 + 0.5 * moneyness**2
                market_prices[i, j] = qf.black_scholes.call_price(spot, k, t, 0.05, vol_smile)

        results = {}

        # IV計算
        start = time.perf_counter()

        iv_surface = np.zeros((grid_size, grid_size))
        for i, k in enumerate(strikes):
            for j, t in enumerate(maturities):
                try:
                    iv = qf.black_scholes.implied_volatility(
                        price=market_prices[i, j], s=spot, k=k, t=t, r=0.05, is_call=True
                    )
                    iv_surface[i, j] = iv
                except:
                    iv_surface[i, j] = np.nan

        end = time.perf_counter()
        results["surface_time"] = end - start

        results["grid_points"] = grid_size * grid_size
        results["points_per_second"] = results["grid_points"] / results["surface_time"]
        results["valid_points"] = np.sum(~np.isnan(iv_surface))
        results["convergence_rate"] = results["valid_points"] / results["grid_points"]

        return results

    def benchmark_batch_sizes(self) -> dict[str, Any]:
        """異なるバッチサイズでの性能測定"""

        batch_sizes = [100, 1000, 10000, 100000, 1000000]
        results = {}

        for size in batch_sizes:
            # データ生成
            spots = np.random.uniform(80, 120, size)
            strikes = np.full(size, 100.0)
            times = np.full(size, 1.0)
            rates = np.full(size, 0.05)
            sigmas = np.full(size, 0.2)

            # 測定
            start = time.perf_counter()
            _ = qf.black_scholes.call_price_batch(spots=spots, strikes=strikes, times=times, rates=rates, sigmas=sigmas)
            end = time.perf_counter()

            elapsed = end - start
            results[f"size_{size}"] = {
                "time": elapsed,
                "throughput": size / elapsed,
                "ns_per_option": elapsed * 1e9 / size,
            }

        return results

    def run_all_benchmarks(self) -> dict[str, Any]:
        """全ベンチマークを実行"""

        print("Running Integration Benchmarks...")

        results = {
            "version": "v2.0.0",
            "layer": self.layer,
            "metadata": {"timestamp": datetime.now().isoformat(), "test_type": "end_to_end"},
            "benchmarks": {
                "portfolio_valuation": self.benchmark_portfolio_valuation(),
                "risk_calculation": self.benchmark_risk_calculation(),
                "scenario_analysis": self.benchmark_scenario_analysis(),
                "iv_surface": self.benchmark_implied_volatility_surface(),
                "batch_sizes": self.benchmark_batch_sizes(),
            },
        }

        return results

    def save_results(self, results: dict[str, Any]):
        """結果を保存"""

        results_dir = Path("benchmark_results/integration")
        results_dir.mkdir(parents=True, exist_ok=True)

        # NumPy型をPython型に変換
        results = self._convert_numpy_types(results)

        # latest.jsonとして保存
        latest_path = results_dir / "latest.json"
        with open(latest_path, "w") as f:
            json.dump(results, f, indent=2)

        # historyにも保存
        history_dir = results_dir / "history"
        history_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_path = history_dir / f"integration_{timestamp}.json"
        with open(history_path, "w") as f:
            json.dump(results, f, indent=2)

        print(f"Results saved to {latest_path} and {history_path}")

    def _convert_numpy_types(self, obj: Any) -> Any:
        """NumPy型を再帰的にPython型に変換"""
        if isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj


if __name__ == "__main__":
    benchmark = IntegrationBenchmark()
    results = benchmark.run_all_benchmarks()
    benchmark.save_results(results)

    # サマリー表示
    print("\n=== Integration Benchmark Summary ===")
    portfolio = results["benchmarks"]["portfolio_valuation"]
    print(f"Portfolio valuation ({portfolio['portfolio_size']} options): {portfolio['throughput']:.0f} ops/sec")

    risk = results["benchmarks"]["risk_calculation"]
    print(f"Risk calculation ({risk['positions']} positions): {risk['throughput']:.0f} greeks/sec")

    scenarios = results["benchmarks"]["scenario_analysis"]
    print(f"Scenario analysis: {scenarios['scenarios_per_second']:.0f} scenarios/sec")

    iv = results["benchmarks"]["iv_surface"]
    print(f"IV surface ({iv['grid_points']} points): {iv['points_per_second']:.0f} points/sec")

    # バッチサイズ別のスループット
    print("\nBatch size performance:")
    for size_key, perf in results["benchmarks"]["batch_sizes"].items():
        size = size_key.replace("size_", "")
        print(f"  {size:>7} options: {perf['throughput']:.0f} ops/sec ({perf['ns_per_option']:.1f} ns/option)")
