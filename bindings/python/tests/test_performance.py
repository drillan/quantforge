"""Performance benchmarks for bindings layer"""

import time

import numpy as np
import pytest
from quantforge import black76, black_scholes, merton
from scipy.stats import norm


def numpy_black_scholes(s, k, t, r, sigma):
    """NumPy reference implementation of Black-Scholes"""
    d1 = (np.log(s / k) + (r + 0.5 * sigma**2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)
    return s * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)


class TestPerformance:
    """Performance benchmarks"""

    @pytest.fixture
    def benchmark_data(self):
        """Standard benchmark data sets"""
        return {
            "small": np.random.uniform(80, 120, 100),
            "medium": np.random.uniform(80, 120, 10_000),
            "large": np.random.uniform(80, 120, 1_000_000),
        }

    def test_single_call_performance(self):
        """Test single call performance"""
        # Warm up
        for _ in range(100):
            _ = black_scholes.call_price(100, 100, 1, 0.05, 0.2)

        # Measure
        start = time.perf_counter()
        for _ in range(10000):
            _ = black_scholes.call_price(100, 100, 1, 0.05, 0.2)
        elapsed = time.perf_counter() - start

        ns_per_call = elapsed * 1e9 / 10000
        print(f"Single call: {ns_per_call:.1f} ns")

        # Target: < 100ns
        assert ns_per_call < 1000, f"Single call too slow: {ns_per_call:.1f} ns"

    def test_batch_performance_scaling(self, benchmark_data):
        """Test batch processing scaling"""
        results = {}

        for size_name, data in benchmark_data.items():
            # Warm up
            _ = black_scholes.call_price_batch(data, 100, 1, 0.05, 0.2)

            # Measure
            start = time.perf_counter()
            for _ in range(10):
                _ = black_scholes.call_price_batch(data, 100, 1, 0.05, 0.2)
            elapsed = (time.perf_counter() - start) / 10

            throughput = len(data) / elapsed
            results[size_name] = {
                "size": len(data),
                "time": elapsed,
                "throughput": throughput,
                "ns_per_calc": elapsed * 1e9 / len(data),
            }
            print(f"{size_name:6s}: {throughput / 1e6:.2f}M ops/sec, {results[size_name]['ns_per_calc']:.1f} ns/calc")

        # Verify linear scaling
        assert results["large"]["ns_per_calc"] < results["small"]["ns_per_calc"] * 2, "Poor scaling for large batches"

        # Verify throughput
        assert results["large"]["throughput"] > 10_000_000, (
            f"Throughput too low: {results['large']['throughput'] / 1e6:.2f}M ops/sec"
        )

    def test_gil_release_performance(self, benchmark_data):
        """Test performance improvement from GIL release"""
        import concurrent.futures

        data = benchmark_data["medium"]

        def compute():
            return black_scholes.call_price_batch(data, 100, 1, 0.05, 0.2)

        # Single-threaded baseline
        start = time.perf_counter()
        for _ in range(4):
            compute()
        single_time = time.perf_counter() - start

        # Multi-threaded with GIL release
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            start = time.perf_counter()
            futures = [executor.submit(compute) for _ in range(4)]
            _ = [f.result() for f in futures]
            multi_time = time.perf_counter() - start

        speedup = single_time / multi_time
        print(f"Parallel speedup: {speedup:.2f}x")

        # Should get at least 2x speedup with 4 threads
        assert speedup > 2.0, f"Insufficient parallel speedup: {speedup:.2f}x"

    def test_numpy_comparison(self, benchmark_data):
        """Compare performance with NumPy implementation"""

        for size_name, spots in benchmark_data.items():
            # NumPy version
            start = time.perf_counter()
            np_prices = numpy_black_scholes(spots, 100, 1, 0.05, 0.2)
            np_time = time.perf_counter() - start

            # QuantForge version
            start = time.perf_counter()
            qf_prices = black_scholes.call_price_batch(spots, 100, 1, 0.05, 0.2)
            qf_time = time.perf_counter() - start

            speedup = np_time / qf_time
            print(f"{size_name:6s}: QuantForge is {speedup:.2f}x faster than NumPy")

            # Verify accuracy
            np.testing.assert_allclose(np_prices, qf_prices, rtol=1e-10)

            # Performance targets
            if len(spots) >= 10000:
                assert speedup > 1.0, f"Should be faster than NumPy for {size_name}"

    def test_greeks_performance(self, benchmark_data):
        """Test Greeks calculation performance"""
        data = benchmark_data["medium"]

        # Warm up
        _ = black_scholes.greeks_batch(data, 100, 1, 0.05, 0.2, True)

        # Measure
        start = time.perf_counter()
        for _ in range(10):
            greeks = black_scholes.greeks_batch(data, 100, 1, 0.05, 0.2, True)
        elapsed = (time.perf_counter() - start) / 10

        ns_per_calc = elapsed * 1e9 / len(data)
        print(f"Greeks batch: {ns_per_calc:.1f} ns per calculation")

        # Should be less than 5x single price calculation
        assert ns_per_calc < 500, f"Greeks calculation too slow: {ns_per_calc:.1f} ns"

        # Verify output structure
        assert "delta" in greeks
        assert "gamma" in greeks
        assert "vega" in greeks
        assert "theta" in greeks
        assert "rho" in greeks
        assert len(greeks["delta"]) == len(data)

    def test_implied_volatility_performance(self):
        """Test implied volatility calculation performance"""
        size = 10_000
        spots = np.random.uniform(80, 120, size)

        # Calculate prices first
        prices = black_scholes.call_price_batch(spots, 100, 1, 0.05, 0.2)

        # Measure IV calculation
        start = time.perf_counter()
        ivs = black_scholes.implied_volatility_batch(prices, spots, 100, 1, 0.05, True)
        elapsed = time.perf_counter() - start

        ns_per_calc = elapsed * 1e9 / size
        print(f"Implied volatility: {ns_per_calc:.1f} ns per calculation")

        # Should be less than 1000ns per calculation
        assert ns_per_calc < 1000, f"IV calculation too slow: {ns_per_calc:.1f} ns"

        # Verify accuracy (should recover original volatility)
        np.testing.assert_allclose(ivs, 0.2, rtol=1e-6)

    def test_model_comparison(self):
        """Compare performance across different models"""
        size = 100_000
        spots = np.random.uniform(80, 120, size)

        models = {
            "black_scholes": lambda: black_scholes.call_price_batch(spots, 100, 1, 0.05, 0.2),
            "black76": lambda: black76.call_price_batch(spots, 100, 1, 0.05, 0.2),
            "merton": lambda: merton.call_price_batch(spots, 100, 1, 0.05, 0.02, 0.2),
        }

        results = {}
        for name, func in models.items():
            # Warm up
            _ = func()

            # Measure
            start = time.perf_counter()
            for _ in range(10):
                _ = func()
            elapsed = (time.perf_counter() - start) / 10

            throughput = size / elapsed
            results[name] = throughput / 1e6
            print(f"{name:15s}: {results[name]:.2f}M ops/sec")

        # All models should have similar performance
        min_throughput = min(results.values())
        max_throughput = max(results.values())
        assert max_throughput / min_throughput < 1.5, "Performance varies too much between models"

    def test_input_type_overhead(self):
        """Test overhead of different input types"""
        size = 10_000

        # Different input types
        inputs = {
            "numpy_array": np.random.uniform(80, 120, size),
            "python_list": list(np.random.uniform(80, 120, size)),
            "scalar": 100.0,
        }

        results = {}
        for input_type, data in inputs.items():
            start = time.perf_counter()
            for _ in range(100):
                _ = black_scholes.call_price_batch(data, 100, 1, 0.05, 0.2)
            elapsed = (time.perf_counter() - start) / 100

            if input_type == "scalar":
                results[input_type] = elapsed * 1e9  # ns
                print(f"{input_type:12s}: {results[input_type]:.1f} ns")
            else:
                results[input_type] = elapsed * 1e9 / size  # ns per element
                print(f"{input_type:12s}: {results[input_type]:.1f} ns/element")

        # List should have minimal overhead vs numpy
        if "python_list" in results and "numpy_array" in results:
            overhead = results["python_list"] / results["numpy_array"]
            assert overhead < 1.5, f"List overhead too high: {overhead:.2f}x"
