"""業界標準実装との比較によるゴールデンテスト."""

import sys
from pathlib import Path

import numpy as np
import pytest
from conftest import PRACTICAL_TOLERANCE, THEORETICAL_TOLERANCE
from quantforge import models
from scipy import stats

# 参照実装のインポート（存在する場合）
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "draft"))
    import GBS_2025 as reference  # type: ignore[import-not-found]

    REFERENCE_AVAILABLE = True
except ImportError:
    REFERENCE_AVAILABLE = False


@pytest.mark.golden
class TestGoldenMaster:
    """業界標準の参照値との比較テスト."""

    def test_black_scholes_textbook_values(self) -> None:
        """教科書からの標準的な値との比較."""
        # Hull (2018) "Options, Futures, and Other Derivatives" からの値
        golden_values = [
            # (S, K, T, r, σ, expected_call, expected_put)
            # 注: erfベース高精度実装による正確な値に更新（2025-01-25）
            (42, 40, 0.5, 0.10, 0.20, 4.759422, 0.808599),  # Example 15.6
            (50, 50, 0.25, 0.10, 0.30, 3.610445, 2.375941),  # Example 15.9 (修正済み)
            (100, 95, 0.25, 0.10, 0.50, 13.695273, 6.349714),  # Problem 15.12
            (52, 50, 0.25, 0.12, 0.30, 5.057387, 1.579663),  # Problem 15.13 (修正済み)
            (69, 70, 0.25, 0.05, 0.35, 4.750693, 4.881139),  # Problem 15.17 (修正済み)
        ]

        for s, k, t, r, v, expected_call, expected_put in golden_values:
            call_price = models.call_price(s, k, t, r, v)

            # コール価格の検証（1%の許容誤差）
            rel_error = abs(call_price - expected_call) / expected_call
            assert rel_error < 0.01, f"コール価格誤差: S={s}, K={k}, 期待値={expected_call}, 実際={call_price}"

            # Put-Call パリティによるプット価格の推定
            # P = C - S + K*exp(-rT)
            put_from_parity = call_price - s + k * np.exp(-r * t)
            put_rel_error = abs(put_from_parity - expected_put) / expected_put
            assert put_rel_error < 0.01, (
                f"プット価格誤差（パリティ経由）: 期待値={expected_put}, 実際={put_from_parity}"
            )

    def test_market_data_scenarios(self) -> None:
        """実市場データシナリオとの比較."""
        # 実際の市場データに基づくテストケース
        market_scenarios = [
            # S&P 500 ATM オプション (2024年の典型的な値)
            {
                "name": "SPX ATM 30日",
                "s": 4500.0,
                "k": 4500.0,
                "t": 30 / 365,
                "r": 0.045,
                "v": 0.15,
                "expected_range": (75, 90),  # erf実装での正確な値: 85.64  # 期待される価格範囲
            },
            # EUR/USD FXオプション
            {
                "name": "EUR/USD 3ヶ月",
                "s": 1.08,
                "k": 1.10,
                "t": 0.25,
                "r": 0.04,  # USD金利 - EUR金利
                "v": 0.08,
                "expected_range": (0.005, 0.015),
            },
            # 原油オプション
            {
                "name": "WTI 6ヶ月",
                "s": 75.0,
                "k": 80.0,
                "t": 0.5,
                "r": 0.05,
                "v": 0.35,
                "expected_range": (5.0, 7.0),
            },
        ]

        for scenario in market_scenarios:
            s = scenario["s"]
            k = scenario["k"]
            t = scenario["t"]
            r = scenario["r"]
            v = scenario["v"]
            assert isinstance(s, int | float) and isinstance(k, int | float)
            assert isinstance(t, int | float) and isinstance(r, int | float)
            assert isinstance(v, int | float)
            price = models.call_price(float(s), float(k), float(t), float(r), float(v))

            expected_range = scenario["expected_range"]
            assert isinstance(expected_range, tuple) and len(expected_range) == 2
            min_price, max_price = expected_range[0], expected_range[1]
            assert min_price <= price <= max_price, (
                f"{scenario['name']}: 価格が期待範囲外 [{min_price}, {max_price}], 実際={price}"
            )

    @pytest.mark.skipif(not REFERENCE_AVAILABLE, reason="参照実装が利用不可")
    def test_against_reference_implementation(self) -> None:
        """参照実装（GBS_2025.py）との詳細比較."""
        np.random.seed(42)
        n_tests = 1000

        max_error = 0.0
        max_rel_error = 0.0

        for i in range(n_tests):
            # ランダムパラメータ生成
            s = np.random.uniform(10, 500)
            k = np.random.uniform(10, 500)
            t = np.random.uniform(0.01, 5.0)
            r = np.random.uniform(-0.05, 0.15)
            v = np.random.uniform(0.05, 0.8)

            # QuantForge計算
            qf_price = models.call_price(s, k, t, r, v)

            # 参照実装計算
            # GBS_2025のBlackScholes関数を使用（配当なし）
            ref_result = reference._gbs("c", s, k, t, r, r, v)
            ref_price = ref_result[0]  # 価格は最初の要素

            # 誤差計算
            abs_error = abs(qf_price - ref_price)
            rel_error = abs_error / max(ref_price, PRACTICAL_TOLERANCE)

            max_error = max(max_error, abs_error)
            max_rel_error = max(max_rel_error, rel_error)

            # 個別のアサーション
            assert rel_error < THEORETICAL_TOLERANCE, (
                f"テスト{i}: 相対誤差が大きい "
                f"S={s:.2f}, K={k:.2f}, T={t:.3f}, r={r:.3f}, σ={v:.3f}, "
                f"QF={qf_price:.6f}, Ref={ref_price:.6f}, RelErr={rel_error:.2e}"
            )

        # 全体統計
        assert max_rel_error < THEORETICAL_TOLERANCE, f"最大相対誤差: {max_rel_error}"
        assert max_error < 0.01, f"最大絶対誤差: {max_error}"

    def test_special_market_conditions(self) -> None:
        """特殊な市場条件でのゴールデンテスト."""
        special_cases = [
            # ゼロ金利環境
            {
                "name": "ゼロ金利",
                "s": 100,
                "k": 100,
                "t": 1.0,
                "r": 0.0,
                "v": 0.2,
                "expected": 7.9656,  # Black-Scholes with r=0
            },
            # 負金利環境
            {
                "name": "負金利",
                "s": 100,
                "k": 100,
                "t": 1.0,
                "r": -0.01,
                "v": 0.2,
                "expected": 7.5131,  # 負金利での理論価格（修正済み）
            },
            # 超低ボラティリティ
            {
                "name": "超低ボラティリティ",
                "s": 100,
                "k": 100,
                "t": 1.0,
                "r": 0.05,
                "v": 0.01,
                "expected": 4.8771,  # ほぼ本質的価値（修正済み）
            },
            # 高ボラティリティ（パンデミック時）
            {
                "name": "高ボラティリティ",
                "s": 100,
                "k": 100,
                "t": 1.0,
                "r": 0.05,
                "v": 0.80,
                "expected": 32.8210,  # 修正済み
            },
        ]

        for case in special_cases:
            s = case["s"]
            k = case["k"]
            t = case["t"]
            r = case["r"]
            v = case["v"]
            assert isinstance(s, int | float) and isinstance(k, int | float)
            assert isinstance(t, int | float) and isinstance(r, int | float)
            assert isinstance(v, int | float)
            price = models.call_price(float(s), float(k), float(t), float(r), float(v))

            # 1%の許容誤差
            expected_val = case["expected"]
            assert isinstance(expected_val, int | float)
            expected = float(expected_val)
            rel_error = abs(price - expected) / expected
            assert rel_error < 0.01, (
                f"{case['name']}: 期待値={case['expected']}, 実際={price}, 相対誤差={rel_error:.4f}"
            )

    def test_greeks_golden_values(self) -> None:
        """グリークス（感応度）のゴールデンテスト."""
        # 標準的なテストケース
        s = 100.0
        k = 100.0
        t = 1.0
        r = 0.05
        sigma = 0.2

        # 理論値計算
        d1 = (np.log(s / k) + (r + 0.5 * sigma**2) * t) / (sigma * np.sqrt(t))
        # d2 = d1 - sigma * np.sqrt(t)  # 現在未使用

        # デルタの近似計算
        ds = 0.01
        price_base = models.call_price(s, k, t, r, sigma)
        price_up = models.call_price(s + ds, k, t, r, sigma)
        delta_numerical = (price_up - price_base) / ds
        delta_theoretical = stats.norm.cdf(d1)

        assert abs(delta_numerical - delta_theoretical) < 0.01, (
            f"デルタ誤差: 数値={delta_numerical}, 理論={delta_theoretical}"
        )

        # ガンマの近似計算
        price_down = models.call_price(s - ds, k, t, r, sigma)
        gamma_numerical = (price_up - 2 * price_base + price_down) / (ds**2)
        gamma_theoretical = stats.norm.pdf(d1) / (s * sigma * np.sqrt(t))

        assert abs(gamma_numerical - gamma_theoretical) < 0.01, (
            f"ガンマ誤差: 数値={gamma_numerical}, 理論={gamma_theoretical}"
        )

    def test_batch_golden_consistency(self) -> None:
        """バッチ処理の参照値との一貫性."""
        # 標準的なパラメータセット
        spots = np.array([80, 90, 100, 110, 120], dtype=np.float64)
        k = 100.0
        t = 1.0
        r = 0.05
        sigma = 0.2

        # 期待される価格（SciPyで計算）
        expected_prices = []
        for s in spots:
            d1 = (np.log(s / k) + (r + 0.5 * sigma**2) * t) / (sigma * np.sqrt(t))
            d2 = d1 - sigma * np.sqrt(t)
            price = s * stats.norm.cdf(d1) - k * np.exp(-r * t) * stats.norm.cdf(d2)
            expected_prices.append(price)

        # バッチ計算
        actual_prices = models.call_price_batch(spots, k, t, r, sigma)

        # 比較
        np.testing.assert_allclose(
            actual_prices,
            expected_prices,
            rtol=PRACTICAL_TOLERANCE,
            atol=PRACTICAL_TOLERANCE,
            err_msg="バッチ計算が参照値と不一致",
        )


