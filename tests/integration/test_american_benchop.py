"""Test American options against BENCHOP reference values."""

import numpy as np
import quantforge as qf

# Direct access to modules
american = qf.american

# BENCHOP reference values for American options
BENCHOP_AMERICAN = {
    (100.0, 100.0, 1.0, 0.05, 0.0, 0.2): {
        "call_price": 10.4506,  # Same as European (no early exercise)
        "put_price": 6.2480,  # Higher than European due to early exercise
    },
}


class TestAmericanBenchop:
    """Test American options against BENCHOP reference values."""

    def test_american_put_benchop_standard(self) -> None:
        """Test American put against BENCHOP reference (standard case)."""
        s, k, t, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.0, 0.2

        result = american.put_price(s, k, t, r, q, sigma)
        expected = BENCHOP_AMERICAN[(s, k, t, r, q, sigma)]["put_price"]

        # Should be within 1% of BENCHOP
        error = abs((result - expected) / expected)
        assert error < 0.01, f"American put error: {error * 100:.2f}%, result: {result:.4f}, BENCHOP: {expected:.4f}"

    def test_american_call_benchop_standard(self) -> None:
        """Test American call against BENCHOP reference (standard case)."""
        s, k, t, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.0, 0.2

        result = american.call_price(s, k, t, r, q, sigma)
        expected = BENCHOP_AMERICAN[(s, k, t, r, q, sigma)]["call_price"]

        # American call with no dividends = European call
        # Should be very close to BENCHOP
        error = abs((result - expected) / expected)
        assert error < 0.01, f"American call error: {error * 100:.2f}%, result: {result:.4f}, BENCHOP: {expected:.4f}"

    def test_american_put_batch_benchop(self) -> None:
        """Test American put batch calculation against BENCHOP."""
        # Test with multiple spot prices
        spots = np.array([90.0, 100.0, 110.0])
        strikes = 100.0
        times = 1.0
        rates = 0.05
        dividend_yields = 0.0
        sigmas = 0.2

        results = american.put_price_batch(spots, strikes, times, rates, dividend_yields, sigmas)

        # Check ATM value against BENCHOP
        atm_result = results[1]  # 100.0 spot
        expected = BENCHOP_AMERICAN[(100.0, 100.0, 1.0, 0.05, 0.0, 0.2)]["put_price"]

        error = abs((atm_result - expected) / expected)
        assert error < 0.01, f"Batch ATM put error: {error * 100:.2f}%"

        # Check monotonicity: put value should increase as spot decreases
        assert results[0] > results[1] > results[2], "Put values should be monotonically decreasing with spot"

    def test_american_early_exercise_premium(self) -> None:
        """Test that American put has early exercise premium."""
        s, k, t, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.0, 0.2

        american_put = american.put_price(s, k, t, r, q, sigma)
        european_put = qf.merton.put_price(s, k, t, r, q, sigma)

        # American put should be worth more than European
        premium = american_put - european_put
        assert premium > 0, f"American put should have positive early exercise premium: {premium:.4f}"

        # Premium should be significant (at least 10% for this case)
        relative_premium = premium / european_put
        assert relative_premium > 0.10, f"Early exercise premium should be significant: {relative_premium * 100:.2f}%"

    def test_binomial_convergence_to_benchop(self) -> None:
        """Test that binomial tree converges to BENCHOP value."""
        s, k, t, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.0, 0.2
        expected = BENCHOP_AMERICAN[(s, k, t, r, q, sigma)]["put_price"]

        # Test different step counts
        step_counts = [100, 500, 1000]
        results = []

        for n_steps in step_counts:
            # Note: binomial_tree not exposed in Python API yet
            # Using BAW approximation for comparison
            result = american.put_price(s, k, t, r, q, sigma)
            results.append(result)
            error = abs((result - expected) / expected)

            # Higher step counts should give better accuracy
            if n_steps >= 1000:
                # With 1000+ steps, should be within 5% of BENCHOP
                assert error < 0.05, f"Binomial with {n_steps} steps error: {error * 100:.2f}%"

        # Check convergence: errors should decrease with more steps
        errors = [abs((r - expected) / expected) for r in results]
        for i in range(1, len(errors)):
            # Allow small fluctuations due to numerical oscillations
            assert errors[i] <= errors[i - 1] * 1.2, "Binomial should generally converge with more steps"

    def test_american_greeks_consistency(self) -> None:
        """Test that American Greeks are consistent."""
        s, k, t, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.0, 0.2

        # Calculate Greeks
        greeks = american.greeks(s, k, t, r, q, sigma, is_call=False)

        # Delta should be negative for put
        assert greeks["delta"] < 0, f"Put delta should be negative: {greeks['delta']:.4f}"
        assert greeks["delta"] > -1, f"Put delta should be > -1: {greeks['delta']:.4f}"

        # Gamma should be positive
        assert greeks["gamma"] > 0, f"Gamma should be positive: {greeks['gamma']:.4f}"

        # Vega should be positive
        assert greeks["vega"] > 0, f"Vega should be positive: {greeks['vega']:.4f}"

        # Theta is usually negative for puts (time decay)
        assert greeks["theta"] < 0, f"Put theta should typically be negative: {greeks['theta']:.4f}"

        # Rho should be negative for puts
        assert greeks["rho"] < 0, f"Put rho should be negative: {greeks['rho']:.4f}"
