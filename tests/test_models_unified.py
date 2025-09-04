"""Unified test suite for all QuantForge models using base test classes.

This module replaces the duplicated test files (test_batch_processing.py,
test_batch_refactored.py, test_models_api.py, test_models_api_refactored.py)
with a single, maintainable test suite.
"""

import numpy as np
import pytest
from quantforge import black76, black_scholes, merton

from tests.base_testing import BaseBatchTest, to_numpy_array


class TestBlackScholes(BaseBatchTest):
    """Comprehensive tests for Black-Scholes model."""

    model = black_scholes  # type: ignore[assignment]
    use_forward_price = False
    has_dividend = False


class TestBlack76(BaseBatchTest):
    """Comprehensive tests for Black76 model."""

    model = black76  # type: ignore[assignment]
    use_forward_price = True
    has_dividend = False


class TestMerton(BaseBatchTest):
    """Comprehensive tests for Merton model (Black-Scholes with dividends)."""

    model = merton  # type: ignore[assignment]
    use_forward_price = False
    has_dividend = True


class TestModelSpecificFeatures:
    """Tests for model-specific features that don't fit the base pattern."""

    def test_black76_forward_price_interpretation(self) -> None:
        """Test that Black76 correctly interprets forward prices."""
        # Black76 uses forward price, not spot
        forward = 105.0
        strike = 100.0
        time = 1.0
        rate = 0.05
        sigma = 0.2

        call_price = black76.call_price(f=forward, k=strike, t=time, r=rate, sigma=sigma)

        # With forward > strike, call should have positive value
        assert call_price > 0

        # Price should be at least the discounted intrinsic value
        discounted_intrinsic = np.exp(-rate * time) * max(0, forward - strike)
        assert call_price >= discounted_intrinsic

    def test_merton_dividend_impact(self) -> None:
        """Test that Merton model correctly accounts for dividends."""
        spot = 100.0
        strike = 100.0
        time = 1.0
        rate = 0.05
        sigma = 0.2

        # Price without dividend (using Black-Scholes)
        price_no_div = black_scholes.call_price(s=spot, k=strike, t=time, r=rate, sigma=sigma)

        # Price with dividend (using Merton)
        dividend = 0.03
        price_with_div = merton.call_price(s=spot, k=strike, t=time, r=rate, q=dividend, sigma=sigma)

        # Dividend should reduce call value
        assert price_with_div < price_no_div

    def test_cross_model_consistency(self) -> None:
        """Test consistency between models in special cases."""
        spot = 100.0
        strike = 100.0
        time = 1.0
        rate = 0.05
        sigma = 0.2

        # Black-Scholes with no dividend
        bs_price = black_scholes.call_price(s=spot, k=strike, t=time, r=rate, sigma=sigma)

        # Merton with zero dividend should match Black-Scholes
        merton_price = merton.call_price(s=spot, k=strike, t=time, r=rate, q=0.0, sigma=sigma)

        assert abs(bs_price - merton_price) < 1e-10

        # Black76 with forward = spot * exp(rt) should match Black-Scholes
        forward = spot * np.exp(rate * time)
        black76_price = black76.call_price(f=forward, k=strike, t=time, r=rate, sigma=sigma)

        assert abs(bs_price - black76_price) < 1e-10


