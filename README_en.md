# QuantForge

[![PyPI Version](https://img.shields.io/pypi/v/quantforge)](https://pypi.org/project/quantforge/)
[![Python Support](https://img.shields.io/pypi/pyversions/quantforge)](https://pypi.org/project/quantforge/)
[![License](https://img.shields.io/pypi/l/quantforge)](https://github.com/drillan/quantforge/blob/main/LICENSE)
[![Tests](https://img.shields.io/badge/coverage-78%25-green)](https://github.com/drillan/quantforge)

High-performance option pricing library powered by Rust + PyO3, delivering 500-1000x speedup over pure Python implementations.

## Features

- **Blazing Fast**: Rust-powered computation with Python interface
- **Comprehensive Models**: Black-Scholes, Black76, Merton, and American options
- **Full Greeks Support**: Delta, Gamma, Vega, Theta, Rho, and Psi (dividend sensitivity)
- **Batch Processing**: Vectorized operations for large-scale calculations
- **Zero-Copy Design**: Direct NumPy array processing without data copying
- **Type Safe**: Full type hints and runtime validation

## Installation

```bash
pip install quantforge
```

### Requirements

- Python 3.12+
- NumPy 1.20+
- x86_64 architecture (ARM support coming soon)

## Quick Start

### Basic Option Pricing

```python
import quantforge as qf

# Black-Scholes European option
call_price = qf.black_scholes.call_price(
    s=100.0,    # Spot price
    k=100.0,    # Strike price
    t=1.0,      # Time to maturity (years)
    r=0.05,     # Risk-free rate
    sigma=0.2   # Volatility
)
print(f"Call price: ${call_price:.2f}")

# Put option
put_price = qf.black_scholes.put_price(
    s=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2
)
print(f"Put price: ${put_price:.2f}")
```

### Greeks Calculation

```python
# Calculate all Greeks at once
greeks = qf.black_scholes.greeks(
    s=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2, is_call=True
)

print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
print(f"Theta: {greeks.theta:.4f}")
print(f"Rho: {greeks.rho:.4f}")
```

### Batch Processing

```python
import numpy as np

# Process multiple options simultaneously
spots = np.array([90.0, 95.0, 100.0, 105.0, 110.0])
strikes = np.full(5, 100.0)
times = np.full(5, 1.0)
rates = np.full(5, 0.05)
sigmas = np.full(5, 0.2)

prices = qf.black_scholes.call_price_batch(
    spots, strikes, times, rates, sigmas
)
print(f"Batch prices: {prices}")
```

### Implied Volatility

```python
# Calculate implied volatility from market price
market_price = 10.45
iv = qf.black_scholes.implied_volatility(
    price=market_price,
    s=100.0, k=100.0, t=1.0, r=0.05,
    is_call=True
)
print(f"Implied volatility: {iv:.2%}")
```

## Available Models

### Black-Scholes Model
Standard European option pricing model for stocks.

```python
from quantforge import black_scholes

# Pricing
call = black_scholes.call_price(s, k, t, r, sigma)
put = black_scholes.put_price(s, k, t, r, sigma)

# Greeks
greeks = black_scholes.greeks(s, k, t, r, sigma, is_call=True)

# Implied volatility
iv = black_scholes.implied_volatility(price, s, k, t, r, is_call=True)
```

### Black76 Model
Futures option pricing model.

```python
from quantforge import black76

# Using forward price instead of spot
call = black76.call_price(f, k, t, r, sigma)
put = black76.put_price(f, k, t, r, sigma)
```

### Merton Model
European options with dividend yield.

```python
from quantforge import merton

# With dividend yield q
call = merton.call_price(s, k, t, r, q, sigma)
put = merton.put_price(s, k, t, r, q, sigma)

# Greeks including Psi (dividend sensitivity)
greeks = merton.greeks(s, k, t, r, q, sigma, is_call=True)
print(f"Psi: {greeks.psi:.4f}")
```

### American Options
Early exercise options using optimized numerical methods.

```python
from quantforge import american

# American options can be exercised early
call = american.call_price(s, k, t, r, q, sigma)
put = american.put_price(s, k, t, r, q, sigma)

# Early exercise premium
euro_put = merton.put_price(s, k, t, r, q, sigma)
amer_put = american.put_price(s, k, t, r, q, sigma)
premium = amer_put - euro_put
print(f"Early exercise premium: ${premium:.2f}")
```

## Performance

QuantForge achieves exceptional performance through:

- **Rust Core**: Zero-cost abstractions and SIMD optimizations
- **Parallel Processing**: Automatic parallelization for batch operations
- **Memory Efficiency**: Zero-copy NumPy array integration
- **Cache Optimization**: Data layout optimized for CPU cache

### Benchmark Results

| Operation | Pure Python | QuantForge | Speedup |
|-----------|------------|------------|---------|
| Single Price | 10 ms | 10 μs | 1000x |
| Greeks (all) | 50 ms | 50 μs | 1000x |
| Batch (10k) | 100 s | 100 ms | 1000x |
| Implied Vol | 100 ms | 200 μs | 500x |

## API Reference

### Common Parameters

- `s` / `spot`: Current price of the underlying asset
- `k` / `strike`: Strike price of the option
- `t` / `time`: Time to expiration in years
- `r` / `rate`: Risk-free interest rate
- `q` / `dividend`: Dividend yield (for dividend-paying assets)
- `sigma` / `volatility`: Volatility of the underlying asset
- `f` / `forward`: Forward price (for Black76 model)
- `is_call`: Boolean flag for call (True) or put (False) option

### Error Handling

QuantForge provides comprehensive input validation:

```python
from quantforge.errors import ValidationError

try:
    price = qf.black_scholes.call_price(
        s=-100.0,  # Invalid: negative spot
        k=100.0, t=1.0, r=0.05, sigma=0.2
    )
except ValidationError as e:
    print(f"Validation error: {e}")
```

## Advanced Usage

### Custom Batch Processing

```python
import numpy as np
from quantforge import black_scholes

# Monte Carlo simulation setup
n_simulations = 100000
spots = np.random.lognormal(np.log(100), 0.2, n_simulations)
strikes = np.full(n_simulations, 100.0)
times = np.full(n_simulations, 1.0)
rates = np.full(n_simulations, 0.05)
sigmas = np.random.uniform(0.1, 0.4, n_simulations)

# Ultra-fast batch pricing
prices = black_scholes.call_price_batch(
    spots, strikes, times, rates, sigmas
)

print(f"Average price: ${prices.mean():.2f}")
print(f"Price std dev: ${prices.std():.2f}")
```

### Greeks Hedging

```python
# Delta-neutral portfolio construction
position_size = 100  # options
delta = qf.black_scholes.greeks(
    s=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2, is_call=True
).delta

hedge_shares = -position_size * delta
print(f"Hedge with {hedge_shares:.0f} shares")
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/drillan/quantforge.git
cd quantforge

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run benchmarks
cargo bench
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Citation

If you use QuantForge in your research, please cite:

```bibtex
@software{quantforge2025,
  title = {QuantForge: High-Performance Option Pricing Library},
  author = {driller},
  year = {2025},
  url = {https://github.com/drillan/quantforge}
}
```

## Support

- **Issues**: [GitHub Issues](https://github.com/drillan/quantforge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/drillan/quantforge/discussions)
- **Email**: quantforge@example.com

## Roadmap

- [ ] GPU acceleration support
- [ ] Exotic options (Asian, Barrier, Lookback)
- [ ] Stochastic volatility models (Heston, SABR)
- [ ] Interest rate derivatives
- [ ] ARM architecture support
- [ ] WebAssembly bindings

---

Built with ❤️ using Rust and Python