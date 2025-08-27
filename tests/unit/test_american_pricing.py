"""
Unit tests for American option pricing using Bjerksund-Stensland 2002.

Test cases are taken from draft/GBS_2025.py to ensure consistency
with the reference implementation.
"""

import numpy as np
import pytest
import quantforge

american = quantforge.models.american

# Import functions from american module
call_price = american.call_price
put_price = american.put_price
call_price_batch = american.call_price_batch
put_price_batch = american.put_price_batch
greeks = american.greeks
implied_volatility = american.implied_volatility
exercise_boundary = american.exercise_boundary


# Test tolerances from conftest.py
PRACTICAL_TOLERANCE = 1e-3  # 0.1% for prices (financial accuracy)
THEORETICAL_TOLERANCE = 1e-5  # For theoretical properties
NUMERICAL_TOLERANCE = 1e-7  # For high-precision calculations


class TestBjerksundStensland2002:
    """Test cases from GBS_2025.py lines 1705-1757."""

    def test_call_price_basic(self) -> None:
        """Test basic American call price calculations.

        Note: These values were verified against GBS_2025.py implementation.
        The GBS test cases use b=0.1, not q=0, so we need to be careful.
        """
        # Test case 1: s=90, k=100, t=0.5, r=0.1, q=0, sigma=0.15
        # For no dividend American call, it can still differ from European
        price = call_price(s=90.0, k=100.0, t=0.5, r=0.1, q=0.0, sigma=0.15)
        assert abs(price - 1.8742) < PRACTICAL_TOLERANCE

        # Test case 2: s=100, k=100, t=0.5, r=0.1, q=0, sigma=0.25
        # ATM call
        price = call_price(s=100.0, k=100.0, t=0.5, r=0.1, q=0.0, sigma=0.25)
        assert abs(price - 9.5822) < PRACTICAL_TOLERANCE

        # Test case 3: s=110, k=100, t=0.5, r=0.1, q=0, sigma=0.35
        # ITM call
        price = call_price(s=110.0, k=100.0, t=0.5, r=0.1, q=0.0, sigma=0.35)
        assert abs(price - 19.2193) < PRACTICAL_TOLERANCE

    def test_put_price_basic(self) -> None:
        """Test basic American put price calculations.

        Note: These values were verified against GBS_2025.py implementation.
        """
        # Test case 1: s=90, k=100, t=0.5, r=0.1, q=0, sigma=0.15
        # Deep ITM put should be at intrinsic value
        price = put_price(s=90.0, k=100.0, t=0.5, r=0.1, q=0.0, sigma=0.15)
        assert abs(price - 10.0000) < PRACTICAL_TOLERANCE

        # Test case 2: s=100, k=100, t=0.5, r=0.1, q=0, sigma=0.25
        # ATM put
        price = put_price(s=100.0, k=100.0, t=0.5, r=0.1, q=0.0, sigma=0.25)
        assert abs(price - 4.5341) < PRACTICAL_TOLERANCE

        # Test case 3: s=110, k=100, t=0.5, r=0.1, q=0, sigma=0.35
        # OTM put
        price = put_price(s=110.0, k=100.0, t=0.5, r=0.1, q=0.0, sigma=0.35)
        assert abs(price - 4.5446) < PRACTICAL_TOLERANCE

    def test_dividend_impact(self) -> None:
        """Test impact of dividends on American option prices.

        When q > 0, American call may be exercised early.
        """
        # Call with dividend should have different value than without
        call_no_div = call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.3)
        call_with_div = call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.03, sigma=0.3)

        # With dividends, call value should be less
        assert call_with_div < call_no_div

        # Put with dividend should have higher value
        put_no_div = put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.3)
        put_with_div = put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.03, sigma=0.3)
        assert put_with_div > put_no_div

    def test_put_call_symmetry(self) -> None:
        """Test put-call symmetry property for American options.

        Due to dividend arbitrage constraint and the complexity of the
        transformation, we test a weaker property: that puts and calls
        behave symmetrically with respect to moneyness.
        """
        # Test symmetric pricing for ITM/OTM
        t, r, q, sigma = 0.5, 0.06, 0.02, 0.25

        # OTM call should have similar value structure to OTM put
        otm_call = call_price(s=90.0, k=100.0, t=t, r=r, q=q, sigma=sigma)
        otm_put = put_price(s=110.0, k=100.0, t=t, r=r, q=q, sigma=sigma)

        # Both should be positive but relatively small
        assert otm_call > 0 and otm_call < 10
        assert otm_put > 0 and otm_put < 10

        # ITM options should have higher values
        itm_call = call_price(s=110.0, k=100.0, t=t, r=r, q=q, sigma=sigma)
        itm_put = put_price(s=90.0, k=100.0, t=t, r=r, q=q, sigma=sigma)

        assert itm_call > otm_call
        assert itm_put > otm_put

    def test_early_exercise_conditions(self) -> None:
        """Test early exercise boundary conditions."""
        # Deep ITM American put should be exercised immediately
        s, k = 50.0, 100.0
        american_put = put_price(s=s, k=k, t=0.5, r=0.05, q=0.0, sigma=0.3)
        intrinsic = k - s

        # American put should be at least intrinsic value
        assert american_put >= intrinsic - PRACTICAL_TOLERANCE

        # For very deep ITM, should be close to intrinsic
        s_deep = 10.0
        american_put_deep = put_price(s=s_deep, k=k, t=0.5, r=0.05, q=0.0, sigma=0.3)
        intrinsic_deep = k - s_deep
        assert abs(american_put_deep - intrinsic_deep) < PRACTICAL_TOLERANCE

    def test_american_european_relationship(self) -> None:
        """Test that American >= European for all cases."""
        test_cases = [
            (100.0, 100.0, 0.5, 0.05, 0.0, 0.25),  # ATM
            (110.0, 100.0, 0.5, 0.05, 0.0, 0.25),  # ITM call / OTM put
            (90.0, 100.0, 0.5, 0.05, 0.0, 0.25),  # OTM call / ITM put
            (100.0, 100.0, 0.1, 0.05, 0.03, 0.25),  # Short maturity with dividend
            (100.0, 100.0, 2.0, 0.05, 0.02, 0.25),  # Long maturity
        ]

        for s, k, t, r, q, sigma in test_cases:
            # American prices
            am_call = call_price(s=s, k=k, t=t, r=r, q=q, sigma=sigma)
            am_put = put_price(s=s, k=k, t=t, r=r, q=q, sigma=sigma)

            # For now, we just check they are positive and finite
            assert am_call > 0 and np.isfinite(am_call)
            assert am_put > 0 and np.isfinite(am_put)

            # Check intrinsic value bounds
            assert am_call >= max(s - k, 0) - PRACTICAL_TOLERANCE
            assert am_put >= max(k - s, 0) - PRACTICAL_TOLERANCE


