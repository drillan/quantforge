"""Test the new models-based API structure."""

import numpy as np
from conftest import NUMERICAL_TOLERANCE, PRACTICAL_TOLERANCE
from quantforge.models import black_scholes


class TestBlackScholesModuleAPI:
    """Test Black-Scholes module API."""

    def test_call_price(self) -> None:
        """Test Black-Scholes call price calculation."""
        price = black_scholes.call_price(spot=100.0, strike=105.0, time=1.0, rate=0.05, sigma=0.2)
        assert abs(price - 8.021352224079687) < PRACTICAL_TOLERANCE

    def test_put_price(self) -> None:
        """Test Black-Scholes put price calculation."""
        price = black_scholes.put_price(spot=100.0, strike=105.0, time=1.0, rate=0.05, sigma=0.2)
        assert abs(price - 7.90044179918926) < PRACTICAL_TOLERANCE

    def test_call_price_batch(self) -> None:
        """Test batch call price calculation."""
        spots = np.array([95.0, 100.0, 105.0, 110.0])
        prices = black_scholes.call_price_batch(spots=spots, strike=100.0, time=1.0, rate=0.05, sigma=0.2)

        # Expected values calculated with current parameters
        expected = [7.510872, 10.450584, 13.857906, 17.662954]
        np.testing.assert_allclose(prices, expected, rtol=PRACTICAL_TOLERANCE)

    def test_put_price_batch(self) -> None:
        """Test batch put price calculation."""
        spots = np.array([95.0, 100.0, 105.0, 110.0])
        prices = black_scholes.put_price_batch(spots=spots, strike=100.0, time=1.0, rate=0.05, sigma=0.2)

        # Expected values calculated with current parameters
        expected = [7.633815, 5.573526, 3.980849, 2.785896]
        np.testing.assert_allclose(prices, expected, rtol=PRACTICAL_TOLERANCE)

    def test_greeks(self) -> None:
        """Test Greeks calculation."""
        greeks = black_scholes.greeks(spot=100.0, strike=100.0, time=1.0, rate=0.05, sigma=0.2, is_call=True)

        assert hasattr(greeks, "delta")
        assert hasattr(greeks, "gamma")
        assert hasattr(greeks, "vega")
        assert hasattr(greeks, "theta")
        assert hasattr(greeks, "rho")

        # Check specific values
        assert abs(greeks.delta - 0.6368306505) < PRACTICAL_TOLERANCE
        assert abs(greeks.gamma - 0.01874042826) < PRACTICAL_TOLERANCE

    def test_implied_volatility(self) -> None:
        """Test implied volatility calculation."""
        # First calculate a price with known volatility
        target_vol = 0.25
        price = black_scholes.call_price(spot=100.0, strike=100.0, time=1.0, rate=0.05, sigma=target_vol)

        # Then recover the volatility
        iv = black_scholes.implied_volatility(price=price, spot=100.0, strike=100.0, time=1.0, rate=0.05, is_call=True)

        assert abs(iv - target_vol) < NUMERICAL_TOLERANCE

    def test_put_call_parity(self) -> None:
        """Test put-call parity relationship."""
        spot = 100.0
        strike = 105.0
        time = 1.0
        rate = 0.05
        sigma = 0.2

        call = black_scholes.call_price(spot, strike, time, rate, sigma)
        put = black_scholes.put_price(spot, strike, time, rate, sigma)

        # Put-Call Parity: C - P = S - K * exp(-r*T)
        lhs = call - put
        rhs = spot - strike * np.exp(-rate * time)

        assert abs(lhs - rhs) < NUMERICAL_TOLERANCE
