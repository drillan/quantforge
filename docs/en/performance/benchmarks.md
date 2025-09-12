# Benchmark Results

Detailed performance measurement results for QuantForge. Data is automatically updated.

:::{note}
**Latest optimizations achieved 43% performance improvement:**
- Micro-batch optimization (100-1000 elements) provides significant improvement for small batches
- Fast erf approximation makes norm_cdf calculations 2-3x faster
:::

## Data Management Policy

Benchmark results are managed as structured data:
- **Historical Data**: `benchmark_results/history.jsonl` (JSON Lines format)
- **Latest Results**: `benchmark_results/latest.json`
- **Display CSVs**: `docs/en/_static/benchmark_data/*.csv` (auto-generated)

## Test Environment

```{csv-table}
:file: ../_static/benchmark_data/environment.csv
:header-rows: 1
:widths: 30, 70
```

## Black-Scholes Call Option Pricing

### Single Calculation

Single execution performance of Black-Scholes call option pricing:

```{csv-table}
:file: ../_static/benchmark_data/single_calculation.csv
:header-rows: 1
:widths: 30, 20, 25, 25
```

### Batch Processing Performance

#### Small Batch (100 items)

```{csv-table}
:file: ../_static/benchmark_data/batch_100.csv
:header-rows: 1
:widths: 25, 25, 30, 20
```

#### Medium Batch (1,000 items)

```{csv-table}
:file: ../_static/benchmark_data/batch_1000.csv
:header-rows: 1
:widths: 25, 25, 30, 20
```

#### Large Batch (10,000 items)

```{csv-table}
:file: ../_static/benchmark_data/batch_10000.csv
:header-rows: 1
:widths: 25, 25, 30, 20
```

## Performance Analysis

### Relative Performance

```{csv-table}
:file: ../_static/benchmark_data/relative_performance.csv
:header-rows: 1
:widths: 20, 20, 20, 20, 20
```

### Throughput

Calculations per second by data size:

```{csv-table}
:file: ../_static/benchmark_data/throughput.csv
:header-rows: 1
:widths: 20, 20, 20, 20, 20
```

## Optimization Impact

### Micro-batch Optimization Effect

| Data Size | Previous | Optimized | Improvement |
|-----------|----------|-----------|-------------|
| 100 | 6.1M ops/sec | 8.8M ops/sec | +44% |
| 500 | 10.2M ops/sec | 14.7M ops/sec | +44% |
| 1,000 | 8.5M ops/sec | 12.3M ops/sec | +45% |

4-element loop unrolling promotes compiler auto-vectorization, achieving significant performance gains for small batches.

## Greeks Calculation

### Greeks Batch (1,000 items)

```{csv-table}
:file: ../_static/benchmark_data/greeks_batch_1000.csv
:header-rows: 1
:widths: 30, 25, 25, 20
```

## Update Method

### Automatic Benchmark Execution

```bash
# Run benchmarks
pytest tests/performance/ -m benchmark

# Generate reports
python tests/performance/generate_benchmark_report.py
```

### Continuous Integration

Benchmark tests run automatically on every push.
Results are automatically saved in JSON format.

## Detailed Metrics

### Statistical Information

Each benchmark includes the following metrics:
- **min**: Minimum execution time
- **max**: Maximum execution time
- **mean**: Average execution time
- **stddev**: Standard deviation
- **rounds**: Number of measurement rounds
- **iterations**: Iterations per round

### Outlier Detection

Outliers are automatically detected and excluded from statistics.
This ensures stable benchmark results.

## Historical Trend

Historical benchmark data is recorded in:
- `benchmark_results/history.jsonl` (all measurement history)
- Latest visualization through dashboard

## Implied Volatility Calculation

### Fair Comparison with Newton-Raphson Method

Implied volatility (IV) calculation is a critical computation that extracts the volatility implied by option prices. QuantForge implements a high-performance Newton-Raphson solver.

:::{note}
**Unified conditions for fair benchmarking**:
- All implementations use the same algorithm (Newton-Raphson method)
- Same parameters (tolerance: 1e-6, max_iterations: 100)
- Pure comparison of implementation technologies (Rust vs Python vs NumPy)
:::

### Performance Comparison with Newton-Raphson

```{csv-table}
:file: ../_static/benchmark_data/implied_volatility_newton.csv
:header-rows: 1
:widths: 20, 20, 20, 20, 10, 10
```

### Key Achievements

- **10,000 item batch processing**: **170x** faster than Pure Python
- **Parallelization effect**: Automatic Rayon parallelization excels with large datasets
- **Zero-copy design**: Memory-efficient implementation with PyO3

### Algorithm Characteristics Comparison (Reference)

```{csv-table}
:file: ../_static/benchmark_data/implied_volatility_algorithm_comparison.csv
:header-rows: 1
:widths: 15, 20, 15, 10, 10, 10, 20
```

:::{note}
**About Brent's Method**:
- Implementation using scipy.optimize.brentq prioritizes robustness
- 10-15x slower than Newton-Raphson but guarantees convergence
- Suitable for special cases or when high precision is required
:::

### IV Calculation Optimization Points

1. **Improved Initial Value Estimation**
   - Appropriate initial values using Manaster-Koehler approximation
   - Faster convergence near ATM

2. **Vectorized Processing**
   - Batch processing of NumPy arrays
   - Minimized conditional branching

3. **Parallelization Strategy**
   - Automatic Rayon parallelization for 30,000+ elements
   - Balance between overhead and parallelization benefits

## Notes

- Measurements are performed in release mode (optimized build)
- Cache warming is implemented to ensure stable measurement
- Parallelization is automatically optimized by Rayon