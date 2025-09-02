"""
Tests for Apache Arrow Native API.
"""

import pytest
import numpy as np
import pyarrow as pa
import quantforge.arrow_api as qf_arrow
import quantforge.numpy_compat as qf_numpy
from quantforge import black_scholes


class TestArrowAPI:
    """Test Arrow API functionality."""

    def test_call_price_arrow(self):
        """Test call price calculation with Arrow arrays."""
        spots = pa.array([100.0, 105.0, 110.0])
        strikes = pa.array([100.0, 100.0, 100.0])
        times = pa.array([1.0, 1.0, 1.0])
        rates = pa.array([0.05, 0.05, 0.05])
        sigmas = pa.array([0.2, 0.2, 0.2])

        result = qf_arrow.call_price(spots, strikes, times, rates, sigmas)

        assert isinstance(result, pa.Array)
        assert len(result) == 3
        assert result[0].as_py() > 0
        # Prices should increase with spot price
        assert result[1].as_py() > result[0].as_py()
        assert result[2].as_py() > result[1].as_py()

    def test_put_price_arrow(self):
        """Test put price calculation with Arrow arrays."""
        spots = pa.array([100.0, 95.0, 90.0])
        strikes = pa.array([100.0, 100.0, 100.0])
        times = pa.array([1.0, 1.0, 1.0])
        rates = pa.array([0.05, 0.05, 0.05])
        sigmas = pa.array([0.2, 0.2, 0.2])

        result = qf_arrow.put_price(spots, strikes, times, rates, sigmas)

        assert isinstance(result, pa.Array)
        assert len(result) == 3
        assert result[0].as_py() > 0
        # Put prices should increase as spot price decreases
        assert result[1].as_py() > result[0].as_py()
        assert result[2].as_py() > result[1].as_py()

    def test_greeks_arrow(self):
        """Test Greeks calculation with Arrow arrays."""
        spots = pa.array([100.0])
        strikes = pa.array([100.0])
        times = pa.array([1.0])
        rates = pa.array([0.05])
        sigmas = pa.array([0.2])

        greeks = qf_arrow.greeks(spots, strikes, times, rates, sigmas, is_call=True)

        assert isinstance(greeks, dict)
        assert "delta" in greeks
        assert "gamma" in greeks
        assert "vega" in greeks
        assert "theta" in greeks
        assert "rho" in greeks

        # Check all are Arrow arrays
        for key, value in greeks.items():
            assert isinstance(value, pa.Array)
            assert len(value) == 1

        # Call delta should be between 0 and 1
        delta = greeks["delta"][0].as_py()
        assert 0 < delta < 1

        # Gamma should be positive
        gamma = greeks["gamma"][0].as_py()
        assert gamma > 0

    @pytest.mark.skip(reason="implied_volatility_batch not yet implemented in Arrow-native version")
    def test_implied_volatility_arrow(self):
        """Test implied volatility calculation with Arrow arrays."""
        # First calculate a price with known volatility
        spots = pa.array([100.0])
        strikes = pa.array([100.0])
        times = pa.array([1.0])
        rates = pa.array([0.05])
        true_sigma = 0.2
        sigmas = pa.array([true_sigma])

        price = qf_arrow.call_price(spots, strikes, times, rates, sigmas)

        # Now calculate implied volatility
        iv = qf_arrow.implied_volatility(price, spots, strikes, times, rates, is_call=True)

        assert isinstance(iv, pa.Array)
        assert len(iv) == 1
        # Should recover the original volatility
        assert abs(iv[0].as_py() - true_sigma) < 1e-6

    def test_broadcast_arrays(self):
        """Test array broadcasting functionality."""
        # Scalar and vector
        scalar = pa.array([100.0])
        vector = pa.array([95.0, 100.0, 105.0])

        broadcasted = qf_arrow.broadcast_arrays(scalar, vector)

        assert len(broadcasted) == 2
        assert len(broadcasted[0]) == 3  # Scalar expanded
        assert len(broadcasted[1]) == 3  # Vector unchanged

        # All values in expanded scalar should be the same
        assert broadcasted[0][0].as_py() == 100.0
        assert broadcasted[0][1].as_py() == 100.0
        assert broadcasted[0][2].as_py() == 100.0

    def test_conversion_utilities(self):
        """Test NumPy <-> Arrow conversion utilities."""
        np_array = np.array([1.0, 2.0, 3.0])

        # NumPy to Arrow
        arrow_array = qf_arrow.from_numpy(np_array)
        assert isinstance(arrow_array, pa.Array)
        assert len(arrow_array) == 3

        # Arrow to NumPy
        np_array_back = qf_arrow.to_numpy(arrow_array)
        assert isinstance(np_array_back, np.ndarray)
        np.testing.assert_array_equal(np_array, np_array_back)

    def test_array_length_validation(self):
        """Test that arrays of different lengths raise errors."""
        spots = pa.array([100.0, 105.0])
        strikes = pa.array([100.0])  # Wrong length
        times = pa.array([1.0, 1.0])
        rates = pa.array([0.05, 0.05])
        sigmas = pa.array([0.2, 0.2])

        with pytest.raises(ValueError, match="Array length mismatch"):
            qf_arrow.call_price(spots, strikes, times, rates, sigmas)


