# Benchmark Results

Detailed performance measurement results for QuantForge. Data is automatically updated.

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

## Notes

- Measurements are performed in release mode (optimized build)
- Cache warming is implemented to ensure stable measurement
- Parallelization is automatically optimized by Rayon