"""Comprehensive base testing framework for QuantForge models.

This module provides base classes and utilities to eliminate code duplication
across test files while maintaining full test coverage.
"""

from abc import ABC
from typing import Any, Protocol, TypeVar

import numpy as np
import pytest
from numpy.typing import NDArray

from tests.conftest import (
    NUMERICAL_TOLERANCE,
    PRACTICAL_TOLERANCE,
    THEORETICAL_TOLERANCE,
    arrow,
)

# Type definitions
ArrayLike = NDArray[np.float64] | list[float] | float
TestArrays = dict[str, ArrayLike]


def to_numpy_array(arr: Any) -> NDArray[np.float64]:
    """Convert any array-like object to NumPy array.

    Handles arro3 Arrow arrays that are returned from batch functions.
    For compatibility, use arrow.to_list() then convert to numpy.
    """
    if arrow.is_arrow(arr):
        return np.array(arrow.to_list(arr), dtype=np.float64)
    return np.asarray(arr, dtype=np.float64)


# Standard test data constants
DEFAULT_SPOT = 100.0
DEFAULT_STRIKE = 100.0
DEFAULT_TIME = 1.0
DEFAULT_RATE = 0.05
DEFAULT_SIGMA = 0.2
DEFAULT_DIVIDEND = 0.02

# Batch test size constants
SMALL_BATCH_SIZE = 5
MEDIUM_BATCH_SIZE = 100
LARGE_BATCH_SIZE = 10000


class ModelProtocol(Protocol):
    """Protocol for option pricing models."""

    def call_price(self, **kwargs: Any) -> float:
        """Calculate call option price."""
        ...

    def put_price(self, **kwargs: Any) -> float:
        """Calculate put option price."""
        ...

    def call_price_batch(self, **kwargs: Any) -> NDArray[np.float64]:
        """Calculate batch call prices."""
        ...

    def put_price_batch(self, **kwargs: Any) -> NDArray[np.float64]:
        """Calculate batch put prices."""
        ...

    def greeks(self, **kwargs: Any) -> dict[str, float]:
        """Calculate option Greeks."""
        ...

    def greeks_batch(self, **kwargs: Any) -> dict[str, NDArray[np.float64]]:
        """Calculate batch Greeks."""
        ...

    def implied_volatility(self, **kwargs: Any) -> float:
        """Calculate implied volatility."""
        ...

    def implied_volatility_batch(self, **kwargs: Any) -> NDArray[np.float64]:
        """Calculate batch implied volatility."""
        ...


