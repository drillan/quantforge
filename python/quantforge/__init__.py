"""
QuantForge: High-performance option pricing library
"""

# Import the native module - explicit imports to avoid star import issues
from .quantforge import __version__, american, black76, black_scholes, merton

# The native module already contains the submodules
# So we just need to re-export them for proper namespace

# Define public API
__all__ = ["__version__", "black_scholes", "black76", "merton", "american"]
