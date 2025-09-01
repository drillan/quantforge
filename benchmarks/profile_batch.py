#!/usr/bin/env python3
"""
Profiling script for batch processing performance analysis.
This script is designed to be called with flamegraph for detailed profiling.
"""

import numpy as np
import quantforge as qf
import sys
from typing import Optional

def profile_batch_100():
    """Profile batch size 100 - where we see 38% degradation"""
    spots = np.full(100, 100.0)
    k = 100.0
    t = 1.0
    r = 0.05
    sigma = 0.2
    
    # Run multiple iterations for stable profiling
    for _ in range(10000):
        results = qf.black_scholes.call_price_batch(spots, k, t, r, sigma)
    
    return results

def profile_batch_1000():
    """Profile batch size 1000 - where we see 17% degradation"""
    spots = np.full(1000, 100.0)
    k = 100.0
    t = 1.0
    r = 0.05
    sigma = 0.2
    
    # Run multiple iterations
    for _ in range(1000):
        results = qf.black_scholes.call_price_batch(spots, k, t, r, sigma)
    
    return results

def profile_batch_10000():
    """Profile batch size 10000 - where we see 3% degradation"""
    spots = np.full(10000, 100.0)
    k = 100.0
    t = 1.0
    r = 0.05
    sigma = 0.2
    
    # Run multiple iterations
    for _ in range(100):
        results = qf.black_scholes.call_price_batch(spots, k, t, r, sigma)
    
    return results

def main(size: Optional[int] = None):
    """Main profiling entry point"""
    if size == 100:
        print("Profiling batch size 100...")
        profile_batch_100()
    elif size == 1000:
        print("Profiling batch size 1000...")
        profile_batch_1000()
    elif size == 10000:
        print("Profiling batch size 10000...")
        profile_batch_10000()
    else:
        # Run all profiles
        print("Profiling all batch sizes...")
        profile_batch_100()
        profile_batch_1000()
        profile_batch_10000()
    
    print(f"Profiling complete for size: {size if size else 'all'}")

if __name__ == "__main__":
    size = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(size)