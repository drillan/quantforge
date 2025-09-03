"""Refactored batch processing tests using base classes."""

from typing import Any

import numpy as np
import pytest
from quantforge import black76, black_scholes, merton

from tests.test_base import BaseBatchTest


class TestBlackScholesBatchRefactored(BaseBatchTest):
    """Test batch processing for Black-Scholes model."""

    @property
    def model(self) -> Any:
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
    def model(self) -> Any:
        """Get Black76 model instance."""
        return black76

    def create_test_arrays(self, n: int = 5, broadcast: bool = False) -> dict[str, Any]:
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

    def test_batch_call_prices(self) -> None:
        """Test batch call price calculation for Black76."""
        arrays = self.create_test_arrays(n=5)
        prices = self.model.call_price_batch(
            arrays["forwards"], arrays["strikes"], arrays["times"], arrays["rates"], arrays["sigmas"]
        )
        assert len(prices) == 5
        assert all(p >= 0 for p in prices), "All prices must be non-negative"
        assert not np.any(np.isnan(prices)), "No NaN values allowed"

    def test_batch_put_prices(self) -> None:
        """Test batch put price calculation for Black76."""
        arrays = self.create_test_arrays(n=5)
        prices = self.model.put_price_batch(
            arrays["forwards"], arrays["strikes"], arrays["times"], arrays["rates"], arrays["sigmas"]
        )
        assert len(prices) == 5
        assert all(p >= 0 for p in prices), "All prices must be non-negative"
        assert not np.any(np.isnan(prices)), "No NaN values allowed"

    def test_batch_broadcasting(self) -> None:
        """Test that broadcasting works correctly for Black76."""
        # Full arrays
        full_arrays = self.create_test_arrays(n=3, broadcast=False)
        full_prices = self.model.call_price_batch(
            full_arrays["forwards"],
            full_arrays["strikes"],
            full_arrays["times"],
            full_arrays["rates"],
            full_arrays["sigmas"],
        )

        # Broadcast arrays (single elements)
        broadcast_arrays = self.create_test_arrays(n=3, broadcast=True)
        broadcast_arrays["forwards"] = np.linspace(70.0, 80.0, 3)
        broadcast_prices = self.model.call_price_batch(
            broadcast_arrays["forwards"],
            broadcast_arrays["strikes"],
            broadcast_arrays["times"],
            broadcast_arrays["rates"],
            broadcast_arrays["sigmas"],
        )

        # Results should be the same
        np.testing.assert_array_almost_equal(
            full_prices, broadcast_prices, err_msg="Broadcasting produced different results"
        )

    def test_batch_greeks(self) -> None:
        """Test batch Greeks calculation for Black76."""
        arrays = self.create_test_arrays(n=4)
        is_calls = np.array([1.0, 1.0, 0.0, 0.0])  # Mix of calls and puts

        greeks = self.model.greeks_batch(
            arrays["forwards"], arrays["strikes"], arrays["times"], arrays["rates"], arrays["sigmas"], is_calls
        )

        assert isinstance(greeks, dict), "Greeks should be a dictionary"
        for key in ["delta", "gamma", "vega", "theta", "rho"]:
            assert key in greeks, f"Missing Greek: {key}"
            assert len(greeks[key]) == 4, f"Greek {key} has wrong length"
            assert not np.any(np.isnan(greeks[key])), f"Greek {key} contains NaN"

    def test_put_call_parity(self) -> None:
        """Test put-call parity for Black76."""
        arrays = self.create_test_arrays(n=5)

        # Note: Black76 expects 'forwards' not 'spots' and uses positional args
        call_prices = self.model.call_price_batch(
            arrays["forwards"], arrays["strikes"], arrays["times"], arrays["rates"], arrays["sigmas"]
        )
        put_prices = self.model.put_price_batch(
            arrays["forwards"], arrays["strikes"], arrays["times"], arrays["rates"], arrays["sigmas"]
        )

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
    def model(self) -> Any:
        """Get Merton model instance."""
        return merton

    def create_test_arrays(self, n: int = 5, broadcast: bool = False) -> dict[str, Any]:
        """Create test arrays for Merton (includes dividends)."""
        base_arrays = super().create_test_arrays(n, broadcast)
        # Add dividend yield
        if broadcast:
            base_arrays["dividends"] = np.array([0.02])
        else:
            base_arrays["dividends"] = np.full(n, 0.02)
        return base_arrays

    def test_batch_call_prices(self) -> None:
        """Test batch call price calculation for Merton."""
        arrays = self.create_test_arrays(n=5)
        prices = self.model.call_price_batch(
            arrays["spots"], arrays["strikes"], arrays["times"], arrays["rates"], arrays["dividends"], arrays["sigmas"]
        )
        assert len(prices) == 5
        assert all(p >= 0 for p in prices), "All prices must be non-negative"
        assert not np.any(np.isnan(prices)), "No NaN values allowed"

    def test_batch_put_prices(self) -> None:
        """Test batch put price calculation for Merton."""
        arrays = self.create_test_arrays(n=5)
        prices = self.model.put_price_batch(
            arrays["spots"], arrays["strikes"], arrays["times"], arrays["rates"], arrays["dividends"], arrays["sigmas"]
        )
        assert len(prices) == 5
        assert all(p >= 0 for p in prices), "All prices must be non-negative"
        assert not np.any(np.isnan(prices)), "No NaN values allowed"

    def test_batch_broadcasting(self) -> None:
        """Test that broadcasting works correctly for Merton."""
        # Full arrays
        full_arrays = self.create_test_arrays(n=3, broadcast=False)
        full_prices = self.model.call_price_batch(
            full_arrays["spots"],
            full_arrays["strikes"],
            full_arrays["times"],
            full_arrays["rates"],
            full_arrays["dividends"],
            full_arrays["sigmas"],
        )

        # Broadcast arrays (single elements)
        broadcast_arrays = self.create_test_arrays(n=3, broadcast=True)
        broadcast_arrays["spots"] = np.linspace(90.0, 110.0, 3)
        broadcast_prices = self.model.call_price_batch(
            broadcast_arrays["spots"],
            broadcast_arrays["strikes"],
            broadcast_arrays["times"],
            broadcast_arrays["rates"],
            broadcast_arrays["dividends"],
            broadcast_arrays["sigmas"],
        )

        # Results should be the same
        np.testing.assert_array_almost_equal(
            full_prices, broadcast_prices, err_msg="Broadcasting produced different results"
        )

    def test_batch_greeks(self) -> None:
        """Test batch Greeks calculation for Merton."""
        arrays = self.create_test_arrays(n=4)
        is_calls = np.array([1.0, 1.0, 0.0, 0.0])  # Mix of calls and puts

        greeks = self.model.greeks_batch(
            arrays["spots"],
            arrays["strikes"],
            arrays["times"],
            arrays["rates"],
            arrays["dividends"],
            arrays["sigmas"],
            is_calls,
        )

        assert isinstance(greeks, dict), "Greeks should be a dictionary"
        for key in ["delta", "gamma", "vega", "theta", "rho"]:
            assert key in greeks, f"Missing Greek: {key}"
            assert len(greeks[key]) == 4, f"Greek {key} has wrong length"
            assert not np.any(np.isnan(greeks[key])), f"Greek {key} contains NaN"

    def test_dividend_sensitivity(self) -> None:
        """Test that option prices respond correctly to dividends."""
        arrays = self.create_test_arrays(n=3)

        # Calculate with different dividend yields
        arrays_no_div = arrays.copy()
        arrays_no_div["dividends"] = np.zeros(3)

        calls_no_div = self.model.call_price_batch(
            arrays_no_div["spots"],
            arrays_no_div["strikes"],
            arrays_no_div["times"],
            arrays_no_div["rates"],
            arrays_no_div["dividends"],
            arrays_no_div["sigmas"],
        )
        calls_with_div = self.model.call_price_batch(
            arrays["spots"], arrays["strikes"], arrays["times"], arrays["rates"], arrays["dividends"], arrays["sigmas"]
        )

        puts_no_div = self.model.put_price_batch(
            arrays_no_div["spots"],
            arrays_no_div["strikes"],
            arrays_no_div["times"],
            arrays_no_div["rates"],
            arrays_no_div["dividends"],
            arrays_no_div["sigmas"],
        )
        puts_with_div = self.model.put_price_batch(
            arrays["spots"], arrays["strikes"], arrays["times"], arrays["rates"], arrays["dividends"], arrays["sigmas"]
        )

        # Calls should decrease with dividends
        assert all(calls_with_div[i] < calls_no_div[i] for i in range(len(calls_no_div))), (
            "Call prices should decrease with dividends"
        )

        # Puts should increase with dividends
        assert all(puts_with_div[i] > puts_no_div[i] for i in range(len(puts_no_div))), (
            "Put prices should increase with dividends"
        )


