"""Type stubs for quantforge native module"""

from typing import Dict, Union, Optional
import numpy as np
from numpy.typing import ArrayLike, NDArray

# Type aliases
FloatOrArray = Union[float, ArrayLike]

# Black-Scholes module
class black_scholes:
    @staticmethod
    def call_price(s: float, k: float, t: float, r: float, sigma: float) -> float:
        """Calculate Black-Scholes call option price.
        
        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            sigma: Volatility
            
        Returns:
            Call option price
        """
        ...
    
    @staticmethod
    def put_price(s: float, k: float, t: float, r: float, sigma: float) -> float:
        """Calculate Black-Scholes put option price.
        
        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            sigma: Volatility
            
        Returns:
            Put option price
        """
        ...
    
    @staticmethod
    def call_price_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        sigmas: FloatOrArray
    ) -> NDArray[np.float64]:
        """Calculate batch of Black-Scholes call option prices.
        
        Args:
            spots: Spot prices
            strikes: Strike prices
            times: Times to maturity
            rates: Risk-free rates
            sigmas: Volatilities
            
        Returns:
            Array of call option prices
        """
        ...
    
    @staticmethod
    def put_price_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        sigmas: FloatOrArray
    ) -> NDArray[np.float64]:
        """Calculate batch of Black-Scholes put option prices.
        
        Args:
            spots: Spot prices
            strikes: Strike prices
            times: Times to maturity
            rates: Risk-free rates
            sigmas: Volatilities
            
        Returns:
            Array of put option prices
        """
        ...
    
    @staticmethod
    def greeks(
        s: float, k: float, t: float, r: float, sigma: float, 
        is_call: bool = True
    ) -> Dict[str, float]:
        """Calculate Greeks for Black-Scholes model.
        
        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            sigma: Volatility
            is_call: True for call option, False for put option (default: True)
            
        Returns:
            Dictionary with Greeks (delta, gamma, vega, theta, rho)
        """
        ...
    
    @staticmethod
    def greeks_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        sigmas: FloatOrArray,
        is_calls: Optional[FloatOrArray] = None
    ) -> Dict[str, NDArray[np.float64]]:
        """Calculate batch of Greeks for Black-Scholes model.
        
        Args:
            spots: Spot prices
            strikes: Strike prices
            times: Times to maturity
            rates: Risk-free rates
            sigmas: Volatilities
            is_calls: Boolean array for option types (default: all calls)
            
        Returns:
            Dictionary with arrays of Greeks
        """
        ...
    
    @staticmethod
    def implied_volatility(
        price: float, s: float, k: float, t: float, r: float, is_call: bool
    ) -> float:
        """Calculate implied volatility using Black-Scholes model.
        
        Args:
            price: Option price
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            is_call: True for call option, False for put option
            
        Returns:
            Implied volatility
        """
        ...
    
    @staticmethod
    def implied_volatility_batch(
        prices: FloatOrArray,
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        is_calls: FloatOrArray
    ) -> NDArray[np.float64]:
        """Calculate batch of implied volatilities.
        
        Args:
            prices: Option prices
            spots: Spot prices
            strikes: Strike prices
            times: Times to maturity
            rates: Risk-free rates
            is_calls: Boolean array for option types
            
        Returns:
            Array of implied volatilities
        """
        ...

