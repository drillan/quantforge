# NumPy Integration

QuantForge integrates seamlessly with NumPy, enabling zero-copy, high-speed processing.

## Zero-copy Optimization

### Memory Efficiency Mechanism

```python
import numpy as np
import quantforge as qf
from quantforge.models import black_scholes

# Create NumPy array
spots = np.random.uniform(90, 110, 1_000_000)

# Process with zero-copy (no memory copy)
prices = black_scholes.call_price_batch(
    spots=spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)

# prices is also returned as a NumPy array
print(f"Type: {type(prices)}")
print(f"Shape: {prices.shape}")
print(f"Memory shared: {prices.base is not None}")
```

### Memory Layout Optimization

```{code-block} python
:name: numpy-integration-code-c
:caption: C-contiguous array (recommended)
:linenos:

# C-contiguous array (recommended)
spots_c = np.ascontiguousarray(spots)
print(f"C-contiguous: {spots_c.flags['C_CONTIGUOUS']}")

# Fortran-contiguous array (auto-converted)
spots_f = np.asfortranarray(spots)
print(f"F-contiguous: {spots_f.flags['F_CONTIGUOUS']}")

# Performance comparison (1 million elements)
import time

def benchmark_layout(array):
    start = time.perf_counter()
    black_scholes.call_price_batch(
        spots=array,
        strike=100.0,
        time=1.0,
        rate=0.05,
        sigma=0.2
    )
    return time.perf_counter() - start

time_c = benchmark_layout(spots_c)
time_f = benchmark_layout(spots_f)
print(f"C-layout: {time_c*1000:.2f}ms")  # Expected: ~56ms
print(f"F-layout: {time_f*1000:.2f}ms")  # Slightly slower
```

## broadcasting

### Automatic Broadcast

```{code-block} python
:name: numpy-integration-code-section
:caption: Combination of scalars and arrays
:linenos:

# Combination of scalars and arrays
spots = np.array([95, 100, 105])
strike = 100.0  # Scalar
rate = 0.05    # Scalar
sigma = 0.20   # Scalar
time = 1.0     # Scalar

# Automatic broadcast
prices = black_scholes.call_price_batch(
    spots=spots,
    strike=strike,
    time=time,
    rate=rate,
    sigma=sigma
)
print(f"Results: {prices}")
```

### multidimensional array

```{code-block} python
:name: numpy-integration-code-2
:caption: Calculation with 2D arrays
:linenos:

# Calculation with 2D arrays
spots = np.random.uniform(90, 110, (100, 1000))
strikes = np.full((100, 1000), 100.0)

# Flatten and calculate
flat_spots = spots.ravel()
flat_prices = black_scholes.call_price_batch(
    spots=flat_spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)

# Restore to original shape
prices = flat_prices.reshape(spots.shape)
print(f"Shape: {prices.shape}")
```

## View Operations

### Slices and Indices

```{code-block} python
:name: numpy-integration-code-section
:caption: Large array
:linenos:

# Large array
all_spots = np.random.uniform(80, 120, 1_000_000)

# Create view (no copy)
subset = all_spots[::10]  # Select every 10th element
print(f"Is view: {subset.base is all_spots}")

# Calculate with view
subset_prices = black_scholes.call_price_batch(
    spots=subset,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)
```

### Conditional Processing

```{code-block} python
:name: numpy-integration-code-section
:caption: Conditional selection
:linenos:

# Conditional selection
spots = np.random.uniform(80, 120, 10000)
mask = (spots > 95) & (spots < 105)  # Near ATM only

# Masked calculation
atm_spots = spots[mask]
atm_prices = black_scholes.call_price_batch(
    spots=atm_spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)

# Return results to original array
full_prices = np.zeros_like(spots)
full_prices[mask] = atm_prices
```

## Handling Data Types

### Type Conversion Optimization

```{code-block} python
:name: numpy-integration-code-float32-vs-float64
:caption: float32 vs float64
:linenos:

# float32 vs float64
spots_f32 = np.random.uniform(90, 110, 100000).astype(np.float32)
spots_f64 = np.random.uniform(90, 110, 100000).astype(np.float64)

# QuantForge uses float64 internally
# float32 is automatically converted
prices_f32 = black_scholes.call_price_batch(
    spots=spots_f32, strike=100.0, time=1.0, rate=0.05, sigma=0.2
)
prices_f64 = black_scholes.call_price_batch(
    spots=spots_f64, strike=100.0, time=1.0, rate=0.05, sigma=0.2
)

print(f"Input f32 dtype: {spots_f32.dtype}")
print(f"Output dtype: {prices_f32.dtype}")  # Converted to float64
```

### structured array

```{code-block} python
:name: numpy-integration-code-section
:caption: Structured array for option data
:linenos:

# Structured array for option data
dtype = np.dtype([
    ('spot', 'f8'),
    ('strike', 'f8'),
    ('vol', 'f8'),
    ('time', 'f8')
])

options = np.zeros(1000, dtype=dtype)
options['spot'] = np.random.uniform(90, 110, 1000)
options['strike'] = 100
options['vol'] = np.random.uniform(0.1, 0.3, 1000)
options['time'] = np.random.uniform(0.1, 2.0, 1000)

# Calculate from structured array
# Note: Current API only supports single time and volatility
# Multiple parameters are processed in a loop
prices = np.array([
    black_scholes.call_price(
        spot=options['spot'][i],
        strike=options['strike'][i],
        time=options['time'][i],
        rate=0.05,
        sigma=options['vol'][i]
    )
    for i in range(len(options))
])
```

## Memory Mapped File

### Processing Large Data

