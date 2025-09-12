# QuantForge

<div align="center">

[日本語](./README-ja.md) | **English**

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Rust](https://img.shields.io/badge/rust-1.88%2B-orange)](https://www.rust-lang.org/)

**Rust-Powered Option Pricing Library — Up to <!-- BENCHMARK:MAX_SPEEDUP_NUMPY -->1<!-- /BENCHMARK:MAX_SPEEDUP_NUMPY -->x Faster than NumPy+SciPy**

[Features](#-main-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Benchmarks](#-benchmarks) • [Documentation](#-documentation)

</div>

---

## 📖 Overview

QuantForge is a high-performance option pricing library implemented in Rust with Python bindings via PyO3. It provides Black-Scholes based pricing, Greeks calculation, and implied volatility computation with Rust's performance while maintaining Python's ease of use.

## 📋 Features and Implementation

#### Option Pricing Models

QuantForge supports multiple option pricing models optimized for various asset classes:

- **Black-Scholes**: European options on stocks
- **American Options**: Early exercise options with Bjerksund-Stensland (2002) approximation
- **Merton**: Options on dividend-paying assets
- **Black76**: Commodity and futures options
- **Asian Options** *(coming soon)*: Path-dependent options
- **Spread Options** *(coming soon)*: Multi-asset options
- **Garman-Kohlhagen** *(coming soon)*: FX options

#### Core Features

- ⚡ **High Performance**: Up to <!-- BENCHMARK:MAX_SPEEDUP_NUMPY -->1<!-- /BENCHMARK:MAX_SPEEDUP_NUMPY -->x faster than NumPy+SciPy, <!-- BENCHMARK:MAX_SPEEDUP_PYTHON -->1<!-- /BENCHMARK:MAX_SPEEDUP_PYTHON -->x faster than Pure Python
- 🎯 **Machine Precision**: erf-based implementation achieving <1e-15 accuracy
- 📊 **Complete Greeks**: Delta, Gamma, Vega, Theta, Rho plus model-specific Greeks (Dividend Rho, Early Exercise Boundary)
- 🔥 **Implied Volatility**: Newton-Raphson solver up to <!-- BENCHMARK:IV:MAX_SPEEDUP -->170<!-- /BENCHMARK:IV:MAX_SPEEDUP -->x faster than Pure Python
- 🚀 **Auto-Parallelization**: Automatic Rayon parallelization for batches >30,000 elements
- 📦 **Zero-Copy Design**: Direct NumPy array access eliminating memory copy overhead
- ✅ **Robustness**: 250+ golden master tests with comprehensive coverage
- 🔧 **Production Ready**: Input validation, edge case handling, Put-Call parity verified

## 📊 Performance Benchmark Results

<!-- BENCHMARK:SUMMARY:START -->
Environment: Linux - 6 cores - 29.3GB RAM - Python 3.12.5 - 2025-09-12 12:47:56
<!-- BENCHMARK:SUMMARY:END -->

### Latest Benchmark Results
<!-- BENCHMARK:TABLE:START -->
*Benchmark data not found*
<!-- BENCHMARK:TABLE:END -->

*Performance varies by environment. Values shown are medians of 5 runs. See [benchmarks](docs/en/performance/benchmarks.md) for details.*

### 🔥 Implied Volatility Performance

Fair comparison using Newton-Raphson method (same algorithm and parameters):

<!-- BENCHMARK:IV:TABLE:START -->
| Data Size | QuantForge | NumPy Newton | Pure Python | Max Speedup |
|-----------|------------|--------------|-------------|-------------|
| Single | 3.94 μs | 180.86 μs | 3.18 μs | 45x |
| 100 | 34.40 μs | 937.50 μs | 1.03 ms | 30x |
| 1,000 | 184.11 μs | 1.33 ms | 10.45 ms | 56x |
| 10,000 | 599.53 μs | 4.28 ms | 102.07 ms | **170x** |
<!-- BENCHMARK:IV:TABLE:END -->

Maximum speedup: <!-- BENCHMARK:IV:MAX_SPEEDUP -->170<!-- /BENCHMARK:IV:MAX_SPEEDUP -->x vs Pure Python, <!-- BENCHMARK:IV:MAX_SPEEDUP_NUMPY -->45<!-- /BENCHMARK:IV:MAX_SPEEDUP_NUMPY -->x vs NumPy

## 📥 Installation


### From TestPyPI (Latest Development Version)

```bash
# Install the latest development version from TestPyPI
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ quantforge
```

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

## 🚀 Quick Start

### Basic Usage

```python
import numpy as np
from quantforge.models import black_scholes

# Single option calculation
spot = 100.0   # Current price
strike = 110.0 # Strike price
time = 1.0     # Time to maturity (years)
rate = 0.05    # Risk-free rate
sigma = 0.2    # Volatility

# Call option price
call_price = black_scholes.call_price(spot, strike, time, rate, sigma)
print(f"Call Price: ${call_price:.4f}")

# Put option price
put_price = black_scholes.put_price(spot, strike, time, rate, sigma)
print(f"Put Price: ${put_price:.4f}")

# All Greeks calculation
greeks = black_scholes.greeks(spot, strike, time, rate, sigma, is_call=True)
print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
print(f"Theta: {greeks.theta:.4f}")
print(f"Rho: {greeks.rho:.4f}")
```

### Batch Processing (High Performance)

```python
import numpy as np
from quantforge.models import black_scholes

# Generate 1 million random data points
n = 1_000_000
spots = np.random.uniform(80, 120, n)      # Uniform distribution 80-120
strikes = np.full(n, 100.0)                # Fixed strike
times = np.random.uniform(0.1, 2.0, n)     # 0.1-2 years
rates = np.full(n, 0.05)                   # Fixed rate
sigmas = np.random.uniform(0.1, 0.4, n)    # 10-40% volatility

# Batch processing (~56ms for 1M elements)
prices = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)

# Batch Greeks calculation
greeks = black_scholes.greeks_batch(spots, strikes, times, rates, sigmas, 
                                    is_call=np.full(n, True))
```

### Implied Volatility Calculation

```python
from quantforge.models import black_scholes

# Calculate implied volatility from market price
market_price = 12.50
iv = black_scholes.implied_volatility(
    price=market_price,
    s=100.0,  # Current price
    k=110.0,  # Strike price
    t=1.0,    # Time to maturity
    r=0.05,   # Risk-free rate
    is_call=True
)
print(f"Implied Volatility: {iv:.2%}")
```

## 🔄 Parallelization Optimization

QuantForge automatically balances computation and overhead by applying parallelization based on data size:

| Data Size | Processing Mode | Notes |
|-----------|----------------|-------|
| < 1,000 | Single-threaded | Avoid overhead |
| 1,000 - 30,000 | Multi-threaded (small) | 2-4 threads |
| > 30,000 | Fully parallel | All available cores |

```python
import numpy as np
from quantforge.models import black_scholes

# Large data: Automatic parallelization (all cores)
large_spots = np.random.uniform(90, 110, 1_000_000)
large_prices = black_scholes.call_price_batch(large_spots, 100, 1.0, 0.05, 0.2)

# Small data: Single-threaded (avoid overhead)
small_spots = np.array([100, 105, 110])
small_prices = black_scholes.call_price_batch(small_spots, 100, 1.0, 0.05, 0.2)
```

## 📊 Benchmarks

### Practical Scenario: Volatility Surface Construction (10×10 Grid)
| Implementation | Time | vs QuantForge |
|---------------|------|---------------|
| **QuantForge** (parallel) | 0.1 ms | - |
| **NumPy+SciPy** (vectorized) | 0.4 ms | 4x slower |
| **Pure Python** (for loop) | 5.5 ms | 55x slower |

### Practical Scenario: 10,000 Option Portfolio Risk Calculation
| Implementation | Time | vs QuantForge |
|---------------|------|---------------|
| **QuantForge** (parallel) | 1.9 ms | - |
| **NumPy+SciPy** (vectorized) | 2.7 ms | 1.4x slower |
| **Pure Python** (for loop, estimated) | ~70 ms | 37x slower |

See [performance benchmarks](docs/en/performance/benchmarks.md) for detailed results.

## 🏗️ Architecture

```
quantforge/
├── src/                    # Rust core implementation
│   ├── models/            # Pricing models (Black-Scholes, Black76, Merton, etc.)
│   ├── math/              # Mathematical functions (erf, norm_cdf, etc.)
│   ├── validation.rs      # Input validation
│   └── traits.rs          # Batch processing traits
│
├── python/                 # Python bindings
│   └── quantforge/        # Python package
│       └── models/        # Model-specific modules
│
└── tests/                  # Test suite
    ├── unit/              # Unit tests
    ├── integration/       # Integration tests
    ├── golden_master/     # Golden master tests
    └── performance/       # Benchmark tests
```

### Technology Stack
- **Rust 1.88+**: Core computation engine
- **PyO3**: Python-Rust bindings
- **Rayon**: Data parallel processing
- **NumPy**: Array interface
- **maturin**: Build and packaging

## 📚 Documentation

- [Official Documentation (English)](https://drillan.github.io/quantforge/en/)
- [API Reference](https://drillan.github.io/quantforge/en/api/)
- [Performance Guide](docs/en/performance/optimization.md)
- [Developer Guide](docs/en/development/architecture.md)
- [Detailed Benchmarks](docs/en/performance/benchmarks.md)

## 🧪 Testing

```bash
# Run Python tests (450+ test cases)
pytest tests/

# Run Rust tests
cargo test --release

# Measure coverage
pytest tests/ --cov=quantforge --cov-report=html

# Run benchmarks
pytest tests/performance/ -m benchmark
```

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- QuantLib for implementation and validation data
- Rayon project for high-speed parallel processing
- PyO3 project for Python-Rust bindings

## 📮 Contact

For questions or suggestions, please [open an issue](https://github.com/drillan/quantforge/issues) or join our [discussions](https://github.com/drillan/quantforge/discussions).

---

<div align="center">
Made with ❤️ by the QuantForge team
</div>