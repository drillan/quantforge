//! Arrow-native model implementations with Python bindings

use arrow::array::Float64Array;
use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::arrow_convert::{
    numpy_to_arrow, arrow_to_numpy, arrayref_to_numpy, 
    broadcast_arrays, broadcast_to_length, find_broadcast_length
};
use crate::error::{arrow_to_py_err, ToPyErr};

// Import Arrow-native compute kernels from core
use quantforge_core::compute::black_scholes::BlackScholes;
use quantforge_core::compute::greeks::calculate_greeks;

// ============================================================================
// Black-Scholes Model
// ============================================================================

/// Calculate Black-Scholes call option price (scalar)
#[pyfunction]
#[pyo3(signature = (s, k, t, r, sigma))]
pub fn call_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // For scalar inputs, create single-element arrays
    let spots = Float64Array::from(vec![s]);
    let strikes = Float64Array::from(vec![k]);
    let times = Float64Array::from(vec![t]);
    let rates = Float64Array::from(vec![r]);
    let sigmas = Float64Array::from(vec![sigma]);
    
    // Call Arrow-native kernel
    let result = BlackScholes::call_price(&spots, &strikes, &times, &rates, &sigmas)
        .map_err(arrow_to_py_err)?;
    
    // Extract scalar result
    let arr = result.as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| pyo3::exceptions::PyTypeError::new_err("Expected Float64Array"))?;
    
    Ok(arr.value(0))
}

/// Calculate Black-Scholes put option price (scalar)
#[pyfunction]
#[pyo3(signature = (s, k, t, r, sigma))]
pub fn put_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // For scalar inputs, create single-element arrays
    let spots = Float64Array::from(vec![s]);
    let strikes = Float64Array::from(vec![k]);
    let times = Float64Array::from(vec![t]);
    let rates = Float64Array::from(vec![r]);
    let sigmas = Float64Array::from(vec![sigma]);
    
    // Call Arrow-native kernel
    let result = BlackScholes::put_price(&spots, &strikes, &times, &rates, &sigmas)
        .map_err(arrow_to_py_err)?;
    
    // Extract scalar result
    let arr = result.as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| pyo3::exceptions::PyTypeError::new_err("Expected Float64Array"))?;
    
    Ok(arr.value(0))
}

/// Calculate Black-Scholes call option price (batch)
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
pub fn call_price_batch<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    strikes: PyReadonlyArray1<f64>,
    times: PyReadonlyArray1<f64>,
    rates: PyReadonlyArray1<f64>,
    sigmas: PyReadonlyArray1<f64>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // Find broadcast length
    let arrays = vec![&spots, &strikes, &times, &rates, &sigmas];
    let target_len = find_broadcast_length(&arrays).map_err(arrow_to_py_err)?;
    
    // Broadcast all arrays to same length
    let spots_arrow = broadcast_to_length(spots, target_len).map_err(arrow_to_py_err)?;
    let strikes_arrow = broadcast_to_length(strikes, target_len).map_err(arrow_to_py_err)?;
    let times_arrow = broadcast_to_length(times, target_len).map_err(arrow_to_py_err)?;
    let rates_arrow = broadcast_to_length(rates, target_len).map_err(arrow_to_py_err)?;
    let sigmas_arrow = broadcast_to_length(sigmas, target_len).map_err(arrow_to_py_err)?;
    
    // Release GIL for computation
    let result = py.allow_threads(|| {
        BlackScholes::call_price(&spots_arrow, &strikes_arrow, &times_arrow, &rates_arrow, &sigmas_arrow)
    }).map_err(arrow_to_py_err)?;
    
    // Convert result back to NumPy
    arrayref_to_numpy(py, result)
}

