# NumPy to PyArrow Migration Guide

## Overview

QuantForge adopts an Arrow-native design while maintaining full compatibility with NumPy. This guide explains how to smoothly migrate from NumPy to PyArrow.

## Why Migrate to PyArrow?

### Performance Benefits

1. **Zero-copy FFI**: No data copying between Python and Rust
2. **Memory efficiency**: No intermediate buffers required
3. **Processing speed**: Approximately 1.5x faster for large-scale data

### Ecosystem Benefits

1. **Integration with modern DataFrame libraries**: Polars, DuckDB, etc.
2. **Distributed processing support**: Good compatibility with Ray and Dask
3. **Standardized format**: Cross-language compatibility

## Basic Conversions

### Array Creation

| Operation | NumPy | PyArrow |
|-----------|-------|---------|
| Create from list | `np.array([1, 2, 3])` | `pa.array([1, 2, 3])` |
| Zero array | `np.zeros(10)` | `pa.array([0] * 10)` or `pa.nulls(10, pa.float64())` |
| Sequence | `np.arange(10)` | `pa.array(range(10))` |
| Repeat | `np.full(10, 5.0)` | `pa.array([5.0] * 10)` |
| Random | `np.random.uniform(0, 1, 10)` | `pa.array(np.random.uniform(0, 1, 10))` |

### Data Type Specification

| NumPy | PyArrow |
|-------|---------|
| `np.array([1, 2, 3], dtype=np.float64)` | `pa.array([1, 2, 3], type=pa.float64())` |
| `np.array([1, 2, 3], dtype=np.int32)` | `pa.array([1, 2, 3], type=pa.int32())` |
| `np.array([True, False], dtype=bool)` | `pa.array([True, False], type=pa.bool_())` |

## Usage Examples with QuantForge

### Migration from NumPy (Before/After)

#### Before (NumPy)
```python
import numpy as np
from quantforge.models import black_scholes

# Using NumPy arrays
spots = np.array([95, 100, 105, 110])
strikes = np.full(4, 100.0)
times = np.ones(4)
rates = np.full(4, 0.05)
sigmas = np.array([0.18, 0.20, 0.22, 0.24])

# Batch calculation
prices = black_scholes.call_price_batch(
    spots=spots,
    strikes=strikes,
    times=times,
    rates=rates,
    sigmas=sigmas
)

# Process results (Arrow array returned)
mean_price = np.mean(np.array(prices))  # Needs conversion to NumPy
```

#### After (PyArrow)
```python
import pyarrow as pa
import numpy as np  # For statistical processing
from quantforge.models import black_scholes

# Using PyArrow arrays
spots = pa.array([95, 100, 105, 110])
strikes = pa.array([100.0] * 4)
times = pa.array([1.0] * 4)
rates = pa.array([0.05] * 4)
sigmas = pa.array([0.18, 0.20, 0.22, 0.24])

# Batch calculation (more efficient)
prices = black_scholes.call_price_batch(
    spots=spots,
    strikes=strikes,
    times=times,
    rates=rates,
    sigmas=sigmas
)

# Process results (convert to NumPy if needed)
mean_price = np.mean(np.array(prices))
```

### Gradual Migration Strategy

#### Step 1: PyArrow for Input Data Only
```python
# Create NumPy array then convert to PyArrow
np_data = np.random.uniform(90, 110, 1000)
spots = pa.array(np_data)  # Convert to PyArrow

prices = black_scholes.call_price_batch(
    spots=spots,  # PyArrow
    strikes=100.0,  # Scalar (auto-processed)
    times=1.0,
    rates=0.05,
    sigmas=0.2
)
```

#### Step 2: Full PyArrow Migration
```python
# Work with PyArrow from the start
spots = pa.array(np.random.uniform(90, 110, 1000))
strikes = pa.array([100.0] * 1000)

prices = black_scholes.call_price_batch(
    spots=spots,
    strikes=strikes,
    times=1.0,
    rates=0.05,
    sigmas=0.2
)
```

## DataFrame Integration

