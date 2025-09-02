"""
Apache Arrow Native API for QuantForge.

This module provides Arrow-first API for option pricing calculations.
Internally uses optimized Arrow arrays for zero-copy operations where possible.
"""

import numpy as np
import pyarrow as pa

from . import black_scholes  # 既存のNumPyベースのバインディング
from .arrow_ffi import (
    arrays_to_numpy_fallback,
    numpy_to_arrow,
    prepare_arrow_arrays,
)


def call_price(
    spots: pa.Array,
    strikes: pa.Array,
    times: pa.Array,
    rates: pa.Array,
    sigmas: pa.Array,
) -> pa.Array:
    """
    Calculate Black-Scholes call option prices using Arrow arrays.

    Parameters
    ----------
    spots : pyarrow.Array
        Spot prices (s)
    strikes : pyarrow.Array
        Strike prices (k)
    times : pyarrow.Array
        Time to maturity in years (t)
    rates : pyarrow.Array
        Risk-free rates (r)
    sigmas : pyarrow.Array
        Volatilities (sigma)

    Returns
    -------
    pyarrow.Array
        Call option prices

    Examples
    --------
    >>> import pyarrow as pa
    >>> import quantforge.arrow_api as qf
    >>>
    >>> spots = pa.array([100.0, 105.0, 110.0])
    >>> strikes = pa.array([100.0, 100.0, 100.0])
    >>> times = pa.array([1.0, 1.0, 1.0])
    >>> rates = pa.array([0.05, 0.05, 0.05])
    >>> sigmas = pa.array([0.2, 0.2, 0.2])
    >>>
    >>> prices = qf.call_price(spots, strikes, times, rates, sigmas)
    """
    # Prepare arrays for FFI
    spots, strikes, times, rates, sigmas = prepare_arrow_arrays(spots, strikes, times, rates, sigmas)

    # 長さの検証
    _validate_array_lengths(spots, strikes, times, rates, sigmas)

    # Check if we can use true FFI (future implementation)
    # For now, use optimized fallback
    spots_np, strikes_np, times_np, rates_np, sigmas_np = arrays_to_numpy_fallback(spots, strikes, times, rates, sigmas)

    # 既存のバッチ処理関数を使用
    result_np = black_scholes.call_price_batch(spots_np, strikes_np, times_np, rates_np, sigmas_np)

    # Convert back to Arrow (zero-copy when possible)
    return numpy_to_arrow(result_np)


def put_price(
    spots: pa.Array,
    strikes: pa.Array,
    times: pa.Array,
    rates: pa.Array,
    sigmas: pa.Array,
) -> pa.Array:
    """
    Calculate Black-Scholes put option prices using Arrow arrays.

    Parameters
    ----------
    spots : pyarrow.Array
        Spot prices (s)
    strikes : pyarrow.Array
        Strike prices (k)
    times : pyarrow.Array
        Time to maturity in years (t)
    rates : pyarrow.Array
        Risk-free rates (r)
    sigmas : pyarrow.Array
        Volatilities (sigma)

    Returns
    -------
    pyarrow.Array
        Put option prices
    """
    # Prepare arrays for FFI
    spots, strikes, times, rates, sigmas = prepare_arrow_arrays(spots, strikes, times, rates, sigmas)

    # 長さの検証
    _validate_array_lengths(spots, strikes, times, rates, sigmas)

    # Check if we can use true FFI (future implementation)
    # For now, use optimized fallback
    spots_np, strikes_np, times_np, rates_np, sigmas_np = arrays_to_numpy_fallback(spots, strikes, times, rates, sigmas)

    # 既存のバッチ処理関数を使用
    result_np = black_scholes.put_price_batch(spots_np, strikes_np, times_np, rates_np, sigmas_np)

    # Convert back to Arrow (zero-copy when possible)
    return numpy_to_arrow(result_np)


def greeks(
    spots: pa.Array,
    strikes: pa.Array,
    times: pa.Array,
    rates: pa.Array,
    sigmas: pa.Array,
    is_call: bool = True,
) -> dict:
    """
    Calculate all Greeks using Arrow arrays.

    Parameters
    ----------
    spots : pyarrow.Array
        Spot prices (s)
    strikes : pyarrow.Array
        Strike prices (k)
    times : pyarrow.Array
        Time to maturity in years (t)
    rates : pyarrow.Array
        Risk-free rates (r)
    sigmas : pyarrow.Array
        Volatilities (sigma)
    is_call : bool, default=True
        True for call options, False for put options

    Returns
    -------
    dict
        Dictionary with keys 'delta', 'gamma', 'vega', 'theta', 'rho'
        Each value is a pyarrow.Array
    """
    # Prepare arrays for FFI
    spots, strikes, times, rates, sigmas = prepare_arrow_arrays(spots, strikes, times, rates, sigmas)

    # 長さの検証
    _validate_array_lengths(spots, strikes, times, rates, sigmas)

    # Check if we can use true FFI (future implementation)
    # For now, use optimized fallback
    spots_np, strikes_np, times_np, rates_np, sigmas_np = arrays_to_numpy_fallback(spots, strikes, times, rates, sigmas)

    # 既存のバッチ処理関数を使用
    greeks_dict = black_scholes.greeks_batch(spots_np, strikes_np, times_np, rates_np, sigmas_np, is_call)

    # Convert back to Arrow (zero-copy when possible)
    return {key: numpy_to_arrow(value) for key, value in greeks_dict.items()}


