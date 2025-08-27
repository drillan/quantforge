"""Base test classes for option pricing models."""

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
from numpy.typing import NDArray


class BaseModelTest(ABC):
    """Base class for model testing with common test patterns.

    This eliminates duplication across model test files.
    """

    @property
    @abstractmethod
    def model(self) -> Any:
        """Get the model instance to test."""
        ...

    @property
    @abstractmethod
    def test_spot(self) -> float:
        """Standard spot price for testing."""
        ...

    @property
    @abstractmethod
    def test_strike(self) -> float:
        """Standard strike price for testing."""
        ...

    @property
    @abstractmethod
    def test_time(self) -> float:
        """Standard time to maturity for testing."""
        ...

    @property
    @abstractmethod
    def test_rate(self) -> float:
        """Standard risk-free rate for testing."""
        ...

    @property
    @abstractmethod
    def test_sigma(self) -> float:
        """Standard volatility for testing."""
        ...

    @property
    def test_dividend(self) -> float | None:
        """Standard dividend yield for testing (if applicable)."""
        return None

    def get_test_params(self) -> dict[str, float]:
        """Get standard test parameters as a dictionary."""
        params = {
            "spot": self.test_spot,
            "strike": self.test_strike,
            "time": self.test_time,
            "rate": self.test_rate,
            "sigma": self.test_sigma,
        }
        if self.test_dividend is not None:
            params["dividend"] = self.test_dividend
        return params

    def test_call_price_positive(self) -> None:
        """Test that call price is always positive."""
        params = self.get_test_params()
        if hasattr(self.model, "call_price"):
            price = self.model.call_price(**params)
            assert price >= 0.0, f"Call price must be non-negative, got {price}"

    def test_put_price_positive(self) -> None:
        """Test that put price is always positive."""
        params = self.get_test_params()
        if hasattr(self.model, "put_price"):
            price = self.model.put_price(**params)
            assert price >= 0.0, f"Put price must be non-negative, got {price}"

    def test_call_intrinsic_value(self) -> None:
        """Test that call price is at least intrinsic value."""
        params = self.get_test_params()
        if hasattr(self.model, "call_price"):
            price = self.model.call_price(**params)
            intrinsic = max(0, params["spot"] - params["strike"])
            assert price >= intrinsic - 1e-10, f"Call price {price} less than intrinsic value {intrinsic}"

    def test_put_intrinsic_value(self) -> None:
        """Test that put price is at least intrinsic value."""
        params = self.get_test_params()
        if hasattr(self.model, "put_price"):
            price = self.model.put_price(**params)
            intrinsic = max(0, params["strike"] - params["spot"])
            assert price >= intrinsic - 1e-10, f"Put price {price} less than intrinsic value {intrinsic}"

    def test_batch_consistency(self) -> None:
        """Test that batch functions match single calculations."""
        params = self.get_test_params()

        # Test call price batch
        if hasattr(self.model, "call_price") and hasattr(self.model, "call_price_batch"):
            single = self.model.call_price(**params)

            # Create arrays for batch
            batch_params = {
                k: np.array([v])
                for k, v in params.items()
                if k != "dividend"  # Handle dividend separately if needed
            }
            if "dividend" in params:
                batch_params["dividends"] = np.array([params["dividend"]])

            batch = self.model.call_price_batch(**batch_params)
            assert len(batch) == 1
            assert abs(batch[0] - single) < 1e-10, f"Batch result {batch[0]} doesn't match single {single}"

    def test_greeks_structure(self) -> None:
        """Test that Greeks have the expected structure."""
        params = self.get_test_params()

        if hasattr(self.model, "greeks"):
            # Add is_call parameter
            greeks = self.model.greeks(**params, is_call=True)

            # Check that all expected Greeks are present
            expected_greeks = ["delta", "gamma", "vega", "theta", "rho"]
            for greek in expected_greeks:
                assert greek in greeks, f"Missing Greek: {greek}"
                assert isinstance(greeks[greek], int | float), (
                    f"Greek {greek} should be numeric, got {type(greeks[greek])}"
                )

    def test_implied_volatility_recovery(self) -> None:
        """Test that IV calculation recovers the input volatility."""
        params = self.get_test_params()

        if hasattr(self.model, "call_price") and hasattr(self.model, "implied_volatility"):
            # Calculate price with known volatility
            price = self.model.call_price(**params)

            # Recover volatility from price
            iv_params = params.copy()
            del iv_params["sigma"]  # Remove sigma from params

            recovered_iv = self.model.implied_volatility(price=price, **iv_params, is_call=True)

            # Check recovery accuracy
            assert abs(recovered_iv - params["sigma"]) < 1e-3, (
                f"IV recovery failed: expected {params['sigma']}, got {recovered_iv}"
            )


