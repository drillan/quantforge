"""Base class for unified model testing to eliminate code duplication.

This module provides a comprehensive base test class that can be used
for all option pricing models, reducing code duplication significantly.
"""

import math
from abc import ABC, abstractmethod
from typing import Any, Protocol

import pytest

from tests.conftest import (
    INPUT_ARRAY_TYPES,
    PRACTICAL_TOLERANCE,
    THEORETICAL_TOLERANCE,
    arrow,
    create_test_array,
)


class OptionModelProtocol(Protocol):
    """Protocol defining the interface for option pricing models."""

    def call_price(self, **kwargs: Any) -> float:
        """Calculate single call option price."""
        ...

    def put_price(self, **kwargs: Any) -> float:
        """Calculate single put option price."""
        ...

    def call_price_batch(self, **kwargs: Any) -> Any:
        """Calculate batch call option prices."""
        ...

    def put_price_batch(self, **kwargs: Any) -> Any:
        """Calculate batch put option prices."""
        ...

    def greeks(self, **kwargs: Any) -> dict[str, float]:
        """Calculate option Greeks."""
        ...

    def implied_volatility(self, **kwargs: Any) -> float:
        """Calculate implied volatility."""
        ...


class BaseModelTest(ABC):
    """Base class for all option pricing model tests.

    This abstract base class provides common test methods that work across
    all models (Black-Scholes, Black76, Merton, American), eliminating
    the need for duplicate test implementations.
    """

    # ===== Configuration (override in subclasses) =====

    @property
    @abstractmethod
    def model(self) -> OptionModelProtocol:
        """The model module to test (e.g., black_scholes, black76)."""
        ...

    @property
    @abstractmethod
    def default_params(self) -> dict[str, float]:
        """Default parameters for the model."""
        ...

    @property
    def atm_call_price_expected(self) -> float:
        """Expected ATM call price for validation."""
        return 10.0  # Override in subclasses

    @property
    def atm_put_price_expected(self) -> float:
        """Expected ATM put price for validation."""
        return 5.0  # Override in subclasses

    @property
    def tolerance(self) -> float:
        """Default tolerance for price comparisons."""
        return 0.5

    # ===== Helper Methods =====

    def calculate_call_intrinsic(self, spot_or_forward: float, strike: float, rate: float, time: float) -> float:
        """Calculate intrinsic value for call option."""
        if self.is_forward_based:
            return (spot_or_forward - strike) * math.exp(-rate * time)
        else:
            return spot_or_forward - strike * math.exp(-rate * time)

    def calculate_put_intrinsic(self, spot_or_forward: float, strike: float, rate: float, time: float) -> float:
        """Calculate intrinsic value for put option."""
        if self.is_forward_based:
            return (strike - spot_or_forward) * math.exp(-rate * time)
        else:
            return strike * math.exp(-rate * time) - spot_or_forward

    @property
    def is_forward_based(self) -> bool:
        """Whether the model uses forward price (Black76) or spot price."""
        return "f" in self.default_params

    def get_price_param_name(self) -> str:
        """Get the parameter name for price (s for spot, f for forward)."""
        return "f" if self.is_forward_based else "s"

    # ===== Common Test Methods =====

    def test_call_price_atm(self) -> None:
        """Test call price for at-the-money option."""
        price = self.model.call_price(**self.default_params)
        assert price > 0
        assert price < self.default_params.get("s", self.default_params.get("f", 100))
        assert abs(price - self.atm_call_price_expected) < self.tolerance

    def test_call_price_itm(self) -> None:
        """Test call price for in-the-money option."""
        params = self.default_params.copy()
        price_key = self.get_price_param_name()
        params[price_key] = 110.0  # Make it ITM

        price = self.model.call_price(**params)
        intrinsic = self.calculate_call_intrinsic(params[price_key], params["k"], params["r"], params["t"])
        assert price > intrinsic  # Must be worth at least intrinsic value

    def test_call_price_otm(self) -> None:
        """Test call price for out-of-the-money option."""
        params = self.default_params.copy()
        price_key = self.get_price_param_name()
        params[price_key] = 90.0  # Make it OTM

        price = self.model.call_price(**params)
        assert price > 0  # Even OTM options have positive value
        assert price < 10.0  # But should be relatively small

    def test_call_price_deep_itm(self) -> None:
        """Test call price for deep in-the-money option."""
        params = self.default_params.copy()
        price_key = self.get_price_param_name()
        params[price_key] = 200.0  # Make it deep ITM

        price = self.model.call_price(**params)
        intrinsic = self.calculate_call_intrinsic(params[price_key], params["k"], params["r"], params["t"])
        assert abs(price - intrinsic) < 1.0  # Should be close to intrinsic

    def test_call_price_deep_otm(self) -> None:
        """Test call price for deep out-of-the-money option."""
        params = self.default_params.copy()
        price_key = self.get_price_param_name()
        params[price_key] = 50.0  # Make it deep OTM

        price = self.model.call_price(**params)
        assert price < 0.01  # Should be nearly worthless

    def test_call_price_zero_volatility(self) -> None:
        """Test call price with zero volatility."""
        params = self.default_params.copy()
        params["sigma"] = 0.0

        with pytest.raises(ValueError):
            self.model.call_price(**params)

    def test_call_price_high_volatility(self) -> None:
        """Test call price with high volatility."""
        params = self.default_params.copy()
        params["sigma"] = 1.0

        price = self.model.call_price(**params)
        assert price > 15.0  # High vol means high option value
        assert price < params.get("s", params.get("f", 100))

    def test_call_price_zero_time(self) -> None:
        """Test call price at expiration."""
        params = self.default_params.copy()
        params["t"] = 0.0

        with pytest.raises(ValueError):
            self.model.call_price(**params)

    def test_call_price_negative_rate(self) -> None:
        """Test call price with negative interest rate."""
        params = self.default_params.copy()
        params["r"] = -0.02

        price = self.model.call_price(**params)
        assert price > 0

    def test_call_price_invalid_inputs(self) -> None:
        """Test call price with invalid inputs."""
        # Negative spot/forward
        params = self.default_params.copy()
        price_key = self.get_price_param_name()
        params[price_key] = -100.0
        with pytest.raises(ValueError):
            self.model.call_price(**params)

        # Negative strike
        params = self.default_params.copy()
        params["k"] = -100.0
        with pytest.raises(ValueError):
            self.model.call_price(**params)

        # Negative time
        params = self.default_params.copy()
        params["t"] = -1.0
        with pytest.raises(ValueError):
            self.model.call_price(**params)

    def test_put_price_atm(self) -> None:
        """Test put price for at-the-money option."""
        price = self.model.put_price(**self.default_params)
        assert price > 0
        assert price < self.default_params.get("s", self.default_params.get("f", 100))
        assert abs(price - self.atm_put_price_expected) < self.tolerance

    def test_put_price_itm(self) -> None:
        """Test put price for in-the-money option."""
        params = self.default_params.copy()
        price_key = self.get_price_param_name()
        params[price_key] = 90.0  # Make put ITM

        price = self.model.put_price(**params)
        intrinsic = self.calculate_put_intrinsic(params[price_key], params["k"], params["r"], params["t"])
        assert price > intrinsic

    def test_put_price_otm(self) -> None:
        """Test put price for out-of-the-money option."""
        params = self.default_params.copy()
        price_key = self.get_price_param_name()
        params[price_key] = 110.0  # Make put OTM

        price = self.model.put_price(**params)
        assert price > 0
        assert price < 10.0

    def test_put_price_deep_itm(self) -> None:
        """Test put price for deep in-the-money option."""
        params = self.default_params.copy()
        price_key = self.get_price_param_name()
        params[price_key] = 50.0  # Make put deep ITM

        price = self.model.put_price(**params)
        intrinsic = self.calculate_put_intrinsic(params[price_key], params["k"], params["r"], params["t"])
        assert abs(price - intrinsic) < 1.0

    def test_put_price_deep_otm(self) -> None:
        """Test put price for deep out-of-the-money option."""
        params = self.default_params.copy()
        price_key = self.get_price_param_name()
        params[price_key] = 150.0  # Make put deep OTM

        price = self.model.put_price(**params)
        assert price < 0.5

    @abstractmethod
    def test_put_call_parity(self) -> None:
        """Test put-call parity relationship (model-specific)."""
        ...

    # ===== Batch Processing Tests =====

    @pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
    def test_call_price_batch_single(self, array_type: str) -> None:
        """Test batch processing with single element."""
        batch_params = {}

        # Create properly named batch parameters
        if self.is_forward_based:
            batch_params["forwards"] = create_test_array([self.default_params["f"]], array_type)
        else:
            batch_params["spots"] = create_test_array([self.default_params["s"]], array_type)

        batch_params["strikes"] = create_test_array([self.default_params["k"]], array_type)
        batch_params["times"] = create_test_array([self.default_params["t"]], array_type)
        batch_params["rates"] = create_test_array([self.default_params["r"]], array_type)
        batch_params["sigmas"] = create_test_array([self.default_params["sigma"]], array_type)

        prices = self.model.call_price_batch(**batch_params)
        assert len(prices) == 1
        arrow.assert_type(prices)

        single_price = self.model.call_price(**self.default_params)
        assert abs(arrow.get_value(prices, 0) - single_price) < THEORETICAL_TOLERANCE

    @pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
    def test_put_price_batch_single(self, array_type: str) -> None:
        """Test batch put processing with single element."""
        batch_params = {}

        # Create properly named batch parameters
        if self.is_forward_based:
            batch_params["forwards"] = create_test_array([self.default_params["f"]], array_type)
        else:
            batch_params["spots"] = create_test_array([self.default_params["s"]], array_type)

        batch_params["strikes"] = create_test_array([self.default_params["k"]], array_type)
        batch_params["times"] = create_test_array([self.default_params["t"]], array_type)
        batch_params["rates"] = create_test_array([self.default_params["r"]], array_type)
        batch_params["sigmas"] = create_test_array([self.default_params["sigma"]], array_type)

        prices = self.model.put_price_batch(**batch_params)
        assert len(prices) == 1
        arrow.assert_type(prices)

        single_price = self.model.put_price(**self.default_params)
        assert abs(arrow.get_value(prices, 0) - single_price) < THEORETICAL_TOLERANCE

    # ===== Greeks Tests =====

    def test_greeks_basic(self) -> None:
        """Test basic Greeks calculation."""
        greeks = self.model.greeks(**self.default_params, is_call=True)

        # All Greeks should be present
        assert "delta" in greeks
        assert "gamma" in greeks
        assert "vega" in greeks
        assert "theta" in greeks
        assert "rho" in greeks

        # Basic sanity checks
        assert -1 <= greeks["delta"] <= 1
        assert greeks["gamma"] >= 0
        assert greeks["vega"] >= 0

    def test_greeks_put(self) -> None:
        """Test put Greeks calculation."""
        greeks = self.model.greeks(**self.default_params, is_call=False)

        # Put delta should be negative
        assert -1 <= greeks["delta"] <= 0
        assert greeks["gamma"] >= 0
        assert greeks["vega"] >= 0

    # ===== Implied Volatility Tests =====

    def test_implied_volatility_call(self) -> None:
        """Test implied volatility calculation for call options."""
        # First calculate a price with known volatility
        known_sigma = 0.25
        params = self.default_params.copy()
        params["sigma"] = known_sigma

        target_price = self.model.call_price(**params)

        # Now calculate IV from that price
        iv_params = {k: v for k, v in params.items() if k != "sigma"}
        iv_params["price"] = target_price
        iv_params["is_call"] = True

        iv = self.model.implied_volatility(**iv_params)
        assert abs(iv - known_sigma) < PRACTICAL_TOLERANCE

    def test_implied_volatility_put(self) -> None:
        """Test implied volatility calculation for put options."""
        # First calculate a price with known volatility
        known_sigma = 0.25
        params = self.default_params.copy()
        params["sigma"] = known_sigma

        target_price = self.model.put_price(**params)

        # Now calculate IV from that price
        iv_params = {k: v for k, v in params.items() if k != "sigma"}
        iv_params["price"] = target_price
        iv_params["is_call"] = False

        iv = self.model.implied_volatility(**iv_params)
        assert abs(iv - known_sigma) < PRACTICAL_TOLERANCE
