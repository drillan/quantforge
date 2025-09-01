"""
QuantForge: High-performance option pricing library
"""

# Import the native module for version and other models
from .quantforge import __version__, american, black76, merton

# Import native black_scholes module directly
from .quantforge import black_scholes

# Import wrapper functions for broadcasting support
from .wrappers import (
    call_price_batch,
    put_price_batch,
    greeks_batch,
)

# Override black_scholes batch functions with wrappers
black_scholes.call_price_batch = call_price_batch
black_scholes.put_price_batch = put_price_batch
black_scholes.greeks_batch = greeks_batch

# Import instrumented module if available (for profiling)
try:
    from .quantforge import instrumented
    __all__ = ["__version__", "black_scholes", "black76", "merton", "american", "instrumented"]
except ImportError:
    # instrumented module not available in regular builds
    __all__ = ["__version__", "black_scholes", "black76", "merton", "american"]
