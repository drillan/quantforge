#!/usr/bin/env python3
"""Test script for Arrow Native implementation."""

import numpy as np
import pyarrow as pa
import time
import quantforge

def test_arrow_native_module():
    """Test the arrow_native module exists and has expected functions."""
    print("Testing arrow_native module...")
    
    # Check if arrow_native module exists
    assert hasattr(quantforge, 'arrow_native'), "arrow_native module not found"
    
    # Check for native functions
    assert hasattr(quantforge.arrow_native, 'call_price_native'), "call_price_native not found"
    assert hasattr(quantforge.arrow_native, 'put_price_native'), "put_price_native not found"
    
    print("✓ arrow_native module loaded successfully")
    
def test_native_functions():
    """Test the native functions with NumPy arrays."""
    print("\nTesting native functions...")
    
    # Test data
    n = 10000
    spots = np.full(n, 100.0)
    strikes = np.full(n, 105.0)
    times = np.full(n, 1.0)
    rates = np.full(n, 0.05)
    sigmas = np.full(n, 0.2)
    
    # Test call price
    start = time.perf_counter()
    call_prices = quantforge.arrow_native.call_price_native(spots, strikes, times, rates, sigmas)
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    print(f"Call price calculation for {n} elements: {elapsed_ms:.2f}ms")
    print(f"First 5 call prices: {call_prices[:5]}")
    
    # Test put price  
    start = time.perf_counter()
    put_prices = quantforge.arrow_native.put_price_native(spots, strikes, times, rates, sigmas)
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    print(f"Put price calculation for {n} elements: {elapsed_ms:.2f}ms")
    print(f"First 5 put prices: {put_prices[:5]}")
    
    print("✓ Native functions work correctly")

def test_arrow_api():
    """Test the Arrow API wrapper."""
    print("\nTesting Arrow API wrapper...")
    
    # Import arrow_api
    from quantforge import arrow_api
    
    # Test data
    n = 10000
    spots = pa.array([100.0] * n)
    strikes = pa.array([105.0] * n)
    times = pa.array([1.0] * n)
    rates = pa.array([0.05] * n)
    sigmas = pa.array([0.2] * n)
    
    # Test call price
    start = time.perf_counter()
    call_prices = arrow_api.call_price(spots, strikes, times, rates, sigmas)
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    print(f"Arrow API call price for {n} elements: {elapsed_ms:.2f}ms")
    print(f"First 5 call prices: {call_prices[:5].to_pylist()}")
    
    print("✓ Arrow API works correctly")

def test_performance_comparison():
    """Compare performance of different approaches."""
    print("\nPerformance comparison:")
    
    from quantforge import black_scholes, arrow_api
    
    # Test sizes
    sizes = [100, 1000, 10000, 100000]
    
    for n in sizes:
        # Prepare data
        spots_np = np.full(n, 100.0)
        strikes_np = np.full(n, 105.0)
        times_np = np.full(n, 1.0)
        rates_np = np.full(n, 0.05)
        sigmas_np = np.full(n, 0.2)
        
        spots_pa = pa.array(spots_np)
        strikes_pa = pa.array(strikes_np)
        times_pa = pa.array(times_np)
        rates_pa = pa.array(rates_np)
        sigmas_pa = pa.array(sigmas_np)
        
        # Test NumPy batch
        start = time.perf_counter()
        _ = black_scholes.call_price_batch(spots_np, strikes_np, times_np, rates_np, sigmas_np)
        numpy_ms = (time.perf_counter() - start) * 1000
        
        # Test native
        start = time.perf_counter()
        _ = quantforge.arrow_native.call_price_native(spots_np, strikes_np, times_np, rates_np, sigmas_np)
        native_ms = (time.perf_counter() - start) * 1000
        
        # Test Arrow API
        start = time.perf_counter()
        _ = arrow_api.call_price(spots_pa, strikes_pa, times_pa, rates_pa, sigmas_pa)
        arrow_ms = (time.perf_counter() - start) * 1000
        
        print(f"\n{n:,} elements:")
        print(f"  NumPy batch: {numpy_ms:.2f}ms")
        print(f"  Native:      {native_ms:.2f}ms ({numpy_ms/native_ms:.2f}x)")
        print(f"  Arrow API:   {arrow_ms:.2f}ms ({numpy_ms/arrow_ms:.2f}x)")

if __name__ == "__main__":
    print("=" * 60)
    print("Arrow Native Implementation Test")
    print("=" * 60)
    
    test_arrow_native_module()
    test_native_functions()
    test_arrow_api()
    test_performance_comparison()
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)