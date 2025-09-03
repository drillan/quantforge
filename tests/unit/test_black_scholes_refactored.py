"""Refactored Black-Scholes model tests using base class to eliminate duplication."""

import math

from quantforge.models import black_scholes

from tests.base_model_test import BaseModelTest
from tests.conftest import THEORETICAL_TOLERANCE


class TestBlackScholesRefactored(BaseModelTest):
    """Comprehensive Black-Scholes model tests with reduced duplication."""

    @property
    def model(self):
        """The Black-Scholes model module."""
        return black_scholes

    @property
    def default_params(self) -> dict[str, float]:
        """Default parameters for Black-Scholes model."""
        return {"s": 100.0, "k": 100.0, "t": 1.0, "r": 0.05, "sigma": 0.2}

    @property
    def atm_call_price_expected(self) -> float:
        """Expected ATM call price for Black-Scholes."""
        return 10.45

    @property
    def atm_put_price_expected(self) -> float:
        """Expected ATM put price for Black-Scholes."""
        return 5.57

    def test_put_call_parity(self) -> None:
        """Test put-call parity relationship for Black-Scholes."""
        s, k, t, r, sigma = 100.0, 95.0, 1.0, 0.05, 0.2
        call = black_scholes.call_price(s, k, t, r, sigma)
        put = black_scholes.put_price(s, k, t, r, sigma)

        # Put-Call Parity: C - P = S - K * exp(-r*t)
        lhs = call - put
        rhs = s - k * math.exp(-r * t)
        assert abs(lhs - rhs) < THEORETICAL_TOLERANCE

    # Additional Black-Scholes specific tests can be added here
    def test_european_no_early_exercise(self) -> None:
        """Test that Black-Scholes prices are for European options only."""
        # Black-Scholes assumes European options (no early exercise)
        # Price should be continuous function of time
        price_t1 = black_scholes.call_price(s=100, k=100, t=1.0, r=0.05, sigma=0.2)
        price_t2 = black_scholes.call_price(s=100, k=100, t=0.9, r=0.05, sigma=0.2)

        # Price should decrease as we approach expiration for ATM options
        assert price_t2 < price_t1

    def test_extreme_moneyness(self) -> None:
        """Test extreme moneyness scenarios specific to Black-Scholes."""
        # Very deep ITM call should be approximately S - K*exp(-r*t)
        deep_itm_call = black_scholes.call_price(s=1000, k=100, t=1, r=0.05, sigma=0.2)
        expected = 1000 - 100 * math.exp(-0.05)
        assert abs(deep_itm_call - expected) < 0.01

        # Very deep OTM call should be nearly zero
        deep_otm_call = black_scholes.call_price(s=10, k=100, t=1, r=0.05, sigma=0.2)
        assert deep_otm_call < 0.0001