/// Calculate Black-Scholes put option price (batch)
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
pub fn put_price_batch<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    strikes: PyReadonlyArray1<f64>,
    times: PyReadonlyArray1<f64>,
    rates: PyReadonlyArray1<f64>,
    sigmas: PyReadonlyArray1<f64>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // Find broadcast length
    let arrays = vec![&spots, &strikes, &times, &rates, &sigmas];
    let target_len = find_broadcast_length(&arrays).map_err(arrow_to_py_err)?;
    
    // Broadcast all arrays to same length
    let spots_arrow = broadcast_to_length(spots, target_len).map_err(arrow_to_py_err)?;
    let strikes_arrow = broadcast_to_length(strikes, target_len).map_err(arrow_to_py_err)?;
    let times_arrow = broadcast_to_length(times, target_len).map_err(arrow_to_py_err)?;
    let rates_arrow = broadcast_to_length(rates, target_len).map_err(arrow_to_py_err)?;
    let sigmas_arrow = broadcast_to_length(sigmas, target_len).map_err(arrow_to_py_err)?;
    
    // Release GIL for computation
    let result = py.allow_threads(|| {
        BlackScholes::put_price(&spots_arrow, &strikes_arrow, &times_arrow, &rates_arrow, &sigmas_arrow)
    }).map_err(arrow_to_py_err)?;
    
    // Convert result back to NumPy
    arrayref_to_numpy(py, result)
}

/// Calculate Greeks for Black-Scholes model (scalar)
#[pyfunction]
#[pyo3(signature = (s, k, t, r, sigma, is_call=true))]
pub fn greeks<'py>(
    py: Python<'py>,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    sigma: f64,
    is_call: bool,
) -> PyResult<Bound<'py, PyDict>> {
    // Create single-element arrays
    let spots = Float64Array::from(vec![s]);
    let strikes = Float64Array::from(vec![k]);
    let times = Float64Array::from(vec![t]);
    let rates = Float64Array::from(vec![r]);
    let sigmas = Float64Array::from(vec![sigma]);
    
    // Calculate all Greeks
    let greeks_struct = calculate_greeks(
        "black_scholes",
        &spots,
        &strikes,
        &times,
        &rates,
        &sigmas,
        is_call
    ).map_err(arrow_to_py_err)?;
    
    // Create Python dict with scalar values
    let dict = PyDict::new_bound(py);
    
    // Extract each Greek and convert to scalar
    for (i, field) in greeks_struct.fields().iter().enumerate() {
        let name = field.name();
        let column = greeks_struct.column(i);
        let arr = column.as_any()
            .downcast_ref::<Float64Array>()
            .ok_or_else(|| pyo3::exceptions::PyTypeError::new_err("Expected Float64Array"))?;
        dict.set_item(name, arr.value(0))?;
    }
    
    Ok(dict)
}

/// Calculate Greeks for Black-Scholes model (batch)
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, sigmas, is_call=true))]
pub fn greeks_batch<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    strikes: PyReadonlyArray1<f64>,
    times: PyReadonlyArray1<f64>,
    rates: PyReadonlyArray1<f64>,
    sigmas: PyReadonlyArray1<f64>,
    is_call: bool,
) -> PyResult<Bound<'py, PyDict>> {
    // Find broadcast length
    let arrays = vec![&spots, &strikes, &times, &rates, &sigmas];
    let target_len = find_broadcast_length(&arrays).map_err(arrow_to_py_err)?;
    
    // Broadcast all arrays to same length
    let spots_arrow = broadcast_to_length(spots, target_len).map_err(arrow_to_py_err)?;
    let strikes_arrow = broadcast_to_length(strikes, target_len).map_err(arrow_to_py_err)?;
    let times_arrow = broadcast_to_length(times, target_len).map_err(arrow_to_py_err)?;
    let rates_arrow = broadcast_to_length(rates, target_len).map_err(arrow_to_py_err)?;
    let sigmas_arrow = broadcast_to_length(sigmas, target_len).map_err(arrow_to_py_err)?;
    
    // Release GIL for computation
    let greeks_struct = py.allow_threads(|| {
        calculate_greeks(
            "black_scholes",
            &spots_arrow,
            &strikes_arrow,
            &times_arrow,
            &rates_arrow,
            &sigmas_arrow,
            is_call
        )
    }).map_err(arrow_to_py_err)?;
    
    // Create Python dict with NumPy arrays
    let dict = PyDict::new_bound(py);
    
    // Extract each Greek and convert to NumPy
    for (i, field) in greeks_struct.fields().iter().enumerate() {
        let name = field.name();
        let column = greeks_struct.column(i);
        let numpy_array = arrayref_to_numpy(py, column.clone())?;
        dict.set_item(name, numpy_array)?;
    }
    
    Ok(dict)
}

