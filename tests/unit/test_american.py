"""Comprehensive unit tests for American option model module."""

import math

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

        greeks = american.greeks_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_calls=True)

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
        ivs = american.implied_volatility_batch(prices, spots, 100.0, 1.0, 0.05, 0.02, is_calls=True)

        assert len(ivs) == 3
        assert all(abs(iv - target_vol) < 1e-3 for iv in ivs)


class TestAmericanExerciseBoundary:
    """Test American option exercise boundary calculation."""

    def test_exercise_boundary_call(self) -> None:
        """Test exercise boundary for American call option."""
        boundary = american.exercise_boundary(k=100.0, t=1.0, r=0.05, q=0.03, sigma=0.2, is_call=True)  # type: ignore[attr-defined]

        # Call boundary should be above strike when there are dividends
        assert boundary > 100.0
        assert boundary < float("inf")

    def test_exercise_boundary_put(self) -> None:
        """Test exercise boundary for American put option."""
        boundary = american.exercise_boundary(k=100.0, t=1.0, r=0.05, q=0.03, sigma=0.2, is_call=False)  # type: ignore[attr-defined]

        # Put boundary should be below strike
        assert boundary < 100.0
        assert boundary > 0.0

    def test_exercise_boundary_no_dividends(self) -> None:
        """Test exercise boundary for call with no dividends."""
        boundary = american.exercise_boundary(k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2, is_call=True)  # type: ignore[attr-defined]

        # Without dividends, American call should never be exercised early
        assert boundary == float("inf")

    def test_exercise_boundary_near_expiry(self) -> None:
        """Test exercise boundary near expiry."""
        # Very close to expiry
        call_boundary = american.exercise_boundary(k=100.0, t=0.001, r=0.05, q=0.03, sigma=0.2, is_call=True)  # type: ignore[attr-defined]
        put_boundary = american.exercise_boundary(k=100.0, t=0.001, r=0.05, q=0.03, sigma=0.2, is_call=False)  # type: ignore[attr-defined]

        # Near expiry, boundaries should be reasonable
        # Call boundary should be >= strike (with dividends can be > strike)
        assert call_boundary >= 100.0
        assert call_boundary != float("inf")  # Should be finite
        # Put boundary should be <= strike
        assert put_boundary <= 100.0
        assert put_boundary > 0.0  # Should be positive

    def test_exercise_boundary_batch(self) -> None:
        """Test batch exercise boundary calculation."""
        import numpy as np

        strikes = np.array([95.0, 100.0, 105.0])
        times = np.array([0.5, 1.0, 1.5])
        boundaries = american.exercise_boundary_batch(  # type: ignore[attr-defined]
            strikes=strikes, times=times, rates=0.05, dividend_yields=0.03, sigmas=0.2, is_calls=True
        )

        # Convert to numpy array for easier testing
        boundaries_array = np.array(boundaries)

        assert len(boundaries_array) == 3
        # All call boundaries should be above their strikes (with dividends)
        for i in range(3):
            assert boundaries_array[i] > strikes[i]

    def test_exercise_boundary_consistency(self) -> None:
        """Test that exercise boundary is consistent with pricing."""
        k = 100.0
        t = 1.0
        r = 0.05
        q = 0.03
        sigma = 0.2

        # Get the exercise boundary
        boundary = american.exercise_boundary(k, t, r, q, sigma, is_call=False)  # type: ignore[attr-defined]

        # Price at the boundary should be close to intrinsic value
        put_price = american.put_price(s=boundary, k=k, t=t, r=r, q=q, sigma=sigma)
        intrinsic = k - boundary

        # At the boundary, the option value should be very close to intrinsic
        assert abs(put_price - intrinsic) < 0.1


class TestAmericanBinomial:
    """Test American option binomial tree calculation."""

    def test_binomial_call(self) -> None:
        """Test binomial tree for American call option."""
        price = american.binomial_tree(s=100.0, k=100.0, t=1.0, r=0.05, q=0.03, sigma=0.2, n_steps=100, is_call=True)  # type: ignore[attr-defined]

        # Should be positive and less than spot
        assert price > 0
        assert price < 100.0

        # Should be at least as valuable as European (within reasonable tolerance for binomial approximation)
        # Note: Binomial with 100 steps may have some approximation error
        euro_price = merton.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.03, sigma=0.2)
        assert price >= euro_price * 0.995  # Allow 0.5% error for binomial approximation

    def test_binomial_put(self) -> None:
        """Test binomial tree for American put option."""
        price = american.binomial_tree(s=100.0, k=100.0, t=1.0, r=0.05, q=0.03, sigma=0.2, n_steps=100, is_call=False)  # type: ignore[attr-defined]

        # Should be positive and less than strike
        assert price > 0
        assert price < 100.0

        # Should be at least as valuable as European (within reasonable tolerance for binomial approximation)
        # Note: Binomial with 100 steps may have some approximation error
        euro_price = merton.put_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.03, sigma=0.2)
        assert price >= euro_price * 0.995  # Allow 0.5% error for binomial approximation

    def test_binomial_convergence(self) -> None:
        """Test that binomial price converges with more steps."""
        # Calculate with different step counts
        price_50 = american.binomial_tree(s=100.0, k=100.0, t=1.0, r=0.05, q=0.03, sigma=0.2, n_steps=50, is_call=True)  # type: ignore[attr-defined]
        price_100 = american.binomial_tree(  # type: ignore[attr-defined]
            s=100.0, k=100.0, t=1.0, r=0.05, q=0.03, sigma=0.2, n_steps=100, is_call=True
        )
        price_200 = american.binomial_tree(  # type: ignore[attr-defined]
            s=100.0, k=100.0, t=1.0, r=0.05, q=0.03, sigma=0.2, n_steps=200, is_call=True
        )

        # Higher step counts should converge
        diff_1 = abs(price_100 - price_50)
        diff_2 = abs(price_200 - price_100)

        # Convergence: differences should decrease
        assert diff_2 < diff_1

    def test_binomial_vs_analytical(self) -> None:
        """Test binomial approximation vs analytical approximation."""
        # Use many steps for accuracy
        binomial_price = american.binomial_tree(  # type: ignore[attr-defined]
            s=100.0, k=100.0, t=1.0, r=0.05, q=0.03, sigma=0.2, n_steps=500, is_call=True
        )
        analytical_price = american.call_price(s=100.0, k=100.0, t=1.0, r=0.05, q=0.03, sigma=0.2)

        # Should be close but not necessarily identical
        # BAW approximation and binomial may differ more with dividends
        assert abs(binomial_price - analytical_price) < 1.5