class BaseModelTest(ABC):
    """Abstract base class for all model tests.

    This class provides common test methods that work across all models,
    eliminating the need for duplicate test implementations.
    """

    # Model configuration (override in subclasses)
    model: ModelProtocol
    use_forward_price: bool = False  # True for Black76
    has_dividend: bool = False  # True for Merton

    # Default test parameters (can be overridden)
    default_spot: float = DEFAULT_SPOT
    default_strike: float = DEFAULT_STRIKE
    default_time: float = DEFAULT_TIME
    default_rate: float = DEFAULT_RATE
    default_sigma: float = DEFAULT_SIGMA
    default_dividend: float = DEFAULT_DIVIDEND

    def get_price_param_name(self) -> str:
        """Get the parameter name for underlying price (s, f for parameters)."""
        return "f" if self.use_forward_price else "s"

    def get_default_params(self, **overrides: Any) -> dict[str, Any]:
        """Get default parameters for testing with optional overrides."""
        price_key = self.get_price_param_name()

        params = {
            price_key: self.default_spot,
            "k": self.default_strike,
            "t": self.default_time,
            "r": self.default_rate,
            "sigma": self.default_sigma,
        }

        if self.has_dividend:
            params["q"] = self.default_dividend

        params.update(overrides)
        return params

    def get_batch_params(
        self, n: int = SMALL_BATCH_SIZE, broadcasting: bool = False, **overrides: Any
    ) -> dict[str, Any]:
        """Generate parameters for batch testing."""
        # Map singular to plural for batch APIs
        price_key = "forwards" if self.use_forward_price else "spots"

        if broadcasting:
            # Create arrays with different shapes for broadcasting test
            params = {
                price_key: np.linspace(90.0, 110.0, n),
                "strikes": np.array([self.default_strike]),  # Broadcast
                "times": np.array([self.default_time]),
                "rates": np.array([self.default_rate]),
                "sigmas": np.array([self.default_sigma]),
            }
        else:
            # All arrays same size
            params = {
                price_key: np.linspace(90.0, 110.0, n),
                "strikes": np.full(n, self.default_strike),
                "times": np.full(n, self.default_time),
                "rates": np.full(n, self.default_rate),
                "sigmas": np.full(n, self.default_sigma),
            }

        if self.has_dividend:
            dividend_key = "dividend_yields" if price_key == "spots" else "dividend_yields"
            if broadcasting:
                params[dividend_key] = np.array([self.default_dividend])
            else:
                params[dividend_key] = np.full(n, self.default_dividend)

        params.update(overrides)
        return params

    # === Core Price Tests ===

    def test_call_price_positive(self) -> None:
        """Test that call prices are non-negative."""
        params = self.get_default_params()
        price = self.model.call_price(**params)
        assert price >= 0, f"Call price must be non-negative, got {price}"
        assert np.isfinite(price), "Call price must be finite"

    def test_put_price_positive(self) -> None:
        """Test that put prices are non-negative."""
        params = self.get_default_params()
        price = self.model.put_price(**params)
        assert price >= 0, f"Put price must be non-negative, got {price}"
        assert np.isfinite(price), "Put price must be finite"

    def test_call_intrinsic_value(self) -> None:
        """Test that call price >= intrinsic value."""
        params = self.get_default_params()
        price = self.model.call_price(**params)

        price_param = params.get("f" if self.use_forward_price else "s")
        strike = params["k"]

        if self.use_forward_price:
            # For Black76: intrinsic = e^(-rt) * max(F - K, 0)
            intrinsic = np.exp(-params["r"] * params["t"]) * max(0, price_param - strike)
        else:
            # For BS/Merton: intrinsic = max(S - K, 0)
            intrinsic = max(0, price_param - strike)

        assert price >= intrinsic - NUMERICAL_TOLERANCE, f"Call price {price} less than intrinsic value {intrinsic}"

    def test_put_intrinsic_value(self) -> None:
        """Test that put price >= intrinsic value."""
        params = self.get_default_params()
        price = self.model.put_price(**params)

        price_param = params.get("f" if self.use_forward_price else "s")
        strike = params["k"]

        if self.use_forward_price:
            # For Black76: intrinsic = e^(-rt) * max(K - F, 0)
            intrinsic = np.exp(-params["r"] * params["t"]) * max(0, strike - price_param)
        else:
            # For BS/Merton: intrinsic = max(K - S, 0)
            intrinsic = max(0, strike - price_param)

        assert price >= intrinsic - NUMERICAL_TOLERANCE, f"Put price {price} less than intrinsic value {intrinsic}"

    # === Put-Call Parity Tests ===

    def test_put_call_parity(self) -> None:
        """Test put-call parity relationship."""
        params = self.get_default_params()

        call_price = self.model.call_price(**params)
        put_price = self.model.put_price(**params)

        price_param = params.get("f" if self.use_forward_price else "s")
        strike = params["k"]
        rate = params["r"]
        time = params["t"]

        if self.use_forward_price:
            # Black76: C - P = e^(-rt) * (F - K)
            lhs = call_price - put_price
            rhs = np.exp(-rate * time) * (price_param - strike)
        elif self.has_dividend:
            # Merton: C - P = S*e^(-qt) - K*e^(-rt)
            dividend = params["q"]
            lhs = call_price - put_price
            rhs = price_param * np.exp(-dividend * time) - strike * np.exp(-rate * time)
        else:
            # Black-Scholes: C - P = S - K*e^(-rt)
            lhs = call_price - put_price
            rhs = price_param - strike * np.exp(-rate * time)

        assert abs(lhs - rhs) < NUMERICAL_TOLERANCE, f"Put-call parity failed: {lhs} != {rhs}"

    # === Batch Processing Tests ===

    def test_batch_call_prices(self) -> None:
        """Test batch call price calculation."""
        params = self.get_batch_params(n=SMALL_BATCH_SIZE)
        prices = self.model.call_price_batch(**params)
        prices = to_numpy_array(prices)

        assert len(prices) == SMALL_BATCH_SIZE
        assert all(p >= 0 for p in prices), "All prices must be non-negative"
        assert np.all(np.isfinite(prices)), "All prices must be finite"

    def test_batch_put_prices(self) -> None:
        """Test batch put price calculation."""
        params = self.get_batch_params(n=SMALL_BATCH_SIZE)
        prices = self.model.put_price_batch(**params)
        prices = to_numpy_array(prices)

        assert len(prices) == SMALL_BATCH_SIZE
        assert all(p >= 0 for p in prices), "All prices must be non-negative"
        assert np.all(np.isfinite(prices)), "All prices must be finite"

    def test_batch_broadcasting(self) -> None:
        """Test NumPy-style broadcasting in batch operations."""
        # Get params with broadcasting
        broadcast_params = self.get_batch_params(n=SMALL_BATCH_SIZE, broadcasting=True)
        broadcast_prices = self.model.call_price_batch(**broadcast_params)
        broadcast_prices = to_numpy_array(broadcast_prices)

        # Get params without broadcasting (all same shape)
        full_params = self.get_batch_params(n=SMALL_BATCH_SIZE, broadcasting=False)
        full_prices = self.model.call_price_batch(**full_params)
        full_prices = to_numpy_array(full_prices)

        # Results should be the same (accounting for the different spot/forward values)
        assert len(broadcast_prices) == len(full_prices) == SMALL_BATCH_SIZE

    def test_batch_consistency(self) -> None:
        """Test consistency between single and batch calculations."""
        single_params = self.get_default_params()

        # Convert to batch params with single element
        price_key_single = self.get_price_param_name()  # 's' or 'f'
        price_key_batch = "forwards" if self.use_forward_price else "spots"
        batch_params = {
            price_key_batch: np.array([single_params[price_key_single]]),
            "strikes": np.array([single_params["k"]]),
            "times": np.array([single_params["t"]]),
            "rates": np.array([single_params["r"]]),
            "sigmas": np.array([single_params["sigma"]]),
        }

        if self.has_dividend:
            batch_params["dividend_yields"] = np.array([single_params["q"]])

        # Test call prices
        single_call = self.model.call_price(**single_params)
        batch_call = self.model.call_price_batch(**batch_params)
        batch_call = to_numpy_array(batch_call)
        assert len(batch_call) == 1
        assert abs(batch_call[0] - single_call) < NUMERICAL_TOLERANCE, (
            f"Batch call {batch_call[0]} != single call {single_call}"
        )

        # Test put prices
        single_put = self.model.put_price(**single_params)
        batch_put = self.model.put_price_batch(**batch_params)
        batch_put = to_numpy_array(batch_put)
        assert len(batch_put) == 1
        assert abs(batch_put[0] - single_put) < NUMERICAL_TOLERANCE, (
            f"Batch put {batch_put[0]} != single put {single_put}"
        )

    def test_batch_put_call_parity(self) -> None:
        """Test put-call parity in batch operations."""
        params = self.get_batch_params(n=SMALL_BATCH_SIZE)

        call_prices = self.model.call_price_batch(**params)
        call_prices = to_numpy_array(call_prices)
        put_prices = self.model.put_price_batch(**params)
        put_prices = to_numpy_array(put_prices)

        # Get the batch price key based on model type
        price_key = "forwards" if self.use_forward_price else "spots"
        prices = params[price_key]
        strikes = params["strikes"]
        rates = params["rates"]
        times = params["times"]

        # Ensure arrays for iteration
        prices = np.atleast_1d(prices)
        strikes = np.atleast_1d(strikes)
        rates = np.atleast_1d(rates)
        times = np.atleast_1d(times)

        # Handle broadcasting
        n = max(len(prices), len(strikes), len(rates), len(times))
        prices = np.broadcast_to(prices, n) if len(prices) == 1 else prices
        strikes = np.broadcast_to(strikes, n) if len(strikes) == 1 else strikes
        rates = np.broadcast_to(rates, n) if len(rates) == 1 else rates
        times = np.broadcast_to(times, n) if len(times) == 1 else times

        for i in range(n):
            if self.use_forward_price:
                # Black76
                lhs = call_prices[i] - put_prices[i]
                rhs = np.exp(-rates[i] * times[i]) * (prices[i] - strikes[i])
            elif self.has_dividend:
                # Merton
                dividends = params["dividend_yields"]
                dividends = np.atleast_1d(dividends)
                dividends = np.broadcast_to(dividends, n) if len(dividends) == 1 else dividends
                lhs = call_prices[i] - put_prices[i]
                rhs = prices[i] * np.exp(-dividends[i] * times[i]) - strikes[i] * np.exp(-rates[i] * times[i])
            else:
                # Black-Scholes
                lhs = call_prices[i] - put_prices[i]
                rhs = prices[i] - strikes[i] * np.exp(-rates[i] * times[i])

            assert abs(lhs - rhs) < THEORETICAL_TOLERANCE, f"Put-call parity failed at index {i}: {lhs} != {rhs}"

    # === Greeks Tests ===

    def test_greeks_structure(self) -> None:
        """Test that Greeks have correct structure and values."""
        params = self.get_default_params()
        params["is_call"] = True

        greeks = self.model.greeks(**params)

        # Check all expected Greeks are present
        expected_greeks = ["delta", "gamma", "vega", "theta", "rho"]
        if self.has_dividend:
            expected_greeks.append("dividend_rho")

        for greek in expected_greeks:
            assert greek in greeks, f"Missing Greek: {greek}"
            assert isinstance(greeks[greek], int | float), f"Greek {greek} should be numeric, got {type(greeks[greek])}"
            assert np.isfinite(greeks[greek]), f"Greek {greek} must be finite"

    def test_greeks_batch(self) -> None:
        """Test batch Greeks calculation."""
        params = self.get_batch_params(n=SMALL_BATCH_SIZE)
        params["is_call"] = True  # Greeks batch uses singular

        greeks = self.model.greeks_batch(**params)

        expected_greeks = ["delta", "gamma", "vega", "theta", "rho"]
        if self.has_dividend:
            expected_greeks.append("dividend_rho")

        for greek in expected_greeks:
            assert greek in greeks, f"Missing Greek: {greek}"
            greek_values = to_numpy_array(greeks[greek])
            assert len(greek_values) == SMALL_BATCH_SIZE, f"Greek {greek} has wrong size: {len(greek_values)}"
            assert np.all(np.isfinite(greek_values)), f"Greek {greek} contains non-finite values"

    def test_delta_bounds(self) -> None:
        """Test that delta is within theoretical bounds."""
        params = self.get_default_params()

        # Call delta should be in [0, 1]
        call_greeks = self.model.greeks(**params, is_call=True)
        assert 0 <= call_greeks["delta"] <= 1, f"Call delta {call_greeks['delta']} out of bounds [0, 1]"

        # Put delta should be in [-1, 0]
        put_greeks = self.model.greeks(**params, is_call=False)
        assert -1 <= put_greeks["delta"] <= 0, f"Put delta {put_greeks['delta']} out of bounds [-1, 0]"

    def test_gamma_positive(self) -> None:
        """Test that gamma is always positive."""
        params = self.get_default_params()

        for is_call in [True, False]:
            greeks = self.model.greeks(**params, is_call=is_call)
            assert greeks["gamma"] >= 0, f"{'Call' if is_call else 'Put'} gamma must be non-negative"

    def test_vega_positive(self) -> None:
        """Test that vega is always positive."""
        params = self.get_default_params()

        for is_call in [True, False]:
            greeks = self.model.greeks(**params, is_call=is_call)
            assert greeks["vega"] >= 0, f"{'Call' if is_call else 'Put'} vega must be non-negative"

    # === Implied Volatility Tests ===

    def test_implied_volatility_recovery(self) -> None:
        """Test that IV calculation recovers input volatility."""
        params = self.get_default_params()

        # Calculate price with known volatility
        call_price = self.model.call_price(**params)

        # Recover volatility
        iv_params = params.copy()
        del iv_params["sigma"]
        iv_params["price"] = call_price
        iv_params["is_call"] = True

        recovered_iv = self.model.implied_volatility(**iv_params)

        assert abs(recovered_iv - self.default_sigma) < THEORETICAL_TOLERANCE, (
            f"Failed to recover volatility: {recovered_iv} != {self.default_sigma}"
        )

    def test_implied_volatility_batch(self) -> None:
        """Test batch implied volatility calculation."""
        # Check if batch IV is implemented
        if not hasattr(self.model, "implied_volatility_batch"):
            pytest.skip("Batch implied volatility not available")

        params = self.get_batch_params(n=SMALL_BATCH_SIZE)

        # Calculate prices
        prices = self.model.call_price_batch(**params)
        prices = to_numpy_array(prices)

        # Try calling IV batch - may not be implemented yet
        try:
            # Note: API uses positional args with different names than batch price functions
            price_key = "forwards" if self.use_forward_price else "spots"
            ivs = self.model.implied_volatility_batch(
                prices=prices,
                spots=params[price_key],
                strikes=params["strikes"],
                times=params["times"],
                rates=params["rates"],
                is_calls=True,  # is_call
            )
            ivs = to_numpy_array(ivs)
        except NotImplementedError:
            pytest.skip("Batch implied volatility not yet implemented")

        assert len(ivs) == SMALL_BATCH_SIZE
        assert np.all(ivs > 0), "All IVs must be positive"
        assert np.all(ivs < 10), "All IVs must be reasonable (<1000%)"

        # Should approximately recover input volatility
        expected_sigma = params["sigmas"]
        if isinstance(expected_sigma, np.ndarray) and len(expected_sigma) == 1:
            expected_sigma = expected_sigma[0]

        if not isinstance(expected_sigma, np.ndarray):
            expected_sigma = np.full(SMALL_BATCH_SIZE, expected_sigma)

        np.testing.assert_allclose(ivs, expected_sigma, rtol=PRACTICAL_TOLERANCE)

    # === Edge Cases and Boundary Tests ===

    def test_zero_time(self) -> None:
        """Test behavior at expiration (t=0)."""
        # At expiration, option value = intrinsic value
        params = self.get_default_params(t=1e-10)  # Nearly zero

        call_price = self.model.call_price(**params)
        put_price = self.model.put_price(**params)

        price_param = params.get("f" if self.use_forward_price else "s")
        strike = params["k"]

        call_intrinsic = max(0, price_param - strike)
        put_intrinsic = max(0, strike - price_param)

        assert abs(call_price - call_intrinsic) < PRACTICAL_TOLERANCE
        assert abs(put_price - put_intrinsic) < PRACTICAL_TOLERANCE

    def test_zero_volatility(self) -> None:
        """Test behavior with zero volatility."""
        params = self.get_default_params(sigma=1e-10)  # Nearly zero

        call_price = self.model.call_price(**params)
        put_price = self.model.put_price(**params)

        # With zero vol, prices should approach intrinsic value
        price_param = params.get("f" if self.use_forward_price else "s")
        strike = params["k"]
        rate = params["r"]
        time = params["t"]

        if self.use_forward_price:
            call_intrinsic = np.exp(-rate * time) * max(0, price_param - strike)
            put_intrinsic = np.exp(-rate * time) * max(0, strike - price_param)
        else:
            # Account for time value
            if self.has_dividend:
                dividend = params["q"]
                forward = price_param * np.exp((rate - dividend) * time)
            else:
                forward = price_param * np.exp(rate * time)

            call_intrinsic = np.exp(-rate * time) * max(0, forward - strike)
            put_intrinsic = np.exp(-rate * time) * max(0, strike - forward)

        assert abs(call_price - call_intrinsic) < PRACTICAL_TOLERANCE
        assert abs(put_price - put_intrinsic) < PRACTICAL_TOLERANCE

    def test_deep_itm_call(self) -> None:
        """Test deep in-the-money call options."""
        # Deep ITM: spot >> strike
        params = self.get_default_params()
        if self.use_forward_price:
            params["forward"] = 200.0
        else:
            params["spot"] = 200.0
        params["k"] = 50.0

        call_price = self.model.call_price(**params)

        # Deep ITM call should be approximately S - K*exp(-rt)
        price_param = params.get("f" if self.use_forward_price else "s")
        strike = params["k"]
        rate = params["r"]
        time = params["t"]

        if self.use_forward_price:
            expected = np.exp(-rate * time) * (price_param - strike)
        elif self.has_dividend:
            dividend = params["q"]
            expected = price_param * np.exp(-dividend * time) - strike * np.exp(-rate * time)
        else:
            expected = price_param - strike * np.exp(-rate * time)

        assert abs(call_price - expected) < PRACTICAL_TOLERANCE

    def test_deep_otm_call(self) -> None:
        """Test deep out-of-the-money call options."""
        # Deep OTM: spot << strike
        params = self.get_default_params()
        if self.use_forward_price:
            params["forward"] = 50.0
        else:
            params["spot"] = 50.0
        params["k"] = 200.0

        call_price = self.model.call_price(**params)

        # Deep OTM call should be nearly zero
        assert call_price < PRACTICAL_TOLERANCE

    def test_extreme_volatility(self) -> None:
        """Test behavior with extreme volatility."""
        # Very high volatility
        params = self.get_default_params(sigma=5.0)  # 500% vol

        call_price = self.model.call_price(**params)
        put_price = self.model.put_price(**params)

        # Prices should still be reasonable
        price_param = params.get("f" if self.use_forward_price else "s")
        strike = params["k"]

        assert 0 < call_price < (price_param * 10 if price_param else 1000)
        assert 0 < put_price < (strike * 10 if strike else 1000)

    def test_negative_rates(self) -> None:
        """Test behavior with negative interest rates."""
        params = self.get_default_params(r=-0.02)  # Negative rate

        call_price = self.model.call_price(**params)
        put_price = self.model.put_price(**params)

        # Prices should still be valid
        assert call_price > 0
        assert put_price > 0

        # Put-call parity should still hold
        self.test_put_call_parity()


