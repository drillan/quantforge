# Optimization Guide

Comprehensive guide to QuantForge optimization techniques.

## Overview

QuantForge achieves extreme performance through multiple optimization layers:
- **Algorithm-level**: Optimal mathematical algorithms
- **Implementation-level**: Rust's zero-cost abstractions
- **System-level**: Parallel processing and vectorization

## Micro-batch Optimization

### 4-Element Loop Unrolling

For small batches of 100-1000 elements, we implement special optimization:

```rust
// 4-element loop unrolling for compiler auto-vectorization
pub fn black_scholes_call_micro_batch(
    spots: &[f64],
    strikes: &[f64],
    times: &[f64],
    rates: &[f64],
    sigmas: &[f64],
    output: &mut [f64],
) {
    let len = spots.len();
    let chunks = len / 4;

    // Process 4 elements at a time
    for i in 0..chunks {
        let idx = i * 4;
        output[idx] = black_scholes_call_scalar(
            spots[idx], strikes[idx], times[idx], 
            rates[idx], sigmas[idx]
        );
        output[idx + 1] = black_scholes_call_scalar(
            spots[idx + 1], strikes[idx + 1], times[idx + 1],
            rates[idx + 1], sigmas[idx + 1]
        );
        output[idx + 2] = black_scholes_call_scalar(
            spots[idx + 2], strikes[idx + 2], times[idx + 2],
            rates[idx + 2], sigmas[idx + 2]
        );
        output[idx + 3] = black_scholes_call_scalar(
            spots[idx + 3], strikes[idx + 3], times[idx + 3],
            rates[idx + 3], sigmas[idx + 3]
        );
    }

    // Process remaining elements
    for i in (chunks * 4)..len {
        output[i] = black_scholes_call_scalar(
            spots[i], strikes[i], times[i], rates[i], sigmas[i]
        );
    }
}
```

This optimization provides:
- **Instruction-Level Parallelism (ILP)** improvement
- **Compiler auto-vectorization** encouragement
- **Branch prediction** efficiency
- **Cache line** utilization

### Micro-batch Threshold

```rust
// MICRO_BATCH_THRESHOLD: Apply micro-batch optimization for ≤1000 elements
if data.len() <= MICRO_BATCH_THRESHOLD {
    black_scholes_call_micro_batch(/* ... */);
} else {
    // Regular parallel processing
}
```

## High-Speed Mathematical Functions

### Fast erf Approximation

Using Abramowitz & Stegun approximation for high-speed erf implementation:

```rust
/// Fast erf approximation
/// Accuracy: 1.5e-7 (sufficient for financial calculations)
/// Speed: 2-3x faster than libm::erf
#[inline(always)]
pub fn fast_erf(x: f64) -> f64 {
    // Abramowitz & Stegun coefficients
    let a1 = 0.254829592;
    let a2 = -0.284496736;
    let a3 = 1.421413741;
    let a4 = -1.453152027;
    let a5 = 1.061405429;
    let p = 0.3275911;

    let sign = if x < 0.0 { -1.0 } else { 1.0 };
    let x = x.abs();

    let t = 1.0 / (1.0 + p * x);
    let y = 1.0 - (((((a5 * t + a4) * t + a3) * t + a2) * t + a1) 
            * t * (-x * x).exp());

    sign * y
}

/// Fast norm_cdf implementation
#[inline(always)]
pub fn fast_norm_cdf(x: f64) -> f64 {
    if x > NORM_CDF_UPPER_BOUND {
        1.0
    } else if x < NORM_CDF_LOWER_BOUND {
        0.0
    } else {
        0.5 * (1.0 + fast_erf(x / std::f64::consts::SQRT_2))
    }
}
```

### Performance Characteristics

| Function | Previous Implementation | Fast Implementation | Improvement |
|----------|------------------------|--------------------|--------------|
| erf | libm::erf | fast_erf | 2-3x |
| norm_cdf | erf-based | fast_norm_cdf | 2-3x |
| norm_pdf | unchanged | fast_norm_pdf | - |

