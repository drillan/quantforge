#!/usr/bin/env python
"""Native Apache Arrow benchmark - no NumPy conversion overhead."""

import time
import numpy as np
from typing import Dict, List, Tuple
import pyarrow as pa
import pyarrow.compute as pc

# Import our Rust implementation
import sys
sys.path.insert(0, '/home/driller/repo/quantforge/python')
from quantforge.quantforge import black_scholes


def create_arrow_arrays(size: int) -> Tuple[pa.Array, ...]:
    """Create native Arrow arrays for testing."""
    np.random.seed(42)
    
    # Create Arrow arrays directly
    spots = pa.array(np.random.uniform(80, 120, size), type=pa.float64())
    strikes = pa.array(np.full(size, 100.0), type=pa.float64())
    times = pa.array(np.full(size, 1.0), type=pa.float64())
    rates = pa.array(np.full(size, 0.05), type=pa.float64())
    sigmas = pa.array(np.random.uniform(0.15, 0.35, size), type=pa.float64())
    
    return spots, strikes, times, rates, sigmas


def benchmark_numpy_interface(size: int, runs: int = 100) -> Dict:
    """Benchmark with NumPy arrays (includes conversion overhead)."""
    np.random.seed(42)
    spots = np.random.uniform(80, 120, size)
    strikes = np.full(size, 100.0)
    times = np.full(size, 1.0)
    rates = np.full(size, 0.05)
    sigmas = np.random.uniform(0.15, 0.35, size)
    
    times_list = []
    
    # Warmup
    for _ in range(10):
        _ = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)
    
    # Actual benchmark
    for _ in range(runs):
        start = time.perf_counter()
        result = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)
        end = time.perf_counter()
        times_list.append((end - start) * 1e6)  # Convert to microseconds
    
    return {
        "mean": np.mean(times_list),
        "std": np.std(times_list),
        "min": np.min(times_list),
        "max": np.max(times_list),
        "median": np.median(times_list),
    }


def benchmark_arrow_native(size: int, runs: int = 100) -> Dict:
    """Benchmark with native Arrow arrays (if we had a direct Arrow API)."""
    # NOTE: This would require a new API that accepts Arrow arrays directly
    # For now, we'll measure the theoretical performance
    
    spots, strikes, times, rates, sigmas = create_arrow_arrays(size)
    
    # Convert to NumPy just for the benchmark (this simulates what would happen
    # if we had a native Arrow API)
    spots_np = spots.to_numpy(zero_copy_only=False)
    strikes_np = strikes.to_numpy(zero_copy_only=False)
    times_np = times.to_numpy(zero_copy_only=False)
    rates_np = rates.to_numpy(zero_copy_only=False)
    sigmas_np = sigmas.to_numpy(zero_copy_only=False)
    
    times_list = []
    
    # Warmup
    for _ in range(10):
        _ = black_scholes.call_price_batch(spots_np, strikes_np, times_np, rates_np, sigmas_np)
    
    # Actual benchmark
    for _ in range(runs):
        start = time.perf_counter()
        result = black_scholes.call_price_batch(spots_np, strikes_np, times_np, rates_np, sigmas_np)
        end = time.perf_counter()
        times_list.append((end - start) * 1e6)  # Convert to microseconds
    
    return {
        "mean": np.mean(times_list),
        "std": np.std(times_list),
        "min": np.min(times_list),
        "max": np.max(times_list),
        "median": np.median(times_list),
    }


def measure_conversion_overhead(size: int, runs: int = 1000) -> Dict:
    """Measure just the NumPy <-> Arrow conversion overhead."""
    np.random.seed(42)
    numpy_array = np.random.uniform(80, 120, size).astype(np.float64)
    
    # NumPy to Arrow
    numpy_to_arrow_times = []
    for _ in range(runs):
        start = time.perf_counter()
        arrow_array = pa.array(numpy_array, type=pa.float64())
        end = time.perf_counter()
        numpy_to_arrow_times.append((end - start) * 1e6)
    
    # Arrow to NumPy
    arrow_array = pa.array(numpy_array, type=pa.float64())
    arrow_to_numpy_times = []
    for _ in range(runs):
        start = time.perf_counter()
        numpy_result = arrow_array.to_numpy(zero_copy_only=False)
        end = time.perf_counter()
        arrow_to_numpy_times.append((end - start) * 1e6)
    
    return {
        "numpy_to_arrow": {
            "mean": np.mean(numpy_to_arrow_times),
            "min": np.min(numpy_to_arrow_times),
            "max": np.max(numpy_to_arrow_times),
        },
        "arrow_to_numpy": {
            "mean": np.mean(arrow_to_numpy_times),
            "min": np.min(arrow_to_numpy_times),
            "max": np.max(arrow_to_numpy_times),
        },
        "total_overhead": {
            "mean": np.mean(numpy_to_arrow_times) + np.mean(arrow_to_numpy_times),
        }
    }


def main():
    print("# Apache Arrow Native Performance Analysis")
    print("=" * 60)
    
    sizes = [100, 1_000, 10_000, 100_000]
    
    for size in sizes:
        print(f"\n## Size: {size:,} elements")
        print("-" * 40)
        
        # Measure conversion overhead
        overhead = measure_conversion_overhead(size)
        print(f"\n### Conversion Overhead:")
        print(f"  NumPy → Arrow: {overhead['numpy_to_arrow']['mean']:.2f}μs")
        print(f"  Arrow → NumPy: {overhead['arrow_to_numpy']['mean']:.2f}μs")
        print(f"  Total overhead: {overhead['total_overhead']['mean']:.2f}μs")
        
        # Benchmark NumPy interface
        numpy_result = benchmark_numpy_interface(size, runs=100)
        print(f"\n### NumPy Interface (with conversion):")
        print(f"  Mean: {numpy_result['mean']:.2f}μs")
        print(f"  Min:  {numpy_result['min']:.2f}μs")
        print(f"  Max:  {numpy_result['max']:.2f}μs")
        
        # Calculate theoretical native Arrow performance
        theoretical_native = numpy_result['mean'] - overhead['total_overhead']['mean']
        print(f"\n### Theoretical Native Arrow Performance:")
        print(f"  Estimated: {theoretical_native:.2f}μs")
        print(f"  Conversion overhead: {(overhead['total_overhead']['mean'] / numpy_result['mean']) * 100:.1f}%")
        
        # Compare with prototype expectations
        if size == 10_000:
            print(f"\n### Comparison with Prototype:")
            print(f"  Prototype expected: 166.71μs")
            print(f"  Current with NumPy: {numpy_result['mean']:.2f}μs")
            print(f"  Native Arrow (est): {theoretical_native:.2f}μs")
            print(f"  Gap to prototype:   {theoretical_native - 166.71:.2f}μs")


if __name__ == "__main__":
    main()