"""
Benchmarks for Apache Arrow Native API.

Compares performance between:
1. Direct NumPy API (existing)
2. Arrow Native API
3. NumPy compatibility layer
"""

import time
import numpy as np
import pyarrow as pa
import quantforge.arrow_api as qf_arrow
import quantforge.numpy_compat as qf_numpy
from quantforge import black_scholes


def benchmark_batch_processing(size: int = 10_000):
    """Benchmark batch processing with different APIs."""
    
    # Generate test data
    np.random.seed(42)
    spots = np.random.uniform(80, 120, size)
    strikes = np.random.uniform(80, 120, size)
    times = np.random.uniform(0.1, 2.0, size)
    rates = np.random.uniform(0.01, 0.1, size)
    sigmas = np.random.uniform(0.1, 0.5, size)
    
    # Convert to Arrow for Arrow API
    spots_arrow = pa.array(spots)
    strikes_arrow = pa.array(strikes)
    times_arrow = pa.array(times)
    rates_arrow = pa.array(rates)
    sigmas_arrow = pa.array(sigmas)
    
    # Warm up
    for _ in range(3):
        _ = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)
        _ = qf_arrow.call_price(spots_arrow, strikes_arrow, times_arrow, rates_arrow, sigmas_arrow)
    
    # Benchmark: Direct NumPy API
    iterations = 100
    start = time.perf_counter()
    for _ in range(iterations):
        result_numpy = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)
    numpy_time = (time.perf_counter() - start) / iterations * 1e6  # μs
    
    # Benchmark: Arrow API (with pre-converted arrays)
    start = time.perf_counter()
    for _ in range(iterations):
        result_arrow = qf_arrow.call_price(spots_arrow, strikes_arrow, times_arrow, rates_arrow, sigmas_arrow)
    arrow_time = (time.perf_counter() - start) / iterations * 1e6  # μs
    
    # Benchmark: Arrow API (including conversion from NumPy)
    start = time.perf_counter()
    for _ in range(iterations):
        s_a = pa.array(spots)
        k_a = pa.array(strikes)
        t_a = pa.array(times)
        r_a = pa.array(rates)
        sig_a = pa.array(sigmas)
        result_arrow_conv = qf_arrow.call_price(s_a, k_a, t_a, r_a, sig_a)
    arrow_with_conversion_time = (time.perf_counter() - start) / iterations * 1e6  # μs
    
    # Benchmark: NumPy compat layer
    start = time.perf_counter()
    for _ in range(iterations):
        result_compat = qf_numpy.call_price_numpy(spots, strikes, times, rates, sigmas)
    compat_time = (time.perf_counter() - start) / iterations * 1e6  # μs
    
    return {
        'size': size,
        'numpy_direct': numpy_time,
        'arrow_native': arrow_time,
        'arrow_with_conversion': arrow_with_conversion_time,
        'numpy_compat': compat_time,
    }


def benchmark_scaling():
    """Benchmark how performance scales with data size."""
    sizes = [100, 1_000, 10_000, 100_000, 1_000_000]
    results = []
    
    for size in sizes:
        print(f"Benchmarking size: {size:,}")
        result = benchmark_batch_processing(size)
        results.append(result)
        
        # Print immediate results
        print(f"  NumPy direct: {result['numpy_direct']:.2f} μs")
        print(f"  Arrow native: {result['arrow_native']:.2f} μs")
        print(f"  Arrow w/ conv: {result['arrow_with_conversion']:.2f} μs")
        print(f"  NumPy compat: {result['numpy_compat']:.2f} μs")
        print(f"  Speedup (Arrow vs NumPy): {result['numpy_direct']/result['arrow_native']:.2f}x")
        print()
    
    return results


def benchmark_broadcasting():
    """Benchmark broadcasting performance."""
    size = 10_000
    
    # Generate test data - mix of scalars and arrays
    np.random.seed(42)
    spots = np.random.uniform(80, 120, size)
    strikes = 100.0  # Scalar
    times = 1.0  # Scalar
    rates = 0.05  # Scalar
    sigmas = np.random.uniform(0.1, 0.5, size)
    
    # Convert to Arrow
    spots_arrow = pa.array(spots)
    strikes_arrow = pa.array([strikes])  # Scalar as single-element array
    times_arrow = pa.array([times])
    rates_arrow = pa.array([rates])
    sigmas_arrow = pa.array(sigmas)
    
    # Apply broadcasting
    broadcasted = qf_arrow.broadcast_arrays(
        spots_arrow, strikes_arrow, times_arrow, rates_arrow, sigmas_arrow
    )
    
    iterations = 100
    
    # Benchmark with broadcasting
    start = time.perf_counter()
    for _ in range(iterations):
        bc = qf_arrow.broadcast_arrays(
            spots_arrow, strikes_arrow, times_arrow, rates_arrow, sigmas_arrow
        )
        result = qf_arrow.call_price(*bc)
    broadcast_time = (time.perf_counter() - start) / iterations * 1e6
    
    # Benchmark without broadcasting (pre-expanded)
    strikes_expanded = pa.array([strikes] * size)
    times_expanded = pa.array([times] * size)
    rates_expanded = pa.array([rates] * size)
    
    start = time.perf_counter()
    for _ in range(iterations):
        result = qf_arrow.call_price(
            spots_arrow, strikes_expanded, times_expanded, rates_expanded, sigmas_arrow
        )
    no_broadcast_time = (time.perf_counter() - start) / iterations * 1e6
    
    print(f"Broadcasting benchmark (size={size:,}):")
    print(f"  With broadcasting: {broadcast_time:.2f} μs")
    print(f"  Pre-expanded: {no_broadcast_time:.2f} μs")
    print(f"  Broadcasting overhead: {broadcast_time - no_broadcast_time:.2f} μs")
    print(f"  Overhead percentage: {(broadcast_time/no_broadcast_time - 1)*100:.1f}%")


def main():
    """Run all benchmarks."""
    print("=" * 60)
    print("Apache Arrow Native API Benchmarks")
    print("=" * 60)
    print()
    
    print("1. Scaling Benchmark")
    print("-" * 40)
    scaling_results = benchmark_scaling()
    
    print()
    print("2. Broadcasting Benchmark")
    print("-" * 40)
    benchmark_broadcasting()
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    # Print summary table
    print(f"{'Size':<10} {'NumPy':<12} {'Arrow':<12} {'Speedup':<10}")
    print("-" * 46)
    for result in scaling_results:
        speedup = result['numpy_direct'] / result['arrow_native']
        print(f"{result['size']:<10,} {result['numpy_direct']:<12.2f} {result['arrow_native']:<12.2f} {speedup:<10.2f}x")
    
    print()
    print("Note: Times are in microseconds (μs)")
    print("Arrow Native shows performance with pre-converted Arrow arrays")
    print("Real-world usage may include conversion overhead")


if __name__ == "__main__":
    main()