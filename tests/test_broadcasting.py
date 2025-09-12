"""Test broadcasting support for batch functions."""

import pyarrow as pa
import pytest
import quantforge.black_scholes as bs  # type: ignore[import-not-found]


class TestBroadcasting:
    """Test suite for broadcasting functionality in batch functions."""

    def test_all_scalars(self):
        """Test that all scalar inputs work (converted to length-1 arrays)."""
        result = bs.call_price_batch(spots=100.0, strikes=105.0, times=1.0, rates=0.05, sigmas=0.2)

        assert result is not None
        assert len(result) == 1

        # Compare with scalar function
        scalar_result = bs.call_price(s=100.0, k=105.0, t=1.0, r=0.05, sigma=0.2)
        assert abs(result.to_pylist()[0] - scalar_result) < 1e-10

    def test_mixed_scalar_array(self):
        """Test mixed scalar and array inputs (broadcasting)."""
        spots_array = pa.array([100.0, 105.0, 110.0])

        result = bs.call_price_batch(
            spots=spots_array,
            strikes=105.0,  # Scalar broadcast to all
            times=1.0,  # Scalar broadcast to all
            rates=0.05,  # Scalar broadcast to all
            sigmas=0.2,  # Scalar broadcast to all
        )

        assert len(result) == 3

        # Each result should match individual scalar calculations
        expected = [
            bs.call_price(s=100.0, k=105.0, t=1.0, r=0.05, sigma=0.2),
            bs.call_price(s=105.0, k=105.0, t=1.0, r=0.05, sigma=0.2),
            bs.call_price(s=110.0, k=105.0, t=1.0, r=0.05, sigma=0.2),
        ]

        results = result.to_pylist()
        for actual, exp in zip(results, expected, strict=False):
            assert abs(actual - exp) < 1e-10

    def test_all_arrays_same_length(self):
        """Test all arrays with same length."""
        spots = pa.array([100.0, 105.0, 110.0])
        strikes = pa.array([95.0, 100.0, 105.0])
        times = pa.array([0.5, 1.0, 1.5])
        rates = pa.array([0.04, 0.05, 0.06])
        sigmas = pa.array([0.18, 0.20, 0.22])

        result = bs.call_price_batch(spots=spots, strikes=strikes, times=times, rates=rates, sigmas=sigmas)

        assert len(result) == 3

        # Verify each element
        expected = [
            bs.call_price(s=100.0, k=95.0, t=0.5, r=0.04, sigma=0.18),
            bs.call_price(s=105.0, k=100.0, t=1.0, r=0.05, sigma=0.20),
            bs.call_price(s=110.0, k=105.0, t=1.5, r=0.06, sigma=0.22),
        ]

        results = result.to_pylist()
        for actual, exp in zip(results, expected, strict=False):
            assert abs(actual - exp) < 1e-10

    def test_put_price_broadcasting(self):
        """Test broadcasting for put prices."""
        spots = pa.array([100.0, 105.0, 110.0])

        result = bs.put_price_batch(
            spots=spots,
            strikes=105.0,  # Scalar
            times=1.0,  # Scalar
            rates=0.05,  # Scalar
            sigmas=0.2,  # Scalar
        )

        assert len(result) == 3

        # Verify results
        expected = [
            bs.put_price(s=100.0, k=105.0, t=1.0, r=0.05, sigma=0.2),
            bs.put_price(s=105.0, k=105.0, t=1.0, r=0.05, sigma=0.2),
            bs.put_price(s=110.0, k=105.0, t=1.0, r=0.05, sigma=0.2),
        ]

        results = result.to_pylist()
        for actual, exp in zip(results, expected, strict=False):
            assert abs(actual - exp) < 1e-10

    def test_greeks_broadcasting(self):
        """Test broadcasting for Greeks calculation."""
        spots = pa.array([100.0, 105.0])

        result = bs.greeks_batch(
            spots=spots,
            strikes=100.0,  # Scalar broadcast
            times=1.0,  # Scalar broadcast
            rates=0.05,  # Scalar broadcast
            sigmas=0.2,  # Scalar broadcast
        )

        assert isinstance(result, dict)
        assert "delta" in result
        assert "gamma" in result
        assert "vega" in result
        assert "theta" in result
        assert "rho" in result

        # Each Greek should have length 2
        for greek_name, greek_values in result.items():
            assert len(greek_values) == 2, f"{greek_name} should have length 2"

    def test_single_element_array_vs_scalar(self):
        """Test that single-element arrays behave like scalars."""
        # Single-element array
        single_array = pa.array([100.0])

        result_array = bs.call_price_batch(spots=single_array, strikes=105.0, times=1.0, rates=0.05, sigmas=0.2)

        # Pure scalar
        result_scalar = bs.call_price_batch(spots=100.0, strikes=105.0, times=1.0, rates=0.05, sigmas=0.2)

        assert len(result_array) == 1
        assert len(result_scalar) == 1
        assert abs(result_array.to_pylist()[0] - result_scalar.to_pylist()[0]) < 1e-15

    def test_invalid_type_error(self):
        """Test that invalid types raise appropriate errors."""
        with pytest.raises(ValueError, match="Expected float, numpy array, or arrow array"):
            bs.call_price_batch(
                spots="invalid",  # String is not valid
                strikes=105.0,
                times=1.0,
                rates=0.05,
                sigmas=0.2,
            )

    def test_no_validation_functions(self):
        """Test that no_validation functions also support broadcasting."""
        spots = pa.array([100.0, 105.0])

        result = bs.call_price_batch_no_validation(
            spots=spots,
            strikes=105.0,  # Scalar
            times=1.0,  # Scalar
            rates=0.05,  # Scalar
            sigmas=0.2,  # Scalar
        )

        assert len(result) == 2

        # Should match regular batch function
        regular_result = bs.call_price_batch(spots=spots, strikes=105.0, times=1.0, rates=0.05, sigmas=0.2)

        results_no_val = result.to_pylist()
        results_regular = regular_result.to_pylist()

        for no_val, regular in zip(results_no_val, results_regular, strict=False):
            assert abs(no_val - regular) < 1e-15
