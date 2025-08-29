"""Comprehensive unit tests for Black76 model module."""

import math
from typing import Any

import numpy as np
import pytest
from conftest import PRACTICAL_TOLERANCE, THEORETICAL_TOLERANCE
from quantforge.models import black76


class TestBlack76CallPrice:
    """Test Black76 call price calculation for futures options."""

    def test_call_price_atm(self) -> None:
        """Test call price for at-the-money futures option."""
        price = black76.call_price(f=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert price > 0
        # ATM call with these parameters should be around 7.97
        assert abs(price - 7.97) < 0.5

    def test_call_price_itm(self) -> None:
        """Test call price for in-the-money futures option."""
        price = black76.call_price(f=110.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        intrinsic = (110.0 - 100.0) * math.exp(-0.05 * 1.0)
        assert price > intrinsic  # Must be worth at least intrinsic value

    def test_call_price_otm(self) -> None:
        """Test call price for out-of-the-money futures option."""
        price = black76.call_price(f=90.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert price > 0  # Even OTM options have positive value
        assert price < 10.0  # But should be relatively small

    def test_call_price_deep_itm(self) -> None:
        """Test call price for deep in-the-money futures option."""
        price = black76.call_price(f=200.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        intrinsic = (200.0 - 100.0) * math.exp(-0.05 * 1.0)
        assert abs(price - intrinsic) < 1.0  # Should be close to intrinsic

    def test_call_price_deep_otm(self) -> None:
        """Test call price for deep out-of-the-money futures option."""
        price = black76.call_price(f=50.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert price < 0.01  # Should be nearly worthless

    def test_call_price_zero_volatility(self) -> None:
        """Test call price with zero volatility."""
        with pytest.raises(ValueError):
            black76.call_price(f=100.0, k=100.0, t=1.0, r=0.05, sigma=0.0)

    def test_call_price_high_volatility(self) -> None:
        """Test call price with high volatility."""
        price = black76.call_price(f=100.0, k=100.0, t=1.0, r=0.05, sigma=1.0)
        assert price > 15.0  # High vol means high option value

    def test_call_price_zero_time(self) -> None:
        """Test call price at expiration."""
        with pytest.raises(ValueError):
            black76.call_price(f=100.0, k=100.0, t=0.0, r=0.05, sigma=0.2)

    def test_call_price_negative_rate(self) -> None:
        """Test call price with negative interest rate."""
        price = black76.call_price(f=100.0, k=100.0, t=1.0, r=-0.02, sigma=0.2)
        assert price > 0

    def test_call_price_invalid_inputs(self) -> None:
        """Test call price with invalid inputs."""
        with pytest.raises(ValueError):
            black76.call_price(f=-100.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        
        with pytest.raises(ValueError):
            black76.call_price(f=100.0, k=-100.0, t=1.0, r=0.05, sigma=0.2)
        
        with pytest.raises(ValueError):
            black76.call_price(f=100.0, k=100.0, t=-1.0, r=0.05, sigma=0.2)


class TestBlack76PutPrice:
    """Test Black76 put price calculation for futures options."""

    def test_put_price_atm(self) -> None:
        """Test put price for at-the-money futures option."""
        price = black76.put_price(f=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert price > 0
        # ATM put with these parameters should be around 7.97 (same as call for ATM)
        assert abs(price - 7.97) < 0.5

    def test_put_price_itm(self) -> None:
        """Test put price for in-the-money futures option."""
        price = black76.put_price(f=90.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        intrinsic = (100.0 - 90.0) * math.exp(-0.05 * 1.0)
        assert price > intrinsic

    def test_put_price_otm(self) -> None:
        """Test put price for out-of-the-money futures option."""
        price = black76.put_price(f=110.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert price > 0
        assert price < 10.0

    def test_put_price_deep_itm(self) -> None:
        """Test put price for deep in-the-money futures option."""
        price = black76.put_price(f=50.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        intrinsic = (100.0 - 50.0) * math.exp(-0.05 * 1.0)
        assert abs(price - intrinsic) < 1.0

    def test_put_price_deep_otm(self) -> None:
        """Test put price for deep out-of-the-money futures option."""
        price = black76.put_price(f=150.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert price < 0.1  # Deep OTM put still has some value

    def test_put_call_parity(self) -> None:
        """Test put-call parity relationship for futures options."""
        f, k, t, r, sigma = 100.0, 95.0, 1.0, 0.05, 0.2
        call = black76.call_price(f, k, t, r, sigma)
        put = black76.put_price(f, k, t, r, sigma)
        
        # Put-Call Parity for futures: C - P = exp(-r*t) * (F - K)
        lhs = call - put
        rhs = math.exp(-r * t) * (f - k)
        assert abs(lhs - rhs) < THEORETICAL_TOLERANCE


class TestBlack76Batch:
    """Test Black76 batch processing for futures options."""

    def test_call_price_batch_single(self) -> None:
        """Test batch processing with single element."""
        forwards = np.array([100.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        sigmas = np.array([0.2])
        prices = black76.call_price_batch(forwards, strikes, times, rates, sigmas)
        assert len(prices) == 1
        single_price = black76.call_price(f=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert abs(prices[0] - single_price) < THEORETICAL_TOLERANCE

    def test_call_price_batch_multiple(self) -> None:
        """Test batch processing with multiple forwards."""
        forwards = np.array([90.0, 100.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        sigmas = np.array([0.2, 0.2, 0.2])
        prices = black76.call_price_batch(forwards, strikes, times, rates, sigmas)
        assert len(prices) == 3
        assert prices[0] < prices[1] < prices[2]  # Monotonic in forward

    def test_put_price_batch_single(self) -> None:
        """Test put batch processing with single element."""
        forwards = np.array([100.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        sigmas = np.array([0.2])
        prices = black76.put_price_batch(forwards, strikes, times, rates, sigmas)
        assert len(prices) == 1
        single_price = black76.put_price(f=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert abs(prices[0] - single_price) < THEORETICAL_TOLERANCE

    def test_put_price_batch_multiple(self) -> None:
        """Test put batch processing with multiple forwards."""
        forwards = np.array([90.0, 100.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        sigmas = np.array([0.2, 0.2, 0.2])
        prices = black76.put_price_batch(forwards, strikes, times, rates, sigmas)
        assert len(prices) == 3
        assert prices[0] > prices[1] > prices[2]  # Monotonic decreasing in forward

    def test_batch_consistency(self) -> None:
        """Test batch results match individual calculations."""
        forwards = np.linspace(80, 120, 10)
        n = len(forwards)
        strikes = np.full(n, 100.0)
        times = np.full(n, 1.0)
        rates = np.full(n, 0.05)
        sigmas = np.full(n, 0.2)
        call_batch = black76.call_price_batch(forwards, strikes, times, rates, sigmas)
        put_batch = black76.put_price_batch(forwards, strikes, times, rates, sigmas)
        
        for i, forward in enumerate(forwards):
            call_single = black76.call_price(f=forward, k=100.0, t=1.0, r=0.05, sigma=0.2)
            put_single = black76.put_price(f=forward, k=100.0, t=1.0, r=0.05, sigma=0.2)
            assert abs(call_batch[i] - call_single) < THEORETICAL_TOLERANCE
            assert abs(put_batch[i] - put_single) < THEORETICAL_TOLERANCE

    def test_batch_with_invalid_forwards(self) -> None:
        """Test batch processing with invalid forwards."""
        forwards = np.array([100.0, -50.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        sigmas = np.array([0.2, 0.2, 0.2])
        prices = black76.call_price_batch(forwards, strikes, times, rates, sigmas)
        assert not np.isnan(prices[0])
        assert np.isnan(prices[1])  # Invalid forward returns NaN
        assert not np.isnan(prices[2])

    def test_empty_batch(self) -> None:
        """Test batch processing with empty array."""
        forwards = np.array([])
        strikes = np.array([])
        times = np.array([])
        rates = np.array([])
        sigmas = np.array([])
        prices = black76.call_price_batch(forwards, strikes, times, rates, sigmas)
        assert len(prices) == 0


class TestBlack76Greeks:
    """Test Black76 Greeks calculation for futures options."""

    def test_greeks_call(self) -> None:
        """Test Greeks for call futures option."""
        greeks = black76.greeks(f=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2, is_call=True)
        
        # Delta should be between 0 and 1 for calls
        assert 0 < greeks.delta < 1
        # ATM delta should be around 0.5 for futures
        assert abs(greeks.delta - 0.5) < 0.1
        
        # Gamma should be positive
        assert greeks.gamma > 0
        
        # Vega should be positive
        assert greeks.vega > 0
        
        # Theta should be negative for calls
        assert greeks.theta < 0
        
        # Rho for futures options
        assert greeks.rho != 0

    def test_greeks_put(self) -> None:
        """Test Greeks for put futures option."""
        greeks = black76.greeks(f=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2, is_call=False)
        
        # Delta should be between -1 and 0 for puts
        assert -1 < greeks.delta < 0
        # ATM put delta should be around -0.5 for futures
        assert abs(greeks.delta + 0.5) < 0.1
        
        # Gamma should be positive (same as call)
        assert greeks.gamma > 0
        
        # Vega should be positive (same as call)
        assert greeks.vega > 0
        
        # Theta for puts
        assert greeks.theta < 0
        
        # Rho for futures options
        assert greeks.rho != 0

    def test_greeks_deep_itm_call(self) -> None:
        """Test Greeks for deep ITM call futures option."""
        greeks = black76.greeks(f=150.0, k=100.0, t=1.0, r=0.05, sigma=0.2, is_call=True)
        
        # Deep ITM call delta should be close to 1
        assert greeks.delta > 0.9
        
        # Gamma should be small for deep ITM
        assert greeks.gamma < 0.01

    def test_greeks_deep_otm_call(self) -> None:
        """Test Greeks for deep OTM call futures option."""
        greeks = black76.greeks(f=50.0, k=100.0, t=1.0, r=0.05, sigma=0.2, is_call=True)
        
        # Deep OTM call delta should be close to 0
        assert greeks.delta < 0.1
        
        # Gamma should be small for deep OTM
        assert greeks.gamma < 0.01

    def test_greeks_batch(self) -> None:
        """Test batch Greeks calculation."""
        forwards = np.array([90.0, 100.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        sigmas = np.array([0.2, 0.2, 0.2])
        is_calls = np.array([True, True, True])
        greeks_dict = black76.greeks_batch(
            forwards, strikes, times, rates, sigmas, is_calls
        )
        
        # greeks_batch returns a dictionary with arrays
        assert 'delta' in greeks_dict
        assert len(greeks_dict['delta']) == 3
        # Delta should increase with forward for calls
        assert greeks_dict['delta'][0] < greeks_dict['delta'][1] < greeks_dict['delta'][2]

    def test_greeks_invalid_inputs(self) -> None:
        """Test Greeks with invalid inputs."""
        with pytest.raises(ValueError):
            black76.greeks(f=-100.0, k=100.0, t=1.0, r=0.05, sigma=0.2)


class TestBlack76ImpliedVolatility:
    """Test Black76 implied volatility calculation for futures options."""

    def test_implied_volatility_call(self) -> None:
        """Test implied volatility for call futures option."""
        # First calculate a price with known volatility
        true_sigma = 0.25
        price = black76.call_price(f=100.0, k=100.0, t=1.0, r=0.05, sigma=true_sigma)
        
        # Now recover the volatility
        iv = black76.implied_volatility(
            price=price, f=100.0, k=100.0, t=1.0, r=0.05, is_call=True
        )
        
        assert abs(iv - true_sigma) < THEORETICAL_TOLERANCE

    def test_implied_volatility_put(self) -> None:
        """Test implied volatility for put futures option."""
        true_sigma = 0.3
        price = black76.put_price(f=100.0, k=100.0, t=1.0, r=0.05, sigma=true_sigma)
        
        iv = black76.implied_volatility(
            price=price, f=100.0, k=100.0, t=1.0, r=0.05, is_call=False
        )
        
        assert abs(iv - true_sigma) < THEORETICAL_TOLERANCE

    def test_implied_volatility_extreme_price(self) -> None:
        """Test implied volatility with extreme prices."""
        # Use reasonable extreme prices that respect arbitrage bounds
        # Low but valid price
        iv_low = black76.implied_volatility(
            price=3.0, f=100.0, k=100.0, t=1.0, r=0.05, is_call=True
        )
        assert iv_low < 0.15
        
        # High but valid price  
        iv_high = black76.implied_volatility(
            price=25.0, f=100.0, k=100.0, t=1.0, r=0.05, is_call=True
        )
        assert iv_high > 0.5

    def test_implied_volatility_batch(self) -> None:
        """Test batch implied volatility calculation."""
        # Create prices with known volatilities
        sigmas = np.array([0.2, 0.25, 0.3])
        prices = np.array([
            black76.call_price(f=100.0, k=100.0, t=1.0, r=0.05, sigma=sig)
            for sig in sigmas
        ])
        
        forwards = np.array([100.0, 100.0, 100.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        is_calls = np.array([True, True, True])
        
        ivs = black76.implied_volatility_batch(
            prices, forwards, strikes, times, rates, is_calls
        )
        
        assert len(ivs) == 3
        for i, (iv, true_sigma) in enumerate(zip(ivs, sigmas)):
            assert abs(iv - true_sigma) < THEORETICAL_TOLERANCE

    def test_implied_volatility_invalid_price(self) -> None:
        """Test implied volatility with invalid price."""
        # Negative price should raise error
        with pytest.raises(ValueError):
            black76.implied_volatility(
                price=-10.0, f=100.0, k=100.0, t=1.0, r=0.05, is_call=True
            )
        
        # Price above theoretical maximum should raise error  
        with pytest.raises((ValueError, RuntimeError)):  # May be RuntimeError for arbitrage
            black76.implied_volatility(
                price=200.0, f=100.0, k=100.0, t=1.0, r=0.05, is_call=True
            )


class TestBlack76Properties:
    """Test mathematical properties of Black76 model."""

    def test_call_price_monotonicity_forward(self) -> None:
        """Test call price increases with forward."""
        forwards = np.linspace(80, 120, 10)
        prices = [
            black76.call_price(f=f, k=100.0, t=1.0, r=0.05, sigma=0.2)
            for f in forwards
        ]
        for i in range(len(prices) - 1):
            assert prices[i] < prices[i + 1]

    def test_put_price_monotonicity_forward(self) -> None:
        """Test put price decreases with forward."""
        forwards = np.linspace(80, 120, 10)
        prices = [
            black76.put_price(f=f, k=100.0, t=1.0, r=0.05, sigma=0.2)
            for f in forwards
        ]
        for i in range(len(prices) - 1):
            assert prices[i] > prices[i + 1]

    def test_call_price_monotonicity_volatility(self) -> None:
        """Test call price increases with volatility."""
        sigmas = np.linspace(0.1, 0.5, 10)
        prices = [
            black76.call_price(f=100.0, k=100.0, t=1.0, r=0.05, sigma=sig)
            for sig in sigmas
        ]
        for i in range(len(prices) - 1):
            assert prices[i] < prices[i + 1]

    def test_price_bounds(self) -> None:
        """Test futures option prices respect arbitrage bounds."""
        f, k, t, r, sigma = 100.0, 95.0, 1.0, 0.05, 0.2
        
        call = black76.call_price(f, k, t, r, sigma)
        put = black76.put_price(f, k, t, r, sigma)
        
        # Call bounds: max(exp(-rt)*(F - K), 0) <= C <= exp(-rt)*F
        discount = math.exp(-r * t)
        assert max(discount * (f - k), 0) <= call <= discount * f
        
        # Put bounds: max(exp(-rt)*(K - F), 0) <= P <= exp(-rt)*K
        assert max(discount * (k - f), 0) <= put <= discount * k

    def test_time_decay(self) -> None:
        """Test options lose value as time decreases (theta effect)."""
        times = [2.0, 1.5, 1.0, 0.5, 0.1]
        call_prices = [
            black76.call_price(f=100.0, k=100.0, t=t, r=0.05, sigma=0.2)
            for t in times
        ]
        # ATM options should decrease in value as expiration approaches
        for i in range(len(call_prices) - 1):
            assert call_prices[i] > call_prices[i + 1]


class TestBlack76EdgeCases:
    """Test edge cases and boundary conditions for Black76."""

    def test_very_short_time(self) -> None:
        """Test with very short time to expiration."""
        # Should approach intrinsic value
        call = black76.call_price(f=110.0, k=100.0, t=0.001, r=0.05, sigma=0.2)
        intrinsic = max((110.0 - 100.0) * math.exp(-0.05 * 0.001), 0)
        assert abs(call - intrinsic) < 0.1

    def test_very_long_time(self) -> None:
        """Test with very long time to expiration."""
        call = black76.call_price(f=100.0, k=100.0, t=10.0, r=0.05, sigma=0.2)
        # Should have significant time value
        assert call > 10.0

    def test_very_low_volatility(self) -> None:
        """Test with very low but non-zero volatility."""
        # Use minimum allowed volatility (0.005 based on validation)
        call = black76.call_price(f=100.0, k=100.0, t=1.0, r=0.05, sigma=0.005)
        # Should be close to intrinsic value
        intrinsic = max((100.0 - 100.0) * math.exp(-0.05), 0)
        assert call < 1.0  # Very low vol means low option value

    def test_very_high_volatility(self) -> None:
        """Test with very high volatility."""
        call = black76.call_price(f=100.0, k=100.0, t=1.0, r=0.05, sigma=2.0)
        # High volatility means high option value
        assert call > 20.0

    def test_extreme_moneyness_call(self) -> None:
        """Test extreme in and out of the money calls."""
        # Very deep ITM
        deep_itm = black76.call_price(f=1000.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert abs(deep_itm - (1000.0 - 100.0) * math.exp(-0.05)) < 1.0
        
        # Very deep OTM
        deep_otm = black76.call_price(f=1.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert deep_otm < 0.0001

    def test_extreme_moneyness_put(self) -> None:
        """Test extreme in and out of the money puts."""
        # Very deep ITM
        deep_itm = black76.put_price(f=1.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert abs(deep_itm - (100.0 - 1.0) * math.exp(-0.05)) < 1.0
        
        # Very deep OTM
        deep_otm = black76.put_price(f=1000.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert deep_otm < 0.0001


class TestBlack76NumericalStability:
    """Test numerical stability of Black76 implementation."""

    def test_large_forward_values(self) -> None:
        """Test with very large forward prices."""
        call = black76.call_price(f=10000.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert math.isfinite(call)
        discount = math.exp(-0.05)
        assert call > (10000.0 - 100.0) * discount * 0.9  # Close to intrinsic

    def test_small_forward_values(self) -> None:
        """Test with very small forward prices."""
        call = black76.call_price(f=0.01, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert math.isfinite(call)
        assert call < 0.01  # Should be nearly zero

    def test_high_interest_rates(self) -> None:
        """Test with high interest rates."""
        call = black76.call_price(f=100.0, k=100.0, t=1.0, r=0.5, sigma=0.2)
        assert math.isfinite(call)
        # Higher discount rate reduces present value
        low_rate_call = black76.call_price(f=100.0, k=100.0, t=1.0, r=0.01, sigma=0.2)
        assert call < low_rate_call

    def test_consistency_across_scales(self) -> None:
        """Test scaling property of Black76."""
        # Scaling forward and strike by same factor shouldn't change relative price
        price1 = black76.call_price(f=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        price2 = black76.call_price(f=1000.0, k=1000.0, t=1.0, r=0.05, sigma=0.2)
        
        # Prices should scale proportionally (accounting for discounting)
        assert abs(price1 / 100.0 - price2 / 1000.0) < THEORETICAL_TOLERANCE