# class TestAmericanBatchRefactored(BaseBatchTest): # TODO: Re-enable when American option is implemented
#     """Test batch processing for American model."""

#     @property
#     def model(self) -> Any:
#         """Get American model instance."""
#         return black_scholes.american

#     def create_test_arrays(self, n: int = 5, broadcast: bool = False) -> dict[str, Any]:
#         """Create test arrays for American (includes dividends)."""
#         base_arrays = super().create_test_arrays(n, broadcast)
# Add dividend yield
#         if broadcast:
#             base_arrays["dividends"] = np.array([0.02])
#         else:
#             base_arrays["dividends"] = np.full(n, 0.02)
#         return base_arrays

#     def test_batch_call_prices(self) -> None:
#         """Test batch call price calculation for American."""
#         arrays = self.create_test_arrays(n=5)
#         prices = self.model.call_price_batch(
#             arrays["spots"], arrays["strikes"], arrays["times"],
#             arrays["rates"], arrays["dividends"], arrays["sigmas"]
#         )
#         assert len(prices) == 5
#         assert all(p >= 0 for p in prices), "All prices must be non-negative"
#         assert not np.any(np.isnan(prices)), "No NaN values allowed"

#     def test_batch_put_prices(self) -> None:
#         """Test batch put price calculation for American."""
#         arrays = self.create_test_arrays(n=5)
#         prices = self.model.put_price_batch(
#             arrays["spots"], arrays["strikes"], arrays["times"],
#             arrays["rates"], arrays["dividends"], arrays["sigmas"]
#         )
#         assert len(prices) == 5
#         assert all(p >= 0 for p in prices), "All prices must be non-negative"
#         assert not np.any(np.isnan(prices)), "No NaN values allowed"

