"""
QuantForge: High-performance option pricing library
"""

# Import the native module
# Import Python wrappers with broadcasting support
from . import black_scholes
from .quantforge import __version__

# Define public API
__all__ = ["__version__", "black_scholes"]
