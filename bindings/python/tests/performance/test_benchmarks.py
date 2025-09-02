"""Performance benchmarks for Python bindings."""

import time
import numpy as np
import pytest
from python.quantforge import models


class TestPerformance:
    """Performance benchmarks."""

    def test_single_calculation_speed(self):
        """Test single calculation performance."""
        n_iterations = 10000

        start = time.perf_counter()
        for _ in range(n_iterations):
            _ = models.black_scholes.call_price(100, 100, 1, 0.05, 0.2)
        elapsed = time.perf_counter() - start

        per_call = elapsed / n_iterations * 1e9  # nanoseconds
        assert per_call < 1000  # Should be < 1 microsecond

    def test_batch_processing_speed(self):
        """Test batch processing performance."""
        sizes = [1000, 10000, 100000]

        for size in sizes:
            spots = np.random.uniform(50, 150, size)

            start = time.perf_counter()
            _ = models.black_scholes.call_price_batch(spots, 100, 1, 0.05, 0.2)
            elapsed = time.perf_counter() - start

            throughput = size / elapsed
            print(f"Size {size}: {throughput:.0f} ops/sec")

            # Performance requirement: > 1M ops/sec for smaller sizes
            if size <= 10000:
                assert throughput > 1_000_000

    def test_gil_release(self):
        """Test that GIL is properly released."""
        import threading
        import queue

        def worker(q, n):
            spots = np.random.uniform(50, 150, n)
            start = time.perf_counter()
            _ = models.black_scholes.call_price_batch(spots, 100, 1, 0.05, 0.2)
            q.put(time.perf_counter() - start)

        # Run in parallel
        q = queue.Queue()
        threads = []
        n = 100000
        n_threads = 4

        start = time.perf_counter()
        for _ in range(n_threads):
            t = threading.Thread(target=worker, args=(q, n))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        total_time = time.perf_counter() - start

        # Should be faster than sequential
        sequential_time = sum(q.get() for _ in range(n_threads))
        speedup = sequential_time / total_time

        assert speedup > 2.0  # At least 2x speedup with 4 threads

    def test_memory_efficiency(self):
        """Test memory efficiency of batch operations."""
        import tracemalloc

        # Start memory tracking
        tracemalloc.start()

        # Large batch operation
        size = 1_000_000
        spots = np.random.uniform(50, 150, size)

        snapshot1 = tracemalloc.take_snapshot()

        # Process batch
        prices = models.black_scholes.call_price_batch(spots, 100, 1, 0.05, 0.2)

        snapshot2 = tracemalloc.take_snapshot()

        # Check memory usage
        top_stats = snapshot2.compare_to(snapshot1, "lineno")
        total_memory = sum(stat.size for stat in top_stats)

        # Should use less than 100MB for 1M elements
        assert total_memory < 100 * 1024 * 1024

        tracemalloc.stop()
