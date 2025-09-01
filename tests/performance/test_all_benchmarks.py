"""Comprehensive benchmark tests comparing Pure Python, NumPy+SciPy, and QuantForge.

This module provides performance comparisons between three implementations:
1. Pure Python - Using only standard library (math)
2. NumPy+SciPy - Vectorized operations with scipy.stats
3. QuantForge - Rust implementation with PyO3 bindings
"""

import math
from typing import Tuple

import numpy as np
import pytest
from scipy.stats import norm

import quantforge as qf


def black_scholes_pure_python(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """Pure Python Black-Scholes call option price calculation.
    
    Uses only standard library math functions.
    """
    sqrt_t = math.sqrt(t)
    d1 = (math.log(s/k) + (r + sigma**2/2) * t) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t
    
    # Standard normal CDF approximation using error function
    def norm_cdf(x: float) -> float:
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0
    
    return s * norm_cdf(d1) - k * math.exp(-r * t) * norm_cdf(d2)


def black_scholes_numpy_scipy(
    s: np.ndarray, 
    k: np.ndarray, 
    t: np.ndarray, 
    r: np.ndarray, 
    sigma: np.ndarray
) -> np.ndarray:
    """NumPy+SciPy Black-Scholes call option price calculation.
    
    Vectorized implementation using NumPy arrays and scipy.stats.norm.
    """
    sqrt_t = np.sqrt(t)
    d1 = (np.log(s/k) + (r + sigma**2/2) * t) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t
    return s * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)


@pytest.mark.benchmark
class TestSingleCalculation:
    """Benchmark tests for single option price calculations."""
    
    def setup_method(self):
        """Setup test parameters."""
        self.s = 100.0
        self.k = 100.0
        self.t = 1.0
        self.r = 0.05
        self.sigma = 0.2
        
    def test_quantforge_single(self, benchmark):
        """Benchmark QuantForge single calculation."""
        result = benchmark(
            qf.black_scholes.call_price,
            self.s, self.k, self.t, self.r, self.sigma
        )
        assert 10.0 < result < 11.0, f"Unexpected result: {result}"
        
    def test_pure_python_single(self, benchmark):
        """Benchmark Pure Python single calculation."""
        result = benchmark(
            black_scholes_pure_python,
            self.s, self.k, self.t, self.r, self.sigma
        )
        assert 10.0 < result < 11.0, f"Unexpected result: {result}"
        
    def test_numpy_scipy_single(self, benchmark):
        """Benchmark NumPy+SciPy single calculation."""
        # For single calculation, we use scalar arrays
        result = benchmark(
            black_scholes_numpy_scipy,
            np.array(self.s), 
            np.array(self.k), 
            np.array(self.t), 
            np.array(self.r), 
            np.array(self.sigma)
        )
        assert 10.0 < result < 11.0, f"Unexpected result: {result}"


@pytest.mark.benchmark
class TestBatchCalculation:
    """Benchmark tests for batch option price calculations."""
    
    def setup_method(self):
        """Setup test parameters for batch calculations."""
        np.random.seed(42)  # For reproducibility
        self.sizes = [100, 1000, 10000]
        
    def _generate_batch_data(self, size: int) -> Tuple[np.ndarray, ...]:
        """Generate batch test data."""
        spots = np.random.uniform(80, 120, size)
        strikes = np.full(size, 100.0)
        times = np.full(size, 1.0)
        rates = np.full(size, 0.05)
        sigmas = np.random.uniform(0.15, 0.35, size)
        return spots, strikes, times, rates, sigmas
        
    @pytest.mark.parametrize("size", [100, 1000, 10000])
    def test_quantforge_batch(self, benchmark, size):
        """Benchmark QuantForge batch calculation."""
        spots, strikes, times, rates, sigmas = self._generate_batch_data(size)
        
        result = benchmark(
            qf.black_scholes.call_price_batch,
            spots=spots,
            strikes=strikes,
            times=times,
            rates=rates,
            sigmas=sigmas
        )
        assert len(result) == size
        assert np.all(result > 0), "All option prices should be positive"
        
    @pytest.mark.parametrize("size", [100, 1000, 10000])
    def test_pure_python_batch(self, benchmark, size):
        """Benchmark Pure Python batch calculation (loop)."""
        spots, strikes, times, rates, sigmas = self._generate_batch_data(size)
        
        def pure_python_batch():
            results = []
            for i in range(size):
                price = black_scholes_pure_python(
                    spots[i], strikes[i], times[i], rates[i], sigmas[i]
                )
                results.append(price)
            return np.array(results)
        
        result = benchmark(pure_python_batch)
        assert len(result) == size
        assert np.all(result > 0), "All option prices should be positive"
        
    @pytest.mark.parametrize("size", [100, 1000, 10000])
    def test_numpy_scipy_batch(self, benchmark, size):
        """Benchmark NumPy+SciPy batch calculation (vectorized)."""
        spots, strikes, times, rates, sigmas = self._generate_batch_data(size)
        
        result = benchmark(
            black_scholes_numpy_scipy,
            spots, strikes, times, rates, sigmas
        )
        assert len(result) == size
        assert np.all(result > 0), "All option prices should be positive"


@pytest.mark.benchmark
class TestModelComparison:
    """Direct comparison tests between different models."""
    
    def test_all_models_accuracy(self):
        """Verify all three implementations produce similar results."""
        s, k, t, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.2
        
        # Calculate with each implementation
        qf_result = qf.black_scholes.call_price(s, k, t, r, sigma)
        python_result = black_scholes_pure_python(s, k, t, r, sigma)
        numpy_result = black_scholes_numpy_scipy(
            np.array(s), np.array(k), np.array(t), np.array(r), np.array(sigma)
        ).item()
        
        # Check they are all close (within 1e-6)
        assert abs(qf_result - python_result) < 1e-6, \
            f"QuantForge ({qf_result}) vs Pure Python ({python_result})"
        assert abs(qf_result - numpy_result) < 1e-6, \
            f"QuantForge ({qf_result}) vs NumPy+SciPy ({numpy_result})"
        assert abs(python_result - numpy_result) < 1e-6, \
            f"Pure Python ({python_result}) vs NumPy+SciPy ({numpy_result})"
    
    @pytest.mark.parametrize("model", ["black_scholes", "black76", "merton", "american"])
    def test_quantforge_models(self, benchmark, model):
        """Benchmark different QuantForge models."""
        s, k, t, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.2
        
        if model == "black_scholes":
            result = benchmark(qf.black_scholes.call_price, s, k, t, r, sigma)
        elif model == "black76":
            # Black76 uses forward price instead of spot
            f = s * math.exp(r * t)  # Forward price
            result = benchmark(qf.black76.call_price, f, k, t, r, sigma)
        elif model == "merton":
            # Merton model includes dividend yield
            q = 0.02  # dividend yield
            result = benchmark(qf.merton.call_price, s, k, t, r, q, sigma)
        elif model == "american":
            # American option pricing (includes dividend yield)
            q = 0.02  # dividend yield
            result = benchmark(qf.american.call_price, s, k, t, r, q, sigma)
        
        assert result > 0, f"Option price should be positive for {model}"