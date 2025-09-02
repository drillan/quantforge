"""Integration tests for Arrow Native functionality with broadcasting."""

import pytest
import pyarrow as pa
import numpy as np
from quantforge import arrow_native


class TestArrowNativeIntegration:
    """Integration tests for arrow_native module."""
    
    def test_module_imports(self):
        """Test that arrow_native module and functions are accessible."""
        assert hasattr(arrow_native, 'arrow_call_price')
        assert hasattr(arrow_native, 'arrow_put_price')
        assert hasattr(arrow_native, 'arrow_greeks')
        assert hasattr(arrow_native, 'arrow76_call_price')
        assert hasattr(arrow_native, 'arrow76_put_price')
        assert hasattr(arrow_native, 'arrow76_greeks')
    
    def test_black_scholes_call_put_parity(self):
        """Test put-call parity for Black-Scholes with broadcasting."""
        # Setup with broadcasting
        spots = pa.array([100.0, 105.0, 110.0])
        strikes = pa.array([100.0])  # Scalar
        times = pa.array([1.0])
        rates = pa.array([0.05])
        sigmas = pa.array([0.2])
        
        # Calculate prices
        call_prices = arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)
        put_prices = arrow_native.arrow_put_price(spots, strikes, times, rates, sigmas)
        
        # Convert to numpy for testing
        calls = call_prices.to_numpy()
        puts = put_prices.to_numpy()
        spots_np = spots.to_numpy()
        
        # Put-call parity: C - P = S - K * exp(-r*T)
        for i, s in enumerate(spots_np):
            parity_lhs = calls[i] - puts[i]
            parity_rhs = s - 100.0 * np.exp(-0.05 * 1.0)
            assert abs(parity_lhs - parity_rhs) < 1e-10, f"Put-call parity failed at index {i}"
    
    def test_greeks_consistency(self):
        """Test that Greeks values are consistent and reasonable."""
        # Setup
        spots = pa.array([95.0, 100.0, 105.0])
        strikes = pa.array([100.0])
        times = pa.array([1.0])
        rates = pa.array([0.05])
        sigmas = pa.array([0.2])
        
        # Calculate Greeks for calls
        greeks = arrow_native.arrow_greeks(spots, strikes, times, rates, sigmas, True)
        
        # Check structure
        assert isinstance(greeks, dict)
        assert set(greeks.keys()) == {'delta', 'gamma', 'vega', 'theta', 'rho'}
        
        # Convert to numpy
        delta = greeks['delta'].to_numpy()
        gamma = greeks['gamma'].to_numpy()
        vega = greeks['vega'].to_numpy()
        
        # Delta should be between 0 and 1 for calls
        assert all(0 <= d <= 1 for d in delta), "Call delta should be between 0 and 1"
        
        # Delta should increase with spot price
        assert delta[0] < delta[1] < delta[2], "Delta should increase with spot"
        
        # Gamma should be positive
        assert all(g > 0 for g in gamma), "Gamma should be positive"
        
        # Vega should be positive
        assert all(v > 0 for v in vega), "Vega should be positive"
    
    def test_broadcasting_edge_cases(self):
        """Test edge cases for broadcasting."""
        # All scalars
        spots = pa.array([100.0])
        strikes = pa.array([100.0])
        times = pa.array([1.0])
        rates = pa.array([0.05])
        sigmas = pa.array([0.2])
        
        result = arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)
        assert len(result) == 1
        assert result.to_numpy()[0] > 0
        
        # Mixed lengths (should work with broadcasting)
        spots = pa.array([100.0, 105.0, 110.0])
        strikes = pa.array([100.0])  # Broadcasts
        times = pa.array([1.0, 0.5, 0.25])  # Same length as spots
        rates = pa.array([0.05])  # Broadcasts
        sigmas = pa.array([0.2, 0.22, 0.25])  # Same length as spots
        
        result = arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)
        assert len(result) == 3
    
    def test_black76_implementation(self):
        """Test Black76 model with broadcasting."""
        # Setup
        forwards = pa.array([100.0, 105.0, 110.0])
        strikes = pa.array([100.0])
        times = pa.array([1.0])
        rates = pa.array([0.05])
        sigmas = pa.array([0.2])
        
        # Calculate prices
        call_prices = arrow_native.arrow76_call_price(forwards, strikes, times, rates, sigmas)
        put_prices = arrow_native.arrow76_put_price(forwards, strikes, times, rates, sigmas)
        
        assert len(call_prices) == 3
        assert len(put_prices) == 3
        
        # Prices should increase/decrease appropriately
        calls = call_prices.to_numpy()
        puts = put_prices.to_numpy()
        
        assert calls[1] > calls[0]  # Call increases with forward
        assert calls[2] > calls[1]
        assert puts[1] < puts[0]  # Put decreases with forward
        assert puts[2] < puts[1]
    
    def test_black76_greeks(self):
        """Test Black76 Greeks calculation."""
        forwards = pa.array([100.0])
        strikes = pa.array([100.0])
        times = pa.array([1.0])
        rates = pa.array([0.05])
        sigmas = pa.array([0.2])
        
        greeks = arrow_native.arrow76_greeks(forwards, strikes, times, rates, sigmas, True)
        
        assert isinstance(greeks, dict)
        assert len(greeks) == 5
        
        # Check specific values for ATM option
        delta = greeks['delta'].to_numpy()[0]
        assert 0.4 < delta < 0.6, "ATM delta should be around 0.5"
    
    def test_error_handling(self):
        """Test that incompatible array lengths raise errors."""
        # Incompatible lengths (not 1 and not matching)
        spots = pa.array([100.0, 105.0])  # Length 2
        strikes = pa.array([95.0, 100.0, 105.0])  # Length 3
        times = pa.array([1.0])
        rates = pa.array([0.05])
        sigmas = pa.array([0.2])
        
        with pytest.raises(Exception) as exc_info:
            arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)
        
        assert "incompatible" in str(exc_info.value).lower()
    
    def test_large_array_performance(self):
        """Test that large arrays work correctly with broadcasting."""
        size = 10_000
        
        # Large array with broadcasting
        spots = pa.array(np.linspace(50, 150, size))
        strikes = pa.array([100.0])  # Scalar broadcasts to all
        times = pa.array([1.0])
        rates = pa.array([0.05])
        sigmas = pa.array([0.2])
        
        # Should complete without error
        result = arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)
        assert len(result) == size
        
        # Greeks should also work
        greeks = arrow_native.arrow_greeks(spots, strikes, times, rates, sigmas, True)
        assert len(greeks['delta']) == size
    
    def test_numerical_accuracy(self):
        """Test numerical accuracy against known values."""
        # Known Black-Scholes value
        # S=100, K=100, T=1, r=0.05, sigma=0.2
        # Expected call price ≈ 10.4506
        
        spots = pa.array([100.0])
        strikes = pa.array([100.0])
        times = pa.array([1.0])
        rates = pa.array([0.05])
        sigmas = pa.array([0.2])
        
        call_price = arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)
        price = call_price.to_numpy()[0]
        
        expected = 10.4506
        assert abs(price - expected) < 0.01, f"Expected {expected}, got {price}"
        
        # Test Greeks accuracy
        greeks = arrow_native.arrow_greeks(spots, strikes, times, rates, sigmas, True)
        delta = greeks['delta'].to_numpy()[0]
        
        expected_delta = 0.6368  # Known value
        assert abs(delta - expected_delta) < 0.01, f"Delta: expected {expected_delta}, got {delta}"


if __name__ == "__main__":
    # Run tests
    test = TestArrowNativeIntegration()
    test.test_module_imports()
    test.test_black_scholes_call_put_parity()
    test.test_greeks_consistency()
    test.test_broadcasting_edge_cases()
    test.test_black76_implementation()
    test.test_black76_greeks()
    test.test_error_handling()
    test.test_large_array_performance()
    test.test_numerical_accuracy()
    print("All integration tests passed!")