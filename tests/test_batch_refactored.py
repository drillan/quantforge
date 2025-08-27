"""Refactored batch processing tests using base classes."""

import numpy as np
import pytest
from quantforge.models import american, black76, black_scholes, merton
from test_base import BaseBatchTest


class TestBlackScholesBatchRefactored(BaseBatchTest):
    """Test batch processing for Black-Scholes model."""

    @property
    def model(self):
        """Get Black-Scholes model instance."""
        return black_scholes

    def test_put_call_parity(self) -> None:
        """Test put-call parity for Black-Scholes."""
        arrays = self.create_test_arrays(n=5)

        call_prices = self.model.call_price_batch(**arrays)
        put_prices = self.model.put_price_batch(**arrays)

        # Put-call parity: C - P = S - K * exp(-r*t)
        spots = arrays["spots"]
        strikes = arrays["strikes"]
        rates = arrays["rates"]
        times = arrays["times"]

        for i in range(len(spots)):
            lhs = call_prices[i] - put_prices[i]
            rhs = spots[i] - strikes[i] * np.exp(-rates[i] * times[i])
            assert abs(lhs - rhs) < 1e-10, f"Put-call parity failed at index {i}"


class TestBlack76BatchRefactored(BaseBatchTest):
    """Test batch processing for Black76 model."""

    @property
    def model(self):
        """Get Black76 model instance."""
        return black76

    def create_test_arrays(self, n: int = 5, broadcast: bool = False):
        """Create test arrays for Black76 (uses forwards instead of spots)."""
        if broadcast:
            return {
                "forwards": np.array([75.0]),
                "strikes": np.array([75.0]),
                "times": np.array([0.5]),
                "rates": np.array([0.05]),
                "sigmas": np.array([0.25]),
            }
        else:
            return {
                "forwards": np.linspace(70.0, 80.0, n),
                "strikes": np.full(n, 75.0),
                "times": np.full(n, 0.5),
                "rates": np.full(n, 0.05),
                "sigmas": np.full(n, 0.25),
            }

    def test_put_call_parity(self) -> None:
        """Test put-call parity for Black76."""
        arrays = self.create_test_arrays(n=5)

        # Note: Black76 expects 'forwards' not 'spots'
        call_prices = self.model.call_price_batch(**arrays)
        put_prices = self.model.put_price_batch(**arrays)

        # Put-call parity for Black76: C - P = exp(-r*t) * (F - K)
        forwards = arrays["forwards"]
        strikes = arrays["strikes"]
        rates = arrays["rates"]
        times = arrays["times"]

        for i in range(len(forwards)):
            lhs = call_prices[i] - put_prices[i]
            rhs = np.exp(-rates[i] * times[i]) * (forwards[i] - strikes[i])
            assert abs(lhs - rhs) < 1e-10, f"Put-call parity failed at index {i}"


class TestMertonBatchRefactored(BaseBatchTest):
    """Test batch processing for Merton model."""

    @property
    def model(self):
        """Get Merton model instance."""
        return merton

    def create_test_arrays(self, n: int = 5, broadcast: bool = False):
        """Create test arrays for Merton (includes dividends)."""
        base_arrays = super().create_test_arrays(n, broadcast)
        # Add dividend yield
        if broadcast:
            base_arrays["dividends"] = np.array([0.02])
        else:
            base_arrays["dividends"] = np.full(n, 0.02)
        return base_arrays

    def test_dividend_sensitivity(self) -> None:
        """Test that option prices respond correctly to dividends."""
        arrays = self.create_test_arrays(n=3)

        # Calculate with different dividend yields
        arrays_no_div = arrays.copy()
        arrays_no_div["dividends"] = np.zeros(3)

        calls_no_div = self.model.call_price_batch(**arrays_no_div)
        calls_with_div = self.model.call_price_batch(**arrays)

        puts_no_div = self.model.put_price_batch(**arrays_no_div)
        puts_with_div = self.model.put_price_batch(**arrays)

        # Calls should decrease with dividends
        assert all(calls_with_div[i] < calls_no_div[i] for i in range(len(calls_no_div))), (
            "Call prices should decrease with dividends"
        )

        # Puts should increase with dividends
        assert all(puts_with_div[i] > puts_no_div[i] for i in range(len(puts_no_div))), (
            "Put prices should increase with dividends"
        )


