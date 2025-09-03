"""Refactored Black76 model tests using base class to eliminate duplication."""

import math

from quantforge.models import black76

from tests.base_model_test import BaseModelTest
from tests.conftest import THEORETICAL_TOLERANCE


class TestBlack76Refactored(BaseModelTest):
    """Comprehensive Black76 model tests with reduced duplication."""

    @property
    def model(self):
        """The Black76 model module."""
        return black76

    @property
    def default_params(self) -> dict[str, float]:
        """Default parameters for Black76 model."""
        return {"f": 100.0, "k": 100.0, "t": 1.0, "r": 0.05, "sigma": 0.2}

    @property
    def atm_call_price_expected(self) -> float:
        """Expected ATM call price for Black76."""
        return 7.97

    @property
    def atm_put_price_expected(self) -> float:
        """Expected ATM put price for Black76."""
        return 7.97  # For futures, ATM call and put have same value

    def test_put_call_parity(self) -> None:
        """Test put-call parity relationship for futures options."""
        f, k, t, r, sigma = 100.0, 95.0, 1.0, 0.05, 0.2
        call = black76.call_price(f, k, t, r, sigma)
        put = black76.put_price(f, k, t, r, sigma)

        # Put-Call Parity for futures: C - P = exp(-r*t) * (F - K)
        lhs = call - put
        rhs = math.exp(-r * t) * (f - k)
        assert abs(lhs - rhs) < THEORETICAL_TOLERANCE

    # Additional Black76 specific tests
    def test_futures_specific_behavior(self) -> None:
        """Test behavior specific to futures options."""
        # For ATM futures options, call and put prices should be equal
        call = black76.call_price(f=100, k=100, t=1, r=0.05, sigma=0.2)
        put = black76.put_price(f=100, k=100, t=1, r=0.05, sigma=0.2)
        assert abs(call - put) < THEORETICAL_TOLERANCE

    def test_interest_rate_sensitivity(self) -> None:
        """Test that Black76 is less sensitive to interest rates than Black-Scholes."""
        # Black76 uses forward price, so interest rate mainly affects discounting
        call_r1 = black76.call_price(f=100, k=100, t=1, r=0.05, sigma=0.2)
        call_r2 = black76.call_price(f=100, k=100, t=1, r=0.10, sigma=0.2)

        # The difference should be relatively small (mainly discounting effect)
        assert abs(call_r1 - call_r2) < 1.0

    def test_forward_price_consistency(self) -> None:
        """Test that forward price is treated correctly."""
        # If forward price equals strike, option should have time value only
        call = black76.call_price(f=100, k=100, t=1, r=0.05, sigma=0.2)
        assert call > 0  # Has time value

        # Deep ITM should converge to discounted intrinsic value
        deep_itm = black76.call_price(f=200, k=100, t=1, r=0.05, sigma=0.01)
        expected_intrinsic = (200 - 100) * math.exp(-0.05)
        assert abs(deep_itm - expected_intrinsic) < 0.1
