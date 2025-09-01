#!/usr/bin/env python
"""Detailed analysis of pyarrow.Array handling."""

import numpy as np
import pyarrow as pa
import time
import sys
sys.path.insert(0, '/home/driller/repo/quantforge/python')
from quantforge import black_scholes

def analyze_data_flow():
    """Analyze what's actually happening with pyarrow.Array."""
    
    print("# Detailed PyArrow Interface Analysis")
    print("=" * 60)
    
    # Create test data
    size = 10000
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
    
    print(f"\n## Data types")
    print(f"NumPy array type: {type(numpy_spots)}")
    print(f"PyArrow array type: {type(arrow_spots)}")
    print(f"PyArrow dtype: {arrow_spots.type}")
    
    # Check if PyArrow implements buffer protocol
    print(f"\n## Buffer protocol check")
    print(f"NumPy has __array__: {hasattr(numpy_spots, '__array__')}")
    print(f"PyArrow has __array__: {hasattr(arrow_spots, '__array__')}")
    print(f"PyArrow has __array_interface__: {hasattr(arrow_spots, '__array_interface__')}")
    
    # Test if PyArrow's __array__ is being called
    if hasattr(arrow_spots, '__array__'):
        print(f"PyArrow.__array__ returns: {type(arrow_spots.__array__())}")
    
    print(f"\n## Performance comparison (10,000 elements)")
    print("-" * 40)
    
    # Benchmark NumPy arrays
    runs = 100
    times_numpy = []
    for _ in range(runs):
        start = time.perf_counter()
        result = black_scholes.call_price_batch(
            numpy_spots, numpy_strikes, numpy_times, numpy_rates, numpy_sigmas
        )
        end = time.perf_counter()
        times_numpy.append((end - start) * 1e6)
    
    avg_numpy = np.mean(times_numpy)
    print(f"NumPy arrays: {avg_numpy:.2f}μs (avg of {runs} runs)")
    
    # Benchmark PyArrow arrays
    times_arrow = []
    for _ in range(runs):
        start = time.perf_counter()
        result = black_scholes.call_price_batch(
            arrow_spots, arrow_strikes, arrow_times, arrow_rates, arrow_sigmas
        )
        end = time.perf_counter()
        times_arrow.append((end - start) * 1e6)
    
    avg_arrow = np.mean(times_arrow)
    print(f"PyArrow arrays: {avg_arrow:.2f}μs (avg of {runs} runs)")
    
    # Benchmark explicit conversion
    times_converted = []
    for _ in range(runs):
        start = time.perf_counter()
        result = black_scholes.call_price_batch(
            arrow_spots.to_numpy(),
            arrow_strikes.to_numpy(),
            arrow_times.to_numpy(),
            arrow_rates.to_numpy(),
            arrow_sigmas.to_numpy()
        )
        end = time.perf_counter()
        times_converted.append((end - start) * 1e6)
    
    avg_converted = np.mean(times_converted)
    print(f"Explicit conversion: {avg_converted:.2f}μs (avg of {runs} runs)")
    
    print(f"\n## Analysis")
    print("-" * 40)
    overhead = avg_arrow - avg_numpy
    print(f"PyArrow overhead: {overhead:.2f}μs ({overhead/avg_numpy*100:.1f}%)")
    
    if overhead > 5:
        print("⚠️  PyArrow arrays have significant overhead")
        print("   This suggests automatic conversion is happening")
    else:
        print("✅ PyArrow arrays have minimal overhead")
        print("   This suggests zero-copy or efficient handling")
    
    print(f"\n## Memory layout comparison")
    print("-" * 40)
    
    # Check memory layout
    numpy_info = {
        'dtype': numpy_spots.dtype,
        'shape': numpy_spots.shape,
        'strides': numpy_spots.strides,
        'contiguous': numpy_spots.flags['C_CONTIGUOUS'],
        'data_ptr': numpy_spots.__array_interface__['data'][0]
    }
    
    arrow_as_numpy = arrow_spots.__array__() if hasattr(arrow_spots, '__array__') else None
    if arrow_as_numpy is not None:
        arrow_info = {
            'dtype': arrow_as_numpy.dtype,
            'shape': arrow_as_numpy.shape,
            'strides': arrow_as_numpy.strides,
            'contiguous': arrow_as_numpy.flags['C_CONTIGUOUS'],
            'data_ptr': arrow_as_numpy.__array_interface__['data'][0]
        }
        
        print(f"NumPy array: {numpy_info}")
        print(f"Arrow array (via __array__): {arrow_info}")
        
        if numpy_info['data_ptr'] != arrow_info['data_ptr']:
            print("⚠️  Different memory addresses - copy is happening!")
        else:
            print("✅ Same memory address - zero-copy!")
    
    print(f"\n## Conclusion")
    print("-" * 40)
    if avg_arrow > avg_numpy * 1.1:  # More than 10% slower
        print("❌ Current implementation does NOT efficiently handle pyarrow.Array")
        print("   PyArrow's __array__() method is being called (implicit conversion)")
        print("   This creates unnecessary copies")
    else:
        print("✅ Current implementation handles pyarrow.Array reasonably well")
        print("   But explicit pyarrow support would be better")
    
    print("\n## Recommendation")
    print("-" * 40)
    print("Add explicit pyarrow.Array support to avoid implicit conversions:")
    print("1. Create overloaded functions that accept pyarrow.Array")
    print("2. Use Arrow's native compute kernels directly")
    print("3. Return pyarrow.Array for Arrow inputs (preserve type)")
    

if __name__ == "__main__":
    analyze_data_flow()