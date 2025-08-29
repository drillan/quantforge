"""Unit tests for the errors module."""

import numpy as np
import pytest
from quantforge.errors import (
    ConvergenceError,
    DimensionError,
    ErrorHandler,
    InputValidator,
    NumericalError,
    ValidationError,
    validate_dividend_yield,
    validate_rate,
    validate_spot,
    validate_strike,
    validate_time,
    validate_volatility,
)


class TestValidationError:
    """Test ValidationError class."""

    def test_validation_error_creation(self) -> None:
        """Test creating ValidationError with all attributes."""
        error = ValidationError(parameter="test_param", value=42, message="invalid value")
        assert error.parameter == "test_param"
        assert error.value == 42
        assert error.message == "invalid value"

    def test_validation_error_string_representation(self) -> None:
        """Test string representation of ValidationError."""
        error = ValidationError(parameter="spot_price", value=-10, message="must be positive")
        assert str(error) == "Invalid spot_price: must be positive (got -10)"

    def test_validation_error_with_different_types(self) -> None:
        """Test ValidationError with different value types."""
        error = ValidationError(parameter="array", value=[1, 2, 3], message="wrong size")
        assert str(error) == "Invalid array: wrong size (got [1, 2, 3])"


class TestConvergenceError:
    """Test ConvergenceError class."""

    def test_convergence_error_basic(self) -> None:
        """Test creating ConvergenceError with method only."""
        error = ConvergenceError(method="Newton-Raphson")
        assert error.method == "Newton-Raphson"
        assert str(error) == "Convergence failed in Newton-Raphson"

    def test_convergence_error_with_iterations(self) -> None:
        """Test ConvergenceError with iterations."""
        error = ConvergenceError(method="bisection", iterations=100)
        assert error.iterations == 100
        assert str(error) == "Convergence failed in bisection after 100 iterations"

    def test_convergence_error_with_tolerance(self) -> None:
        """Test ConvergenceError with tolerance."""
        error = ConvergenceError(method="gradient_descent", tolerance=1e-6)
        assert error.tolerance == 1e-6
        assert str(error) == "Convergence failed in gradient_descent tolerance=1e-06"

    def test_convergence_error_full(self) -> None:
        """Test ConvergenceError with all attributes."""
        error = ConvergenceError(method="iterative_solver", iterations=50, tolerance=1e-8)
        assert str(error) == "Convergence failed in iterative_solver after 50 iterations tolerance=1e-08"


class TestNumericalError:
    """Test NumericalError class."""

    def test_numerical_error_creation(self) -> None:
        """Test creating NumericalError."""
        error = NumericalError(operation="matrix_inversion", details="singular matrix")
        assert error.operation == "matrix_inversion"
        assert error.details == "singular matrix"

    def test_numerical_error_string_representation(self) -> None:
        """Test string representation of NumericalError."""
        error = NumericalError(operation="sqrt", details="negative input")
        assert str(error) == "Numerical error in sqrt: negative input"


class TestDimensionError:
    """Test DimensionError class."""

    def test_dimension_error_basic(self) -> None:
        """Test creating DimensionError without parameter name."""
        error = DimensionError(expected=10, actual=5)
        assert str(error) == "Dimension mismatch: expected 10, got 5"

    def test_dimension_error_with_parameter(self) -> None:
        """Test DimensionError with parameter name."""
        error = DimensionError(expected=(3, 3), actual=(2, 4), parameter="weight_matrix")
        assert str(error) == "Dimension mismatch for weight_matrix: expected (3, 3), got (2, 4)"

    def test_dimension_error_tuple_dimensions(self) -> None:
        """Test DimensionError with tuple dimensions."""
        error = DimensionError(expected=(100, 50), actual=(100, 60))
        assert error.expected == (100, 50)
        assert error.actual == (100, 60)