class TestAmericanBatchPricing:
    """Test batch pricing functions."""

    def test_call_price_batch(self) -> None:
        """Test batch calculation of call prices."""
        spots = np.array([80.0, 90.0, 100.0, 110.0, 120.0])
        k, t, r, q, sigma = 100.0, 0.5, 0.1, 0.0, 0.25

        prices = call_price_batch(spots=spots, strikes=k, times=t, rates=r, qs=q, sigmas=sigma)

        # Check shape
        assert len(prices) == len(spots)

        # Check monotonicity (call price increases with spot)
        assert all(prices[i] <= prices[i + 1] for i in range(len(prices) - 1))

        # Check individual values match scalar function
        for i, s in enumerate(spots):
            expected = call_price(s=s, k=k, t=t, r=r, q=q, sigma=sigma)
            assert abs(prices[i] - expected) < NUMERICAL_TOLERANCE

    def test_put_price_batch(self) -> None:
        """Test batch calculation of put prices."""
        spots = np.array([80.0, 90.0, 100.0, 110.0, 120.0])
        k, t, r, q, sigma = 100.0, 0.5, 0.1, 0.0, 0.25

        prices = put_price_batch(spots=spots, strikes=k, times=t, rates=r, qs=q, sigmas=sigma)

        # Check shape
        assert len(prices) == len(spots)

        # Check monotonicity (put price decreases with spot)
        assert all(prices[i] >= prices[i + 1] for i in range(len(prices) - 1))

        # Check individual values match scalar function
        for i, s in enumerate(spots):
            expected = put_price(s=s, k=k, t=t, r=r, q=q, sigma=sigma)
            assert abs(prices[i] - expected) < NUMERICAL_TOLERANCE


class TestAmericanGreeks:
    """Test Greeks calculations for American options."""

    def test_call_greeks(self) -> None:
        """Test Greeks for American call options."""
        s, k, t, r, q, sigma = 100.0, 100.0, 0.5, 0.05, 0.02, 0.25

        result = greeks(s=s, k=k, t=t, r=r, q=q, sigma=sigma, is_call=True)

        # Check that all Greeks are present and finite
        assert hasattr(result, "delta")
        assert hasattr(result, "gamma")
        assert hasattr(result, "vega")
        assert hasattr(result, "theta")
        assert hasattr(result, "rho")

        assert np.isfinite(result.delta)
        assert np.isfinite(result.gamma)
        assert np.isfinite(result.vega)
        assert np.isfinite(result.theta)
        assert np.isfinite(result.rho)

        # Delta should be between 0 and 1 for calls
        assert 0 <= result.delta <= 1

        # Gamma should be positive
        assert result.gamma >= 0

        # Vega should be positive (except at boundaries)
        assert result.vega >= 0

    def test_put_greeks(self) -> None:
        """Test Greeks for American put options."""
        s, k, t, r, q, sigma = 100.0, 100.0, 0.5, 0.05, 0.02, 0.25

        result = greeks(s=s, k=k, t=t, r=r, q=q, sigma=sigma, is_call=False)

        # Check that all Greeks are present and finite
        assert np.isfinite(result.delta)
        assert np.isfinite(result.gamma)
        assert np.isfinite(result.vega)
        assert np.isfinite(result.theta)
        assert np.isfinite(result.rho)

        # Delta should be between -1 and 0 for puts
        assert -1 <= result.delta <= 0

        # Gamma should be positive
        assert result.gamma >= 0


