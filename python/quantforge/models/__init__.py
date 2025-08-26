"""QuantForge models module - option pricing models."""

# Import the Rust models submodule
from ..quantforge import models as _rust_models  # type: ignore[import-not-found]


# Create a namespace for black_scholes
class BlackScholesModule:
    """Black-Scholes option pricing model."""

    def __init__(self) -> None:
        # Bind functions from the Rust module
        self.call_price = _rust_models.call_price
        self.put_price = _rust_models.put_price
        self.call_price_batch = _rust_models.call_price_batch
        self.put_price_batch = _rust_models.put_price_batch
        self.greeks = _rust_models.greeks
        self.implied_volatility = _rust_models.implied_volatility


# Create module instance
black_scholes = BlackScholesModule()

__all__ = ["black_scholes"]
