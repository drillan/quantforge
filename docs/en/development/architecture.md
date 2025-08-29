# System Architecture

The internal design and implementation details of QuantForge.

## Overall Structure

```{mermaid}
graph TB
    subgraph "Python Layer"
        PY[Python API]
        NP[NumPy Interface]
    end
    
    subgraph "Binding Layer"
        PYO3[PyO3 Bindings]
        MAT[Maturin Build]
    end
    
    subgraph "Rust Core"
        MODELS[Price Models]
        PARALLEL[Parallel Executor]
        MATH[Math Functions]
    end
    
    subgraph "Hardware"
        CPU[CPU]
        CACHE[Cache]
    end
    
    PY --> PYO3
    NP --> PYO3
    PYO3 --> MODELS
    MODELS --> PARALLEL
    MODELS --> MATH
    PARALLEL --> CPU
    MATH --> CACHE
```

## Component Design

### Python API Layer

```python
# quantforge/__init__.py
class QuantForgeAPI:
    """Python user interface"""
    
    def __init__(self):
        self._rust_core = _quantforge_rust
        self._config = Config()
    
    def calculate(self, spots, strikes, rate, vol, time, **kwargs):
        # Input validation
        validated = self._validate_inputs(spots, strikes, rate, vol, time)
        
        # Rust function call
        return self._rust_core.calculate_batch(validated)
```

### Rust Core Layer

```rust
// src/lib.rs
pub struct QuantForgeCore {
    parallel_executor: ParallelExecutor,
    memory_pool: MemoryPool,
}

impl QuantForgeCore {
    pub fn calculate(&self, params: &CalculationParams) -> Result<Vec<f64>> {
        // Strategy selection
        let strategy = self.select_strategy(params.size());
        
        match strategy {
            Strategy::Sequential => self.calculate_sequential(params),
            Strategy::Parallel => self.parallel_executor.calculate(params),
            Strategy::Hybrid => self.calculate_hybrid(params),
        }
    }
}
```

## Memory Layout

### data structure

```rust
#[repr(C)]
pub struct OptionData {
    spot: f64,
    strike: f64,
    rate: f64,
    vol: f64,
    time: f64,
}

// Memory alignment
#[repr(align(64))]
pub struct AlignedBuffer {
    data: Vec<f64>,
}
```

### Zero-copy design

```rust
use numpy::PyReadonlyArray1;

#[pyfunction]
fn calculate_zero_copy(
    spots: PyReadonlyArray1<f64>,
) -> PyResult<Py<PyArray1<f64>>> {
    // Direct reference to NumPy array (no copy)
    let spots_slice = spots.as_slice()?;
    
    // Processing
    let results = process(spots_slice);
    
    // Return results with zero copy
    Python::with_gil(|py| {
        Ok(PyArray1::from_vec(py, results).to_owned())
    })
}
```

## Parallel Processing Architecture

### Hierarchical Parallelization

```rust
pub enum ParallelStrategy {
    
    // Level 2: Threads (task-level parallelism)
    ThreadPool {
        num_threads: usize,
        chunk_size: usize,
    },
    
    // Level 3: Hybrid (multi-level parallelization)
    Hybrid {
        num_threads: usize,
        chunk_strategy: String,
    },
}
```

### work stealing

```rust
use rayon::prelude::*;

pub fn parallel_calculate(data: &[f64]) -> Vec<f64> {
    data.par_chunks(1000)
        .flat_map(|chunk| {
            // Process each chunk
            process(chunk)
        })
        .collect()
}
```

## Error Handling

### type-safe error

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum QuantForgeError {
    #[error("Invalid spot price: {0}")]
    InvalidSpot(f64),
    
    #[error("Convergence failed after {0} iterations")]
    ConvergenceFailed(usize),
    
}

// Result type alias
pub type Result<T> = std::result::Result<T, QuantForgeError>;
```

## Optimization Pipeline

### Compile-time optimization

```rust
// Constant folding
const SQRT_2PI: f64 = 2.5066282746310007;

// Inline expansion
#[inline(always)]
fn fast_exp(x: f64) -> f64 {
    // Optimization using Taylor expansion
    if x.abs() < 0.5 {
        1.0 + x + x * x / 2.0 + x * x * x / 6.0
    } else {
        x.exp()
    }
}
```

### Run-time Optimization

```rust
// Dynamic detection of CPU features
fn select_implementation() -> fn(&[f64]) -> Vec<f64> {
    if is_x86_feature_detected!("avx512f") {
        calculate_avx512
    } else if is_x86_feature_detected!("avx2") {
        calculate_avx2
    } else {
        calculate_scalar
    }
}
```

## Test Architecture

### Multi-Layer Test Strategy

```rust
#[cfg(test)]
mod tests {
    // Unit tests
    #[test]
    fn test_black_scholes() { ... }
    
    // Integration tests
    #[test]
    fn test_python_binding() { ... }
    
    // Property-based tests
    #[quickcheck]
    fn prop_put_call_parity(s: f64, k: f64) -> bool { ... }
    
    // Benchmarks
    #[bench]
    fn bench_million_options(b: &mut Bencher) { ... }
}
```

## Build System

### Cargo.toml

```toml
[package]
name = "quantforge"
version = "0.1.0"

[lib]
name = "quantforge"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.20", features = ["extension-module"] }
numpy = "0.20"
rayon = "1.7"

[profile.release]
lto = true
codegen-units = 1
opt-level = 3
```

### pyproject.toml

```toml
[build-system]
requires = ["maturin>=1.0"]
build-backend = "maturin"

[tool.maturin]
features = ["pyo3/extension-module"]
python-source = "python"
```

## Deployment Architecture

### Multiplatform

```yaml
# .github/workflows/build.yml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python: ["3.12"]
    
steps:
  - uses: actions/setup-python@v4
  - uses: dtolnay/rust-toolchain@stable
  - run: pip install maturin
  - run: maturin build --release
```

## Security Considerations

### Memory Safety

- Guarantee provided by Rust's ownership system
- Minimizing the `unsafe` block
- Verification by Miri

### Input Validation

```rust
fn validate_inputs(spot: f64, strike: f64) -> Result<()> {
    if !spot.is_finite() || spot <= 0.0 {
        return Err(QuantForgeError::InvalidSpot(spot));
    }
    if !strike.is_finite() || strike <= 0.0 {
        return Err(QuantForgeError::InvalidStrike(strike));
    }
    Ok(())
}
```

## Summary

QuantForge's architecture consists of:
- **Hierarchical Design**: Each layer has distinct responsibilities
- **Zero-Cost Abstractions**: Leverage Rust's strengths
- **Adaptive Optimization**: Selects optimal strategies during runtime
- **Type Safety**: Prevents errors at compile time