class TestNumPyCompat:
    """Test NumPy compatibility layer."""

    def test_call_price_numpy(self):
        """Test call price with NumPy arrays."""
        spots = np.array([100.0, 105.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        sigmas = np.array([0.2, 0.2, 0.2])

        result = qf_numpy.call_price_numpy(spots, strikes, times, rates, sigmas)

        assert isinstance(result, np.ndarray)
        assert len(result) == 3
        assert result[0] > 0
        # Prices should increase with spot price
        assert result[1] > result[0]
        assert result[2] > result[1]

    def test_numpy_arrow_consistency(self):
        """Test that NumPy compat gives same results as direct Arrow API."""
        spots = np.array([100.0, 105.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        sigmas = np.array([0.2, 0.2, 0.2])

        # NumPy compat
        numpy_result = qf_numpy.call_price_numpy(spots, strikes, times, rates, sigmas)

        # Direct Arrow
        arrow_result = qf_arrow.call_price(
            pa.array(spots), pa.array(strikes), pa.array(times), pa.array(rates), pa.array(sigmas)
        )

        # Should be identical
        np.testing.assert_array_almost_equal(numpy_result, arrow_result.to_numpy(), decimal=10)

    def test_greeks_numpy(self):
        """Test Greeks calculation with NumPy arrays."""
        spots = np.array([100.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        sigmas = np.array([0.2])

        greeks = qf_numpy.greeks_numpy(spots, strikes, times, rates, sigmas, is_call=True)

        assert isinstance(greeks, dict)
        assert "delta" in greeks
        assert "gamma" in greeks
        assert "vega" in greeks
        assert "theta" in greeks
        assert "rho" in greeks

        # Check all are NumPy arrays
        for key, value in greeks.items():
            assert isinstance(value, np.ndarray)
            assert len(value) == 1

    def test_legacy_aliases(self):
        """Test that legacy function aliases work with deprecation warnings."""
        spots = np.array([100.0])
        strikes = np.array([100.0])
        times = np.array([1.0])
        rates = np.array([0.05])
        sigmas = np.array([0.2])

        with pytest.warns(DeprecationWarning):
            result = qf_numpy.black_scholes_call(spots, strikes, times, rates, sigmas)
            assert result.shape == (1,)

        with pytest.warns(DeprecationWarning):
            result = qf_numpy.black_scholes_put(spots, strikes, times, rates, sigmas)
            assert result.shape == (1,)


class TestPerformanceComparison:
    """Test performance comparisons between APIs."""

    def test_arrow_vs_numpy_consistency(self):
        """Ensure Arrow and NumPy APIs give identical results."""
        np.random.seed(42)
        size = 100

        spots = np.random.uniform(80, 120, size)
        strikes = np.random.uniform(80, 120, size)
        times = np.random.uniform(0.1, 2.0, size)
        rates = np.random.uniform(0.01, 0.1, size)
        sigmas = np.random.uniform(0.1, 0.5, size)

        # Direct NumPy (existing API)
        numpy_direct = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)

        # Arrow API
        arrow_result = qf_arrow.call_price(
            pa.array(spots), pa.array(strikes), pa.array(times), pa.array(rates), pa.array(sigmas)
        )

        # NumPy compat
        numpy_compat = qf_numpy.call_price_numpy(spots, strikes, times, rates, sigmas)

        # All should be identical
        np.testing.assert_array_almost_equal(numpy_direct, arrow_result.to_numpy(), decimal=10)
        np.testing.assert_array_almost_equal(numpy_direct, numpy_compat, decimal=10)
