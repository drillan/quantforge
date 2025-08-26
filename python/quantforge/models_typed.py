"""QuantForge models module - option pricing models with complete type hints.

This module provides fully typed interfaces to the Rust-based option pricing models.
"""

from typing import Protocol, overload

import numpy as np
from numpy.typing import ArrayLike, NDArray


class Greeks(Protocol):
    """Protocol for option Greeks."""

    @property
    def delta(self) -> float:
        """Rate of change of option price with respect to underlying price."""
        ...

    @property
    def gamma(self) -> float:
        """Rate of change of delta with respect to underlying price."""
        ...

    @property
    def vega(self) -> float:
        """Rate of change of option price with respect to volatility."""
        ...

    @property
    def theta(self) -> float:
        """Rate of change of option price with respect to time."""
        ...

    @property
    def rho(self) -> float:
        """Rate of change of option price with respect to interest rate."""
        ...


class MertonGreeks(Greeks, Protocol):
    """Protocol for Merton model Greeks with dividend yield sensitivity."""

    @property
    def psi(self) -> float:
        """Rate of change of option price with respect to dividend yield."""
        ...


class OptionPricingModel(Protocol):
    """Protocol for option pricing models."""

    def call_price(
        self,
        spot: float,
        strike: float,
        time: float,
        rate: float,
        sigma: float,
    ) -> float:
        """Calculate call option price.

        Args:
            spot: Current price of underlying asset
            strike: Strike price of the option
            time: Time to expiration (in years)
            rate: Risk-free interest rate
            sigma: Volatility of the underlying

        Returns:
            Call option price

        Raises:
            ValueError: If inputs are invalid (negative prices, time, or volatility)
        """
        ...

    def put_price(
        self,
        spot: float,
        strike: float,
        time: float,
        rate: float,
        sigma: float,
    ) -> float:
        """Calculate put option price.

        Args:
            spot: Current price of underlying asset
            strike: Strike price of the option
            time: Time to expiration (in years)
            rate: Risk-free interest rate
            sigma: Volatility of the underlying

        Returns:
            Put option price

        Raises:
            ValueError: If inputs are invalid
        """
        ...

    def call_price_batch(
        self,
        spots: ArrayLike,
        strike: float,
        time: float,
        rate: float,
        sigma: float,
    ) -> NDArray[np.float64]:
        """Calculate call option prices for multiple spot prices.

        Args:
            spots: Array of spot prices
            strike: Strike price of the option
            time: Time to expiration (in years)
            rate: Risk-free interest rate
            sigma: Volatility of the underlying

        Returns:
            Array of call option prices

        Raises:
            ValueError: If inputs are invalid
        """
        ...

    def put_price_batch(
        self,
        spots: ArrayLike,
        strike: float,
        time: float,
        rate: float,
        sigma: float,
    ) -> NDArray[np.float64]:
        """Calculate put option prices for multiple spot prices.

        Args:
            spots: Array of spot prices
            strike: Strike price of the option
            time: Time to expiration (in years)
            rate: Risk-free interest rate
            sigma: Volatility of the underlying

        Returns:
            Array of put option prices

        Raises:
            ValueError: If inputs are invalid
        """
        ...

    def greeks(
        self,
        spot: float,
        strike: float,
        time: float,
        rate: float,
        sigma: float,
        is_call: bool = True,
    ) -> Greeks:
        """Calculate option Greeks.

        Args:
            spot: Current price of underlying asset
            strike: Strike price of the option
            time: Time to expiration (in years)
            rate: Risk-free interest rate
            sigma: Volatility of the underlying
            is_call: True for call option, False for put option

        Returns:
            Greeks object with delta, gamma, vega, theta, rho

        Raises:
            ValueError: If inputs are invalid
        """
        ...

    @overload
    def implied_volatility(
        self,
        price: float,
        spot: float,
        strike: float,
        time: float,
        rate: float,
        is_call: bool = True,
        *,
        initial_guess: None = None,
    ) -> float: ...

    @overload
    def implied_volatility(
        self,
        price: float,
        spot: float,
        strike: float,
        time: float,
        rate: float,
        is_call: bool = True,
        *,
        initial_guess: float,
    ) -> float: ...

    def implied_volatility(
        self,
        price: float,
        spot: float,
        strike: float,
        time: float,
        rate: float,
        is_call: bool = True,
        initial_guess: float | None = None,
    ) -> float:
        """Calculate implied volatility from option price.

        Args:
            price: Option market price
            spot: Current price of underlying asset
            strike: Strike price of the option
            time: Time to expiration (in years)
            rate: Risk-free interest rate
            is_call: True for call option, False for put option
            initial_guess: Initial guess for volatility (optional)

        Returns:
            Implied volatility

        Raises:
            ValueError: If inputs are invalid or convergence fails
            RuntimeError: If implied volatility cannot be found
        """
        ...


