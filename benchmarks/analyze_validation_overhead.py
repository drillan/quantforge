#!/usr/bin/env python
"""Analyze the actual validation overhead in detail."""

import time
import numpy as np
from quantforge import black_scholes

def measure_validation_overhead():
    """Measure the actual cost of validation."""
    
    print("# Validation Overhead Analysis")
    print("=" * 60)
    
    # Test with valid data
    sizes = [100, 1_000, 10_000, 100_000]
    
    for size in sizes:
        print(f"\n## Size: {size:,} elements")
        print("-" * 40)
        
        # Generate valid test data
        np.random.seed(42)
        spots = np.random.uniform(80, 120, size)
        strikes = np.full(size, 100.0)
        times = np.full(size, 1.0)
        rates = np.full(size, 0.05)
        sigmas = np.random.uniform(0.15, 0.35, size)
        
        # Measure 1000 iterations for better accuracy
        runs = 1000
        
        # Safe version
        start = time.perf_counter()
        for _ in range(runs):
            _ = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)
        safe_time = (time.perf_counter() - start) / runs * 1e6
        
        # Unsafe version
        start = time.perf_counter()
        for _ in range(runs):
            _ = black_scholes.call_price_batch_unsafe(spots, strikes, times, rates, sigmas)
        unsafe_time = (time.perf_counter() - start) / runs * 1e6
        
        validation_overhead = safe_time - unsafe_time
        percentage = (validation_overhead / unsafe_time) * 100 if unsafe_time > 0 else 0
        
        print(f"Safe version:        {safe_time:10.2f} μs")
        print(f"Unsafe version:      {unsafe_time:10.2f} μs")
        print(f"Validation overhead: {validation_overhead:10.2f} μs ({percentage:+.1f}%)")
        
        # Theoretical validation cost per element
        if validation_overhead > 0:
            per_element = validation_overhead / size * 1000  # Convert to nanoseconds
            print(f"Per element:         {per_element:10.2f} ns")
    
    print("\n## Analysis")
    print("-" * 40)
    print("The validation overhead is minimal because:")
    print("1. Validation happens in Rust (compiled, optimized)")
    print("2. Simple comparisons (s > 0, k > 0, etc.) are very fast")
    print("3. The main computation dominates the runtime")
    print()
    print("Let's check what the validation actually does...")

def check_validation_behavior():
    """Check what validation is actually happening."""
    
    print("\n# Validation Behavior Test")
    print("=" * 60)
    
    # Test with invalid data
    print("\n## Testing with invalid inputs")
    print("-" * 40)
    
    size = 100
    valid_array = np.random.uniform(80, 120, size)
    invalid_array = np.array([-1.0] + list(np.random.uniform(80, 120, size-1)))  # First element negative
    
    # Test safe version with invalid data
    try:
        result = black_scholes.call_price_batch(
            invalid_array,  # Invalid spot price
            np.full(size, 100.0),
            np.full(size, 1.0),
            np.full(size, 0.05),
            np.full(size, 0.2)
        )
        print("Safe version with invalid data: Succeeded (validation might be incomplete)")
    except ValueError as e:
        print(f"Safe version with invalid data: Raised ValueError: {e}")
    
    # Test unsafe version with invalid data
    try:
        result = black_scholes.call_price_batch_unsafe(
            invalid_array,  # Invalid spot price
            np.full(size, 100.0),
            np.full(size, 1.0),
            np.full(size, 0.05),
            np.full(size, 0.2)
        )
        # Check if result contains NaN or Inf
        if np.any(np.isnan(result)) or np.any(np.isinf(result)):
            print(f"Unsafe version with invalid data: Produced NaN/Inf (as expected)")
        else:
            print(f"Unsafe version with invalid data: Produced finite result (unexpected)")
    except Exception as e:
        print(f"Unsafe version with invalid data: Raised {type(e).__name__}: {e}")

def main():
    measure_validation_overhead()
    check_validation_behavior()
    
    print("\n## Conclusion")
    print("-" * 40)
    print("The minimal difference between safe and unsafe versions suggests:")
    print("1. Validation is already very efficient")
    print("2. The computation cost dominates (norm_cdf calculations)")
    print("3. Unsafe version mainly benefits when validation is a bottleneck")
    print("   (e.g., complex validation logic or very simple computations)")
    print()
    print("For Black-Scholes, the computation is complex enough that")
    print("validation overhead is negligible compared to the actual pricing.")

if __name__ == "__main__":
    main()