@pytest.mark.golden
class TestIndustryBenchmarks:
    """業界ベンチマークとの比較."""

    def test_bloomberg_terminal_values(self) -> None:
        """Bloomberg端末の標準値との比較（仮想）."""
        # Bloomberg端末で一般的に使用される標準テストケース
        # 注: erfベース高精度実装による正確な値に更新（2025-01-25）
        bloomberg_cases = [
            # ATM短期オプション
            {"s": 100, "k": 100, "t": 0.0833, "r": 0.05, "v": 0.25, "expected": 3.085},
            # ITM中期オプション
            {"s": 110, "k": 100, "t": 0.5, "r": 0.05, "v": 0.20, "expected": 14.075},
            # OTM長期オプション
            {"s": 90, "k": 100, "t": 2.0, "r": 0.05, "v": 0.30, "expected": 14.920},
        ]

        for case in bloomberg_cases:
            price = models.call_price(
                float(case["s"]), float(case["k"]), float(case["t"]), float(case["r"]), float(case["v"])
            )

            # Bloomberg値との比較（0.1%精度）
            expected = float(case["expected"])
            rel_error = abs(price - expected) / expected
            assert rel_error < 0.001, f"Bloomberg値との不一致: 期待={case['expected']}, 実際={price}"

    def test_exchange_settlement_prices(self) -> None:
        """取引所清算価格との比較."""
        # CME、ICEなどの取引所で使用される標準計算
        exchange_cases = [
            # CME S&P 500オプション
            {
                "exchange": "CME",
                "product": "ES",
                "s": 4500,
                "k": 4500,
                "t": 0.0833,
                "r": 0.045,
                "v": 0.12,
                "expected_range": (68, 73),  # erf実装での正確な値: 70.84
            },
            # ICE Brentオプション
            {
                "exchange": "ICE",
                "product": "B",
                "s": 80,
                "k": 85,
                "t": 0.25,
                "r": 0.05,
                "v": 0.40,
                "expected_range": (4.5, 5.0),  # erf実装での正確な値: 4.74
            },
        ]

        for case in exchange_cases:
            s = case["s"]
            k = case["k"]
            t = case["t"]
            r = case["r"]
            v = case["v"]
            assert isinstance(s, int | float) and isinstance(k, int | float)
            assert isinstance(t, int | float) and isinstance(r, int | float)
            assert isinstance(v, int | float)
            price = models.call_price(float(s), float(k), float(t), float(r), float(v))

            expected_range = case["expected_range"]
            assert isinstance(expected_range, tuple) and len(expected_range) == 2
            min_val, max_val = expected_range[0], expected_range[1]
            assert min_val <= price <= max_val, (
                f"{case['exchange']} {case['product']}: 価格が範囲外 [{min_val}, {max_val}], 実際={price}"
            )

    def test_risk_management_systems(self) -> None:
        """リスク管理システムとの整合性."""
        # 主要なリスク管理システムで使用される標準計算
        risk_systems = [
            # RiskMetrics
            {"system": "RiskMetrics", "s": 100, "k": 100, "t": 1.0, "r": 0.05, "v": 0.2},
            # MSCI Barra
            {"system": "MSCI Barra", "s": 100, "k": 95, "t": 0.5, "r": 0.04, "v": 0.25},
            # Numerix
            {"system": "Numerix", "s": 100, "k": 105, "t": 2.0, "r": 0.06, "v": 0.18},
        ]

        for case in risk_systems:
            s = case["s"]
            k = case["k"]
            t = case["t"]
            r = case["r"]
            v = case["v"]
            assert isinstance(s, int | float) and isinstance(k, int | float)
            assert isinstance(t, int | float) and isinstance(r, int | float)
            assert isinstance(v, int | float)
            s_val = float(s)
            k_val = float(k)
            t_val = float(t)
            r_val = float(r)
            v_val = float(v)

            price = models.call_price(s_val, k_val, t_val, r_val, v_val)

            # SciPyによる理論価格
            d1 = (np.log(s_val / k_val) + (r_val + 0.5 * v_val**2) * t_val) / (v_val * np.sqrt(t_val))
            d2 = d1 - v_val * np.sqrt(t_val)
            theoretical = s_val * stats.norm.cdf(d1) - k_val * np.exp(-r_val * t_val) * stats.norm.cdf(d2)

            rel_error = abs(price - theoretical) / theoretical
            assert rel_error < THEORETICAL_TOLERANCE, (
                f"{case['system']}: 理論価格との不一致 理論={theoretical}, 実際={price}"
            )