class TestBatchProcessingAdvanced:
    """Advanced batch processing tests not covered by base classes."""

    def test_vectorized_performance(self) -> None:
        """Ensure batch operations are properly vectorized."""
        import time

        n = 10000
        spots = np.random.uniform(80, 120, n)
        strikes = np.random.uniform(90, 110, n)
        times = np.random.uniform(0.1, 2.0, n)
        rates = np.random.uniform(0.01, 0.1, n)
        sigmas = np.random.uniform(0.1, 0.5, n)

        # Batch calculation
        start = time.perf_counter()
        batch_prices = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)
        batch_prices = to_numpy_array(batch_prices)
        batch_time = time.perf_counter() - start

        # Sequential calculation (first 100 only for time)
        start = time.perf_counter()
        sequential_prices = []
        for i in range(100):
            price = black_scholes.call_price(s=spots[i], k=strikes[i], t=times[i], r=rates[i], sigma=sigmas[i])
            sequential_prices.append(price)
        sequential_time = (time.perf_counter() - start) * (n / 100)  # Extrapolate

        # Batch should be significantly faster (at least 2x speedup)
        assert batch_time < sequential_time / 2, (
            f"Batch not faster: {batch_time:.3f}s vs {sequential_time:.3f}s sequential"
        )

        # Verify correctness (spot check first 10)
        for i in range(10):
            single_price = black_scholes.call_price(s=spots[i], k=strikes[i], t=times[i], r=rates[i], sigma=sigmas[i])
            assert abs(batch_prices[i] - single_price) < 1e-10

    def test_broadcasting_shapes(self) -> None:
        """Test various broadcasting shape combinations."""
        # Test all valid broadcasting combinations
        test_cases = [
            # (spots_shape, strikes_shape, times_shape, rates_shape, sigmas_shape, expected_shape)
            ((5,), (1,), (1,), (1,), (1,), (5,)),  # Broadcast all to spots
            ((1,), (5,), (1,), (1,), (1,), (5,)),  # Broadcast all to strikes
            ((3,), (3,), (1,), (1,), (1,), (3,)),  # Two arrays same size
            ((1,), (1,), (1,), (1,), (1,), (1,)),  # All scalars
            ((5,), (5,), (5,), (5,), (5,), (5,)),  # All same size
        ]

        for spots_shape, strikes_shape, times_shape, rates_shape, sigmas_shape, expected_shape in test_cases:
            spots = np.ones(spots_shape) * 100
            strikes = np.ones(strikes_shape) * 100
            times = np.ones(times_shape) * 1.0
            rates = np.ones(rates_shape) * 0.05
            sigmas = np.ones(sigmas_shape) * 0.2

            prices = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)
            prices = to_numpy_array(prices)

            assert prices.shape == expected_shape, f"Shape mismatch: got {prices.shape}, expected {expected_shape}"

    def test_mixed_data_types(self) -> None:
        """Test that different numeric types are handled correctly."""
        # Mix of Python types and numpy types
        spots = np.array([100.0, 105.0, 110.0])  # NumPy array (lists not supported)
        strikes = np.array([100], dtype=np.float32)  # float32 array
        times = 1.0  # Python float
        rates = np.float64(0.05)  # NumPy scalar
        sigmas = np.array([0.2])  # float64 array

        # Should handle mixed types gracefully
        prices = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)
        prices = to_numpy_array(prices)

        assert len(prices) == 3
        assert prices.dtype == np.float64  # Should upcast to float64


class TestGreeksAdvanced:
    """Advanced Greeks tests beyond the base class coverage."""

    def test_greeks_relationships(self) -> None:
        """Test mathematical relationships between Greeks."""
        spot = 100.0
        strike = 100.0
        time = 1.0
        rate = 0.05
        sigma = 0.2

        # Get Greeks
        greeks = black_scholes.greeks(s=spot, k=strike, t=time, r=rate, sigma=sigma, is_call=True)

        # Basic sanity checks on Greeks
        assert greeks["delta"] > 0 and greeks["delta"] < 1  # Call delta is between 0 and 1
        assert greeks["gamma"] > 0  # Gamma is always positive
        assert greeks["vega"] > 0  # Vega is positive for all options

    def test_greeks_sensitivities(self) -> None:
        """Test that Greeks correctly measure sensitivities."""
        spot = 100.0
        strike = 100.0
        time = 1.0
        rate = 0.05
        sigma = 0.2
        epsilon = 1e-4

        base_price = black_scholes.call_price(s=spot, k=strike, t=time, r=rate, sigma=sigma)
        greeks = black_scholes.greeks(s=spot, k=strike, t=time, r=rate, sigma=sigma, is_call=True)

        # Delta: dPrice/dSpot
        spot_up = black_scholes.call_price(s=spot + epsilon, k=strike, t=time, r=rate, sigma=sigma)
        numerical_delta = (spot_up - base_price) / epsilon
        assert abs(greeks["delta"] - numerical_delta) < 1e-3

        # Vega: dPrice/dSigma (scaled by 1.0 = 100% volatility change)
        sigma_up = black_scholes.call_price(s=spot, k=strike, t=time, r=rate, sigma=sigma + 0.01)
        numerical_vega = (sigma_up - base_price) * 100  # Scale to per 1.0 change
        assert abs(greeks["vega"] - numerical_vega) < 0.1  # Slightly higher tolerance for vega scaling

        # Rho: dPrice/dRate (scaled by 1.0 = 100% rate change)
        rate_up = black_scholes.call_price(s=spot, k=strike, t=time, r=rate + 0.01, sigma=sigma)
        numerical_rho = (rate_up - base_price) * 100  # Scale to per 1.0 change
        assert abs(greeks["rho"] - numerical_rho) < 1.0  # Higher tolerance due to scaling and finite difference

    def test_greeks_batch_consistency(self) -> None:
        """Test that batch Greeks match single calculations."""
        n = 5
        spots = np.linspace(90, 110, n)
        strikes = np.full(n, 100.0)
        times = np.full(n, 1.0)
        rates = np.full(n, 0.05)
        sigmas = np.full(n, 0.2)

        # Batch Greeks
        batch_greeks = black_scholes.greeks_batch(
            spots=spots,
            strikes=strikes,
            times=times,
            rates=rates,
            sigmas=sigmas,
            is_call=True,  # type: ignore[call-arg]
        )

        # Compare with individual calculations
        for i in range(n):
            single_greeks = black_scholes.greeks(
                s=spots[i], k=strikes[i], t=times[i], r=rates[i], sigma=sigmas[i], is_call=True
            )

            for greek_name in ["delta", "gamma", "vega", "theta", "rho"]:
                batch_value = to_numpy_array(batch_greeks[greek_name])[i]
                assert abs(batch_value - single_greeks[greek_name]) < 1e-10, f"Greek {greek_name} mismatch at index {i}"


