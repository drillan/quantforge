# Greeks API Reference

## Overview

Greeks are financial risk measures that describe how option prices change with respect to various factors. QuantForge provides unified, high-performance Greeks calculations across all option pricing models.

## Return Format Specification

All Greeks functions in QuantForge follow a unified return format for consistency and ease of use:

### Single Option Greeks

For single option calculations, Greeks are returned as a `dict` with the following structure:

```python
{
    'delta': float,    # Rate of change in option price with respect to spot price
    'gamma': float,    # Rate of change in delta with respect to spot price
    'theta': float,    # Rate of change in option price with respect to time
    'vega': float,     # Rate of change in option price with respect to volatility
    'rho': float       # Rate of change in option price with respect to interest rate
}
```

### Batch Greeks Calculations

For batch calculations, Greeks are returned as a `Dict[str, np.ndarray]` where each Greek is a NumPy array:

```python
{
    'delta': np.ndarray,    # Array of delta values
    'gamma': np.ndarray,    # Array of gamma values
    'theta': np.ndarray,    # Array of theta values
    'vega': np.ndarray,     # Array of vega values
    'rho': np.ndarray       # Array of rho values
}
```

This format is consistent across all models:
- Black-Scholes (`quantforge.black_scholes_greeks_batch`)
- Black76 (`quantforge.black76_greeks_batch`)
- Merton Jump Diffusion (`quantforge.merton_greeks_batch`)
- American Options (`quantforge.american_greeks_batch`)

## Memory Efficiency

The batch format uses NumPy arrays for optimal memory efficiency:

```python
# Structure of Arrays (SoA) - Memory efficient
greeks_dict = {
    'delta': np.array([0.5, 0.6, 0.7]),    # Contiguous memory
    'gamma': np.array([0.02, 0.03, 0.04]),
    # ... other Greeks
}

# This is more efficient than Array of Structures (AoS):
# greeks_list = [
#     {'delta': 0.5, 'gamma': 0.02, ...},  # Scattered memory
#     {'delta': 0.6, 'gamma': 0.03, ...},
#     {'delta': 0.7, 'gamma': 0.04, ...},
# ]
```

## Usage Examples

### Single Option Greeks

```python
import quantforge as qf

# Black-Scholes model
greeks = qf.black_scholes_greeks(
    s=100.0,      # Spot price
    k=110.0,      # Strike price
    t=0.25,       # Time to maturity
    r=0.05,       # Risk-free rate
    sigma=0.2,    # Volatility
    is_call=True  # Call option
)

print(f"Delta: {greeks['delta']:.4f}")
print(f"Gamma: {greeks['gamma']:.4f}")
print(f"Theta: {greeks['theta']:.4f}")
print(f"Vega: {greeks['vega']:.4f}")
print(f"Rho: {greeks['rho']:.4f}")
```

### Batch Greeks Calculations

```python
import numpy as np
import quantforge as qf

# Prepare batch inputs
n = 1000
spots = np.random.uniform(90, 110, n)
strikes = np.full(n, 100.0)
times = np.random.uniform(0.1, 2.0, n)
rates = np.full(n, 0.05)
volatilities = np.random.uniform(0.15, 0.35, n)
is_calls = np.ones(n, dtype=bool)

# Calculate Greeks for all options at once
greeks_batch = qf.black_scholes_greeks_batch(
    s=spots,
    k=strikes,
    t=times,
    r=rates,
    sigma=volatilities,
    is_call=is_calls
)

# Access individual Greek arrays
deltas = greeks_batch['delta']  # np.ndarray of shape (n,)
gammas = greeks_batch['gamma']  # np.ndarray of shape (n,)

# Statistical analysis
print(f"Average Delta: {np.mean(deltas):.4f}")
print(f"Max Gamma: {np.max(gammas):.4f}")
```

### American Option Greeks

American options follow the same unified format:

```python
import quantforge as qf
import numpy as np

# Single American option Greeks
greeks = qf.american_greeks(
    s=100.0,
    k=110.0,
    t=0.25,
    r=0.05,
    sigma=0.2,
    is_call=True,
    steps=100  # Number of binomial tree steps
)

# Batch American Greeks (unified format)
n = 100
greeks_batch = qf.american_greeks_batch(
    s=np.random.uniform(90, 110, n),
    k=np.full(n, 100.0),
    t=np.random.uniform(0.1, 1.0, n),
    r=np.full(n, 0.05),
    sigma=np.random.uniform(0.15, 0.35, n),
    is_call=np.ones(n, dtype=bool),
    steps=100
)

# Returns Dict[str, np.ndarray] - same as other models
print(f"Delta range: [{greeks_batch['delta'].min():.4f}, {greeks_batch['delta'].max():.4f}]")
```

## Model-Specific Notes

### Black-Scholes Greeks

Standard Greeks for European options under Black-Scholes assumptions.

### Black76 Greeks

Greeks for futures options. The spot price `s` represents the forward/futures price.

### Merton Jump Diffusion Greeks

Greeks accounting for jump risk:
```python
greeks = qf.merton_greeks(
    s=100.0,
    k=110.0,
    t=0.25,
    r=0.05,
    sigma=0.2,
    lambda_=0.1,  # Jump intensity
    mu_j=-0.05,   # Mean jump size
    sigma_j=0.1,  # Jump volatility
    is_call=True
)
```

### American Option Greeks

Calculated using the binomial tree method. The `steps` parameter controls accuracy:
- More steps = higher accuracy but slower computation
- Default: 100 steps (good balance)
- For high precision: 200-500 steps
- For quick estimates: 50 steps

## Performance Considerations

1. **Batch Processing**: Always prefer batch functions when calculating multiple options
2. **Memory Layout**: Dict format with NumPy arrays provides optimal cache locality
3. **Parallelization**: Batch functions automatically use parallel processing for large inputs
4. **Type Consistency**: All batch functions return the same Dict[str, np.ndarray] format

## Error Handling

All Greeks functions validate inputs and raise appropriate errors:

```python
try:
    greeks = qf.black_scholes_greeks(
        s=-100.0,  # Invalid: negative spot
        k=110.0,
        t=0.25,
        r=0.05,
        sigma=0.2,
        is_call=True
    )
except ValueError as e:
    print(f"Error: {e}")  # "s must be positive"
```

## See Also

- [Pricing Functions](pricing.md) - Option price calculations
- [Implied Volatility](implied_vol.md) - IV calculations
- [Batch Processing](batch_processing.md) - Efficient bulk calculations