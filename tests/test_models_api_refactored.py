"""Test the models-based API structure (Refactored).

重複を削減し、パラメータ化テストとヘルパー関数を活用。
"""

from collections.abc import Callable

import numpy as np
import pytest
from conftest import NUMERICAL_TOLERANCE, PRACTICAL_TOLERANCE
from numpy.typing import NDArray
from quantforge.models import black_scholes


class TestBlackScholesAPI:
    """Black-Scholesモデルの統合APIテスト"""

    # 共通のテストパラメータ
    DEFAULT_PARAMS = {
        "spot": 100.0,
        "strike": 105.0,
        "time": 1.0,
        "rate": 0.05,
        "sigma": 0.2,
    }

    ATM_PARAMS = {
        "spot": 100.0,
        "strike": 100.0,
        "time": 1.0,
        "rate": 0.05,
        "sigma": 0.2,
    }

    @pytest.mark.parametrize(
        "price_func,expected",
        [
            (black_scholes.call_price, 8.021352224079687),
            (black_scholes.put_price, 7.90044179918926),
        ],
    )
    def test_single_price_calculation(self, price_func: Callable[..., float], expected: float) -> None:
        """単一価格計算のパラメータ化テスト"""
        price = price_func(**self.DEFAULT_PARAMS)
        assert abs(price - expected) < PRACTICAL_TOLERANCE

    @pytest.mark.parametrize(
        "batch_func,expected_values",
        [
            (
                black_scholes.call_price_batch,
                [7.510872, 10.450584, 13.857906, 17.662954],
            ),
            (
                black_scholes.put_price_batch,
                [7.633815, 5.573526, 3.980849, 2.785896],
            ),
        ],
    )
    def test_batch_price_calculation(
        self, batch_func: Callable[..., NDArray[np.float64]], expected_values: list[float]
    ) -> None:
        """バッチ価格計算のパラメータ化テスト"""
        spots = np.array([95.0, 100.0, 105.0, 110.0])
        prices = batch_func(spots, 100.0, 1.0, 0.05, 0.2)
        np.testing.assert_allclose(prices, expected_values, rtol=PRACTICAL_TOLERANCE)

    def test_greeks_structure_and_values(self) -> None:
        """Greeks構造体のテスト（構造と値の検証）"""
        greeks = black_scholes.greeks(**self.ATM_PARAMS, is_call=True)

        # 構造の検証（全属性の存在確認）
        required_attrs = ["delta", "gamma", "vega", "theta", "rho"]
        for attr in required_attrs:
            assert hasattr(greeks, attr), f"Missing attribute: {attr}"
            assert getattr(greeks, attr) is not None, f"None value for: {attr}"
            assert np.isfinite(getattr(greeks, attr)), f"Non-finite value for: {attr}"

        # 具体的な値の検証
        expected_values = {
            "delta": 0.6368306505,
            "gamma": 0.01874042826,
        }
        for name, expected in expected_values.items():
            actual = getattr(greeks, name)
            assert abs(actual - expected) < PRACTICAL_TOLERANCE, f"{name}: expected {expected}, got {actual}"

    @pytest.mark.parametrize("target_vol", [0.15, 0.25, 0.35, 0.45])
    def test_implied_volatility_recovery(self, target_vol: float) -> None:
        """インプライドボラティリティの復元テスト"""
        # 既知のボラティリティで価格を計算
        params = self.ATM_PARAMS.copy()
        params["sigma"] = target_vol
        price = black_scholes.call_price(**params)

        # ボラティリティを逆算
        iv = black_scholes.implied_volatility(
            price,
            params["spot"],
            params["strike"],
            params["time"],
            params["rate"],
            is_call=True,
        )

        assert abs(iv - target_vol) < NUMERICAL_TOLERANCE

    @pytest.mark.parametrize(
        "spot,strike,time,rate,sigma",
        [
            (100.0, 105.0, 1.0, 0.05, 0.2),
            (110.0, 100.0, 0.5, 0.03, 0.25),
            (90.0, 100.0, 2.0, 0.07, 0.15),
            (100.0, 100.0, 1.0, 0.0, 0.3),  # Zero rate
        ],
    )
    def test_put_call_parity(self, spot: float, strike: float, time: float, rate: float, sigma: float) -> None:
        """プット・コールパリティのパラメータ化テスト"""
        call = black_scholes.call_price(spot, strike, time, rate, sigma)
        put = black_scholes.put_price(spot, strike, time, rate, sigma)

        # Put-Call Parity: C - P = S - K * exp(-r*T)
        lhs = call - put
        rhs = spot - strike * np.exp(-rate * time)

        assert abs(lhs - rhs) < NUMERICAL_TOLERANCE