class TestImpliedVolatilityAdvanced:
    """Advanced implied volatility tests."""

    def test_iv_smile_recovery(self) -> None:
        """Test IV recovery across different strikes (volatility smile)."""
        spot = 100.0
        strikes = np.array([80.0, 90.0, 100.0, 110.0, 120.0])
        time = 1.0
        rate = 0.05

        # Create a simple smile pattern
        sigmas = np.array([0.25, 0.22, 0.20, 0.22, 0.25])

        # Calculate prices
        prices = black_scholes.call_price_batch(spots=spot, strikes=strikes, times=time, rates=rate, sigmas=sigmas)
        prices = to_numpy_array(prices)

        # Recover IVs
        recovered_ivs = black_scholes.implied_volatility_batch(
            prices=prices, spots=spot, strikes=strikes, times=time, rates=rate, is_calls=True
        )
        recovered_ivs = to_numpy_array(recovered_ivs)

        # Should recover the smile
        np.testing.assert_allclose(recovered_ivs, sigmas, rtol=1e-4)

    def test_iv_convergence_difficult_cases(self) -> None:
        """Test IV calculation in difficult cases."""
        spot = 100.0
        strike = 100.0
        time = 0.01  # Very short maturity
        rate = 0.05
        sigma = 0.5  # High volatility

        # Calculate price
        price = black_scholes.call_price(s=spot, k=strike, t=time, r=rate, sigma=sigma)

        # Should still converge
        recovered_iv = black_scholes.implied_volatility(price=price, s=spot, k=strike, t=time, r=rate, is_call=True)

        assert abs(recovered_iv - sigma) < 1e-3

    def test_iv_bounds_checking(self) -> None:
        """Test that IV calculation handles boundary conditions."""
        spot = 100.0
        strike = 100.0
        time = 1.0
        rate = 0.05

        # Price at intrinsic value (should give very low IV)
        intrinsic = max(spot - strike * np.exp(-rate * time), 0)

        with pytest.raises((ValueError, RuntimeError)):
            # This should fail as it's below possible values
            black_scholes.implied_volatility(price=intrinsic * 0.99, s=spot, k=strike, t=time, r=rate, is_call=True)


class TestEdgeCasesAndValidation:
    """Test edge cases and input validation."""

    def test_negative_price_validation(self) -> None:
        """Test that negative prices are rejected."""
        with pytest.raises(ValueError):
            black_scholes.call_price(s=-100, k=100, t=1, r=0.05, sigma=0.2)

    def test_negative_strike_validation(self) -> None:
        """Test that negative strikes are rejected."""
        with pytest.raises(ValueError):
            black_scholes.call_price(s=100, k=-100, t=1, r=0.05, sigma=0.2)

    def test_negative_time_validation(self) -> None:
        """Test that negative time is rejected."""
        with pytest.raises(ValueError):
            black_scholes.call_price(s=100, k=100, t=-1, r=0.05, sigma=0.2)

    def test_negative_volatility_validation(self) -> None:
        """Test that negative volatility is rejected."""
        with pytest.raises(ValueError):
            black_scholes.call_price(s=100, k=100, t=1, r=0.05, sigma=-0.2)

    def test_nan_handling(self) -> None:
        """Test that NaN inputs are handled appropriately."""
        with pytest.raises((ValueError, RuntimeError)):
            black_scholes.call_price(s=np.nan, k=100, t=1, r=0.05, sigma=0.2)

    def test_inf_handling(self) -> None:
        """Test that infinity inputs are handled appropriately."""
        with pytest.raises((ValueError, RuntimeError)):
            black_scholes.call_price(s=np.inf, k=100, t=1, r=0.05, sigma=0.2)

    def test_extreme_values(self) -> None:
        """Test behavior with extreme but valid values."""
        # Very large spot price
        price = black_scholes.call_price(s=1e6, k=100, t=1, r=0.05, sigma=0.2)
        assert price > 0
        assert np.isfinite(price)

        # Very small time (use minimum allowed)
        price = black_scholes.call_price(s=100, k=100, t=0.001, r=0.05, sigma=0.2)
        assert price >= 0
        assert np.isfinite(price)

        # Very high volatility (use maximum allowed)
        price = black_scholes.call_price(s=100, k=100, t=1, r=0.05, sigma=5.0)
        assert price > 0
        assert np.isfinite(price)


# Note: The duplicate test files (test_batch_processing.py, test_batch_refactored.py,
# test_models_api.py, test_models_api_refactored.py) can now be removed as this
# unified test suite provides comprehensive coverage with no duplication.
