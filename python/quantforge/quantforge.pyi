"""Type stubs for quantforge native module"""

from typing import Union

import numpy as np
from numpy.typing import ArrayLike, NDArray

# Type aliases
FloatOrArray = Union[float, ArrayLike]

# Black-Scholes module
class black_scholes:
    @staticmethod
    def call_price(s: float, k: float, t: float, r: float, sigma: float) -> float:
        """Calculate Black-Scholes call option price.

        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            sigma: Volatility

        Returns:
            Call option price
        """
        ...

    @staticmethod
    def put_price(s: float, k: float, t: float, r: float, sigma: float) -> float:
        """Calculate Black-Scholes put option price."""
        ...

    @staticmethod
    def call_price_batch(
        spots: FloatOrArray, strikes: FloatOrArray, times: FloatOrArray, rates: FloatOrArray, sigmas: FloatOrArray
    ) -> NDArray[np.float64]:
        """Calculate batch of Black-Scholes call option prices."""
        ...

    @staticmethod
    def put_price_batch(
        spots: FloatOrArray, strikes: FloatOrArray, times: FloatOrArray, rates: FloatOrArray, sigmas: FloatOrArray
    ) -> NDArray[np.float64]:
        """Calculate batch of Black-Scholes put option prices."""
        ...

    @staticmethod
    def greeks(s: float, k: float, t: float, r: float, sigma: float, is_call: bool = True) -> dict[str, float]:
        """Calculate Greeks for Black-Scholes model."""
        ...

    @staticmethod
    def greeks_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        sigmas: FloatOrArray,
        is_calls: FloatOrArray,
    ) -> dict[str, NDArray[np.float64]]:
        """Calculate batch of Greeks for Black-Scholes model."""
        ...

    @staticmethod
    def implied_volatility(price: float, s: float, k: float, t: float, r: float, is_call: bool) -> float:
        """Calculate implied volatility using Black-Scholes model."""
        ...

    @staticmethod
    def implied_volatility_batch(
        prices: FloatOrArray,
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        is_calls: FloatOrArray,
    ) -> NDArray[np.float64]:
        """Calculate batch of implied volatilities."""
        ...

# Black76 module
class black76:
    @staticmethod
    def call_price(f: float, k: float, t: float, r: float, sigma: float) -> float:
        """Calculate Black76 call option price.

        Args:
            f: Forward price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            sigma: Volatility

        Returns:
            Call option price
        """
        ...

    @staticmethod
    def put_price(f: float, k: float, t: float, r: float, sigma: float) -> float:
        """Calculate Black76 put option price."""
        ...

    @staticmethod
    def call_price_batch(
        forwards: FloatOrArray, strikes: FloatOrArray, times: FloatOrArray, rates: FloatOrArray, sigmas: FloatOrArray
    ) -> NDArray[np.float64]:
        """Calculate batch of Black76 call option prices."""
        ...

    @staticmethod
    def put_price_batch(
        forwards: FloatOrArray, strikes: FloatOrArray, times: FloatOrArray, rates: FloatOrArray, sigmas: FloatOrArray
    ) -> NDArray[np.float64]:
        """Calculate batch of Black76 put option prices."""
        ...

    @staticmethod
    def greeks(f: float, k: float, t: float, r: float, sigma: float, is_call: bool = True) -> dict[str, float]:
        """Calculate Greeks for Black76 model."""
        ...

    @staticmethod
    def greeks_batch(
        forwards: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        sigmas: FloatOrArray,
        is_calls: FloatOrArray,
    ) -> dict[str, NDArray[np.float64]]:
        """Calculate batch of Greeks for Black76 model."""
        ...

    @staticmethod
    def implied_volatility(price: float, f: float, k: float, t: float, r: float, is_call: bool) -> float:
        """Calculate implied volatility using Black76 model."""
        ...

    @staticmethod
    def implied_volatility_batch(
        prices: FloatOrArray,
        forwards: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        is_calls: FloatOrArray,
    ) -> NDArray[np.float64]:
        """Calculate batch of implied volatilities."""
        ...

# Merton model
class merton:
    @staticmethod
    def call_price(s: float, k: float, t: float, r: float, q: float, sigma: float) -> float:
        """Calculate Merton call option price.

        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            q: Dividend yield
            sigma: Volatility

        Returns:
            Call option price
        """
        ...

    @staticmethod
    def put_price(s: float, k: float, t: float, r: float, q: float, sigma: float) -> float:
        """Calculate Merton put option price."""
        ...

    @staticmethod
    def call_price_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray,
    ) -> NDArray[np.float64]:
        """Calculate batch of Merton call option prices."""
        ...

    @staticmethod
    def put_price_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray,
    ) -> NDArray[np.float64]:
        """Calculate batch of Merton put option prices."""
        ...

    @staticmethod
    def greeks(
        s: float, k: float, t: float, r: float, q: float, sigma: float, is_call: bool = True
    ) -> dict[str, float]:
        """Calculate Greeks for Merton model."""
        ...

    @staticmethod
    def greeks_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray,
        is_calls: FloatOrArray,
    ) -> dict[str, NDArray[np.float64]]:
        """Calculate batch of Greeks for Merton model."""
        ...

    @staticmethod
    def implied_volatility(price: float, s: float, k: float, t: float, r: float, q: float, is_call: bool) -> float:
        """Calculate implied volatility using Merton model."""
        ...

    @staticmethod
    def implied_volatility_batch(
        prices: FloatOrArray,
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        is_calls: FloatOrArray,
    ) -> NDArray[np.float64]:
        """Calculate batch of implied volatilities."""
        ...

# American model
class american:
    @staticmethod
    def call_price(s: float, k: float, t: float, r: float, q: float, sigma: float) -> float:
        """Calculate American call option price using Bjerksund-Stensland approximation.

        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            q: Dividend yield
            sigma: Volatility

        Returns:
            Call option price
        """
        ...

    @staticmethod
    def put_price(s: float, k: float, t: float, r: float, q: float, sigma: float) -> float:
        """Calculate American put option price."""
        ...

    @staticmethod
    def call_price_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray,
    ) -> NDArray[np.float64]:
        """Calculate batch of American call option prices."""
        ...

    @staticmethod
    def put_price_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray,
    ) -> NDArray[np.float64]:
        """Calculate batch of American put option prices."""
        ...

    @staticmethod
    def greeks(
        s: float, k: float, t: float, r: float, q: float, sigma: float, is_call: bool = True
    ) -> dict[str, float]:
        """Calculate Greeks for American model."""
        ...

    @staticmethod
    def greeks_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray,
        is_calls: FloatOrArray,
    ) -> dict[str, NDArray[np.float64]]:
        """Calculate batch of Greeks for American model."""
        ...

    @staticmethod
    def implied_volatility(price: float, s: float, k: float, t: float, r: float, q: float, is_call: bool) -> float:
        """Calculate implied volatility using American model."""
        ...

    @staticmethod
    def implied_volatility_batch(
        prices: FloatOrArray,
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        is_calls: FloatOrArray,
    ) -> NDArray[np.float64]:
        """Calculate batch of implied volatilities."""
        ...

# Module version
__version__: str