class TestBlackScholesConsistency:
    """Black-Scholesモデルの一貫性テスト"""

    def test_price_monotonicity(self) -> None:
        """価格の単調性テスト"""
        spots = np.linspace(80, 120, 20)
        strike = 100.0
        params = {"strike": strike, "time": 1.0, "rate": 0.05, "sigma": 0.2}

        call_prices = [black_scholes.call_price(s, **params) for s in spots]
        put_prices = [black_scholes.put_price(s, **params) for s in spots]

        # Call prices should increase with spot
        assert call_prices == sorted(call_prices), "Call prices not monotonic in spot"

        # Put prices should decrease with spot
        assert put_prices == sorted(put_prices, reverse=True), "Put prices not monotonic in spot"

    def test_time_decay(self) -> None:
        """時間価値の減衰テスト"""
        times = np.linspace(0.01, 2.0, 10)
        base_params = {"spot": 100.0, "strike": 100.0, "rate": 0.05, "sigma": 0.2}

        call_prices = [black_scholes.call_price(**base_params, time=t) for t in times]
        put_prices = [black_scholes.put_price(**base_params, time=t) for t in times]

        # Prices should increase with time (for standard options)
        assert call_prices == sorted(call_prices), "Call prices should increase with time"
        assert put_prices == sorted(put_prices), "Put prices should increase with time"

    @pytest.mark.parametrize("multiplier", [0.5, 1.0, 2.0])
    def test_homogeneity(self, multiplier: float) -> None:
        """同次性テスト（価格スケーリング）"""
        base_spot = 100.0
        base_strike = 100.0
        time = 1.0
        rate = 0.05
        sigma = 0.2

        # Calculate base prices
        base_call = black_scholes.call_price(base_spot, base_strike, time, rate, sigma)
        base_put = black_scholes.put_price(base_spot, base_strike, time, rate, sigma)

        # Calculate scaled prices
        scaled_call = black_scholes.call_price(base_spot * multiplier, base_strike * multiplier, time, rate, sigma)
        scaled_put = black_scholes.put_price(base_spot * multiplier, base_strike * multiplier, time, rate, sigma)

        # Prices should scale proportionally (accounting for discounting)
        assert abs(scaled_call - base_call * multiplier) < PRACTICAL_TOLERANCE
        assert abs(scaled_put - base_put * multiplier) < PRACTICAL_TOLERANCE


class TestBoundaryConditions:
    """境界条件のテスト"""

    def test_deep_itm_call(self) -> None:
        """Deep ITMコールの境界条件"""
        spot = 200.0
        strike = 100.0
        time = 1.0
        rate = 0.05
        sigma = 0.2

        price = black_scholes.call_price(spot, strike, time, rate, sigma)
        intrinsic = spot - strike * np.exp(-rate * time)

        # Deep ITM call should be close to intrinsic value
        assert abs(price - intrinsic) < PRACTICAL_TOLERANCE

    def test_deep_otm_call(self) -> None:
        """Deep OTMコールの境界条件"""
        spot = 50.0
        strike = 100.0
        time = 1.0
        rate = 0.05
        sigma = 0.2

        price = black_scholes.call_price(spot, strike, time, rate, sigma)

        # Deep OTM call should be close to zero
        assert price < 0.01

    def test_zero_volatility_call(self) -> None:
        """ゼロボラティリティの境界条件"""
        spot = 110.0
        strike = 100.0
        time = 1.0
        rate = 0.05
        sigma = 0.001  # Near-zero volatility

        price = black_scholes.call_price(spot, strike, time, rate, sigma)
        intrinsic = max(spot - strike * np.exp(-rate * time), 0)

        # With zero vol, price should equal intrinsic value
        assert abs(price - intrinsic) < 0.01

    def test_zero_time_to_expiry(self) -> None:
        """満期時点での価格"""
        spot = 105.0
        strike = 100.0
        time = 0.001  # Near expiry
        rate = 0.05
        sigma = 0.2

        call_price = black_scholes.call_price(spot, strike, time, rate, sigma)
        put_price = black_scholes.put_price(spot, strike, time, rate, sigma)

        # At expiry, prices should equal intrinsic values
        call_intrinsic = max(spot - strike, 0)
        put_intrinsic = max(strike - spot, 0)

        assert abs(call_price - call_intrinsic) < 0.1
        assert abs(put_price - put_intrinsic) < 0.1
