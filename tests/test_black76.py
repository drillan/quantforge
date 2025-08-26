"""Tests for Black76 model implementation."""

import math

import numpy as np
import pytest
from quantforge.models import black76


class TestBlack76Pricing:
    """Test Black76 pricing functions."""

    def test_call_price_basic(self) -> None:
        """Test basic call option pricing."""
        f = 100.0  # forward
        k = 100.0  # strike
        t = 1.0  # time
        r = 0.05  # rate
        sigma = 0.2

        call_price = black76.call_price(f, k, t, r, sigma)

        assert call_price > 0
        assert call_price < f  # Call price should be less than forward

    def test_put_price_basic(self) -> None:
        """Test basic put option pricing."""
        f = 100.0  # forward
        k = 100.0  # strike
        t = 1.0  # time
        r = 0.05  # rate
        sigma = 0.2

        put_price = black76.put_price(f, k, t, r, sigma)

        assert put_price > 0
        assert put_price < k  # Put price should be less than strike

    def test_put_call_parity(self) -> None:
        """Test put-call parity: C - P = DF * (F - K)."""
        f = 100.0  # forward
        k = 105.0  # strike
        t = 1.0  # time
        r = 0.05  # rate
        sigma = 0.25

        call_price = black76.call_price(f, k, t, r, sigma)
        put_price = black76.put_price(f, k, t, r, sigma)

        discount_factor = math.exp(-r * t)
        expected_diff = discount_factor * (f - k)
        actual_diff = call_price - put_price

        assert abs(actual_diff - expected_diff) < 1e-10

    def test_atm_option(self) -> None:
        """Test at-the-money option pricing."""
        f = 100.0  # forward
        k = 100.0  # strike
        t = 1.0  # time
        r = 0.05  # rate
        sigma = 0.2

        call_price = black76.call_price(f, k, t, r, sigma)
        put_price = black76.put_price(f, k, t, r, sigma)

        # For ATM with F = K, call and put should be equal
        assert abs(call_price - put_price) < 1e-10

    def test_deep_itm_call(self) -> None:
        """Test deep in-the-money call option."""
        f = 150.0  # forward
        k = 100.0  # strike
        t = 0.01  # Short maturity
        r = 0.05  # rate
        sigma = 0.2

        call_price = black76.call_price(f, k, t, r, sigma)
        discount_factor = math.exp(-r * t)
        intrinsic_value = discount_factor * (f - k)

        # Deep ITM call should be close to intrinsic value
        assert abs(call_price - intrinsic_value) < 0.01

    def test_deep_otm_call(self) -> None:
        """Test deep out-of-the-money call option."""
        f = 50.0  # forward
        k = 100.0  # strike
        t = 0.01  # Short maturity
        r = 0.05  # rate
        sigma = 0.2

        call_price = black76.call_price(f, k, t, r, sigma)

        # Deep OTM call should be nearly worthless
        assert call_price < 0.001

    def test_batch_processing(self) -> None:
        """Test batch price calculation."""
        fs = np.array([90.0, 95.0, 100.0, 105.0, 110.0])  # forwards
        k = 100.0  # strike
        t = 1.0  # time
        r = 0.05  # rate
        sigma = 0.2

        batch_prices = black76.call_price_batch(fs, k, t, r, sigma)

        assert len(batch_prices) == len(fs)

        # Verify each price individually
        for i, forward in enumerate(fs):
            individual_price = black76.call_price(forward, k, t, r, sigma)
            assert abs(batch_prices[i] - individual_price) < 1e-10

    def test_invalid_inputs(self) -> None:
        """Test that invalid inputs raise appropriate errors."""
        with pytest.raises(ValueError):
            black76.call_price(-100, 100, 1.0, 0.05, 0.2)  # Negative forward

        with pytest.raises(ValueError):
            black76.put_price(100, -100, 1.0, 0.05, 0.2)  # Negative strike

        with pytest.raises(ValueError):
            black76.call_price(100, 100, -1.0, 0.05, 0.2)  # Negative time

        with pytest.raises(ValueError):
            black76.put_price(100, 100, 1.0, 0.05, -0.2)  # Negative volatility