### Accuracy vs Performance Trade-off

- **Absolute Error**: < 1.5e-7
- **Relative Error**: < 1e-6
- **Use Case**: Sufficient accuracy for option pricing
- **Note**: Use standard implementation for scientific computing requiring higher precision

## Algorithm Optimization

### 1. Black-Scholes Formula Optimization

#### Standard Implementation
Traditional implementations use `scipy.stats.norm.cdf` which is general-purpose but slow.

#### QuantForge Optimization
- Custom error function implementation using Abramowitz & Stegun approximation
- Optimized polynomial evaluation using Horner's method
- Single-precision fallback for non-critical calculations

```rust
// Optimized normal CDF calculation
pub fn norm_cdf_optimized(x: f64) -> f64 {
    if x > 8.0 {
        1.0
    } else if x < -8.0 {
        0.0
    } else {
        // Abramowitz & Stegun approximation
        let a1 =  0.254829592;
        let a2 = -0.284496736;
        let a3 =  1.421413741;
        let a4 = -1.453152027;
        let a5 =  1.061405429;
        let p  =  0.3275911;
        
        let sign = if x < 0.0 { -1.0 } else { 1.0 };
        let x = x.abs();
        
        let t = 1.0 / (1.0 + p * x);
        let t2 = t * t;
        let t3 = t2 * t;
        let t4 = t3 * t;
        let t5 = t4 * t;
        
        let y = 1.0 - ((((a5 * t5 + a4 * t4) + a3 * t3) + a2 * t2) + a1 * t) * (-x * x).exp();
        
        0.5 * (1.0 + sign * y)
    }
}
```

### 2. Implied Volatility Optimization

#### Traditional Newton-Raphson
- Good convergence but requires good initial guess
- Can fail for extreme values

#### QuantForge Hybrid Approach
1. **Smart Initial Guess**: Based on option moneyness and time to expiry
2. **Bounded Newton-Raphson**: With fallback to bisection
3. **Early Exit**: For deep ITM/OTM options

```rust
pub fn implied_volatility_optimized(
    price: f64,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    is_call: bool,
) -> Result<f64, String> {
    // Smart initial guess based on ATM approximation
    let initial_vol = (2.0 * PI / t).sqrt() * (price / s);
    
    // Bounded iteration with convergence check
    let mut vol = initial_vol;
    for _ in 0..MAX_ITERATIONS {
        let price_calc = black_scholes(s, k, t, r, vol, is_call);
        let vega = black_scholes_vega(s, k, t, r, vol);
        
        if vega < VEGA_THRESHOLD {
            // Switch to bisection for numerical stability
            return bisection_fallback(price, s, k, t, r, is_call);
        }
        
        let diff = price_calc - price;
        if diff.abs() < PRICE_TOLERANCE {
            return Ok(vol);
        }
        
        vol -= diff / vega;
        vol = vol.max(MIN_VOL).min(MAX_VOL);
    }
    
    Err("Failed to converge".to_string())
}
```

## Implementation Optimization

### 1. Memory Layout Optimization

#### Struct Alignment
```rust
#[repr(C)]
pub struct OptionData {
    pub spot: f64,      // 8 bytes
    pub strike: f64,    // 8 bytes
    pub time: f64,      // 8 bytes
    pub rate: f64,      // 8 bytes
    pub vol: f64,       // 8 bytes
    pub is_call: bool,  // 1 byte + 7 padding
    // Total: 48 bytes (cache line friendly)
}
```

### 2. Compiler-Driven Vectorization

Instead of explicit SIMD, we rely on compiler auto-vectorization through loop unrolling:
```rust
// Compiler-friendly pattern for auto-vectorization
pub fn process_batch_vectorizable(data: &[f64], output: &mut [f64]) {
    // 4-element unrolling helps compiler recognize vectorization opportunity
    let chunks = data.len() / 4;
    
    for i in 0..chunks {
        let idx = i * 4;
        // Compiler can vectorize these independent operations
        output[idx] = compute(data[idx]);
        output[idx + 1] = compute(data[idx + 1]);
        output[idx + 2] = compute(data[idx + 2]);
        output[idx + 3] = compute(data[idx + 3]);
    }
    
    // Handle remainder
    for i in (chunks * 4)..data.len() {
        output[i] = compute(data[i]);
    }
}
```