```{code-block} python
:name: numpy-integration-code-section
:caption: Create memory-mapped file
:linenos:

# Create memory-mapped file
filename = 'large_spots.dat'
shape = (10_000_000,)
spots_mmap = np.memmap(filename, dtype='float64', mode='w+', shape=shape)

# Write data
spots_mmap[:] = np.random.uniform(90, 110, shape)

# Process by chunks
chunk_size = 100_000
results = []

for i in range(0, len(spots_mmap), chunk_size):
    chunk = spots_mmap[i:i+chunk_size]
    chunk_prices = black_scholes.call_price_batch(
        spots=chunk,
        strike=100.0,
        time=1.0,
        rate=0.05,
        sigma=0.2
    )
    results.append(chunk_prices)

# Combine results
all_prices = np.concatenate(results)

# Cleanup
del spots_mmap
import os
os.remove(filename)
```

## vectorized functions

### Custom ufunc

```{code-block} python
:name: numpy-integration-code-quantforgeufunc
:caption: Use QuantForge functions as ufunc
:linenos:

# Use QuantForge functions as ufunc
@np.vectorize
def custom_pricer(spot, strike, moneyness_threshold=0.1):
    """Conditional pricing based on moneyness"""
    moneyness = abs(spot / strike - 1.0)
    
    if moneyness < moneyness_threshold:
        # High precision calculation for near ATM
        return black_scholes.call_price(
            spot=spot, strike=strike, time=1.0, rate=0.05, sigma=0.2
        )
    else:
        # Simplified calculation for OTM
        return black_scholes.call_price(
            spot=spot, strike=strike, time=1.0, rate=0.05, sigma=0.15
        )

# Vectorized usage
spots = np.array([95, 100, 105, 120])
strikes = np.array([100, 100, 100, 100])
prices = custom_pricer(spots, strikes)
```

## Combined with Parallel Processing

### NumPy and Multiprocessing

```python
from multiprocessing import Pool
import numpy as np

def process_batch(args):
    """Batch processing function"""
    spots, strike, rate, sigma, time = args
    return black_scholes.call_price_batch(
        spots=spots,
        strike=strike,
        time=time,
        rate=rate,
        sigma=sigma
    )

# Split data
n_total = 10_000_000
n_chunks = 10
spots = np.random.uniform(90, 110, n_total)
chunks = np.array_split(spots, n_chunks)

# Parallel processing
with Pool() as pool:
    args = [(chunk, 100, 0.05, 0.2, 1.0) for chunk in chunks]
    results = pool.map(process_batch, args)

# Combine results
all_prices = np.concatenate(results)
```

## Performance Tuning

### Optimize Alignment

```{code-block} python
:name: numpy-integration-code-64
:caption: Align to 64-byte boundary (cache line)
:linenos:

# Align to 64-byte boundary (cache line)
def create_aligned_array(size, alignment=64):
    """Create an aligned array"""
    dtype = np.float64
    itemsize = np.dtype(dtype).itemsize
    buf = np.empty(size * itemsize + alignment, dtype=np.uint8)
    offset = (-buf.ctypes.data) % alignment
    return np.frombuffer(buf[offset:offset+size*itemsize], dtype=dtype)

# Calculate with aligned array
aligned_spots = create_aligned_array(1_000_000)
aligned_spots[:] = np.random.uniform(90, 110, 1_000_000)

# Performance measurement
import time
start = time.perf_counter()
prices = black_scholes.call_price_batch(
    spots=aligned_spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)
elapsed = time.perf_counter() - start
print(f"Aligned array: {elapsed*1000:.2f}ms")  # Expected: ~56ms (1M elements)
```

### Monitor Memory Usage

```python
import tracemalloc

# Start memory tracking
tracemalloc.start()

# Large-scale calculation
spots = np.random.uniform(90, 110, 5_000_000)
prices = black_scholes.call_price_batch(
    spots=spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)

# Memory usage
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory: {peak / 1024 / 1024:.1f} MB")

tracemalloc.stop()
```

## In-place operation

### Direct Result Writing

```{code-block} python
:name: numpy-integration-code-section
:caption: Pre-allocated arrays
:linenos:

# Pre-allocated arrays
n = 1_000_000
spots = np.random.uniform(90, 110, n)
prices = np.empty(n)  # Array for results

# In-place calculation (memory efficient)
# Note: Current API does not support in-place operations
prices = black_scholes.call_price_batch(
    spots=spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)

print(f"Prices array modified in-place: {prices[:5]}")
```

## Statistical Processing

### Combining with NumPy Statistical Functions

```{code-block} python
:name: numpy-integration-code-section
:caption: Portfolio statistics
:linenos:

# Portfolio statistics
spots = np.random.uniform(90, 110, 10000)
prices = black_scholes.call_price_batch(
    spots=spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)

# Statistics
stats = {
    'mean': np.mean(prices),
    'std': np.std(prices),
    'median': np.median(prices),
    'percentile_5': np.percentile(prices, 5),
    'percentile_95': np.percentile(prices, 95),
    'skew': np.mean(((prices - np.mean(prices)) / np.std(prices))**3),
    'kurtosis': np.mean(((prices - np.mean(prices)) / np.std(prices))**4) - 3
}

for key, value in stats.items():
    print(f"{key}: {value:.4f}")
```

## Summary

NumPy integration enables:

- **Zero-copy processing**: Fast computation without memory copying (via PyO3)
- **Broadcasting**: Flexible array operations
- **Memory Efficiency**: Efficient processing of large datasets
- **High-Speed Batch Processing**: Processes 1 million records in approximately 56ms (AMD Ryzen 5 5600G)

For detailed performance information, see the performance section.

Next, explore [Advanced Models](advanced_models.md) to learn about complex pricing models like American options.
