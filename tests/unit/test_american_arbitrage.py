"""Test no-arbitrage conditions for American options."""

import pytest
import quantforge as qf

# Direct access to modules
american = qf.american
merton = qf.merton


class TestAmericanNoArbitrage:
    """Test that American options satisfy no-arbitrage bounds."""

    def test_put_no_arbitrage_standard(self) -> None:
        """Test put price >= max(intrinsic, European) for standard cases."""
        test_cases = [
            (100, 100, 1.0, 0.05, 0.0, 0.2),  # ATM
            (90, 100, 1.0, 0.05, 0.0, 0.2),   # ITM
            (110, 100, 1.0, 0.05, 0.0, 0.2),  # OTM
        ]
        
        for s, k, t, r, q, sigma in test_cases:
            amer = american.put_price(s, k, t, r, q, sigma)
            euro = merton.put_price(s, k, t, r, q, sigma)
            intrinsic = max(k - s, 0)
            
            # American must be at least as valuable as European
            assert amer >= euro - 1e-10, \
                f"American put ({amer}) < European ({euro}) for S={s}, K={k}"
            
            # American must be at least intrinsic value
            assert amer >= intrinsic - 1e-10, \
                f"American put ({amer}) < intrinsic ({intrinsic}) for S={s}, K={k}"

    def test_put_no_arbitrage_edge_cases(self) -> None:
        """Test put price >= max(intrinsic, European) for edge cases."""
        edge_cases = [
            (100, 100, 0.1, 0.05, 0.0, 0.2),    # Short maturity
            (100, 100, 0.001, 0.05, 0.0, 0.2),  # Very short maturity
            (100, 100, 1.0, 0.1, 0.0, 0.2),     # High interest rate
            (100, 100, 1.0, 0.05, 0.0, 0.01),   # Low volatility
            (100, 100, 1.0, -0.05, 0.0, 0.2),   # Negative interest rate
        ]
        
        for s, k, t, r, q, sigma in edge_cases:
            amer = american.put_price(s, k, t, r, q, sigma)
            euro = merton.put_price(s, k, t, r, q, sigma)
            intrinsic = max(k - s, 0)
            
            # No-arbitrage bounds must hold even in edge cases
            assert amer >= euro - 1e-10, \
                f"Edge case failed: American put ({amer}) < European ({euro})"
            assert amer >= intrinsic - 1e-10, \
                f"Edge case failed: American put ({amer}) < intrinsic ({intrinsic})"

    def test_call_no_arbitrage_standard(self) -> None:
        """Test call price >= max(intrinsic, European) for standard cases."""
        test_cases = [
            (100, 100, 1.0, 0.05, 0.0, 0.2),   # ATM (no dividend)
            (110, 100, 1.0, 0.05, 0.03, 0.2),  # ITM (with dividend)
            (90, 100, 1.0, 0.05, 0.03, 0.2),   # OTM (with dividend)
        ]
        
        for s, k, t, r, q, sigma in test_cases:
            amer = american.call_price(s, k, t, r, q, sigma)
            euro = merton.call_price(s, k, t, r, q, sigma)
            intrinsic = max(s - k, 0)
            
            # American must be at least as valuable as European
            assert amer >= euro - 1e-10, \
                f"American call ({amer}) < European ({euro}) for S={s}, K={k}"
            
            # American must be at least intrinsic value
            assert amer >= intrinsic - 1e-10, \
                f"American call ({amer}) < intrinsic ({intrinsic}) for S={s}, K={k}"

    def test_call_no_arbitrage_edge_cases(self) -> None:
        """Test call price >= max(intrinsic, European) for edge cases."""
        edge_cases = [
            (100, 100, 0.1, 0.05, 0.0, 0.2),    # Short maturity
            (100, 100, 0.001, 0.05, 0.0, 0.2),  # Very short maturity
            (100, 100, 1.0, 0.1, 0.0, 0.2),     # High interest rate
            (100, 100, 1.0, 0.05, 0.0, 0.01),   # Low volatility
        ]
        
        for s, k, t, r, q, sigma in edge_cases:
            amer = american.call_price(s, k, t, r, q, sigma)
            euro = merton.call_price(s, k, t, r, q, sigma)
            intrinsic = max(s - k, 0)
            
            # No-arbitrage bounds must hold even in edge cases
            assert amer >= euro - 1e-10, \
                f"Edge case failed: American call ({amer}) < European ({euro})"
            assert amer >= intrinsic - 1e-10, \
                f"Edge case failed: American call ({amer}) < intrinsic ({intrinsic})"

    def test_put_call_parity_bounds(self) -> None:
        """Test that American options respect modified put-call parity bounds."""
        s, k, t, r, q, sigma = 100, 100, 1.0, 0.05, 0.02, 0.2
        
        amer_call = american.call_price(s, k, t, r, q, sigma)
        amer_put = american.put_price(s, k, t, r, q, sigma)
        euro_call = merton.call_price(s, k, t, r, q, sigma)
        euro_put = merton.put_price(s, k, t, r, q, sigma)
        
        # American options should have non-negative early exercise premium
        call_premium = amer_call - euro_call
        put_premium = amer_put - euro_put
        
        assert call_premium >= -1e-10, "Negative call premium"
        assert put_premium >= -1e-10, "Negative put premium"
        
        # For dividend-paying stock, both can have positive premium
        if q > 0:
            # At least one should have positive premium in general
            # (though not strictly required by theory)
            pass

    def test_batch_no_arbitrage(self) -> None:
        """Test no-arbitrage conditions hold for batch operations."""
        import numpy as np
        
        spots = np.array([90.0, 100.0, 110.0])
        strikes = np.array([100.0, 100.0, 100.0])
        times = np.array([1.0, 1.0, 1.0])
        rates = np.array([0.05, 0.05, 0.05])
        sigmas = np.array([0.2, 0.2, 0.2])
        
        # Test put batch
        amer_puts = american.put_price_batch(spots, strikes, times, rates, 0.0, sigmas)
        euro_puts = merton.put_price_batch(spots, strikes, times, rates, 0.0, sigmas)
        
        for i, (amer, euro, s, k) in enumerate(zip(amer_puts, euro_puts, spots, strikes)):
            intrinsic = max(k - s, 0)
            assert amer >= euro - 1e-10, \
                f"Batch put {i}: American ({amer}) < European ({euro})"
            assert amer >= intrinsic - 1e-10, \
                f"Batch put {i}: American ({amer}) < intrinsic ({intrinsic})"
        
        # Test call batch
        amer_calls = american.call_price_batch(spots, strikes, times, rates, 0.0, sigmas)
        euro_calls = merton.call_price_batch(spots, strikes, times, rates, 0.0, sigmas)
        
        for i, (amer, euro, s, k) in enumerate(zip(amer_calls, euro_calls, spots, strikes)):
            intrinsic = max(s - k, 0)
            assert amer >= euro - 1e-10, \
                f"Batch call {i}: American ({amer}) < European ({euro})"
            assert amer >= intrinsic - 1e-10, \
                f"Batch call {i}: American ({amer}) < intrinsic ({intrinsic})"