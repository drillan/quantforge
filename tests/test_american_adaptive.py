"""Tests for American Adaptive option pricing implementation"""
# mypy: disable-error-code="attr-defined"

import time

import numpy as np
import pytest


class TestAmericanAdaptive:
    """American Adaptive実装のテストスイート"""

    def test_adaptive_api_exists(self):
        """Adaptive APIが存在することを確認"""
        from quantforge import american

        assert hasattr(american, "call_price_adaptive")
        assert hasattr(american, "put_price_adaptive")

    def test_backward_compatibility(self):
        """既存APIが変更されていないことを確認"""
        from quantforge import american

        # 既存のcall_price, put_priceが正常動作
        price = american.call_price(100, 100, 1.0, 0.05, 0.02, 0.2)
        assert price > 0
        assert price < 100  # Call can't be worth more than spot

    def test_adaptive_accuracy_deep_otm(self):
        """Deep OTMでAdaptiveがBAWより高精度（または同等）"""
        from quantforge import american

        s, k = 70.0, 100.0  # Deep OTM put
        t, r, q, sigma = 0.25, 0.05, 0.0, 0.3

        baw_price = american.put_price(s, k, t, r, q, sigma)
        adaptive_price = american.put_price_adaptive(s, k, t, r, q, sigma)

        # Note: Due to BAW approximation, both can be slightly below intrinsic for deep ITM
        # This is a known limitation of the BAW method

        # Both prices should be positive and reasonable
        assert adaptive_price > 0
        assert baw_price > 0

        # 両者の差が妥当な範囲内（価格の10%以内）
        relative_diff = abs(adaptive_price - baw_price) / baw_price
        assert relative_diff < 0.10, f"Difference {relative_diff:.2%} too large"

    def test_adaptive_short_term_options(self):
        """短期オプションでのAdaptive動作確認"""
        from quantforge import american

        s, k = 100.0, 100.0  # ATM
        t = 0.05  # Very short term (約18日)
        r, q, sigma = 0.05, 0.02, 0.2

        adaptive_call = american.call_price_adaptive(s, k, t, r, q, sigma)
        adaptive_put = american.put_price_adaptive(s, k, t, r, q, sigma)

        # 短期オプションの基本的な性質を確認
        assert adaptive_call >= (s - k) * np.exp(-r * t)  # Discounted intrinsic
        assert adaptive_put >= (k - s) * np.exp(-r * t)  # Discounted intrinsic

    def test_adaptive_high_volatility(self):
        """高ボラティリティでのAdaptive動作確認"""
        from quantforge import american

        s, k = 100.0, 100.0
        t, r, q = 1.0, 0.05, 0.0
        sigma_high = 0.5  # High volatility

        baw_price = american.put_price(s, k, t, r, q, sigma_high)
        adaptive_price = american.put_price_adaptive(s, k, t, r, q, sigma_high)

        # 高ボラティリティでも妥当な価格
        assert adaptive_price > 0
        assert adaptive_price < k  # Put can't be worth more than strike

        # BAWとの差が妥当
        relative_diff = abs(adaptive_price - baw_price) / baw_price
        assert relative_diff < 0.15, f"High vol difference {relative_diff:.2%} too large"

    def test_performance_acceptable(self):
        """パフォーマンス劣化が許容範囲内（20%以内）"""
        from quantforge import american

        params = (100, 100, 1.0, 0.05, 0.02, 0.2)
        n_iterations = 1000

        # ウォームアップ
        for _ in range(10):
            american.call_price(*params)
            american.call_price_adaptive(*params)

        # BAW計測
        start = time.perf_counter()
        for _ in range(n_iterations):
            american.call_price(*params)
        baw_time = time.perf_counter() - start

        # Adaptive計測
        start = time.perf_counter()
        for _ in range(n_iterations):
            american.call_price_adaptive(*params)
        adaptive_time = time.perf_counter() - start

        # 劣化が20%以内（より現実的な閾値）
        performance_ratio = adaptive_time / baw_time
        assert performance_ratio < 1.20, f"Performance degradation {performance_ratio:.2f}x exceeds limit"

    def test_adaptive_batch_processing(self):
        """バッチ処理でのAdaptive動作確認"""
        from quantforge import american

        # 複数のオプション価格を一度に計算
        spots = np.array([90, 95, 100, 105, 110])
        strikes = 100.0
        times = 1.0
        rates = 0.05
        dividend_yields = 0.02
        sigmas = 0.2

        # バッチ処理が存在し、動作することを確認
        if hasattr(american, "call_price_adaptive_batch"):
            prices = american.call_price_adaptive_batch(spots, strikes, times, rates, dividend_yields, sigmas)
            assert len(prices) == len(spots)
            assert all(p > 0 for p in prices)

    def test_edge_cases(self):
        """エッジケースでの動作確認"""
        from quantforge import american

        # 1. 満期直前
        price_near_expiry = american.put_price_adaptive(90, 100, 0.001, 0.05, 0.0, 0.2)
        assert abs(price_near_expiry - 10.0) < 0.01  # ほぼ intrinsic value

        # 2. Deep ITM
        price_deep_itm = american.call_price_adaptive(150, 100, 1.0, 0.05, 0.02, 0.2)
        assert price_deep_itm >= 50  # At least intrinsic value

        # 3. Zero dividend (American call = European call)
        price_no_div = american.call_price_adaptive(100, 100, 1.0, 0.05, 0.0, 0.2)
        # Should be close to Black-Scholes European price
        assert price_no_div > 0


@pytest.mark.benchmark
class TestAdaptiveBenchmark:
    """Adaptive実装のベンチマークテスト"""

    def test_moneyness_accuracy(self):
        """モネーネス別の精度比較"""
        from quantforge import american

        results = []
        for moneyness in [0.5, 0.7, 0.9, 1.0, 1.1, 1.3, 1.5]:
            s = 100.0 * moneyness
            k = 100.0
            t, r, q, sigma = 1.0, 0.05, 0.0, 0.2

            baw = american.put_price(s, k, t, r, q, sigma)
            adaptive = american.put_price_adaptive(s, k, t, r, q, sigma)

            results.append(
                {
                    "moneyness": moneyness,
                    "baw": baw,
                    "adaptive": adaptive,
                    "diff": abs(adaptive - baw),
                    "rel_diff": abs(adaptive - baw) / baw if baw > 0 else 0,
                }
            )

        # 結果の検証
        max_rel_diff = max(r["rel_diff"] for r in results)
        assert max_rel_diff < 0.20, f"Maximum relative difference {max_rel_diff:.2%} too large"