# Black76 module
class black76:
    @staticmethod
    def call_price(f: float, k: float, t: float, r: float, sigma: float) -> float:
        """Calculate Black76 call option price.
        
        Args:
            f: Forward price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            sigma: Volatility
            
        Returns:
            Call option price
        """
        ...
    
    @staticmethod
    def put_price(f: float, k: float, t: float, r: float, sigma: float) -> float:
        """Calculate Black76 put option price.
        
        Args:
            f: Forward price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            sigma: Volatility
            
        Returns:
            Put option price
        """
        ...
    
    @staticmethod
    def call_price_batch(
        forwards: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        sigmas: FloatOrArray
    ) -> NDArray[np.float64]:
        """Calculate batch of Black76 call option prices.
        
        Args:
            forwards: Forward prices
            strikes: Strike prices
            times: Times to maturity
            rates: Risk-free rates
            sigmas: Volatilities
            
        Returns:
            Array of call option prices
        """
        ...
    
    @staticmethod
    def put_price_batch(
        forwards: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        sigmas: FloatOrArray
    ) -> NDArray[np.float64]:
        """Calculate batch of Black76 put option prices.
        
        Args:
            forwards: Forward prices
            strikes: Strike prices
            times: Times to maturity
            rates: Risk-free rates
            sigmas: Volatilities
            
        Returns:
            Array of put option prices
        """
        ...
    
    @staticmethod
    def greeks(
        f: float, k: float, t: float, r: float, sigma: float, 
        is_call: bool = True
    ) -> Dict[str, float]:
        """Calculate Greeks for Black76 model.
        
        Args:
            f: Forward price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            sigma: Volatility
            is_call: True for call option, False for put option (default: True)
            
        Returns:
            Dictionary with Greeks (delta, gamma, vega, theta, rho)
        """
        ...
    
    @staticmethod
    def greeks_batch(
        forwards: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        sigmas: FloatOrArray,
        is_calls: Optional[FloatOrArray] = None
    ) -> Dict[str, NDArray[np.float64]]:
        """Calculate batch of Greeks for Black76 model.
        
        Args:
            forwards: Forward prices
            strikes: Strike prices
            times: Times to maturity
            rates: Risk-free rates
            sigmas: Volatilities
            is_calls: Boolean array for option types (default: all calls)
            
        Returns:
            Dictionary with arrays of Greeks
        """
        ...
    
    @staticmethod
    def implied_volatility(
        price: float, f: float, k: float, t: float, r: float, is_call: bool
    ) -> float:
        """Calculate implied volatility using Black76 model.
        
        Args:
            price: Option price
            f: Forward price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            is_call: True for call option, False for put option
            
        Returns:
            Implied volatility
        """
        ...
    
    @staticmethod
    def implied_volatility_batch(
        prices: FloatOrArray,
        forwards: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        is_calls: FloatOrArray
    ) -> NDArray[np.float64]:
        """Calculate batch of implied volatilities.
        
        Args:
            prices: Option prices
            forwards: Forward prices
            strikes: Strike prices
            times: Times to maturity
            rates: Risk-free rates
            is_calls: Boolean array for option types
            
        Returns:
            Array of implied volatilities
        """
        ...

# Merton model
class merton:
    @staticmethod
    def call_price(s: float, k: float, t: float, r: float, q: float, sigma: float) -> float:
        """Calculate Merton call option price.
        
        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            q: Dividend yield
            sigma: Volatility
            
        Returns:
            Call option price
        """
        ...
    
    @staticmethod
    def put_price(s: float, k: float, t: float, r: float, q: float, sigma: float) -> float:
        """Calculate Merton put option price.
        
        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            q: Dividend yield
            sigma: Volatility
            
        Returns:
            Put option price
        """
        ...
    
    @staticmethod
    def call_price_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray
    ) -> NDArray[np.float64]:
        """Calculate batch of Merton call option prices.
        
        Args:
            spots: Spot prices
            strikes: Strike prices
            times: Times to maturity
            rates: Risk-free rates
            dividend_yields: Dividend yields
            sigmas: Volatilities
            
        Returns:
            Array of call option prices
        """
        ...
    
    @staticmethod
    def put_price_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray
    ) -> NDArray[np.float64]:
        """Calculate batch of Merton put option prices.
        
        Args:
            spots: Spot prices
            strikes: Strike prices
            times: Times to maturity
            rates: Risk-free rates
            dividend_yields: Dividend yields
            sigmas: Volatilities
            
        Returns:
            Array of put option prices
        """
        ...
    
    @staticmethod
    def greeks(
        s: float, k: float, t: float, r: float, q: float, sigma: float, 
        is_call: bool = True
    ) -> Dict[str, float]:
        """Calculate Greeks for Merton model.
        
        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            q: Dividend yield
            sigma: Volatility
            is_call: True for call option, False for put option (default: True)
            
        Returns:
            Dictionary with Greeks (delta, gamma, vega, theta, rho, dividend_rho)
        """
        ...
    
    @staticmethod
    def greeks_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray,
        is_calls: Optional[FloatOrArray] = None
    ) -> Dict[str, NDArray[np.float64]]:
        """Calculate batch of Greeks for Merton model.
        
        Args:
            spots: Spot prices
            strikes: Strike prices
            times: Times to maturity
            rates: Risk-free rates
            dividend_yields: Dividend yields
            sigmas: Volatilities
            is_calls: Boolean array for option types (default: all calls)
            
        Returns:
            Dictionary with arrays of Greeks
        """
        ...
    
    @staticmethod
    def implied_volatility(
        price: float, s: float, k: float, t: float, r: float, q: float, is_call: bool
    ) -> float:
        """Calculate implied volatility using Merton model.
        
        Args:
            price: Option price
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            q: Dividend yield
            is_call: True for call option, False for put option
            
        Returns:
            Implied volatility
        """
        ...
    
    @staticmethod
    def implied_volatility_batch(
        prices: FloatOrArray,
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        is_calls: FloatOrArray
    ) -> NDArray[np.float64]:
        """Calculate batch of implied volatilities.
        
        Args:
            prices: Option prices
            spots: Spot prices
            strikes: Strike prices
            times: Times to maturity
            rates: Risk-free rates
            dividend_yields: Dividend yields
            is_calls: Boolean array for option types
            
        Returns:
            Array of implied volatilities
        """
        ...