class BaseBatchTest(ABC):
    """Base class for batch processing tests."""

    @property
    @abstractmethod
    def model(self) -> Any:
        """Get the model instance to test."""
        ...

    def create_test_arrays(self, n: int = 5, broadcast: bool = False) -> dict[str, NDArray[np.float64]]:
        """Create test arrays for batch processing.

        Args:
            n: Number of elements
            broadcast: If True, create single-element arrays for broadcasting

        Returns:
            Dictionary of test arrays
        """
        if broadcast:
            return {
                "spots": np.array([100.0]),
                "strikes": np.array([100.0]),
                "times": np.array([1.0]),
                "rates": np.array([0.05]),
                "sigmas": np.array([0.2]),
            }
        else:
            return {
                "spots": np.linspace(90.0, 110.0, n),
                "strikes": np.full(n, 100.0),
                "times": np.full(n, 1.0),
                "rates": np.full(n, 0.05),
                "sigmas": np.full(n, 0.2),
            }

    def test_batch_call_prices(self) -> None:
        """Test batch call price calculation."""
        if hasattr(self.model, "call_price_batch"):
            arrays = self.create_test_arrays(n=5)
            prices = self.model.call_price_batch(**arrays)

            assert len(prices) == 5
            assert all(p >= 0 for p in prices), "All prices must be non-negative"
            assert not np.any(np.isnan(prices)), "No NaN values allowed"

    def test_batch_put_prices(self) -> None:
        """Test batch put price calculation."""
        if hasattr(self.model, "put_price_batch"):
            arrays = self.create_test_arrays(n=5)
            prices = self.model.put_price_batch(**arrays)

            assert len(prices) == 5
            assert all(p >= 0 for p in prices), "All prices must be non-negative"
            assert not np.any(np.isnan(prices)), "No NaN values allowed"

    def test_batch_broadcasting(self) -> None:
        """Test that broadcasting works correctly."""
        if hasattr(self.model, "call_price_batch"):
            # Full arrays
            full_arrays = self.create_test_arrays(n=3, broadcast=False)
            full_prices = self.model.call_price_batch(**full_arrays)

            # Broadcast arrays (single elements)
            broadcast_arrays = self.create_test_arrays(n=3, broadcast=True)
            broadcast_arrays["spots"] = np.linspace(90.0, 110.0, 3)
            broadcast_prices = self.model.call_price_batch(**broadcast_arrays)

            # Results should be the same
            np.testing.assert_array_almost_equal(
                full_prices, broadcast_prices, err_msg="Broadcasting produced different results"
            )

    def test_batch_greeks(self) -> None:
        """Test batch Greeks calculation."""
        if hasattr(self.model, "greeks_batch"):
            arrays = self.create_test_arrays(n=4)
            arrays["is_calls"] = np.array([1.0, 1.0, 0.0, 0.0])  # Mix of calls and puts

            greeks = self.model.greeks_batch(**arrays)

            assert isinstance(greeks, dict), "Greeks should be a dictionary"
            for key in ["delta", "gamma", "vega", "theta", "rho"]:
                assert key in greeks, f"Missing Greek: {key}"
                assert len(greeks[key]) == 4, f"Greek {key} has wrong length"
                assert not np.any(np.isnan(greeks[key])), f"Greek {key} contains NaN"
