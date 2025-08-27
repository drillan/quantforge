# Batch Processing API

## Overview

QuantForge provides high-performance batch processing capabilities for all option pricing models. The batch APIs support full array inputs with NumPy-style broadcasting, enabling efficient processing of large portfolios and market data.

## Key Features

- **Full Array Support**: All parameters accept arrays, not just single parameter variation
- **Broadcasting**: Automatic expansion of scalar values and length-1 arrays
- **Zero-Copy Performance**: Direct NumPy array processing without intermediate conversions
- **Parallel Execution**: Automatic parallelization using Rayon for large datasets
- **Consistent API**: Uniform interface across all models

## Broadcasting Rules

The batch APIs follow NumPy-style broadcasting rules:

1. **Scalar values** are automatically expanded to match the output size
2. **Length-1 arrays** are expanded to the required length
3. **Different length arrays** (except length 1) raise an error
4. **Output size** is determined by the maximum input array length

### Example

```python
import numpy as np
from quantforge.models import black_scholes

# Mixed scalar and array inputs
prices = black_scholes.call_price_batch(
    spots=np.array([95, 100, 105]),  # Array of 3 spot prices
    strikes=100.0,                    # Scalar, expanded to [100, 100, 100]
    times=1.0,                        # Scalar, expanded to [1.0, 1.0, 1.0]
    rates=0.05,                       # Scalar, expanded to [0.05, 0.05, 0.05]
    sigmas=np.array([0.2, 0.25, 0.3]) # Array of 3 volatilities
)
# Result: array of 3 prices
```

## API Reference

### Black-Scholes Model

#### call_price_batch

Calculate call option prices for multiple inputs.

```python
call_price_batch(spots, strikes, times, rates, sigmas) -> np.ndarray
```

**Parameters:**
- `spots`: Spot prices (scalar or array)
- `strikes`: Strike prices (scalar or array)
- `times`: Time to maturity in years (scalar or array)
- `rates`: Risk-free rates (scalar or array)
- `sigmas`: Volatilities (scalar or array)

**Returns:**
- NumPy array of call option prices

#### put_price_batch

Calculate put option prices for multiple inputs.

```python
put_price_batch(spots, strikes, times, rates, sigmas) -> np.ndarray
```

**Parameters:**
- Same as `call_price_batch`

**Returns:**
- NumPy array of put option prices

#### implied_volatility_batch

Calculate implied volatilities from market prices.

```python
implied_volatility_batch(prices, spots, strikes, times, rates, is_calls) -> np.ndarray
```

**Parameters:**
- `prices`: Market prices (scalar or array)
- `spots`: Spot prices (scalar or array)
- `strikes`: Strike prices (scalar or array)
- `times`: Time to maturity in years (scalar or array)
- `rates`: Risk-free rates (scalar or array)
- `is_calls`: Option types - True for calls, False for puts (scalar or array)

**Returns:**
- NumPy array of implied volatilities

#### greeks_batch

Calculate all Greeks for multiple inputs.

```python
greeks_batch(spots, strikes, times, rates, sigmas, is_calls) -> Dict[str, np.ndarray]
```

**Parameters:**
- `spots`: Spot prices (scalar or array)
- `strikes`: Strike prices (scalar or array)
- `times`: Time to maturity in years (scalar or array)
- `rates`: Risk-free rates (scalar or array)
- `sigmas`: Volatilities (scalar or array)
- `is_calls`: Option types (scalar or array)

**Returns:**
- Dictionary with keys: 'delta', 'gamma', 'vega', 'theta', 'rho'
- Each value is a NumPy array of the corresponding Greek

### Black76 Model

#### call_price_batch

Calculate call option prices for futures/forwards.

```python
call_price_batch(forwards, strikes, times, rates, sigmas) -> np.ndarray
```

**Parameters:**
- `forwards`: Forward/futures prices (scalar or array)
- `strikes`: Strike prices (scalar or array)
- `times`: Time to maturity in years (scalar or array)
- `rates`: Risk-free rates (scalar or array)
- `sigmas`: Volatilities (scalar or array)