class TestInputValidator:
    """Test InputValidator utility class."""

    def test_validate_positive_valid(self) -> None:
        """Test validate_positive with valid input."""
        InputValidator.validate_positive(10.0, "test_value")
        InputValidator.validate_positive(0.001, "small_value")

    def test_validate_positive_invalid(self) -> None:
        """Test validate_positive with invalid input."""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_positive(0.0, "zero_value")
        assert "must be positive" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_positive(-5.0, "negative_value")
        assert "must be positive" in str(exc_info.value)

    def test_validate_non_negative_valid(self) -> None:
        """Test validate_non_negative with valid input."""
        InputValidator.validate_non_negative(0.0, "zero")
        InputValidator.validate_non_negative(10.0, "positive")

    def test_validate_non_negative_invalid(self) -> None:
        """Test validate_non_negative with invalid input."""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_non_negative(-1.0, "negative")
        assert "must be non-negative" in str(exc_info.value)

    def test_validate_finite_valid(self) -> None:
        """Test validate_finite with valid input."""
        InputValidator.validate_finite(42.0, "normal_value")
        InputValidator.validate_finite(-100.0, "negative_value")
        InputValidator.validate_finite(0, "integer_value")

    def test_validate_finite_invalid(self) -> None:
        """Test validate_finite with invalid input."""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_finite(float("inf"), "infinity")
        assert "must be finite" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_finite(float("nan"), "not_a_number")
        assert "must be finite" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_finite("not_numeric", "string")  # type: ignore
        assert "must be numeric" in str(exc_info.value)

    def test_validate_range_valid(self) -> None:
        """Test validate_range with valid input."""
        InputValidator.validate_range(5.0, 0.0, 10.0, "in_range")
        InputValidator.validate_range(0.0, 0.0, 10.0, "at_min")
        InputValidator.validate_range(10.0, 0.0, 10.0, "at_max")

    def test_validate_range_invalid(self) -> None:
        """Test validate_range with invalid input."""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_range(-1.0, 0.0, 10.0, "below_min")
        assert "must be between 0.0 and 10.0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_range(11.0, 0.0, 10.0, "above_max")
        assert "must be between 0.0 and 10.0" in str(exc_info.value)

    def test_validate_option_inputs_valid(self) -> None:
        """Test validate_option_inputs with valid inputs."""
        InputValidator.validate_option_inputs(
            spot=100.0,
            strike=95.0,
            time=1.0,
            rate=0.05,
            sigma=0.2,
        )

    def test_validate_option_inputs_invalid_spot(self) -> None:
        """Test validate_option_inputs with invalid spot price."""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_option_inputs(
                spot=-100.0,
                strike=95.0,
                time=1.0,
                rate=0.05,
                sigma=0.2,
            )
        assert "spot price" in str(exc_info.value)

    def test_validate_option_inputs_invalid_strike(self) -> None:
        """Test validate_option_inputs with invalid strike price."""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_option_inputs(
                spot=100.0,
                strike=0.0,
                time=1.0,
                rate=0.05,
                sigma=0.2,
            )
        assert "strike price" in str(exc_info.value)

    def test_validate_option_inputs_invalid_time(self) -> None:
        """Test validate_option_inputs with invalid time."""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_option_inputs(
                spot=100.0,
                strike=95.0,
                time=-1.0,
                rate=0.05,
                sigma=0.2,
            )
        assert "time to expiration" in str(exc_info.value)

    def test_validate_option_inputs_invalid_rate(self) -> None:
        """Test validate_option_inputs with invalid rate."""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_option_inputs(
                spot=100.0,
                strike=95.0,
                time=1.0,
                rate=float("inf"),
                sigma=0.2,
            )
        assert "interest rate" in str(exc_info.value)

    def test_validate_option_inputs_invalid_sigma(self) -> None:
        """Test validate_option_inputs with invalid volatility."""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_option_inputs(
                spot=100.0,
                strike=95.0,
                time=1.0,
                rate=0.05,
                sigma=0.0,
            )
        assert "volatility" in str(exc_info.value)

    def test_validate_array_positive_valid(self) -> None:
        """Test validate_array_positive with valid arrays."""
        InputValidator.validate_array_positive([1, 2, 3], "test_array")
        InputValidator.validate_array_positive(np.array([0.1, 0.2, 0.3]), "numpy_array")

    def test_validate_array_positive_invalid(self) -> None:
        """Test validate_array_positive with invalid arrays."""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_array_positive([1, 0, 3], "array_with_zero")
        assert "all elements must be positive" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_array_positive([1, -2, 3], "array_with_negative")
        assert "all elements must be positive" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_array_positive([1, float("inf"), 3], "array_with_inf")
        assert "all elements must be finite" in str(exc_info.value)


