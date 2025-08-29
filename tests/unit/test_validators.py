"""Unit tests for the validators module."""

from typing import TYPE_CHECKING

import numpy as np
import pytest
from quantforge.errors import DimensionError, ValidationError
from quantforge.validators import VectorizedValidator, validate_batch_inputs

if TYPE_CHECKING:
    from numpy.typing import ArrayLike


class TestVectorizedValidator:
    """Test VectorizedValidator class."""

    def test_ensure_array_scalar(self) -> None:
        """Test ensure_array with scalar input."""
        result = VectorizedValidator.ensure_array(42.0)
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float64
        assert result.shape == ()
        assert result == 42.0

    def test_ensure_array_list(self) -> None:
        """Test ensure_array with list input."""
        result = VectorizedValidator.ensure_array([1, 2, 3])
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float64
        assert result.shape == (3,)
        assert np.array_equal(result, [1.0, 2.0, 3.0])

    def test_ensure_array_nested_list(self) -> None:
        """Test ensure_array with nested list."""
        result = VectorizedValidator.ensure_array([[1, 2], [3, 4]])
        assert result.shape == (2, 2)
        assert np.array_equal(result, [[1.0, 2.0], [3.0, 4.0]])

    def test_ensure_array_numpy_array(self) -> None:
        """Test ensure_array with NumPy array input."""
        arr = np.array([1, 2, 3], dtype=np.int32)
        result = VectorizedValidator.ensure_array(arr)
        assert result.dtype == np.float64
        assert np.array_equal(result, [1.0, 2.0, 3.0])

    def test_ensure_array_custom_dtype(self) -> None:
        """Test ensure_array with custom dtype."""
        result = VectorizedValidator.ensure_array([1, 2, 3], dtype=np.int32)
        assert result.dtype == np.int32
        assert np.array_equal(result, [1, 2, 3])

    def test_ensure_array_invalid_data(self) -> None:
        """Test ensure_array with invalid data."""
        with pytest.raises(ValidationError) as exc_info:
            VectorizedValidator.ensure_array("not_numeric", name="test_param")
        assert "cannot convert" in str(exc_info.value)
        assert "test_param" in str(exc_info.value)

    def test_validate_positive_array_scalar(self) -> None:
        """Test validate_positive_array with scalar."""
        result = VectorizedValidator.validate_positive_array(10.0)
        assert result == 10.0

    def test_validate_positive_array_list(self) -> None:
        """Test validate_positive_array with list."""
        result = VectorizedValidator.validate_positive_array([1, 2, 3])
        assert np.array_equal(result, [1.0, 2.0, 3.0])

    def test_validate_positive_array_numpy(self) -> None:
        """Test validate_positive_array with NumPy array."""
        arr = np.array([0.1, 0.2, 0.3])
        result = VectorizedValidator.validate_positive_array(arr)
        assert np.array_equal(result, arr)

    def test_validate_positive_array_strict_mode(self) -> None:
        """Test validate_positive_array in strict mode (> 0)."""
        # Valid positive values
        result = VectorizedValidator.validate_positive_array([1, 2, 3], strict=True)
        assert np.array_equal(result, [1.0, 2.0, 3.0])

        # Zero should fail in strict mode
        with pytest.raises(ValidationError) as exc_info:
            VectorizedValidator.validate_positive_array([1, 0, 3], strict=True)
        assert "all elements must be positive" in str(exc_info.value)
        assert "index 1" in str(exc_info.value)

    def test_validate_positive_array_non_strict_mode(self) -> None:
        """Test validate_positive_array in non-strict mode (>= 0)."""
        # Zero is allowed in non-strict mode
        result = VectorizedValidator.validate_positive_array([1, 0, 3], strict=False)
        assert np.array_equal(result, [1.0, 0.0, 3.0])

        # Negative should still fail
        with pytest.raises(ValidationError) as exc_info:
            VectorizedValidator.validate_positive_array([1, -1, 3], strict=False)
        assert "all elements must be non-negative" in str(exc_info.value)

    def test_validate_positive_array_negative(self) -> None:
        """Test validate_positive_array with negative values."""
        with pytest.raises(ValidationError) as exc_info:
            VectorizedValidator.validate_positive_array([1, -2, 3], name="test_array")
        assert "test_array" in str(exc_info.value)
        assert "index 1" in str(exc_info.value)
        assert "-2" in str(exc_info.value)

    def test_validate_positive_array_nan(self) -> None:
        """Test validate_positive_array with NaN."""
        with pytest.raises(ValidationError) as exc_info:
            VectorizedValidator.validate_positive_array([1, float("nan"), 3])
        assert "all elements must be finite" in str(exc_info.value)
        assert "index 1" in str(exc_info.value)

    def test_validate_positive_array_inf(self) -> None:
        """Test validate_positive_array with infinity."""
        with pytest.raises(ValidationError) as exc_info:
            VectorizedValidator.validate_positive_array([1, float("inf"), 3])
        assert "all elements must be finite" in str(exc_info.value)

    def test_validate_positive_array_empty(self) -> None:
        """Test validate_positive_array with empty array."""
        result = VectorizedValidator.validate_positive_array([])
        assert result.shape == (0,)

    def test_validate_shape_compatibility_identical(self) -> None:
        """Test validate_shape_compatibility with identical shapes."""
        arrays: dict[str, ArrayLike] = {
            "a": [1, 2, 3],
            "b": [4, 5, 6],
            "c": [7, 8, 9],
        }
        result = VectorizedValidator.validate_shape_compatibility(arrays, broadcast=False)
        assert all(arr.shape == (3,) for arr in result.values())

    def test_validate_shape_compatibility_mismatch_no_broadcast(self) -> None:
        """Test validate_shape_compatibility with mismatched shapes, no broadcasting."""
        arrays: dict[str, ArrayLike] = {
            "a": [1, 2, 3],
            "b": [4, 5],
        }
        with pytest.raises(DimensionError) as exc_info:
            VectorizedValidator.validate_shape_compatibility(arrays, broadcast=False)
        assert exc_info.value.expected == (3,)
        assert exc_info.value.actual == (2,)

    def test_validate_shape_compatibility_broadcast_scalar(self) -> None:
        """Test validate_shape_compatibility with broadcasting scalar."""
        arrays: dict[str, ArrayLike] = {
            "a": [1, 2, 3],
            "b": 5,  # Scalar broadcasts to any shape
        }
        result = VectorizedValidator.validate_shape_compatibility(arrays, broadcast=True)
        assert result["a"].shape == (3,)
        assert result["b"].shape == ()

    def test_validate_shape_compatibility_broadcast_compatible(self) -> None:
        """Test validate_shape_compatibility with compatible broadcast shapes."""
        arrays: dict[str, ArrayLike] = {
            "a": [[1, 2], [3, 4]],  # (2, 2)
            "b": [5, 6],  # (2,) broadcasts to (2, 2)
            "c": [[7], [8]],  # (2, 1) broadcasts to (2, 2)
        }
        result = VectorizedValidator.validate_shape_compatibility(arrays, broadcast=True)
        assert result["a"].shape == (2, 2)
        assert result["b"].shape == (2,)
        assert result["c"].shape == (2, 1)

    def test_validate_shape_compatibility_broadcast_incompatible(self) -> None:
        """Test validate_shape_compatibility with incompatible broadcast shapes."""
        arrays: dict[str, ArrayLike] = {
            "a": [[1, 2], [3, 4]],  # (2, 2)
            "b": [5, 6, 7],  # (3,) cannot broadcast with (2, 2)
        }
        with pytest.raises(DimensionError):
            VectorizedValidator.validate_shape_compatibility(arrays, broadcast=True)

    def test_validate_option_arrays_basic(self) -> None:
        """Test validate_option_arrays with valid inputs."""
        result = VectorizedValidator.validate_option_arrays(
            spot=100.0,
            strike=95.0,
            time=1.0,
            rate=0.05,
            sigma=0.2,
        )
        assert "spot" in result
        assert "strike" in result
        assert "time" in result
        assert "rate" in result
        assert "sigma" in result
        assert all(isinstance(arr, np.ndarray) for arr in result.values())

    def test_validate_option_arrays_with_dividend(self) -> None:
        """Test validate_option_arrays with dividend."""
        result = VectorizedValidator.validate_option_arrays(
            spot=100.0,
            strike=95.0,
            time=1.0,
            rate=0.05,
            sigma=0.2,
            dividend=0.02,
        )
        assert "dividend" in result
        assert result["dividend"] == 0.02

    def test_validate_option_arrays_batch(self) -> None:
        """Test validate_option_arrays with batch inputs."""
        result = VectorizedValidator.validate_option_arrays(
            spot=[100, 110, 120],
            strike=[95, 100, 105],
            time=[0.5, 1.0, 1.5],
            rate=[0.05, 0.05, 0.05],
            sigma=[0.2, 0.25, 0.3],
        )
        assert result["spot"].shape == (3,)
        assert result["strike"].shape == (3,)
        assert np.array_equal(result["spot"], [100, 110, 120])

    def test_validate_option_arrays_broadcast(self) -> None:
        """Test validate_option_arrays with broadcasting."""
        result = VectorizedValidator.validate_option_arrays(
            spot=[100, 110, 120],
            strike=95.0,  # Scalar broadcasts
            time=1.0,
            rate=0.05,
            sigma=[0.2, 0.25, 0.3],  # Must match spot length
            broadcast=True,
        )
        assert result["spot"].shape == (3,)
        assert result["strike"].shape == ()
        assert result["sigma"].shape == (3,)

    def test_validate_option_arrays_negative_spot(self) -> None:
        """Test validate_option_arrays with negative spot."""
        with pytest.raises(ValidationError) as exc_info:
            VectorizedValidator.validate_option_arrays(
                spot=-100.0,
                strike=95.0,
                time=1.0,
                rate=0.05,
                sigma=0.2,
            )
        assert "spot prices" in str(exc_info.value)

    def test_validate_option_arrays_zero_strike(self) -> None:
        """Test validate_option_arrays with zero strike."""
        with pytest.raises(ValidationError) as exc_info:
            VectorizedValidator.validate_option_arrays(
                spot=100.0,
                strike=0.0,
                time=1.0,
                rate=0.05,
                sigma=0.2,
            )
        assert "strike prices" in str(exc_info.value)

    def test_validate_option_arrays_negative_time(self) -> None:
        """Test validate_option_arrays with negative time."""
        with pytest.raises(ValidationError) as exc_info:
            VectorizedValidator.validate_option_arrays(
                spot=100.0,
                strike=95.0,
                time=-1.0,
                rate=0.05,
                sigma=0.2,
            )
        assert "times to maturity" in str(exc_info.value)

    def test_validate_option_arrays_zero_time_allowed(self) -> None:
        """Test validate_option_arrays with zero time (allowed in non-strict mode)."""
        result = VectorizedValidator.validate_option_arrays(
            spot=100.0,
            strike=95.0,
            time=0.0,
            rate=0.05,
            sigma=0.2,
        )
        assert result["time"] == 0.0

    def test_validate_option_arrays_negative_volatility(self) -> None:
        """Test validate_option_arrays with negative volatility."""
        with pytest.raises(ValidationError) as exc_info:
            VectorizedValidator.validate_option_arrays(
                spot=100.0,
                strike=95.0,
                time=1.0,
                rate=0.05,
                sigma=-0.2,
            )
        assert "volatilities" in str(exc_info.value)

    def test_validate_option_arrays_inf_rate(self) -> None:
        """Test validate_option_arrays with infinite rate."""
        with pytest.raises(ValidationError) as exc_info:
            VectorizedValidator.validate_option_arrays(
                spot=100.0,
                strike=95.0,
                time=1.0,
                rate=float("inf"),
                sigma=0.2,
            )
        assert "rate" in str(exc_info.value)
        assert "finite" in str(exc_info.value)

    def test_validate_option_arrays_nan_dividend(self) -> None:
        """Test validate_option_arrays with NaN dividend."""
        with pytest.raises(ValidationError) as exc_info:
            VectorizedValidator.validate_option_arrays(
                spot=100.0,
                strike=95.0,
                time=1.0,
                rate=0.05,
                sigma=0.2,
                dividend=float("nan"),
            )
        assert "dividend" in str(exc_info.value)
        assert "finite" in str(exc_info.value)