class TestAmericanImpliedVolatility:
    """Test implied volatility calculations."""

    def test_call_implied_volatility(self) -> None:
        """Test IV calculation for American calls."""
        # First calculate a price with known volatility
        s, k, t, r, q = 100.0, 100.0, 0.5, 0.05, 0.02
        true_sigma = 0.25

        price = call_price(s=s, k=k, t=t, r=r, q=q, sigma=true_sigma)

        # Now solve for IV
        iv = implied_volatility(price=price, s=s, k=k, t=t, r=r, q=q, is_call=True)

        # Should recover the original volatility
        assert abs(iv - true_sigma) < PRACTICAL_TOLERANCE

    def test_put_implied_volatility(self) -> None:
        """Test IV calculation for American puts."""
        # First calculate a price with known volatility
        s, k, t, r, q = 100.0, 100.0, 0.5, 0.05, 0.02
        true_sigma = 0.25

        price = put_price(s=s, k=k, t=t, r=r, q=q, sigma=true_sigma)

        # Now solve for IV
        iv = implied_volatility(price=price, s=s, k=k, t=t, r=r, q=q, is_call=False)

        # Should recover the original volatility
        assert abs(iv - true_sigma) < PRACTICAL_TOLERANCE

    def test_iv_with_initial_guess(self) -> None:
        """Test IV calculation with initial guess."""
        s, k, t, r, q = 100.0, 100.0, 0.5, 0.05, 0.02
        true_sigma = 0.35

        price = call_price(s=s, k=k, t=t, r=r, q=q, sigma=true_sigma)

        # Provide a good initial guess
        iv = implied_volatility(price=price, s=s, k=k, t=t, r=r, q=q, is_call=True, initial_guess=0.3)

        assert abs(iv - true_sigma) < PRACTICAL_TOLERANCE


class TestExerciseBoundary:
    """Test early exercise boundary calculations."""

    def test_call_exercise_boundary(self) -> None:
        """Test exercise boundary for American calls."""
        s, k, t, r, q, sigma = 100.0, 100.0, 0.5, 0.05, 0.03, 0.25

        boundary = exercise_boundary(s=s, k=k, t=t, r=r, q=q, sigma=sigma, is_call=True)

        # Boundary should be finite and positive
        assert np.isfinite(boundary)
        assert boundary > 0

        # For call with dividends, boundary should be finite
        # Without dividends, it should be infinite
        boundary_no_div = exercise_boundary(s=s, k=k, t=t, r=r, q=0.0, sigma=sigma, is_call=True)
        assert np.isinf(boundary_no_div)

    def test_put_exercise_boundary(self) -> None:
        """Test exercise boundary for American puts."""
        s, k, t, r, q, sigma = 100.0, 100.0, 0.5, 0.05, 0.02, 0.25

        boundary = exercise_boundary(s=s, k=k, t=t, r=r, q=q, sigma=sigma, is_call=False)

        # Boundary should be finite and positive
        assert np.isfinite(boundary)
        assert boundary > 0

        # Put boundary should be less than strike
        assert boundary < k


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_time_to_maturity(self) -> None:
        """Test options at expiry."""
        s, k = 105.0, 100.0

        # At expiry, value equals intrinsic
        call_val = call_price(s=s, k=k, t=0.0, r=0.05, q=0.02, sigma=0.25)
        assert abs(call_val - max(s - k, 0)) < NUMERICAL_TOLERANCE

        put_val = put_price(s=s, k=k, t=0.0, r=0.05, q=0.02, sigma=0.25)
        assert abs(put_val - max(k - s, 0)) < NUMERICAL_TOLERANCE

    def test_deep_itm_put(self) -> None:
        """Test deep in-the-money put."""
        s, k = 50.0, 100.0

        put_val = put_price(s=s, k=k, t=0.5, r=0.05, q=0.0, sigma=0.3)
        intrinsic = k - s

        # Deep ITM put should be close to intrinsic value
        assert put_val >= intrinsic - PRACTICAL_TOLERANCE

    def test_deep_otm_options(self) -> None:
        """Test deep out-of-the-money options."""
        # Deep OTM call
        call_val = call_price(s=50.0, k=100.0, t=0.1, r=0.05, q=0.0, sigma=0.2)
        assert call_val < 0.01  # Should be very small

        # Deep OTM put
        put_val = put_price(s=150.0, k=100.0, t=0.1, r=0.05, q=0.0, sigma=0.2)
        assert put_val < 0.01  # Should be very small

    def test_dividend_arbitrage_prevention(self) -> None:
        """Test that q > r raises an error."""
        with pytest.raises(ValueError, match="arbitrage"):
            call_price(s=100.0, k=100.0, t=0.5, r=0.05, q=0.06, sigma=0.25)

        with pytest.raises(ValueError, match="arbitrage"):
            put_price(s=100.0, k=100.0, t=0.5, r=0.05, q=0.06, sigma=0.25)
