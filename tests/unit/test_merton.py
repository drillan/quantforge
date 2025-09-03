"""Comprehensive unit tests for Merton model module (with dividends)."""

import math

import numpy as np
import pytest
from quantforge.models import merton

from tests.conftest import (
    INPUT_ARRAY_TYPES,
    THEORETICAL_TOLERANCE,
    arrow,
    create_test_array,
)


class TestMertonCallPrice:
    """Test Merton call price calculation with dividend yield."""

    def test_call_price_atm_no_dividend(self) -> None:
        """Test call price for at-the-money option with no dividend."""
        price = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price > 0
        assert price < 100.0
        # Should match Black-Scholes when q=0
        assert abs(price - 10.45) < 0.5

    def test_call_price_atm_with_dividend(self) -> None:
        """Test call price for at-the-money option with dividend."""
        price = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert price > 0
        # Dividend reduces call value
        no_div_price = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price < no_div_price

    def test_call_price_itm(self) -> None:
        """Test call price for in-the-money option with dividend."""
        price = merton.call_price(s=110.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        # Adjusted intrinsic value with dividend
        adj_spot = 110.0 * math.exp(-0.02 * 1.0)
        intrinsic = adj_spot - 100.0 * math.exp(-0.05 * 1.0)
        assert price > max(intrinsic, 0)

    def test_call_price_otm(self) -> None:
        """Test call price for out-of-the-money option with dividend."""
        price = merton.call_price(s=90.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert price > 0
        assert price < 10.0

    def test_call_price_deep_itm(self) -> None:
        """Test call price for deep in-the-money option with dividend."""
        price = merton.call_price(s=200.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        adj_spot = 200.0 * math.exp(-0.02 * 1.0)
        intrinsic = adj_spot - 100.0 * math.exp(-0.05 * 1.0)
        assert abs(price - intrinsic) < 1.0

    def test_call_price_deep_otm(self) -> None:
        """Test call price for deep out-of-the-money option with dividend."""
        price = merton.call_price(s=50.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert price < 0.01

    def test_call_price_high_dividend(self) -> None:
        """Test call price with high dividend yield."""
        price = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.1, sigma=0.2)
        assert price > 0
        # High dividend significantly reduces call value
        low_div_price = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.01, sigma=0.2)
        assert price < low_div_price

    def test_call_price_zero_volatility(self) -> None:
        """Test call price with zero volatility."""
        with pytest.raises(ValueError):
            merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.0)

    def test_call_price_near_expiry(self) -> None:
        """Test call price at near expiration."""
        # Near expiration with ITM option
        price = merton.call_price(s=105.0, k=100.0, t=0.001, r=0.05, q=0.02, sigma=0.2)
        intrinsic = max(105.0 - 100.0, 0.0)
        # Near expiry ITM option should be close to intrinsic value
        assert price >= intrinsic  # Must be at least intrinsic
        assert price < intrinsic + 0.5  # But not much more

    def test_call_price_negative_rate(self) -> None:
        """Test call price with negative interest rate."""
        price = merton.call_price(s=100.0, k=100.0, t=1.0, r=-0.02, q=0.01, sigma=0.2)
        assert price > 0

    def test_call_price_invalid_inputs(self) -> None:
        """Test call price with invalid inputs."""
        with pytest.raises(ValueError):
            merton.call_price(s=-100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)

        with pytest.raises(ValueError):
            merton.call_price(s=100.0, k=-100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)

        with pytest.raises(ValueError):
            merton.call_price(s=100.0, k=100.0, t=-1.0, r=0.05, q=0.02, sigma=0.2)


class TestMertonPutPrice:
    """Test Merton put price calculation with dividend yield."""

    def test_put_price_atm_no_dividend(self) -> None:
        """Test put price for at-the-money option with no dividend."""
        price = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price > 0
        # Should match Black-Scholes when q=0
        assert abs(price - 5.57) < 0.5

    def test_put_price_atm_with_dividend(self) -> None:
        """Test put price for at-the-money option with dividend."""
        price = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert price > 0
        # Dividend increases put value
        no_div_price = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price > no_div_price

    def test_put_price_itm(self) -> None:
        """Test put price for in-the-money option with dividend."""
        price = merton.put_price(s=90.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        adj_spot = 90.0 * math.exp(-0.02 * 1.0)
        intrinsic = 100.0 * math.exp(-0.05 * 1.0) - adj_spot
        assert price > max(intrinsic, 0)

    def test_put_price_otm(self) -> None:
        """Test put price for out-of-the-money option with dividend."""
        price = merton.put_price(s=110.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert price > 0
        assert price < 10.0

    def test_put_price_deep_itm(self) -> None:
        """Test put price for deep in-the-money option with dividend."""
        price = merton.put_price(s=50.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        adj_spot = 50.0 * math.exp(-0.02 * 1.0)
        intrinsic = 100.0 * math.exp(-0.05 * 1.0) - adj_spot
        assert abs(price - intrinsic) < 1.0

    def test_put_price_deep_otm(self) -> None:
        """Test put price for deep out-of-the-money option with dividend."""
        price = merton.put_price(s=150.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert price < 0.15  # Deep OTM put should have small value

    def test_put_call_parity_with_dividend(self) -> None:
        """Test put-call parity relationship with dividends."""
        s, k, t, r, q, sigma = 100.0, 95.0, 1.0, 0.05, 0.02, 0.2
        call = merton.call_price(s, k, t, r, q, sigma)
        put = merton.put_price(s, k, t, r, q, sigma)

        # Put-Call Parity with dividends: C - P = S*exp(-q*t) - K*exp(-r*t)
        lhs = call - put
        rhs = s * math.exp(-q * t) - k * math.exp(-r * t)
        assert abs(lhs - rhs) < THEORETICAL_TOLERANCE


class TestMertonBatch:
    """Test Merton batch processing with dividends."""

    @pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
    def test_call_price_batch_single(self, array_type: str) -> None:
        """Test batch processing with single element."""
        spots = create_test_array([100.0], array_type)
        strikes = create_test_array([100.0], array_type)
        times = create_test_array([1.0], array_type)
        rates = create_test_array([0.05], array_type)
        divs = create_test_array([0.02], array_type)
        sigmas = create_test_array([0.2], array_type)
        prices = merton.call_price_batch(spots, strikes, times, rates, divs, sigmas)
        arrow.assert_type(prices)
        prices_list = arrow.to_list(prices)
        assert len(prices_list) == 1
        single_price = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert abs(prices_list[0] - single_price) < THEORETICAL_TOLERANCE

    @pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
    def test_call_price_batch_multiple(self, array_type: str) -> None:
        """Test batch processing with multiple spots."""
        spots = create_test_array([90.0, 100.0, 110.0], array_type)
        strikes = create_test_array([100.0, 100.0, 100.0], array_type)
        times = create_test_array([1.0, 1.0, 1.0], array_type)
        rates = create_test_array([0.05, 0.05, 0.05], array_type)
        divs = create_test_array([0.02, 0.02, 0.02], array_type)
        sigmas = create_test_array([0.2, 0.2, 0.2], array_type)
        prices = merton.call_price_batch(spots, strikes, times, rates, divs, sigmas)
        arrow.assert_type(prices)
        prices_list = arrow.to_list(prices)
        assert len(prices_list) == 3
        assert prices_list[0] < prices_list[1] < prices_list[2]

    @pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
    def test_put_price_batch_single(self, array_type: str) -> None:
        """Test put batch processing with single element."""
        spots = create_test_array([100.0], array_type)
        strikes = create_test_array([100.0], array_type)
        times = create_test_array([1.0], array_type)
        rates = create_test_array([0.05], array_type)
        divs = create_test_array([0.02], array_type)
        sigmas = create_test_array([0.2], array_type)
        prices = merton.put_price_batch(spots, strikes, times, rates, divs, sigmas)
        arrow.assert_type(prices)
        prices_list = arrow.to_list(prices)
        assert len(prices_list) == 1
        single_price = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert abs(prices_list[0] - single_price) < THEORETICAL_TOLERANCE

    @pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
    def test_put_price_batch_multiple(self, array_type: str) -> None:
        """Test put batch processing with multiple spots."""
        spots = create_test_array([90.0, 100.0, 110.0], array_type)
        strikes = create_test_array([100.0, 100.0, 100.0], array_type)
        times = create_test_array([1.0, 1.0, 1.0], array_type)
        rates = create_test_array([0.05, 0.05, 0.05], array_type)
        divs = create_test_array([0.02, 0.02, 0.02], array_type)
        sigmas = create_test_array([0.2, 0.2, 0.2], array_type)
        prices = merton.put_price_batch(spots, strikes, times, rates, divs, sigmas)
        arrow.assert_type(prices)
        prices_list = arrow.to_list(prices)
        assert len(prices_list) == 3
        assert prices_list[0] > prices_list[1] > prices_list[2]

    @pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
    def test_batch_consistency(self, array_type: str) -> None:
        """Test batch results match individual calculations."""
        spots_np = np.linspace(80, 120, 10)
        n = len(spots_np)
        spots = create_test_array(spots_np.tolist(), array_type)
        strikes = create_test_array(np.full(n, 100.0).tolist(), array_type)
        times = create_test_array(np.full(n, 1.0).tolist(), array_type)
        rates = create_test_array(np.full(n, 0.05).tolist(), array_type)
        divs = create_test_array(np.full(n, 0.02).tolist(), array_type)
        sigmas = create_test_array(np.full(n, 0.2).tolist(), array_type)

        call_batch = merton.call_price_batch(spots, strikes, times, rates, divs, sigmas)
        put_batch = merton.put_price_batch(spots, strikes, times, rates, divs, sigmas)

        arrow.assert_type(call_batch)
        arrow.assert_type(put_batch)
        call_batch_list = arrow.to_list(call_batch)
        put_batch_list = arrow.to_list(put_batch)

        for i, spot in enumerate(spots_np):
            call_single = merton.call_price(s=spot, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
            put_single = merton.put_price(s=spot, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
            assert abs(call_batch_list[i] - call_single) < THEORETICAL_TOLERANCE
            assert abs(put_batch_list[i] - put_single) < THEORETICAL_TOLERANCE

    @pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
    def test_batch_with_varying_dividends(self, array_type: str) -> None:
        """Test batch processing with varying dividend yields."""
        spots = create_test_array([100.0, 100.0, 100.0], array_type)
        strikes = create_test_array([100.0, 100.0, 100.0], array_type)
        times = create_test_array([1.0, 1.0, 1.0], array_type)
        rates = create_test_array([0.05, 0.05, 0.05], array_type)
        divs = create_test_array([0.0, 0.02, 0.05], array_type)  # Varying dividends
        sigmas = create_test_array([0.2, 0.2, 0.2], array_type)

        call_prices = merton.call_price_batch(spots, strikes, times, rates, divs, sigmas)
        arrow.assert_type(call_prices)
        call_prices_list = arrow.to_list(call_prices)
        # Higher dividend should reduce call value
        assert call_prices_list[0] > call_prices_list[1] > call_prices_list[2]

        put_prices = merton.put_price_batch(spots, strikes, times, rates, divs, sigmas)
        arrow.assert_type(put_prices)
        put_prices_list = arrow.to_list(put_prices)
        # Higher dividend should increase put value
        assert put_prices_list[0] < put_prices_list[1] < put_prices_list[2]

    @pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
    def test_empty_batch(self, array_type: str) -> None:
        """Test batch processing with empty array."""
        spots = create_test_array([], array_type)
        strikes = create_test_array([], array_type)
        times = create_test_array([], array_type)
        rates = create_test_array([], array_type)
        divs = create_test_array([], array_type)
        sigmas = create_test_array([], array_type)
        prices = merton.call_price_batch(spots, strikes, times, rates, divs, sigmas)
        arrow.assert_type(prices)
        prices_list = arrow.to_list(prices)
        assert len(prices_list) == 0


class TestMertonGreeks:
    """Test Merton Greeks calculation with dividends."""

    def test_greeks_call(self) -> None:
        """Test Greeks for call option with dividend."""
        greeks = merton.greeks(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2, is_call=True)

        # Delta should be between 0 and 1 for calls
        assert 0 < greeks["delta"] < 1

        # Gamma should be positive
        assert greeks["gamma"] > 0

        # Vega should be positive
        assert greeks["vega"] > 0

        # Theta should be negative for calls (usually)
        assert greeks["theta"] < 0

        # Rho should be positive for calls
        assert greeks["rho"] > 0

        # Dividend sensitivity should be negative for calls
        assert "dividend_rho" in greeks
        assert greeks["dividend_rho"] < 0

    def test_greeks_put(self) -> None:
        """Test Greeks for put option with dividend."""
        greeks = merton.greeks(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2, is_call=False)

        # Delta should be between -1 and 0 for puts
        assert -1 < greeks["delta"] < 0

        # Gamma should be positive (same as call)
        assert greeks["gamma"] > 0

        # Vega should be positive (same as call)
        assert greeks["vega"] > 0

        # Rho should be negative for puts
        assert greeks["rho"] < 0

        # Dividend sensitivity should be positive for puts
        assert "dividend_rho" in greeks
        assert greeks["dividend_rho"] > 0

    def test_greeks_dividend_effect(self) -> None:
        """Test dividend effect on Greeks."""
        greeks_no_div = merton.greeks(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2, is_call=True)
        greeks_with_div = merton.greeks(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2, is_call=True)

        # Dividend reduces call delta
        assert greeks_with_div["delta"] < greeks_no_div["delta"]

    @pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
    def test_greeks_batch(self, array_type: str) -> None:
        """Test batch Greeks calculation."""
        spots = create_test_array([90.0, 100.0, 110.0], array_type)
        strikes = create_test_array([100.0, 100.0, 100.0], array_type)
        times = create_test_array([1.0, 1.0, 1.0], array_type)
        rates = create_test_array([0.05, 0.05, 0.05], array_type)
        divs = create_test_array([0.02, 0.02, 0.02], array_type)
        sigmas = create_test_array([0.2, 0.2, 0.2], array_type)
        # For batch processing with boolean, use scalar True (will broadcast)
        greeks_dict = merton.merton_greeks_batch(spots, strikes, times, rates, divs, sigmas, True)  # type: ignore[attr-defined]

        assert "delta" in greeks_dict
        delta_list = arrow.to_list(greeks_dict["delta"])
        assert len(delta_list) == 3
        # Delta should increase with spot for calls
        assert delta_list[0] < delta_list[1] < delta_list[2]

    def test_greeks_invalid_inputs(self) -> None:
        """Test Greeks with invalid inputs."""
        with pytest.raises(ValueError):
            merton.greeks(s=-100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2, is_call=True)


class TestMertonImpliedVolatility:
    """Test Merton implied volatility calculation with dividends."""

    def test_implied_volatility_call(self) -> None:
        """Test implied volatility for call option with dividend."""
        true_sigma = 0.25
        price = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=true_sigma)

        iv = merton.implied_volatility(price=price, s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, is_call=True)

        assert abs(iv - true_sigma) < THEORETICAL_TOLERANCE

    def test_implied_volatility_put(self) -> None:
        """Test implied volatility for put option with dividend."""
        true_sigma = 0.3
        price = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=true_sigma)

        iv = merton.implied_volatility(price=price, s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, is_call=False)

        assert abs(iv - true_sigma) < THEORETICAL_TOLERANCE

    @pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
    def test_implied_volatility_batch(self, array_type: str) -> None:
        """Test batch implied volatility calculation."""
        sigmas = np.array([0.2, 0.25, 0.3])
        prices_vals = [merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=sig) for sig in sigmas]
        prices = create_test_array(prices_vals, array_type)

        spots = create_test_array([100.0, 100.0, 100.0], array_type)
        strikes = create_test_array([100.0, 100.0, 100.0], array_type)
        times = create_test_array([1.0, 1.0, 1.0], array_type)
        rates = create_test_array([0.05, 0.05, 0.05], array_type)
        divs = create_test_array([0.02, 0.02, 0.02], array_type)
        # For batch processing with boolean, use scalar True (will broadcast)
        ivs = merton.implied_volatility_batch(prices, spots, strikes, times, rates, divs, True)

        arrow.assert_type(ivs)
        ivs_list = arrow.to_list(ivs)
        assert len(ivs_list) == 3
        for _i, (iv, true_sigma) in enumerate(zip(ivs_list, sigmas, strict=False)):
            assert abs(iv - true_sigma) < THEORETICAL_TOLERANCE

    def test_implied_volatility_invalid_price(self) -> None:
        """Test implied volatility with invalid price."""
        with pytest.raises(ValueError):
            merton.implied_volatility(price=-10.0, s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, is_call=True)


class TestMertonProperties:
    """Test mathematical properties of Merton model."""

    def test_call_price_monotonicity_spot(self) -> None:
        """Test call price increases with spot."""
        spots = np.linspace(80, 120, 10)
        prices = [merton.call_price(s=s, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2) for s in spots]
        for i in range(len(prices) - 1):
            assert prices[i] < prices[i + 1]

    def test_put_price_monotonicity_spot(self) -> None:
        """Test put price decreases with spot."""
        spots = np.linspace(80, 120, 10)
        prices = [merton.put_price(s=s, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2) for s in spots]
        for i in range(len(prices) - 1):
            assert prices[i] > prices[i + 1]

    def test_dividend_effect_on_call(self) -> None:
        """Test dividend reduces call value."""
        divs = np.linspace(0, 0.1, 10)
        prices = [merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=q, sigma=0.2) for q in divs]
        for i in range(len(prices) - 1):
            assert prices[i] > prices[i + 1]

    def test_dividend_effect_on_put(self) -> None:
        """Test dividend increases put value."""
        divs = np.linspace(0, 0.1, 10)
        prices = [merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=q, sigma=0.2) for q in divs]
        for i in range(len(prices) - 1):
            assert prices[i] < prices[i + 1]

    def test_price_bounds_with_dividend(self) -> None:
        """Test option prices respect arbitrage bounds with dividends."""
        s, k, t, r, q, sigma = 100.0, 95.0, 1.0, 0.05, 0.02, 0.2

        call = merton.call_price(s, k, t, r, q, sigma)
        put = merton.put_price(s, k, t, r, q, sigma)

        # Adjusted bounds with dividend
        adj_spot = s * math.exp(-q * t)
        disc_strike = k * math.exp(-r * t)

        # Call bounds
        assert max(adj_spot - disc_strike, 0) <= call <= adj_spot

        # Put bounds
        assert max(disc_strike - adj_spot, 0) <= put <= disc_strike


class TestMertonEdgeCases:
    """Test edge cases and boundary conditions for Merton model."""

    def test_zero_dividend_matches_black_scholes(self) -> None:
        """Test Merton with zero dividend matches Black-Scholes."""
        merton_call = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        merton_put = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)

        # Should match standard Black-Scholes values
        assert abs(merton_call - 10.45) < 0.5
        assert abs(merton_put - 5.57) < 0.5

    def test_very_high_dividend(self) -> None:
        """Test with very high dividend yield."""
        # High dividend makes calls less valuable
        call = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.5, sigma=0.2)
        assert call < 2.0  # Very low value

        # High dividend makes puts more valuable
        put = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.5, sigma=0.2)
        assert put > 20.0  # High value

    def test_dividend_equals_rate(self) -> None:
        """Test when dividend yield equals risk-free rate."""
        call = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.05, sigma=0.2)
        put = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.05, sigma=0.2)

        # When r=q, call and put should be equal for ATM
        assert abs(call - put) < 0.1

    def test_negative_dividend(self) -> None:
        """Test with negative dividend (storage cost)."""
        # Negative dividend increases call value
        call_pos_div = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        call_neg_div = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=-0.02, sigma=0.2)
        assert call_neg_div > call_pos_div

        # Negative dividend decreases put value
        put_pos_div = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        put_neg_div = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=-0.02, sigma=0.2)
        assert put_neg_div < put_pos_div

    def test_very_short_time(self) -> None:
        """Test with very short time to expiration."""
        call = merton.call_price(s=110.0, k=100.0, t=0.001, r=0.05, q=0.02, sigma=0.2)
        # Should approach adjusted intrinsic value
        adj_spot = 110.0 * math.exp(-0.02 * 0.001)
        intrinsic = max(adj_spot - 100.0, 0)
        assert abs(call - intrinsic) < 0.5

    def test_very_low_volatility(self) -> None:
        """Test with very low but non-zero volatility."""
        call = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.005)
        # Should be close to adjusted intrinsic value
        # adj_spot = 100.0 * math.exp(-0.02) ≈ 98.02
        # disc_strike = 100.0 * math.exp(-0.05) ≈ 95.12
        # intrinsic = max(adj_spot - disc_strike, 0) ≈ 2.90
        assert 2.5 < call < 3.5  # Should be close to intrinsic value


class TestMertonNumericalStability:
    """Test numerical stability of Merton implementation."""

    def test_large_spot_values(self) -> None:
        """Test with very large spot prices."""
        call = merton.call_price(s=10000.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert math.isfinite(call)
        # Should be close to adjusted intrinsic
        adj_spot = 10000.0 * math.exp(-0.02)
        disc_strike = 100.0 * math.exp(-0.05)
        assert call > (adj_spot - disc_strike) * 0.9

    def test_small_spot_values(self) -> None:
        """Test with very small spot prices."""
        call = merton.call_price(s=0.01, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert math.isfinite(call)
        assert call < 0.01

    def test_consistency_across_scales(self) -> None:
        """Test scaling property of Merton model."""
        price1 = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        price2 = merton.call_price(s=1000.0, k=1000.0, t=1.0, r=0.05, q=0.02, sigma=0.2)

        # Prices should scale proportionally
        assert abs(price1 / 100.0 - price2 / 1000.0) < THEORETICAL_TOLERANCE