**Returns:**
- NumPy array of call option prices

#### put_price_batch

Calculate put option prices for futures/forwards.

```python
put_price_batch(forwards, strikes, times, rates, sigmas) -> np.ndarray
```

#### implied_volatility_batch

```python
implied_volatility_batch(prices, forwards, strikes, times, rates, is_calls) -> np.ndarray
```

#### greeks_batch

```python
greeks_batch(forwards, strikes, times, rates, sigmas, is_calls) -> Dict[str, np.ndarray]
```

### Merton Model (Dividend-Adjusted)

#### call_price_batch

Calculate call option prices with continuous dividend yield.

```python
call_price_batch(spots, strikes, times, rates, dividend_yields, sigmas) -> np.ndarray
```

**Parameters:**
- `spots`: Spot prices (scalar or array)
- `strikes`: Strike prices (scalar or array)
- `times`: Time to maturity in years (scalar or array)
- `rates`: Risk-free rates (scalar or array)
- `dividend_yields`: Continuous dividend yields (scalar or array)
- `sigmas`: Volatilities (scalar or array)

**Returns:**
- NumPy array of call option prices

#### put_price_batch

```python
put_price_batch(spots, strikes, times, rates, dividend_yields, sigmas) -> np.ndarray
```

#### implied_volatility_batch

```python
implied_volatility_batch(prices, spots, strikes, times, rates, dividend_yields, is_calls) -> np.ndarray
```

#### greeks_batch

```python
greeks_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_calls) -> Dict[str, np.ndarray]
```

**Returns:**
- Dictionary with keys: 'delta', 'gamma', 'vega', 'theta', 'rho', 'dividend_rho'

### American Model

#### call_price_batch

Calculate American call option prices using Barone-Adesi-Whaley approximation.

```python
call_price_batch(spots, strikes, times, rates, dividend_yields, sigmas) -> np.ndarray
```

#### put_price_batch

```python
put_price_batch(spots, strikes, times, rates, dividend_yields, sigmas) -> np.ndarray
```

#### implied_volatility_batch

```python
implied_volatility_batch(prices, spots, strikes, times, rates, dividend_yields, is_calls) -> np.ndarray
```

#### greeks_batch

```python
greeks_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_calls) -> Dict[str, np.ndarray]
```

#### exercise_boundary_batch

Calculate optimal exercise boundaries for American options.

```python
exercise_boundary_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_calls) -> np.ndarray
```

**Returns:**
- NumPy array of optimal exercise prices

## Usage Examples

### Portfolio Valuation

```python
import numpy as np
from quantforge.models import black_scholes

# Portfolio of 1000 different options
n = 1000
spots = np.random.uniform(90, 110, n)
strikes = np.random.uniform(95, 105, n)
times = np.random.uniform(0.1, 2.0, n)
sigmas = np.random.uniform(0.15, 0.35, n)
rate = 0.05  # Same rate for all

# Calculate all prices at once
prices = black_scholes.call_price_batch(spots, strikes, times, rate, sigmas)
```

### Greeks for Risk Management

```python
# Calculate all Greeks for a portfolio
greeks = black_scholes.greeks_batch(spots, strikes, times, rate, sigmas, is_calls=True)

# Extract individual Greeks as arrays
portfolio_delta = greeks['delta'].sum()
portfolio_vega = greeks['vega'].sum()
portfolio_gamma = greeks['gamma'].sum()
```

### Implied Volatility Surface

```python
# Create volatility surface from market prices
spots = 100.0  # Current spot
strikes = np.linspace(80, 120, 41)
times = np.array([0.25, 0.5, 1.0, 2.0])

# Create grid
K, T = np.meshgrid(strikes, times)
strikes_flat = K.flatten()
times_flat = T.flatten()

# Market prices (example)
market_prices = np.random.uniform(5, 25, len(strikes_flat))

# Calculate implied volatilities
ivs = black_scholes.implied_volatility_batch(
    prices=market_prices,
    spots=spots,
    strikes=strikes_flat,
    times=times_flat,
    rates=0.05,
    is_calls=True
)

# Reshape for surface plot
iv_surface = ivs.reshape(K.shape)
```

