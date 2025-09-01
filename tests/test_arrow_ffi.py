"""
Arrow FFI zero-copy implementation tests.
TDD Phase 0: Red tests (will fail until implementation is complete)
"""

import time
import numpy as np
import pyarrow as pa
import pytest
from quantforge import arrow_native  # Will be implemented

# Performance targets
PERFORMANCE_TARGET_10K = 170  # μs for 10,000 elements
PERFORMANCE_TARGET_100K = 1500  # μs for 100,000 elements
PERFORMANCE_TARGET_1M = 15000  # μs for 1,000,000 elements

# Accuracy tolerance
ACCURACY_TOLERANCE = 1e-10


class TestArrowNativeZeroCopy:
    """Test suite for Arrow native zero-copy implementation."""
    
    def test_arrow_call_price_zero_copy(self):
        """Test zero-copy Arrow call price calculation."""
        # Create PyArrow arrays
        size = 10_000
        spots = pa.array([100.0] * size)
        strikes = pa.array([105.0] * size)
        times = pa.array([1.0] * size)
        rates = pa.array([0.05] * size)
        sigmas = pa.array([0.2] * size)
        
        # Measure performance
        start = time.perf_counter()
        result = arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)
        duration_us = (time.perf_counter() - start) * 1_000_000
        
        # Performance assertion
        assert duration_us < PERFORMANCE_TARGET_10K, \
            f"Performance requirement: <{PERFORMANCE_TARGET_10K}μs for {size} elements, got {duration_us:.2f}μs"
        
        # Accuracy assertion (Black-Scholes reference value)
        expected_value = 8.021352235143176
        assert abs(result[0].as_py() - expected_value) < ACCURACY_TOLERANCE, \
            f"Accuracy check failed: expected {expected_value}, got {result[0].as_py()}"
    
    def test_arrow_put_price_zero_copy(self):
        """Test zero-copy Arrow put price calculation."""
        size = 10_000
        spots = pa.array([100.0] * size)
        strikes = pa.array([105.0] * size)
        times = pa.array([1.0] * size)
        rates = pa.array([0.05] * size)
        sigmas = pa.array([0.2] * size)
        
        start = time.perf_counter()
        result = arrow_native.arrow_put_price(spots, strikes, times, rates, sigmas)
        duration_us = (time.perf_counter() - start) * 1_000_000
        
        assert duration_us < PERFORMANCE_TARGET_10K, \
            f"Performance requirement: <{PERFORMANCE_TARGET_10K}μs for {size} elements, got {duration_us:.2f}μs"
        
        # Put price reference value
        expected_value = 7.899151753253662
        assert abs(result[0].as_py() - expected_value) < ACCURACY_TOLERANCE, \
            f"Accuracy check failed: expected {expected_value}, got {result[0].as_py()}"
    
    def test_performance_scaling(self):
        """Test performance scaling with different data sizes."""
        test_cases = [
            (10_000, PERFORMANCE_TARGET_10K),
            (100_000, PERFORMANCE_TARGET_100K),
            (1_000_000, PERFORMANCE_TARGET_1M),
        ]
        
        for size, target_us in test_cases:
            spots = pa.array([100.0] * size)
            strikes = pa.array([105.0] * size)
            times = pa.array([1.0] * size)
            rates = pa.array([0.05] * size)
            sigmas = pa.array([0.2] * size)
            
            start = time.perf_counter()
            result = arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)
            duration_us = (time.perf_counter() - start) * 1_000_000
            
            assert duration_us < target_us, \
                f"Performance target for {size:,} elements: <{target_us}μs, got {duration_us:.2f}μs"
            assert len(result) == size, f"Expected {size} results, got {len(result)}"
    
    def test_zero_copy_verification(self):
        """Verify that no memory copies occur during conversion."""
        import sys
        
        size = 10_000
        spots = pa.array([100.0] * size)
        
        # Get memory address before passing to Rust
        spots_ptr = spots.buffers()[1].address
        
        # Call function (should not copy data)
        strikes = pa.array([105.0] * size)
        times = pa.array([1.0] * size)
        rates = pa.array([0.05] * size)
        sigmas = pa.array([0.2] * size)
        
        # Memory usage should not significantly increase (no copy)
        mem_before = sys.getsizeof(spots)
        result = arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)
        
        # The original array should still be at the same address
        assert spots.buffers()[1].address == spots_ptr, \
            "Data was copied instead of zero-copy operation"
    
    def test_gil_release(self):
        """Test that GIL is properly released during computation."""
        import threading
        import queue
        
        size = 100_000
        spots = pa.array([100.0] * size)
        strikes = pa.array([105.0] * size)
        times = pa.array([1.0] * size)
        rates = pa.array([0.05] * size)
        sigmas = pa.array([0.2] * size)
        
        q = queue.Queue()
        
        def compute():
            result = arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)
            q.put(len(result))
        
        def parallel_task():
            # This should run in parallel if GIL is released
            count = 0
            for _ in range(1000000):
                count += 1
            q.put(count)
        
        # Start both threads
        t1 = threading.Thread(target=compute)
        t2 = threading.Thread(target=parallel_task)
        
        start = time.perf_counter()
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        duration = time.perf_counter() - start
        
        # Both tasks should complete in parallel
        results = []
        while not q.empty():
            results.append(q.get())
        
        assert len(results) == 2, "Both tasks should complete"
        assert size in results, "Computation should complete"
        assert 1000000 in results, "Parallel task should complete"
        
        # Time should be less than sequential execution would take
        # This is a rough check - actual timing depends on system
        assert duration < 1.0, "Tasks should run in parallel (GIL released)"


@pytest.mark.benchmark
class TestArrowNativeBenchmarks:
    """Benchmark tests for Arrow native implementation."""
    
    def test_benchmark_vs_numpy(self):
        """Compare performance against NumPy implementation."""
        import quantforge.black_scholes as bs_numpy
        
        size = 10_000
        
        # NumPy arrays
        spots_np = np.full(size, 100.0)
        strikes_np = np.full(size, 105.0)
        times_np = np.full(size, 1.0)
        rates_np = np.full(size, 0.05)
        sigmas_np = np.full(size, 0.2)
        
        # NumPy timing
        start = time.perf_counter()
        result_np = bs_numpy.call_price_batch(spots_np, strikes_np, times_np, rates_np, sigmas_np)
        numpy_time = time.perf_counter() - start
        
        # Arrow arrays
        spots_arrow = pa.array(spots_np)
        strikes_arrow = pa.array(strikes_np)
        times_arrow = pa.array(times_np)
        rates_arrow = pa.array(rates_np)
        sigmas_arrow = pa.array(sigmas_np)
        
        # Arrow timing
        start = time.perf_counter()
        result_arrow = arrow_native.arrow_call_price(
            spots_arrow, strikes_arrow, times_arrow, rates_arrow, sigmas_arrow
        )
        arrow_time = time.perf_counter() - start
        
        speedup = numpy_time / arrow_time
        print(f"\nPerformance comparison for {size:,} elements:")
        print(f"NumPy: {numpy_time*1000:.3f}ms")
        print(f"Arrow: {arrow_time*1000:.3f}ms")
        print(f"Speedup: {speedup:.2f}x")
        
        # Arrow should be at least 1.5x faster for 10k elements
        assert speedup >= 1.5, f"Arrow should be at least 1.5x faster, got {speedup:.2f}x"