class TestAmericanBatchRefactored(BaseBatchTest):
    """Test batch processing for American model."""

    @property
    def model(self):
        """Get American model instance."""
        return american

    def create_test_arrays(self, n: int = 5, broadcast: bool = False):
        """Create test arrays for American (includes dividends)."""
        base_arrays = super().create_test_arrays(n, broadcast)
        # Add dividend yield
        if broadcast:
            base_arrays["dividends"] = np.array([0.02])
        else:
            base_arrays["dividends"] = np.full(n, 0.02)
        return base_arrays

    def test_early_exercise_premium(self) -> None:
        """Test that American options have early exercise premium."""
        arrays = self.create_test_arrays(n=5)

        # American prices
        am_calls = self.model.call_price_batch(**arrays)
        am_puts = self.model.put_price_batch(**arrays)

        # European prices (using Merton as proxy)
        eu_calls = merton.call_price_batch(**arrays)
        eu_puts = merton.put_price_batch(**arrays)

        # American should be >= European
        assert all(am_calls[i] >= eu_calls[i] - 1e-10 for i in range(len(am_calls))), (
            "American calls should be >= European calls"
        )

        assert all(am_puts[i] >= eu_puts[i] - 1e-10 for i in range(len(am_puts))), (
            "American puts should be >= European puts"
        )

    def test_exercise_boundary(self) -> None:
        """Test exercise boundary calculation."""
        if hasattr(self.model, "exercise_boundary_batch"):
            arrays = self.create_test_arrays(n=5)
            arrays["is_calls"] = np.array([1.0, 1.0, 0.0, 0.0, 1.0])

            boundaries = self.model.exercise_boundary_batch(**arrays)

            assert len(boundaries) == 5
            assert all(b > 0 or np.isnan(b) for b in boundaries), "Boundaries should be positive or NaN"


# Helper function for parameterized tests
def get_all_models():
    """Get all model instances for parameterized testing."""
    return [
        (black_scholes, "black_scholes"),
        (black76, "black76"),
        (merton, "merton"),
        (american, "american"),
    ]


class TestGenericBatchOperations:
    """Generic batch operations that apply to all models."""

    @pytest.mark.parametrize("model,name", get_all_models())
    def test_batch_size_consistency(self, model, name: str) -> None:
        """Test that batch functions return correct size."""
        # Create appropriate arrays based on model
        if name == "black76":
            arrays = {
                "forwards": np.linspace(70, 80, 10),
                "strikes": np.full(10, 75.0),
                "times": np.full(10, 0.5),
                "rates": np.full(10, 0.05),
                "sigmas": np.full(10, 0.25),
            }
        else:
            arrays = {
                "spots": np.linspace(90, 110, 10),
                "strikes": np.full(10, 100.0),
                "times": np.full(10, 1.0),
                "rates": np.full(10, 0.05),
                "sigmas": np.full(10, 0.2),
            }

            if name in ["merton", "american"]:
                arrays["dividends"] = np.full(10, 0.02)

        if hasattr(model, "call_price_batch"):
            prices = model.call_price_batch(**arrays)
            assert len(prices) == 10, f"{name}: Batch size mismatch"

    @pytest.mark.parametrize("model,name", get_all_models())
    def test_no_negative_prices(self, model, name: str) -> None:
        """Test that no negative prices are returned."""
        # Create appropriate arrays based on model
        if name == "black76":
            arrays = {
                "forwards": np.random.uniform(50, 100, 20),
                "strikes": np.random.uniform(50, 100, 20),
                "times": np.random.uniform(0.1, 2.0, 20),
                "rates": np.random.uniform(0.01, 0.10, 20),
                "sigmas": np.random.uniform(0.1, 0.5, 20),
            }
        else:
            arrays = {
                "spots": np.random.uniform(50, 150, 20),
                "strikes": np.random.uniform(50, 150, 20),
                "times": np.random.uniform(0.1, 2.0, 20),
                "rates": np.random.uniform(0.01, 0.10, 20),
                "sigmas": np.random.uniform(0.1, 0.5, 20),
            }

            if name in ["merton", "american"]:
                arrays["dividends"] = np.random.uniform(0.0, 0.05, 20)

        if hasattr(model, "call_price_batch"):
            call_prices = model.call_price_batch(**arrays)
            assert all(p >= 0 or np.isnan(p) for p in call_prices), f"{name}: Negative call price detected"

        if hasattr(model, "put_price_batch"):
            put_prices = model.put_price_batch(**arrays)
            assert all(p >= 0 or np.isnan(p) for p in put_prices), f"{name}: Negative put price detected"
