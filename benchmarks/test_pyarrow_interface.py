#!/usr/bin/env python
"""Test if current API accepts pyarrow.Array directly."""

import numpy as np
import pyarrow as pa
import sys
sys.path.insert(0, '/home/driller/repo/quantforge/python')
from quantforge import black_scholes

def test_current_interface():
    """Test what types the current API accepts."""
    
    print("# Current Python Binding Interface Analysis")
    print("=" * 60)
    
    # Create test data
    size = 100
    np.random.seed(42)
    
    # NumPy arrays
    numpy_spots = np.random.uniform(80, 120, size)
    numpy_strikes = np.full(size, 100.0)
    numpy_times = np.full(size, 1.0)
    numpy_rates = np.full(size, 0.05)
    numpy_sigmas = np.random.uniform(0.15, 0.35, size)
    
    # PyArrow arrays
    arrow_spots = pa.array(numpy_spots)
    arrow_strikes = pa.array(numpy_strikes)
    arrow_times = pa.array(numpy_times)
    arrow_rates = pa.array(numpy_rates)
    arrow_sigmas = pa.array(numpy_sigmas)
    
    print("\n## Test 1: NumPy arrays (current supported)")
    try:
        result = black_scholes.call_price_batch(
            numpy_spots, numpy_strikes, numpy_times, numpy_rates, numpy_sigmas
        )
        print(f"✅ NumPy arrays: Success")
        print(f"   Result type: {type(result)}")
        print(f"   Result shape: {result.shape}")
    except Exception as e:
        print(f"❌ NumPy arrays: Failed")
        print(f"   Error: {e}")
    
    print("\n## Test 2: PyArrow arrays (desired)")
    try:
        result = black_scholes.call_price_batch(
            arrow_spots, arrow_strikes, arrow_times, arrow_rates, arrow_sigmas
        )
        print(f"✅ PyArrow arrays: Success")
        print(f"   Result type: {type(result)}")
    except Exception as e:
        print(f"❌ PyArrow arrays: Failed")
        print(f"   Error: {e}")
        print(f"   Error type: {type(e).__name__}")
    
    print("\n## Test 3: PyArrow arrays converted to NumPy (workaround)")
    try:
        # Current workaround: manual conversion
        result = black_scholes.call_price_batch(
            arrow_spots.to_numpy(),
            arrow_strikes.to_numpy(),
            arrow_times.to_numpy(),
            arrow_rates.to_numpy(),
            arrow_sigmas.to_numpy()
        )
        print(f"✅ PyArrow → NumPy conversion: Success")
        print(f"   This is the current workaround")
    except Exception as e:
        print(f"❌ PyArrow → NumPy conversion: Failed")
        print(f"   Error: {e}")
    
    print("\n## Analysis of conversion overhead")
    print("-" * 40)
    
    # Measure conversion cost
    import time
    
    # PyArrow to NumPy
    start = time.perf_counter()
    for _ in range(1000):
        _ = arrow_spots.to_numpy()
    end = time.perf_counter()
    arrow_to_numpy_us = (end - start) / 1000 * 1e6
    
    # NumPy to PyArrow  
    start = time.perf_counter()
    for _ in range(1000):
        _ = pa.array(numpy_spots)
    end = time.perf_counter()
    numpy_to_arrow_us = (end - start) / 1000 * 1e6
    
    print(f"PyArrow → NumPy: {arrow_to_numpy_us:.2f}μs per array")
    print(f"NumPy → PyArrow: {numpy_to_arrow_us:.2f}μs per array")
    print(f"Total for 5 arrays: {arrow_to_numpy_us * 5:.2f}μs")
    
    print("\n## Current data flow (inefficient)")
    print("-" * 40)
    print("1. User loads data with pyarrow (e.g., from Parquet)")
    print("2. User converts pyarrow.Array → NumPy (unnecessary)")
    print("3. QuantForge converts NumPy → Arrow internally (redundant)")
    print("4. Computation in Arrow")
    print("5. QuantForge converts Arrow → NumPy for result")
    print("\n⚠️  Two unnecessary conversions!")
    
    print("\n## Ideal data flow")
    print("-" * 40)
    print("1. User loads data with pyarrow")
    print("2. QuantForge accepts pyarrow.Array directly")
    print("3. Computation in Arrow (zero-copy)")
    print("4. Return pyarrow.Array or NumPy (user choice)")
    print("\n✅ Zero unnecessary conversions!")


if __name__ == "__main__":
    test_current_interface()