class FuturesOptionPricingModel(Protocol):
    """Protocol for futures option pricing models (e.g., Black76)."""

    def call_price(
        self,
        forward: float,
        strike: float,
        time: float,
        rate: float,
        sigma: float,
    ) -> float:
        """Calculate call option price on futures.

        Args:
            forward: Forward price of the underlying
            strike: Strike price of the option
            time: Time to expiration (in years)
            rate: Risk-free interest rate
            sigma: Volatility of the underlying

        Returns:
            Call option price

        Raises:
            ValueError: If inputs are invalid
        """
        ...

    def put_price(
        self,
        forward: float,
        strike: float,
        time: float,
        rate: float,
        sigma: float,
    ) -> float:
        """Calculate put option price on futures.

        Args:
            forward: Forward price of the underlying
            strike: Strike price of the option
            time: Time to expiration (in years)
            rate: Risk-free interest rate
            sigma: Volatility of the underlying

        Returns:
            Put option price

        Raises:
            ValueError: If inputs are invalid
        """
        ...

    def call_price_batch(
        self,
        forwards: ArrayLike,
        strike: float,
        time: float,
        rate: float,
        sigma: float,
    ) -> NDArray[np.float64]:
        """Calculate call option prices for multiple forward prices."""
        ...

    def put_price_batch(
        self,
        forwards: ArrayLike,
        strike: float,
        time: float,
        rate: float,
        sigma: float,
    ) -> NDArray[np.float64]:
        """Calculate put option prices for multiple forward prices."""
        ...


class DividendOptionPricingModel(Protocol):
    """Protocol for option pricing models with dividend support (e.g., Merton)."""

    def call_price(
        self,
        spot: float,
        strike: float,
        time: float,
        rate: float,
        div_yield: float,
        sigma: float,
    ) -> float:
        """Calculate call option price with dividends.

        Args:
            spot: Current price of underlying asset
            strike: Strike price of the option
            time: Time to expiration (in years)
            rate: Risk-free interest rate
            div_yield: Continuous dividend yield
            sigma: Volatility of the underlying

        Returns:
            Call option price

        Raises:
            ValueError: If inputs are invalid
        """
        ...

    def put_price(
        self,
        spot: float,
        strike: float,
        time: float,
        rate: float,
        div_yield: float,
        sigma: float,
    ) -> float:
        """Calculate put option price with dividends."""
        ...

    def call_price_batch(
        self,
        spots: ArrayLike,
        strike: float,
        time: float,
        rate: float,
        sigma: float,
    ) -> NDArray[np.float64]:
        """Calculate call prices for multiple spots (no dividend)."""
        ...

    def put_price_batch(
        self,
        spots: ArrayLike,
        strike: float,
        time: float,
        rate: float,
        sigma: float,
    ) -> NDArray[np.float64]:
        """Calculate put prices for multiple spots (no dividend)."""
        ...

    def call_price_batch_q(
        self,
        spots: ArrayLike,
        strike: float,
        time: float,
        rate: float,
        div_yield: float,
        sigma: float,
    ) -> NDArray[np.float64]:
        """Calculate call prices for multiple spots with dividend."""
        ...

    def put_price_batch_q(
        self,
        spots: ArrayLike,
        strike: float,
        time: float,
        rate: float,
        div_yield: float,
        sigma: float,
    ) -> NDArray[np.float64]:
        """Calculate put prices for multiple spots with dividend."""
        ...

    def greeks(
        self,
        spot: float,
        strike: float,
        time: float,
        rate: float,
        div_yield: float,
        sigma: float,
        is_call: bool = True,
    ) -> MertonGreeks:
        """Calculate option Greeks including dividend sensitivity (psi)."""
        ...


# Import the actual implementations
try:
    from ..quantforge import models as _rust_models  # type: ignore[import-not-found]

    # Type-safe wrappers
    class BlackScholesTyped:
        """Type-safe wrapper for Black-Scholes model."""

        def __init__(self) -> None:
            self._impl = _rust_models

        def call_price(self, spot: float, strike: float, time: float, rate: float, sigma: float) -> float:
            return self._impl.call_price(spot, strike, time, rate, sigma)

        def put_price(self, spot: float, strike: float, time: float, rate: float, sigma: float) -> float:
            return self._impl.put_price(spot, strike, time, rate, sigma)

        def call_price_batch(
            self, spots: ArrayLike, strike: float, time: float, rate: float, sigma: float
        ) -> NDArray[np.float64]:
            return self._impl.call_price_batch(spots, strike, time, rate, sigma)

        def put_price_batch(
            self, spots: ArrayLike, strike: float, time: float, rate: float, sigma: float
        ) -> NDArray[np.float64]:
            return self._impl.put_price_batch(spots, strike, time, rate, sigma)

        def greeks(
            self,
            spot: float,
            strike: float,
            time: float,
            rate: float,
            sigma: float,
            is_call: bool = True,
        ) -> Greeks:
            return self._impl.greeks(spot, strike, time, rate, sigma, is_call)

        def implied_volatility(
            self,
            price: float,
            spot: float,
            strike: float,
            time: float,
            rate: float,
            is_call: bool = True,
            initial_guess: float | None = None,
        ) -> float:
            return self._impl.implied_volatility(price, spot, strike, time, rate, is_call, initial_guess)

    black_scholes: OptionPricingModel = BlackScholesTyped()

except ImportError:
    # Provide mock implementations for type checking
    black_scholes = None  # type: ignore[assignment]

__all__ = [
    "Greeks",
    "MertonGreeks",
    "OptionPricingModel",
    "FuturesOptionPricingModel",
    "DividendOptionPricingModel",
    "black_scholes",
]
