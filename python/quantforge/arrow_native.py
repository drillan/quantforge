"""Arrow Native API with Broadcasting support.

This module provides direct access to Arrow-native functions with broadcasting support
for high-performance option pricing calculations using Apache Arrow arrays.

Functions:
    arrow_call_price: Black-Scholes call price with broadcasting
    arrow_put_price: Black-Scholes put price with broadcasting
    arrow_greeks: Black-Scholes Greeks calculation
    arrow76_call_price: Black76 call price with broadcasting
    arrow76_put_price: Black76 put price with broadcasting
    arrow76_greeks: Black76 Greeks calculation

All functions support broadcasting where scalar values (length 1 arrays) are
automatically expanded to match the length of other arrays.

Example:
    >>> import pyarrow as pa
    >>> from quantforge.arrow_native import arrow_call_price
    >>>
    >>> # Multiple spots, single strike (broadcasting)
    >>> spots = pa.array([100.0, 105.0, 110.0])
    >>> strikes = pa.array([100.0])  # Will broadcast to all spots
    >>> times = pa.array([1.0])
    >>> rates = pa.array([0.05])
    >>> sigmas = pa.array([0.2])
    >>>
    >>> prices = arrow_call_price(spots, strikes, times, rates, sigmas)
"""

# Import all arrow_native functions from the compiled module
from .quantforge import (
    arrow76_call_price,
    arrow76_greeks,
    arrow76_put_price,
    arrow_call_price,
    arrow_greeks,
    arrow_put_price,
)

__all__ = [
    "arrow_call_price",
    "arrow_put_price",
    "arrow_greeks",
    "arrow76_call_price",
    "arrow76_put_price",
    "arrow76_greeks",
]
