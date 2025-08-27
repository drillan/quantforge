"""Tests for batch processing functions across all models."""

import numpy as np
import pytest
from quantforge.models import black_scholes, black76, merton, american


class TestBlackScholesBatch:
    """Test batch processing for Black-Scholes model."""

    def test_implied_volatility_batch(self):
        """Test batch IV calculation for Black-Scholes."""
        # Setup
        prices = np.array([10.45, 11.0, 9.5, 12.0, 8.0])
        s, k, t, r = 100.0, 100.0, 1.0, 0.05
        
        # Calculate IV for each price
        ivs = black_scholes.implied_volatility_batch(prices, s, k, t, r, is_call=True)
        
        # Verify results
        assert len(ivs) == len(prices)
        assert all(0.01 < iv < 2.0 or np.isnan(iv) for iv in ivs)
        
        # Verify consistency with single calculation
        single_iv = black_scholes.implied_volatility(prices[0], s, k, t, r, is_call=True)
        assert abs(ivs[0] - single_iv) < 1e-10

    def test_greeks_batch(self):
        """Test batch Greeks calculation for Black-Scholes."""
        # Setup
        spots = np.array([95.0, 100.0, 105.0, 110.0])
        k, t, r, sigma = 100.0, 1.0, 0.05, 0.2
        
        # Calculate Greeks for each spot
        greeks = black_scholes.greeks_batch(spots, k, t, r, sigma, is_call=True)
        
        # Verify results
        assert len(greeks) == len(spots)
        
        # Verify consistency with single calculation
        single_greeks = black_scholes.greeks(spots[0], k, t, r, sigma, is_call=True)
        assert abs(greeks[0].delta - single_greeks.delta) < 1e-10
        assert abs(greeks[0].gamma - single_greeks.gamma) < 1e-10
        assert abs(greeks[0].vega - single_greeks.vega) < 1e-10
        assert abs(greeks[0].theta - single_greeks.theta) < 1e-10
        assert abs(greeks[0].rho - single_greeks.rho) < 1e-10


class TestBlack76Batch:
    """Test batch processing for Black76 model."""

    def test_implied_volatility_batch(self):
        """Test batch IV calculation for Black76."""
        # Setup
        prices = np.array([5.5, 6.0, 5.0, 6.5, 4.5])
        f, k, t, r = 75.0, 75.0, 0.5, 0.05
        
        # Calculate IV for each price
        ivs = black76.implied_volatility_batch(prices, f, k, t, r, is_call=True)
        
        # Verify results
        assert len(ivs) == len(prices)
        assert all(0.01 < iv < 2.0 or np.isnan(iv) for iv in ivs)
        
        # Verify consistency with single calculation
        single_iv = black76.implied_volatility(prices[0], f, k, t, r, is_call=True)
        assert abs(ivs[0] - single_iv) < 1e-10

    def test_greeks_batch(self):
        """Test batch Greeks calculation for Black76."""
        # Setup
        forwards = np.array([70.0, 75.0, 80.0, 85.0])
        k, t, r, sigma = 75.0, 0.5, 0.05, 0.25
        
        # Calculate Greeks for each forward
        greeks = black76.greeks_batch(forwards, k, t, r, sigma, is_call=True)
        
        # Verify results
        assert len(greeks) == len(forwards)
        
        # Verify consistency with single calculation
        single_greeks = black76.greeks(forwards[0], k, t, r, sigma, is_call=True)
        assert abs(greeks[0].delta - single_greeks.delta) < 1e-10
        assert abs(greeks[0].gamma - single_greeks.gamma) < 1e-10


