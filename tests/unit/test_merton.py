"""Comprehensive unit tests for Merton model module (with dividends)."""

import math
from typing import Any

import numpy as np
import pytest
from conftest import PRACTICAL_TOLERANCE, THEORETICAL_TOLERANCE
from quantforge.models import merton


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

    def test_call_price_zero_time(self) -> None:
        """Test call price at expiration."""
        with pytest.raises(ValueError):
            merton.call_price(s=100.0, k=100.0, t=0.0, r=0.05, q=0.02, sigma=0.2)

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
        assert price < 0.1

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

    def test_call_price_batch_single(self) -> None:
        """Test batch processing with single element."""
        spots = np.array([100.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        divs = np.array([0.02])
        sigmas = np.array([0.2])
        prices = merton.call_price_batch(spots, strikes, times, rates, divs, sigmas)
        assert len(prices) == 1
        single_price = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert abs(prices[0] - single_price) < THEORETICAL_TOLERANCE

    def test_call_price_batch_multiple(self) -> None:
        """Test batch processing with multiple spots."""
        spots = np.array([90.0, 100.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        divs = np.array([0.02, 0.02, 0.02])
        sigmas = np.array([0.2, 0.2, 0.2])
        prices = merton.call_price_batch(spots, strikes, times, rates, divs, sigmas)
        assert len(prices) == 3
        assert prices[0] < prices[1] < prices[2]

    def test_put_price_batch_single(self) -> None:
        """Test put batch processing with single element."""
        spots = np.array([100.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        divs = np.array([0.02])
        sigmas = np.array([0.2])
        prices = merton.put_price_batch(spots, strikes, times, rates, divs, sigmas)
        assert len(prices) == 1
        single_price = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert abs(prices[0] - single_price) < THEORETICAL_TOLERANCE

    def test_put_price_batch_multiple(self) -> None:
        """Test put batch processing with multiple spots."""
        spots = np.array([90.0, 100.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        divs = np.array([0.02, 0.02, 0.02])
        sigmas = np.array([0.2, 0.2, 0.2])
        prices = merton.put_price_batch(spots, strikes, times, rates, divs, sigmas)
        assert len(prices) == 3
        assert prices[0] > prices[1] > prices[2]

    def test_batch_consistency(self) -> None:
        """Test batch results match individual calculations."""
        spots = np.linspace(80, 120, 10)
        n = len(spots)
        strikes = np.full(n, 100.0)
        times = np.full(n, 1.0)
        rates = np.full(n, 0.05)
        divs = np.full(n, 0.02)
        sigmas = np.full(n, 0.2)
        
        call_batch = merton.call_price_batch(spots, strikes, times, rates, divs, sigmas)
        put_batch = merton.put_price_batch(spots, strikes, times, rates, divs, sigmas)
        
        for i, spot in enumerate(spots):
            call_single = merton.call_price(s=spot, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
            put_single = merton.put_price(s=spot, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
            assert abs(call_batch[i] - call_single) < THEORETICAL_TOLERANCE
            assert abs(put_batch[i] - put_single) < THEORETICAL_TOLERANCE

    def test_batch_with_varying_dividends(self) -> None:
        """Test batch processing with varying dividend yields."""
        spots = np.array([100.0, 100.0, 100.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        divs = np.array([0.0, 0.02, 0.05])  # Varying dividends
        sigmas = np.array([0.2, 0.2, 0.2])
        
        call_prices = merton.call_price_batch(spots, strikes, times, rates, divs, sigmas)
        # Higher dividend should reduce call value
        assert call_prices[0] > call_prices[1] > call_prices[2]
        
        put_prices = merton.put_price_batch(spots, strikes, times, rates, divs, sigmas)
        # Higher dividend should increase put value
        assert put_prices[0] < put_prices[1] < put_prices[2]

    def test_empty_batch(self) -> None:
        """Test batch processing with empty array."""
        spots = np.array([])
        strikes = np.array([])
        times = np.array([])
        rates = np.array([])
        divs = np.array([])
        sigmas = np.array([])
        prices = merton.call_price_batch(spots, strikes, times, rates, divs, sigmas)
        assert len(prices) == 0


class TestMertonGreeks:
    """Test Merton Greeks calculation with dividends."""

    def test_greeks_call(self) -> None:
        """Test Greeks for call option with dividend."""
        greeks = merton.greeks(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2, is_call=True)
        
        # Delta should be between 0 and 1 for calls
        assert 0 < greeks.delta < 1
        
        # Gamma should be positive
        assert greeks.gamma > 0
        
        # Vega should be positive
        assert greeks.vega > 0
        
        # Theta should be negative for calls (usually)
        assert greeks.theta < 0
        
        # Rho should be positive for calls
        assert greeks.rho > 0
        
        # Psi (dividend sensitivity) should be negative for calls
        assert hasattr(greeks, 'psi')
        assert greeks.psi < 0

    def test_greeks_put(self) -> None:
        """Test Greeks for put option with dividend."""
        greeks = merton.greeks(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2, is_call=False)
        
        # Delta should be between -1 and 0 for puts
        assert -1 < greeks.delta < 0
        
        # Gamma should be positive (same as call)
        assert greeks.gamma > 0
        
        # Vega should be positive (same as call)
        assert greeks.vega > 0
        
        # Rho should be negative for puts
        assert greeks.rho < 0
        
        # Psi (dividend sensitivity) should be positive for puts
        assert hasattr(greeks, 'psi')
        assert greeks.psi > 0

    def test_greeks_dividend_effect(self) -> None:
        """Test dividend effect on Greeks."""
        greeks_no_div = merton.greeks(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2, is_call=True)
        greeks_with_div = merton.greeks(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2, is_call=True)
        
        # Dividend reduces call delta
        assert greeks_with_div.delta < greeks_no_div.delta

    def test_greeks_batch(self) -> None:
        """Test batch Greeks calculation."""
        spots = np.array([90.0, 100.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        divs = np.array([0.02, 0.02, 0.02])
        sigmas = np.array([0.2, 0.2, 0.2])
        is_calls = np.array([True, True, True])
        
        greeks_dict = merton.greeks_batch(
            spots, strikes, times, rates, divs, sigmas, is_calls
        )
        
        assert 'delta' in greeks_dict
        assert len(greeks_dict['delta']) == 3
        # Delta should increase with spot for calls
        assert greeks_dict['delta'][0] < greeks_dict['delta'][1] < greeks_dict['delta'][2]

    def test_greeks_invalid_inputs(self) -> None:
        """Test Greeks with invalid inputs."""
        with pytest.raises(ValueError):
            merton.greeks(s=-100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)


class TestMertonImpliedVolatility:
    """Test Merton implied volatility calculation with dividends."""

    def test_implied_volatility_call(self) -> None:
        """Test implied volatility for call option with dividend."""
        true_sigma = 0.25
        price = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=true_sigma)
        
        iv = merton.implied_volatility(
            price=price, s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, is_call=True
        )
        
        assert abs(iv - true_sigma) < THEORETICAL_TOLERANCE

    def test_implied_volatility_put(self) -> None:
        """Test implied volatility for put option with dividend."""
        true_sigma = 0.3
        price = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=true_sigma)
        
        iv = merton.implied_volatility(
            price=price, s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, is_call=False
        )
        
        assert abs(iv - true_sigma) < THEORETICAL_TOLERANCE

    def test_implied_volatility_batch(self) -> None:
        """Test batch implied volatility calculation."""
        sigmas = np.array([0.2, 0.25, 0.3])
        prices = np.array([
            merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=sig)
            for sig in sigmas
        ])
        
        spots = np.array([100.0, 100.0, 100.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        divs = np.array([0.02, 0.02, 0.02])
        is_calls = np.array([True, True, True])
        
        ivs = merton.implied_volatility_batch(
            prices, spots, strikes, times, rates, divs, is_calls
        )
        
        assert len(ivs) == 3
        for i, (iv, true_sigma) in enumerate(zip(ivs, sigmas)):
            assert abs(iv - true_sigma) < THEORETICAL_TOLERANCE

    def test_implied_volatility_invalid_price(self) -> None:
        """Test implied volatility with invalid price."""
        with pytest.raises(ValueError):
            merton.implied_volatility(
                price=-10.0, s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, is_call=True
            )


class TestMertonProperties:
    """Test mathematical properties of Merton model."""

    def test_call_price_monotonicity_spot(self) -> None:
        """Test call price increases with spot."""
        spots = np.linspace(80, 120, 10)
        prices = [
            merton.call_price(s=s, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
            for s in spots
        ]
        for i in range(len(prices) - 1):
            assert prices[i] < prices[i + 1]

    def test_put_price_monotonicity_spot(self) -> None:
        """Test put price decreases with spot."""
        spots = np.linspace(80, 120, 10)
        prices = [
            merton.put_price(s=s, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
            for s in spots
        ]
        for i in range(len(prices) - 1):
            assert prices[i] > prices[i + 1]

    def test_dividend_effect_on_call(self) -> None:
        """Test dividend reduces call value."""
        divs = np.linspace(0, 0.1, 10)
        prices = [
            merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=q, sigma=0.2)
            for q in divs
        ]
        for i in range(len(prices) - 1):
            assert prices[i] > prices[i + 1]

    def test_dividend_effect_on_put(self) -> None:
        """Test dividend increases put value."""
        divs = np.linspace(0, 0.1, 10)
        prices = [
            merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=q, sigma=0.2)
            for q in divs
        ]
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
        adj_spot = 100.0 * math.exp(-0.02)
        disc_strike = 100.0 * math.exp(-0.05)
        intrinsic = max(adj_spot - disc_strike, 0)
        assert call < 1.0


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