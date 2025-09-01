#!/usr/bin/env python
"""Quick test to verify parallel threshold change impact."""

import time
import numpy as np
from quantforge import black_scholes


def benchmark_simple(size: int, runs: int = 100):
    """Simple benchmark for quick testing."""
    np.random.seed(42)
    spots = np.random.uniform(80, 120, size)
    strikes = np.full(size, 100.0)
    times = np.full(size, 1.0)
    rates = np.full(size, 0.05)
    sigmas = np.random.uniform(0.15, 0.35, size)
    
    # Warmup
    for _ in range(10):
        _ = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)
    
    # Benchmark
    times_list = []
    for _ in range(runs):
        start = time.perf_counter()
        result = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)
        end = time.perf_counter()
        times_list.append((end - start) * 1e6)
    
    return np.mean(times_list), np.std(times_list)


def main():
    print("# Parallel Threshold Impact Test")
    print("=" * 60)
    print("Testing with new threshold = 10,000 (was 50,000)")
    print()
    
    # Reference times from prototype
    prototype_ref = {
        1_000: None,
        10_000: 166.71,  # μs
        50_000: None,
        100_000: None,
    }
    
    # Previous measurements with 50K threshold
    previous_50k = {
        1_000: 41.76,
        10_000: 245.35,  # Much slower!
        50_000: 815.44,
        100_000: 1355.20,
    }
    
    sizes = [1_000, 10_000, 50_000, 100_000]
    
    print("Size        Current Time    Previous (50K)    Change       Prototype")
    print("-" * 70)
    
    for size in sizes:
        mean_time, std_time = benchmark_simple(size, runs=50 if size < 50_000 else 20)
        
        prev_time = previous_50k.get(size)
        if prev_time:
            change = mean_time - prev_time
            pct_change = (change / prev_time) * 100
            change_str = f"{change:+8.2f}μs ({pct_change:+.1f}%)"
        else:
            change_str = "N/A"
        
        proto_time = prototype_ref.get(size)
        if proto_time:
            proto_diff = mean_time - proto_time
            proto_pct = (proto_diff / proto_time) * 100
            proto_str = f"{proto_time:.2f}μs ({proto_pct:+.1f}%)"
        else:
            proto_str = "N/A"
        
        print(f"{size:7,}     {mean_time:8.2f}μs     {prev_time:8.2f}μs     {change_str:20s}     {proto_str}")
    
    print()
    print("## Analysis")
    print("-" * 40)
    
    # Check 10K performance specifically
    mean_10k, _ = benchmark_simple(10_000, runs=100)
    proto_10k = 166.71
    prev_10k = 245.35
    
    improvement = ((prev_10k - mean_10k) / prev_10k) * 100
    proto_diff = abs(mean_10k - proto_10k)
    proto_pct = (proto_diff / proto_10k) * 100
    
    print(f"10,000 elements performance:")
    print(f"  Current:     {mean_10k:.2f}μs")
    print(f"  Previous:    {prev_10k:.2f}μs")
    print(f"  Prototype:   {proto_10k:.2f}μs")
    print(f"  Improvement: {improvement:.1f}% vs previous")
    print(f"  Gap to prototype: {proto_pct:.1f}%")
    
    if proto_pct < 5:
        print(f"\n✅ SUCCESS: Within 5% of prototype performance!")
    elif proto_pct < 10:
        print(f"\n✅ GOOD: Within 10% of prototype performance")
    else:
        print(f"\n⚠️  Still {proto_pct:.1f}% slower than prototype")
    
    # Check if parallelization is happening
    print("\n## Parallelization Status")
    print("-" * 40)
    print("With threshold = 10,000:")
    print("  1,000 elements: Sequential (< 10,000)")
    print(" 10,000 elements: Parallel (>= 10,000) ✅")
    print(" 50,000 elements: Parallel (>= 10,000) ✅")
    print("100,000 elements: Parallel (>= 10,000) ✅")


if __name__ == "__main__":
    main()