def implied_volatility(
    prices: pa.Array,
    spots: pa.Array,
    strikes: pa.Array,
    times: pa.Array,
    rates: pa.Array,
    is_call: bool = True,
    initial_guess: pa.Array | None = None,
) -> pa.Array:
    """
    Calculate implied volatility using Arrow arrays.

    Parameters
    ----------
    prices : pyarrow.Array
        Option prices
    spots : pyarrow.Array
        Spot prices (s)
    strikes : pyarrow.Array
        Strike prices (k)
    times : pyarrow.Array
        Time to maturity in years (t)
    rates : pyarrow.Array
        Risk-free rates (r)
    is_call : bool, default=True
        True for call options, False for put options
    initial_guess : pyarrow.Array, optional
        Initial guess for volatility

    Returns
    -------
    pyarrow.Array
        Implied volatilities
    """
    # Prepare arrays for FFI
    prices, spots, strikes, times, rates = prepare_arrow_arrays(prices, spots, strikes, times, rates)

    # 長さの検証
    _validate_array_lengths(prices, spots, strikes, times, rates)

    # Check if we can use true FFI (future implementation)
    # For now, use optimized fallback
    prices_np, spots_np, strikes_np, times_np, rates_np = arrays_to_numpy_fallback(prices, spots, strikes, times, rates)

    # Initial guessの処理
    if initial_guess is not None:
        initial_guess = _ensure_float64_array(initial_guess)
        initial_guess_np = initial_guess.to_numpy()
    else:
        initial_guess_np = None

    # is_callをarrayに変換（implied_volatility_batchの要件）
    is_calls_np = np.full(len(prices), is_call)

    # 既存のバッチ処理関数を使用
    result_np = black_scholes.implied_volatility_batch(prices_np, spots_np, strikes_np, times_np, rates_np, is_calls_np)

    # Convert back to Arrow (zero-copy when possible)
    return numpy_to_arrow(result_np)


# ユーティリティ関数


def _ensure_float64_array(arr: pa.Array | list | np.ndarray) -> pa.Array:
    """Ensure input is a Float64 Arrow array."""
    if not isinstance(arr, pa.Array):
        arr = pa.array(arr)

    if arr.type != pa.float64():
        arr = arr.cast(pa.float64())

    return arr


def _validate_array_lengths(*arrays):
    """Validate all arrays have the same length."""
    if not arrays:
        return

    first_len = len(arrays[0])
    for i, arr in enumerate(arrays[1:], 1):
        if len(arr) != first_len:
            raise ValueError(f"Array length mismatch: array 0 has length {first_len}, array {i} has length {len(arr)}")


# Broadcasting サポート


def broadcast_arrays(*arrays):
    """
    Broadcast arrays to compatible shapes.

    Supports scalar (length 1) broadcasting to match the maximum length.

    Parameters
    ----------
    *arrays : pyarrow.Array
        Arrays to broadcast

    Returns
    -------
    list[pyarrow.Array]
        Broadcasted arrays
    """
    arrays = [_ensure_float64_array(arr) for arr in arrays]

    # Find the maximum non-scalar length
    max_len = 1
    for arr in arrays:
        if len(arr) > 1:
            if max_len > 1 and len(arr) != max_len:
                raise ValueError(f"Cannot broadcast arrays with incompatible lengths: {[len(a) for a in arrays]}")
            max_len = max(max_len, len(arr))

    # Broadcast each array
    result = []
    for arr in arrays:
        if len(arr) == 1 and max_len > 1:
            # Scalar broadcast
            value = arr[0].as_py()
            result.append(pa.array([value] * max_len))
        else:
            result.append(arr)

    return result


# Conversion utilities


def from_numpy(np_array: np.ndarray) -> pa.Array:
    """Convert NumPy array to Arrow array."""
    return pa.array(np_array)


def to_numpy(arrow_array: pa.Array) -> np.ndarray:
    """Convert Arrow array to NumPy array."""
    return arrow_array.to_numpy()


# Performance utilities


def compute_parallel_threshold() -> int:
    """
    Get the parallel computation threshold.

    Returns the number of elements above which parallel processing is used.
    """
    # This could be made configurable or determined dynamically
    return 10_000


# Module initialization
__all__ = [
    "call_price",
    "put_price",
    "greeks",
    "implied_volatility",
    "broadcast_arrays",
    "from_numpy",
    "to_numpy",
    "compute_parallel_threshold",
]
