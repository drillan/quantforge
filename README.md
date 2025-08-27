# QuantForge

<div align="center">

[日本語](./README-ja.md) | **English**

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Rust](https://img.shields.io/badge/rust-1.88%2B-orange)](https://www.rust-lang.org/)

**Ultra-High Performance Option Pricing Library — 500-1000x Faster than Pure Python**

[Features](#-features) • [Benchmarks](#-benchmarks) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Documentation](#-documentation)

</div>

---

## 🚀 Performance First

QuantForge delivers institutional-grade option pricing with unprecedented speed:

| Operation | Performance | Notes |
|-----------|-------------|-------|
| Black-Scholes Single | **< 10ns** | Call/Put pricing |
| Complete Greeks | **< 50ns** | Delta, Gamma, Vega, Theta, Rho |
| Implied Volatility | **< 200ns** | Newton-Raphson solver |
| 1M Batch Processing | **< 20ms** | Auto-parallelization via Rayon |

<details>
<summary><b>Benchmark Results (1M options)</b></summary>

| Implementation | Time | Relative Speed |
|----------------|------|----------------|
| Pure Python | 10,000ms | 1x |
| NumPy | 100ms | 100x |
| **QuantForge (Sequential)** | **20ms** | **500x** |
| **QuantForge (Parallel)** | **9.7ms** | **1,000x** |

</details>

## ✨ Features

### Option Pricing Models

QuantForge supports multiple option pricing models, each optimized for specific asset classes:

- **Black-Scholes**: European options on stocks
- **American Options**: Early exercise options with Bjerksund-Stensland (2002) approximation
- **Merton**: Options on dividend-paying assets
- **Black76**: Commodity and futures options
- **Asian Options** *(coming soon)*: Path-dependent options
- **Spread Options** *(coming soon)*: Multi-asset options
- **Garman-Kohlhagen** *(coming soon)*: FX options

### Core Capabilities
- **Complete Greeks**: Delta, Gamma, Vega, Theta, Rho with analytical precision
- **Model-Specific Greeks**: Dividend Rho (Merton), Early Exercise Boundaries (American)
- **Implied Volatility**: Hybrid Newton-Raphson/Brent solver with Brenner-Subrahmanyam initialization
- **Batch Processing**: Zero-copy NumPy integration with automatic parallelization (>30k elements)

### Technical Excellence
- 🦀 **Pure Rust Core**: Memory-safe, zero-overhead abstractions
- 🎯 **Machine Precision**: Error-function based implementation (<1e-15 accuracy)
- ⚡ **Optimized Implementation**: High-performance mathematical functions (measured on Intel i9-12900K)
- 🔧 **Production Ready**: Comprehensive input validation and edge case handling

## 📦 Installation

### From Source (Development)

```bash
# Clone repository
git clone https://github.com/drillan/quantforge.git
cd quantforge

# Install Rust (if needed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Build and install
pip install maturin
maturin develop --release
```

### Development Dependencies

```bash
# Using uv (recommended)
uv sync --group dev

# Or standard pip
pip install -e ".[dev]"
```

## 💻 Quick Start

### Black-Scholes Model (European Options)

```python
import numpy as np
from quantforge.models import black_scholes

# Single option pricing
spot = 100.0      # Underlying price
strike = 105.0    # Strike price  
time = 0.25       # Time to maturity (years)
rate = 0.05       # Risk-free rate
sigma = 0.2       # Volatility (industry standard σ)

# Black-Scholes model for stock options
call_price = black_scholes.call_price(spot, strike, time, rate, sigma)
put_price = black_scholes.put_price(spot, strike, time, rate, sigma)

print(f"Call: ${call_price:.4f}, Put: ${put_price:.4f}")
```

### American Options (Early Exercise)

```python
from quantforge.models import american

# American option with dividends
spot = 100.0      # Current stock price
strike = 100.0    # Strike price
time = 1.0        # Time to maturity (years)
rate = 0.05       # Risk-free rate
q = 0.03          # Dividend yield
sigma = 0.2       # Volatility

# American call price (Bjerksund-Stensland 2002)
call_price = american.call_price(spot, strike, time, rate, q, sigma)
put_price = american.put_price(spot, strike, time, rate, q, sigma)

# Early exercise boundary
boundary = american.exercise_boundary(spot, strike, time, rate, q, sigma, is_call=True)
print(f"Early exercise boundary: ${boundary:.2f}")
```

### Merton Model (Dividend-Paying Assets)

```python
from quantforge.models import merton

# Options on dividend-paying stocks
spot = 100.0      # Current stock price
strike = 105.0    # Strike price
time = 1.0        # Time to maturity
rate = 0.05       # Risk-free rate
q = 0.03          # Continuous dividend yield
sigma = 0.2       # Volatility

# Merton model pricing
call_price = merton.call_price(spot, strike, time, rate, q, sigma)
put_price = merton.put_price(spot, strike, time, rate, q, sigma)

# Greeks including dividend sensitivity
greeks = merton.greeks(spot, strike, time, rate, q, sigma, is_call=True)
print(f"Dividend Rho: {greeks.dividend_rho:.4f}")  # Merton-specific Greek
```

### Black76 Model (Futures & Commodities)

```python
from quantforge.models import black76

# Commodity futures options
forward = 75.50   # Forward/futures price
strike = 70.00    # Strike price
time = 0.25       # Time to maturity
rate = 0.05       # Risk-free rate
sigma = 0.3       # Volatility

# Black76 pricing for futures
call_price = black76.call_price(forward, strike, time, rate, sigma)
put_price = black76.put_price(forward, strike, time, rate, sigma)

print(f"Futures Call: ${call_price:.4f}, Put: ${put_price:.4f}")
```

### Batch Processing

```python
# Process 100,000 options in milliseconds
spots = np.linspace(80, 120, 100000)

from quantforge.models import black_scholes
call_prices = black_scholes.call_price_batch(spots, strike, time, rate, sigma)

# Automatic parallelization for large arrays (>30k elements)
print(f"Processed {len(call_prices):,} options")
```

### Greeks Calculation

```python
# Module-based API
from quantforge.models import black_scholes

# All Greeks at once
greeks = black_scholes.greeks(spot, strike, time, rate, sigma, is_call=True)
print(greeks)  # Greeks(delta=0.377, gamma=0.038, vega=0.189, theta=-0.026, rho=0.088)

# Access individual Greeks
print(f"Delta: {greeks.delta:.3f}")
print(f"Gamma: {greeks.gamma:.3f}")
```

### Implied Volatility

```python
from quantforge.models import black_scholes

# Solve for IV from market price
market_price = 3.5
iv = black_scholes.implied_volatility(
    market_price, spot, strike, time, rate, is_call=True
)
print(f"Implied Volatility: {iv:.2%}")

# Note: Batch IV calculation coming in future release
# Will support vectorized implied volatility solving
```

## 🔬 Implementation Details

### Mathematical Foundation
- **Normal CDF**: Error function (erf) based implementation for machine precision
- **Greeks**: Analytical formulas with special handling for edge cases (ATM, near-expiry)
- **IV Solver**: Hybrid approach combining Newton-Raphson (fast convergence) with Brent's method (guaranteed convergence)

### Architecture
- **Zero-Copy Design**: Direct NumPy array access via PyO3
- **Dynamic Parallelization**: Automatic thread pool sizing based on workload
- **Memory Efficiency**: Stack allocation for small batches, minimal heap pressure

### Validation
- **250+ Golden Master Tests**: Validated against reference implementations
- **Property-Based Testing**: Hypothesis framework for edge case discovery
- **Put-Call Parity**: Automatic validation in test suite
- **Boundary Conditions**: Special handling for extreme values
- **Model Cross-Validation**: Consistency checks between related models (BS-Merton, American-European)

## 📊 Detailed Benchmarks

### Single Option Pricing (ns per calculation)
```
Black-Scholes Call:     8.5ns  ████████▌
Black-Scholes Put:      9.2ns  █████████▏
Delta Calculation:     12.3ns  ████████████▎
Complete Greeks:       48.7ns  ████████████████████████████████████████████████▋
Implied Volatility:   187.4ns  ████████████████████████████████████████████████████████████████████
```

### Batch Processing Scalability
```
Elements    Sequential    Parallel    Speedup
1,000         0.12ms         -           -
10,000        1.2ms          -           -
30,000        3.6ms       2.1ms        1.7x
100,000       12ms        3.8ms        3.2x
1,000,000     120ms       9.7ms       12.4x
```

## 🛠️ Development

### Building
```bash
# Debug build
cargo build

# Release build (optimized)
cargo build --release

# Run tests
cargo test --release
pytest
```

### Code Quality
```bash
# Rust linting
cargo clippy -- -D warnings

# Python formatting
uv run ruff format .

# Python linting
uv run ruff check .

# Type checking
uv run mypy .
```

### Performance Testing
```bash
# Run benchmarks
cargo bench
pytest tests/performance/ --benchmark-only

# Generate performance report
pytest tests/performance/ --benchmark-json=benchmark.json
```

## 📚 Documentation

Comprehensive documentation available via Sphinx:

```bash
# Build documentation
uv run sphinx-build -M html docs docs/_build

# View in browser
open docs/_build/html/index.html
```

Documentation includes:
- Complete API reference
- Mathematical foundations
- Performance optimization guide
- Architecture deep-dive

## 🗺️ Roadmap

### Completed ✅
- [x] Black-Scholes Model (European options)
- [x] American Options (Bjerksund-Stensland 2002 approximation)
- [x] Merton Model (Dividend-paying assets)
- [x] Black76 Model (Futures and commodities)
- [x] Complete Greeks suite (including model-specific Greeks)
- [x] Implied Volatility solver
- [x] Batch processing with auto-parallelization
- [x] Zero-copy NumPy integration
- [x] Early exercise boundary calculation

### In Progress 🚧
- [ ] Asian options (geometric and arithmetic averaging)
- [ ] Spread options (Kirk's approximation)
- [ ] Barrier options (up/down, in/out)
- [ ] Lookback options

### Planned 📋
- [ ] Garman-Kohlhagen (FX options)
- [ ] Stochastic volatility models (Heston, SABR)
- [ ] Monte Carlo framework with variance reduction
- [ ] Finite difference methods (American options refinement)
- [ ] GPU acceleration (CUDA/Metal)
- [ ] Real-time market data integration
- [ ] Calibration framework

## 🤝 Contributing

We welcome contributions!

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards
- Follow Rust idioms and `clippy` recommendations
- Maintain test coverage above 90%
- Document public APIs
- Benchmark performance-critical changes

## 📈 Use Cases

QuantForge is designed for:
- **High-Frequency Trading**: Sub-microsecond pricing for market making
- **Risk Management**: Real-time portfolio Greeks calculation
- **Backtesting**: Process millions of scenarios efficiently
- **Research**: Rapid prototyping with Python, production performance with Rust

## 🔐 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with these excellent tools:
- [PyO3](https://github.com/PyO3/pyo3) - Rust bindings for Python
- [Rayon](https://github.com/rayon-rs/rayon) - Data parallelism for Rust
- [maturin](https://github.com/PyO3/maturin) - Build and publish Rust Python extensions

## 📞 Contact

- **Issues**: [GitHub Issues](https://github.com/drillan/quantforge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/drillan/quantforge/discussions)
- **Security**: Please report security vulnerabilities privately

---

<div align="center">

**Built with Rust for Speed, Wrapped in Python for Simplicity**

⭐ Star us on GitHub — it helps the project grow!

*Performance metrics measured on Intel Core i9-12900K, 32GB DDR5, Ubuntu 22.04 (2025-01-27)*

</div>