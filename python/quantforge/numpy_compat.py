"""
NumPy compatibility layer for QuantForge Arrow API.

This module provides convenience functions for NumPy users who want to
leverage the performance of QuantForge without converting to Arrow arrays.
For best performance, use the Arrow API directly.
"""


import numpy as np
import pyarrow as pa

from . import arrow_api


def call_price_numpy(
    spots: np.ndarray,
    strikes: np.ndarray,
    times: np.ndarray,
    rates: np.ndarray,
    sigmas: np.ndarray,
) -> np.ndarray:
    """
    Calculate Black-Scholes call option prices using NumPy arrays.

    This is a convenience wrapper around the Arrow API for NumPy users.
    For best performance, use the Arrow API directly.

    Parameters
    ----------
    spots : np.ndarray
        Spot prices (s)
    strikes : np.ndarray
        Strike prices (k)
    times : np.ndarray
        Time to maturity in years (t)
    rates : np.ndarray
        Risk-free rates (r)
    sigmas : np.ndarray
        Volatilities (sigma)

    Returns
    -------
    np.ndarray
        Call option prices

    Examples
    --------
    >>> import numpy as np
    >>> from quantforge.numpy_compat import call_price_numpy
    >>>
    >>> spots = np.array([100.0, 105.0, 110.0])
    >>> strikes = np.array([100.0, 100.0, 100.0])
    >>> times = np.array([1.0, 1.0, 1.0])
    >>> rates = np.array([0.05, 0.05, 0.05])
    >>> sigmas = np.array([0.2, 0.2, 0.2])
    >>>
    >>> prices = call_price_numpy(spots, strikes, times, rates, sigmas)
    """
    # NumPy → Arrow
    spots_arrow = pa.array(spots)
    strikes_arrow = pa.array(strikes)
    times_arrow = pa.array(times)
    rates_arrow = pa.array(rates)
    sigmas_arrow = pa.array(sigmas)

    # Arrow API呼び出し
    result_arrow = arrow_api.call_price(spots_arrow, strikes_arrow, times_arrow, rates_arrow, sigmas_arrow)

    # Arrow → NumPy
    return result_arrow.to_numpy()


def put_price_numpy(
    spots: np.ndarray,
    strikes: np.ndarray,
    times: np.ndarray,
    rates: np.ndarray,
    sigmas: np.ndarray,
) -> np.ndarray:
    """
    Calculate Black-Scholes put option prices using NumPy arrays.

    This is a convenience wrapper around the Arrow API for NumPy users.
    For best performance, use the Arrow API directly.

    Parameters
    ----------
    spots : np.ndarray
        Spot prices (s)
    strikes : np.ndarray
        Strike prices (k)
    times : np.ndarray
        Time to maturity in years (t)
    rates : np.ndarray
        Risk-free rates (r)
    sigmas : np.ndarray
        Volatilities (sigma)

    Returns
    -------
    np.ndarray
        Put option prices
    """
    # NumPy → Arrow
    spots_arrow = pa.array(spots)
    strikes_arrow = pa.array(strikes)
    times_arrow = pa.array(times)
    rates_arrow = pa.array(rates)
    sigmas_arrow = pa.array(sigmas)

    # Arrow API呼び出し
    result_arrow = arrow_api.put_price(spots_arrow, strikes_arrow, times_arrow, rates_arrow, sigmas_arrow)

    # Arrow → NumPy
    return result_arrow.to_numpy()


def greeks_numpy(
    spots: np.ndarray,
    strikes: np.ndarray,
    times: np.ndarray,
    rates: np.ndarray,
    sigmas: np.ndarray,
    is_call: bool = True,
) -> dict:
    """
    Calculate all Greeks using NumPy arrays.

    This is a convenience wrapper around the Arrow API for NumPy users.
    For best performance, use the Arrow API directly.

    Parameters
    ----------
    spots : np.ndarray
        Spot prices (s)
    strikes : np.ndarray
        Strike prices (k)
    times : np.ndarray
        Time to maturity in years (t)
    rates : np.ndarray
        Risk-free rates (r)
    sigmas : np.ndarray
        Volatilities (sigma)
    is_call : bool, default=True
        True for call options, False for put options

    Returns
    -------
    dict
        Dictionary with keys 'delta', 'gamma', 'vega', 'theta', 'rho'
        Each value is a np.ndarray
    """
    # NumPy → Arrow
    spots_arrow = pa.array(spots)
    strikes_arrow = pa.array(strikes)
    times_arrow = pa.array(times)
    rates_arrow = pa.array(rates)
    sigmas_arrow = pa.array(sigmas)

    # Arrow API呼び出し
    greeks_arrow = arrow_api.greeks(spots_arrow, strikes_arrow, times_arrow, rates_arrow, sigmas_arrow, is_call)

    # Arrow → NumPy for each Greek
    return {key: value.to_numpy() for key, value in greeks_arrow.items()}