# American model
class american:
    @staticmethod
    def call_price(s: float, k: float, t: float, r: float, q: float, sigma: float) -> float:
        """Calculate American call option price using Bjerksund-Stensland approximation.
        
        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            q: Dividend yield
            sigma: Volatility
            
        Returns:
            Call option price
        """
        ...
    
    @staticmethod
    def put_price(s: float, k: float, t: float, r: float, q: float, sigma: float) -> float:
        """Calculate American put option price.
        
        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            q: Dividend yield
            sigma: Volatility
            
        Returns:
            Put option price
        """
        ...
    
    @staticmethod
    def call_price_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray
    ) -> NDArray[np.float64]:
        """Calculate batch of American call option prices.
        
        Args:
            spots: Spot prices
            strikes: Strike prices
            times: Times to maturity
            rates: Risk-free rates
            dividend_yields: Dividend yields
            sigmas: Volatilities
            
        Returns:
            Array of call option prices
        """
        ...
    
    @staticmethod
    def put_price_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray
    ) -> NDArray[np.float64]:
        """Calculate batch of American put option prices.
        
        Args:
            spots: Spot prices
            strikes: Strike prices
            times: Times to maturity
            rates: Risk-free rates
            dividend_yields: Dividend yields
            sigmas: Volatilities
            
        Returns:
            Array of put option prices
        """
        ...
    
    @staticmethod
    def greeks(
        s: float, k: float, t: float, r: float, q: float, sigma: float, 
        is_call: bool = True
    ) -> Dict[str, float]:
        """Calculate Greeks for American model.
        
        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            q: Dividend yield
            sigma: Volatility
            is_call: True for call option, False for put option (default: True)
            
        Returns:
            Dictionary with Greeks (delta, gamma, vega, theta, rho, dividend_rho)
        """
        ...
    
    @staticmethod
    def greeks_batch(
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        sigmas: FloatOrArray,
        is_calls: Optional[FloatOrArray] = None
    ) -> Dict[str, NDArray[np.float64]]:
        """Calculate batch of Greeks for American model.
        
        Args:
            spots: Spot prices
            strikes: Strike prices
            times: Times to maturity
            rates: Risk-free rates
            dividend_yields: Dividend yields
            sigmas: Volatilities
            is_calls: Boolean array for option types (default: all calls)
            
        Returns:
            Dictionary with arrays of Greeks
        """
        ...
    
    @staticmethod
    def implied_volatility(
        price: float, s: float, k: float, t: float, r: float, q: float, is_call: bool
    ) -> float:
        """Calculate implied volatility using American model.
        
        Args:
            price: Option price
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            q: Dividend yield
            is_call: True for call option, False for put option
            
        Returns:
            Implied volatility
        """
        ...
    
    @staticmethod
    def implied_volatility_batch(
        prices: FloatOrArray,
        spots: FloatOrArray,
        strikes: FloatOrArray,
        times: FloatOrArray,
        rates: FloatOrArray,
        dividend_yields: FloatOrArray,
        is_calls: FloatOrArray
    ) -> NDArray[np.float64]:
        """Calculate batch of implied volatilities.
        
        Args:
            prices: Option prices
            spots: Spot prices
            strikes: Strike prices
            times: Times to maturity
            rates: Risk-free rates
            dividend_yields: Dividend yields
            is_calls: Boolean array for option types
            
        Returns:
            Array of implied volatilities
        """
        ...

# Module version
__version__: str