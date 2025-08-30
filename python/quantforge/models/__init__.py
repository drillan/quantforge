"""
QuantForge models module.

This module provides access to various option pricing models:
- black_scholes: Black-Scholes model for European options (default)
- black76: Black-76 model for futures options
- merton: Merton model with continuous dividends
- american: American options using Bjerksund-Stensland 2002 approximation
"""

# Import models from the parent package (which is imported from Rust)
from .. import models as _models

# Re-export models and their functions
# Note: black_scholes is the default model, so its functions are at the top level
black_scholes = _models  # black_scholes uses the default models functions
black76 = _models.black76
merton = _models.merton
american = _models.american

__all__ = ["black_scholes", "black76", "merton", "american"]