class BaseBatchTest(BaseModelTest):
    """Extended base class with additional batch-specific tests."""

    def test_large_batch_performance(self) -> None:
        """Test that large batches are handled efficiently."""
        import time

        params = self.get_batch_params(n=LARGE_BATCH_SIZE)

        start = time.perf_counter()
        prices = self.model.call_price_batch(**params)
        prices = to_numpy_array(prices)
        elapsed = time.perf_counter() - start

        assert len(prices) == LARGE_BATCH_SIZE
        assert elapsed < 1.0, f"Large batch took {elapsed:.2f}s, expected < 1s"

    def test_mixed_broadcasting(self) -> None:
        """Test complex broadcasting scenarios."""
        price_key = self.get_price_param_name() + "s"

        # Different array sizes to test broadcasting
        params = {
            price_key: np.array([100.0, 105.0, 110.0]),  # 3 elements
            "strikes": np.array([95.0, 100.0]),  # 2 elements - should fail
            "times": np.array([1.0]),  # 1 element - broadcasts
            "rates": np.array([0.05]),  # 1 element - broadcasts
            "sigmas": np.array([0.2]),  # 1 element - broadcasts
        }

        if self.has_dividend:
            params["dividend_yields"] = np.array([0.02])  # 1 element - broadcasts

        # This should raise an error due to incompatible shapes
        with pytest.raises((ValueError, RuntimeError)):
            self.model.call_price_batch(**params)

    def test_empty_batch(self) -> None:
        """Test handling of empty input arrays."""
        price_key = self.get_price_param_name() + "s"

        params = {
            price_key: np.array([]),
            "strikes": np.array([]),
            "times": np.array([]),
            "rates": np.array([]),
            "sigmas": np.array([]),
        }

        if self.has_dividend:
            params["dividend_yields"] = np.array([])

        prices = self.model.call_price_batch(**params)
        prices = to_numpy_array(prices)

        assert len(prices) == 0
        assert isinstance(prices, np.ndarray)

    def test_scalar_inputs_batch(self) -> None:
        """Test that scalar inputs are properly handled in batch functions."""
        price_key = "forwards" if self.use_forward_price else "spots"

        # Test with Python scalars
        params = {
            price_key: 100.0,
            "strikes": 100.0,
            "times": 1.0,
            "rates": 0.05,
            "sigmas": 0.2,
        }

        if self.has_dividend:
            params["dividend_yields"] = 0.02

        prices = self.model.call_price_batch(**params)
        prices = to_numpy_array(prices)

        # Should return single-element array
        assert isinstance(prices, np.ndarray)
        assert len(prices) == 1
        assert prices[0] > 0


