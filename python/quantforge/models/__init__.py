"""QuantForge models module - option pricing models."""

# Import the Rust models submodule
from ..quantforge import models as _rust_models  # type: ignore[import-not-found]
from .base import BaseOptionModel


# Create a namespace for black_scholes
class BlackScholesModule(BaseOptionModel):
    """Black-Scholes option pricing model."""

    def __init__(self) -> None:
        """Initialize Black-Scholes model."""
        super().__init__(
            rust_module=_rust_models, model_name="black_scholes", has_dividends=False, has_exercise_boundary=False
        )


# Create a namespace for black76
class Black76Module(BaseOptionModel):
    """Black76 option pricing model for commodity and futures options."""

    def __init__(self) -> None:
        """Initialize Black76 model."""
        super().__init__(
            rust_module=_rust_models.black76, model_name="black76", has_dividends=False, has_exercise_boundary=False
        )


# Create a namespace for merton
class MertonModule(BaseOptionModel):
    """Merton model for options on dividend-paying assets."""

    def __init__(self) -> None:
        """Initialize Merton model."""
        super().__init__(
            rust_module=_rust_models.merton, model_name="merton", has_dividends=True, has_exercise_boundary=False
        )


# Create a namespace for american
class AmericanModule(BaseOptionModel):
    """American option pricing model with early exercise."""

    def __init__(self) -> None:
        """Initialize American model."""
        super().__init__(
            rust_module=_rust_models.american, model_name="american", has_dividends=True, has_exercise_boundary=True
        )


# Create module instances
black_scholes = BlackScholesModule()
black76 = Black76Module()
merton = MertonModule()
american = AmericanModule()

__all__ = ["black_scholes", "black76", "merton", "american"]