class TestMertonBatch:
    """Test batch processing for Merton model."""

    def test_implied_volatility_batch(self):
        """Test batch IV calculation for Merton."""
        # Setup
        prices = np.array([10.0, 10.5, 9.5, 11.0, 9.0])
        s, k, t, r, q = 100.0, 100.0, 1.0, 0.05, 0.03
        
        # Calculate IV for each price
        ivs = merton.implied_volatility_batch(prices, s, k, t, r, q, is_call=True)
        
        # Verify results
        assert len(ivs) == len(prices)
        assert all(0.01 < iv < 2.0 or np.isnan(iv) for iv in ivs)
        
        # Verify consistency with single calculation
        single_iv = merton.implied_volatility(prices[0], s, k, t, r, q, is_call=True)
        assert abs(ivs[0] - single_iv) < 1e-10

    def test_greeks_batch(self):
        """Test batch Greeks calculation for Merton."""
        # Setup
        spots = np.array([95.0, 100.0, 105.0, 110.0])
        k, t, r, q, sigma = 100.0, 1.0, 0.05, 0.03, 0.2
        
        # Calculate Greeks for each spot
        greeks = merton.greeks_batch(spots, k, t, r, q, sigma, is_call=True)
        
        # Verify results
        assert len(greeks) == len(spots)
        
        # Verify consistency with single calculation
        single_greeks = merton.greeks(spots[0], k, t, r, q, sigma, is_call=True)
        assert abs(greeks[0].delta - single_greeks.delta) < 1e-10
        assert abs(greeks[0].gamma - single_greeks.gamma) < 1e-10
        assert abs(greeks[0].dividend_rho - single_greeks.dividend_rho) < 1e-10


class TestAmericanBatch:
    """Test batch processing for American model."""

    def test_implied_volatility_batch(self):
        """Test batch IV calculation for American."""
        # Setup
        prices = np.array([15.0, 15.5, 14.5, 16.0, 14.0])
        s, k, t, r, q = 100.0, 100.0, 1.0, 0.05, 0.03
        
        # Calculate IV for each price
        ivs = american.implied_volatility_batch(prices, s, k, t, r, q, is_call=False)
        
        # Verify results
        assert len(ivs) == len(prices)
        # American options may have wider IV ranges
        assert all(0.01 < iv < 3.0 or np.isnan(iv) for iv in ivs)

    def test_greeks_batch(self):
        """Test batch Greeks calculation for American."""
        # Setup
        spots = np.array([95.0, 100.0, 105.0, 110.0])
        k, t, r, q, sigma = 100.0, 1.0, 0.05, 0.03, 0.2
        
        # Calculate Greeks for each spot
        greeks = american.greeks_batch(spots, k, t, r, q, sigma, is_call=False)
        
        # Verify results
        assert len(greeks) == len(spots)
        
        # Verify consistency with single calculation
        single_greeks = american.greeks(spots[0], k, t, r, q, sigma, is_call=False)
        assert abs(greeks[0].delta - single_greeks.delta) < 1e-10
        assert abs(greeks[0].gamma - single_greeks.gamma) < 1e-10

    def test_exercise_boundary_batch(self):
        """Test batch exercise boundary calculation for American."""
        # Setup
        spots = np.array([90.0, 95.0, 100.0, 105.0, 110.0])
        k, t, r, q, sigma = 100.0, 1.0, 0.05, 0.03, 0.2
        
        # Calculate exercise boundaries
        boundaries = american.exercise_boundary_batch(spots, k, t, r, q, sigma, is_call=False)
        
        # Verify results
        assert len(boundaries) == len(spots)
        assert all(b > 0 for b in boundaries)
        
        # Verify consistency with single calculation
        single_boundary = american.exercise_boundary(spots[0], k, t, r, q, sigma, is_call=False)
        assert abs(boundaries[0] - single_boundary) < 1e-10


class TestBatchPerformance:
    """Test performance characteristics of batch processing."""

    def test_large_batch_processing(self):
        """Test processing large batches efficiently."""
        # Create large batch
        n = 10000
        spots = np.linspace(80, 120, n)
        k, t, r, sigma = 100.0, 1.0, 0.05, 0.2
        
        # Test Black-Scholes batch
        greeks = black_scholes.greeks_batch(spots, k, t, r, sigma, is_call=True)
        assert len(greeks) == n
        
        # Test that all results are valid
        for g in greeks:
            assert -1.0 <= g.delta <= 1.0
            assert g.gamma >= 0
            assert not np.isnan(g.vega)

    def test_edge_cases(self):
        """Test batch processing with edge cases."""
        # Test with single element
        spots = np.array([100.0])
        k, t, r, sigma = 100.0, 1.0, 0.05, 0.2
        greeks = black_scholes.greeks_batch(spots, k, t, r, sigma, is_call=True)
        assert len(greeks) == 1
        
        # Test with empty array (should handle gracefully)
        spots = np.array([])
        greeks = black_scholes.greeks_batch(spots, k, t, r, sigma, is_call=True)
        assert len(greeks) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])