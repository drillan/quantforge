# Batch API Migration Status

## Phase 1: Documentation (COMPLETED)
✅ Created comprehensive batch processing documentation
✅ Updated all Python API documentation
✅ Updated README files (both English and Japanese)
✅ Updated internal documentation and templates

## Phase 2: Deletion of Old Implementation (IN PROGRESS)

### Rust Core (COMPLETED)
✅ Removed batch functions from:
- `src/models/black_scholes_model.rs`
- `src/models/black76/mod.rs`
- `src/models/black76/pricing.rs`
- `src/models/black76/implied_volatility.rs`
- `src/models/merton/mod.rs`
- `src/models/merton/pricing.rs`
- `src/models/merton/implied_volatility.rs`
- `src/models/american/mod.rs`
- `src/models/american/batch.rs`

### PyO3 Bindings (NEEDS COMPLETION)
The following functions need to be removed from `src/python_modules.rs`:
- `bs_call_price_batch`, `bs_put_price_batch`
- `bs_implied_volatility_batch`, `bs_greeks_batch`
- `b76_call_price_batch`, `b76_put_price_batch`
- `b76_implied_volatility_batch`, `b76_greeks_batch`
- `merton_call_price_batch`, `merton_put_price_batch`
- `merton_call_price_batch_q`, `merton_put_price_batch_q`
- `merton_implied_volatility_batch`, `merton_greeks_batch`
- `american_call_price_batch`, `american_put_price_batch`
- `american_implied_volatility_batch`, `american_greeks_batch`
- `american_exercise_boundary_batch`

And their module exports need to be removed from the module definitions.

## Phase 3: New Implementation (TODO)

### Core Requirements
1. **Full Array Support**: All parameters accept arrays or scalars
2. **Broadcasting**: NumPy-style automatic expansion of scalars and length-1 arrays
3. **Dict Return for Greeks**: Return `Dict[str, np.ndarray]` instead of `List[PyGreeks]`
4. **Performance**: Target 20x speedup over loop implementation

### Implementation Structure

```rust
// Core broadcast module
mod broadcast {
    pub fn broadcast_arrays(arrays: Vec<&[f64]>) -> Result<Vec<Vec<f64>>, QuantForgeError>
    pub fn calculate_output_size(lengths: &[usize]) -> Result<usize, QuantForgeError>
}

// Example Black-Scholes implementation
pub fn call_price_batch(
    spots: &[f64],
    strikes: &[f64],
    times: &[f64],
    rates: &[f64],
    sigmas: &[f64]
) -> Result<Vec<f64>, QuantForgeError>
```

### PyO3 Binding Pattern

```rust
#[pyfunction]
fn call_price_batch<'py>(
    py: Python<'py>,
    spots: PyArrayLike1<f64>,    // Accepts array or scalar
    strikes: PyArrayLike1<f64>,
    times: PyArrayLike1<f64>,
    rates: PyArrayLike1<f64>,
    sigmas: PyArrayLike1<f64>,
) -> PyResult<Bound<'py, PyArray1<f64>>>
```

## Phase 4: Testing (TODO)
- Update `tests/test_batch_processing.py`
- Add broadcasting tests
- Add performance benchmarks
- Test edge cases (empty arrays, different lengths)

## Next Steps
1. Complete PyO3 binding removal
2. Implement broadcast module
3. Implement new batch functions with full array support
4. Update Python module bindings
5. Update and run tests
6. Performance validation