# Testing Strategy

Comprehensive testing policy and guidelines for QuantForge.

## Test Pyramid

```
         /\
        /  \  E2E Tests (5%)
       /____\
      /      \  Integration Tests (20%)
     /________\
    /          \  Unit Tests (75%)
   /____________\
```

## Unit Tests

### Rust Unit Tests

```{code-block} rust
:name: testing-code-src/models/black_scholes.rs
:caption: src/models/black_scholes.rs

// src/models/black_scholes.rs
#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;
    
    #[test]
    fn test_call_price() {
        let price = black_scholes_call(100.0, 100.0, 0.05, 0.2, 1.0);
        assert_relative_eq!(price, 10.4506, epsilon = 1e-4);
    }
    
    #[test]
    fn test_put_call_parity() {
        let spot = 100.0;
        let strike = 100.0;
        let rate = 0.05;
        let vol = 0.2;
        let time = 1.0;
        
        let call = black_scholes_call(spot, strike, rate, vol, time);
        let put = black_scholes_put(spot, strike, rate, vol, time);
        
        let parity = call - put;
        let theoretical = spot - strike * (-rate * time).exp();
        
        assert_relative_eq!(parity, theoretical, epsilon = 1e-10);
    }
}
```

### Python Unit Tests

```{code-block} python
:name: testing-code-tests/test_pricing.py
:caption: tests/test_pricing.py

# tests/test_pricing.py
import pytest
import numpy as np
import quantforge as qf
from quantforge.models import black_scholes

class TestBlackScholes:
    def test_call_price(self):
        """Test call option pricing."""
        price = black_scholes.call_price(
            spot=100.0, strike=100.0, time=1.0, rate=0.05, sigma=0.2
        )
        assert abs(price - 10.4506) < 1e-4
    
    def test_boundary_conditions(self):
        """Test extreme cases."""
        # Deep ITM
        price = black_scholes.call_price(
            spot=200.0, strike=100.0, time=1.0, rate=0.05, sigma=0.2
        )
        assert abs(price - (200 - 100 * np.exp(-0.05))) < 0.01
        
        # Deep OTM
        price = black_scholes.call_price(
            spot=50.0, strike=100.0, time=1.0, rate=0.05, sigma=0.2
        )
        assert price < 0.001
```

## Property-Based Testing

### Hypothesis (Python)

```python
from hypothesis import given, strategies as st
import quantforge as qf

@given(
    spot=st.floats(min_value=0.1, max_value=1000),
    strike=st.floats(min_value=0.1, max_value=1000),
    rate=st.floats(min_value=-0.1, max_value=0.5),
    vol=st.floats(min_value=0.01, max_value=2.0),
    time=st.floats(min_value=0.01, max_value=10.0)
)
def test_price_boundaries(spot, strike, rate, vol, time):
    """Test price stays within theoretical bounds."""
    call_price = black_scholes.call_price(
        spot=spot, strike=strike, time=time, rate=rate, sigma=vol
    )
    
    # Lower bound
    intrinsic = max(spot - strike * np.exp(-rate * time), 0)
    assert call_price >= intrinsic - 1e-10
    
    # Upper bound
    assert call_price <= spot
```

### QuickCheck (Rust)

```rust
use quickcheck::{quickcheck, TestResult};

quickcheck! {
    fn prop_monotonicity(spot1: f64, spot2: f64, strike: f64) -> TestResult {
        if spot1 <= 0.0 || spot2 <= 0.0 || strike <= 0.0 {
            return TestResult::discard();
        }
        
        let price1 = black_scholes_call(spot1, strike, 0.05, 0.2, 1.0);
        let price2 = black_scholes_call(spot2, strike, 0.05, 0.2, 1.0);
        
        // Call price increases with spot
        TestResult::from_bool(
            (spot1 <= spot2) == (price1 <= price2)
        )
    }
}
```

## Integration Tests

### Python-Rust Integration

```{code-block} python
:name: testing-code-tests/test_integration.py
:caption: tests/test_integration.py

# tests/test_integration.py
def test_numpy_integration():
    """Test NumPy array processing."""
    spots = np.random.uniform(90, 110, 10000)
    
    prices = black_scholes.call_price_batch(
        spots=spots, strike=100.0, time=1.0, rate=0.05, sigma=0.2
    )
    
    assert isinstance(prices, np.ndarray)
    assert prices.shape == spots.shape
    assert prices.dtype == np.float64
    assert all(prices >= 0)

def test_zero_copy():
    """Test zero-copy optimization."""
    data = np.random.uniform(90, 110, 1000000)
    
    # Record data memory address
    data_ptr = data.ctypes.data
    
    # Process
    result = black_scholes.call_price_batch(
        spots=data, strike=100.0, time=1.0, rate=0.05, sigma=0.2
    )
    
    # Original data unchanged
    assert data.ctypes.data == data_ptr
```

## Performance Tests

### Benchmarking

```{code-block} python
:name: testing-code-tests/test_performance.py
:caption: tests/test_performance.py

# tests/test_performance.py
import pytest
import time

class TestPerformance:
    @pytest.mark.benchmark
    def test_single_option_speed(self, benchmark):
        """Single option calculation benchmark."""
        result = benchmark(
            black_scholes.call_price,
            spot=100.0, strike=100.0, time=1.0, rate=0.05, sigma=0.2
        )
        assert result > 0
    
    @pytest.mark.benchmark
    def test_batch_processing(self, benchmark):
        """Batch processing benchmark."""
        spots = np.random.uniform(90, 110, 100000)
        
        result = benchmark(
            black_scholes.call_price_batch,
            spots=spots, strike=100.0, time=1.0, rate=0.05, sigma=0.2
        )
        
        # Performance requirements
        assert benchmark.stats['mean'] < 0.020  # < 20ms
```

