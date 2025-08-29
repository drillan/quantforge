# Performance Tuning Guide

Guide for optimizing QuantForge performance in production environments.

## System Requirements

### Minimum Requirements
- **CPU**: x86_64 with SSE2 support
- **Memory**: 4GB RAM
- **OS**: Linux/macOS/Windows (64-bit)
- **Python**: 3.8+

### Recommended Requirements
- **CPU**: Modern x86_64 with AVX2 support (Intel Haswell+ or AMD Zen+)
- **Memory**: 16GB+ RAM for large portfolios
- **OS**: Linux for best performance
- **Python**: 3.10+ with NumPy 1.20+

## Installation Optimization

### 1. Compiler Optimization

Install from source with native CPU optimizations:
```bash
# Clone repository
git clone https://github.com/quantforge/quantforge.git
cd quantforge

# Build with native optimizations
RUSTFLAGS="-C target-cpu=native" pip install .
```

### 2. Pre-built Wheels

For production, use optimized pre-built wheels:
```bash
# Intel CPUs with AVX2
pip install quantforge[avx2]

# AMD CPUs with Zen2+
pip install quantforge[zen2]

# Generic x86_64 (fallback)
pip install quantforge
```

## Runtime Configuration

### 1. Thread Pool Configuration

```python
import quantforge as qf

# Set thread pool size (default: CPU cores)
qf.set_num_threads(8)

# Get current configuration
print(qf.get_num_threads())

# Auto-tune based on workload
qf.auto_tune_threads(sample_size=10000)
```

### 2. Memory Pool Settings

```python
# Enable memory pooling for repeated calculations
qf.enable_memory_pool(
    initial_size_mb=100,
    max_size_mb=1000,
    growth_factor=2.0
)

# Monitor memory usage
stats = qf.get_memory_stats()
print(f"Pool usage: {stats['used_mb']:.1f}/{stats['total_mb']:.1f} MB")
```

### 3. Precision Settings

```python
# Set precision mode
qf.set_precision_mode('high')  # Full f64 precision (default)
qf.set_precision_mode('fast')  # Mixed precision where safe
qf.set_precision_mode('ultra')  # Extended precision for edge cases

# Configure tolerances
qf.set_convergence_tolerance(1e-10)  # For iterative methods
qf.set_numerical_tolerance(1e-15)    # For comparisons
```

## Workload-Specific Tuning

### 1. Real-time Trading

For low-latency applications:
```python
# Minimize latency configuration
qf.configure_realtime(
    thread_priority='high',
    cpu_affinity=[0, 1],  # Pin to specific cores
    disable_gc=True,       # Disable Python GC during critical sections
    preallocate_memory=True
)

# Warm up the JIT and caches
qf.warmup(iterations=1000)

# Use low-latency API
price = qf.black_scholes_fast(s, k, t, r, sigma)  # Single precision
```

### 2. Batch Processing

For high-throughput scenarios:
```python
# Configure for batch processing
qf.configure_batch(
    chunk_size=10000,
    parallel_threshold=1000,  # Use parallel processing above this size
    memory_prefetch=True
)

# Process large dataset
results = qf.black_scholes_batch(
    data,
    progress_callback=lambda x: print(f"Progress: {x:.1%}")
)
```

### 3. Risk Analytics

For portfolio-wide calculations:
```python
# Configure for analytics
qf.configure_analytics(
    cache_greeks=True,        # Cache intermediate results
    aggregate_parallel=True,  # Parallel aggregation
    use_approximations=False  # Full precision for risk
)

# Calculate portfolio metrics
portfolio_risk = qf.calculate_portfolio_risk(
    positions,
    market_data,
    correlation_matrix=corr_matrix
)
```

## Platform-Specific Optimization

### Linux

```bash
# Disable CPU frequency scaling
sudo cpupower frequency-set -g performance

# Set CPU governor
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Increase file descriptor limits
ulimit -n 65536

# Disable NUMA balancing for dedicated servers
echo 0 | sudo tee /proc/sys/kernel/numa_balancing
```

### macOS

```bash
# Disable App Nap
defaults write NSGlobalDomain NSAppSleepDisabled -bool YES

# Increase memory limits
sudo launchctl limit maxfiles 65536 200000
```

