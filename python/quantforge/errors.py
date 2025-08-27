"""Unified error handling for QuantForge Python API.

This module provides consistent error types and validation utilities.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationError(ValueError):
    """Input validation error."""

    parameter: str
    value: Any
    message: str

    def __str__(self) -> str:
        return f"Invalid {self.parameter}: {self.message} (got {self.value})"


@dataclass
class ConvergenceError(RuntimeError):
    """Numerical convergence error."""

    method: str
    iterations: int | None = None
    tolerance: float | None = None

    def __str__(self) -> str:
        parts = [f"Convergence failed in {self.method}"]
        if self.iterations:
            parts.append(f"after {self.iterations} iterations")
        if self.tolerance:
            parts.append(f"tolerance={self.tolerance}")
        return " ".join(parts)


@dataclass
class NumericalError(RuntimeError):
    """General numerical computation error."""

    operation: str
    details: str

    def __str__(self) -> str:
        return f"Numerical error in {self.operation}: {self.details}"


@dataclass
class DimensionError(ValueError):
    """Dimension mismatch error."""

    expected: int | tuple[int, ...]
    actual: int | tuple[int, ...]
    parameter: str | None = None

    def __str__(self) -> str:
        if self.parameter:
            return f"Dimension mismatch for {self.parameter}: expected {self.expected}, got {self.actual}"
        return f"Dimension mismatch: expected {self.expected}, got {self.actual}"


class InputValidator:
    """Utility class for input validation with consistent error messages."""

    @staticmethod
    def validate_positive(value: float, name: str) -> None:
        """Validate that a value is positive."""
        if value <= 0:
            raise ValidationError(name, value, "must be positive")

    @staticmethod
    def validate_non_negative(value: float, name: str) -> None:
        """Validate that a value is non-negative."""
        if value < 0:
            raise ValidationError(name, value, "must be non-negative")

    @staticmethod
    def validate_finite(value: float, name: str) -> None:
        """Validate that a value is finite (not NaN or Inf)."""
        if not isinstance(value, int | float):
            raise ValidationError(name, value, "must be numeric")

        import math

        if not math.isfinite(value):
            raise ValidationError(name, value, "must be finite")

    @staticmethod
    def validate_range(value: float, min_val: float, max_val: float, name: str) -> None:
        """Validate that a value is within a range."""
        if not min_val <= value <= max_val:
            raise ValidationError(name, value, f"must be between {min_val} and {max_val}")

    @staticmethod
    def validate_option_inputs(
        spot: float,
        strike: float,
        time: float,
        rate: float,
        sigma: float,
    ) -> None:
        """Validate standard option pricing inputs."""
        InputValidator.validate_positive(spot, "spot price")
        InputValidator.validate_positive(strike, "strike price")
        InputValidator.validate_positive(time, "time to expiration")
        InputValidator.validate_finite(rate, "interest rate")
        InputValidator.validate_positive(sigma, "volatility")

    @staticmethod
    def validate_array_positive(values: Any, name: str) -> None:
        """Validate that all values in an array are positive."""
        import numpy as np

        arr = np.asarray(values)
        if not (arr > 0).all():
            raise ValidationError(name, "array", "all elements must be positive")
        if not np.isfinite(arr).all():
            raise ValidationError(name, "array", "all elements must be finite")


class ErrorHandler:
    """Context manager for consistent error handling."""

    def __init__(self, operation: str):
        self.operation = operation

    def __enter__(self) -> "ErrorHandler":
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        if exc_type is None:
            return

        # Re-raise our custom errors as-is
        if isinstance(exc_val, ValidationError | ConvergenceError | NumericalError):
            return

        # Wrap unexpected errors
        if exc_type is ValueError:
            raise ValidationError(parameter="unknown", value="N/A", message=str(exc_val)) from exc_val
        elif exc_type is RuntimeError:
            raise NumericalError(operation=self.operation, details=str(exc_val)) from exc_val

        # Let other exceptions propagate
        return


# Convenience functions for common validations
def validate_spot(spot: float) -> None:
    """Validate spot price."""
    InputValidator.validate_positive(spot, "spot price")
    InputValidator.validate_finite(spot, "spot price")


def validate_strike(strike: float) -> None:
    """Validate strike price."""
    InputValidator.validate_positive(strike, "strike price")
    InputValidator.validate_finite(strike, "strike price")


def validate_time(time: float) -> None:
    """Validate time to expiration."""
    InputValidator.validate_positive(time, "time to expiration")
    InputValidator.validate_finite(time, "time to expiration")
    InputValidator.validate_range(time, 0.001, 100.0, "time to expiration")


def validate_rate(rate: float) -> None:
    """Validate interest rate."""
    InputValidator.validate_finite(rate, "interest rate")
    InputValidator.validate_range(rate, -1.0, 1.0, "interest rate")


def validate_volatility(sigma: float) -> None:
    """Validate volatility."""
    InputValidator.validate_positive(sigma, "volatility")
    InputValidator.validate_finite(sigma, "volatility")
    InputValidator.validate_range(sigma, 0.001, 10.0, "volatility")


def validate_dividend_yield(div_yield: float) -> None:
    """Validate dividend yield."""
    InputValidator.validate_finite(div_yield, "dividend yield")
    InputValidator.validate_range(div_yield, -1.0, 1.0, "dividend yield")


__all__ = [
    "ValidationError",
    "ConvergenceError",
    "NumericalError",
    "InputValidator",
    "ErrorHandler",
    "validate_spot",
    "validate_strike",
    "validate_time",
    "validate_rate",
    "validate_volatility",
    "validate_dividend_yield",
]
