# Type stubs for iv_baseline
import numpy as np
from numpy.typing import NDArray

def black_scholes_price_scipy(s: float, k: float, t: float, r: float, sigma: float, is_call: bool = True) -> float: ...
def black76_price(f: float, k: float, t: float, r: float, sigma: float, is_call: bool = True) -> float: ...
def merton_price(s: float, k: float, t: float, r: float, q: float, sigma: float, is_call: bool = True) -> float: ...
def american_price_approx(
    s: float, k: float, t: float, r: float, q: float, sigma: float, is_call: bool = True
) -> float: ...
def vega_scipy(s: float, k: float, t: float, r: float, sigma: float) -> float: ...
def vega_merton(s: float, k: float, t: float, r: float, q: float, sigma: float) -> float: ...
def implied_volatility_scipy(price: float, s: float, k: float, t: float, r: float, is_call: bool = True) -> float: ...
def black76_iv_scipy(price: float, f: float, k: float, t: float, r: float, is_call: bool = True) -> float: ...
def merton_iv_scipy(price: float, s: float, k: float, t: float, r: float, q: float, is_call: bool = True) -> float: ...
def american_iv_scipy(
    price: float, s: float, k: float, t: float, r: float, q: float, is_call: bool = True
) -> float: ...
def implied_volatility_newton(
    price: float,
    s: float,
    k: float,
    t: float,
    r: float,
    is_call: bool = True,
    initial_guess: float | None = None,
    max_iterations: int = 50,
    tolerance: float = 1e-6,
) -> float: ...
def implied_volatility_batch_scipy(
    prices: NDArray[np.float64],
    s: NDArray[np.float64] | float,
    k: NDArray[np.float64] | float,
    t: NDArray[np.float64] | float,
    r: NDArray[np.float64] | float,
    is_calls: NDArray[np.bool_] | bool,
    method: str = "brentq",
) -> NDArray[np.float64]: ...
def implied_volatility_batch_newton(
    prices: NDArray[np.float64],
    s: NDArray[np.float64] | float,
    k: NDArray[np.float64] | float,
    t: NDArray[np.float64] | float,
    r: NDArray[np.float64] | float,
    is_calls: NDArray[np.bool_] | bool,
    initial_guess: float | None = None,
    max_iterations: int = 50,
    tolerance: float = 1e-6,
) -> NDArray[np.float64]: ...