### Windows

```powershell
# Set high performance power plan
powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c

# Disable CPU throttling
powercfg -setacvalueindex scheme_current sub_processor PROCTHROTTLEMAX 100
```

## Monitoring and Profiling

### 1. Built-in Profiler

```python
# Enable profiling
qf.enable_profiler()

# Run calculations
results = perform_calculations()

# Get profile report
profile = qf.get_profile_report()
print(profile.to_string(sort_by='time'))

# Export to file
profile.to_csv('profile_results.csv')
```

### 2. Performance Metrics

```python
# Enable metrics collection
qf.enable_metrics()

# After calculations
metrics = qf.get_metrics()
print(f"""
Performance Metrics:
- Total operations: {metrics['total_ops']:,}
- Throughput: {metrics['ops_per_second']:,.0f} ops/sec
- Average latency: {metrics['avg_latency_us']:.2f} μs
- P99 latency: {metrics['p99_latency_us']:.2f} μs
- Cache hit rate: {metrics['cache_hit_rate']:.1%}
""")
```

### 3. Memory Profiling

```python
# Track memory usage
qf.enable_memory_tracking()

# Run calculations
results = process_large_dataset()

# Get memory report
mem_report = qf.get_memory_report()
print(f"""
Memory Usage:
- Peak usage: {mem_report['peak_mb']:.1f} MB
- Current usage: {mem_report['current_mb']:.1f} MB
- Allocations: {mem_report['num_allocations']:,}
- Deallocations: {mem_report['num_deallocations']:,}
""")
```

## Troubleshooting Performance Issues

### Common Issues and Solutions

#### 1. Slower than Expected Performance

**Symptoms**: Performance below benchmarks
**Solutions**:
- Check CPU throttling: `cat /proc/cpuinfo | grep MHz`
- Verify thread pool size: `qf.get_num_threads()`
- Ensure optimized build: `qf.get_build_info()`

#### 2. High Memory Usage

**Symptoms**: Excessive memory consumption
**Solutions**:
```python
# Limit memory pool
qf.set_memory_limit_mb(500)

# Process in chunks
for chunk in qf.chunk_iterator(data, chunk_size=1000):
    process_chunk(chunk)

# Clear caches periodically
qf.clear_caches()
```

#### 3. Inconsistent Latency

**Symptoms**: Variable response times
**Solutions**:
```python
# Disable automatic garbage collection
import gc
gc.disable()
try:
    results = critical_calculation()
finally:
    gc.enable()

# Pin threads to cores
qf.set_cpu_affinity([0, 1, 2, 3])

# Pre-warm caches
qf.warmup(iterations=100)
```

## Best Practices

### 1. Data Preparation
- Pre-sort data when possible
- Use contiguous memory layouts
- Avoid unnecessary type conversions

### 2. API Usage
- Use batch APIs for multiple calculations
- Reuse option objects for repeated calculations
- Prefer specialized functions over generic ones

### 3. System Configuration
- Dedicate cores for QuantForge in production
- Monitor and adjust thread pool size
- Use memory pools for repeated allocations

## Advanced Tuning

### Custom Compilation Flags

```toml
# pyproject.toml
[tool.maturin]
rustc-args = [
    "-C", "target-cpu=native",
    "-C", "opt-level=3",
    "-C", "lto=fat",
    "-C", "codegen-units=1"
]
```

### Environment Variables

```bash
# Set before running Python
export QUANTFORGE_THREADS=8
export QUANTFORGE_MEMORY_POOL=1
export QUANTFORGE_SIMD=avx2
export QUANTFORGE_PRECISION=fast
```

### Configuration File

```yaml
# quantforge.yaml
performance:
  threads: 8
  memory_pool_mb: 1000
  simd_level: avx2
  precision: high
  
optimization:
  parallel_threshold: 1000
  cache_size_mb: 100
  prefetch_distance: 8
  
monitoring:
  enable_metrics: true
  enable_profiling: false
  log_level: info
```

## References

- [QuantForge Benchmarks](benchmarks.md)
- [Optimization Guide](optimization.md)
- [Installation Guide](../installation.md)