### Sensitivity Analysis

```python
# Analyze option sensitivity to spot price changes
base_spot = 100.0
spot_range = np.linspace(80, 120, 100)

prices = black_scholes.call_price_batch(
    spots=spot_range,
    strikes=100.0,      # Fixed strike
    times=1.0,          # Fixed maturity
    rates=0.05,         # Fixed rate
    sigmas=0.2          # Fixed volatility
)

# Price sensitivity curve
import matplotlib.pyplot as plt
plt.plot(spot_range, prices)
plt.xlabel('Spot Price')
plt.ylabel('Option Price')
plt.title('Call Option Price Sensitivity')
```

## Performance Considerations

### Automatic Optimization

The batch APIs automatically optimize based on input size:

- **Small batches (< 1,000)**: Direct sequential processing
- **Medium batches (1,000 - 10,000)**: Vectorized operations
- **Large batches (10,000 - 100,000)**: Chunked processing
- **Very large batches (> 100,000)**: Parallel processing with Rayon

### Memory Efficiency

- Input arrays are accessed directly without copying (zero-copy)
- Output arrays are pre-allocated for efficiency
- Broadcasting doesn't create intermediate arrays

### Best Practices

1. **Use arrays when possible**: Even for uniform parameters, arrays can be more efficient than broadcasting scalars
2. **Pre-allocate output arrays**: For repeated calculations, reuse output arrays
3. **Batch similar calculations**: Group calculations with similar parameters together
4. **Monitor memory usage**: Very large batches may require chunking for memory-constrained systems

## Error Handling

### Broadcasting Errors

```python
# This will raise an error - incompatible array lengths
try:
    prices = black_scholes.call_price_batch(
        spots=np.array([100, 101, 102]),  # Length 3
        strikes=np.array([95, 100]),      # Length 2 - ERROR!
        times=1.0,
        rates=0.05,
        sigmas=0.2
    )
except ValueError as e:
    print(f"Broadcasting error: {e}")
```

### Numerical Errors

```python
# Implied volatility may return NaN for invalid inputs
ivs = black_scholes.implied_volatility_batch(
    prices=np.array([0.01, 50.0, -1.0]),  # Invalid negative price
    spots=100.0,
    strikes=100.0,
    times=1.0,
    rates=0.05,
    is_calls=True
)
# ivs[2] will be NaN due to negative price
```

## Migration Guide

### From Single Parameter Variation

Old API (single parameter variation):
```python
# OLD - Only spots could be an array
prices = black_scholes.call_price_batch(
    spots=[95, 100, 105],  # Array
    k=100.0,                # Scalar only
    t=1.0,                  # Scalar only
    r=0.05,                 # Scalar only
    sigma=0.2               # Scalar only
)
```

New API (full array support):
```python
# NEW - All parameters can be arrays
prices = black_scholes.call_price_batch(
    spots=[95, 100, 105],   # Array
    strikes=100.0,          # Can be scalar or array
    times=1.0,              # Can be scalar or array
    rates=0.05,             # Can be scalar or array
    sigmas=0.2              # Can be scalar or array
)
```

### From List[PyGreeks] to Dict

Old API:
```python
# OLD - Returns list of Greek objects
greeks_list = black_scholes.greeks_batch(...)
for greek in greeks_list:
    print(greek.delta, greek.gamma)
```

New API:
```python
# NEW - Returns dictionary of arrays
greeks_dict = black_scholes.greeks_batch(...)
print(greeks_dict['delta'])  # NumPy array of all deltas
print(greeks_dict['gamma'])  # NumPy array of all gammas
```

## See Also

- [Black-Scholes Model](black_scholes.md)
- [Black76 Model](black76.md)
- [Merton Model](merton.md)
- [American Options](american.md)
- [Performance Optimization](../performance/optimization.md)