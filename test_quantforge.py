#!/usr/bin/env python3
"""Test QuantForge basic functionality after refactoring"""

import numpy as np
import quantforge

def test_scalar():
    """Test scalar Black-Scholes calculations"""
    # Call price
    call_price = quantforge.black_scholes.call_price(
        s=100, k=100, t=1, r=0.05, sigma=0.2
    )
    print(f"Call price: {call_price:.4f}")
    assert 10 < call_price < 15  # Reasonable range
    
    # Put price
    put_price = quantforge.black_scholes.put_price(
        s=100, k=100, t=1, r=0.05, sigma=0.2
    )
    print(f"Put price: {put_price:.4f}")
    assert 5 < put_price < 10  # Reasonable range
    
    # Greeks
    greeks = quantforge.black_scholes.greeks(
        s=100, k=100, t=1, r=0.05, sigma=0.2
    )
    print(f"Greeks: {greeks}")
    assert 'delta' in greeks
    assert 'gamma' in greeks
    assert 'vega' in greeks
    assert 'theta' in greeks
    assert 'rho' in greeks

def test_batch():
    """Test batch Black-Scholes calculations"""
    spots = np.array([95, 100, 105])
    strikes = np.array([100, 100, 100])
    times = np.array([1, 1, 1])
    rates = np.array([0.05, 0.05, 0.05])
    sigmas = np.array([0.2, 0.2, 0.2])
    
    # Call prices
    call_prices = quantforge.black_scholes.call_price_batch(
        spots=spots, strikes=strikes, times=times, rates=rates, sigmas=sigmas
    )
    print(f"Call prices batch: {call_prices}")
    assert len(call_prices) == 3
    assert all(price > 0 for price in call_prices)
    
    # Put prices
    put_prices = quantforge.black_scholes.put_price_batch(
        spots=spots, strikes=strikes, times=times, rates=rates, sigmas=sigmas
    )
    print(f"Put prices batch: {put_prices}")
    assert len(put_prices) == 3
    assert all(price > 0 for price in put_prices)

def test_broadcasting():
    """Test broadcasting in batch calculations"""
    spots = np.array([90, 100, 110])
    strikes = 100.0  # Scalar - should broadcast
    times = 1.0
    rates = 0.05
    sigmas = 0.2
    
    call_prices = quantforge.black_scholes.call_price_batch(
        spots=spots, strikes=strikes, times=times, rates=rates, sigmas=sigmas
    )
    print(f"Broadcasting test: {call_prices}")
    assert len(call_prices) == 3
    assert call_prices[0] < call_prices[1] < call_prices[2]  # Increasing with spot

def test_arrow_native():
    """Test arrow native module"""
    print(f"Arrow native functions: {dir(quantforge.arrow_native)}")
    # Currently placeholder, will have functions when pyo3-arrow is fully integrated

if __name__ == "__main__":
    print("=" * 60)
    print("Testing QuantForge after refactoring")
    print("=" * 60)
    
    print("\n1. Scalar tests:")
    test_scalar()
    
    print("\n2. Batch tests:")
    test_batch()
    
    print("\n3. Broadcasting tests:")
    test_broadcasting()
    
    print("\n4. Arrow native module:")
    test_arrow_native()
    
    print("\n✅ All tests passed!")
    print("=" * 60)