#     def test_batch_broadcasting(self) -> None:
#         """Test that broadcasting works correctly for American."""
# Full arrays
#         full_arrays = self.create_test_arrays(n=3, broadcast=False)
#         full_prices = self.model.call_price_batch(
#             full_arrays["spots"],
#             full_arrays["strikes"],
#             full_arrays["times"],
#             full_arrays["rates"],
#             full_arrays["dividends"],
#             full_arrays["sigmas"],
#         )

# Broadcast arrays (single elements)
#         broadcast_arrays = self.create_test_arrays(n=3, broadcast=True)
#         broadcast_arrays["spots"] = np.linspace(90.0, 110.0, 3)
#         broadcast_prices = self.model.call_price_batch(
#             broadcast_arrays["spots"],
#             broadcast_arrays["strikes"],
#             broadcast_arrays["times"],
#             broadcast_arrays["rates"],
#             broadcast_arrays["dividends"],
#             broadcast_arrays["sigmas"],
#         )

# Results should be the same
#         np.testing.assert_array_almost_equal(
#             full_prices, broadcast_prices, err_msg="Broadcasting produced different results"
#         )

#     def test_batch_greeks(self) -> None:
#         """Test batch Greeks calculation for American."""
#         arrays = self.create_test_arrays(n=4)
#         is_calls = np.array([1.0, 1.0, 0.0, 0.0])  # Mix of calls and puts

