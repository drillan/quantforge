"""Type checking tests for quantforge module"""

import numpy as np
import pytest
from quantforge import black76, black_scholes, merton
from quantforge.quantforge import american  # Direct import for american


class TestTypeChecking:
    """Test type annotations and type checking"""

    def test_scalar_return_types(self):
        """Test that scalar functions return float"""
        # Black-Scholes
        price = black_scholes.call_price(100, 100, 1, 0.05, 0.2)
        assert isinstance(price, float)

        price = black_scholes.put_price(100, 100, 1, 0.05, 0.2)
        assert isinstance(price, float)

        # Black76
        price = black76.call_price(100, 100, 1, 0.05, 0.2)
        assert isinstance(price, float)

        # Merton
        price = merton.call_price(100, 100, 1, 0.05, 0.02, 0.2)
        assert isinstance(price, float)

        # American
        price = american.call_price(100, 100, 1, 0.05, 0.02, 0.2)
        assert isinstance(price, float)

    def test_batch_return_types(self):
        """Test that batch functions return numpy arrays"""
        spots = np.array([90, 100, 110], dtype=np.float64)

        # Black-Scholes batch
        prices = black_scholes.call_price_batch(spots, 100, 1, 0.05, 0.2)
        assert isinstance(prices, np.ndarray)
        assert prices.dtype == np.float64

        # Black76 batch
        forwards = np.array([90, 100, 110], dtype=np.float64)
        prices = black76.call_price_batch(forwards, 100, 1, 0.05, 0.2)
        assert isinstance(prices, np.ndarray)

        # Merton batch
        prices = merton.call_price_batch(spots, 100, 1, 0.05, 0.02, 0.2)
        assert isinstance(prices, np.ndarray)

    def test_greeks_return_types(self):
        """Test that greeks functions return dictionaries"""
        # Black-Scholes Greeks
        greeks = black_scholes.greeks(100, 100, 1, 0.05, 0.2)
        assert isinstance(greeks, dict)
        assert "delta" in greeks
        assert "gamma" in greeks
        assert "vega" in greeks
        assert "theta" in greeks
        assert "rho" in greeks
        assert all(isinstance(v, float) for v in greeks.values())

        # Black76 Greeks
        greeks = black76.greeks(100, 100, 1, 0.05, 0.2)
        assert isinstance(greeks, dict)

        # Merton Greeks
        greeks = merton.greeks(100, 100, 1, 0.05, 0.02, 0.2)
        assert isinstance(greeks, dict)
        assert "dividend_rho" in greeks  # Extra Greek for Merton

    def test_greeks_batch_return_types(self):
        """Test that batch greeks functions return dict of arrays"""
        spots = np.array([90, 100, 110], dtype=np.float64)
        is_calls = np.array([True, True, False])

        # Black-Scholes batch Greeks
        greeks = black_scholes.greeks_batch(spots, 100, 1, 0.05, 0.2, is_calls)
        assert isinstance(greeks, dict)
        assert "delta" in greeks
        assert isinstance(greeks["delta"], np.ndarray)
        assert greeks["delta"].shape == spots.shape

        # Merton batch Greeks
        greeks = merton.greeks_batch(spots, 100, 1, 0.05, 0.02, 0.2, is_calls)
        assert isinstance(greeks, dict)
        assert "dividend_rho" in greeks
        assert isinstance(greeks["dividend_rho"], np.ndarray)

    def test_implied_volatility_types(self):
        """Test implied volatility return types"""
        # Scalar IV
        iv = black_scholes.implied_volatility(10, 100, 100, 1, 0.05, True)
        assert isinstance(iv, float)

        # Batch IV
        prices = np.array([8, 10, 12], dtype=np.float64)
        spots = np.array([90, 100, 110], dtype=np.float64)
        is_calls = np.array([True, True, False])

        ivs = black_scholes.implied_volatility_batch(prices, spots, 100, 1, 0.05, is_calls)
        assert isinstance(ivs, np.ndarray)
        assert ivs.shape == prices.shape

    def test_input_type_flexibility(self):
        """Test that functions accept various input types"""
        # Test with Python list
        spots_list = [90.0, 100.0, 110.0]
        prices = black_scholes.call_price_batch(spots_list, 100, 1, 0.05, 0.2)
        assert isinstance(prices, np.ndarray)
        assert len(prices) == 3

        # Test with integer inputs (should be converted to float)
        price = black_scholes.call_price(100, 100, 1, 0.05, 0.2)
        assert isinstance(price, float)

        # Test with mixed types
        prices = black_scholes.call_price_batch(
            [90, 100, 110],  # int list
            100.0,  # float scalar
            1,  # int
            0.05,  # float
            0.2,  # float
        )
        assert isinstance(prices, np.ndarray)

    def test_broadcasting_behavior(self):
        """Test broadcasting behavior with mixed scalar/array inputs"""
        spots = np.array([90, 100, 110])

        # Scalar strike, array spots
        prices = black_scholes.call_price_batch(spots, 100, 1, 0.05, 0.2)
        assert len(prices) == 3

        # Array spots, array strikes (same length)
        strikes = np.array([95, 100, 105])
        prices = black_scholes.call_price_batch(spots, strikes, 1, 0.05, 0.2)
        assert len(prices) == 3

        # All scalars should work
        prices = black_scholes.call_price_batch(100, 100, 1, 0.05, 0.2)
        assert isinstance(prices, np.ndarray)

    def test_error_types(self):
        """Test that appropriate errors are raised for invalid inputs"""
        # Invalid input values should raise ValueError
        with pytest.raises(ValueError):
            black_scholes.call_price(-100, 100, 1, 0.05, 0.2)  # Negative spot

        with pytest.raises(ValueError):
            black_scholes.call_price(100, 100, -1, 0.05, 0.2)  # Negative time

        with pytest.raises(ValueError):
            black_scholes.call_price(100, 100, 1, 0.05, -0.2)  # Negative volatility

        # Shape mismatch should raise ValueError
        spots = np.array([90, 100])
        strikes = np.array([95, 100, 105])
        with pytest.raises(ValueError, match="Shape mismatch|broadcast"):
            black_scholes.call_price_batch(spots, strikes, 1, 0.05, 0.2)

    def test_nan_handling(self):
        """Test handling of invalid calculations that produce NaN"""
        # Implied volatility with impossible price should return NaN
        iv = black_scholes.implied_volatility(200, 100, 100, 1, 0.05, True)
        assert np.isnan(iv) or iv == float("inf")

        # Batch with invalid inputs
        prices = np.array([10, -5, 200])  # Middle value is invalid
        spots = np.array([100, 100, 100])
        ivs = black_scholes.implied_volatility_batch(prices, spots, 100, 1, 0.05, True)
        assert len(ivs) == 3
        assert np.isnan(ivs[1])  # Invalid price should produce NaN


