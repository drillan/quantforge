"""Memory safety and leak detection tests"""

import contextlib
import gc
import sys
import tracemalloc
import weakref

import numpy as np
from quantforge import black76, black_scholes, merton


class TestMemorySafety:
    """Test memory safety and leak prevention"""

    def test_no_memory_leak_small_batches(self):
        """Test for memory leaks with many small batches"""
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        # Run many small batches
        for _ in range(1000):
            arr = np.random.randn(100)
            _ = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)
            del arr

        gc.collect()
        snapshot2 = tracemalloc.take_snapshot()
        stats = snapshot2.compare_to(snapshot1, "lineno")

        # Calculate total memory increase
        total_increase = sum(stat.size_diff for stat in stats if stat.size_diff > 0)

        # Should be less than 1MB increase
        assert total_increase < 1024 * 1024, f"Memory leak detected: {total_increase} bytes"
        tracemalloc.stop()

    def test_no_memory_leak_large_batches(self):
        """Test for memory leaks with large batches"""
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        # Run several large batches
        for _ in range(10):
            arr = np.random.randn(100_000)
            _ = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)
            del arr
            gc.collect()

        gc.collect()
        snapshot2 = tracemalloc.take_snapshot()
        stats = snapshot2.compare_to(snapshot1, "lineno")

        # Calculate total memory increase
        total_increase = sum(stat.size_diff for stat in stats if stat.size_diff > 0)

        # Should be less than 10MB increase for large batches
        assert total_increase < 10 * 1024 * 1024, f"Memory leak detected: {total_increase} bytes"
        tracemalloc.stop()

    def test_reference_counting(self):
        """Test that reference counts are correct"""
        arr = np.array([100.0, 105.0, 110.0])
        initial_refcount = sys.getrefcount(arr)

        # Call bindings function
        _ = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)

        # Reference count should not increase
        final_refcount = sys.getrefcount(arr)
        assert final_refcount == initial_refcount, (
            f"Reference count increased from {initial_refcount} to {final_refcount}"
        )

    def test_array_ownership(self):
        """Test that arrays are not retained after function returns"""
        arr = np.array([100.0, 105.0, 110.0])
        weak_ref = weakref.ref(arr)

        _ = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)

        # Delete the array
        del arr
        gc.collect()

        # Weak reference should be dead
        assert weak_ref() is None, "Array is still referenced after deletion"

    def test_zero_copy_optimization(self):
        """Test that zero-copy optimization is working"""
        size = 1_000_000
        arr = np.random.randn(size)

        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        # This should use zero-copy if possible
        _ = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)

        snapshot2 = tracemalloc.take_snapshot()
        stats = snapshot2.compare_to(snapshot1, "lineno")

        # Memory increase should be less than 2x input size (indicating zero-copy)
        total_increase = sum(stat.size_diff for stat in stats if stat.size_diff > 0)
        input_size = arr.nbytes

        assert total_increase < input_size * 2, (
            f"Expected zero-copy, but allocated {total_increase / input_size:.1f}x input size"
        )
        tracemalloc.stop()

    def test_greeks_batch_memory(self):
        """Test memory usage for Greeks batch calculation"""
        size = 10_000
        arr = np.random.uniform(80, 120, size)

        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        greeks = black_scholes.greeks_batch(arr, 100, 1, 0.05, 0.2, True)

        snapshot2 = tracemalloc.take_snapshot()
        stats = snapshot2.compare_to(snapshot1, "lineno")

        # Should allocate approximately 5 arrays (delta, gamma, vega, theta, rho)
        total_increase = sum(stat.size_diff for stat in stats if stat.size_diff > 0)
        expected_size = size * 8 * 5  # 5 f64 arrays

        # Allow 2x overhead for temporary allocations
        assert total_increase < expected_size * 2, f"Greeks batch allocated too much memory: {total_increase} bytes"

        del greeks
        gc.collect()
        tracemalloc.stop()

    def test_concurrent_memory_safety(self):
        """Test memory safety with concurrent operations"""
        import threading

        def worker():
            for _ in range(100):
                arr = np.random.randn(1000)
                _ = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)

        threads = [threading.Thread(target=worker) for _ in range(4)]

        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        gc.collect()
        snapshot2 = tracemalloc.take_snapshot()
        stats = snapshot2.compare_to(snapshot1, "lineno")

        total_increase = sum(stat.size_diff for stat in stats if stat.size_diff > 0)

        # Should have minimal memory increase after threads complete
        assert total_increase < 5 * 1024 * 1024, f"Memory leak in concurrent execution: {total_increase} bytes"
        tracemalloc.stop()

    def test_exception_memory_cleanup(self):
        """Test that memory is cleaned up on exceptions"""
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        for _ in range(100):
            with contextlib.suppress(Exception):
                # This should raise an error (negative time)
                _ = black_scholes.call_price_batch(np.array([100.0]), 100, -1.0, 0.05, 0.2)

        gc.collect()
        snapshot2 = tracemalloc.take_snapshot()
        stats = snapshot2.compare_to(snapshot1, "lineno")

        total_increase = sum(stat.size_diff for stat in stats if stat.size_diff > 0)

        # Should have no significant memory increase
        assert total_increase < 100_000, f"Memory not cleaned up on exceptions: {total_increase} bytes"
        tracemalloc.stop()

    def test_model_switching_memory(self):
        """Test memory behavior when switching between models"""
        size = 10_000
        arr = np.random.uniform(80, 120, size)

        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        # Use different models
        for _ in range(10):
            _ = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)
            _ = black76.call_price_batch(arr, 100, 1, 0.05, 0.2)
            _ = merton.call_price_batch(arr, 100, 1, 0.05, 0.02, 0.2)

        gc.collect()
        snapshot2 = tracemalloc.take_snapshot()
        stats = snapshot2.compare_to(snapshot1, "lineno")

        total_increase = sum(stat.size_diff for stat in stats if stat.size_diff > 0)

        # Should have minimal memory increase
        assert total_increase < 2 * 1024 * 1024, f"Memory leak when switching models: {total_increase} bytes"
        tracemalloc.stop()