def implied_volatility_numpy(
    prices: np.ndarray,
    spots: np.ndarray,
    strikes: np.ndarray,
    times: np.ndarray,
    rates: np.ndarray,
    is_call: bool = True,
    initial_guess: np.ndarray | None = None,
) -> np.ndarray:
    """
    Calculate implied volatility using NumPy arrays.

    This is a convenience wrapper around the Arrow API for NumPy users.
    For best performance, use the Arrow API directly.

    Parameters
    ----------
    prices : np.ndarray
        Option prices
    spots : np.ndarray
        Spot prices (s)
    strikes : np.ndarray
        Strike prices (k)
    times : np.ndarray
        Time to maturity in years (t)
    rates : np.ndarray
        Risk-free rates (r)
    is_call : bool, default=True
        True for call options, False for put options
    initial_guess : np.ndarray, optional
        Initial guess for volatility

    Returns
    -------
    np.ndarray
        Implied volatilities
    """
    # NumPy → Arrow
    prices_arrow = pa.array(prices)
    spots_arrow = pa.array(spots)
    strikes_arrow = pa.array(strikes)
    times_arrow = pa.array(times)
    rates_arrow = pa.array(rates)

    initial_guess_arrow = None
    if initial_guess is not None:
        initial_guess_arrow = pa.array(initial_guess)

    # Arrow API呼び出し
    result_arrow = arrow_api.implied_volatility(
        prices_arrow, spots_arrow, strikes_arrow, times_arrow, rates_arrow, is_call, initial_guess_arrow
    )

    # Arrow → NumPy
    return result_arrow.to_numpy()


# Utility functions


def to_numpy(arrow_array: pa.Array) -> np.ndarray:
    """
    Convert Arrow array to NumPy array.

    Parameters
    ----------
    arrow_array : pyarrow.Array
        Arrow array to convert

    Returns
    -------
    np.ndarray
        NumPy array
    """
    return arrow_array.to_numpy()


def from_numpy(numpy_array: np.ndarray) -> pa.Array:
    """
    Convert NumPy array to Arrow array.

    Parameters
    ----------
    numpy_array : np.ndarray
        NumPy array to convert

    Returns
    -------
    pyarrow.Array
        Arrow array
    """
    return pa.array(numpy_array)


# Legacy API aliases (for backward compatibility during migration)

# These aliases allow existing code using the old API to continue working
# They will be deprecated in a future version


def black_scholes_call(spots, strikes, times, rates, sigmas):
    """Legacy alias for call_price_numpy. Deprecated - use call_price_numpy instead."""
    import warnings

    warnings.warn("black_scholes_call is deprecated. Use call_price_numpy instead.", DeprecationWarning, stacklevel=2)
    return call_price_numpy(spots, strikes, times, rates, sigmas)


def black_scholes_put(spots, strikes, times, rates, sigmas):
    """Legacy alias for put_price_numpy. Deprecated - use put_price_numpy instead."""
    import warnings

    warnings.warn("black_scholes_put is deprecated. Use put_price_numpy instead.", DeprecationWarning, stacklevel=2)
    return put_price_numpy(spots, strikes, times, rates, sigmas)


# Module initialization
__all__ = [
    "call_price_numpy",
    "put_price_numpy",
    "greeks_numpy",
    "implied_volatility_numpy",
    "to_numpy",
    "from_numpy",
    # Legacy aliases (will be removed in future version)
    "black_scholes_call",
    "black_scholes_put",
]