/// Calculate implied volatility (scalar)
#[pyfunction]
#[pyo3(signature = (price, s, k, t, r, is_call=true))]
pub fn implied_volatility(
    price: f64,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    is_call: bool,
) -> PyResult<f64> {
    // TODO: Implement using Newton-Raphson or Brent's method with Arrow kernels
    Err(pyo3::exceptions::PyNotImplementedError::new_err(
        "Implied volatility not yet implemented in Arrow-native version"
    ))
}

/// Calculate implied volatility (batch)
#[pyfunction]
#[pyo3(signature = (prices, spots, strikes, times, rates, is_calls))]
pub fn implied_volatility_batch<'py>(
    py: Python<'py>,
    prices: PyReadonlyArray1<f64>,
    spots: PyReadonlyArray1<f64>,
    strikes: PyReadonlyArray1<f64>,
    times: PyReadonlyArray1<f64>,
    rates: PyReadonlyArray1<f64>,
    is_calls: PyReadonlyArray1<bool>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // TODO: Implement batch implied volatility
    Err(pyo3::exceptions::PyNotImplementedError::new_err(
        "Batch implied volatility not yet implemented in Arrow-native version"
    ))
}

// ============================================================================
// Black76 Model (Futures)
// ============================================================================

/// Calculate Black76 call option price (scalar)
#[pyfunction]
#[pyo3(signature = (f, k, t, r, sigma))]
pub fn black76_call_price(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // TODO: Implement using Arrow-native Black76 kernel from core
    Err(pyo3::exceptions::PyNotImplementedError::new_err(
        "Black76 not yet implemented in Arrow-native version"
    ))
}

/// Calculate Black76 put option price (scalar)
#[pyfunction]
#[pyo3(signature = (f, k, t, r, sigma))]
pub fn black76_put_price(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // TODO: Implement using Arrow-native Black76 kernel from core
    Err(pyo3::exceptions::PyNotImplementedError::new_err(
        "Black76 not yet implemented in Arrow-native version"
    ))
}

// ============================================================================
// Merton Model (Dividends)
// ============================================================================

/// Calculate Merton model call option price (scalar)
#[pyfunction]
#[pyo3(signature = (s, k, t, r, q, sigma))]
pub fn merton_call_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    // TODO: Implement using Arrow-native Merton kernel from core
    Err(pyo3::exceptions::PyNotImplementedError::new_err(
        "Merton model not yet implemented in Arrow-native version"
    ))
}

/// Calculate Merton model put option price (scalar)
#[pyfunction]
#[pyo3(signature = (s, k, t, r, q, sigma))]
pub fn merton_put_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    // TODO: Implement using Arrow-native Merton kernel from core
    Err(pyo3::exceptions::PyNotImplementedError::new_err(
        "Merton model not yet implemented in Arrow-native version"
    ))
}

// ============================================================================
// American Options
// ============================================================================

/// Calculate American call option price (scalar)
#[pyfunction]
#[pyo3(signature = (s, k, t, r, sigma))]
pub fn american_call_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // TODO: Implement using Arrow-native American kernel from core
    Err(pyo3::exceptions::PyNotImplementedError::new_err(
        "American options not yet implemented in Arrow-native version"
    ))
}

/// Calculate American put option price (scalar)
#[pyfunction]
#[pyo3(signature = (s, k, t, r, sigma))]
pub fn american_put_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // TODO: Implement using Arrow-native American kernel from core
    Err(pyo3::exceptions::PyNotImplementedError::new_err(
        "American options not yet implemented in Arrow-native version"
    ))
}