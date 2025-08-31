"""ArrayLike type conversion tests"""

import numpy as np
import pytest
from quantforge import black76, black_scholes, merton


class TestArrayConversion:
    """Test ArrayLike type conversion for various input types"""

    def test_scalar_float_input(self):
        """Test scalar float input"""
        price = black_scholes.call_price_batch(100.0, 100.0, 1.0, 0.05, 0.2)
        assert isinstance(price, np.ndarray)
        assert price.shape == (1,) or price.shape == ()
        assert price.item() > 0

    def test_scalar_int_input(self):
        """Test scalar integer input (should convert to float)"""
        price = black_scholes.call_price_batch(100, 100, 1, 0.05, 0.2)
        assert isinstance(price, np.ndarray)
        assert price.item() > 0

    def test_python_list_input(self):
        """Test Python list input"""
        spots = [90.0, 100.0, 110.0]
        prices = black_scholes.call_price_batch(spots, 100.0, 1.0, 0.05, 0.2)
        assert isinstance(prices, np.ndarray)
        assert len(prices) == 3
        assert all(p > 0 for p in prices)

    def test_numpy_array_input(self):
        """Test NumPy array input"""
        spots = np.array([90.0, 100.0, 110.0])
        prices = black_scholes.call_price_batch(spots, 100.0, 1.0, 0.05, 0.2)
        assert isinstance(prices, np.ndarray)
        assert len(prices) == 3
        assert all(p > 0 for p in prices)

    def test_mixed_types_input(self):
        """Test mixed input types"""
        prices = black_scholes.call_price_batch(
            [90, 100, 110],  # list of ints
            np.array([100.0]),  # 1-element array
            1.0,  # float scalar
            0.05,  # float scalar
            [0.2, 0.2, 0.2],  # list of floats
        )
        assert isinstance(prices, np.ndarray)
        assert len(prices) == 3

    def test_broadcasting_scalar_to_array(self):
        """Test broadcasting scalar to match array size"""
        spots = np.array([90, 100, 110])  # 3 elements
        strikes = 100.0  # scalar -> broadcast to 3

        prices = black_scholes.call_price_batch(spots, strikes, 1.0, 0.05, 0.2)
        assert len(prices) == 3

        # Verify broadcasting worked correctly
        for i, spot in enumerate(spots):
            single_price = black_scholes.call_price(spot, 100.0, 1.0, 0.05, 0.2)
            np.testing.assert_allclose(prices[i], single_price, rtol=1e-10)

    def test_broadcasting_array_to_array(self):
        """Test broadcasting different sized arrays"""
        spots = np.array([90, 100, 110])  # 3 elements
        strikes = np.array([100.0])  # 1 element -> broadcast to 3
        times = np.array([1.0, 1.0, 1.0])  # 3 elements

        prices = black_scholes.call_price_batch(spots, strikes, times, 0.05, 0.2)
        assert len(prices) == 3

    def test_non_contiguous_array(self):
        """Test non-contiguous array input"""
        # Create non-contiguous array through slicing
        arr = np.arange(20).reshape(4, 5)[::2, ::2].flatten() * 10.0 + 80
        assert not arr.flags["C_CONTIGUOUS"]

        prices = black_scholes.call_price_batch(arr, 100.0, 1.0, 0.05, 0.2)
        assert len(prices) == len(arr)
        assert all(p > 0 for p in prices)

    def test_empty_array(self):
        """Test empty array handling"""
        empty = np.array([])
        prices = black_scholes.call_price_batch(empty, 100.0, 1.0, 0.05, 0.2)
        assert isinstance(prices, np.ndarray)
        assert len(prices) == 0

    def test_single_element_array(self):
        """Test single element array"""
        spots = np.array([100.0])
        prices = black_scholes.call_price_batch(spots, 100.0, 1.0, 0.05, 0.2)
        assert len(prices) == 1

        # Should match scalar calculation
        scalar_price = black_scholes.call_price(100.0, 100.0, 1.0, 0.05, 0.2)
        np.testing.assert_allclose(prices[0], scalar_price, rtol=1e-10)

    def test_shape_mismatch_error(self):
        """Test that shape mismatch raises appropriate error"""
        spots = np.array([90, 100])  # 2 elements
        strikes = np.array([95, 100, 105])  # 3 elements

        # Should raise error about shape mismatch
        with pytest.raises((ValueError, Exception)) as exc_info:
            black_scholes.call_price_batch(spots, strikes, 1.0, 0.05, 0.2)
        assert "shape" in str(exc_info.value).lower() or "broadcast" in str(exc_info.value).lower()

    def test_boolean_conversion(self):
        """Test boolean values in is_call parameter"""
        spots = np.array([100.0, 100.0])
        is_calls = [True, False]  # Boolean list

        greeks = black_scholes.greeks_batch(spots, 100.0, 1.0, 0.05, 0.2, is_calls)
        assert "delta" in greeks
        assert len(greeks["delta"]) == 2

        # First should be call delta (positive), second put delta (negative)
        assert greeks["delta"][0] > 0  # Call delta
        assert greeks["delta"][1] < 0  # Put delta

    def test_integer_array_conversion(self):
        """Test integer array conversion to float"""
        spots = np.array([90, 100, 110], dtype=np.int32)
        prices = black_scholes.call_price_batch(spots, 100, 1, 0.05, 0.2)
        assert len(prices) == 3
        assert all(p > 0 for p in prices)

    def test_black76_array_conversion(self):
        """Test array conversion for Black76 model"""
        forwards = [90.0, 100.0, 110.0]
        prices = black76.call_price_batch(forwards, 100.0, 1.0, 0.05, 0.2)
        assert len(prices) == 3
        assert all(p > 0 for p in prices)

    def test_merton_array_conversion(self):
        """Test array conversion for Merton model"""
        spots = np.array([90.0, 100.0, 110.0])
        dividend_yields = [0.01, 0.02, 0.03]  # List input

        prices = merton.call_price_batch(spots, 100.0, 1.0, 0.05, dividend_yields, 0.2)
        assert len(prices) == 3
        assert all(p > 0 for p in prices)

    def test_large_array_conversion(self):
        """Test conversion of large arrays"""
        size = 1_000_000
        spots = np.random.uniform(80, 120, size)

        prices = black_scholes.call_price_batch(spots, 100.0, 1.0, 0.05, 0.2)
        assert len(prices) == size
        assert np.all(np.isfinite(prices))

    def test_list_of_lists_rejection(self):
        """Test that nested lists are properly rejected"""
        nested = [[100.0], [110.0]]

        with pytest.raises((TypeError, ValueError)):
            black_scholes.call_price_batch(nested, 100.0, 1.0, 0.05, 0.2)
