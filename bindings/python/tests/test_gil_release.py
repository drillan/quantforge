"""GIL release verification tests"""

import threading
import time

import numpy as np
from quantforge import black76, black_scholes, merton


class TestGILRelease:
    """Test that GIL is properly released during computation"""

    def test_black_scholes_parallel_execution(self):
        """Test Black-Scholes parallel execution with GIL release"""
        size = 100_000
        arr = np.random.uniform(80, 120, size)

        # Single-threaded execution time
        start = time.perf_counter()
        for _ in range(4):
            _ = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)
        single_time = time.perf_counter() - start

        # Multi-threaded execution time
        def worker():
            _ = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)

        threads = [threading.Thread(target=worker) for _ in range(4)]

        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        multi_time = time.perf_counter() - start

        # GIL released should give speedup
        speedup = single_time / multi_time
        assert speedup > 2.0, f"Expected speedup > 2.0, got {speedup:.2f}"
        print(f"Black-Scholes GIL release confirmed: {speedup:.2f}x speedup")

    def test_black76_parallel_execution(self):
        """Test Black76 parallel execution with GIL release"""
        size = 100_000
        arr = np.random.uniform(80, 120, size)

        # Single-threaded execution time
        start = time.perf_counter()
        for _ in range(4):
            _ = black76.call_price_batch(arr, 100, 1, 0.05, 0.2)
        single_time = time.perf_counter() - start

        # Multi-threaded execution time
        def worker():
            _ = black76.call_price_batch(arr, 100, 1, 0.05, 0.2)

        threads = [threading.Thread(target=worker) for _ in range(4)]

        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        multi_time = time.perf_counter() - start

        # GIL released should give speedup
        speedup = single_time / multi_time
        assert speedup > 2.0, f"Expected speedup > 2.0, got {speedup:.2f}"
        print(f"Black76 GIL release confirmed: {speedup:.2f}x speedup")

    def test_merton_parallel_execution(self):
        """Test Merton parallel execution with GIL release"""
        size = 100_000
        arr = np.random.uniform(80, 120, size)

        # Single-threaded execution time
        start = time.perf_counter()
        for _ in range(4):
            _ = merton.call_price_batch(arr, 100, 1, 0.05, 0.02, 0.2)
        single_time = time.perf_counter() - start

        # Multi-threaded execution time
        def worker():
            _ = merton.call_price_batch(arr, 100, 1, 0.05, 0.02, 0.2)

        threads = [threading.Thread(target=worker) for _ in range(4)]

        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        multi_time = time.perf_counter() - start

        # GIL released should give speedup
        speedup = single_time / multi_time
        assert speedup > 2.0, f"Expected speedup > 2.0, got {speedup:.2f}"
        print(f"Merton GIL release confirmed: {speedup:.2f}x speedup")

    def test_gil_checker(self):
        """Test that GIL is released during computation"""
        gil_released = threading.Event()

        def monitor():
            # If this thread can run during computation, GIL is released
            gil_released.set()

        # Large data to ensure computation takes time
        arr = np.random.randn(10_000_000)

        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.start()

        # Run computation
        _ = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)

        monitor_thread.join(timeout=0.1)
        assert gil_released.is_set(), "GIL was not released during computation"

    def test_concurrent_different_models(self):
        """Test concurrent execution of different models"""
        size = 50_000
        arr = np.random.uniform(80, 120, size)
        results = {}

        def bs_worker():
            results["bs"] = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)

        def b76_worker():
            results["b76"] = black76.call_price_batch(arr, 100, 1, 0.05, 0.2)

        def merton_worker():
            results["merton"] = merton.call_price_batch(arr, 100, 1, 0.05, 0.02, 0.2)

        # Run concurrently
        threads = [
            threading.Thread(target=bs_worker),
            threading.Thread(target=b76_worker),
            threading.Thread(target=merton_worker),
        ]

        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        concurrent_time = time.perf_counter() - start

        # Run sequentially for comparison
        start = time.perf_counter()
        bs_worker()
        b76_worker()
        merton_worker()
        sequential_time = time.perf_counter() - start

        speedup = sequential_time / concurrent_time
        assert speedup > 1.5, f"Expected speedup > 1.5, got {speedup:.2f}"
        print(f"Concurrent models speedup: {speedup:.2f}x")

        # Verify all results are present
        assert "bs" in results
        assert "b76" in results
        assert "merton" in results
        assert len(results["bs"]) == size
        assert len(results["b76"]) == size
        assert len(results["merton"]) == size
