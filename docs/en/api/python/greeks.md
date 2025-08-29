# GreeKS API Reference

## Overview

The Greeks represent a financial risk metric that describes how option prices respond to various factors. QuantForge provides unified, high-performance Greeks calculations for all option pricing models.

## Return Value Format Specification

All Greeks functions in QuantForge follow a unified return value format for consistency and ease of use:

### Single Option Greeks

For single-option calculations, the Greeks are returned as a `dict` with the following structure:

```python
{
    'delta': float,    # Rate of change of option price with respect to spot price
    'gamma': float,    # Rate of change of delta with respect to spot price
    'theta': float,    # Rate of change of option price with respect to time
    'vega': float,     # Rate of change of option price with respect to volatility
    'rho': float       # Rate of change of option price with respect to interest rate
}
```

### Batch Greeks Calculation

For batch computations, the Greeks are returned as a `Dict[str, np.ndarray]`, where each Greek is a NumPy array:

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
- American Option (`quantforge.american_greeks_batch`)

## Memory Efficiency

The batch format uses NumPy arrays for optimal memory efficiency:

```{code-block} python
:name: greeks-code-structure-of-arrays-soa
:caption: Structure of Arrays (SoA) - memory efficient
:linenos:
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

## Examples

### Single Option Greeks

```{code-block} python
:name: greeks-code-single-option-example
:caption: Single option Greeks calculation
:linenos:

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

### Batch Greeks Calculation

```{code-block} python
:name: greeks-code-batch-calculation-example
:caption: Batch Greeks calculation
:linenos:

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

# Access individual Greeks arrays
deltas = greeks_batch['delta']  # np.ndarray with shape (n,)
gammas = greeks_batch['gamma']  # np.ndarray with shape (n,)

# Statistical analysis
print(f"Average delta: {np.mean(deltas):.4f}")
print(f"Maximum gamma: {np.max(gammas):.4f}")
```

### American Option Greeks

American options also follow this unified format:

```{code-block} python
:name: greeks-code-american-option-example
:caption: American option Greeks
:linenos:

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

## Model-specific notes

### Black-Scholes Greeks

Standard Greeks for European options under the Black-Scholes assumptions.

### Black76 Greeks

Greeks for futures options. The spot price `s` represents the forward/futures price.

### Merton Jump Diffusion Greeks

Jump-Risk-Adjusted Greeks:

```{code-block} python
:name: greeks-code-merton-greeks-example
:caption: Merton Jump Diffusion Greeks
:linenos:

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

Calculated using the binary tree method. The `steps` parameter controls precision:
- More steps = Higher precision but slower computation
- Default: 100 steps (balanced)
- For high precision: 200-500 steps
- For approximation: 50 steps

## Performance Considerations

1. **Batch Processing**: Always prefer batch functions when calculating multiple options
2. **Memory Layout**: Dict formats with NumPy arrays provide optimal cache locality
3. **Parallelization**: The Batch function automatically utilizes parallel processing for large inputs
4. **Type consistency**: All batch functions return the same Dict[str, np.ndarray] format

## Error Handling

All Greek functions validate their inputs and raise appropriate errors:

```{code-block} python
:name: greeks-code-error-handling-example
:caption: Error handling example
:linenos:

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

## Related Information

- [Pricing Calculation Functions](pricing.md) - Option pricing calculations
- [Implied Volatility](implied_vol.md) - IV Calculation
- [Batch Processing](batch_processing.md) - Efficient bulk computation
