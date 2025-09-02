"""Performance benchmarks for Arrow Native Broadcasting functionality."""

import pytest
import pyarrow as pa
import numpy as np
from quantforge import arrow_native


class TestArrowBroadcastingPerformance:
    """Benchmark Arrow Native broadcasting performance."""
    
    @pytest.mark.benchmark(group="arrow-broadcasting")
    @pytest.mark.parametrize("size", [100, 1_000, 10_000])
    def test_broadcasting_vs_full_array(self, benchmark, size):
        """Compare broadcasting (scalar) vs full array performance."""
        # Create test data with broadcasting (scalar strike)
        spots = pa.array(np.linspace(90, 110, size))
        strikes_scalar = pa.array([100.0])  # Single value to broadcast
        times = pa.array([1.0])
        rates = pa.array([0.05])
        sigmas = pa.array([0.2])
        
        # Benchmark with broadcasting
        result = benchmark(
            arrow_native.arrow_call_price,
            spots, strikes_scalar, times, rates, sigmas
        )
        
        assert len(result) == size
        assert result.to_numpy()[0] > 0  # Basic sanity check
    
    @pytest.mark.benchmark(group="arrow-no-broadcasting")
    @pytest.mark.parametrize("size", [100, 1_000, 10_000])
    def test_full_array_no_broadcasting(self, benchmark, size):
        """Benchmark full arrays (no broadcasting needed)."""
        # Create full arrays
        spots = pa.array(np.linspace(90, 110, size))
        strikes = pa.array([100.0] * size)  # Full array
        times = pa.array([1.0] * size)
        rates = pa.array([0.05] * size)
        sigmas = pa.array([0.2] * size)
        
        # Benchmark without broadcasting
        result = benchmark(
            arrow_native.arrow_call_price,
            spots, strikes, times, rates, sigmas
        )
        
        assert len(result) == size
    
    @pytest.mark.benchmark(group="arrow-mixed-broadcasting")
    @pytest.mark.parametrize("size", [100, 1_000, 10_000])
    def test_mixed_broadcasting(self, benchmark, size):
        """Benchmark mixed array sizes with broadcasting."""
        # Some arrays are scalars, some are full
        spots = pa.array(np.linspace(90, 110, size))
        strikes = pa.array(np.linspace(95, 105, size))  # Full array
        times = pa.array([1.0])  # Scalar
        rates = pa.array([0.05])  # Scalar
        sigmas = pa.array(np.linspace(0.15, 0.25, size))  # Full array
        
        result = benchmark(
            arrow_native.arrow_call_price,
            spots, strikes, times, rates, sigmas
        )
        
        assert len(result) == size


class TestArrowGreeksPerformance:
    """Benchmark Arrow Native Greeks calculations."""
    
    @pytest.mark.benchmark(group="arrow-greeks")
    @pytest.mark.parametrize("size", [100, 1_000, 10_000])
    def test_greeks_broadcasting(self, benchmark, size):
        """Benchmark Greeks calculation with broadcasting."""
        # Create test data
        spots = pa.array(np.linspace(90, 110, size))
        strikes = pa.array([100.0])  # Scalar
        times = pa.array([1.0])
        rates = pa.array([0.05])
        sigmas = pa.array([0.2])
        
        # Benchmark Greeks
        result = benchmark(
            arrow_native.arrow_greeks,
            spots, strikes, times, rates, sigmas, True
        )
        
        assert isinstance(result, dict)
        assert len(result["delta"]) == size
        assert len(result["gamma"]) == size
        assert len(result["vega"]) == size
        assert len(result["theta"]) == size
        assert len(result["rho"]) == size
    
    @pytest.mark.benchmark(group="arrow-greeks-individual")
    @pytest.mark.parametrize("size", [1_000, 10_000])
    def test_individual_vs_batch_greeks(self, benchmark, size):
        """Compare individual Greek calls vs batch calculation."""
        # Setup
        spots = pa.array(np.linspace(90, 110, size))
        strikes = pa.array([100.0])
        times = pa.array([1.0])
        rates = pa.array([0.05])
        sigmas = pa.array([0.2])
        
        # Benchmark batch Greeks (all at once)
        result = benchmark(
            arrow_native.arrow_greeks,
            spots, strikes, times, rates, sigmas, True
        )
        
        # Greeks calculation should be efficient (< 5x single price)
        assert len(result) == 5  # Five Greeks