#         greeks = self.model.greeks_batch(
#             arrays["spots"],
#             arrays["strikes"],
#             arrays["times"],
#             arrays["rates"],
#             arrays["dividends"],
#             arrays["sigmas"],
#             is_calls,
#         )

#         assert isinstance(greeks, dict), "Greeks should be a dictionary"
#         for key in ["delta", "gamma", "vega", "theta", "rho"]:
#             assert key in greeks, f"Missing Greek: {key}"
#             assert len(greeks[key]) == 4, f"Greek {key} has wrong length"
#             assert not np.any(np.isnan(greeks[key])), f"Greek {key} contains NaN"

#     @pytest.mark.skip(reason="American option implementation issue - needs investigation")
#     def test_early_exercise_premium(self) -> None:
#         """Test that American options have early exercise premium."""
#         arrays = self.create_test_arrays(n=5)

# American prices
#         am_calls = self.model.call_price_batch(
#             arrays["spots"], arrays["strikes"], arrays["times"],
#             arrays["rates"], arrays["dividends"], arrays["sigmas"]
#         )
#         am_puts = self.model.put_price_batch(
#             arrays["spots"], arrays["strikes"], arrays["times"],
#             arrays["rates"], arrays["dividends"], arrays["sigmas"]
#         )

# European prices (using Merton as proxy)
#         eu_calls = merton.call_price_batch(
#             arrays["spots"], arrays["strikes"], arrays["times"],
#             arrays["rates"], arrays["dividends"], arrays["sigmas"]
#         )
#         eu_puts = merton.put_price_batch(
#             arrays["spots"], arrays["strikes"], arrays["times"],
#             arrays["rates"], arrays["dividends"], arrays["sigmas"]
#         )

# American should be >= European
#         assert all(am_calls[i] >= eu_calls[i] - 1e-10 for i in range(len(am_calls))), (
#             "American calls should be >= European calls"
#         )

#         assert all(am_puts[i] >= eu_puts[i] - 1e-10 for i in range(len(am_puts))), (
#             "American puts should be >= European puts"
#         )

#     def test_exercise_boundary(self) -> None:
#         """Test exercise boundary calculation."""
#         if hasattr(self.model, "exercise_boundary_batch"):
#             arrays = self.create_test_arrays(n=5)
#             is_calls = np.array([1.0, 1.0, 0.0, 0.0, 1.0])

#             boundaries = self.model.exercise_boundary_batch(
#                 arrays["spots"],
#                 arrays["strikes"],
#                 arrays["times"],
#                 arrays["rates"],
#                 arrays["dividends"],
#                 arrays["sigmas"],
#                 is_calls,
#             )

#             assert len(boundaries) == 5
#             assert all(b > 0 or np.isnan(b) for b in boundaries), "Boundaries should be positive or NaN"


# Helper function for parameterized tests
# def get_all_models() -> list[tuple[Any, str]]:
#     """Get all model instances for parameterized testing."""
#     return [
#         (models, "models"),
#         (models.black76, "models.black76"),
#         (models.merton, "models.merton"),
#         (black_scholes.american, "black_scholes.american"),
#     ]


def get_all_models() -> list[tuple[Any, str]]:
    """Get all model instances for parameterized testing."""
    return [
        (black_scholes, "black_scholes"),
        (black76, "black76"),
        (merton, "merton"),
        # (american, "american"),  # TODO: Re-enable when American option is implemented
    ]