class TestMypyCompliance:
    """Test for mypy compliance (these would be checked by mypy, not pytest)"""

    def test_type_annotations_example(self):
        """Example code that should pass mypy type checking"""
        # This is more documentation than test - mypy would check this

        # Correct usage
        s: float = 100.0
        k: float = 100.0
        t: float = 1.0
        r: float = 0.05
        sigma: float = 0.2

        price: float = black_scholes.call_price(s, k, t, r, sigma)
        assert isinstance(price, float)

        # Array usage
        spots: np.ndarray = np.array([90.0, 100.0, 110.0])
        prices: np.ndarray = black_scholes.call_price_batch(spots, k, t, r, sigma)
        assert isinstance(prices, np.ndarray)

        # Greeks
        greeks: dict[str, float] = black_scholes.greeks(s, k, t, r, sigma)
        delta: float = greeks["delta"]
        assert isinstance(delta, float)

    def test_reveal_type_examples(self):
        """Examples of what reveal_type would show (for documentation)"""
        # These are examples of what mypy's reveal_type would show
        # In actual mypy runs, these would print the inferred types

        black_scholes.call_price(100, 100, 1, 0.05, 0.2)
        # reveal_type(price)  # Would show: float

        arr = np.array([100.0])
        black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)
        # reveal_type(prices)  # Would show: NDArray[float64]

        black_scholes.greeks(100, 100, 1, 0.05, 0.2)
        # reveal_type(greeks)  # Would show: Dict[str, float]
