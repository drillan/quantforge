"""Black-Scholes model with broadcasting support."""

from typing import Union

import numpy as np
from numpy.typing import NDArray

# Import native implementation
from .quantforge import black_scholes as _native

# Type aliases
ArrayLike = Union[float, NDArray[np.float64]]


def _ensure_array(x: ArrayLike) -> NDArray[np.float64]:
    """Convert input to numpy array with float64 dtype."""
    return np.atleast_1d(np.asarray(x, dtype=np.float64))


def call_price(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """
    Calculate Black-Scholes call option price.

    Parameters
    ----------
    s : float
        Spot price
    k : float
        Strike price
    t : float
        Time to maturity (years)
    r : float
        Risk-free rate
    sigma : float
        Volatility

    Returns
    -------
    float
        Call option price
    """
    return _native.call_price(s, k, t, r, sigma)


def put_price(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """
    Calculate Black-Scholes put option price.

    Parameters
    ----------
    s : float
        Spot price
    k : float
        Strike price
    t : float
        Time to maturity (years)
    r : float
        Risk-free rate
    sigma : float
        Volatility

    Returns
    -------
    float
        Put option price
    """
    return _native.put_price(s, k, t, r, sigma)


def call_price_batch(
    spots: ArrayLike, strikes: ArrayLike, times: ArrayLike, rates: ArrayLike, sigmas: ArrayLike
) -> NDArray[np.float64]:
    """
    Calculate Black-Scholes call option prices with broadcasting.

    Parameters
    ----------
    spots : array_like
        Spot prices (scalar or array)
    strikes : array_like
        Strike prices (scalar or array)
    times : array_like
        Times to maturity in years (scalar or array)
    rates : array_like
        Risk-free rates (scalar or array)
    sigmas : array_like
        Volatilities (scalar or array)

    Returns
    -------
    numpy.ndarray
        Call option prices
    """
    # Convert all inputs to arrays
    spots = _ensure_array(spots)
    strikes = _ensure_array(strikes)
    times = _ensure_array(times)
    rates = _ensure_array(rates)
    sigmas = _ensure_array(sigmas)

    # Call native implementation
    return _native.call_price_batch(spots, strikes, times, rates, sigmas)


def put_price_batch(
    spots: ArrayLike, strikes: ArrayLike, times: ArrayLike, rates: ArrayLike, sigmas: ArrayLike
) -> NDArray[np.float64]:
    """
    Calculate Black-Scholes put option prices with broadcasting.

    Parameters
    ----------
    spots : array_like
        Spot prices (scalar or array)
    strikes : array_like
        Strike prices (scalar or array)
    times : array_like
        Times to maturity in years (scalar or array)
    rates : array_like
        Risk-free rates (scalar or array)
    sigmas : array_like
        Volatilities (scalar or array)

    Returns
    -------
    numpy.ndarray
        Put option prices
    """
    # Convert all inputs to arrays
    spots = _ensure_array(spots)
    strikes = _ensure_array(strikes)
    times = _ensure_array(times)
    rates = _ensure_array(rates)
    sigmas = _ensure_array(sigmas)

    # Call native implementation
    return _native.put_price_batch(spots, strikes, times, rates, sigmas)


def greeks(s: float, k: float, t: float, r: float, sigma: float, is_call: bool = True) -> dict[str, float]:
    """
    Calculate Black-Scholes Greeks.

    Parameters
    ----------
    s : float
        Spot price
    k : float
        Strike price
    t : float
        Time to maturity (years)
    r : float
        Risk-free rate
    sigma : float
        Volatility
    is_call : bool, default=True
        True for call, False for put

    Returns
    -------
    dict
        Dictionary with keys: delta, gamma, vega, theta, rho
    """
    return _native.greeks(s, k, t, r, sigma, is_call)


def greeks_batch(
    spots: ArrayLike, strikes: ArrayLike, times: ArrayLike, rates: ArrayLike, sigmas: ArrayLike, is_call: bool = True
) -> dict[str, NDArray[np.float64]]:
    """
    Calculate Black-Scholes Greeks with broadcasting.

    Parameters
    ----------
    spots : array_like
        Spot prices (scalar or array)
    strikes : array_like
        Strike prices (scalar or array)
    times : array_like
        Times to maturity in years (scalar or array)
    rates : array_like
        Risk-free rates (scalar or array)
    sigmas : array_like
        Volatilities (scalar or array)
    is_call : bool, default=True
        True for call, False for put

    Returns
    -------
    dict
        Dictionary with NumPy arrays for: delta, gamma, vega, theta, rho
    """
    # Convert all inputs to arrays
    spots = _ensure_array(spots)
    strikes = _ensure_array(strikes)
    times = _ensure_array(times)
    rates = _ensure_array(rates)
    sigmas = _ensure_array(sigmas)

    # Call native implementation
    return _native.greeks_batch(spots, strikes, times, rates, sigmas, is_call)


def implied_volatility(price: float, s: float, k: float, t: float, r: float, is_call: bool = True) -> float:
    """
    Calculate implied volatility using Newton-Raphson method.

    Parameters
    ----------
    price : float
        Option price
    s : float
        Spot price
    k : float
        Strike price
    t : float
        Time to maturity (years)
    r : float
        Risk-free rate
    is_call : bool, default=True
        True for call, False for put

    Returns
    -------
    float
        Implied volatility
    """
    return _native.implied_volatility(price, s, k, t, r, is_call)


def implied_volatility_batch(
    prices: ArrayLike, spots: ArrayLike, strikes: ArrayLike, times: ArrayLike, rates: ArrayLike, is_calls: ArrayLike
) -> NDArray[np.float64]:
    """
    Calculate implied volatility with broadcasting.

    Parameters
    ----------
    prices : array_like
        Option prices (scalar or array)
    spots : array_like
        Spot prices (scalar or array)
    strikes : array_like
        Strike prices (scalar or array)
    times : array_like
        Times to maturity in years (scalar or array)
    rates : array_like
        Risk-free rates (scalar or array)
    is_calls : array_like
        True for calls, False for puts (scalar or array)

    Returns
    -------
    numpy.ndarray
        Implied volatilities
    """
    # Convert all inputs to arrays
    prices = _ensure_array(prices)
    spots = _ensure_array(spots)
    strikes = _ensure_array(strikes)
    times = _ensure_array(times)
    rates = _ensure_array(rates)
    is_calls = np.atleast_1d(np.asarray(is_calls, dtype=bool))

    # Call native implementation
    return _native.implied_volatility_batch(prices, spots, strikes, times, rates, is_calls)
