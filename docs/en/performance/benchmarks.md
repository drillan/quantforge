# Benchmark Results

Detailed performance measurement results for QuantForge.

## Data Management Policy

Benchmark results are managed as structured data:
- **Historical Data**: `benchmarks/results/history.jsonl` (JSON Lines format)
- **Latest Results**: `benchmarks/results/latest.json`
- **CSV Output**: `benchmarks/results/history.csv` (for analysis)

## Latest Measurement Results (2025-08-28)

### Test Environment
- **CPU**: AMD Ryzen 5 5600G (6 cores/12 threads)
- **Memory**: 29.3 GB
- **OS**: Linux 6.12 (Pop!_OS 22.04) - CUI mode (multi-user.target)
- **Python**: 3.12.5
- **Measurement Method**: Measured in CUI mode without GUI overhead

### Implied Volatility Benchmark (Latest)

#### Single IV Calculation
| Implementation | Actual Time | vs Fastest(QF) | vs Slowest(Brentq) |
|----------------|-------------|----------------|-------------------|
| **QuantForge** (Rust + PyO3) | 1.5 μs | - | 472x faster |
| **Pure Python** (Newton-Raphson + math) | 32.9 μs | 22x slower | 22x faster |
| **NumPy+SciPy** (optimize.brentq) | 707.3 μs | 472x slower | - |

#### Batch Processing (10,000 items)
| Implementation | Actual Time | Throughput | vs Fastest(QF) | vs Slowest |
|----------------|-------------|------------|----------------|------------|
| **QuantForge** (Parallel) | 19.87 ms | 503K ops/sec | - | 346x faster |
| **NumPy+SciPy** (Vectorized) | 120 ms | 83K ops/sec | 6x slower | 57x faster |
| **Pure Python** (for loop) | 6,865 ms | 1.5K ops/sec | 346x slower | - |

### Practical Scenario Benchmarks

#### Volatility Surface Construction
Building volatility smile curves that are important for options trading. Calculating implied volatility from market prices to form a 3D surface.

**Note**: Vectorized NumPy+SciPy implementation shows different characteristics depending on data size.
- Small scale (100 points): QuantForge is fastest (less parallelization overhead)
- Large scale (10,000 points): NumPy+SciPy is fastest (maximized vectorization efficiency)

##### Small Scale (10×10 grid = 100 points) - 3 Implementation Comparison
| Implementation | Actual Time | vs Fastest(QF) | vs Slowest(Python) |
|----------------|-------------|----------------|-------------------|
| **QuantForge** (Parallel) | 0.1 ms | - | 55x faster |
| **NumPy+SciPy** (Vectorized) | 0.4 ms | 4x slower | 14x faster |
| **Pure Python** (for loop) | 5.5 ms | 55x slower | - |

##### Large Scale (100×100 grid = 10,000 points)
| Implementation | Actual Time | vs Fastest(NumPy) | vs QuantForge |
|----------------|-------------|-------------------|---------------|
| **NumPy+SciPy** (Vectorized) | 2.3 ms | - | 2.8x faster |
| **QuantForge** (Parallel) | 6.5 ms | 2.8x slower | - |
| **Pure Python** (for loop, estimated) | ~550 ms | 239x slower | 85x slower |

#### Portfolio Risk Calculation
Risk management for large option portfolios. Calculating Greeks (Delta, Gamma, Vega, Theta, Rho) for each option to quantify market risk.

##### Small Scale (100 options) - 3 Implementation Comparison
| Implementation | Actual Time | vs Fastest(QF) | vs Slowest(Python) |
|----------------|-------------|----------------|-------------------|
| **QuantForge** (Batch) | 0.03 ms | - | 23x faster |
| **NumPy+SciPy** (Vectorized) | 0.5 ms | 17x slower | 1.4x faster |
| **Pure Python** (for loop) | 0.7 ms | 23x slower | - |

##### Large Scale (10,000 options)
| Implementation | Actual Time | vs Fastest(QF) | vs NumPy+SciPy |
|----------------|-------------|----------------|----------------|
| **QuantForge** (Parallel) | 1.9 ms | - | 1.4x faster |
| **NumPy+SciPy** (Vectorized) | 2.7 ms | 1.4x slower | - |
| **Pure Python** (for loop, estimated) | ~70 ms | 37x slower | 26x slower |

### Black-Scholes Call Option Pricing

#### Single Calculation
| Implementation | Actual Time | vs Fastest(QF) | vs Slowest(NumPy+SciPy) |
|----------------|-------------|----------------|------------------------|
| **QuantForge** (Rust + PyO3) | 1.40 μs | - | 55.6x faster |
| **Pure Python** (math.erf) | 2.37 μs | 1.7x slower | 32.8x faster |
| **NumPy+SciPy** (stats.norm.cdf) | 77.74 μs | 55.6x slower | - |

## Performance Comparison Summary

QuantForge consistently outperforms traditional Python implementations:
- **Single calculations**: 50-500x faster than NumPy+SciPy
- **Batch processing**: Maintains high performance with parallel processing
- **Memory efficiency**: Zero-copy data transfer via PyO3

For detailed optimization techniques, see [Optimization Guide](optimization.md).