"""Tests for batch processing functions across all models."""

import numpy as np
import pytest
from quantforge import models

# NOTE: Batch functions now support full array parameters with
# NumPy-style broadcasting. All parameters can be arrays or scalars.


class TestBlackScholesBatch:
    """Test batch processing for Black-Scholes model."""

    def test_call_price_batch(self) -> None:
        """Test batch call price calculation with broadcasting."""
        # Test with all arrays
        spots = np.array([95.0, 100.0, 105.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        sigmas = np.array([0.2, 0.2, 0.2])

        prices = models.call_price_batch(spots, strikes, times, rates, sigmas)

        # Verify results
        assert len(prices) == 3
        assert all(p > 0 for p in prices)

        # Test broadcasting with single element arrays
        spots = np.array([95.0, 100.0, 105.0])
        strikes = np.array([100.0])  # Will broadcast
        times = np.array([1.0])
        rates = np.array([0.05])
        sigmas = np.array([0.2])

        prices_broadcast = models.call_price_batch(spots, strikes, times, rates, sigmas)
        np.testing.assert_array_almost_equal(prices, prices_broadcast)

    def test_put_price_batch(self) -> None:
        """Test batch put price calculation with broadcasting."""
        spots = np.array([95.0, 100.0, 105.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        sigmas = np.array([0.2])

        prices = models.put_price_batch(spots, strikes, times, rates, sigmas)

        # Verify results
        assert len(prices) == 3
        assert all(p > 0 for p in prices)

        # Verify put-call parity
        call_prices = models.call_price_batch(spots, strikes, times, rates, sigmas)
        for _i, (c, p, s) in enumerate(zip(call_prices, prices, spots, strict=False)):
            parity_lhs = c - p
            parity_rhs = s - 100.0 * np.exp(-0.05 * 1.0)
            assert abs(parity_lhs - parity_rhs) < 1e-10

    def test_implied_volatility_batch(self) -> None:
        """Test batch IV calculation for Black-Scholes."""
        # Setup
        prices = np.array([10.45, 11.0, 9.5, 12.0, 8.0])
        spots = np.array([100.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        is_calls = np.array([1.0])  # True for all

        # Calculate IV for each price
        ivs = models.implied_volatility_batch(prices, spots, strikes, times, rates, is_calls)

        # Verify results
        assert len(ivs) == len(prices)
        assert all(0.01 < iv < 2.0 or np.isnan(iv) for iv in ivs)

        # Verify consistency with single calculation
        single_iv = models.implied_volatility(prices[0], 100.0, 100.0, 1.0, 0.05, is_call=True)
        assert abs(ivs[0] - single_iv) < 1e-10

    def test_greeks_batch(self) -> None:
        """Test batch Greeks calculation for Black-Scholes."""
        # Setup
        spots = np.array([95.0, 100.0, 105.0, 110.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        sigmas = np.array([0.2])
        is_calls = np.array([1.0])  # True

        # Calculate Greeks for each spot
        greeks = models.greeks_batch(spots, strikes, times, rates, sigmas, is_calls)

        # Verify results (now returns dict of arrays)
        assert isinstance(greeks, dict)
        assert len(greeks["delta"]) == len(spots)
        assert len(greeks["gamma"]) == len(spots)
        assert len(greeks["vega"]) == len(spots)
        assert len(greeks["theta"]) == len(spots)
        assert len(greeks["rho"]) == len(spots)

        # Verify consistency with single calculation
        single_greeks = models.greeks(spots[0], 100.0, 1.0, 0.05, 0.2, is_call=True)
        assert abs(greeks["delta"][0] - single_greeks.delta) < 1e-10
        assert abs(greeks["gamma"][0] - single_greeks.gamma) < 1e-10
        assert abs(greeks["vega"][0] - single_greeks.vega) < 1e-10
        assert abs(greeks["theta"][0] - single_greeks.theta) < 1e-10
        assert abs(greeks["rho"][0] - single_greeks.rho) < 1e-10


class TestBlack76Batch:
    """Test batch processing for Black76 model."""

    def test_call_price_batch(self) -> None:
        """Test batch call price calculation with broadcasting."""
        # Test with all arrays
        forwards = np.array([95.0, 100.0, 105.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        sigmas = np.array([0.2, 0.2, 0.2])

        prices = models.black76.call_price_batch(forwards, strikes, times, rates, sigmas)

        # Verify results
        assert len(prices) == 3
        assert all(p > 0 for p in prices)

        # Test broadcasting with single element arrays
        forwards = np.array([95.0, 100.0, 105.0])
        strikes = np.array([100.0])  # Will broadcast
        times = np.array([1.0])
        rates = np.array([0.05])
        sigmas = np.array([0.2])

        prices_broadcast = models.black76.call_price_batch(forwards, strikes, times, rates, sigmas)
        np.testing.assert_array_almost_equal(prices, prices_broadcast)

    def test_put_price_batch(self) -> None:
        """Test batch put price calculation with broadcasting."""
        forwards = np.array([95.0, 100.0, 105.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        sigmas = np.array([0.2])

        prices = models.black76.put_price_batch(forwards, strikes, times, rates, sigmas)

        # Verify results
        assert len(prices) == 3
        assert all(p > 0 for p in prices)

        # Verify put-call parity
        call_prices = models.black76.call_price_batch(forwards, strikes, times, rates, sigmas)
        discount = np.exp(-rates[0] * times[0])
        for _i, (c, p, f) in enumerate(zip(call_prices, prices, forwards, strict=False)):
            parity_lhs = c - p
            parity_rhs = discount * (f - 100.0)
            assert abs(parity_lhs - parity_rhs) < 1e-10

    def test_implied_volatility_batch(self) -> None:
        """Test batch IV calculation for Black76."""
        # Setup
        prices = np.array([5.5, 6.0, 5.0, 6.5, 4.5])
        forwards = np.array([75.0])
        strikes = np.array([75.0])
        times = np.array([0.5])
        rates = np.array([0.05])
        is_calls = np.array([1.0])  # True for all

        # Calculate IV for each price
        ivs = models.black76.implied_volatility_batch(prices, forwards, strikes, times, rates, is_calls)

        # Verify results
        assert len(ivs) == len(prices)
        assert all(0.01 < iv < 2.0 or np.isnan(iv) for iv in ivs)

        # Verify consistency with single calculation
        single_iv = models.black76.implied_volatility(prices[0], 75.0, 75.0, 0.5, 0.05, is_call=True)
        assert abs(ivs[0] - single_iv) < 1e-10

    def test_greeks_batch(self) -> None:
        """Test batch Greeks calculation for Black76."""
        # Setup
        forwards = np.array([70.0, 75.0, 80.0, 85.0])
        strikes = np.array([75.0])
        times = np.array([0.5])
        rates = np.array([0.05])
        sigmas = np.array([0.25])
        is_calls = np.array([1.0])  # True

        # Calculate Greeks for each forward
        greeks = models.black76.greeks_batch(forwards, strikes, times, rates, sigmas, is_calls)

        # Verify results (now returns dict of arrays)
        assert isinstance(greeks, dict)
        assert len(greeks["delta"]) == len(forwards)
        assert len(greeks["gamma"]) == len(forwards)
        assert len(greeks["vega"]) == len(forwards)
        assert len(greeks["theta"]) == len(forwards)
        assert len(greeks["rho"]) == len(forwards)

        # Verify consistency with single calculation
        single_greeks = models.black76.greeks(forwards[0], 75.0, 0.5, 0.05, 0.25, is_call=True)
        assert abs(greeks["delta"][0] - single_greeks.delta) < 1e-10
        assert abs(greeks["gamma"][0] - single_greeks.gamma) < 1e-10
        assert abs(greeks["vega"][0] - single_greeks.vega) < 1e-10
        assert abs(greeks["theta"][0] - single_greeks.theta) < 1e-10
        assert abs(greeks["rho"][0] - single_greeks.rho) < 1e-10


class TestMertonBatch:
    """Test batch processing for Merton model."""

    def test_call_price_batch(self) -> None:
        """Test batch call price calculation with broadcasting."""
        # Test with all arrays
        spots = np.array([95.0, 100.0, 105.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        qs = np.array([0.02, 0.02, 0.02])
        sigmas = np.array([0.2, 0.2, 0.2])

        prices = models.merton.call_price_batch(spots, strikes, times, rates, qs, sigmas)

        # Verify results
        assert len(prices) == 3
        assert all(p > 0 for p in prices)

        # Test broadcasting with single element arrays
        spots = np.array([95.0, 100.0, 105.0])
        strikes = np.array([100.0])  # Will broadcast
        times = np.array([1.0])
        rates = np.array([0.05])
        qs = np.array([0.02])
        sigmas = np.array([0.2])

        prices_broadcast = models.merton.call_price_batch(spots, strikes, times, rates, qs, sigmas)
        np.testing.assert_array_almost_equal(prices, prices_broadcast)

    def test_put_price_batch(self) -> None:
        """Test batch put price calculation with broadcasting."""
        spots = np.array([95.0, 100.0, 105.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        qs = np.array([0.02])
        sigmas = np.array([0.2])

        prices = models.merton.put_price_batch(spots, strikes, times, rates, qs, sigmas)

        # Verify results
        assert len(prices) == 3
        assert all(p > 0 for p in prices)

        # Verify put-call parity with dividends
        call_prices = models.merton.call_price_batch(spots, strikes, times, rates, qs, sigmas)
        for _i, (c, p, s) in enumerate(zip(call_prices, prices, spots, strict=False)):
            parity_lhs = c - p
            parity_rhs = s * np.exp(-qs[0] * times[0]) - strikes[0] * np.exp(-rates[0] * times[0])
            assert abs(parity_lhs - parity_rhs) < 1e-10

    def test_implied_volatility_batch(self) -> None:
        """Test batch IV calculation for Merton."""
        # Setup
        prices = np.array([10.0, 10.5, 9.5, 11.0, 9.0])
        spots = np.array([100.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        qs = np.array([0.03])
        is_calls = np.array([1.0])  # True for all

        # Calculate IV for each price
        ivs = models.merton.implied_volatility_batch(prices, spots, strikes, times, rates, qs, is_calls)

        # Verify results
        assert len(ivs) == len(prices)
        assert all(0.01 < iv < 2.0 or np.isnan(iv) for iv in ivs)

        # Verify consistency with single calculation
        single_iv = models.merton.implied_volatility(prices[0], 100.0, 100.0, 1.0, 0.05, 0.03, is_call=True)
        assert abs(ivs[0] - single_iv) < 1e-10

    def test_greeks_batch(self) -> None:
        """Test batch Greeks calculation for Merton."""
        # Setup
        spots = np.array([95.0, 100.0, 105.0, 110.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        qs = np.array([0.03])
        sigmas = np.array([0.2])
        is_calls = np.array([1.0])  # True

        # Calculate Greeks for each spot
        greeks = models.merton.greeks_batch(spots, strikes, times, rates, qs, sigmas, is_calls)

        # Verify results (now returns dict of arrays)
        assert isinstance(greeks, dict)
        assert len(greeks["delta"]) == len(spots)
        assert len(greeks["gamma"]) == len(spots)
        assert len(greeks["vega"]) == len(spots)
        assert len(greeks["theta"]) == len(spots)
        assert len(greeks["rho"]) == len(spots)
        assert len(greeks["dividend_rho"]) == len(spots)

        # Verify consistency with single calculation
        single_greeks = models.merton.greeks(spots[0], 100.0, 1.0, 0.05, 0.03, 0.2, is_call=True)
        assert abs(greeks["delta"][0] - single_greeks.delta) < 1e-10
        assert abs(greeks["gamma"][0] - single_greeks.gamma) < 1e-10
        assert abs(greeks["vega"][0] - single_greeks.vega) < 1e-10
        assert abs(greeks["theta"][0] - single_greeks.theta) < 1e-10
        assert abs(greeks["rho"][0] - single_greeks.rho) < 1e-10
        assert abs(greeks["dividend_rho"][0] - single_greeks.dividend_rho) < 1e-10


class TestAmericanBatch:
    """Test batch processing for American model."""

    def test_call_price_batch(self) -> None:
        """Test batch call price calculation with broadcasting."""
        # Test with all arrays
        spots = np.array([95.0, 100.0, 105.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        qs = np.array([0.02, 0.02, 0.02])
        sigmas = np.array([0.2, 0.2, 0.2])

        prices = models.american.call_price_batch(spots, strikes, times, rates, qs, sigmas)

        # Verify results
        assert len(prices) == 3
        assert all(p > 0 for p in prices)

        # Test broadcasting with single element arrays
        spots = np.array([95.0, 100.0, 105.0])
        strikes = np.array([100.0])  # Will broadcast
        times = np.array([1.0])
        rates = np.array([0.05])
        qs = np.array([0.02])
        sigmas = np.array([0.2])

        prices_broadcast = models.american.call_price_batch(spots, strikes, times, rates, qs, sigmas)
        np.testing.assert_array_almost_equal(prices, prices_broadcast)

    def test_put_price_batch(self) -> None:
        """Test batch put price calculation with broadcasting."""
        spots = np.array([95.0, 100.0, 105.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        qs = np.array([0.02])
        sigmas = np.array([0.2])

        prices = models.american.put_price_batch(spots, strikes, times, rates, qs, sigmas)

        # Verify results
        assert len(prices) == 3
        assert all(p > 0 for p in prices)

    def test_implied_volatility_batch(self) -> None:
        """Test batch IV calculation for American."""
        # Setup
        prices = np.array([15.0, 15.5, 14.5, 16.0, 14.0])
        spots = np.array([100.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        qs = np.array([0.03])
        is_calls = np.array([0.0])  # False for puts

        # Calculate IV for each price
        ivs = models.american.implied_volatility_batch(prices, spots, strikes, times, rates, qs, is_calls)

        # Verify results
        assert len(ivs) == len(prices)
        # American options may have wider IV ranges
        assert all(0.01 < iv < 3.0 or np.isnan(iv) for iv in ivs)

        # Verify consistency with single calculation
        single_iv = models.american.implied_volatility(prices[0], 100.0, 100.0, 1.0, 0.05, 0.03, is_call=False)
        assert abs(ivs[0] - single_iv) < 1e-10

    def test_greeks_batch(self) -> None:
        """Test batch Greeks calculation for American."""
        # Setup
        spots = np.array([95.0, 100.0, 105.0, 110.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        qs = np.array([0.03])
        sigmas = np.array([0.2])
        is_calls = np.array([0.0])  # False for puts

        # Calculate Greeks for each spot
        greeks = models.american.greeks_batch(spots, strikes, times, rates, qs, sigmas, is_calls)

        # Verify results (now returns dict of arrays)
        assert isinstance(greeks, dict)
        assert len(greeks["delta"]) == len(spots)
        assert len(greeks["gamma"]) == len(spots)
        assert len(greeks["vega"]) == len(spots)
        assert len(greeks["theta"]) == len(spots)
        assert len(greeks["rho"]) == len(spots)
        assert len(greeks["dividend_rho"]) == len(spots)

        # Verify consistency with single calculation
        single_greeks = models.american.greeks(spots[0], 100.0, 1.0, 0.05, 0.03, 0.2, is_call=False)
        assert abs(greeks["delta"][0] - single_greeks.delta) < 1e-10
        assert abs(greeks["gamma"][0] - single_greeks.gamma) < 1e-10
        assert abs(greeks["vega"][0] - single_greeks.vega) < 1e-10
        assert abs(greeks["theta"][0] - single_greeks.theta) < 1e-10
        assert abs(greeks["rho"][0] - single_greeks.rho) < 1e-10

    def test_exercise_boundary_batch(self) -> None:
        """Test batch exercise boundary calculation for American."""
        # Setup - now all parameters can be arrays
        spots = np.array([90.0, 95.0, 100.0, 105.0, 110.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        qs = np.array([0.03])
        sigmas = np.array([0.2])
        is_calls = np.array([0.0])  # False for puts

        # Calculate exercise boundaries
        boundaries = models.american.exercise_boundary_batch(spots, strikes, times, rates, qs, sigmas, is_calls)

        # Verify results
        assert len(boundaries) == len(spots)
        assert all(b > 0 for b in boundaries)

        # Verify consistency with single calculation
        single_boundary = models.american.exercise_boundary(spots[0], 100.0, 1.0, 0.05, 0.03, 0.2, is_call=False)
        assert abs(boundaries[0] - single_boundary) < 1e-10


class TestBatchPerformance:
    """Test performance characteristics of batch processing."""

    @pytest.mark.skip(reason="Batch functions not yet reimplemented with new API")
    def test_large_batch_processing(self) -> None:
        """Test processing large batches efficiently."""
        # Create large batch
        n = 10000
        spots = np.linspace(80, 120, n)
        k, t, r, sigma = 100.0, 1.0, 0.05, 0.2

        # Test Black-Scholes batch
        greeks = models.greeks_batch(spots, k, t, r, sigma, is_calls=1.0)
        assert len(greeks) == n

        # Test that all results are valid
        for i in range(n):
            assert -1.0 <= greeks["delta"][i] <= 1.0
            assert greeks["gamma"][i] >= 0
            assert not np.isnan(greeks["vega"][i])

    @pytest.mark.skip(reason="Batch functions not yet reimplemented with new API")
    def test_edge_cases(self) -> None:
        """Test batch processing with edge cases."""
        # Test with single element
        spots = np.array([100.0])
        k, t, r, sigma = 100.0, 1.0, 0.05, 0.2
        greeks = models.greeks_batch(spots, k, t, r, sigma, is_calls=1.0)
        assert len(greeks) == 1

        # Test with empty array (should handle gracefully)
        spots = np.array([])
        greeks = models.greeks_batch(spots, k, t, r, sigma, is_calls=1.0)
        assert len(greeks) == 0


class TestScalarInputs:
    """Test scalar input support for batch functions."""

    def test_black_scholes_scalar_inputs(self) -> None:
        """Test Black-Scholes batch functions with scalar inputs."""
        # Test all scalars
        result = models.call_price_batch(100.0, 100.0, 1.0, 0.05, 0.2)
        assert isinstance(result, np.ndarray)
        assert len(result) == 1
        assert abs(result[0] - 10.450583571) < 1e-6

        # Test mixed scalars and arrays
        spots = np.array([95.0, 100.0, 105.0])
        result = models.call_price_batch(spots, 100.0, 1.0, 0.05, 0.2)
        assert len(result) == 3
        assert all(r > 0 for r in result)

        # Test Python list input
        result = models.call_price_batch([95, 100, 105], 100.0, 1.0, 0.05, 0.2)
        assert len(result) == 3
        assert all(r > 0 for r in result)

    def test_black76_scalar_inputs(self) -> None:
        """Test Black76 batch functions with scalar inputs."""
        result = models.black76.call_price_batch(100.0, 100.0, 1.0, 0.05, 0.2)
        assert isinstance(result, np.ndarray)
        assert len(result) == 1
        assert result[0] > 0

        # Test Greeks with mixed inputs
        forwards = [95, 100, 105]
        greeks = models.black76.greeks_batch(forwards, 100.0, 1.0, 0.05, 0.2, 1.0)
        assert isinstance(greeks, dict)
        assert len(greeks["delta"]) == 3

    def test_merton_scalar_inputs(self) -> None:
        """Test Merton batch functions with scalar inputs."""
        result = models.merton.call_price_batch(100.0, 100.0, 1.0, 0.05, 0.02, 0.2)
        assert isinstance(result, np.ndarray)
        assert len(result) == 1
        assert result[0] > 0

        # Test Greeks with Python lists
        spots = [95, 100, 105]
        greeks = models.merton.greeks_batch(spots, 100.0, 1.0, 0.05, 0.02, 0.2, 1.0)
        assert isinstance(greeks, dict)
        assert "dividend_rho" in greeks
        assert len(greeks["dividend_rho"]) == 3

    def test_american_scalar_inputs(self) -> None:
        """Test American batch functions with scalar inputs."""
        result = models.american.call_price_batch(100.0, 100.0, 1.0, 0.05, 0.02, 0.2)
        assert isinstance(result, np.ndarray)
        assert len(result) == 1
        assert result[0] > 0

        # Test Greeks with Python lists
        spots = [95, 100, 105]
        greeks = models.american.greeks_batch(spots, 100.0, 1.0, 0.05, 0.02, 0.2, 1.0)
        assert isinstance(greeks, dict)
        assert "dividend_rho" in greeks
        assert len(greeks["dividend_rho"]) == 3

    def test_implied_volatility_scalar_inputs(self) -> None:
        """Test implied volatility with scalar inputs."""
        # Black-Scholes
        iv = models.implied_volatility_batch(10.0, 100.0, 100.0, 1.0, 0.05, 1.0)
        assert isinstance(iv, np.ndarray)
        assert len(iv) == 1
        assert 0.1 < iv[0] < 0.5

        # Test with mixed inputs
        prices = [8.0, 10.0, 12.0]
        ivs = models.implied_volatility_batch(prices, 100.0, 100.0, 1.0, 0.05, 1.0)
        assert len(ivs) == 3
        assert all(0.1 < v < 0.5 for v in ivs if not np.isnan(v))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
