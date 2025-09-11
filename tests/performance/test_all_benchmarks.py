"""Comprehensive benchmark tests comparing Pure Python, NumPy+SciPy, and QuantForge.

This module provides performance comparisons between three implementations:
1. Pure Python - Using only standard library (math)
2. NumPy+SciPy - Vectorized operations with scipy.stats
3. QuantForge - Rust implementation with PyO3 bindings
"""

import math

import numpy as np
import pytest
import quantforge as qf
from scipy.optimize import brentq
from scipy.stats import norm


def black_scholes_pure_python(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """Pure Python Black-Scholes call option price calculation.

    Uses only standard library math functions.
    """
    sqrt_t = math.sqrt(t)
    d1 = (math.log(s / k) + (r + sigma**2 / 2) * t) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t

    # Standard normal CDF approximation using error function
    def norm_cdf(x: float) -> float:
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

    return s * norm_cdf(d1) - k * math.exp(-r * t) * norm_cdf(d2)


def implied_volatility_pure_python(
    price: float,
    s: float,
    k: float,
    t: float,
    r: float,
    is_call: bool = True,
    initial_guess: float = 0.2,
    max_iterations: int = 100,
    tolerance: float = 1e-6,
) -> float:
    """Pure Python Newton-Raphson method for implied volatility calculation.

    Uses Newton-Raphson iteration to find the volatility that produces
    the given option price.
    """
    # Intrinsic value check
    if is_call:
        intrinsic = max(s - k * math.exp(-r * t), 0)
    else:
        intrinsic = max(k * math.exp(-r * t) - s, 0)

    if price < intrinsic:
        raise ValueError(f"Price {price} is below intrinsic value {intrinsic}")

    # Manaster-Koehler initial guess
    moneyness = math.log(s / k) if s > 0 and k > 0 else 0
    if abs(moneyness) < 0.1:  # Near ATM
        sigma = initial_guess
    else:
        # Adjust initial guess based on moneyness
        sigma = initial_guess * (1 + abs(moneyness))

    # Newton-Raphson iteration
    for iteration in range(max_iterations):
        # Calculate option price and vega
        sqrt_t = math.sqrt(t)
        d1 = (math.log(s / k) + (r + sigma**2 / 2) * t) / (sigma * sqrt_t)
        d2 = d1 - sigma * sqrt_t

        # Standard normal PDF
        def norm_pdf(x: float) -> float:
            return math.exp(-(x**2) / 2) / math.sqrt(2 * math.pi)

        # Standard normal CDF
        def norm_cdf(x: float) -> float:
            return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

        # Calculate theoretical price
        if is_call:
            theo_price = s * norm_cdf(d1) - k * math.exp(-r * t) * norm_cdf(d2)
        else:
            theo_price = k * math.exp(-r * t) * norm_cdf(-d2) - s * norm_cdf(-d1)

        # Calculate vega
        vega = s * norm_pdf(d1) * sqrt_t

        # Check convergence
        price_diff = theo_price - price
        if abs(price_diff) < tolerance:
            return sigma

        # Avoid division by zero
        if abs(vega) < 1e-10:
            # Vega too small, can't continue
            break

        # Newton-Raphson update
        sigma = sigma - price_diff / vega

        # Boundary constraints
        sigma = max(0.001, min(sigma, 5.0))

    # Failed to converge
    raise ValueError(f"Failed to converge after {max_iterations} iterations")


def black_scholes_numpy_scipy(
    s: np.ndarray, k: np.ndarray, t: np.ndarray, r: np.ndarray, sigma: np.ndarray
) -> np.ndarray:
    """NumPy+SciPy Black-Scholes call option price calculation.

    Vectorized implementation using NumPy arrays and scipy.stats.norm.
    """
    sqrt_t = np.sqrt(t)
    d1 = (np.log(s / k) + (r + sigma**2 / 2) * t) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t
    result: np.ndarray = s * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)
    return result


