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

For batch computations, the Greeks are returned as a `Dict[str, arro3.core.Array]`, where each Greek is an Arrow array:

```python
# バッチ計算の戻り値例:
# {
#     'delta': arro3.core.Array,    # Array of delta values
#     'gamma': arro3.core.Array,    # Array of gamma values
#     'theta': arro3.core.Array,    # Array of theta values
#     'vega': arro3.core.Array,     # Array of vega values
#     'rho': arro3.core.Array       # Array of rho values
# }
```

This format is consistent across all models:
- Black-Scholes (`black_scholes.greeks_batch`)
- Black76 (`black76.greeks_batch`)
- Merton (`merton.greeks_batch`)
- American Option (`american.greeks_batch`)

## Memory Efficiency

The batch format uses Arrow arrays for optimal memory efficiency:

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

from quantforge.models import black_scholes

# Black-Scholes model
greeks = black_scholes.greeks(
    100.0,      # s: Spot price
    110.0,      # k: Strike price
    0.25,       # t: Time to maturity
    0.05,       # r: Risk-free rate
    0.2,        # sigma: Volatility
    True        # is_call: Call option
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
from quantforge.models import black_scholes

# Prepare batch inputs
n = 1000
spots = np.random.uniform(90, 110, n)
strikes = np.full(n, 100.0)
times = np.random.uniform(0.1, 2.0, n)
rates = np.full(n, 0.05)
volatilities = np.random.uniform(0.15, 0.35, n)
is_calls = np.ones(n, dtype=bool)

# Calculate Greeks for all options at once
greeks_batch = black_scholes.greeks_batch(
    spots,
    strikes,
    times,
    rates,
    volatilities,
    True  # is_call - all call options
)

# Access individual Greeks arrays
deltas = greeks_batch['delta']  # arro3.core.Array with shape (n,)
gammas = greeks_batch['gamma']  # arro3.core.Array with shape (n,)

# Statistical analysis
print(f"Average delta: {np.mean(np.array(deltas)):.4f}")
print(f"Maximum gamma: {np.max(np.array(gammas)):.4f}")
```

### American Option Greeks

American options also follow this unified format:

```{code-block} python
:name: greeks-code-american-option-example
:caption: American option Greeks
:linenos:

from quantforge.models import american
import numpy as np

# Single American option Greeks
greeks = american.greeks(
    100.0,      # s: Spot price
    110.0,      # k: Strike price
    0.25,       # t: Time to maturity
    0.05,       # r: Risk-free rate
    0.03,       # q: Dividend yield
    0.2,        # sigma: Volatility
    True        # is_call: Call option
)

# Batch American Greeks (unified format)
n = 100
spots = np.random.uniform(90, 110, n)
greeks_batch = american.greeks_batch(
    spots,
    np.full(n, 100.0),
    np.random.uniform(0.1, 1.0, n),
    np.full(n, 0.05),
    np.full(n, 0.03),  # Dividend yield
    np.random.uniform(0.15, 0.35, n),
    True  # is_call - all call options
)

# Returns Dict[str, arro3.core.Array] - same as other models
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

from quantforge.models import merton

greeks = merton.greeks(
    100.0,      # s: Spot price
    110.0,      # k: Strike price
    0.25,       # t: Time to maturity
    0.05,       # r: Risk-free rate
    0.03,       # q: Dividend yield
    0.2,        # sigma: Volatility
    True        # is_call: Call option
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
2. **Memory Layout**: Dict formats with Arrow arrays provide optimal cache locality
3. **Parallelization**: The Batch function automatically utilizes parallel processing for large inputs
4. **Type consistency**: All batch functions return the same Dict[str, arro3.core.Array] format

## Error Handling

All Greek functions validate their inputs and raise appropriate errors:

```{code-block} python
:name: greeks-code-error-handling-example
:caption: Error handling example
:linenos:

from quantforge.models import black_scholes

try:
    greeks = black_scholes.greeks(
        -100.0,  # Invalid: negative spot
        110.0,
        0.25,
        0.05,
        0.2,
        True
    )
except ValueError as e:
    print(f"Error: {e}")  # "s must be positive"
```

## Related Information

- [Pricing Calculation Functions](pricing.md) - Option pricing calculations
- [Implied Volatility](implied_vol.md) - IV Calculation
- [Batch Processing](batch_processing.md) - Efficient bulk computation
