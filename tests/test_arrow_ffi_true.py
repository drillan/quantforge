"""
Test for TRUE Arrow FFI implementation without NumPy.
"""

import pytest
import pyarrow as pa
import quantforge.arrow_native as arrow_native


class TestArrowFFITrue:
    """Test TRUE Arrow FFI implementation."""

    def test_arrow_call_price_true(self):
        """Test TRUE arrow call price calculation."""
        spots = pa.array([100.0, 105.0, 110.0])
        strikes = pa.array([100.0, 100.0, 100.0])
        times = pa.array([1.0, 1.0, 1.0])
        rates = pa.array([0.05, 0.05, 0.05])
        sigmas = pa.array([0.2, 0.2, 0.2])

        result = arrow_native.arrow_call_price_true(spots, strikes, times, rates, sigmas)

        assert isinstance(result, pa.Array)
        assert len(result) == 3

        # Values should be positive and increasing with spot
        values = result.to_pylist()
        assert all(v > 0 for v in values)
        assert values[1] > values[0]
        assert values[2] > values[1]

    def test_arrow_put_price_true(self):
        """Test TRUE arrow put price calculation."""
        spots = pa.array([90.0, 95.0, 100.0])
        strikes = pa.array([100.0, 100.0, 100.0])
        times = pa.array([1.0, 1.0, 1.0])
        rates = pa.array([0.05, 0.05, 0.05])
        sigmas = pa.array([0.2, 0.2, 0.2])

        result = arrow_native.arrow_put_price_true(spots, strikes, times, rates, sigmas)

        assert isinstance(result, pa.Array)
        assert len(result) == 3

        # Values should be positive and decreasing with spot
        values = result.to_pylist()
        assert all(v > 0 for v in values)
        assert values[0] > values[1]
        assert values[1] > values[2]

    def test_no_numpy_import(self):
        """Verify that NumPy is not imported during Arrow FFI operations."""
        import sys

        # Remove numpy from sys.modules if present
        if "numpy" in sys.modules:
            del sys.modules["numpy"]

        # Run arrow operations
        spots = pa.array([100.0])
        strikes = pa.array([100.0])
        times = pa.array([1.0])
        rates = pa.array([0.05])
        sigmas = pa.array([0.2])

        result = arrow_native.arrow_call_price_true(spots, strikes, times, rates, sigmas)

        # Check that numpy was not imported
        assert "numpy" not in sys.modules, "NumPy should not be imported for TRUE Arrow FFI"
        assert isinstance(result, pa.Array)
