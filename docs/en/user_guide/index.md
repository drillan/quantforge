# User Guide

Learn step-by-step from basic to advanced features of QuantForge.

## Guide Composition

### 📚 Fundamentals

- [Basic Usage](basic_usage.md) - Black-Scholes Model and Greeks Calculation
- [NumPy Integration](numpy_integration.md) - Efficient array processing and zero-copy optimizations

### 🎯 Advanced Applications

- [Advanced Models](advanced_models.md) - American, Asian, and Spread Options
- [Implementation Examples](examples.md) - Practical use cases for real-world applications

## Main Features

### Price Calculation Model

| model | Description | Performance (Actual) |
|--------|------|---------------|
| Black-Scholes | European Option | 1.4 μs/calculation |
| Bjerksund-Stensland | American Option Approximation | Scheduled Measurement |
| Asian Options | Average Price Option | Scheduled Measurement |
| Spread Options | 2 Asset Spread | Scheduled Measurement |

※ Measurement environment: AMD Ryzen 5 5600G, CUI mode.

### Greeks

- **Delta (δ)**: Sensitivity to changes in the underlying asset price
- **Gamma (Γ)**: The rate of change of Delta
- **Vega (ν)**: Sensitivity to changes in volatility
- **Theta (Θ)**: Sensitivity over time
- **Rho (ρ)**: Sensitivity to interest rate changes

## Performance Optimization

QuantForge achieves acceleration through the following technologies:

```{admonition} Optimization Technologies
:class: tip

1. **Parallel Processing**: Efficient parallel computation using Rayon (effective for large datasets)
2. **Arrow-native Design**: Zero-copy FFI for fast data exchange
3. **Memory Efficiency**: Column-oriented storage for efficient processing
4. **Cache Optimization**: Memory access pattern optimization
```

## Usage Examples Overview

### Simple Price Calculation

```python
from quantforge.models import black_scholes

# Single option price
price = black_scholes.call_price(
    s=100.0,   # spot price
    k=110.0,   # strike price
    t=1.0,     # time to maturity
    r=0.05,    # risk-free rate
    sigma=0.2  # volatility
)
```

### Batch Processing

```python
import numpy as np
from quantforge.models import black_scholes

# Batch calculate 1 million options  
# ~56ms on AMD Ryzen 5 5600G (CUI mode)
spots = np.random.uniform(90, 110, 1_000_000)
prices = black_scholes.call_price_batch(
    spots=spots,
    strikes=100.0,
    times=1.0,
    rates=0.05,
    sigmas=0.2
)
```

### Portfolio Evaluation

```python
# Multiple option positions
from quantforge.models import black_scholes

positions = [
    {"is_call": True, "s": 100, "k": 105, "quantity": 100},
    {"is_call": False, "s": 100, "k": 95, "quantity": -50},
]

total_value = 0
for pos in positions:
    if pos["is_call"]:
        price = black_scholes.call_price(
            s=pos["s"], k=pos["k"], t=0.25, r=0.05, sigma=0.2
        )
    else:
        price = black_scholes.put_price(
            s=pos["s"], k=pos["k"], t=0.25, r=0.05, sigma=0.2
        )
    total_value += price * pos["quantity"]
```

## Recommended Workflow

1. **Data Preparation** → Prepare your input data
2. **NumPy Array Conversion** → Convert to NumPy arrays for optimal performance
3. **QuantForge Calculation** → Execute pricing/Greeks calculations
4. **Result Validation** → Verify results against expectations
5. **Visualization/Report** → Generate outputs and visualizations

Additional optimization steps:
- **Batch Size Optimization** → Tune batch sizes for optimal performance
- **Performance Measurement** → Monitor calculation times
- **Tuning** → Adjust parameters based on measurements

## Best Practices

### ✅ Recommended

- Use NumPy arrays
- Appropriate batch size (10,000–100,000)
- Pre-allocate memory
- Standardize type (float64)

### ❌ Deprecated

- Using Python lists
- Loop through each item
- Frequent type conversions
- Giant Single-Batch (> 1,000,000)

## Troubleshooting

For issues and questions, please check the [GitHub Issues](https://github.com/drillan/quantforge/issues).

## Next Step

1. Start with [Basic Usage](basic_usage.md)
2. [Efficiency with NumPy Integration](numpy_integration.md)
3. Train [Advanced Models](advanced_models.md)
4. [Practical Applications](examples.md)