### 3. Parallel Processing

Using Rayon for automatic parallelization:
```rust
use rayon::prelude::*;

pub fn calculate_portfolio_risk(options: &[OptionData]) -> PortfolioRisk {
    let results: Vec<Greeks> = options
        .par_iter()
        .map(|opt| calculate_greeks(opt))
        .collect();
    
    aggregate_risk(results)
}
```

## System-Level Optimization

### 1. Zero-Copy Data Transfer

PyO3 integration with NumPy arrays:
```rust
#[pyfunction]
pub fn process_array(py: Python, arr: &PyArray1<f64>) -> PyResult<Py<PyArray1<f64>>> {
    let data = unsafe { arr.as_slice()? };
    let result = process_data_zero_copy(data);
    Ok(PyArray1::from_vec(py, result).to_owned())
}
```

### 2. Cache Optimization

#### Prefetching
```rust
use std::intrinsics::prefetch_read_data;

pub fn process_large_dataset(data: &[f64]) {
    for i in 0..data.len() {
        // Prefetch next cache line
        if i + 8 < data.len() {
            unsafe {
                prefetch_read_data(&data[i + 8], 3);
            }
        }
        // Process current element
        process_element(data[i]);
    }
}
```

### 3. Branch Prediction Optimization

```rust
// Avoid unpredictable branches
pub fn option_payoff_branchless(s: f64, k: f64, is_call: bool) -> f64 {
    let intrinsic = s - k;
    let call_payoff = intrinsic.max(0.0);
    let put_payoff = (-intrinsic).max(0.0);
    
    // Branchless selection
    is_call as i32 as f64 * call_payoff + 
    (!is_call) as i32 as f64 * put_payoff
}
```

## Profiling and Benchmarking

### 1. Using Criterion.rs
```rust
use criterion::{criterion_group, criterion_main, Criterion};

fn benchmark_black_scholes(c: &mut Criterion) {
    c.bench_function("black_scholes single", |b| {
        b.iter(|| black_scholes(100.0, 100.0, 1.0, 0.05, 0.2, true))
    });
}

criterion_group!(benches, benchmark_black_scholes);
criterion_main!(benches);
```

### 2. Flame Graphs
```bash
# Generate flame graph
cargo flamegraph --bin quantforge-bench
```

### 3. Performance Monitoring
```python
import quantforge as qf
import time

# Enable performance stats
qf.enable_performance_stats()

# Run calculations
results = qf.black_scholes_batch(spots, strikes, times, rates, vols)

# Get performance metrics
stats = qf.get_performance_stats()
print(f"Throughput: {stats['ops_per_second']:.0f} ops/sec")
print(f"Latency: {stats['avg_latency_us']:.2f} μs")
```

## Best Practices

### 1. Data Layout
- Use Structure of Arrays (SoA) for vectorization
- Align data to cache line boundaries
- Minimize pointer chasing

### 2. Algorithm Selection
- Choose algorithms based on input characteristics
- Use lookup tables for frequently accessed values
- Implement multiple algorithms with runtime selection

### 3. Error Handling
- Use Result types for recoverable errors
- Avoid panics in hot paths
- Batch validation for better performance

## Future Optimizations

### Planned Improvements
1. **GPU Acceleration**: CUDA/OpenCL for massive parallelism
2. **AVX-512 Support**: For newer Intel processors
3. **Custom Memory Allocator**: For reduced allocation overhead
4. **JIT Compilation**: For dynamic optimization

### Experimental Features
- WebAssembly target for browser deployment
- Distributed computing support
- Hardware-specific optimizations

## References

- [Intel Optimization Manual](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
- [Rust Performance Book](https://nnethercote.github.io/perf-book/)
- [Agner Fog's Optimization Resources](https://www.agner.org/optimize/)