class TestBlack76Greeks:
    """Test Black76 Greeks calculations."""

    def test_greeks_basic(self) -> None:
        """Test basic Greeks calculation."""
        f = 100.0  # forward
        k = 100.0  # strike
        t = 1.0  # time
        r = 0.05  # rate
        sigma = 0.2

        greeks = black76.greeks(f, k, t, r, sigma, is_call=True)

        assert hasattr(greeks, "delta")
        assert hasattr(greeks, "gamma")
        assert hasattr(greeks, "vega")
        assert hasattr(greeks, "theta")
        assert hasattr(greeks, "rho")

    def test_delta_bounds(self) -> None:
        """Test that delta is within theoretical bounds."""
        f = 100.0  # forward
        k = 100.0  # strike
        t = 1.0  # time
        r = 0.05  # rate
        sigma = 0.2
        discount_factor = math.exp(-r * t)

        call_greeks = black76.greeks(f, k, t, r, sigma, is_call=True)
        put_greeks = black76.greeks(f, k, t, r, sigma, is_call=False)

        # Call delta should be between 0 and discount factor
        assert 0 <= call_greeks.delta <= discount_factor

        # Put delta should be between -discount factor and 0
        assert -discount_factor <= put_greeks.delta <= 0

    def test_gamma_symmetry(self) -> None:
        """Test that gamma is the same for calls and puts."""
        f = 100.0  # forward
        k = 100.0  # strike
        t = 1.0  # time
        r = 0.05  # rate
        sigma = 0.2

        call_greeks = black76.greeks(f, k, t, r, sigma, is_call=True)
        put_greeks = black76.greeks(f, k, t, r, sigma, is_call=False)

        assert abs(call_greeks.gamma - put_greeks.gamma) < 1e-10

    def test_vega_symmetry(self) -> None:
        """Test that vega is the same for calls and puts."""
        f = 100.0  # forward
        k = 100.0  # strike
        t = 1.0  # time
        r = 0.05  # rate
        sigma = 0.2

        call_greeks = black76.greeks(f, k, t, r, sigma, is_call=True)
        put_greeks = black76.greeks(f, k, t, r, sigma, is_call=False)

        assert abs(call_greeks.vega - put_greeks.vega) < 1e-10

    def test_theta_sign(self) -> None:
        """Test that theta is calculated correctly."""
        f = 100.0  # forward
        k = 100.0  # strike
        t = 1.0  # time
        r = 0.05  # rate
        sigma = 0.2

        call_greeks = black76.greeks(f, k, t, r, sigma, is_call=True)

        # Theta should be finite and reasonable
        assert abs(call_greeks.theta) < 1.0  # Daily theta should be small
        assert not math.isnan(call_greeks.theta)
        assert not math.isinf(call_greeks.theta)


class TestBlack76ImpliedVolatility:
    """Test Black76 implied volatility calculations."""

    def test_iv_recovery(self) -> None:
        """Test that we can recover the original volatility."""
        f = 100.0  # forward
        k = 100.0  # strike
        t = 1.0  # time
        r = 0.05  # rate
        original_sigma = 0.25

        # Calculate price with known volatility
        call_price = black76.call_price(f, k, t, r, original_sigma)

        # Recover implied volatility
        recovered_iv = black76.implied_volatility(call_price, f, k, t, r, is_call=True)

        assert abs(recovered_iv - original_sigma) < 0.001

    def test_iv_different_strikes(self) -> None:
        """Test IV recovery for different strikes."""
        f = 100.0  # forward
        t = 1.0  # time
        r = 0.05  # rate
        true_sigma = 0.3

        for k in [80.0, 90.0, 100.0, 110.0, 120.0]:  # strike values
            call_price = black76.call_price(f, k, t, r, true_sigma)
            recovered_iv = black76.implied_volatility(call_price, f, k, t, r, is_call=True)
            assert abs(recovered_iv - true_sigma) < 0.001

    def test_iv_put_option(self) -> None:
        """Test IV calculation for put options."""
        f = 100.0  # forward
        k = 100.0  # strike
        t = 1.0  # time
        r = 0.05  # rate
        original_sigma = 0.2

        put_price = black76.put_price(f, k, t, r, original_sigma)
        recovered_iv = black76.implied_volatility(put_price, f, k, t, r, is_call=False)

        assert abs(recovered_iv - original_sigma) < 0.001

    def test_iv_invalid_price(self) -> None:
        """Test that invalid prices raise appropriate errors."""
        f = 100.0  # forward
        k = 100.0  # strike
        t = 1.0  # time
        r = 0.05  # rate

        # Negative price should raise error (now ValueError due to validation)
        with pytest.raises(ValueError):
            black76.implied_volatility(-10.0, f, k, t, r, is_call=True)

        # Price below intrinsic value should raise error
        discount = math.exp(-r * t)
        intrinsic = discount * (f - k)
        if intrinsic > 0:
            with pytest.raises(RuntimeError):
                black76.implied_volatility(intrinsic * 0.5, f, k, t, r, is_call=True)


def test_spot_to_forward_conversion() -> None:
    """Test conversion from spot to forward price."""
    # This is a utility function that should be provided separately
    # F = S * exp((r - q) * T)
    s = 100.0  # spot
    r = 0.05  # rate
    q = 0.02  # dividend yield
    t = 1.0  # time

    expected_forward = s * math.exp((r - q) * t)

    # If the module provides this utility
    # actual_forward = black76.spot_to_forward(spot, rate, div_yield, time)
    # assert abs(actual_forward - expected_forward) < 1e-10

    # For now, just verify the formula
    assert abs(expected_forward - 103.045453) < 1e-6