def implied_volatility_numpy_scipy(
    prices: np.ndarray,
    s: np.ndarray,
    k: np.ndarray,
    t: np.ndarray,
    r: np.ndarray,
    is_call: bool = True,
) -> np.ndarray:
    """NumPy+SciPy implied volatility calculation using Brent's method.

    Uses scipy.optimize.brentq for robust root finding.
    """
    # Ensure arrays
    prices = np.atleast_1d(prices)
    s = np.atleast_1d(s)
    k = np.atleast_1d(k)
    t = np.atleast_1d(t)
    r = np.atleast_1d(r)

    # Broadcast to same shape
    prices, s, k, t, r = np.broadcast_arrays(prices, s, k, t, r)

    # Result array
    ivs = np.zeros_like(prices)

    # Process each option
    for i in range(len(prices)):
        price_i = prices.flat[i]
        s_i = s.flat[i]
        k_i = k.flat[i]
        t_i = t.flat[i]
        r_i = r.flat[i]

        # Objective function for root finding
        def objective(sigma: float) -> float:
            sqrt_t = np.sqrt(t_i)
            d1 = (np.log(s_i / k_i) + (r_i + sigma**2 / 2) * t_i) / (sigma * sqrt_t)
            d2 = d1 - sigma * sqrt_t

            if is_call:
                theo_price = s_i * norm.cdf(d1) - k_i * np.exp(-r_i * t_i) * norm.cdf(d2)
            else:
                theo_price = k_i * np.exp(-r_i * t_i) * norm.cdf(-d2) - s_i * norm.cdf(-d1)

            return theo_price - price_i

        try:
            # Use Brent's method for robust root finding
            iv = brentq(objective, 0.001, 5.0, xtol=1e-6, maxiter=100)
            ivs.flat[i] = iv
        except (ValueError, RuntimeError):
            # Failed to converge, set to NaN
            ivs.flat[i] = np.nan

    return ivs.reshape(prices.shape)


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
        result = benchmark(qf.black_scholes.call_price, self.s, self.k, self.t, self.r, self.sigma)
        assert 10.0 < result < 11.0, f"Unexpected result: {result}"

    def test_pure_python_single(self, benchmark):
        """Benchmark Pure Python single calculation."""
        result = benchmark(black_scholes_pure_python, self.s, self.k, self.t, self.r, self.sigma)
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
            np.array(self.sigma),
        )
        assert 10.0 < result < 11.0, f"Unexpected result: {result}"


@pytest.mark.benchmark
class TestBatchCalculation:
    """Benchmark tests for batch option price calculations."""

    def setup_method(self):
        """Setup test parameters for batch calculations."""
        np.random.seed(42)  # For reproducibility
        self.sizes = [100, 1000, 10000]

    def _generate_batch_data(self, size: int) -> tuple[np.ndarray, ...]:
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
            qf.black_scholes.call_price_batch, spots=spots, strikes=strikes, times=times, rates=rates, sigmas=sigmas
        )
        assert len(result) == size
        # Convert Arrow array to numpy for testing
        result_np = result.to_numpy() if hasattr(result, "to_numpy") else result
        assert np.all(result_np > 0), "All option prices should be positive"

    @pytest.mark.parametrize("size", [100, 1000, 10000])
    def test_pure_python_batch(self, benchmark, size):
        """Benchmark Pure Python batch calculation (loop)."""
        spots, strikes, times, rates, sigmas = self._generate_batch_data(size)

        def pure_python_batch():
            results = []
            for i in range(size):
                price = black_scholes_pure_python(spots[i], strikes[i], times[i], rates[i], sigmas[i])
                results.append(price)
            return np.array(results)

        result = benchmark(pure_python_batch)
        assert len(result) == size
        assert np.all(result > 0), "All option prices should be positive"

    @pytest.mark.parametrize("size", [100, 1000, 10000])
    def test_numpy_scipy_batch(self, benchmark, size):
        """Benchmark NumPy+SciPy batch calculation (vectorized)."""
        spots, strikes, times, rates, sigmas = self._generate_batch_data(size)

        result = benchmark(black_scholes_numpy_scipy, spots, strikes, times, rates, sigmas)
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
        assert abs(qf_result - python_result) < 1e-6, f"QuantForge ({qf_result}) vs Pure Python ({python_result})"
        assert abs(qf_result - numpy_result) < 1e-6, f"QuantForge ({qf_result}) vs NumPy+SciPy ({numpy_result})"
        assert abs(python_result - numpy_result) < 1e-6, (
            f"Pure Python ({python_result}) vs NumPy+SciPy ({numpy_result})"
        )

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