class TestErrorHandler:
    """Test ErrorHandler context manager."""

    def test_error_handler_no_exception(self) -> None:
        """Test ErrorHandler with no exception."""
        with ErrorHandler("test_operation"):
            result = 1 + 1
        assert result == 2

    def test_error_handler_custom_error_passthrough(self) -> None:
        """Test ErrorHandler passes through custom errors."""
        with pytest.raises(ValidationError) as exc_info, ErrorHandler("test_operation"):
            raise ValidationError("param", 123, "test message")
        assert "test message" in str(exc_info.value)

    def test_error_handler_convergence_error_passthrough(self) -> None:
        """Test ErrorHandler passes through ConvergenceError."""
        with pytest.raises(ConvergenceError) as exc_info, ErrorHandler("test_operation"):
            raise ConvergenceError(method="test_method")
        assert "test_method" in str(exc_info.value)

    def test_error_handler_numerical_error_passthrough(self) -> None:
        """Test ErrorHandler passes through NumericalError."""
        with pytest.raises(NumericalError) as exc_info, ErrorHandler("test_operation"):
            raise NumericalError(operation="test_op", details="test details")
        assert "test details" in str(exc_info.value)

    def test_error_handler_wraps_value_error(self) -> None:
        """Test ErrorHandler wraps ValueError."""
        with pytest.raises(ValidationError) as exc_info, ErrorHandler("test_operation"):
            raise ValueError("original value error")
        assert "original value error" in str(exc_info.value)
        assert exc_info.value.parameter == "unknown"

    def test_error_handler_wraps_runtime_error(self) -> None:
        """Test ErrorHandler wraps RuntimeError."""
        with pytest.raises(NumericalError) as exc_info, ErrorHandler("test_operation"):
            raise RuntimeError("original runtime error")
        assert "original runtime error" in str(exc_info.value)
        assert exc_info.value.operation == "test_operation"

    def test_error_handler_propagates_other_exceptions(self) -> None:
        """Test ErrorHandler propagates other exceptions."""
        with pytest.raises(TypeError), ErrorHandler("test_operation"):
            raise TypeError("type error")


