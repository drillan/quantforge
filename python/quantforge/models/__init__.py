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
        self.greeks_batch = _rust_models.greeks_batch
        self.implied_volatility = _rust_models.implied_volatility
        self.implied_volatility_batch = _rust_models.implied_volatility_batch


# Create a namespace for black76
class Black76Module:
    """Black76 option pricing model for commodity and futures options."""

    def __init__(self) -> None:
        # Bind functions from the Rust module
        self.call_price = _rust_models.black76.call_price
        self.put_price = _rust_models.black76.put_price
        self.call_price_batch = _rust_models.black76.call_price_batch
        self.put_price_batch = _rust_models.black76.put_price_batch
        self.greeks = _rust_models.black76.greeks
        self.greeks_batch = _rust_models.black76.greeks_batch
        self.implied_volatility = _rust_models.black76.implied_volatility
        self.implied_volatility_batch = _rust_models.black76.implied_volatility_batch


# Create a namespace for merton
class MertonModule:
    """Merton model for options on dividend-paying assets."""

    def __init__(self) -> None:
        # Bind functions from the Rust module
        self.call_price = _rust_models.merton.call_price
        self.put_price = _rust_models.merton.put_price
        self.call_price_batch = _rust_models.merton.call_price_batch
        self.put_price_batch = _rust_models.merton.put_price_batch
        self.call_price_batch_q = _rust_models.merton.call_price_batch_q
        self.put_price_batch_q = _rust_models.merton.put_price_batch_q
        self.greeks = _rust_models.merton.greeks
        self.greeks_batch = _rust_models.merton.greeks_batch
        self.implied_volatility = _rust_models.merton.implied_volatility
        self.implied_volatility_batch = _rust_models.merton.implied_volatility_batch


# Create a namespace for american
class AmericanModule:
    """American option pricing model with early exercise."""

    def __init__(self) -> None:
        # Bind functions from the Rust module
        self.call_price = _rust_models.american.call_price
        self.put_price = _rust_models.american.put_price
        self.call_price_batch = _rust_models.american.call_price_batch
        self.put_price_batch = _rust_models.american.put_price_batch
        self.greeks = _rust_models.american.greeks
        self.greeks_batch = _rust_models.american.greeks_batch
        self.implied_volatility = _rust_models.american.implied_volatility
        self.implied_volatility_batch = _rust_models.american.implied_volatility_batch
        self.exercise_boundary = _rust_models.american.exercise_boundary
        self.exercise_boundary_batch = _rust_models.american.exercise_boundary_batch


# Create module instances
black_scholes = BlackScholesModule()
black76 = Black76Module()
merton = MertonModule()
american = AmericanModule()

__all__ = ["black_scholes", "black76", "merton", "american"]