@pytest.mark.benchmark
class TestImpliedVolatilityCalculation:
    """Benchmark tests for implied volatility calculations."""

    def setup_method(self):
        """Setup test parameters for IV calculation."""
        self.s = 100.0
        self.k = 100.0
        self.t = 1.0
        self.r = 0.05
        self.true_sigma = 0.2
        # Calculate the option price with true volatility
        self.call_price = qf.black_scholes.call_price(self.s, self.k, self.t, self.r, self.true_sigma)

    def test_quantforge_iv_single(self, benchmark):
        """Benchmark QuantForge single IV calculation."""
        result = benchmark(
            qf.black_scholes.implied_volatility,
            price=self.call_price,
            s=self.s,
            k=self.k,
            t=self.t,
            r=self.r,
            is_call=True,
        )
        assert abs(result - self.true_sigma) < 1e-5, (
            f"IV should be close to true volatility: {result} vs {self.true_sigma}"
        )

    def test_pure_python_iv_single(self, benchmark):
        """Benchmark Pure Python single IV calculation."""
        result = benchmark(
            implied_volatility_pure_python,
            price=self.call_price,
            s=self.s,
            k=self.k,
            t=self.t,
            r=self.r,
            is_call=True,
        )
        assert abs(result - self.true_sigma) < 1e-5, (
            f"IV should be close to true volatility: {result} vs {self.true_sigma}"
        )

    def test_numpy_scipy_iv_single(self, benchmark):
        """Benchmark NumPy+SciPy single IV calculation."""
        result = benchmark(
            implied_volatility_numpy_scipy,
            prices=np.array(self.call_price),
            s=np.array(self.s),
            k=np.array(self.k),
            t=np.array(self.t),
            r=np.array(self.r),
            is_call=True,
        )
        assert abs(result.item() - self.true_sigma) < 1e-5, "IV should be close to true volatility"

    @pytest.mark.parametrize("size", [100, 1000, 10000])
    def test_quantforge_iv_batch(self, benchmark, size):
        """Benchmark QuantForge batch IV calculation."""
        np.random.seed(42)
        # Generate random volatilities
        true_sigmas = np.random.uniform(0.15, 0.35, size)
        spots = np.random.uniform(80, 120, size)
        strikes = np.full(size, 100.0)
        times = np.full(size, 1.0)
        rates = np.full(size, 0.05)

        # Calculate prices with true volatilities
        prices = qf.black_scholes.call_price_batch(
            spots=spots, strikes=strikes, times=times, rates=rates, sigmas=true_sigmas
        )
        # Convert Arrow to NumPy for input
        prices_np = prices.to_numpy() if hasattr(prices, "to_numpy") else prices

        result = benchmark(
            qf.black_scholes.implied_volatility_batch,
            prices=prices_np,
            spots=spots,
            strikes=strikes,
            times=times,
            rates=rates,
            is_calls=True,
        )
        assert len(result) == size, f"Should return {size} IVs"
        # Convert result to numpy if needed
        result_np = result.to_numpy() if hasattr(result, "to_numpy") else result
        # Check average error is small
        avg_error = np.mean(np.abs(result_np - true_sigmas))
        assert avg_error < 1e-4, f"Average IV error should be small: {avg_error}"

    @pytest.mark.parametrize("size", [100, 1000, 10000])
    def test_pure_python_iv_batch(self, benchmark, size):
        """Benchmark Pure Python batch IV calculation (loop)."""
        np.random.seed(42)
        true_sigmas = np.random.uniform(0.15, 0.35, size)
        spots = np.random.uniform(80, 120, size)
        strikes = np.full(size, 100.0)
        times = np.full(size, 1.0)
        rates = np.full(size, 0.05)

        # Calculate prices with true volatilities
        prices = []
        for i in range(size):
            price = black_scholes_pure_python(spots[i], strikes[i], times[i], rates[i], true_sigmas[i])
            prices.append(price)
        prices = np.array(prices)

        def pure_python_iv_batch():
            results = []
            for i in range(size):
                try:
                    iv = implied_volatility_pure_python(
                        prices[i], spots[i], strikes[i], times[i], rates[i], is_call=True
                    )
                    results.append(iv)
                except ValueError:
                    results.append(np.nan)
            return np.array(results)

        result = benchmark(pure_python_iv_batch)
        assert len(result) == size, f"Should return {size} IVs"
        # Check that most converged
        converged = np.sum(~np.isnan(result))
        assert converged > size * 0.95, f"At least 95% should converge: {converged}/{size}"

    @pytest.mark.parametrize("size", [100, 1000, 10000])
    def test_numpy_scipy_iv_batch(self, benchmark, size):
        """Benchmark NumPy+SciPy batch IV calculation."""
        np.random.seed(42)
        true_sigmas = np.random.uniform(0.15, 0.35, size)
        spots = np.random.uniform(80, 120, size)
        strikes = np.full(size, 100.0)
        times = np.full(size, 1.0)
        rates = np.full(size, 0.05)

        # Calculate prices with true volatilities
        prices = black_scholes_numpy_scipy(spots, strikes, times, rates, true_sigmas)

        result = benchmark(
            implied_volatility_numpy_scipy,
            prices=prices,
            s=spots,
            k=strikes,
            t=times,
            r=rates,
            is_call=True,
        )
        assert len(result) == size, f"Should return {size} IVs"
        # Check that most converged
        converged = np.sum(~np.isnan(result))
        assert converged > size * 0.95, f"At least 95% should converge: {converged}/{size}"