T = TypeVar("T", bound=BaseModelTest)


def run_comprehensive_tests[T: BaseModelTest](test_class: type[T], model: ModelProtocol) -> None:
    """Run all tests for a given model through its test class.

    This utility function can be used to ensure all standard tests
    are run for a model implementation.
    """
    instance = test_class()
    instance.model = model

    # Price tests
    instance.test_call_price_positive()
    instance.test_put_price_positive()
    instance.test_call_intrinsic_value()
    instance.test_put_intrinsic_value()
    instance.test_put_call_parity()

    # Batch tests
    instance.test_batch_call_prices()
    instance.test_batch_put_prices()
    instance.test_batch_broadcasting()
    instance.test_batch_consistency()
    instance.test_batch_put_call_parity()

    # Greeks tests
    instance.test_greeks_structure()
    instance.test_greeks_batch()
    instance.test_delta_bounds()
    instance.test_gamma_positive()
    instance.test_vega_positive()

    # IV tests
    instance.test_implied_volatility_recovery()
    instance.test_implied_volatility_batch()

    # Edge cases
    instance.test_zero_time()
    instance.test_zero_volatility()
    instance.test_deep_itm_call()
    instance.test_deep_otm_call()
    instance.test_extreme_volatility()
    instance.test_negative_rates()

    # Additional batch tests if applicable
    if isinstance(instance, BaseBatchTest):
        instance.test_large_batch_performance()
        instance.test_mixed_broadcasting()
        instance.test_empty_batch()
        instance.test_scalar_inputs_batch()
