"""
QuantForge: High-performance option pricing library

Type stubs for the main module re-exports.
"""

from .quantforge import (
    __version__ as __version__,
    black76 as black76,
    black_scholes as black_scholes,
    merton as merton,
    american as american,
)

__all__ = ["__version__", "black_scholes", "black76", "merton", "american"]