class TestGenericBatchOperations:
    """Generic batch operations that apply to all models."""

    @pytest.mark.parametrize("model,name", get_all_models())
    def test_batch_size_consistency(self, model: Any, name: str) -> None:
        """Test that batch functions return correct size."""
        # Create appropriate arrays based on model
        if name == "black76":
            forwards = np.linspace(70, 80, 10)
            strikes = np.full(10, 75.0)
            times = np.full(10, 0.5)
            rates = np.full(10, 0.05)
            sigmas = np.full(10, 0.25)

            if hasattr(model, "call_price_batch"):
                prices = model.call_price_batch(forwards, strikes, times, rates, sigmas)
                assert len(prices) == 10, f"{name}: Batch size mismatch"
        elif name == "models":
            spots = np.linspace(90, 110, 10)
            strikes = np.full(10, 100.0)
            times = np.full(10, 1.0)
            rates = np.full(10, 0.05)
            sigmas = np.full(10, 0.2)

            if hasattr(model, "call_price_batch"):
                prices = model.call_price_batch(spots, strikes, times, rates, sigmas)
                assert len(prices) == 10, f"{name}: Batch size mismatch"
        elif name in ["merton"]:  # TODO: Add "american" when implemented
            spots = np.linspace(90, 110, 10)
            strikes = np.full(10, 100.0)
            times = np.full(10, 1.0)
            rates = np.full(10, 0.05)
            dividends = np.full(10, 0.02)
            sigmas = np.full(10, 0.2)

            if hasattr(model, "call_price_batch"):
                prices = model.call_price_batch(spots, strikes, times, rates, dividends, sigmas)
                assert len(prices) == 10, f"{name}: Batch size mismatch"

    @pytest.mark.parametrize("model,name", get_all_models())
    def test_no_negative_prices(self, model: Any, name: str) -> None:
        """Test that no negative prices are returned."""
        # Create appropriate arrays based on model
        if name == "models.black76":
            forwards = np.random.uniform(50, 100, 20)
            strikes = np.random.uniform(50, 100, 20)
            times = np.random.uniform(0.1, 2.0, 20)
            rates = np.random.uniform(0.01, 0.10, 20)
            sigmas = np.random.uniform(0.1, 0.5, 20)

            if hasattr(model, "call_price_batch"):
                call_prices = model.call_price_batch(forwards, strikes, times, rates, sigmas)
                assert all(p >= 0 or np.isnan(p) for p in call_prices), f"{name}: Negative call price detected"

            if hasattr(model, "put_price_batch"):
                put_prices = model.put_price_batch(forwards, strikes, times, rates, sigmas)
                assert all(p >= 0 or np.isnan(p) for p in put_prices), f"{name}: Negative put price detected"
        elif name == "models":
            spots = np.random.uniform(50, 150, 20)
            strikes = np.random.uniform(50, 150, 20)
            times = np.random.uniform(0.1, 2.0, 20)
            rates = np.random.uniform(0.01, 0.10, 20)
            sigmas = np.random.uniform(0.1, 0.5, 20)

            if hasattr(model, "call_price_batch"):
                call_prices = model.call_price_batch(spots, strikes, times, rates, sigmas)
                assert all(p >= 0 or np.isnan(p) for p in call_prices), f"{name}: Negative call price detected"

            if hasattr(model, "put_price_batch"):
                put_prices = model.put_price_batch(spots, strikes, times, rates, sigmas)
                assert all(p >= 0 or np.isnan(p) for p in put_prices), f"{name}: Negative put price detected"
        elif name in ["merton"]:  # TODO: Add "american" when implemented
            spots = np.random.uniform(50, 150, 20)
            strikes = np.random.uniform(50, 150, 20)
            times = np.random.uniform(0.1, 2.0, 20)
            rates = np.random.uniform(0.01, 0.10, 20)
            dividends = np.random.uniform(0.0, 0.05, 20)
            sigmas = np.random.uniform(0.1, 0.5, 20)

            if hasattr(model, "call_price_batch"):
                call_prices = model.call_price_batch(spots, strikes, times, rates, dividends, sigmas)
                assert all(p >= 0 or np.isnan(p) for p in call_prices), f"{name}: Negative call price detected"

            if hasattr(model, "put_price_batch"):
                put_prices = model.put_price_batch(spots, strikes, times, rates, dividends, sigmas)
                assert all(p >= 0 or np.isnan(p) for p in put_prices), f"{name}: Negative put price detected"