class TestValidateBatchInputs:
    """Test validate_batch_inputs function."""

    def test_black_scholes_valid(self) -> None:
        """Test validate_batch_inputs for Black-Scholes model."""
        result = validate_batch_inputs(
            "black_scholes",
            spot=100.0,
            strike=95.0,
            time=1.0,
            rate=0.05,
            sigma=0.2,
        )
        assert all(key in result for key in ["spot", "strike", "time", "rate", "sigma"])

    def test_black_scholes_missing_params(self) -> None:
        """Test validate_batch_inputs for Black-Scholes with missing parameters."""
        with pytest.raises(ValueError) as exc_info:
            validate_batch_inputs(
                "black_scholes",
                spot=100.0,
                strike=95.0,
                # Missing time, rate, sigma
            )
        assert "Missing required parameters" in str(exc_info.value)
        assert "time" in str(exc_info.value)

    def test_black76_valid(self) -> None:
        """Test validate_batch_inputs for Black76 model."""
        result = validate_batch_inputs(
            "black76",
            forward=100.0,
            strike=95.0,
            time=1.0,
            rate=0.05,
            sigma=0.2,
        )
        assert "spot" in result  # forward is renamed to spot internally

    def test_black76_forwards_plural(self) -> None:
        """Test validate_batch_inputs for Black76 with 'forwards' instead of 'forward'."""
        result = validate_batch_inputs(
            "black76",
            forwards=100.0,  # Plural form
            strike=95.0,
            time=1.0,
            rate=0.05,
            sigma=0.2,
        )
        assert "spot" in result

    def test_black76_missing_params(self) -> None:
        """Test validate_batch_inputs for Black76 with missing parameters."""
        with pytest.raises(ValueError) as exc_info:
            validate_batch_inputs(
                "black76",
                strike=95.0,
                time=1.0,
                # Missing forward, rate, sigma
            )
        assert "Missing required parameters" in str(exc_info.value)

    def test_merton_valid(self) -> None:
        """Test validate_batch_inputs for Merton model."""
        result = validate_batch_inputs(
            "merton",
            spot=100.0,
            strike=95.0,
            time=1.0,
            rate=0.05,
            sigma=0.2,
            dividend=0.02,
        )
        assert "dividend" in result
        assert result["dividend"] == 0.02

    def test_merton_dividends_plural(self) -> None:
        """Test validate_batch_inputs for Merton with 'dividends' instead of 'dividend'."""
        result = validate_batch_inputs(
            "merton",
            spot=100.0,
            strike=95.0,
            time=1.0,
            rate=0.05,
            sigma=0.2,
            dividends=0.02,  # Plural form
        )
        assert "dividend" in result

    def test_merton_q_notation(self) -> None:
        """Test validate_batch_inputs for Merton with 'q' instead of 'dividend'."""
        result = validate_batch_inputs(
            "merton",
            spot=100.0,
            strike=95.0,
            time=1.0,
            rate=0.05,
            sigma=0.2,
            q=0.02,  # Alternative notation
        )
        assert "dividend" in result

    def test_american_valid(self) -> None:
        """Test validate_batch_inputs for American model."""
        result = validate_batch_inputs(
            "american",
            spot=100.0,
            strike=95.0,
            time=1.0,
            rate=0.05,
            sigma=0.2,
            dividend=0.02,
        )
        assert all(key in result for key in ["spot", "strike", "time", "rate", "sigma", "dividend"])

    def test_american_missing_dividend(self) -> None:
        """Test validate_batch_inputs for American with missing dividend."""
        with pytest.raises(ValueError) as exc_info:
            validate_batch_inputs(
                "american",
                spot=100.0,
                strike=95.0,
                time=1.0,
                rate=0.05,
                sigma=0.2,
                # Missing dividend
            )
        assert "Missing required parameters" in str(exc_info.value)
        assert "dividend" in str(exc_info.value)

    def test_unknown_model(self) -> None:
        """Test validate_batch_inputs with unknown model type."""
        with pytest.raises(ValueError) as exc_info:
            validate_batch_inputs(
                "unknown_model",
                spot=100.0,
                strike=95.0,
                time=1.0,
                rate=0.05,
                sigma=0.2,
            )
        assert "Unknown model type" in str(exc_info.value)

    def test_batch_inputs_arrays(self) -> None:
        """Test validate_batch_inputs with array inputs."""
        spots = [100, 110, 120]
        strikes = [95, 100, 105]
        times = [0.5, 1.0, 1.5]
        rates = [0.05, 0.05, 0.05]
        sigmas = [0.2, 0.25, 0.3]

        result = validate_batch_inputs(
            "black_scholes",
            spot=spots,
            strike=strikes,
            time=times,
            rate=rates,
            sigma=sigmas,
        )

        assert result["spot"].shape == (3,)
        assert result["strike"].shape == (3,)
        assert np.array_equal(result["spot"], spots)
        assert np.array_equal(result["strike"], strikes)

    def test_batch_inputs_mixed_scalar_array(self) -> None:
        """Test validate_batch_inputs with mixed scalar and array inputs."""
        result = validate_batch_inputs(
            "black_scholes",
            spot=[100, 110, 120],
            strike=95.0,  # Scalar
            time=1.0,  # Scalar
            rate=0.05,  # Scalar
            sigma=[0.2, 0.25, 0.3],  # Array
        )

        assert result["spot"].shape == (3,)
        assert result["strike"].shape == ()  # Scalar
        assert result["sigma"].shape == (3,)


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_ensure_array_with_complex_numbers(self) -> None:
        """Test ensure_array behavior with complex numbers."""
        # Complex numbers should work if dtype allows
        result = VectorizedValidator.ensure_array([1 + 2j, 3 + 4j], dtype=np.complex128, name="complex_data")
        assert result.dtype == np.complex128
        assert result[0] == 1 + 2j

    def test_validate_positive_array_multidimensional(self) -> None:
        """Test validate_positive_array with multidimensional arrays."""
        arr = [[1, 2], [3, 4]]
        result = VectorizedValidator.validate_positive_array(arr)
        assert result.shape == (2, 2)
        assert np.array_equal(result, [[1, 2], [3, 4]])

        # With negative in 2D array
        arr_neg = [[1, 2], [3, -4]]
        with pytest.raises(ValidationError) as exc_info:
            VectorizedValidator.validate_positive_array(arr_neg)
        # Note: argmax on flattened array
        assert "index" in str(exc_info.value)

    def test_validate_shape_compatibility_empty_dict(self) -> None:
        """Test validate_shape_compatibility with empty dictionary."""
        result = VectorizedValidator.validate_shape_compatibility({})
        assert result == {}

    def test_validate_shape_compatibility_single_array(self) -> None:
        """Test validate_shape_compatibility with single array."""
        arrays: dict[str, ArrayLike] = {"single": [1, 2, 3]}
        result = VectorizedValidator.validate_shape_compatibility(arrays)
        assert result["single"].shape == (3,)

    def test_validate_option_arrays_large_batch(self) -> None:
        """Test validate_option_arrays with large batch."""
        n = 10000
        result = VectorizedValidator.validate_option_arrays(
            spot=np.random.uniform(50, 150, n),
            strike=np.random.uniform(50, 150, n),
            time=np.random.uniform(0.1, 2.0, n),
            rate=np.random.uniform(-0.01, 0.1, n),
            sigma=np.random.uniform(0.1, 0.5, n),
        )
        assert all(arr.shape == (n,) for arr in result.values())

    def test_validate_batch_inputs_extra_params(self) -> None:
        """Test validate_batch_inputs ignores extra parameters."""
        # Extra parameters should be ignored
        result = validate_batch_inputs(
            "black_scholes",
            spot=100.0,
            strike=95.0,
            time=1.0,
            rate=0.05,
            sigma=0.2,
            extra_param="ignored",  # This should be ignored
        )
        assert "extra_param" not in result
        assert "spot" in result
