"""Comprehensive unit tests for American option model module."""

import math
import pytest
from quantforge.models import american, merton

# Test tolerances
THEORETICAL_TOLERANCE = 1e-3
PRACTICAL_TOLERANCE = 1e-2


class TestAmericanCallPrice:
    """Test American call price calculation."""

    def test_call_price_atm(self) -> None:
        """Test call price for at-the-money American option."""
        price = american.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price > 0
        assert price < 100.0
        # American call should be at least as valuable as European
        euro_price = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price >= euro_price - THEORETICAL_TOLERANCE

    def test_call_price_with_dividend(self) -> None:
        """Test American call with dividend."""
        price = american.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert price > 0
        # With dividends, American call can be exercised early
        euro_price = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert price >= euro_price - THEORETICAL_TOLERANCE

    def test_call_price_no_early_exercise_value(self) -> None:
        """Test American call when early exercise has no value (no dividends)."""
        price = american.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        euro_price = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        # Without dividends, American call should equal European call
        assert abs(price - euro_price) < PRACTICAL_TOLERANCE

    def test_call_price_deep_itm(self) -> None:
        """Test American call for deep in-the-money option."""
        price = american.call_price(s=200.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        # Deep ITM American call with dividend might be exercised early
        intrinsic = 200.0 - 100.0
        assert price >= intrinsic
        # Should be at least as valuable as discounted intrinsic
        assert price >= intrinsic * math.exp(-0.05 * 1.0)

    def test_call_price_deep_otm(self) -> None:
        """Test American call for deep out-of-the-money option."""
        price = american.call_price(s=50.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price < 0.01
        # Should be same as European for deep OTM
        euro_price = merton.call_price(s=50.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert abs(price - euro_price) < THEORETICAL_TOLERANCE


class TestAmericanPutPrice:
    """Test American put price calculation."""

    def test_put_price_atm(self) -> None:
        """Test put price for at-the-money American option."""
        price = american.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price > 0
        assert price < 100.0
        # American put should be more valuable than European
        euro_price = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price >= euro_price - THEORETICAL_TOLERANCE

    def test_put_price_with_dividend(self) -> None:
        """Test American put with dividend."""
        price = american.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert price > 0
        euro_price = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2)
        assert price >= euro_price - THEORETICAL_TOLERANCE

    def test_put_price_early_exercise_premium(self) -> None:
        """Test American put early exercise premium."""
        price = american.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        euro_price = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        # American put should have early exercise premium
        assert price > euro_price

    def test_put_price_deep_itm(self) -> None:
        """Test American put for deep in-the-money option."""
        price = american.put_price(s=50.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        intrinsic = 100.0 - 50.0
        # Deep ITM American put should be close to intrinsic value
        assert price >= intrinsic
        assert price < intrinsic * 1.1  # Not too much above intrinsic

    def test_put_price_deep_otm(self) -> None:
        """Test American put for deep out-of-the-money option."""
        price = american.put_price(s=200.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert price < 0.01
        # Even American put has low value when deep OTM
        euro_price = merton.put_price(s=200.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2)
        assert abs(price - euro_price) < THEORETICAL_TOLERANCE


class TestAmericanGreeks:
    """Test American Greeks calculation."""

    def test_greeks_call_atm(self) -> None:
        """Test Greeks for at-the-money American call."""
        greeks = american.greeks(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2, is_call=True)
        
        # Delta should be around 0.5 for ATM
        assert 0.4 < greeks["delta"] < 0.7
        
        # Gamma should be positive
        assert greeks["gamma"] > 0
        
        # Vega should be positive
        assert greeks["vega"] > 0
        
        # Theta should be negative for calls
        assert greeks["theta"] < 0
        
        # Rho should be positive for calls
        assert greeks["rho"] > 0

    def test_greeks_put_atm(self) -> None:
        """Test Greeks for at-the-money American put."""
        greeks = american.greeks(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=0.2, is_call=False)
        
        # Delta should be around -0.5 for ATM
        assert -0.7 < greeks["delta"] < -0.3
        
        # Gamma should be positive
        assert greeks["gamma"] > 0
        
        # Vega should be positive
        assert greeks["vega"] > 0
        
        # Rho should be negative for puts
        assert greeks["rho"] < 0


class TestAmericanBatchOperations:
    """Test batch operations for American options."""

    def test_call_price_batch(self) -> None:
        """Test batch calculation of American call prices."""
        import numpy as np
        
        spots = np.array([90.0, 100.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = 1.0
        rates = 0.05
        dividend_yields = 0.02
        sigmas = 0.2
        
        prices = american.call_price_batch(spots, strikes, times, rates, dividend_yields, sigmas)
        
        assert len(prices) == 3
        assert all(p >= 0 for p in prices)
        # Prices should increase with spot
        assert prices[0] < prices[1] < prices[2]

    def test_put_price_batch(self) -> None:
        """Test batch calculation of American put prices."""
        import numpy as np
        
        spots = np.array([90.0, 100.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = 1.0
        rates = 0.05
        dividend_yields = 0.02
        sigmas = 0.2
        
        prices = american.put_price_batch(spots, strikes, times, rates, dividend_yields, sigmas)
        
        assert len(prices) == 3
        assert all(p >= 0 for p in prices)
        # Prices should decrease with spot
        assert prices[0] > prices[1] > prices[2]

    def test_greeks_batch(self) -> None:
        """Test batch calculation of American Greeks."""
        import numpy as np
        
        spots = np.array([90.0, 100.0, 110.0])
        strikes = 100.0
        times = 1.0
        rates = 0.05
        dividend_yields = 0.02
        sigmas = 0.2
        
        greeks = american.greeks_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_call=True)
        
        assert "delta" in greeks
        assert "gamma" in greeks
        assert "vega" in greeks
        assert "theta" in greeks
        assert "rho" in greeks
        
        assert len(greeks["delta"]) == 3
        assert all(0 < d < 1 for d in greeks["delta"])
        # Delta should increase with spot for calls
        assert greeks["delta"][0] < greeks["delta"][1] < greeks["delta"][2]


class TestAmericanImpliedVolatility:
    """Test implied volatility calculations for American options."""

    def test_implied_volatility_call(self) -> None:
        """Test implied volatility for American call."""
        # First calculate a price with known volatility
        target_vol = 0.25
        price = american.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=target_vol)
        
        # Then solve for implied volatility
        iv = american.implied_volatility(price=price, s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, is_call=True)
        
        assert abs(iv - target_vol) < 1e-4

    def test_implied_volatility_put(self) -> None:
        """Test implied volatility for American put."""
        # First calculate a price with known volatility
        target_vol = 0.25
        price = american.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, sigma=target_vol)
        
        # Then solve for implied volatility
        iv = american.implied_volatility(price=price, s=100.0, k=100.0, t=1.0, r=0.05, q=0.02, is_call=False)
        
        assert abs(iv - target_vol) < 1e-4

    def test_implied_volatility_batch(self) -> None:
        """Test batch implied volatility calculation."""
        import numpy as np
        
        # Calculate prices with known volatility
        spots = np.array([90.0, 100.0, 110.0])
        target_vol = 0.25
        prices = american.call_price_batch(spots, 100.0, 1.0, 0.05, 0.02, target_vol)
        
        # Solve for implied volatilities
        ivs = american.implied_volatility_batch(prices, spots, 100.0, 1.0, 0.05, 0.02, is_call=True)
        
        assert len(ivs) == 3
        assert all(abs(iv - target_vol) < 1e-3 for iv in ivs)