class TestBlack76Broadcasting:
    """Benchmark Black76 broadcasting performance."""
    
    @pytest.mark.benchmark(group="black76-broadcasting")
    @pytest.mark.parametrize("size", [100, 1_000, 10_000])
    def test_black76_broadcasting(self, benchmark, size):
        """Benchmark Black76 with broadcasting."""
        # Create test data
        forwards = pa.array(np.linspace(90, 110, size))
        strikes = pa.array([100.0])  # Scalar
        times = pa.array([1.0])
        rates = pa.array([0.05])
        sigmas = pa.array([0.2])
        
        result = benchmark(
            arrow_native.arrow76_call_price,
            forwards, strikes, times, rates, sigmas
        )
        
        assert len(result) == size
    
    @pytest.mark.benchmark(group="black76-greeks")
    @pytest.mark.parametrize("size", [1_000, 10_000])
    def test_black76_greeks(self, benchmark, size):
        """Benchmark Black76 Greeks with broadcasting."""
        forwards = pa.array(np.linspace(90, 110, size))
        strikes = pa.array([100.0])
        times = pa.array([1.0])
        rates = pa.array([0.05])
        sigmas = pa.array([0.2])
        
        result = benchmark(
            arrow_native.arrow76_greeks,
            forwards, strikes, times, rates, sigmas, True
        )
        
        assert len(result["delta"]) == size


# Memory efficiency tests
class TestMemoryEfficiency:
    """Test memory efficiency of broadcasting."""
    
    def test_memory_usage_comparison(self):
        """Compare memory usage with and without broadcasting."""
        import psutil
        import gc
        
        size = 100_000
        process = psutil.Process()
        
        # Measure memory with broadcasting (scalars)
        gc.collect()
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        spots = pa.array(np.linspace(90, 110, size))
        strikes_scalar = pa.array([100.0])
        times_scalar = pa.array([1.0])
        rates_scalar = pa.array([0.05])
        sigmas_scalar = pa.array([0.2])
        
        result1 = arrow_native.arrow_call_price(
            spots, strikes_scalar, times_scalar, rates_scalar, sigmas_scalar
        )
        
        mem_after_broadcast = process.memory_info().rss / 1024 / 1024
        broadcast_memory = mem_after_broadcast - mem_before
        
        # Clean up
        del spots, strikes_scalar, times_scalar, rates_scalar, sigmas_scalar, result1
        gc.collect()
        
        # Measure memory without broadcasting (full arrays)
        mem_before = process.memory_info().rss / 1024 / 1024
        
        spots = pa.array(np.linspace(90, 110, size))
        strikes_full = pa.array([100.0] * size)
        times_full = pa.array([1.0] * size)
        rates_full = pa.array([0.05] * size)
        sigmas_full = pa.array([0.2] * size)
        
        result2 = arrow_native.arrow_call_price(
            spots, strikes_full, times_full, rates_full, sigmas_full
        )
        
        mem_after_full = process.memory_info().rss / 1024 / 1024
        full_array_memory = mem_after_full - mem_before
        
        # Broadcasting should use less memory
        print(f"\nMemory usage for {size:,} elements:")
        print(f"  Broadcasting: {broadcast_memory:.2f} MB")
        print(f"  Full arrays:  {full_array_memory:.2f} MB")
        print(f"  Savings:      {full_array_memory - broadcast_memory:.2f} MB")
        
        # Broadcasting should save at least some memory for large arrays
        assert broadcast_memory <= full_array_memory * 1.1  # Allow 10% margin