"""実用的なトレーディングシナリオのベンチマーク.

ボラティリティサーフェス構築、ポートフォリオリスク計算など、
実際のトレーディングシステムで使用される計算パターンを測定。
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


class PracticalScenariosBenchmark:
    """実トレーディングシナリオでのベンチマーク."""

    def __init__(self) -> None:
        """ベンチマークランナーを初期化."""
        # QuantForgeモデルのインポート（エラー処理付き）
        try:
            from quantforge import models

            american = models.american
            black76 = models.black76
            black_scholes = models
            merton = models.merton

            self.black_scholes = black_scholes
            self.black76 = black76
            self.merton = merton
            self.american = american
            self.models_available = True
        except ImportError as e:
            print(f"Warning: QuantForge models not available: {e}")
            self.models_available = False

    def _simulate_market_prices_bs(
        self,
        spots: np.ndarray,
        strikes: np.ndarray,
        times: np.ndarray,
        rates: np.ndarray,
        base_vol: float = 0.2,
        vol_smile_factor: float = 0.1,
    ) -> np.ndarray:
        """Black-Scholesモデルの市場価格をシミュレート.

        ボラティリティスマイルを含む現実的な価格を生成。

        Args:
            spots: スポット価格の配列
            strikes: 権利行使価格の配列
            times: 満期までの時間の配列
            rates: 無リスク金利の配列
            base_vol: 基準ボラティリティ
            vol_smile_factor: スマイル効果の強度

        Returns:
            市場価格の配列
        """
        # モンeyネス（K/S）によるボラティリティスマイル
        moneyness = strikes / spots
        smile_adjustment = vol_smile_factor * ((moneyness - 1.0) ** 2)
        implied_vols = base_vol * (1.0 + smile_adjustment)

        # 価格計算
        prices = np.zeros_like(spots)
        for i in range(len(spots)):
            if self.models_available:
                prices[i] = self.black_scholes.call_price(spots[i], strikes[i], times[i], rates[i], implied_vols[i])
            else:
                # 簡易計算（テスト用）
                prices[i] = max(spots[i] - strikes[i], 0) * np.exp(-rates[i] * times[i])

        return prices

    def _simulate_market_prices_merton(
        self,
        spots: np.ndarray,
        strikes: np.ndarray,
        times: np.ndarray,
        rates: np.ndarray,
        dividends: np.ndarray,
        base_vol: float = 0.2,
    ) -> np.ndarray:
        """Mertonモデルの市場価格をシミュレート.

        Args:
            spots: スポット価格の配列
            strikes: 権利行使価格の配列
            times: 満期までの時間の配列
            rates: 無リスク金利の配列
            dividends: 配当利回りの配列
            base_vol: 基準ボラティリティ

        Returns:
            市場価格の配列
        """
        prices = np.zeros_like(spots)
        for i in range(len(spots)):
            if self.models_available:
                prices[i] = self.merton.call_price(spots[i], strikes[i], times[i], rates[i], dividends[i], base_vol)
            else:
                # 簡易計算（テスト用）
                prices[i] = max(spots[i] - strikes[i], 0) * np.exp(-rates[i] * times[i])

        return prices

    def _generate_mixed_portfolio(self, size: int) -> dict[str, np.ndarray]:
        """混合オプションポートフォリオを生成.

        Args:
            size: ポートフォリオサイズ

        Returns:
            ポートフォリオデータ
        """
        np.random.seed(42)

        # 基本パラメータ
        spots = np.random.uniform(80, 120, size)
        strikes = np.random.uniform(70, 130, size)
        times = np.random.uniform(0.1, 2.0, size)
        rates = np.full(size, 0.05)
        dividends = np.random.uniform(0, 0.04, size)

        # オプションタイプをランダムに割り当て
        is_calls = np.random.choice([True, False], size)
        is_american = np.random.choice([True, False], size, p=[0.3, 0.7])  # 30% American

        # 市場価格をシミュレート
        market_prices = np.zeros(size)
        for i in range(size):
            if is_american[i]:
                if self.models_available:
                    if is_calls[i]:
                        market_prices[i] = self.american.call_price(
                            spots[i], strikes[i], times[i], rates[i], dividends[i], 0.2
                        )
                    else:
                        market_prices[i] = self.american.put_price(
                            spots[i], strikes[i], times[i], rates[i], dividends[i], 0.2
                        )
                else:
                    market_prices[i] = (
                        max(strikes[i] - spots[i], 0) if not is_calls[i] else max(spots[i] - strikes[i], 0)
                    )
            else:
                if self.models_available:
                    if is_calls[i]:
                        market_prices[i] = self.merton.call_price(
                            spots[i], strikes[i], times[i], rates[i], dividends[i], 0.2
                        )
                    else:
                        market_prices[i] = self.merton.put_price(
                            spots[i], strikes[i], times[i], rates[i], dividends[i], 0.2
                        )
                else:
                    market_prices[i] = (
                        max(strikes[i] - spots[i], 0) if not is_calls[i] else max(spots[i] - strikes[i], 0)
                    )

        return {
            "spots": spots,
            "strikes": strikes,
            "times": times,
            "rates": rates,
            "dividends": dividends,
            "market_prices": market_prices,
            "is_calls": is_calls,
            "is_american": is_american,
        }

    def volatility_surface_construction(self) -> dict[str, Any]:
        """ボラティリティサーフェス構築（複数モデル比較）.

        Returns:
            ボラティリティサーフェス構築の性能結果
        """
        if not self.models_available:
            return {"error": "QuantForge models not available"}

        # 実際の市場データを模擬
        spot = 100.0
        strikes = np.linspace(70, 130, 100)  # 100ストライク
        maturities = np.array([0.083, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0])  # 10満期
        rate = 0.05

        # メッシュグリッド生成
        K, T = np.meshgrid(strikes, maturities)
        k_flat = K.flatten()
        t_flat = T.flatten()
        s_flat = np.full_like(k_flat, spot)
        r_flat = np.full_like(k_flat, rate)

        results: dict[str, Any] = {}

        # Black-Scholesモデル
        market_prices_bs = self._simulate_market_prices_bs(s_flat, k_flat, t_flat, r_flat)

        if hasattr(self.black_scholes, "implied_volatility_batch"):
            start = time.perf_counter()
            ivs_bs = self.black_scholes.implied_volatility_batch(
                market_prices_bs, s_flat, k_flat, t_flat, r_flat, np.full(len(market_prices_bs), True)
            )
            bs_time = time.perf_counter() - start

            # スマイル形状を構築
            smile_bs = ivs_bs.reshape(10, 100)

            results["black_scholes"] = {
                "time_ms": bs_time * 1000,
                "points": len(market_prices_bs),
                "throughput_kops": len(market_prices_bs) / bs_time / 1000,
                "smile_shape": smile_bs.shape,
                "min_iv": np.nanmin(ivs_bs),
                "max_iv": np.nanmax(ivs_bs),
                "mean_iv": np.nanmean(ivs_bs),
            }

        # Mertonモデル（配当考慮）
        q_flat = np.full_like(k_flat, 0.02)
        market_prices_merton = self._simulate_market_prices_merton(s_flat, k_flat, t_flat, r_flat, q_flat)

        if hasattr(self.merton, "implied_volatility_batch"):
            start = time.perf_counter()
            ivs_merton = self.merton.implied_volatility_batch(
                market_prices_merton, s_flat, k_flat, t_flat, r_flat, q_flat, np.full(len(market_prices_merton), True)
            )
            merton_time = time.perf_counter() - start

            smile_merton = ivs_merton.reshape(10, 100)

            results["merton"] = {
                "time_ms": merton_time * 1000,
                "points": len(market_prices_merton),
                "throughput_kops": len(market_prices_merton) / merton_time / 1000,
                "smile_shape": smile_merton.shape,
                "min_iv": np.nanmin(ivs_merton),
                "max_iv": np.nanmax(ivs_merton),
                "mean_iv": np.nanmean(ivs_merton),
            }

        # American モデル（早期行使考慮）
        if hasattr(self.american, "implied_volatility_batch"):
            # Americanは計算が重いので点数を減らす
            k_reduced = k_flat[::10]  # 10点ごとにサンプリング
            t_reduced = t_flat[::10]
            s_reduced = s_flat[::10]
            r_reduced = r_flat[::10]
            q_reduced = q_flat[::10]
            prices_reduced = market_prices_merton[::10]

            start = time.perf_counter()
            self.american.implied_volatility_batch(
                prices_reduced,
                s_reduced,
                k_reduced,
                t_reduced,
                r_reduced,
                q_reduced,
                np.full(len(prices_reduced), True),
            )
            american_time = time.perf_counter() - start

            results["american"] = {
                "time_ms": american_time * 1000,
                "points": len(prices_reduced),
                "throughput_kops": len(prices_reduced) / american_time / 1000,
                "note": "Reduced sampling (1/10 points)",
            }

        return results

    def realtime_portfolio_risk_with_early_exercise(self, portfolio_size: int = 10000) -> dict[str, Any]:
        """早期行使境界を含むポートフォリオリスク計算.

        Args:
            portfolio_size: ポートフォリオサイズ

        Returns:
            ポートフォリオリスク計算の性能結果
        """
        if not self.models_available:
            return {"error": "QuantForge models not available"}

        # 大規模ポートフォリオを模擬（American options含む）
        positions = self._generate_mixed_portfolio(portfolio_size)

        # American optionsのマスク
        american_mask = positions["is_american"]
        american_count = np.sum(american_mask)

        results: dict[str, Any] = {
            "portfolio_size": portfolio_size,
            "american_options": int(american_count),
            "european_options": portfolio_size - int(american_count),
        }

        if american_count == 0:
            return results

        # American optionsのIV計算
        if hasattr(self.american, "implied_volatility_batch"):
            start = time.perf_counter()
            ivs_american = self.american.implied_volatility_batch(
                positions["market_prices"][american_mask],
                positions["spots"][american_mask],
                positions["strikes"][american_mask],
                positions["times"][american_mask],
                positions["rates"][american_mask],
                positions["dividends"][american_mask],
                positions["is_calls"][american_mask],
            )
            iv_calc_time = time.perf_counter() - start

            results["iv_calculation"] = {
                "time_ms": iv_calc_time * 1000,
                "throughput_kops": american_count / iv_calc_time / 1000,
                "ivs_calculated": len(ivs_american),
            }

        # 早期行使境界の計算
        if hasattr(self.american, "exercise_boundary_batch"):
            start = time.perf_counter()
            self.american.exercise_boundary_batch(
                positions["spots"][american_mask],
                positions["strikes"][american_mask],
                positions["times"][american_mask],
                positions["rates"][american_mask],
                positions["dividends"][american_mask],
                ivs_american,
                positions["is_calls"][american_mask],
            )
            boundary_calc_time = time.perf_counter() - start

            results["boundary_calculation"] = {
                "time_ms": boundary_calc_time * 1000,
                "throughput_kops": american_count / boundary_calc_time / 1000,
            }

        # Greeks計算（リスク管理用）
        if hasattr(self.american, "greeks_batch"):
            start = time.perf_counter()
            self.american.greeks_batch(
                positions["spots"][american_mask],
                positions["strikes"][american_mask],
                positions["times"][american_mask],
                positions["rates"][american_mask],
                positions["dividends"][american_mask],
                ivs_american,
                positions["is_calls"][american_mask],
            )
            greeks_calc_time = time.perf_counter() - start

            results["greeks_calculation"] = {
                "time_ms": greeks_calc_time * 1000,
                "throughput_kops": american_count / greeks_calc_time / 1000,
            }

            # 合計時間
            total_time = iv_calc_time + boundary_calc_time + greeks_calc_time
            results["total"] = {
                "time_ms": total_time * 1000,
                "throughput_kops": american_count / total_time / 1000,
                "realtime_capable": total_time < 0.1,  # 100ms以内ならリアルタイム可能
            }

        return results

    def high_frequency_trading_scenario(self) -> dict[str, Any]:
        """高頻度取引シナリオのベンチマーク.

        リアルタイムでの価格更新とリスク計算を測定。

        Returns:
            高頻度取引シナリオの性能結果
        """
        if not self.models_available:
            return {"error": "QuantForge models not available"}

        # 100銘柄、各10ストライク
        num_underlyings = 100
        strikes_per_underlying = 10
        total_options = num_underlyings * strikes_per_underlying

        np.random.seed(42)

        # データ生成
        base_spots = np.random.uniform(50, 200, num_underlyings)
        spots = np.repeat(base_spots, strikes_per_underlying)

        # 各銘柄に対してATM周辺のストライク
        strikes = np.zeros(total_options)
        for i in range(num_underlyings):
            start_idx = i * strikes_per_underlying
            end_idx = start_idx + strikes_per_underlying
            strikes[start_idx:end_idx] = np.linspace(base_spots[i] * 0.8, base_spots[i] * 1.2, strikes_per_underlying)

        times = np.full(total_options, 0.25)  # 3ヶ月満期
        rates = np.full(total_options, 0.05)
        true_vols = np.random.uniform(0.15, 0.35, total_options)

        results: dict[str, Any] = {"total_options": total_options, "underlyings": num_underlyings}

        # 価格計算（市場価格シミュレーション）
        start = time.perf_counter()
        if hasattr(self.black_scholes, "call_price_batch"):
            market_prices = self.black_scholes.call_price_batch(spots, strikes, times, rates, true_vols)
        else:
            market_prices = np.maximum(spots - strikes, 0)
        price_calc_time = time.perf_counter() - start

        results["price_calculation"] = {
            "time_ms": price_calc_time * 1000,
            "throughput_kops": total_options / price_calc_time / 1000,
        }

        # IV計算（リアルタイムキャリブレーション）
        if hasattr(self.black_scholes, "implied_volatility_batch"):
            start = time.perf_counter()
            ivs = self.black_scholes.implied_volatility_batch(
                market_prices, spots, strikes, times, rates, np.full(total_options, True)
            )
            iv_calc_time = time.perf_counter() - start

            results["iv_calibration"] = {
                "time_ms": iv_calc_time * 1000,
                "throughput_kops": total_options / iv_calc_time / 1000,
            }

        # Greeks計算（リスク管理）
        if hasattr(self.black_scholes, "greeks_batch"):
            start = time.perf_counter()
            self.black_scholes.greeks_batch(spots, strikes, times, rates, ivs, np.full(total_options, True))
            greeks_calc_time = time.perf_counter() - start

            results["greeks_calculation"] = {
                "time_ms": greeks_calc_time * 1000,
                "throughput_kops": total_options / greeks_calc_time / 1000,
            }

            # トータルレイテンシ
            total_latency = price_calc_time + iv_calc_time + greeks_calc_time
            results["total_latency"] = {
                "time_ms": total_latency * 1000,
                "microseconds_per_option": total_latency * 1e6 / total_options,
                "updates_per_second": 1.0 / total_latency if total_latency > 0 else 0,
            }

        return results

    def run_all_scenarios(self) -> dict[str, Any]:
        """全実用シナリオのベンチマークを実行.

        Returns:
            全シナリオのベンチマーク結果
        """
        print("🚀 実用シナリオベンチマーク開始...")

        results: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
        }

        # ボラティリティサーフェス構築
        print("📊 ボラティリティサーフェス構築...")
        results["volatility_surface"] = self.volatility_surface_construction()

        # ポートフォリオリスク計算
        print("📊 ポートフォリオリスク計算...")
        for size in [1000, 10000]:
            print(f"  - ポートフォリオサイズ {size:,} ...")
            results[f"portfolio_risk_{size}"] = self.realtime_portfolio_risk_with_early_exercise(size)

        # 高頻度取引シナリオ
        print("📊 高頻度取引シナリオ...")
        results["high_frequency"] = self.high_frequency_trading_scenario()

        # 結果を保存
        self.save_results(results)

        print("✅ 実用シナリオベンチマーク完了")
        return results

    def save_results(self, results: dict[str, Any]) -> None:
        """結果をファイルに保存.

        Args:
            results: ベンチマーク結果
        """
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True, parents=True)

        # 最新結果を保存
        with open(results_dir / "practical_scenarios_latest.json", "w") as f:
            json.dump(results, f, indent=2)

        # 履歴に追加
        with open(results_dir / "practical_scenarios_history.jsonl", "a") as f:
            json.dump(results, f)
            f.write("\n")

        print(f"📝 結果を保存: {results_dir}/practical_scenarios_latest.json")


def main() -> None:
    """メインエントリーポイント."""
    runner = PracticalScenariosBenchmark()
    results = runner.run_all_scenarios()

    # 簡易結果表示
    print("\n=== 実用シナリオサマリ ===")

    # ボラティリティサーフェス
    if "volatility_surface" in results:
        vs = results["volatility_surface"]
        if "black_scholes" in vs:
            bs_vs = vs["black_scholes"]
            print("\nボラティリティサーフェス（1000点）:")
            print(f"  Black-Scholes: {bs_vs['time_ms']:.1f} ms")
            print(f"  スループット: {bs_vs['throughput_kops']:.1f} K ops/sec")

    # 高頻度取引
    if "high_frequency" in results:
        hf = results["high_frequency"]
        if "total_latency" in hf:
            print("\n高頻度取引シナリオ:")
            print(f"  総レイテンシ: {hf['total_latency']['time_ms']:.1f} ms")
            print(f"  更新レート: {hf['total_latency']['updates_per_second']:.0f} 回/秒")


if __name__ == "__main__":
    main()
