"""Type stubs for quantforge extension module"""

import numpy as np
from numpy.typing import ArrayLike as NpArrayLike
from numpy.typing import NDArray

# Type aliases for better readability
FloatLike = float | int
ArrayOrFloat = FloatLike | list[float] | NDArray[np.float64] | NpArrayLike

class models:
    """Options pricing models module"""

    @staticmethod
    def call_price(s: float, k: float, t: float, r: float, sigma: float) -> float:
        """Calculate Black-Scholes call option price"""
        ...

    @staticmethod
    def put_price(s: float, k: float, t: float, r: float, sigma: float) -> float:
        """Calculate Black-Scholes put option price"""
        ...

    @staticmethod
    def call_price_batch(
        spots: ArrayOrFloat, strikes: ArrayOrFloat, times: ArrayOrFloat, rates: ArrayOrFloat, sigmas: ArrayOrFloat
    ) -> NDArray[np.float64]:
        """Calculate call prices for multiple parameters with broadcasting"""
        ...

    @staticmethod
    def put_price_batch(
        spots: ArrayOrFloat, strikes: ArrayOrFloat, times: ArrayOrFloat, rates: ArrayOrFloat, sigmas: ArrayOrFloat
    ) -> NDArray[np.float64]:
        """Calculate put prices for multiple parameters with broadcasting"""
        ...

    @staticmethod
    def implied_volatility(price: float, s: float, k: float, t: float, r: float, is_call: bool = True) -> float:
        """Calculate implied volatility from Black-Scholes option price"""
        ...

    @staticmethod
    def implied_volatility_batch(
        prices: ArrayOrFloat,
        spots: ArrayOrFloat,
        strikes: ArrayOrFloat,
        times: ArrayOrFloat,
        rates: ArrayOrFloat,
        is_calls: ArrayOrFloat,
    ) -> NDArray[np.float64]:
        """Calculate implied volatilities for multiple parameters with broadcasting"""
        ...

    @staticmethod
    def greeks(s: float, k: float, t: float, r: float, sigma: float, is_call: bool = True) -> PyGreeks:
        """Calculate all Greeks for Black-Scholes option"""
        ...

    @staticmethod
    def greeks_batch(
        spots: ArrayOrFloat,
        strikes: ArrayOrFloat,
        times: ArrayOrFloat,
        rates: ArrayOrFloat,
        sigmas: ArrayOrFloat,
        is_calls: ArrayOrFloat,
    ) -> dict[str, NDArray[np.float64]]:
        """Calculate Greeks for multiple parameters with broadcasting"""
        ...

    class black76:
        """Black76 futures options model"""

        @staticmethod
        def call_price(f: float, k: float, t: float, r: float, sigma: float) -> float:
            """Calculate Black76 call option price"""
            ...

        @staticmethod
        def put_price(f: float, k: float, t: float, r: float, sigma: float) -> float:
            """Calculate Black76 put option price"""
            ...

        @staticmethod
        def call_price_batch(
            fs: ArrayOrFloat, ks: ArrayOrFloat, ts: ArrayOrFloat, rs: ArrayOrFloat, sigmas: ArrayOrFloat
        ) -> NDArray[np.float64]:
            """Calculate call prices with broadcasting support"""
            ...

        @staticmethod
        def put_price_batch(
            fs: ArrayOrFloat, ks: ArrayOrFloat, ts: ArrayOrFloat, rs: ArrayOrFloat, sigmas: ArrayOrFloat
        ) -> NDArray[np.float64]:
            """Calculate put prices with broadcasting support"""
            ...

        @staticmethod
        def greeks(f: float, k: float, t: float, r: float, sigma: float, is_call: bool = True) -> PyGreeks:
            """Calculate all Greeks for Black76 option"""
            ...

        @staticmethod
        def implied_volatility(price: float, f: float, k: float, t: float, r: float, is_call: bool = True) -> float:
            """Calculate implied volatility from Black76 option price"""
            ...

        @staticmethod
        def implied_volatility_batch(
            prices: ArrayOrFloat,
            fs: ArrayOrFloat,
            ks: ArrayOrFloat,
            ts: ArrayOrFloat,
            rs: ArrayOrFloat,
            is_calls: ArrayOrFloat,
        ) -> NDArray[np.float64]:
            """Calculate implied volatility for multiple option prices"""
            ...

        @staticmethod
        def greeks_batch(
            fs: ArrayOrFloat,
            ks: ArrayOrFloat,
            ts: ArrayOrFloat,
            rs: ArrayOrFloat,
            sigmas: ArrayOrFloat,
            is_calls: ArrayOrFloat,
        ) -> dict[str, NDArray[np.float64]]:
            """Calculate Greeks with broadcasting support"""
            ...

    class merton:
        """Merton model with dividend yield"""

        @staticmethod
        def call_price(s: float, k: float, t: float, r: float, q: float, sigma: float) -> float:
            """Calculate Merton model call option price"""
            ...

        @staticmethod
        def put_price(s: float, k: float, t: float, r: float, q: float, sigma: float) -> float:
            """Calculate Merton model put option price"""
            ...

        @staticmethod
        def call_price_batch(
            spots: ArrayOrFloat,
            strikes: ArrayOrFloat,
            times: ArrayOrFloat,
            rates: ArrayOrFloat,
            qs: ArrayOrFloat,
            sigmas: ArrayOrFloat,
        ) -> NDArray[np.float64]:
            """Calculate call prices with broadcasting support"""
            ...

        @staticmethod
        def put_price_batch(
            spots: ArrayOrFloat,
            strikes: ArrayOrFloat,
            times: ArrayOrFloat,
            rates: ArrayOrFloat,
            qs: ArrayOrFloat,
            sigmas: ArrayOrFloat,
        ) -> NDArray[np.float64]:
            """Calculate put prices with broadcasting support"""
            ...

        @staticmethod
        def greeks(
            s: float, k: float, t: float, r: float, q: float, sigma: float, is_call: bool = True
        ) -> PyMertonGreeks:
            """Calculate all Greeks for Merton model option"""
            ...

        @staticmethod
        def implied_volatility(
            price: float, s: float, k: float, t: float, r: float, q: float, is_call: bool = True
        ) -> float:
            """Calculate implied volatility from Merton model option price"""
            ...

        @staticmethod
        def implied_volatility_batch(
            prices: ArrayOrFloat,
            spots: ArrayOrFloat,
            strikes: ArrayOrFloat,
            times: ArrayOrFloat,
            rates: ArrayOrFloat,
            qs: ArrayOrFloat,
            is_calls: ArrayOrFloat,
        ) -> NDArray[np.float64]:
            """Calculate implied volatility for multiple option prices"""
            ...

        @staticmethod
        def greeks_batch(
            spots: ArrayOrFloat,
            strikes: ArrayOrFloat,
            times: ArrayOrFloat,
            rates: ArrayOrFloat,
            qs: ArrayOrFloat,
            sigmas: ArrayOrFloat,
            is_calls: ArrayOrFloat,
        ) -> dict[str, NDArray[np.float64]]:
            """Calculate Greeks with broadcasting support"""
            ...

    class american:
        """American options model using Bjerksund-Stensland 2002"""

        @staticmethod
        def call_price(s: float, k: float, t: float, r: float, q: float, sigma: float) -> float:
            """Calculate American call option price"""
            ...

        @staticmethod
        def put_price(s: float, k: float, t: float, r: float, q: float, sigma: float) -> float:
            """Calculate American put option price"""
            ...

        @staticmethod
        def call_price_batch(
            spots: ArrayOrFloat,
            strikes: ArrayOrFloat,
            times: ArrayOrFloat,
            rates: ArrayOrFloat,
            qs: ArrayOrFloat,
            sigmas: ArrayOrFloat,
        ) -> NDArray[np.float64]:
            """Calculate call prices for multiple spots"""
            ...

        @staticmethod
        def put_price_batch(
            spots: ArrayOrFloat,
            strikes: ArrayOrFloat,
            times: ArrayOrFloat,
            rates: ArrayOrFloat,
            qs: ArrayOrFloat,
            sigmas: ArrayOrFloat,
        ) -> NDArray[np.float64]:
            """Calculate put prices for multiple spots"""
            ...

        @staticmethod
        def greeks(s: float, k: float, t: float, r: float, q: float, sigma: float, is_call: bool = True) -> PyGreeks:
            """Calculate all Greeks for American option"""
            ...

        @staticmethod
        def implied_volatility(
            price: float,
            s: float,
            k: float,
            t: float,
            r: float,
            q: float,
            is_call: bool = True,
            initial_guess: float | None = None,
        ) -> float:
            """Calculate implied volatility from American option price"""
            ...

        @staticmethod
        def implied_volatility_batch(
            prices: ArrayOrFloat,
            spots: ArrayOrFloat,
            strikes: ArrayOrFloat,
            times: ArrayOrFloat,
            rates: ArrayOrFloat,
            qs: ArrayOrFloat,
            is_calls: ArrayOrFloat,
        ) -> NDArray[np.float64]:
            """Calculate implied volatility for multiple option prices"""
            ...

        @staticmethod
        def greeks_batch(
            spots: ArrayOrFloat,
            strikes: ArrayOrFloat,
            times: ArrayOrFloat,
            rates: ArrayOrFloat,
            qs: ArrayOrFloat,
            sigmas: ArrayOrFloat,
            is_calls: ArrayOrFloat,
        ) -> dict[str, NDArray[np.float64]]:
            """Calculate Greeks for multiple spot prices"""
            ...

        @staticmethod
        def exercise_boundary(
            s: float, k: float, t: float, r: float, q: float, sigma: float, is_call: bool = True
        ) -> float:
            """Calculate early exercise boundary for American option"""
            ...

        @staticmethod
        def exercise_boundary_batch(
            spots: ArrayOrFloat,
            strikes: ArrayOrFloat,
            times: ArrayOrFloat,
            rates: ArrayOrFloat,
            qs: ArrayOrFloat,
            sigmas: ArrayOrFloat,
            is_calls: ArrayOrFloat,
        ) -> NDArray[np.float64]:
            """Calculate early exercise boundaries for multiple spot prices"""
            ...

class PyGreeks:
    """Black-Scholes Greeks structure"""

    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float

class PyMertonGreeks:
    """Merton model Greeks structure with dividend_rho"""

    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float
    dividend_rho: float

# Module version
__version__: str = "0.1.0"
