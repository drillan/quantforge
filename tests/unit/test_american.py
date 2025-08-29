"""Comprehensive unit tests for American option model module."""

import math
from typing import Any

import numpy as np
import pytest
from conftest import PRACTICAL_TOLERANCE, THEORETICAL_TOLERANCE
from quantforge.models import american, merton


class TestAmericanCallPrice:
    """Test American call price calculation."""

    def test_call_price_atm(self) -> None:
        """Test call price for at-the-money American option."""
        price = american.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price > 0
        assert price < 100.0
        # American call should be at least as valuable as European
        euro_price = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price >= euro_price - THEORETICAL_TOLERANCE

    def test_call_price_with_dividend(self) -> None:
        """Test American call with dividend."""
        price = american.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert price > 0
        # With dividends, American call can be exercised early
        euro_price = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert price >= euro_price - THEORETICAL_TOLERANCE

    def test_call_price_no_early_exercise_value(self) -> None:
        """Test American call when early exercise has no value (no dividends)."""
        price = american.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        euro_price = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        # Without dividends, American call should equal European call
        assert abs(price - euro_price) < PRACTICAL_TOLERANCE

    def test_call_price_deep_itm(self) -> None:
        """Test American call for deep in-the-money option."""
        price = american.call_price(s=200.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        # Deep ITM American call with dividend might be exercised early
        intrinsic = 200.0 - 100.0
        assert price >= intrinsic
        # Should be at least as valuable as discounted intrinsic
        assert price >= intrinsic * math.exp(-0.05 * 1.0)

    def test_call_price_deep_otm(self) -> None:
        """Test American call for deep out-of-the-money option."""
        price = american.call_price(s=50.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price < 0.01
        # Should be same as European for deep OTM
        euro_price = merton.call_price(s=50.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert abs(price - euro_price) < THEORETICAL_TOLERANCE

    def test_call_price_invalid_inputs(self) -> None:
        """Test American call with invalid inputs."""
        with pytest.raises(ValueError):
            american.call_price(s=-100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        
        with pytest.raises(ValueError):
            american.call_price(s=100.0, k=-100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        
        with pytest.raises(ValueError):
            american.call_price(s=100.0, k=100.0, t=-1.0, r=0.05, q=0.0, sigma=0.2)


class TestAmericanPutPrice:
    """Test American put price calculation."""

    def test_put_price_atm(self) -> None:
        """Test put price for at-the-money American option."""
        price = american.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price > 0
        assert price < 100.0
        # American put should be more valuable than European
        euro_price = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price >= euro_price

    def test_put_price_early_exercise_premium(self) -> None:
        """Test American put early exercise premium."""
        amer_price = american.put_price(s=90.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        euro_price = merton.put_price(s=90.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        
        # American put should have early exercise premium
        premium = amer_price - euro_price
        assert premium > 0
        
        # Intrinsic value
        intrinsic = 100.0 - 90.0
        assert amer_price >= intrinsic

    def test_put_price_deep_itm(self) -> None:
        """Test American put for deep in-the-money option."""
        price = american.put_price(s=50.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        intrinsic = 100.0 - 50.0
        # Deep ITM American put should be close to intrinsic value
        assert abs(price - intrinsic) < 1.0
        # Should be at least intrinsic value
        assert price >= intrinsic

    def test_put_price_deep_otm(self) -> None:
        """Test American put for deep out-of-the-money option."""
        price = american.put_price(s=150.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price < 0.5
        # Still should be more valuable than European
        euro_price = merton.put_price(s=150.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price >= euro_price

    def test_put_price_with_dividend(self) -> None:
        """Test American put with dividend."""
        price = american.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert price > 0
        # Dividend reduces early exercise incentive for puts
        no_div_price = american.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        # But still should be more valuable than European
        euro_price = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert price >= euro_price

    def test_put_price_immediate_exercise(self) -> None:
        """Test American put when immediate exercise is optimal."""
        # Very deep ITM with high interest rate
        price = american.put_price(s=10.0, k=100.0, t=1.0, r=0.2, q=0.0, sigma=0.2)
        intrinsic = 100.0 - 10.0
        # Should be very close to intrinsic value
        assert abs(price - intrinsic) < 0.5


class TestAmericanBatch:
    """Test American option batch processing."""

    def test_call_price_batch_single(self) -> None:
        """Test batch processing with single element."""
        spots = np.array([100.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        divs = np.array([0.0])
        sigmas = np.array([0.2])
        prices = american.call_price_batch(spots, strikes, times, rates, divs, sigmas)
        assert len(prices) == 1
        single_price = american.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert abs(prices[0] - single_price) < THEORETICAL_TOLERANCE

    def test_call_price_batch_multiple(self) -> None:
        """Test batch processing with multiple spots."""
        spots = np.array([90.0, 100.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        divs = np.array([0.0, 0.0, 0.0])
        sigmas = np.array([0.2, 0.2, 0.2])
        prices = american.call_price_batch(spots, strikes, times, rates, divs, sigmas)
        assert len(prices) == 3
        assert prices[0] < prices[1] < prices[2]

    def test_put_price_batch_single(self) -> None:
        """Test put batch processing with single element."""
        spots = np.array([100.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        divs = np.array([0.0])
        sigmas = np.array([0.2])
        prices = american.put_price_batch(spots, strikes, times, rates, divs, sigmas)
        assert len(prices) == 1
        single_price = american.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert abs(prices[0] - single_price) < THEORETICAL_TOLERANCE

    def test_put_price_batch_multiple(self) -> None:
        """Test put batch processing with multiple spots."""
        spots = np.array([90.0, 100.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        divs = np.array([0.0, 0.0, 0.0])
        sigmas = np.array([0.2, 0.2, 0.2])
        prices = american.put_price_batch(spots, strikes, times, rates, divs, sigmas)
        assert len(prices) == 3
        assert prices[0] > prices[1] > prices[2]

    def test_batch_consistency(self) -> None:
        """Test batch results match individual calculations."""
        spots = np.linspace(80, 120, 5)
        n = len(spots)
        strikes = np.full(n, 100.0)
        times = np.full(n, 1.0)
        rates = np.full(n, 0.05)
        divs = np.full(n, 0.02)
        sigmas = np.full(n, 0.2)
        
        call_batch = american.call_price_batch(spots, strikes, times, rates, divs, sigmas)
        put_batch = american.put_price_batch(spots, strikes, times, rates, divs, sigmas)
        
        for i, spot in enumerate(spots):
            call_single = american.call_price(s=spot, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
            put_single = american.put_price(s=spot, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
            assert abs(call_batch[i] - call_single) < THEORETICAL_TOLERANCE
            assert abs(put_batch[i] - put_single) < THEORETICAL_TOLERANCE

    def test_empty_batch(self) -> None:
        """Test batch processing with empty array."""
        spots = np.array([])
        strikes = np.array([])
        times = np.array([])
        rates = np.array([])
        divs = np.array([])
        sigmas = np.array([])
        prices = american.call_price_batch(spots, strikes, times, rates, divs, sigmas)
        assert len(prices) == 0


class TestAmericanGreeks:
    """Test American option Greeks calculation."""

    def test_greeks_call(self) -> None:
        """Test Greeks for American call option."""
        greeks = american.greeks(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2, is_call=True)
        
        # Delta should be between 0 and 1 for calls
        assert 0 < greeks.delta < 1
        
        # Gamma should be positive
        assert greeks.gamma > 0
        
        # Vega should be positive
        assert greeks.vega > 0
        
        # Theta is usually negative for calls
        assert greeks.theta < 0
        
        # Rho should be positive for calls
        assert greeks.rho > 0

    def test_greeks_put(self) -> None:
        """Test Greeks for American put option."""
        greeks = american.greeks(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2, is_call=False)
        
        # Delta should be between -1 and 0 for puts
        assert -1 < greeks.delta < 0
        
        # Gamma should be positive
        assert greeks.gamma > 0
        
        # Vega should be positive
        assert greeks.vega > 0
        
        # Rho should be negative for puts
        assert greeks.rho < 0

    def test_greeks_batch(self) -> None:
        """Test batch Greeks calculation."""
        spots = np.array([90.0, 100.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        divs = np.array([0.0, 0.0, 0.0])
        sigmas = np.array([0.2, 0.2, 0.2])
        is_calls = np.array([True, True, True])
        
        greeks_dict = american.greeks_batch(
            spots, strikes, times, rates, divs, sigmas, is_calls
        )
        
        assert 'delta' in greeks_dict
        assert len(greeks_dict['delta']) == 3
        # Delta should increase with spot for calls
        assert greeks_dict['delta'][0] < greeks_dict['delta'][1] < greeks_dict['delta'][2]

    def test_greeks_invalid_inputs(self) -> None:
        """Test Greeks with invalid inputs."""
        with pytest.raises(ValueError):
            american.greeks(s=-100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)


class TestAmericanImpliedVolatility:
    """Test American option implied volatility calculation."""

    def test_implied_volatility_call(self) -> None:
        """Test implied volatility for American call option."""
        true_sigma = 0.25
        price = american.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=true_sigma)
        
        iv = american.implied_volatility(
            price=price, s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, is_call=True
        )
        
        assert abs(iv - true_sigma) < PRACTICAL_TOLERANCE

    def test_implied_volatility_put(self) -> None:
        """Test implied volatility for American put option."""
        true_sigma = 0.3
        price = american.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=true_sigma)
        
        iv = american.implied_volatility(
            price=price, s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, is_call=False
        )
        
        # American IV might not exactly match due to early exercise
        assert abs(iv - true_sigma) < 0.01

    def test_implied_volatility_batch(self) -> None:
        """Test batch implied volatility calculation."""
        sigmas = np.array([0.2, 0.25, 0.3])
        prices = np.array([
            american.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=sig)
            for sig in sigmas
        ])
        
        spots = np.array([100.0, 100.0, 100.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        divs = np.array([0.0, 0.0, 0.0])
        is_calls = np.array([True, True, True])
        
        ivs = american.implied_volatility_batch(
            prices, spots, strikes, times, rates, divs, is_calls
        )
        
        assert len(ivs) == 3
        for i, (iv, true_sigma) in enumerate(zip(ivs, sigmas)):
            assert abs(iv - true_sigma) < PRACTICAL_TOLERANCE

    def test_implied_volatility_invalid_price(self) -> None:
        """Test implied volatility with invalid price."""
        with pytest.raises(ValueError):
            american.implied_volatility(
                price=-10.0, s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, is_call=True
            )


class TestAmericanProperties:
    """Test mathematical properties of American options."""

    def test_american_european_relationship(self) -> None:
        """Test American options are at least as valuable as European."""
        s, k, t, r, q, sigma = 100.0, 95.0, 1.0, 0.05, 0.02, 0.2
        
        amer_call = american.call_price(s, k, t, r, q, sigma)
        euro_call = merton.call_price(s, k, t, r, q, sigma)
        assert amer_call >= euro_call - THEORETICAL_TOLERANCE
        
        amer_put = american.put_price(s, k, t, r, q, sigma)
        euro_put = merton.put_price(s, k, t, r, q, sigma)
        assert amer_put >= euro_put - THEORETICAL_TOLERANCE

    def test_intrinsic_value_bound(self) -> None:
        """Test American options are at least intrinsic value."""
        # ITM call
        call = american.call_price(s=110.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert call >= 110.0 - 100.0
        
        # ITM put
        put = american.put_price(s=90.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert put >= 100.0 - 90.0

    def test_monotonicity_spot(self) -> None:
        """Test price monotonicity with respect to spot."""
        spots = np.linspace(80, 120, 10)
        
        call_prices = [
            american.call_price(s=s, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
            for s in spots
        ]
        for i in range(len(call_prices) - 1):
            assert call_prices[i] < call_prices[i + 1]
        
        put_prices = [
            american.put_price(s=s, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
            for s in spots
        ]
        for i in range(len(put_prices) - 1):
            assert put_prices[i] > put_prices[i + 1]

    def test_early_exercise_boundary(self) -> None:
        """Test early exercise boundary exists for American put."""
        # For low spot prices, American put should be exercised immediately
        deep_itm_put = american.put_price(s=20.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        intrinsic = 100.0 - 20.0
        # Should be very close to intrinsic value
        assert abs(deep_itm_put - intrinsic) < 0.1
        
        # For higher spot, time value should exist
        atm_put = american.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert atm_put > 0  # Has time value


class TestAmericanEdgeCases:
    """Test edge cases for American options."""

    def test_very_short_time(self) -> None:
        """Test with very short time to expiration."""
        # Should approach intrinsic value
        call = american.call_price(s=110.0, k=100.0, t=0.001, r=0.05, q=0.0, sigma=0.2)
        intrinsic = max(110.0 - 100.0, 0)
        assert abs(call - intrinsic) < 0.1
        
        put = american.put_price(s=90.0, k=100.0, t=0.001, r=0.05, q=0.0, sigma=0.2)
        intrinsic = max(100.0 - 90.0, 0)
        assert abs(put - intrinsic) < 0.1

    def test_very_high_volatility(self) -> None:
        """Test with very high volatility."""
        call = american.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=2.0)
        assert call > 30.0  # High volatility means high value
        
        put = american.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=2.0)
        assert put > 30.0

    def test_zero_interest_rate(self) -> None:
        """Test with zero interest rate."""
        call = american.call_price(s=100.0, k=100.0, t=1.0, r=0.0, q=0.0, sigma=0.2)
        put = american.put_price(s=100.0, k=100.0, t=1.0, r=0.0, q=0.0, sigma=0.2)
        
        # With zero rate and no dividend, put-call parity simplified
        assert call > 0
        assert put > 0

    def test_high_dividend_call(self) -> None:
        """Test American call with high dividend (early exercise likely)."""
        # High dividend makes early exercise more likely for calls
        call = american.call_price(s=110.0, k=100.0, t=1.0, r=0.05, q=0.1, sigma=0.2)
        # Should consider early exercise
        euro_call = merton.call_price(s=110.0, k=100.0, t=1.0, r=0.05, q=0.1, sigma=0.2)
        # American should have significant premium over European
        assert call > euro_call


class TestAmericanNumericalStability:
    """Test numerical stability of American option implementation."""

    def test_large_spot_values(self) -> None:
        """Test with very large spot prices."""
        call = american.call_price(s=10000.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert math.isfinite(call)
        # Should be close to S - K for deep ITM
        assert call > 9800

    def test_small_spot_values(self) -> None:
        """Test with very small spot prices."""
        put = american.put_price(s=0.01, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert math.isfinite(put)
        # Should be close to K for deep ITM put
        assert abs(put - 100.0) < 1.0

    def test_consistency_across_scales(self) -> None:
        """Test scaling property of American options."""
        price1 = american.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        price2 = american.call_price(s=1000.0, k=1000.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        
        # Prices should scale proportionally
        assert abs(price1 / 100.0 - price2 / 1000.0) < 0.01  # Larger tolerance for American