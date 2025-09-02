"""Test Arrow Native Broadcasting functionality."""

import pyarrow as pa
import pytest
from quantforge import arrow_native


def test_black_scholes_broadcasting():
    """Test Black-Scholes broadcasting with scalar values."""
    # Multiple spots, single strike (broadcasting)
    spots = pa.array([100.0, 105.0, 110.0])
    strikes = pa.array([100.0])  # scalar - will broadcast
    times = pa.array([1.0])  # scalar
    rates = pa.array([0.05])  # scalar
    sigmas = pa.array([0.2])  # scalar

    # Call prices
    result = arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)
    assert len(result) == 3

    # Prices should increase with spot price
    prices = result.to_numpy()
    assert prices[1] > prices[0]
    assert prices[2] > prices[1]

    # Put prices
    result = arrow_native.arrow_put_price(spots, strikes, times, rates, sigmas)
    assert len(result) == 3

    # Put prices should decrease with spot price
    prices = result.to_numpy()
    assert prices[1] < prices[0]
    assert prices[2] < prices[1]


def test_black_scholes_greeks_broadcasting():
    """Test Black-Scholes Greeks with broadcasting."""
    # Multiple spots, single strike
    spots = pa.array([95.0, 100.0, 105.0])
    strikes = pa.array([100.0])  # scalar
    times = pa.array([1.0])  # scalar
    rates = pa.array([0.05])  # scalar
    sigmas = pa.array([0.2])  # scalar

    # Calculate Greeks for calls
    greeks = arrow_native.arrow_greeks(spots, strikes, times, rates, sigmas, True)

    assert isinstance(greeks, dict)
    assert "delta" in greeks
    assert "gamma" in greeks
    assert "vega" in greeks
    assert "theta" in greeks
    assert "rho" in greeks

    # All Greeks should have same length as spots
    for greek_name, greek_values in greeks.items():
        assert len(greek_values) == 3, f"{greek_name} has wrong length"

    # Delta should increase with spot price for calls
    delta_values = greeks["delta"].to_numpy()
    assert delta_values[1] > delta_values[0]
    assert delta_values[2] > delta_values[1]


def test_black76_broadcasting():
    """Test Black76 broadcasting with scalar values."""
    # Multiple forwards, single strike
    forwards = pa.array([100.0, 105.0, 110.0])
    strikes = pa.array([100.0])  # scalar
    times = pa.array([1.0])  # scalar
    rates = pa.array([0.05])  # scalar
    sigmas = pa.array([0.2])  # scalar

    # Call prices
    result = arrow_native.arrow76_call_price(forwards, strikes, times, rates, sigmas)
    assert len(result) == 3

    # Prices should increase with forward price
    prices = result.to_numpy()
    assert prices[1] > prices[0]
    assert prices[2] > prices[1]

    # Put prices
    result = arrow_native.arrow76_put_price(forwards, strikes, times, rates, sigmas)
    assert len(result) == 3

    # Put prices should decrease with forward price
    prices = result.to_numpy()
    assert prices[1] < prices[0]
    assert prices[2] < prices[1]


def test_black76_greeks_broadcasting():
    """Test Black76 Greeks with broadcasting."""
    # Multiple forwards, single strike
    forwards = pa.array([95.0, 100.0, 105.0])
    strikes = pa.array([100.0])  # scalar
    times = pa.array([1.0])  # scalar
    rates = pa.array([0.05])  # scalar
    sigmas = pa.array([0.2])  # scalar

    # Calculate Greeks for calls
    greeks = arrow_native.arrow76_greeks(forwards, strikes, times, rates, sigmas, True)

    assert isinstance(greeks, dict)
    assert "delta" in greeks
    assert "gamma" in greeks
    assert "vega" in greeks
    assert "theta" in greeks
    assert "rho" in greeks

    # All Greeks should have same length as forwards
    for greek_name, greek_values in greeks.items():
        assert len(greek_values) == 3, f"{greek_name} has wrong length"

    # Delta should increase with forward price for calls
    delta_values = greeks["delta"].to_numpy()
    assert delta_values[1] > delta_values[0]
    assert delta_values[2] > delta_values[1]


def test_mixed_broadcasting():
    """Test broadcasting with mixed scalar and array inputs."""
    # Array strikes, scalar spot (reverse broadcasting)
    spots = pa.array([100.0])  # scalar
    strikes = pa.array([95.0, 100.0, 105.0])  # array
    times = pa.array([1.0])  # scalar
    rates = pa.array([0.05])  # scalar
    sigmas = pa.array([0.2])  # scalar

    result = arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)
    assert len(result) == 3

    # Prices should decrease with strike price
    prices = result.to_numpy()
    assert prices[1] < prices[0]
    assert prices[2] < prices[1]


def test_incompatible_lengths():
    """Test that incompatible lengths raise an error."""
    # Arrays with incompatible lengths (not 1 and not same)
    spots = pa.array([100.0, 105.0])  # length 2
    strikes = pa.array([95.0, 100.0, 105.0])  # length 3
    times = pa.array([1.0])  # scalar
    rates = pa.array([0.05])  # scalar
    sigmas = pa.array([0.2])  # scalar

    with pytest.raises(Exception):  # Should raise an error
        arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)


def test_all_arrays_same_length():
    """Test normal case where all arrays have same length."""
    # All arrays same length
    spots = pa.array([100.0, 105.0, 110.0])
    strikes = pa.array([95.0, 100.0, 105.0])
    times = pa.array([1.0, 0.5, 0.25])
    rates = pa.array([0.05, 0.04, 0.03])
    sigmas = pa.array([0.2, 0.25, 0.3])

    result = arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)
    assert len(result) == 3

    # Greeks should also work
    greeks = arrow_native.arrow_greeks(spots, strikes, times, rates, sigmas, True)
    for greek_name, greek_values in greeks.items():
        assert len(greek_values) == 3


def test_single_element_arrays():
    """Test that single element arrays work correctly."""
    # All single element arrays (should work like scalars)
    spots = pa.array([100.0])
    strikes = pa.array([100.0])
    times = pa.array([1.0])
    rates = pa.array([0.05])
    sigmas = pa.array([0.2])

    result = arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)
    assert len(result) == 1

    # Should give same result as standard Black-Scholes
    price = result.to_numpy()[0]
    assert abs(price - 10.4506) < 0.01  # Expected Black-Scholes value


if __name__ == "__main__":
    test_black_scholes_broadcasting()
    test_black_scholes_greeks_broadcasting()
    test_black76_broadcasting()
    test_black76_greeks_broadcasting()
    test_mixed_broadcasting()
    test_incompatible_lengths()
    test_all_arrays_same_length()
    test_single_element_arrays()
    print("All broadcasting tests passed!")
