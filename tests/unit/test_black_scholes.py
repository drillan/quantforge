"""Comprehensive unit tests for Black-Scholes model module."""

import math

import numpy as np
import pytest
from quantforge.models import black_scholes

from tests.conftest import (
    THEORETICAL_TOLERANCE,
    arrow,
    create_test_array,
    INPUT_ARRAY_TYPES,
)


class TestBlackScholesCallPrice:
    """Test Black-Scholes call price calculation."""

    def test_call_price_atm(self) -> None:
        """Test call price for at-the-money option."""
        price = black_scholes.call_price(s=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert price > 0
        assert price < 100.0  # Call price must be less than spot
        # ATM call with these parameters should be around 10.45
        assert abs(price - 10.45) < 0.5

    def test_call_price_itm(self) -> None:
        """Test call price for in-the-money option."""
        price = black_scholes.call_price(s=110.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        intrinsic = 110.0 - 100.0 * math.exp(-0.05 * 1.0)
        assert price > intrinsic  # Must be worth at least intrinsic value
        assert price < 110.0  # But less than spot

    def test_call_price_otm(self) -> None:
        """Test call price for out-of-the-money option."""
        price = black_scholes.call_price(s=90.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert price > 0  # Even OTM options have positive value
        assert price < 10.0  # But should be relatively small

    def test_call_price_deep_itm(self) -> None:
        """Test call price for deep in-the-money option."""
        price = black_scholes.call_price(s=200.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        intrinsic = 200.0 - 100.0 * math.exp(-0.05 * 1.0)
        assert abs(price - intrinsic) < 1.0  # Should be close to intrinsic

    def test_call_price_deep_otm(self) -> None:
        """Test call price for deep out-of-the-money option."""
        price = black_scholes.call_price(s=50.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert price < 0.01  # Should be nearly worthless

    def test_call_price_zero_volatility(self) -> None:
        """Test call price with very low volatility."""
        with pytest.raises(ValueError):
            # Zero volatility should raise error
            black_scholes.call_price(s=100.0, k=100.0, t=1.0, r=0.05, sigma=0.0)

    def test_call_price_high_volatility(self) -> None:
        """Test call price with high volatility."""
        price = black_scholes.call_price(s=100.0, k=100.0, t=1.0, r=0.05, sigma=1.0)
        assert price > 20.0  # High vol means high option value
        assert price < 100.0

    def test_call_price_zero_time(self) -> None:
        """Test call price at expiration."""
        with pytest.raises(ValueError):
            # Zero time should raise error
            black_scholes.call_price(s=100.0, k=100.0, t=0.0, r=0.05, sigma=0.2)

    def test_call_price_negative_rate(self) -> None:
        """Test call price with negative interest rate."""
        price = black_scholes.call_price(s=100.0, k=100.0, t=1.0, r=-0.02, sigma=0.2)
        assert price > 0
        assert price < 100.0

    def test_call_price_invalid_inputs(self) -> None:
        """Test call price with invalid inputs."""
        with pytest.raises(ValueError):
            black_scholes.call_price(s=-100.0, k=100.0, t=1.0, r=0.05, sigma=0.2)

        with pytest.raises(ValueError):
            black_scholes.call_price(s=100.0, k=-100.0, t=1.0, r=0.05, sigma=0.2)

        with pytest.raises(ValueError):
            black_scholes.call_price(s=100.0, k=100.0, t=-1.0, r=0.05, sigma=0.2)


class TestBlackScholesPutPrice:
    """Test Black-Scholes put price calculation."""

    def test_put_price_atm(self) -> None:
        """Test put price for at-the-money option."""
        price = black_scholes.put_price(s=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert price > 0
        assert price < 100.0
        # ATM put with these parameters should be around 5.57
        assert abs(price - 5.57) < 0.5

    def test_put_price_itm(self) -> None:
        """Test put price for in-the-money option."""
        price = black_scholes.put_price(s=90.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        intrinsic = 100.0 * math.exp(-0.05 * 1.0) - 90.0
        assert price > intrinsic

    def test_put_price_otm(self) -> None:
        """Test put price for out-of-the-money option."""
        price = black_scholes.put_price(s=110.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert price > 0
        assert price < 10.0

    def test_put_price_deep_itm(self) -> None:
        """Test put price for deep in-the-money option."""
        price = black_scholes.put_price(s=50.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        intrinsic = 100.0 * math.exp(-0.05 * 1.0) - 50.0
        assert abs(price - intrinsic) < 1.0

    def test_put_price_deep_otm(self) -> None:
        """Test put price for deep out-of-the-money option."""
        price = black_scholes.put_price(s=150.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert price < 0.1  # Deep OTM put still has some value

    def test_put_call_parity(self) -> None:
        """Test put-call parity relationship."""
        s, k, t, r, sigma = 100.0, 95.0, 1.0, 0.05, 0.2
        call = black_scholes.call_price(s, k, t, r, sigma)
        put = black_scholes.put_price(s, k, t, r, sigma)

        # Put-Call Parity: C - P = S - K * exp(-r*t)
        lhs = call - put
        rhs = s - k * math.exp(-r * t)
        assert abs(lhs - rhs) < THEORETICAL_TOLERANCE


class TestBlackScholesBatch:
    """Test Black-Scholes batch processing."""

    @pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
    def test_call_price_batch_single(self, array_type: str) -> None:
        """Test batch processing with single element."""
        spots = create_test_array([100.0], array_type)
        strikes = create_test_array([100.0], array_type)
        times = create_test_array([1.0], array_type)
        rates = create_test_array([0.05], array_type)
        sigmas = create_test_array([0.2], array_type)
        prices = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)
        assert len(prices) == 1
        arrow.assert_type(prices)
        single_price = black_scholes.call_price(s=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert abs(arrow.get_value(prices, 0) - single_price) < THEORETICAL_TOLERANCE

    @pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
    def test_call_price_batch_multiple(self, array_type: str) -> None:
        """Test batch processing with multiple spots."""
        spots = create_test_array([90.0, 100.0, 110.0], array_type)
        strikes = create_test_array([100.0, 100.0, 100.0], array_type)
        times = create_test_array([1.0, 1.0, 1.0], array_type)
        rates = create_test_array([0.05, 0.05, 0.05], array_type)
        sigmas = create_test_array([0.2, 0.2, 0.2], array_type)
        prices = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)
        assert len(prices) == 3
        arrow.assert_type(prices)
        prices_list = arrow.to_list(prices)
        assert prices_list[0] < prices_list[1] < prices_list[2]  # Monotonic in spot

    @pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
    def test_put_price_batch_single(self, array_type: str) -> None:
        """Test put batch processing with single element."""
        spots = create_test_array([100.0], array_type)
        strikes = create_test_array([100.0], array_type)
        times = create_test_array([1.0], array_type)
        rates = create_test_array([0.05], array_type)
        sigmas = create_test_array([0.2], array_type)
        prices = black_scholes.put_price_batch(spots, strikes, times, rates, sigmas)
        assert len(prices) == 1
        arrow.assert_type(prices)
        single_price = black_scholes.put_price(s=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert abs(arrow.get_value(prices, 0) - single_price) < THEORETICAL_TOLERANCE

    @pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
    def test_put_price_batch_multiple(self, array_type: str) -> None:
        """Test put batch processing with multiple spots."""
        spots = create_test_array([90.0, 100.0, 110.0], array_type)
        strikes = create_test_array([100.0, 100.0, 100.0], array_type)
        times = create_test_array([1.0, 1.0, 1.0], array_type)
        rates = create_test_array([0.05, 0.05, 0.05], array_type)
        sigmas = create_test_array([0.2, 0.2, 0.2], array_type)
        prices = black_scholes.put_price_batch(spots, strikes, times, rates, sigmas)
        assert len(prices) == 3
        arrow.assert_type(prices)
        prices_list = arrow.to_list(prices)
        assert prices_list[0] > prices_list[1] > prices_list[2]  # Monotonic decreasing in spot

    @pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
    def test_batch_consistency(self, array_type: str) -> None:
        """Test batch results match individual calculations."""
        spots_np = np.linspace(80, 120, 10)
        n = len(spots_np)
        spots = create_test_array(spots_np.tolist(), array_type)
        strikes = create_test_array([100.0] * n, array_type)
        times = create_test_array([1.0] * n, array_type)
        rates = create_test_array([0.05] * n, array_type)
        sigmas = create_test_array([0.2] * n, array_type)
        call_batch = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)
        put_batch = black_scholes.put_price_batch(spots, strikes, times, rates, sigmas)
        
        arrow.assert_type(call_batch)
        arrow.assert_type(put_batch)

        for i, spot in enumerate(spots_np):
            call_single = black_scholes.call_price(s=spot, k=100.0, t=1.0, r=0.05, sigma=0.2)
            put_single = black_scholes.put_price(s=spot, k=100.0, t=1.0, r=0.05, sigma=0.2)
            assert abs(arrow.get_value(call_batch, i) - call_single) < THEORETICAL_TOLERANCE
            assert abs(arrow.get_value(put_batch, i) - put_single) < THEORETICAL_TOLERANCE

    @pytest.mark.skip(reason="NumPy API migrated to Arrow")
    def test_batch_with_invalid_spots(self) -> None:
        """Test batch processing with invalid spots."""
        spots = np.array([100.0, -50.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        sigmas = np.array([0.2, 0.2, 0.2])
        # Invalid spot should raise an error now (validation enhanced)
        with pytest.raises(ValueError, match="spot must be positive"):
            black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)

    @pytest.mark.skip(reason="NumPy API migrated to Arrow")
    def test_empty_batch(self) -> None:
        """Test batch processing with empty array."""
        spots = np.array([])
        strikes = np.array([])
        times = np.array([])
        rates = np.array([])
        sigmas = np.array([])
        prices = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)
        assert len(prices) == 0


class TestBlackScholesGreeks:
    """Test Black-Scholes Greeks calculation."""

    def test_greeks_call(self) -> None:
        """Test Greeks for call option."""
        greeks = black_scholes.greeks(s=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2, is_call=True)

        # Delta should be between 0 and 1 for calls
        assert 0 < greeks["delta"] < 1
        # ATM delta should be around 0.6 for these parameters
        assert abs(greeks["delta"] - 0.64) < 0.05

        # Gamma should be positive
        assert greeks["gamma"] > 0

        # Vega should be positive
        assert greeks["vega"] > 0

        # Theta should be negative for calls
        assert greeks["theta"] < 0

        # Rho should be positive for calls
        assert greeks["rho"] > 0

    def test_greeks_put(self) -> None:
        """Test Greeks for put option."""
        greeks = black_scholes.greeks(s=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2, is_call=False)

        # Delta should be between -1 and 0 for puts
        assert -1 < greeks["delta"] < 0
        # ATM put delta should be around -0.36 for these parameters
        assert abs(greeks["delta"] + 0.36) < 0.05

        # Gamma should be positive (same as call)
        assert greeks["gamma"] > 0

        # Vega should be positive (same as call)
        assert greeks["vega"] > 0

        # Theta could be positive or negative for puts
        # depending on moneyness and rates

        # Rho should be negative for puts
        assert greeks["rho"] < 0

    def test_greeks_deep_itm_call(self) -> None:
        """Test Greeks for deep ITM call."""
        greeks = black_scholes.greeks(s=150.0, k=100.0, t=1.0, r=0.05, sigma=0.2, is_call=True)

        # Deep ITM call delta should be close to 1
        assert greeks["delta"] > 0.95

        # Gamma should be small for deep ITM
        assert greeks["gamma"] < 0.01

    def test_greeks_deep_otm_call(self) -> None:
        """Test Greeks for deep OTM call."""
        greeks = black_scholes.greeks(s=50.0, k=100.0, t=1.0, r=0.05, sigma=0.2, is_call=True)

        # Deep OTM call delta should be close to 0
        assert greeks["delta"] < 0.05

        # Gamma should be small for deep OTM
        assert greeks["gamma"] < 0.01

    @pytest.mark.skip(reason="NumPy API migrated to Arrow")
    def test_greeks_batch(self) -> None:
        """Test batch Greeks calculation."""
        spots = np.array([90.0, 100.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        sigmas = np.array([0.2, 0.2, 0.2])
        is_calls = np.array([1.0, 1.0, 1.0])  # 1.0 for calls, 0.0 for puts
        greeks_dict = black_scholes.greeks_batch(spots, strikes, times, rates, sigmas, is_calls)

        # greeks_batch returns a dictionary with arrays
        assert "delta" in greeks_dict
        assert len(greeks_dict["delta"]) == 3
        # Delta should increase with spot for calls
        assert greeks_dict["delta"][0] < greeks_dict["delta"][1] < greeks_dict["delta"][2]

    def test_greeks_invalid_inputs(self) -> None:
        """Test Greeks with invalid inputs."""
        with pytest.raises(ValueError):
            black_scholes.greeks(s=-100.0, k=100.0, t=1.0, r=0.05, sigma=0.2, is_call=True)


class TestBlackScholesImpliedVolatility:
    """Test Black-Scholes implied volatility calculation."""

    def test_implied_volatility_call(self) -> None:
        """Test implied volatility for call option."""
        # First calculate a price with known volatility
        true_sigma = 0.25
        price = black_scholes.call_price(s=100.0, k=100.0, t=1.0, r=0.05, sigma=true_sigma)

        # Now recover the volatility
        iv = black_scholes.implied_volatility(price=price, s=100.0, k=100.0, t=1.0, r=0.05, is_call=True)

        assert abs(iv - true_sigma) < THEORETICAL_TOLERANCE

    def test_implied_volatility_put(self) -> None:
        """Test implied volatility for put option."""
        true_sigma = 0.3
        price = black_scholes.put_price(s=100.0, k=100.0, t=1.0, r=0.05, sigma=true_sigma)

        iv = black_scholes.implied_volatility(price=price, s=100.0, k=100.0, t=1.0, r=0.05, is_call=False)

        assert abs(iv - true_sigma) < THEORETICAL_TOLERANCE

    def test_implied_volatility_with_guess(self) -> None:
        """Test implied volatility calculation."""
        true_sigma = 0.4
        price = black_scholes.call_price(s=100.0, k=100.0, t=1.0, r=0.05, sigma=true_sigma)

        # API doesn't support initial_guess parameter
        iv = black_scholes.implied_volatility(price=price, s=100.0, k=100.0, t=1.0, r=0.05, is_call=True)

        assert abs(iv - true_sigma) < THEORETICAL_TOLERANCE

    def test_implied_volatility_extreme_price(self) -> None:
        """Test implied volatility with extreme prices."""
        # Use reasonable extreme prices that respect arbitrage bounds
        # Low but valid price
        iv_low = black_scholes.implied_volatility(price=5.0, s=100.0, k=100.0, t=1.0, r=0.05, is_call=True)
        assert iv_low < 0.15

        # High but valid price
        iv_high = black_scholes.implied_volatility(price=30.0, s=100.0, k=100.0, t=1.0, r=0.05, is_call=True)
        assert iv_high > 0.5

    @pytest.mark.skip(reason="NumPy API migrated to Arrow")
    def test_implied_volatility_batch(self) -> None:
        """Test batch implied volatility calculation."""
        # Create prices with known volatilities
        sigmas = np.array([0.2, 0.25, 0.3])
        prices = np.array([black_scholes.call_price(s=100.0, k=100.0, t=1.0, r=0.05, sigma=sig) for sig in sigmas])

        spots = np.array([100.0, 100.0, 100.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        # Use scalar boolean for batch processing (will broadcast)
        ivs = black_scholes.implied_volatility_batch(prices, spots, strikes, times, rates, True)

        assert len(ivs) == 3
        for _i, (iv, true_sigma) in enumerate(zip(ivs, sigmas, strict=False)):
            assert abs(iv - true_sigma) < THEORETICAL_TOLERANCE

    def test_implied_volatility_invalid_price(self) -> None:
        """Test implied volatility with invalid price."""
        # Negative price should raise error
        with pytest.raises(ValueError):
            black_scholes.implied_volatility(price=-10.0, s=100.0, k=100.0, t=1.0, r=0.05, is_call=True)

        # Price above spot for call should raise error
        with pytest.raises((ValueError, RuntimeError)):  # May be RuntimeError for arbitrage
            black_scholes.implied_volatility(price=110.0, s=100.0, k=100.0, t=1.0, r=0.05, is_call=True)


class TestBlackScholesProperties:
    """Test mathematical properties of Black-Scholes model."""

    def test_call_price_monotonicity_spot(self) -> None:
        """Test call price increases with spot."""
        spots = np.linspace(80, 120, 10)
        prices = [black_scholes.call_price(s=s, k=100.0, t=1.0, r=0.05, sigma=0.2) for s in spots]
        for i in range(len(prices) - 1):
            assert prices[i] < prices[i + 1]

    def test_put_price_monotonicity_spot(self) -> None:
        """Test put price decreases with spot."""
        spots = np.linspace(80, 120, 10)
        prices = [black_scholes.put_price(s=s, k=100.0, t=1.0, r=0.05, sigma=0.2) for s in spots]
        for i in range(len(prices) - 1):
            assert prices[i] > prices[i + 1]

    def test_call_price_monotonicity_volatility(self) -> None:
        """Test call price increases with volatility."""
        sigmas = np.linspace(0.1, 0.5, 10)
        prices = [black_scholes.call_price(s=100.0, k=100.0, t=1.0, r=0.05, sigma=sig) for sig in sigmas]
        for i in range(len(prices) - 1):
            assert prices[i] < prices[i + 1]

    def test_price_bounds(self) -> None:
        """Test option prices respect arbitrage bounds."""
        s, k, t, r, sigma = 100.0, 95.0, 1.0, 0.05, 0.2

        call = black_scholes.call_price(s, k, t, r, sigma)
        put = black_scholes.put_price(s, k, t, r, sigma)

        # Call bounds: max(S - K*exp(-rt), 0) <= C <= S
        assert max(s - k * math.exp(-r * t), 0) <= call <= s

        # Put bounds: max(K*exp(-rt) - S, 0) <= P <= K*exp(-rt)
        assert max(k * math.exp(-r * t) - s, 0) <= put <= k * math.exp(-r * t)

    def test_time_decay(self) -> None:
        """Test options lose value as time decreases (theta effect)."""
        times = [2.0, 1.5, 1.0, 0.5, 0.1]
        call_prices = [black_scholes.call_price(s=100.0, k=100.0, t=t, r=0.05, sigma=0.2) for t in times]
        # ATM options should decrease in value as expiration approaches
        for i in range(len(call_prices) - 1):
            assert call_prices[i] > call_prices[i + 1]


class TestBlackScholesEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_short_time(self) -> None:
        """Test with very short time to expiration."""
        # Should approach intrinsic value
        call = black_scholes.call_price(s=110.0, k=100.0, t=0.001, r=0.05, sigma=0.2)
        intrinsic = max(110.0 - 100.0, 0)
        assert abs(call - intrinsic) < 0.1

    def test_very_long_time(self) -> None:
        """Test with very long time to expiration."""
        call = black_scholes.call_price(s=100.0, k=100.0, t=10.0, r=0.05, sigma=0.2)
        # Should have significant time value
        assert call > 20.0
        assert call < 100.0

    def test_very_low_volatility(self) -> None:
        """Test with very low but non-zero volatility."""
        # Use minimum allowed volatility (0.005 based on validation)
        call = black_scholes.call_price(s=100.0, k=100.0, t=1.0, r=0.05, sigma=0.005)
        # Should be close to intrinsic value
        intrinsic = max(100.0 - 100.0 * math.exp(-0.05), 0)
        assert abs(call - intrinsic) < 1.0

    def test_very_high_volatility(self) -> None:
        """Test with very high volatility."""
        call = black_scholes.call_price(s=100.0, k=100.0, t=1.0, r=0.05, sigma=2.0)
        # High volatility means high option value
        assert call > 30.0

    def test_extreme_moneyness_call(self) -> None:
        """Test extreme in and out of the money calls."""
        # Very deep ITM
        deep_itm = black_scholes.call_price(s=1000.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert abs(deep_itm - (1000.0 - 100.0 * math.exp(-0.05))) < 1.0

        # Very deep OTM
        deep_otm = black_scholes.call_price(s=1.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert deep_otm < 0.0001

    def test_extreme_moneyness_put(self) -> None:
        """Test extreme in and out of the money puts."""
        # Very deep ITM
        deep_itm = black_scholes.put_price(s=1.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert abs(deep_itm - (100.0 * math.exp(-0.05) - 1.0)) < 1.0

        # Very deep OTM
        deep_otm = black_scholes.put_price(s=1000.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert deep_otm < 0.0001


class TestBlackScholesNumericalStability:
    """Test numerical stability of Black-Scholes implementation."""

    def test_large_spot_values(self) -> None:
        """Test with very large spot prices."""
        call = black_scholes.call_price(s=10000.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert math.isfinite(call)
        assert call > 9800  # Should be close to S - K*exp(-rt)

    def test_small_spot_values(self) -> None:
        """Test with very small spot prices."""
        call = black_scholes.call_price(s=0.01, k=100.0, t=1.0, r=0.05, sigma=0.2)
        assert math.isfinite(call)
        assert call < 0.01  # Should be nearly zero

    def test_high_interest_rates(self) -> None:
        """Test with high interest rates."""
        call = black_scholes.call_price(s=100.0, k=100.0, t=1.0, r=0.5, sigma=0.2)
        assert math.isfinite(call)
        # High rates increase call value
        low_rate_call = black_scholes.call_price(s=100.0, k=100.0, t=1.0, r=0.01, sigma=0.2)
        assert call > low_rate_call

    def test_consistency_across_scales(self) -> None:
        """Test scaling property of Black-Scholes."""
        # Scaling spot and strike by same factor shouldn't change relative price
        price1 = black_scholes.call_price(s=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2)
        price2 = black_scholes.call_price(s=1000.0, k=1000.0, t=1.0, r=0.05, sigma=0.2)

        assert abs(price1 / 100.0 - price2 / 1000.0) < THEORETICAL_TOLERANCE
