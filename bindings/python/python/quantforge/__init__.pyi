"""
QuantForge: High-performance option pricing library

Type stubs for the main module re-exports.
"""

from .quantforge import (
    __version__ as __version__,
)
from .quantforge import (
    american as american,
)
from .quantforge import (
    black76 as black76,
)
from .quantforge import (
    black_scholes as black_scholes,
)
from .quantforge import (
    merton as merton,
)

__all__ = ["__version__", "black_scholes", "black76", "merton", "american"]
