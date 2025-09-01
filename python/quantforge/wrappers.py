"""Wrapper functions for broadcasting support."""

from typing import Union

import numpy as np
from numpy.typing import NDArray

# Import native module
from . import quantforge

# Get native functions from the module
_native_call_batch = quantforge.black_scholes.call_price_batch
_native_put_batch = quantforge.black_scholes.put_price_batch
_native_greeks_batch = quantforge.black_scholes.greeks_batch

# Type alias for array-like inputs
ArrayLike = Union[float, int, list, NDArray]


def _ensure_array(x: ArrayLike) -> NDArray[np.float64]:
    """Convert input to numpy array with float64 dtype."""
    return np.atleast_1d(np.asarray(x, dtype=np.float64))


def call_price_batch(
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    sigmas: ArrayLike,
) -> NDArray[np.float64]:
    """
    Calculate Black-Scholes call option prices with broadcasting support.

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
    # Convert all inputs to numpy arrays
    spots = _ensure_array(spots)
    strikes = _ensure_array(strikes)
    times = _ensure_array(times)
    rates = _ensure_array(rates)
    sigmas = _ensure_array(sigmas)

    # Call native implementation
    return _native_call_batch(spots, strikes, times, rates, sigmas)


def put_price_batch(
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    sigmas: ArrayLike,
) -> NDArray[np.float64]:
    """
    Calculate Black-Scholes put option prices with broadcasting support.

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
    # Convert all inputs to numpy arrays
    spots = _ensure_array(spots)
    strikes = _ensure_array(strikes)
    times = _ensure_array(times)
    rates = _ensure_array(rates)
    sigmas = _ensure_array(sigmas)

    # Call native implementation
    return _native_put_batch(spots, strikes, times, rates, sigmas)


def greeks_batch(
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    sigmas: ArrayLike,
    is_call: bool = True,
) -> dict[str, NDArray[np.float64]]:
    """
    Calculate Black-Scholes Greeks with broadcasting support.

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
        True for call options, False for put options

    Returns
    -------
    dict
        Dictionary with NumPy arrays for: delta, gamma, vega, theta, rho
    """
    # Convert all inputs to numpy arrays
    spots = _ensure_array(spots)
    strikes = _ensure_array(strikes)
    times = _ensure_array(times)
    rates = _ensure_array(rates)
    sigmas = _ensure_array(sigmas)

    # Call native implementation
    return _native_greeks_batch(spots, strikes, times, rates, sigmas, is_call)
