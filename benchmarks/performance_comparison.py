#!/usr/bin/env python3
"""
Performance Comparison Script
Compares current implementation with baseline and NumPy
"""

import numpy as np
import quantforge as qf
import time
from typing import Dict, List
import statistics
import json
from scipy.stats import norm

def benchmark_function(func, *args, warmup: int = 10, repeats: int = 100) -> Dict[str, float]:
    """Benchmark a function with warmup and multiple repeats"""
    # Warmup
    for _ in range(warmup):
        _ = func(*args)
    
    # Actual measurements
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        _ = func(*args)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    return {
        'min': min(times) * 1_000_000,  # Convert to microseconds
        'mean': statistics.mean(times) * 1_000_000,
        'median': statistics.median(times) * 1_000_000,
        'max': max(times) * 1_000_000,
        'stddev': statistics.stdev(times) * 1_000_000 if len(times) > 1 else 0
    }

def load_baseline_results(filepath: str = "/home/driller/work/quantforge/benchmarks/results/latest.json") -> Dict:
    """Load baseline benchmark results"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    baseline = {}
    for item in data.get('batch', []):
        size = item['size']
        baseline[size] = item['quantforge'] * 1_000_000  # Convert to microseconds
    
    return baseline

def numpy_black_scholes_call(s, k, t, r, sigma):
    """NumPy implementation of Black-Scholes call option pricing"""
    d1 = (np.log(s / k) + (r + 0.5 * sigma * sigma) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)
    return s * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)

def run_performance_comparison():
    """Run comprehensive performance comparison"""
    
    print("=" * 80)
    print("PERFORMANCE COMPARISON ANALYSIS")
    print("=" * 80)
    
    # Load baseline results
    try:
        baseline = load_baseline_results()
        print(f"\nBaseline loaded: {list(baseline.keys())} sizes available")
    except Exception as e:
        print(f"Warning: Could not load baseline: {e}")
        baseline = {}
    
    # Test parameters
    sizes = [100, 1000, 10000]
    k = 100.0
    t = 1.0
    r = 0.05
    sigma = 0.2
    
    results = {}
    
    for size in sizes:
        print(f"\n{'='*60}")
        print(f"Testing batch size: {size}")
        print(f"{'='*60}")
        
        # Prepare data
        spots = np.full(size, 100.0)
        
        # Test 1: Current QuantForge implementation
        print("\n1. Current QuantForge implementation:")
        qf_results = benchmark_function(
            qf.black_scholes.call_price_batch,
            spots, k, t, r, sigma
        )
        print(f"   Median: {qf_results['median']:.3f} μs")
        print(f"   Mean:   {qf_results['mean']:.3f} μs (±{qf_results['stddev']:.3f})")
        
        # Test 2: NumPy/SciPy implementation
        print("\n2. NumPy/SciPy implementation:")
        numpy_results = benchmark_function(
            numpy_black_scholes_call,
            spots, k, t, r, sigma
        )
        print(f"   Median: {numpy_results['median']:.3f} μs")
        print(f"   Mean:   {numpy_results['mean']:.3f} μs (±{numpy_results['stddev']:.3f})")
        
        # Comparisons
        print("\n3. Performance comparisons:")
        
        # vs NumPy
        speedup_numpy = numpy_results['median'] / qf_results['median']
        print(f"   vs NumPy: {speedup_numpy:.2f}x {'faster' if speedup_numpy > 1 else 'slower'}")
        
        # vs Baseline (if available)
        if size in baseline:
            baseline_time = baseline[size]
            diff_pct = ((qf_results['median'] - baseline_time) / baseline_time) * 100
            print(f"   vs Baseline: {diff_pct:+.1f}% ({'slower' if diff_pct > 0 else 'faster'})")
            print(f"      Baseline: {baseline_time:.3f} μs")
            print(f"      Current:  {qf_results['median']:.3f} μs")
        
        # Store results
        results[size] = {
            'quantforge': qf_results,
            'numpy': numpy_results,
            'baseline': baseline.get(size),
            'speedup_vs_numpy': speedup_numpy,
            'diff_vs_baseline_pct': diff_pct if size in baseline else None
        }
    
    # Summary table
    print("\n" + "=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Size':<10} {'Current (μs)':<15} {'Baseline (μs)':<15} {'Diff %':<10} {'vs NumPy':<10}")
    print("-" * 65)
    
    for size in sizes:
        r = results[size]
        current = r['quantforge']['median']
        baseline_val = r['baseline'] if r['baseline'] else 0
        diff = r['diff_vs_baseline_pct'] if r['diff_vs_baseline_pct'] is not None else 0
        speedup = r['speedup_vs_numpy']
        
        if baseline_val > 0:
            print(f"{size:<10} {current:<15.3f} {baseline_val:<15.3f} {diff:<+10.1f} {speedup:<10.2f}x")
        else:
            print(f"{size:<10} {current:<15.3f} {'N/A':<15} {'N/A':<10} {speedup:<10.2f}x")
    
    # Diagnosis
    print("\n" + "=" * 80)
    print("DIAGNOSIS")
    print("=" * 80)
    
    # Check for small batch degradation
    if 100 in results and results[100]['diff_vs_baseline_pct'] is not None:
        diff_100 = results[100]['diff_vs_baseline_pct']
        if diff_100 > 20:
            print(f"⚠️  Small batch (100) shows {diff_100:.1f}% degradation")
            print("   Likely cause: FFI overhead from Core+Bindings architecture")
            print("   Recommendation: Consider specialized path for small batches")
        elif diff_100 > 10:
            print(f"⚠️  Small batch (100) shows moderate {diff_100:.1f}% degradation")
            print("   Within acceptable range but could be improved")
        else:
            print(f"✅ Small batch (100) performance is good ({diff_100:+.1f}%)")
    
    # Check NumPy comparison
    for size in sizes:
        if size in results:
            speedup = results[size]['speedup_vs_numpy']
            if speedup < 1:
                print(f"⚠️  Size {size}: Slower than NumPy ({speedup:.2f}x)")
            elif speedup < 2:
                print(f"✓  Size {size}: Moderately faster than NumPy ({speedup:.2f}x)")
            else:
                print(f"✅ Size {size}: Significantly faster than NumPy ({speedup:.2f}x)")
    
    return results

def main():
    """Main entry point"""
    print("Starting performance comparison analysis...")
    print("Each measurement uses 100 repeats with 10 warmup runs\n")
    
    results = run_performance_comparison()
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    
    # Final verdict
    print("\nFINAL VERDICT:")
    
    all_good = True
    for size, r in results.items():
        if r['speedup_vs_numpy'] < 1:
            all_good = False
            print(f"❌ Size {size}: Performance regression vs NumPy")
        elif r['diff_vs_baseline_pct'] is not None and r['diff_vs_baseline_pct'] > 30:
            all_good = False
            print(f"⚠️  Size {size}: Significant regression vs baseline")
    
    if all_good:
        print("✅ Performance is acceptable across all batch sizes")
    else:
        print("\n🔧 Optimization needed for identified issues")

if __name__ == "__main__":
    main()