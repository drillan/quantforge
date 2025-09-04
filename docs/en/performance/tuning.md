# Performance Tuning

Detailed tuning guide according to environment and workload.

```{warning}
The advanced performance tuning features described on this page (strategy selection, CPU-specific optimization, NUMA settings, etc.) are planned for future implementation.
Currently, QuantForge performs optimizations automatically internally.
```

## Environment-Specific Tuning

### Linux

```{code-block} bash
:name: tuning-code-cpu
:caption: CPU Governor Settings

# CPU Governor Settings
sudo cpupower frequency-set -g performance

# Enable Huge Pages
echo 1024 | sudo tee /proc/sys/vm/nr_hugepages

# NUMA Optimization
numactl --cpunodebind=0 --membind=0 python script.py
```

### macOS

```{code-block} bash
:name: tuning-code-apple-silicon
:caption: Apple Silicon Optimization

# Apple Silicon Optimization
export CARGO_BUILD_TARGET=aarch64-apple-darwin

# Avoid Rosetta (Native Execution)
arch -arm64 python script.py
```

### Windows

```{code-block} powershell
:name: tuning-code-power-plan
:caption: Power Plan

# Power Plan
powercfg /setactive SCHEME_MIN

# Process Priority
Start-Process python.exe -Priority High
```

## Batch Size Optimization

### Parallel Processing Thresholds

Current threshold values (future adjustable):

| Constant | Current Value | Purpose |
|----------|--------------|---------|
| `PARALLEL_THRESHOLD_SMALL` | 1,000 | Threshold for parallel processing of small data |
| `PARALLEL_THRESHOLD_MEDIUM` | 10,000 | Threshold for switching parallel strategy |
| `PARALLEL_THRESHOLD_LARGE` | 100,000 | Threshold for large-scale processing |

### Batch Size Guidelines

| Calculation Type | Recommended Batch Size | Reason |
|-----------------|------------------------|---------|
| Real-time | 1-100 | Minimize latency |
| Interactive | 100-1,000 | Balance responsiveness and efficiency |
| Batch processing | 10,000-100,000 | Maximize throughput |
| Backtesting | 1,000,000+ | Utilize full parallelization |

## Memory Optimization

### Pre-allocation Strategy

```python
import numpy as np
from quantforge.models import black_scholes

# Pre-allocate memory
n = 1_000_000
spots = np.empty(n, dtype=np.float64)
results = np.empty(n, dtype=np.float64)

# Reuse allocated memory
for batch in data_batches:
    spots[:len(batch)] = batch
    results[:len(batch)] = black_scholes.call_price_batch(
        spots=spots[:len(batch)],
        strike=100.0,
        time=1.0,
        rate=0.05,
        sigma=0.2
    )
```

### Memory Pool Usage

```python
# Use memory pool for repeated allocations
import gc

# Disable GC during calculation
gc.disable()
try:
    # Intensive calculations
    for _ in range(1000):
        prices = black_scholes.call_price_batch(...)
finally:
    gc.enable()
    gc.collect()
```

## CPU Architecture Specific Optimization

### x86_64 (Intel/AMD)

```bash
# Check CPU features
lscpu | grep -E "avx|sse"

# Build with specific features
RUSTFLAGS="-C target-cpu=native" pip install quantforge
```

### ARM (Apple Silicon/AWS Graviton)

```bash
# Neon SIMD optimization
export RUSTFLAGS="-C target-feature=+neon"

# Build for ARM
cargo build --release --target aarch64-apple-darwin
```

## Parallel Processing Control

### Thread Count Adjustment

```python
import os

# Set Rayon thread count
os.environ['RAYON_NUM_THREADS'] = '8'

# Or use system CPU count
os.environ['RAYON_NUM_THREADS'] = str(os.cpu_count())
```

### NUMA Awareness

```bash
# Bind to specific NUMA node
numactl --cpunodebind=0 --membind=0 python your_script.py

# Check NUMA topology
numactl --hardware
```

## Profiling and Measurement

### Performance Profiling

```bash
# Python profiling
python -m cProfile -o profile.out your_script.py
python -m pstats profile.out

# Flamegraph generation
py-spy record -o profile.svg -- python your_script.py
```

### Bottleneck Identification

```python
import time
import contextlib

@contextlib.contextmanager
def timer(name):
    start = time.perf_counter()
    yield
    end = time.perf_counter()
    print(f"{name}: {(end - start) * 1000:.2f}ms")

# Usage
with timer("Price calculation"):
    prices = black_scholes.call_price_batch(...)

with timer("Greeks calculation"):
    greeks = black_scholes.greeks_batch(...)
```

## Production Deployment

### Container Optimization

```dockerfile
# Dockerfile
FROM python:3.12-slim

# Install with optimization
RUN RUSTFLAGS="-C target-cpu=native" pip install quantforge

# Set thread count
ENV RAYON_NUM_THREADS=4
```

### Kubernetes Configuration

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: quantforge-app
        resources:
          requests:
            memory: "1Gi"
            cpu: "2"
          limits:
            memory: "4Gi"
            cpu: "4"
        env:
        - name: RAYON_NUM_THREADS
          value: "4"
```

## Benchmarking Best Practices

### Warm-up Runs

```python
# Warm up cache and JIT
for _ in range(10):
    _ = black_scholes.call_price(
        spot=100.0, strike=100.0, time=1.0, rate=0.05, sigma=0.2
    )

# Actual measurement
import timeit
result = timeit.timeit(
    lambda: black_scholes.call_price_batch(spots, 100.0, 1.0, 0.05, 0.2),
    number=100
)
```

### Statistical Measurement

```python
import numpy as np

# Multiple measurements
times = []
for _ in range(100):
    start = time.perf_counter()
    result = black_scholes.call_price_batch(...)
    times.append(time.perf_counter() - start)

# Statistical analysis
print(f"Mean: {np.mean(times):.3f}s")
print(f"Std: {np.std(times):.3f}s")
print(f"Min: {np.min(times):.3f}s")
print(f"Max: {np.max(times):.3f}s")
print(f"Median: {np.median(times):.3f}s")
```

## Troubleshooting

### Performance Degradation

1. **Check CPU throttling**
   ```bash
   # Linux
   cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
   
   # Should show "performance"
   ```

2. **Check memory pressure**
   ```bash
   free -h
   vmstat 1
   ```

3. **Check background processes**
   ```bash
   top -H
   htop
   ```

### Unexpected Slowness

- Verify release build: `pip show quantforge`
- Check Python version: `python --version` (3.10+ recommended)
- Confirm NumPy uses BLAS: `np.show_config()`
- Test with simple benchmark first

## Future Optimization Plans

The following features are planned for implementation:

1. **Strategy Selection API**: Choose parallel strategy based on data characteristics
2. **GPU Acceleration**: CUDA/ROCm support for massive parallel calculations
3. **Custom Memory Allocators**: Specialized allocators for specific workloads
4. **JIT Compilation**: Runtime optimization for hot paths
5. **Vector Instructions**: Explicit SIMD usage for critical loops