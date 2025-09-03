"""Type stubs for quantforge"""

import numpy as np
from numpy.typing import ArrayLike, NDArray

# Type aliases
FloatOrArray = float | ArrayLike

class black_scholes:
    @staticmethod
    def call_price(s: float, k: float, t: float, r: float, sigma: float) -> float: ...
    @staticmethod
    def put_price(s: float, k: float, t: float, r: float, sigma: float) -> float: ...
    @staticmethod
    def call_price_batch(
        spots: FloatOrArray, strikes: FloatOrArray, times: FloatOrArray, rates: FloatOrArray, sigmas: FloatOrArray
    ) -> NDArray[np.float64]: ...
    @staticmethod
    def put_price_batch(
        spots: FloatOrArray, strikes: FloatOrArray, times: FloatOrArray, rates: FloatOrArray, sigmas: FloatOrArray
    ) -> NDArray[np.float64]: ...
    @staticmethod
    def greeks(s: float, k: float, t: float, r: float, sigma: float, is_call: bool = True) -> dict[str, float]: ...
    @staticmethod
    def greeks_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        sigmas: FloatOrArray,
        is_calls: FloatOrArray = True,
    ) -> dict[str, NDArray[np.float64]]: ...
    @staticmethod
    def implied_volatility(price: float, s: float, k: float, t: float, r: float, is_call: bool = True) -> float: ...
    @staticmethod
    def implied_volatility_batch(
        prices: FloatOrArray,
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        is_calls: FloatOrArray = True,
    ) -> NDArray[np.float64]: ...

class black76:
    @staticmethod
    def call_price(f: float, k: float, t: float, r: float, sigma: float) -> float: ...
    @staticmethod
    def put_price(f: float, k: float, t: float, r: float, sigma: float) -> float: ...
    @staticmethod
    def call_price_batch(
        forwards: FloatOrArray, strikes: FloatOrArray, times: FloatOrArray, rates: FloatOrArray, sigmas: FloatOrArray
    ) -> NDArray[np.float64]: ...
    @staticmethod
    def put_price_batch(
        forwards: FloatOrArray, strikes: FloatOrArray, times: FloatOrArray, rates: FloatOrArray, sigmas: FloatOrArray
    ) -> NDArray[np.float64]: ...
    @staticmethod
    def greeks(f: float, k: float, t: float, r: float, sigma: float, is_call: bool = True) -> dict[str, float]: ...
    @staticmethod
    def greeks_batch(
        forwards: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        sigmas: FloatOrArray,
        is_calls: FloatOrArray = True,
    ) -> dict[str, NDArray[np.float64]]: ...
    @staticmethod
    def implied_volatility(price: float, f: float, k: float, t: float, r: float, is_call: bool = True) -> float: ...
    @staticmethod
    def implied_volatility_batch(
        prices: FloatOrArray,
        forwards: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        is_calls: FloatOrArray = True,
    ) -> NDArray[np.float64]: ...

class merton:
    @staticmethod
    def call_price(s: float, k: float, t: float, r: float, q: float, sigma: float) -> float: ...
    @staticmethod
    def put_price(s: float, k: float, t: float, r: float, q: float, sigma: float) -> float: ...
    @staticmethod
    def call_price_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray,
    ) -> NDArray[np.float64]: ...
    @staticmethod
    def put_price_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray,
    ) -> NDArray[np.float64]: ...
    @staticmethod
    def greeks(
        s: float, k: float, t: float, r: float, q: float, sigma: float, is_call: bool = True
    ) -> dict[str, float]: ...
    @staticmethod
    def greeks_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray,
        is_calls: FloatOrArray = True,
    ) -> dict[str, NDArray[np.float64]]: ...
    @staticmethod
    def implied_volatility(
        price: float, s: float, k: float, t: float, r: float, q: float, is_call: bool = True
    ) -> float: ...
    @staticmethod
    def implied_volatility_batch(
        prices: FloatOrArray,
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        is_calls: FloatOrArray = True,
    ) -> NDArray[np.float64]: ...

class american:
    @staticmethod
    def call_price(s: float, k: float, t: float, r: float, q: float, sigma: float, n_steps: int = 100) -> float: ...
    @staticmethod
    def put_price(s: float, k: float, t: float, r: float, q: float, sigma: float, n_steps: int = 100) -> float: ...
    @staticmethod
    def call_price_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray,
        n_steps: int = 100,
    ) -> NDArray[np.float64]: ...
    @staticmethod
    def put_price_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray,
        n_steps: int = 100,
    ) -> NDArray[np.float64]: ...
    @staticmethod
    def greeks(
        s: float, k: float, t: float, r: float, q: float, sigma: float, is_call: bool = True, n_steps: int = 100
    ) -> dict[str, float]: ...
    @staticmethod
    def greeks_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray,
        is_calls: FloatOrArray = True,
        n_steps: int = 100,
    ) -> dict[str, NDArray[np.float64]]: ...
    @staticmethod
    def implied_volatility(
        price: float, s: float, k: float, t: float, r: float, q: float, is_call: bool = True, n_steps: int = 100
    ) -> float: ...
    @staticmethod
    def implied_volatility_batch(
        prices: FloatOrArray,
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        is_calls: FloatOrArray = True,
        n_steps: int = 100,
    ) -> NDArray[np.float64]: ...

__version__: str
__all__: list[str]
