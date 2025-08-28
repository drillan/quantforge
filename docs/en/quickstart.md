# Quick Start

Start calculating option prices in just 5 minutes using QuantForge.

## Installation

```bash
# Install latest development version from TestPyPI (currently available)
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ quantforge

# Install stable version from PyPI (after stable release)
pip install quantforge

# Or install development version from source
git clone https://github.com/drillan/quantforge.git
cd quantforge
pip install maturin
maturin develop --release
```

## First Calculation

### Module-Based API

```python
from quantforge.models import black_scholes

# Calculate call option price using Black-Scholes model
price = black_scholes.call_price(
    s=100.0,      # Spot price
    k=110.0,      # Strike price
    t=1.0,        # Time to maturity (years)
    r=0.05,       # Risk-free rate
    sigma=0.2     # Volatility
)

print(f"Call Option Price: ${price:.2f}")
```

### The Greeks' Calculations

```python
# Detailed calculation including Greeks
greeks = black_scholes.greeks(
    s=100.0,
    k=100.0,
    t=1.0,
    r=0.05,
    sigma=0.2,
    is_call=True
)

print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
print(f"Theta: {greeks.theta:.4f}")
print(f"Rho: {greeks.rho:.4f}")
```

## Batch Processing

QuantForge's true value lies in its ability to process massive datasets at high speed:

```python
import numpy as np
import time
from quantforge.models import black_scholes

# 1 million option data points
n = 1_000_000
spots = np.random.uniform(90, 110, n)

# High-speed batch processing
start = time.perf_counter()
prices = black_scholes.call_price_batch(
    spots=spots,
    k=100.0,
    t=1.0,
    r=0.05,
    sigma=0.2
)
elapsed = (time.perf_counter() - start) * 1000

print(f"Calculation time: {elapsed:.1f}ms")
print(f"Per option: {elapsed/n*1000:.1f}ns")
```

## implied volatility

Deriving volatility from market prices:

```python
# Calculate IV from market price
market_price = 10.45
iv = black_scholes.implied_volatility(
    price=market_price,
    s=100.0,
    k=100.0,
    t=1.0,
    r=0.05,
    is_call=True
)
print(f"Implied Volatility: {iv:.1%}")
```


## Real-Time Risk Management

```python
from quantforge.models import black_scholes

# Calculate portfolio delta
positions = [
    {"spot": 100, "strike": 95, "contracts": 10},
    {"spot": 100, "strike": 105, "contracts": -5},
]

total_delta = 0
for pos in positions:
    greeks = black_scholes.greeks(
        s=pos["spot"], k=pos["strike"], t=1.0, r=0.05, sigma=0.2, is_call=True
    )
    total_delta += pos["contracts"] * greeks.delta * 100

print(f"Portfolio Delta: {total_delta:.2f} shares")
```

## Performance

QuantForge benchmark results (AMD Ryzen 5 5600G, CUI mode):

| Operation | Processing Time |
|------|----------|
| Single Price Calculation | 1.4 μs |
| all Greeks | Scheduled Measurement |
| IV Calculation | 1.5 μs |
| 1 million batch | 55.6 ms |

For detailed measurement results, see the performance section.

## Next Step

- [Basic Usage](user_guide/basic_usage.md) - Detailed API documentation
- [NumPy Integration](user_guide/numpy_integration.md) - Large-scale data processing
- API Reference - Complete API documentation (coming soon)
