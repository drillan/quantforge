"""Test Black-Scholes Python API bindings."""

import numpy as np

from python.quantforge import models


class TestBlackScholesAPI:
    """Test Black-Scholes Python API."""

    def test_call_price_scalar(self):
        """Test scalar call price calculation."""
        price = models.black_scholes.call_price(100, 100, 1, 0.05, 0.2)
        assert isinstance(price, float)
        assert abs(price - 10.450583572185565) < 1e-10

    def test_put_price_scalar(self):
        """Test scalar put price calculation."""
        price = models.black_scholes.put_price(100, 100, 1, 0.05, 0.2)
        assert isinstance(price, float)
        assert price > 0

    def test_greeks_return_type(self):
        """Test Greeks return dictionary."""
        greeks = models.black_scholes.greeks(100, 100, 1, 0.05, 0.2)
        assert isinstance(greeks, dict)
        assert all(k in greeks for k in ["delta", "gamma", "vega", "theta", "rho"])


class TestBatchProcessing:
    """Test batch processing functionality."""

    def test_call_price_batch_numpy(self):
        """Test batch processing with NumPy arrays."""
        spots = np.array([90, 100, 110], dtype=np.float64)
        prices = models.black_scholes.call_price_batch(spots, 100, 1, 0.05, 0.2)

        assert isinstance(prices, np.ndarray)
        assert len(prices) == 3
        assert all(prices > 0)

    def test_broadcasting(self):
        """Test NumPy-style broadcasting."""
        spots = np.linspace(80, 120, 100)
        strikes = 100.0  # Scalar

        prices = models.black_scholes.call_price_batch(spots, strikes, 1, 0.05, 0.2)
        assert len(prices) == 100


class TestBlack76API:
    """Test Black76 Python API."""

    def test_call_price_scalar(self):
        """Test scalar call price calculation."""
        price = models.black76.call_price(100, 100, 1, 0.05, 0.2)
        assert isinstance(price, float)
        assert price > 0

    def test_batch_processing(self):
        """Test batch processing."""
        forwards = np.array([90, 100, 110], dtype=np.float64)
        prices = models.black76.call_price_batch(forwards, 100, 1, 0.05, 0.2)

        assert isinstance(prices, np.ndarray)
        assert len(prices) == 3
        assert all(prices > 0)


class TestMertonAPI:
    """Test Merton (dividend) model Python API."""

    def test_call_price_with_dividend(self):
        """Test call price with dividend yield."""
        price = models.merton.call_price(100, 100, 1, 0.05, 0.02, 0.2)
        assert isinstance(price, float)
        assert price > 0

    def test_zero_dividend_equals_black_scholes(self):
        """Test that Merton with q=0 equals Black-Scholes."""
        bs_price = models.black_scholes.call_price(100, 100, 1, 0.05, 0.2)
        merton_price = models.merton.call_price(100, 100, 1, 0.05, 0.0, 0.2)

        assert abs(bs_price - merton_price) < 1e-10
