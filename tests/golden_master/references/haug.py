"""Haug (2007) "Complete Guide to Option Pricing Formulas" reference implementation.

This module provides validated reference values from Haug's textbook,
which is an industry-standard reference for option pricing formulas.
"""

import math

from scipy.stats import norm


class HaugReference:
    """Reference implementation based on Haug's formulas."""

    @staticmethod
    def black_scholes(s: float, k: float, t: float, r: float, sigma: float) -> dict[str, float]:
        """Black-Scholes model from Haug Chapter 1.

        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            sigma: Volatility

        Returns:
            Dictionary with call_price, put_price and Greeks
        """
        # Standard Black-Scholes formulas
        sqrt_t = math.sqrt(t)
        d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / (sigma * sqrt_t)
        d2 = d1 - sigma * sqrt_t

        # Prices
        call_price = s * norm.cdf(d1) - k * math.exp(-r * t) * norm.cdf(d2)
        put_price = k * math.exp(-r * t) * norm.cdf(-d2) - s * norm.cdf(-d1)

        # Greeks
        delta_call = norm.cdf(d1)
        delta_put = -norm.cdf(-d1)
        gamma = norm.pdf(d1) / (s * sigma * sqrt_t)
        vega = s * norm.pdf(d1) * sqrt_t
        theta_call = -(s * norm.pdf(d1) * sigma) / (2 * sqrt_t) - r * k * math.exp(-r * t) * norm.cdf(d2)
        theta_put = -(s * norm.pdf(d1) * sigma) / (2 * sqrt_t) + r * k * math.exp(-r * t) * norm.cdf(-d2)
        rho_call = k * t * math.exp(-r * t) * norm.cdf(d2)
        rho_put = -k * t * math.exp(-r * t) * norm.cdf(-d2)

        return {
            "call_price": call_price,
            "put_price": put_price,
            "delta_call": delta_call,
            "delta_put": delta_put,
            "gamma": gamma,
            "vega": vega,
            "theta_call": theta_call / 365,  # Convert to per-day
            "theta_put": theta_put / 365,
            "rho_call": rho_call,
            "rho_put": rho_put,
        }

    @staticmethod
    def black76(f: float, k: float, t: float, r: float, sigma: float) -> dict[str, float]:
        """Black-76 model for futures options from Haug Chapter 1.

        Args:
            f: Forward/futures price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            sigma: Volatility

        Returns:
            Dictionary with prices and Greeks
        """
        sqrt_t = math.sqrt(t)
        d1 = (math.log(f / k) + 0.5 * sigma * sigma * t) / (sigma * sqrt_t)
        d2 = d1 - sigma * sqrt_t
        discount = math.exp(-r * t)

        # Prices
        call_price = discount * (f * norm.cdf(d1) - k * norm.cdf(d2))
        put_price = discount * (k * norm.cdf(-d2) - f * norm.cdf(-d1))

        # Greeks (adjusted for futures)
        delta_call = discount * norm.cdf(d1)
        delta_put = -discount * norm.cdf(-d1)
        gamma = discount * norm.pdf(d1) / (f * sigma * sqrt_t)
        vega = f * discount * norm.pdf(d1) * sqrt_t
        theta_call = -discount * (f * norm.pdf(d1) * sigma / (2 * sqrt_t) + r * call_price)
        theta_put = -discount * (f * norm.pdf(d1) * sigma / (2 * sqrt_t) + r * put_price)
        rho_call = -t * call_price
        rho_put = -t * put_price

        return {
            "call_price": call_price,
            "put_price": put_price,
            "delta_call": delta_call,
            "delta_put": delta_put,
            "gamma": gamma,
            "vega": vega,
            "theta_call": theta_call / 365,
            "theta_put": theta_put / 365,
            "rho_call": rho_call,
            "rho_put": rho_put,
        }

    @staticmethod
    def merton(s: float, k: float, t: float, r: float, q: float, sigma: float) -> dict[str, float]:
        """Merton model with continuous dividend yield from Haug Chapter 1.

        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            q: Dividend yield
            sigma: Volatility

        Returns:
            Dictionary with prices and Greeks
        """
        sqrt_t = math.sqrt(t)
        d1 = (math.log(s / k) + (r - q + 0.5 * sigma * sigma) * t) / (sigma * sqrt_t)
        d2 = d1 - sigma * sqrt_t

        # Prices
        call_price = s * math.exp(-q * t) * norm.cdf(d1) - k * math.exp(-r * t) * norm.cdf(d2)
        put_price = k * math.exp(-r * t) * norm.cdf(-d2) - s * math.exp(-q * t) * norm.cdf(-d1)

        # Greeks
        delta_call = math.exp(-q * t) * norm.cdf(d1)
        delta_put = -math.exp(-q * t) * norm.cdf(-d1)
        gamma = math.exp(-q * t) * norm.pdf(d1) / (s * sigma * sqrt_t)
        vega = s * math.exp(-q * t) * norm.pdf(d1) * sqrt_t
        theta_call = (
            -s * math.exp(-q * t) * norm.pdf(d1) * sigma / (2 * sqrt_t)
            + q * s * math.exp(-q * t) * norm.cdf(d1)
            - r * k * math.exp(-r * t) * norm.cdf(d2)
        )
        theta_put = (
            -s * math.exp(-q * t) * norm.pdf(d1) * sigma / (2 * sqrt_t)
            - q * s * math.exp(-q * t) * norm.cdf(-d1)
            + r * k * math.exp(-r * t) * norm.cdf(-d2)
        )
        rho_call = k * t * math.exp(-r * t) * norm.cdf(d2)
        rho_put = -k * t * math.exp(-r * t) * norm.cdf(-d2)

        return {
            "call_price": call_price,
            "put_price": put_price,
            "delta_call": delta_call,
            "delta_put": delta_put,
            "gamma": gamma,
            "vega": vega,
            "theta_call": theta_call / 365,
            "theta_put": theta_put / 365,
            "rho_call": rho_call,
            "rho_put": rho_put,
        }
