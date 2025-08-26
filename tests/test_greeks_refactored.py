# mypy: disable-error-code="attr-defined"
"""Black-Scholesグリークスのテスト（リファクタリング版）

Rust実装のグリークス計算が正しく動作することを検証。
重複コードを削減し、パラメータ化テストを活用。
"""

from typing import Any

import numpy as np
import pytest
from conftest import NUMERICAL_TOLERANCE
from quantforge.models import black_scholes


class TestGreeksParameterized:
    """パラメータ化されたグリークステスト"""

    @pytest.mark.parametrize(
        "is_call,greek_name,expected_value,sign_check",
        [
            (True, "delta", 0.6368306517096883, lambda x: x > 0),
            (False, "delta", -0.36316934829031174, lambda x: x < 0),
            (True, "gamma", 0.018762017345846895, lambda x: x > 0),
            (False, "gamma", 0.018762017345846895, lambda x: x > 0),
            (True, "vega", 0.3752403469169379, lambda x: x > 0),
            (False, "vega", 0.3752403469169379, lambda x: x > 0),
            (True, "theta", None, lambda x: x < 0),
            (False, "theta", None, lambda x: x < 0),
            (True, "rho", None, lambda x: x > 0),
            (False, "rho", None, lambda x: x < 0),
        ],
    )
    def test_single_greek(
        self,
        is_call: bool,
        greek_name: str,
        expected_value: float | None,
        sign_check: Any,
    ) -> None:
        """単一のグリークス計算テスト（パラメータ化）"""
        greeks = black_scholes.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=is_call)
        greek_value = getattr(greeks, greek_name)

        # 符号チェック
        assert sign_check(greek_value), f"{greek_name} sign check failed"

        # 期待値がある場合は精度チェック
        if expected_value is not None:
            assert abs(greek_value - expected_value) < NUMERICAL_TOLERANCE, f"{greek_name} accuracy check failed"

    @pytest.mark.parametrize(
        "spot,strike,time,rate,sigma,is_call",
        [
            (100.0, 100.0, 1.0, 0.05, 0.2, True),  # ATM Call
            (100.0, 100.0, 1.0, 0.05, 0.2, False),  # ATM Put
            (110.0, 100.0, 1.0, 0.05, 0.2, True),  # ITM Call
            (90.0, 100.0, 1.0, 0.05, 0.2, False),  # ITM Put
            (90.0, 100.0, 1.0, 0.05, 0.2, True),  # OTM Call
            (110.0, 100.0, 1.0, 0.05, 0.2, False),  # OTM Put
        ],
    )
    def test_delta_moneyness(
        self,
        spot: float,
        strike: float,
        time: float,
        rate: float,
        sigma: float,
        is_call: bool,
    ) -> None:
        """Deltaのマネーネス依存性テスト"""
        greeks = black_scholes.greeks(spot, strike, time, rate, sigma, is_call)
        delta = greeks.delta

        if is_call:
            # Call delta: 0 < delta < 1
            assert 0.0 < delta < 1.0, f"Call delta {delta} out of bounds"
            # ITM call should have higher delta
            if spot > strike:
                assert delta > 0.5, f"ITM call delta {delta} should be > 0.5"
            elif spot < strike:
                assert delta < 0.5, f"OTM call delta {delta} should be < 0.5"
        else:
            # Put delta: -1 < delta < 0
            assert -1.0 < delta < 0.0, f"Put delta {delta} out of bounds"
            # ITM put should have more negative delta
            if spot < strike:
                assert delta < -0.5, f"ITM put delta {delta} should be < -0.5"
            elif spot > strike:
                assert delta > -0.5, f"OTM put delta {delta} should be > -0.5"

    @pytest.mark.parametrize(
        "spot_range",
        [
            np.linspace(80, 120, 10),  # 10 points
            np.linspace(50, 150, 20),  # 20 points
        ],
    )
    def test_batch_calculation(self, spot_range: np.ndarray) -> None:
        """バッチ計算のテスト"""
        strike = 100.0
        time = 1.0
        rate = 0.05
        sigma = 0.2

        # Calculate greeks for each spot
        results = []
        for spot in spot_range:
            greeks = black_scholes.greeks(spot, strike, time, rate, sigma, is_call=True)
            results.append(
                {
                    "spot": spot,
                    "delta": greeks.delta,
                    "gamma": greeks.gamma,
                    "vega": greeks.vega,
                    "theta": greeks.theta,
                    "rho": greeks.rho,
                }
            )

        # Verify monotonicity and bounds
        deltas = [r["delta"] for r in results]
        assert all(0 <= d <= 1 for d in deltas), "Delta out of bounds"
        assert deltas == sorted(deltas), "Delta should be monotonic in spot"

        gammas = [r["gamma"] for r in results]
        assert all(g >= 0 for g in gammas), "Gamma should be non-negative"

        vegas = [r["vega"] for r in results]
        assert all(v >= 0 for v in vegas), "Vega should be non-negative"


