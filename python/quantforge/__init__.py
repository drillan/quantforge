"""
QuantForge: High-performance option pricing library
"""

# Import the native module for version and other models
from .quantforge import __version__, american, black76, merton

# Import the Python wrapper for black_scholes (provides broadcasting support)
from . import black_scholes

# Import instrumented module if available (for profiling)
try:
    from .quantforge import instrumented
    __all__ = ["__version__", "black_scholes", "black76", "merton", "american", "instrumented"]
except ImportError:
    # instrumented module not available in regular builds
    __all__ = ["__version__", "black_scholes", "black76", "merton", "american"]
