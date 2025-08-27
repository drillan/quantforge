"""Base classes and protocols for option pricing models."""

from collections.abc import Callable
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray


class PricingFunction(Protocol):
    """Protocol for single pricing functions."""

    def __call__(self, spot: float, strike: float, time: float, rate: float, *args: float, **kwargs: float) -> float:
        """Calculate option price."""
        ...


class BatchPricingFunction(Protocol):
    """Protocol for batch pricing functions."""

    def __call__(
        self,
        spots: NDArray[np.float64],
        strikes: NDArray[np.float64],
        times: NDArray[np.float64],
        rates: NDArray[np.float64],
        *args: NDArray[np.float64],
        **kwargs: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Calculate batch option prices."""
        ...


class GreeksFunction(Protocol):
    """Protocol for Greeks calculation functions."""

    def __call__(
        self,
        spot: float,
        strike: float,
        time: float,
        rate: float,
        sigma: float,
        is_call: bool,
        *args: float,
        **kwargs: Any,
    ) -> dict[str, float]:
        """Calculate option Greeks."""
        ...


class BaseOptionModel:
    """Base class for option pricing models with common interface.

    This class provides a unified interface for all option pricing models,
    eliminating code duplication across model implementations.
    """

    def __init__(
        self, rust_module: Any, model_name: str, has_dividends: bool = False, has_exercise_boundary: bool = False
    ) -> None:
        """Initialize the option model.

        Args:
            rust_module: The Rust module containing the model functions
            model_name: Name of the model for debugging
            has_dividends: Whether the model supports dividend yield
            has_exercise_boundary: Whether the model has early exercise boundary
        """
        self._rust_module = rust_module
        self._model_name = model_name
        self._has_dividends = has_dividends
        self._has_exercise_boundary = has_exercise_boundary

        # Bind core functions
        self.call_price = self._get_function("call_price")
        self.put_price = self._get_function("put_price")

        # Bind batch functions
        self.call_price_batch = self._get_function("call_price_batch")
        self.put_price_batch = self._get_function("put_price_batch")

        # Bind Greeks functions
        self.greeks = self._get_function("greeks")
        self.greeks_batch = self._get_function("greeks_batch")

        # Bind implied volatility functions
        self.implied_volatility = self._get_function("implied_volatility")
        self.implied_volatility_batch = self._get_function("implied_volatility_batch")

        # Optional: exercise boundary for American options
        if has_exercise_boundary:
            self.exercise_boundary = self._get_function("exercise_boundary")
            self.exercise_boundary_batch = self._get_function("exercise_boundary_batch")

        # Mark deprecated batch_q functions as None
        if has_dividends:
            self.call_price_batch_q = None  # Deprecated - use full broadcasting
            self.put_price_batch_q = None  # Deprecated - use full broadcasting

    def _get_function(self, name: str) -> Callable[..., Any] | None:
        """Get a function from the Rust module.

        Args:
            name: Function name to retrieve

        Returns:
            The function if it exists, None otherwise
        """
        try:
            func = getattr(self._rust_module, name)
            return func if callable(func) else None
        except AttributeError:
            # Function might not exist for this model
            return None

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"{self.__class__.__name__}(model='{self._model_name}')"

    def validate_inputs(
        self, spot: float, strike: float, time: float, rate: float, sigma: float, dividend: float | None = None
    ) -> None:
        """Validate common input parameters.

        Args:
            spot: Spot price
            strike: Strike price
            time: Time to maturity
            rate: Risk-free rate
            sigma: Volatility
            dividend: Optional dividend yield

        Raises:
            ValueError: If any input is invalid
        """
        if spot <= 0:
            raise ValueError(f"Spot price must be positive, got {spot}")
        if strike <= 0:
            raise ValueError(f"Strike price must be positive, got {strike}")
        if time < 0:
            raise ValueError(f"Time to maturity must be non-negative, got {time}")
        if sigma < 0:
            raise ValueError(f"Volatility must be non-negative, got {sigma}")
        if dividend is not None and dividend < 0:
            raise ValueError(f"Dividend yield must be non-negative, got {dividend}")
