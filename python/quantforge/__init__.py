"""
QuantForge: High-performance option pricing library
"""

# Import the native module - explicit imports to avoid star import issues
from .quantforge import __version__, american, black76, black_scholes, merton

# Import instrumented module if available (for profiling)
try:
    from .quantforge import instrumented
    __all__ = ["__version__", "black_scholes", "black76", "merton", "american", "instrumented"]
except ImportError:
    # instrumented module not available in regular builds
    __all__ = ["__version__", "black_scholes", "black76", "merton", "american"]
