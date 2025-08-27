"""Merton model for options on dividend-paying assets.

This module provides the Python interface to the Rust-implemented
Merton model for pricing options on assets with continuous dividend yields.
"""

from quantforge.quantforge import models  # type: ignore[import-not-found]

# Re-export all functions from the Rust module
call_price = models.merton.call_price
put_price = models.merton.put_price
call_price_batch = models.merton.call_price_batch
put_price_batch = models.merton.put_price_batch
greeks = models.merton.greeks
greeks_batch = models.merton.greeks_batch
implied_volatility = models.merton.implied_volatility
implied_volatility_batch = models.merton.implied_volatility_batch

# These don't exist in the Rust implementation yet
call_price_batch_q = models.merton.call_price_batch
put_price_batch_q = models.merton.put_price_batch

__all__ = [
    "call_price",
    "put_price",
    "call_price_batch",
    "put_price_batch",
    "call_price_batch_q",
    "put_price_batch_q",
    "greeks",
    "greeks_batch",
    "implied_volatility",
    "implied_volatility_batch",
]