@pytest.mark.benchmark
class TestImpliedVolatilityEdgeCases:
    """Benchmark tests for implied volatility edge cases."""

    def setup_method(self):
        """Setup test parameters for edge cases."""
        np.random.seed(42)

    def test_deep_itm_options(self, benchmark):
        """Benchmark Deep ITM options (convergence can be challenging)."""
        size = 100
        # Deep ITM: S >> K
        spots = np.random.uniform(150, 200, size)
        strikes = np.full(size, 100.0)
        times = np.full(size, 1.0)
        rates = np.full(size, 0.05)
        true_sigmas = np.random.uniform(0.15, 0.35, size)

        # Calculate prices
        prices = qf.black_scholes.call_price_batch(
            spots=spots, strikes=strikes, times=times, rates=rates, sigmas=true_sigmas
        )
        prices_np = prices.to_numpy() if hasattr(prices, "to_numpy") else prices

        result = benchmark(
            qf.black_scholes.implied_volatility_batch,
            prices=prices_np,
            spots=spots,
            strikes=strikes,
            times=times,
            rates=rates,
            is_calls=True,
        )
        assert len(result) == size, "Should handle all deep ITM options"

    def test_deep_otm_options(self, benchmark):
        """Benchmark Deep OTM options (small vega, convergence difficult)."""
        size = 100
        # Deep OTM: S << K
        spots = np.random.uniform(50, 70, size)
        strikes = np.full(size, 100.0)
        times = np.full(size, 1.0)
        rates = np.full(size, 0.05)
        true_sigmas = np.random.uniform(0.15, 0.35, size)

        # Calculate prices
        prices = qf.black_scholes.call_price_batch(
            spots=spots, strikes=strikes, times=times, rates=rates, sigmas=true_sigmas
        )
        prices_np = prices.to_numpy() if hasattr(prices, "to_numpy") else prices

        result = benchmark(
            qf.black_scholes.implied_volatility_batch,
            prices=prices_np,
            spots=spots,
            strikes=strikes,
            times=times,
            rates=rates,
            is_calls=True,
        )
        assert len(result) == size, "Should handle all deep OTM options"

    def test_near_expiry_options(self, benchmark):
        """Benchmark near-expiry options (numerically unstable)."""
        size = 100
        spots = np.random.uniform(95, 105, size)
        strikes = np.full(size, 100.0)
        times = np.full(size, 0.01)  # Very short time to expiry
        rates = np.full(size, 0.05)
        true_sigmas = np.random.uniform(0.15, 0.35, size)

        # Calculate prices
        prices = qf.black_scholes.call_price_batch(
            spots=spots, strikes=strikes, times=times, rates=rates, sigmas=true_sigmas
        )
        prices_np = prices.to_numpy() if hasattr(prices, "to_numpy") else prices

        result = benchmark(
            qf.black_scholes.implied_volatility_batch,
            prices=prices_np,
            spots=spots,
            strikes=strikes,
            times=times,
            rates=rates,
            is_calls=True,
        )
        assert len(result) == size, "Should handle near-expiry options"

    def test_iv_smile_surface(self, benchmark):
        """Benchmark IV smile/surface construction (practical scenario)."""
        # Create a grid of strikes and maturities
        strikes = np.linspace(80, 120, 21)  # 21 strikes
        times = np.array([0.25, 0.5, 1.0, 2.0])  # 4 maturities
        spot = 100.0
        rate = 0.05

        # Create grid
        K, T = np.meshgrid(strikes, times)
        K_flat = K.flatten()
        T_flat = T.flatten()
        size = len(K_flat)

        S_flat = np.full(size, spot)
        R_flat = np.full(size, rate)

        # Generate realistic volatility smile
        moneyness = np.log(S_flat / K_flat)
        # Smile effect: higher vol for OTM options
        base_vol = 0.2
        smile_adjustment = 0.1 * moneyness**2
        true_sigmas = base_vol + smile_adjustment

        # Calculate prices
        prices = qf.black_scholes.call_price_batch(
            spots=S_flat, strikes=K_flat, times=T_flat, rates=R_flat, sigmas=true_sigmas
        )
        prices_np = prices.to_numpy() if hasattr(prices, "to_numpy") else prices

        result = benchmark(
            qf.black_scholes.implied_volatility_batch,
            prices=prices_np,
            spots=S_flat,
            strikes=K_flat,
            times=T_flat,
            rates=R_flat,
            is_calls=True,
        )
        assert len(result) == size, f"Should compute full IV surface ({size} points)"
