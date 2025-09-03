# Python API Reference

A complete reference for the QuantForge Python API.

## Import Method

```python
from quantforge.models import black_scholes
```

## API Structure

### API Structure

It employs an explicit, highly extensible module-based design.

```python
from quantforge.models import black_scholes, black76

# Black-Scholes model (spot price)
# Parameters: s(spot), k(strike), t(time), r(rate), sigma
price_bs = black_scholes.call_price(100, 105, 1.0, 0.05, 0.2)
greeks_bs = black_scholes.greeks(100, 100, 1.0, 0.05, 0.2, True)
iv_bs = black_scholes.implied_volatility(10.45, 100, 100, 1.0, 0.05, True)

# Black76 model (forward price)
# Parameters: f(forward), k(strike), t(time), r(rate), sigma
price_b76 = black76.call_price(75, 70, 0.25, 0.05, 0.3)
greeks_b76 = black76.greeks(75, 70, 0.25, 0.05, 0.3, True)
iv_b76 = black76.implied_volatility(5.5, 75, 75, 0.5, 0.05, True)
```


## API Category

### Price Calculation
- [Pricing Calculation Functions](pricing.md) - Calculating option prices
- [Implied Volatility](implied_vol.md) - IV Calculation

### Greeks
- `black_scholes.greeks()` - Compute all Greeks at once

### Batch Calculation

```python
import pyarrow as pa
import numpy as np  # NumPy compatibility
from quantforge.models import black_scholes, black76

# Black-Scholes batch calculation (full array support + Broadcasting)
# PyArrow usage (recommended - Arrow-native)
spots = pa.array([95, 100, 105, 110])
sigmas = pa.array([0.18, 0.20, 0.22, 0.24])

# NumPy arrays also work (compatibility)
# spots = np.array([95, 100, 105, 110])

# All parameters accept arrays
prices_bs = black_scholes.call_price_batch(
    spots,
    100.0,    # strikes - Scalar automatically broadcasts
    1.0,      # times
    0.05,     # rates
    sigmas
)  # Returns: arro3.core.Array

# Greeks are returned as a dictionary
greeks_bs = black_scholes.greeks_batch(spots, 100.0, 1.0, 0.05, sigmas, is_calls=True)
# Each element is arro3.core.Array

# NumPy operations if needed, convert
print(np.array(greeks_bs['delta']))  # Convert to NumPy array
print(np.array(greeks_bs['gamma']))  # Convert to NumPy array

# Black76 batch calculation
forwards = pa.array([70, 75, 80, 85])
prices_b76 = black76.call_price_batch(forwards, 75.0, 0.5, 0.05, 0.25)
# prices_b76 also returns arro3.core.Array
```

For details, refer to the [Batch Processing API](batch_processing.md).

### Greek Calculations

```python
# Black-Scholes Greeks
# Parameters: s(spot), k, t, r, sigma, is_call
greeks = black_scholes.greeks(100, 100, 1.0, 0.05, 0.2, True)
print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
```

## Function Parameter Specifications

### Scalar Calculations (Single Values)

Function signatures for calculating a single option price:

**Functions**: `call_price(s, k, t, r, sigma)` / `put_price(s, k, t, r, sigma)`

| Parameter | Type | Description |
|-----------|------|-------------|
| s | float | Spot price (current price) |
| k | float | Strike price (exercise price) |
| t | float | Time to maturity (in years) |
| r | float | Risk-free rate |
| sigma | float | Volatility |

**Returns**: `float` - Option price

### Batch Calculations (Array Processing)

Function signatures for calculating multiple option prices at once:

**Functions**: `call_price_batch(spots, strikes, times, rates, sigmas)` / `put_price_batch(...)`

| Parameter | Type | Description |
|-----------|------|-------------|
| spots | pa.array \| np.ndarray \| float | Array of spot prices |
| strikes | pa.array \| np.ndarray \| float | Array of strike prices |
| times | pa.array \| np.ndarray \| float | Array of times to maturity |
| rates | pa.array \| np.ndarray \| float | Array of risk-free rates |
| sigmas | pa.array \| np.ndarray \| float | Array of volatilities |

**Returns**: `arro3.core.Array` - Arrow array of option prices

**Notes**:
- Batch functions support NumPy broadcasting
- Scalar values and arrays can be mixed (automatically broadcast)
- All arrays must have compatible shapes for broadcasting

### Greeks Return Values

**Scalar version** (`greeks()`): `PyGreeks` object
- Contains attributes: `delta`, `gamma`, `vega`, `theta`, `rho`

**Batch version** (`greeks_batch()`): Dictionary format
- Keys: `'delta'`, `'gamma'`, `'vega'`, `'theta'`, `'rho'`
- Values: `arro3.core.Array` for each Greek

### Usage Guidelines

| Use Case | Recommended Function | Reason |
|----------|---------------------|---------|
| Single calculation | `call_price()` | Simple and fast |
| Multiple calculations (100+) | `call_price_batch()` | Significantly faster via vectorization |
| Parameter sweeps | `call_price_batch()` | Leverages broadcasting |
| Interactive calculations | `call_price()` | Quick response time |

## Error Handling

### exception class

```python
class QuantForgeError(Exception):
    """QuantForge base exception class"""
    
class InvalidInputError(QuantForgeError):
    """Invalid input parameters"""
    
class ConvergenceError(QuantForgeError):
    """Numerical computation convergence failure"""
```

### Example Error Handling

```python
try:
    price = black_scholes.call_price(
        s=-100,  # Invalid negative value
        k=100,
        r=0.05,
        sigma=0.2,
        t=1.0
    )
except ValueError as e:
    print(f"Input error: {e}")
except RuntimeError as e:
    print(f"Calculation error: {e}")
```

## Performance Considerations

### Optimal Usage

1. **Use NumPy arrays**: Faster than lists
2. **Appropriate Batch Size**: 10,000 to 100,000 elements
3. **Memory alignment**: 64-byte boundary
4. **Consistent Data Types**: Use `float64`

### Performance Measurement

```python
import time

def benchmark(func, *args, n_iter=100):
    """Function benchmark"""
    times = []
    for _ in range(n_iter):
        start = time.perf_counter()
        func(*args)
        times.append(time.perf_counter() - start)
    
    return {
        'mean': np.mean(times) * 1000,  # ms
        'std': np.std(times) * 1000,
        'min': np.min(times) * 1000,
        'max': np.max(times) * 1000
    }

# Execute benchmark
spots = np.random.uniform(90, 110, 100000)
stats = benchmark(qf.calculate, spots, 100, 0.05, 0.2, 1.0)
print(f"Mean: {stats['mean']:.2f}ms ± {stats['std']:.2f}ms")
```

## Thread Safety

QuantForge functions are **thread-safe**:

```python
from concurrent.futures import ThreadPoolExecutor

def price_batch(spots):
    return qf.calculate(spots, 100, 0.05, 0.2, 1.0)

# Multi-threaded execution
with ThreadPoolExecutor(max_workers=4) as executor:
    batches = np.array_split(large_spots_array, 4)
    results = list(executor.map(price_batch, batches))
    final_results = np.concatenate(results)
```

## Next Step

- [Pricing API](pricing.md) - Detailed pricing calculation functions
- [Implied Volatility API](implied_vol.md) - IV Calculation Functions
- [Rust API](../rust/index.md) - Low-level Rust API
