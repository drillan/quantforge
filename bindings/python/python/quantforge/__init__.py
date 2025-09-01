"""
QuantForge: High-performance option pricing library
"""

# Import the native module
from .quantforge import __version__

# Import Python wrappers with broadcasting support
from . import black_scholes

# Define public API
__all__ = ["__version__", "black_scholes"]
