"""Baseline implementations for benchmarking."""

from benchmarks.baseline.iv_baseline import (
    american_iv_scipy,
    black_scholes_price_scipy,
    implied_volatility_scipy,
)
from benchmarks.baseline.iv_vectorized import (
    black_scholes_vectorized,
    implied_volatility_newton_vectorized,
    vega_vectorized,
)
from benchmarks.baseline.python_baseline import (
    black_scholes_numpy_batch,
    black_scholes_pure_python,
    black_scholes_scipy_single,
    norm_cdf_pure,
)

__all__ = [
    # Pure Python
    "black_scholes_pure_python",
    "black_scholes_numpy_batch",
    "black_scholes_scipy_single",
    "norm_cdf_pure",
    # SciPy
    "black_scholes_price_scipy",
    "implied_volatility_scipy",
    "american_iv_scipy",
    # Vectorized
    "black_scholes_vectorized",
    "vega_vectorized",
    "implied_volatility_newton_vectorized",
]
