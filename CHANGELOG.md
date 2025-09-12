# Changelog

All notable changes to QuantForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-30

### Added
- First stable release on PyPI
- Production-ready wheel distribution via GitHub Actions
- Comprehensive test coverage (620+ tests)
- Full type hints support with mypy strict compliance

### Changed
- Version bump to 0.1.0 for stable release
- Development Status updated from Alpha to Beta
- Installation moved from TestPyPI to PyPI
- CI/CD workflow simplified for PyPI-only deployment

### Removed
- TestPyPI distribution support (migrated to PyPI)
- Dynamic environment selection in GitHub Actions (use static 'pypi')

## [0.0.14] - 2025-09-08

### Initial Stable Release

This is the first production-ready release of QuantForge, a high-performance option pricing library powered by Rust and PyO3.

### Core Features

#### Pricing Models
- **Black-Scholes**: European option pricing with full Greeks support
- **Black76**: Futures option pricing model
- **Merton**: Dividend-adjusted option pricing
- **American Options**: Early exercise options with Binomial Tree and BAW approximation methods

#### Performance
- **500-1000x faster** than pure Python implementations
- **15M+ operations/second** for single calculations
- **Parallel processing** with Rayon for batch operations
- **Zero-copy FFI** via Apache Arrow integration
- **Memory efficient** with direct Arrow array construction

#### Technical Architecture
- **Rust core** with PyO3 bindings for maximum performance
- **Python 3.12+ support** via abi3 stable ABI (supports 3.12, 3.13, and future versions)
- **Apache Arrow native** for efficient data interchange
- **NumPy compatible** via transparent conversion layer
- **Broadcasting support** for flexible batch operations

#### API Surface
- Single calculation functions: `call_price`, `put_price`
- Batch processing: `call_price_batch`, `put_price_batch`
- Greeks calculations: `greeks`, `greeks_batch`
- Implied volatility: Newton-Raphson method with arbitrage bounds
- Complete input validation with detailed error messages

### Quality Assurance
- **576 tests** with comprehensive coverage
- **Golden master validation** against industry references
- **Performance benchmarks** with baseline management
- **CI/CD pipeline** with multi-platform testing
- **Type safety** with complete PyO3 type stubs

### Platform Support
- Linux (x86_64, aarch64)
- macOS (x86_64, ARM64)
- Windows (x64)
- Single wheel supports all Python 3.12+ versions

### Installation

```bash
pip install quantforge
```

### Example Usage

```python
from quantforge import black_scholes

# Single option pricing
price = black_scholes.call_price(
    s=100.0,    # Spot price
    k=105.0,    # Strike price
    t=1.0,      # Time to maturity
    r=0.05,     # Risk-free rate
    sigma=0.2   # Volatility
)

# Batch processing with NumPy arrays
import numpy as np
spots = np.array([100.0, 105.0, 110.0])
prices = black_scholes.call_price_batch(
    spots=spots,
    strikes=105.0,
    times=1.0,
    rates=0.05,
    sigmas=0.2
)
```

### Project Links
- Homepage: https://github.com/drillan/quantforge
- Documentation: https://github.com/drillan/quantforge/tree/main/docs
- Issues: https://github.com/drillan/quantforge/issues

[0.1.0]: https://github.com/drillan/quantforge/releases/tag/v0.1.0
[0.0.14]: https://github.com/drillan/quantforge/releases/tag/v0.0.14