class TestConvenienceFunctions:
    """Test convenience validation functions."""

    def test_validate_spot_valid(self) -> None:
        """Test validate_spot with valid values."""
        validate_spot(100.0)
        validate_spot(0.01)
        validate_spot(1000000.0)

    def test_validate_spot_invalid(self) -> None:
        """Test validate_spot with invalid values."""
        with pytest.raises(ValidationError):
            validate_spot(0.0)
        with pytest.raises(ValidationError):
            validate_spot(-100.0)
        with pytest.raises(ValidationError):
            validate_spot(float("inf"))

    def test_validate_strike_valid(self) -> None:
        """Test validate_strike with valid values."""
        validate_strike(95.0)
        validate_strike(0.001)
        validate_strike(999999.0)

    def test_validate_strike_invalid(self) -> None:
        """Test validate_strike with invalid values."""
        with pytest.raises(ValidationError):
            validate_strike(0.0)
        with pytest.raises(ValidationError):
            validate_strike(-50.0)
        with pytest.raises(ValidationError):
            validate_strike(float("nan"))

    def test_validate_time_valid(self) -> None:
        """Test validate_time with valid values."""
        validate_time(1.0)
        validate_time(0.001)
        validate_time(10.0)

    def test_validate_time_invalid(self) -> None:
        """Test validate_time with invalid values."""
        with pytest.raises(ValidationError):
            validate_time(0.0)
        with pytest.raises(ValidationError):
            validate_time(-1.0)
        with pytest.raises(ValidationError):
            validate_time(0.0001)  # Below minimum
        with pytest.raises(ValidationError):
            validate_time(101.0)  # Above maximum

    def test_validate_rate_valid(self) -> None:
        """Test validate_rate with valid values."""
        validate_rate(0.05)
        validate_rate(-0.01)
        validate_rate(0.0)
        validate_rate(0.5)

    def test_validate_rate_invalid(self) -> None:
        """Test validate_rate with invalid values."""
        with pytest.raises(ValidationError):
            validate_rate(float("inf"))
        with pytest.raises(ValidationError):
            validate_rate(-1.1)  # Below minimum
        with pytest.raises(ValidationError):
            validate_rate(1.1)  # Above maximum

    def test_validate_volatility_valid(self) -> None:
        """Test validate_volatility with valid values."""
        validate_volatility(0.2)
        validate_volatility(0.001)
        validate_volatility(2.0)

    def test_validate_volatility_invalid(self) -> None:
        """Test validate_volatility with invalid values."""
        with pytest.raises(ValidationError):
            validate_volatility(0.0)
        with pytest.raises(ValidationError):
            validate_volatility(-0.2)
        with pytest.raises(ValidationError):
            validate_volatility(0.0001)  # Below minimum
        with pytest.raises(ValidationError):
            validate_volatility(11.0)  # Above maximum

    def test_validate_dividend_yield_valid(self) -> None:
        """Test validate_dividend_yield with valid values."""
        validate_dividend_yield(0.02)
        validate_dividend_yield(-0.01)
        validate_dividend_yield(0.0)
        validate_dividend_yield(0.3)

    def test_validate_dividend_yield_invalid(self) -> None:
        """Test validate_dividend_yield with invalid values."""
        with pytest.raises(ValidationError):
            validate_dividend_yield(float("nan"))
        with pytest.raises(ValidationError):
            validate_dividend_yield(-1.1)  # Below minimum
        with pytest.raises(ValidationError):
            validate_dividend_yield(1.1)  # Above maximum


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_validation_error_with_none_value(self) -> None:
        """Test ValidationError with None value."""
        error = ValidationError(parameter="optional_param", value=None, message="cannot be None")
        assert str(error) == "Invalid optional_param: cannot be None (got None)"

    def test_validation_error_with_complex_object(self) -> None:
        """Test ValidationError with complex object."""
        complex_obj = {"key": "value", "list": [1, 2, 3]}
        error = ValidationError(parameter="config", value=complex_obj, message="invalid configuration")
        assert "invalid configuration" in str(error)

    def test_dimension_error_with_single_dimension(self) -> None:
        """Test DimensionError with single dimension."""
        error = DimensionError(expected=100, actual=50, parameter="vector_length")
        assert "expected 100, got 50" in str(error)

    def test_validate_array_positive_empty_array(self) -> None:
        """Test validate_array_positive with empty array."""
        # Empty array should not raise since there are no elements to check
        # But numpy will evaluate (arr > 0).all() as True for empty arrays
        InputValidator.validate_array_positive([], "empty_array")
        InputValidator.validate_array_positive(np.array([]), "empty_numpy_array")

    def test_error_handler_multiple_operations(self) -> None:
        """Test ErrorHandler with nested operations."""
        with ErrorHandler("outer_operation"), ErrorHandler("inner_operation"):
            result = 10 * 10
        assert result == 100

    def test_convergence_error_none_values(self) -> None:
        """Test ConvergenceError with None values."""
        error = ConvergenceError(method="solver", iterations=None, tolerance=None)
        assert str(error) == "Convergence failed in solver"
