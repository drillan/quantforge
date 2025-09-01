"""
QuantForge: High-performance option pricing library
"""

# Import the native module for version and other models
# Import native black_scholes module directly
from .quantforge import __version__, american, black76, black_scholes, merton

# Import wrapper functions for broadcasting support
from .wrappers import (
    call_price_batch,
    greeks_batch,
    put_price_batch,
)

# Override black_scholes batch functions with wrappers
black_scholes.call_price_batch = call_price_batch
black_scholes.put_price_batch = put_price_batch
black_scholes.greeks_batch = greeks_batch

# Import Arrow API modules
from . import arrow_api, numpy_compat

# Import optional modules
try:
    from .quantforge import arrow_native
    has_arrow_native = True
except ImportError:
    has_arrow_native = False

try:
    from .quantforge import instrumented
    has_instrumented = True
except ImportError:
    has_instrumented = False

# Build __all__ list based on available modules
__all__ = ["__version__", "black_scholes", "black76", "merton", "american", "arrow_api", "numpy_compat"]
if has_arrow_native:
    __all__.append("arrow_native")
if has_instrumented:
    __all__.append("instrumented")
