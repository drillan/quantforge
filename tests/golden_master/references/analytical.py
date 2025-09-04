"""Analytical reference values for special cases.

Direct mathematical formulas for edge cases and special scenarios
where closed-form solutions exist.
"""

import math


class AnalyticalReference:
    """Analytical solutions for special cases."""

    @staticmethod
    def intrinsic_value(s: float, k: float, t: float, r: float, is_call: bool = True) -> float:
        """Calculate intrinsic value for zero volatility case.

        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            is_call: True for call, False for put

        Returns:
            Intrinsic value
        """
        discounted_strike = k * math.exp(-r * t)
        if is_call:
            return max(s - discounted_strike, 0.0)
        else:
            return max(discounted_strike - s, 0.0)

    @staticmethod
    def put_call_parity(call_price: float, s: float, k: float, t: float, r: float) -> float:
        """Calculate put price using put-call parity.

        C - P = S - K*exp(-r*t)

        Args:
            call_price: Call option price
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate

        Returns:
            Put option price
        """
        return call_price - s + k * math.exp(-r * t)

    @staticmethod
    def extreme_cases(s: float, k: float, t: float, r: float, sigma: float) -> dict[str, float]:
        """Handle extreme parameter cases analytically.

        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            sigma: Volatility

        Returns:
            Dictionary with prices for extreme cases
        """
        result = {}

        # Very deep ITM/OTM
        moneyness = s / k
        if moneyness > 5.0:  # Deep ITM call / Deep OTM put
            result["call_price"] = s - k * math.exp(-r * t)
            result["put_price"] = 0.0
            result["delta_call"] = 1.0
            result["delta_put"] = 0.0
        elif moneyness < 0.2:  # Deep OTM call / Deep ITM put
            result["call_price"] = 0.0
            result["put_price"] = k * math.exp(-r * t) - s
            result["delta_call"] = 0.0
            result["delta_put"] = -1.0

        # Near expiry
        if t < 0.001:  # Less than ~8 hours
            if s > k:
                result["call_price"] = s - k
                result["put_price"] = 0.0
            elif s < k:
                result["call_price"] = 0.0
                result["put_price"] = k - s
            else:  # ATM
                # Approximate using sqrt(t) scaling
                result["call_price"] = 0.3989 * s * sigma * math.sqrt(t)
                result["put_price"] = result["call_price"]

        # Zero volatility
        if sigma < 0.001:
            result["call_price"] = max(s - k * math.exp(-r * t), 0.0)
            result["put_price"] = max(k * math.exp(-r * t) - s, 0.0)

        return result

    @staticmethod
    def boundary_conditions(s: float, k: float, t: float, r: float, sigma: float) -> dict[str, float]:
        """Check boundary conditions for option pricing.

        Args:
            s: Spot price
            k: Strike price
            t: Time to maturity
            r: Risk-free rate
            sigma: Volatility

        Returns:
            Dictionary with boundary values
        """
        result = {}

        # Price bounds
        result["call_lower_bound"] = max(s - k * math.exp(-r * t), 0.0)
        result["call_upper_bound"] = s
        result["put_lower_bound"] = max(k * math.exp(-r * t) - s, 0.0)
        result["put_upper_bound"] = k * math.exp(-r * t)

        # American option bounds
        result["american_call_lower"] = max(s - k, result["call_lower_bound"])
        result["american_put_lower"] = max(k - s, result["put_lower_bound"])

        return result
