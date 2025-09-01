#!/usr/bin/env python3
"""
FFI Overhead Analysis Script
Measures the overhead of different components in the Python-Rust FFI boundary
"""

import numpy as np
import quantforge as qf
import time
from typing import Dict, List
import statistics

def measure_with_repeats(func, *args, repeats: int = 100) -> Dict[str, float]:
    """Measure a function with multiple repeats and return statistics"""
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        result = func(*args)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    return {
        'min': min(times) * 1_000_000,  # Convert to microseconds
        'mean': statistics.mean(times) * 1_000_000,
        'median': statistics.median(times) * 1_000_000,
        'max': max(times) * 1_000_000,
        'stddev': statistics.stdev(times) * 1_000_000 if len(times) > 1 else 0
    }

def analyze_ffi_overhead(sizes: List[int]) -> None:
    """Analyze FFI overhead for different batch sizes"""
    
    print("=" * 80)
    print("FFI OVERHEAD ANALYSIS")
    print("=" * 80)
    
    # Standard parameters
    k = 100.0
    t = 1.0
    r = 0.05
    sigma = 0.2
    
    for size in sizes:
        print(f"\n{'='*40}")
        print(f"Batch size: {size}")
        print(f"{'='*40}")
        
        # Prepare data
        spots = np.full(size, 100.0)
        strikes = np.full(size, k)
        times = np.full(size, t)
        rates = np.full(size, r)
        sigmas = np.full(size, sigma)
        
        # Warm up
        for _ in range(10):
            qf.black_scholes.call_price_batch(spots, k, t, r, sigma)
        
        # Test 1: Minimal FFI (baseline)
        print("\n1. Minimal FFI (baseline):")
        results = measure_with_repeats(qf.instrumented.minimal_ffi_call, size)
        baseline = results['median']
        print(f"   Median: {results['median']:.3f} μs")
        print(f"   Min-Max: {results['min']:.3f} - {results['max']:.3f} μs")
        
        # Test 2: With ArrayLike conversion
        print("\n2. With ArrayLike conversion:")
        results = measure_with_repeats(
            qf.instrumented.ffi_with_conversion,
            spots, strikes, times, rates, sigmas
        )
        conversion_overhead = results['median'] - baseline
        print(f"   Median: {results['median']:.3f} μs")
        print(f"   Overhead vs baseline: {conversion_overhead:.3f} μs ({conversion_overhead/baseline*100:.1f}%)")
        
        # Test 3: With BroadcastIterator
        print("\n3. With BroadcastIterator:")
        results = measure_with_repeats(
            qf.instrumented.ffi_with_broadcast,
            spots, strikes, times, rates, sigmas
        )
        broadcast_overhead = results['median'] - baseline
        print(f"   Median: {results['median']:.3f} μs")
        print(f"   Overhead vs baseline: {broadcast_overhead:.3f} μs ({broadcast_overhead/baseline*100:.1f}%)")
        
        # Test 4: Full implementation (instrumented)
        print("\n4. Full implementation (with timing output):")
        # Run once to see the instrumented output
        print("   Running instrumented version...")
        _ = qf.instrumented.call_price_batch_instrumented(
            spots, strikes, times, rates, sigmas
        )
        
        # Test 5: Regular implementation for comparison
        print("\n5. Regular implementation:")
        results = measure_with_repeats(
            qf.black_scholes.call_price_batch,
            spots, k, t, r, sigma
        )
        print(f"   Median: {results['median']:.3f} μs")
        print(f"   Min-Max: {results['min']:.3f} - {results['max']:.3f} μs")
        
        # Summary
        print(f"\n{'='*40}")
        print(f"SUMMARY for size {size}:")
        print(f"  ArrayLike conversion: {conversion_overhead:.3f} μs")
        print(f"  Broadcast iterator:   {broadcast_overhead - conversion_overhead:.3f} μs")
        print(f"  Total FFI overhead:   {broadcast_overhead:.3f} μs")

def main():
    """Main entry point"""
    sizes = [100, 1000, 10000]
    
    print("Testing FFI overhead components...")
    print("Each measurement is based on 100 repeats")
    
    analyze_ffi_overhead(sizes)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()