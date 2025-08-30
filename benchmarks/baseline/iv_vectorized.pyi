# Type stubs for iv_vectorized
import numpy as np
from numpy.typing import NDArray

def implied_volatility_vectorized(
    prices: NDArray[np.float64],
    spots: NDArray[np.float64],
    strikes: NDArray[np.float64],
    rates: NDArray[np.float64],
    times: NDArray[np.float64],
    is_calls: NDArray[np.bool_],
) -> NDArray[np.float64]: ...
def implied_volatility_newton_vectorized(
    prices: NDArray[np.float64],
    spots: NDArray[np.float64],
    strikes: NDArray[np.float64],
    times: NDArray[np.float64],
    rates: NDArray[np.float64],
    is_calls: NDArray[np.bool_],
) -> NDArray[np.float64]: ...
def black_scholes_vectorized(
    spots: NDArray[np.float64],
    strikes: NDArray[np.float64],
    times: NDArray[np.float64],
    rates: NDArray[np.float64],
    sigmas: NDArray[np.float64],
    is_calls: NDArray[np.bool_],
) -> NDArray[np.float64]: ...
def vega_vectorized(
    spots: NDArray[np.float64],
    strikes: NDArray[np.float64],
    times: NDArray[np.float64],
    rates: NDArray[np.float64],
    sigmas: NDArray[np.float64],
) -> NDArray[np.float64]: ...