class TestGreeksPutCallParity:
    """プット・コールパリティを使用したグリークステスト"""

    @pytest.mark.parametrize(
        "spot,strike,time,rate,sigma",
        [
            (100.0, 100.0, 1.0, 0.05, 0.2),
            (110.0, 100.0, 0.5, 0.03, 0.25),
            (90.0, 100.0, 2.0, 0.07, 0.15),
        ],
    )
    def test_greek_relationships(self, spot: float, strike: float, time: float, rate: float, sigma: float) -> None:
        """グリークス間の関係性テスト"""
        call_greeks = black_scholes.greeks(spot, strike, time, rate, sigma, is_call=True)
        put_greeks = black_scholes.greeks(spot, strike, time, rate, sigma, is_call=False)

        # Delta parity: Call Delta - Put Delta = 1 (approximately, due to discounting)
        delta_diff = call_greeks.delta - put_greeks.delta
        expected_diff = np.exp(-rate * time)
        assert abs(delta_diff - expected_diff) < NUMERICAL_TOLERANCE

        # Gamma equality
        assert abs(call_greeks.gamma - put_greeks.gamma) < NUMERICAL_TOLERANCE

        # Vega equality
        assert abs(call_greeks.vega - put_greeks.vega) < NUMERICAL_TOLERANCE


class TestGreeksEdgeCases:
    """エッジケースのテスト"""

    @pytest.mark.parametrize(
        "sigma,time,test_name",
        [
            (0.001, 1.0, "near_zero_volatility"),
            (0.2, 0.001, "near_expiry"),
            (5.0, 1.0, "extreme_volatility"),
        ],
    )
    def test_edge_parameters(self, sigma: float, time: float, test_name: str) -> None:
        """極端なパラメータでのテスト"""
        spot = 100.0
        strike = 100.0
        rate = 0.05

        # Should not raise exception
        try:
            greeks = black_scholes.greeks(spot, strike, time, rate, sigma, is_call=True)

            # Basic sanity checks
            assert np.isfinite(greeks.delta), f"{test_name}: Delta is not finite"
            assert np.isfinite(greeks.gamma), f"{test_name}: Gamma is not finite"
            assert np.isfinite(greeks.vega), f"{test_name}: Vega is not finite"
            assert np.isfinite(greeks.theta), f"{test_name}: Theta is not finite"
            assert np.isfinite(greeks.rho), f"{test_name}: Rho is not finite"

        except Exception as e:
            pytest.fail(f"{test_name} raised exception: {e}")


class TestGreeksConsistency:
    """一貫性テスト"""

    def test_cross_model_consistency(self) -> None:
        """異なるモデル間での一貫性テスト"""
        spot = 100.0
        strike = 100.0
        time = 1.0
        rate = 0.05
        sigma = 0.2

        # Black-Scholes greeks
        bs_greeks = black_scholes.greeks(spot, strike, time, rate, sigma, is_call=True)

        # ここで他のモデル（Merton等）があれば比較
        # 例: merton_greeks = merton.greeks(spot, strike, time, rate, 0, sigma, is_call=True)
        # assert abs(bs_greeks.delta - merton_greeks.delta) < NUMERICAL_TOLERANCE

        # 自己一貫性チェック
        assert bs_greeks.delta is not None
        assert bs_greeks.gamma is not None
        assert bs_greeks.vega is not None
        assert bs_greeks.theta is not None
        assert bs_greeks.rho is not None

    @pytest.mark.parametrize("spot_shift", [-1.0, 1.0])
    def test_numerical_differentiation(self, spot_shift: float) -> None:
        """数値微分による検証"""
        base_spot = 100.0
        strike = 100.0
        time = 1.0
        rate = 0.05
        sigma = 0.2
        epsilon = 0.01

        # Calculate prices at shifted spots
        price_base = black_scholes.call_price(base_spot, strike, time, rate, sigma)
        price_shifted = black_scholes.call_price(base_spot + spot_shift * epsilon, strike, time, rate, sigma)

        # Numerical delta
        numerical_delta = (price_shifted - price_base) / (spot_shift * epsilon)

        # Analytical delta
        greeks = black_scholes.greeks(base_spot, strike, time, rate, sigma, is_call=True)

        # Should be approximately equal
        assert abs(numerical_delta - greeks.delta) < 0.01  # Larger tolerance for numerical diff