### Interoperability with Pandas DataFrame
```python
import pandas as pd
import pyarrow as pa

# Pandas DataFrame
df = pd.DataFrame({
    'spot': [95, 100, 105],
    'strike': [100, 100, 100],
    'time': [1.0, 1.0, 1.0],
    'rate': [0.05, 0.05, 0.05],
    'sigma': [0.2, 0.2, 0.2]
})

# Pandas to PyArrow
spots_arrow = pa.array(df['spot'].values)
strikes_arrow = pa.array(df['strike'].values)

# Calculate with QuantForge
prices = black_scholes.call_price_batch(
    spots=spots_arrow,
    strikes=strikes_arrow,
    times=df['time'].iloc[0],  # Scalar value
    rates=df['rate'].iloc[0],
    sigmas=df['sigma'].iloc[0]
)

# Add results to DataFrame
df['option_price'] = np.array(prices)
```

### Integration with Polars DataFrame (Recommended)
```python
import polars as pl

# Polars DataFrame (Arrow-native)
df = pl.DataFrame({
    'spot': [95, 100, 105],
    'strike': [100, 100, 100],
    'time': [1.0, 1.0, 1.0],
    'rate': [0.05, 0.05, 0.05],
    'sigma': [0.2, 0.2, 0.2]
})

# Polars uses Arrow internally
prices = black_scholes.call_price_batch(
    spots=df['spot'].to_arrow(),
    strikes=df['strike'].to_arrow(),
    times=df['time'][0],  # Scalar value
    rates=df['rate'][0],
    sigmas=df['sigma'][0]
)

# Add results (efficient)
df = df.with_columns(
    pl.Series('option_price', prices)
)
```

## Large-Scale Data Processing Comparison

### NumPy Style (Traditional)
```python
import numpy as np
import time

n = 10_000_000

# Create NumPy arrays
start = time.perf_counter()
spots_np = np.random.uniform(90, 110, n)
strikes_np = np.full(n, 100.0)

# Calculate (internally converted to Arrow)
prices = black_scholes.call_price_batch(
    spots=spots_np,
    strikes=strikes_np,
    times=1.0,
    rates=0.05,
    sigmas=0.2
)
total_time = time.perf_counter() - start

print(f"NumPy input: {total_time:.3f} seconds")
```

### PyArrow Style (Recommended)
```python
import pyarrow as pa
import numpy as np
import time

n = 10_000_000

# Create PyArrow arrays
start = time.perf_counter()
spots_pa = pa.array(np.random.uniform(90, 110, n))
strikes_pa = pa.array([100.0] * n)

# Calculate (zero-copy)
prices = black_scholes.call_price_batch(
    spots=spots_pa,
    strikes=strikes_pa,
    times=1.0,
    rates=0.05,
    sigmas=0.2
)
total_time = time.perf_counter() - start

print(f"PyArrow input: {total_time:.3f} seconds")
# Expect 10-20% speedup
```

## Frequently Asked Questions

### Q: Do I need to rewrite all existing NumPy code?

A: No, QuantForge accepts NumPy arrays as well, allowing for gradual migration. You can migrate performance-critical parts first.

### Q: Can I do statistical processing with PyArrow?

A: Basic aggregations (sum, mean, etc.) are possible, but NumPy or SciPy is needed for advanced statistical processing. We recommend converting results to NumPy for such operations.

```python
# Calculate with PyArrow
prices = black_scholes.call_price_batch(...)

# Statistical processing with NumPy
prices_np = np.array(prices)
mean = np.mean(prices_np)
std = np.std(prices_np)
percentile_95 = np.percentile(prices_np, 95)
```

### Q: Will memory usage increase?

A: No, it will actually decrease. Arrow format has an efficient memory layout and doesn't require intermediate buffers, reducing overall memory usage.

### Q: Are there compatibility issues?

A: QuantForge internally handles both NumPy and PyArrow appropriately, so there are no compatibility issues. However, return values are always Arrow arrays (arro3.core.Array).

## Migration Checklist

- [ ] Install PyArrow: `pip install pyarrow`
- [ ] Identify performance-critical sections
- [ ] Convert input data to PyArrow arrays
- [ ] Check result processing needs (conversion to NumPy needed?)
- [ ] Verify improvements with benchmarks
- [ ] Gradually migrate everything

## Summary

Migration to PyArrow provides the following benefits:

1. **Immediate effect**: 10-20% speedup for large-scale data
2. **Future-proofing**: Integration with modern data processing ecosystem
3. **Memory efficiency**: Reduced memory usage through zero-copy
4. **Maintained compatibility**: Gradual migration without breaking existing code

To maximize the benefits of QuantForge's Arrow-native design, we recommend using PyArrow for new code.