### Criterion (Rust)

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn benchmark_black_scholes(c: &mut Criterion) {
    c.bench_function("black_scholes_single", |b| {
        b.iter(|| {
            black_scholes_call(
                black_box(100.0),
                black_box(100.0),
                black_box(0.05),
                black_box(0.2),
                black_box(1.0)
            )
        })
    });
    
    let mut group = c.benchmark_group("batch_sizes");
    for size in [100, 1000, 10000, 100000].iter() {
        group.bench_with_input(
            format!("size_{}", size),
            size,
            |b, &size| {
                let data = vec![100.0; size];
                b.iter(|| process_batch(&data))
            }
        );
    }
    group.finish();
}

criterion_group!(benches, benchmark_black_scholes);
criterion_main!(benches);
```

## Fuzz Testing

### cargo-fuzz

```{code-block} rust
:name: testing-code-fuzz/fuzz_targets/pricing.rs
:caption: fuzz/fuzz_targets/pricing.rs

// fuzz/fuzz_targets/pricing.rs
#![no_main]
use libfuzzer_sys::fuzz_target;
use quantforge::black_scholes_call;

fuzz_target!(|data: (f64, f64, f64, f64, f64)| {
    let (spot, strike, rate, vol, time) = data;
    
    // Restrict to valid ranges
    if spot > 0.0 && spot < 1e6 &&
       strike > 0.0 && strike < 1e6 &&
       rate > -1.0 && rate < 1.0 &&
       vol > 0.0 && vol < 10.0 &&
       time > 0.0 && time < 100.0 {
        
        let _ = black_scholes_call(spot, strike, rate, vol, time);
    }
});
```

Run:
```bash
cargo fuzz run pricing -- -max_total_time=60
```

## Regression Tests

### Golden File Tests

```{code-block} python
:name: testing-code-tests/test_regression.py
:caption: tests/test_regression.py

# tests/test_regression.py
import json
import pytest

def test_regression_black_scholes():
    """Test against known good values."""
    with open('tests/golden/black_scholes.json') as f:
        test_cases = json.load(f)
    
    for case in test_cases:
        price = black_scholes.call_price(
            spot=case['spot'],
            strike=case['strike'],
            time=case['time'],
            rate=case['rate'],
            sigma=case['vol']
        )
        
        assert abs(price - case['expected']) < 1e-10, \
            f"Regression: {case['name']}"
```

## Error Case Testing

```{code-block} python
:name: testing-code-test_invalid_inputs
:caption: test_invalid_inputs

def test_invalid_inputs():
    """Test error handling."""
    with pytest.raises(ValueError, match="Spot price must be positive"):
        black_scholes.call_price(
            spot=-100.0, strike=100.0, time=1.0, rate=0.05, sigma=0.2
        )
    
    with pytest.raises(ValueError, match="Volatility cannot be negative"):
        black_scholes.call_price(
            spot=100.0, strike=100.0, time=1.0, rate=0.05, sigma=-0.2
        )
    
    with pytest.raises(ValueError, match="Time must be positive"):
        black_scholes.call_price(
            spot=100.0, strike=100.0, time=-1.0, rate=0.05, sigma=0.2
        )

def test_numerical_stability():
    """Test numerical edge cases."""
    # Very small time
    price = black_scholes.call_price(
        spot=100.0, strike=100.0, time=1e-10, rate=0.05, sigma=0.2
    )
    assert abs(price - 0) < 1e-8
    
    # Very large volatility
    price = black_scholes.call_price(
        spot=100.0, strike=100.0, time=1.0, rate=0.05, sigma=10.0
    )
    assert price > 0 and price < 100
```

## Test Execution

### Running All Tests

```{code-block} bash
:name: testing-code-rust
:caption: Rust tests

# Rust tests
cargo test --all-features

# Python tests
pytest tests/ -v

# With coverage
pytest --cov=quantforge --cov-report=html

# Parallel execution
pytest -n auto
```

### Continuous Integration

```{code-block} yaml
:name: testing-code-.github/workflows/test.yml
:caption: .github/workflows/test.yml

# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python: ["3.12"]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Rust
      uses: dtolnay/rust-toolchain@stable
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python }}
    
    - name: Install dependencies
      run: |
        pip install uv
        uv pip install -e ".[dev]"
    
    - name: Run Rust tests
      run: cargo test --all-features
    
    - name: Run Python tests
      run: pytest tests/ --cov=quantforge
    
    - name: Run benchmarks
      run: cargo bench --no-run
```

## Test Quality Metrics

### Coverage Targets

- Unit tests: > 95%
- Integration tests: > 80%
- E2E tests: 100% critical paths

### Performance Criteria

| Test | Target Time | Actual |
|------|------------|--------|
| Unit tests | < 5s | ✅ |
| Integration tests | < 30s | ✅ |
| All tests | < 2min | ✅ |

## Summary

Key points for effective testing:

1. **Fast feedback**: Rich unit test coverage
2. **Boundary testing**: Cover edge cases
3. **Property testing**: Verify invariants
4. **Performance monitoring**: Prevent regressions
5. **Continuous execution**: Automate with CI/CD