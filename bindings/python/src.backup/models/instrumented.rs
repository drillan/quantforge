//! Instrumented version of Black-Scholes for profiling FFI overhead

use crate::converters::ArrayLike;
use crate::converters::broadcast_optimized::{BroadcastIteratorOptimized, BroadcastInput};
use numpy::{PyArray1, PyArrayMethods};
use pyo3::prelude::*;
use quantforge_core::models::black_scholes::BlackScholes;
use quantforge_core::OptionModel;
use std::time::Instant;

/// Instrumented call_price_batch to measure FFI overhead components
#[pyfunction]
#[pyo3(name = "call_price_batch_instrumented")]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
pub fn call_price_batch_instrumented(
    py: Python<'_>,
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    sigmas: ArrayLike,
) -> PyResult<Py<PyArray1<f64>>> {
    let total_start = Instant::now();
    
    // Phase 1: Parameter extraction
    let param_start = Instant::now();
    let max_len = spots
        .len()
        .max(strikes.len())
        .max(times.len())
        .max(rates.len())
        .max(sigmas.len());
    let param_time = param_start.elapsed();
    
    // Phase 2: Create broadcast iterator
    let broadcast_start = Instant::now();
    let iter = BroadcastIteratorOptimized::new(
        vec![&spots, &strikes, &times, &rates, &sigmas],
    ).map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;
    let broadcast_time = broadcast_start.elapsed();
    
    // Phase 3: Computation with GIL release
    let compute_start = Instant::now();
    let results = py.allow_threads(move || {
        let bs = BlackScholes;
        iter.compute_with(|values| {
            let s = values[0];
            let k = values[1];
            let t = values[2];
            let r = values[3];
            let sigma = values[4];
            bs.call_price(s, k, t, r, sigma).unwrap_or(f64::NAN)
        })
    });
    let compute_time = compute_start.elapsed();
    
    // Phase 4: Convert results to PyArray
    let convert_start = Instant::now();
    let py_array = PyArray1::from_vec_bound(py, results);
    let convert_time = convert_start.elapsed();
    
    let total_time = total_start.elapsed();
    
    // Print timing breakdown
    println!("\n=== FFI Overhead Breakdown (batch size: {}) ===", max_len);
    println!("Parameter extraction: {:?} ({:.1}%)", 
        param_time, 
        param_time.as_secs_f64() / total_time.as_secs_f64() * 100.0
    );
    println!("Broadcast setup:      {:?} ({:.1}%)", 
        broadcast_time,
        broadcast_time.as_secs_f64() / total_time.as_secs_f64() * 100.0
    );
    println!("Computation:          {:?} ({:.1}%)", 
        compute_time,
        compute_time.as_secs_f64() / total_time.as_secs_f64() * 100.0
    );
    println!("Result conversion:    {:?} ({:.1}%)", 
        convert_time,
        convert_time.as_secs_f64() / total_time.as_secs_f64() * 100.0
    );
    println!("Total time:           {:?}", total_time);
    println!("===============================================\n");
    
    Ok(py_array.unbind())
}

/// Minimal FFI function for baseline measurement
#[pyfunction]
#[pyo3(name = "minimal_ffi_call")]
pub fn minimal_ffi_call(py: Python<'_>, size: usize) -> PyResult<Py<PyArray1<f64>>> {
    let results = vec![1.0; size];
    Ok(PyArray1::from_vec_bound(py, results).unbind())
}

/// FFI with ArrayLike conversion but no computation
#[pyfunction]
#[pyo3(name = "ffi_with_conversion")]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
pub fn ffi_with_conversion(
    py: Python<'_>,
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    sigmas: ArrayLike,
) -> PyResult<Py<PyArray1<f64>>> {
    let max_len = spots
        .len()
        .max(strikes.len())
        .max(times.len())
        .max(rates.len())
        .max(sigmas.len());
    
    let results = vec![1.0; max_len];
    Ok(PyArray1::from_vec_bound(py, results).unbind())
}

/// FFI with BroadcastIterator but minimal computation
#[pyfunction]
#[pyo3(name = "ffi_with_broadcast")]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
pub fn ffi_with_broadcast(
    py: Python<'_>,
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    sigmas: ArrayLike,
) -> PyResult<Py<PyArray1<f64>>> {
    let _max_len = spots
        .len()
        .max(strikes.len())
        .max(times.len())
        .max(rates.len())
        .max(sigmas.len());
    
    let iter = BroadcastIteratorOptimized::new(
        vec![&spots, &strikes, &times, &rates, &sigmas],
    ).map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;
    
    let results = py.allow_threads(move || {
        iter.compute_with(|values| values[0] + values[1])  // Minimal computation
    });
    
    Ok(PyArray1::from_vec_bound(py, results).unbind())
}

/// Register instrumented functions
pub fn register_instrumented(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(call_price_batch_instrumented, m)?)?;
    m.add_function(wrap_pyfunction!(minimal_ffi_call, m)?)?;
    m.add_function(wrap_pyfunction!(ffi_with_conversion, m)?)?;
    m.add_function(wrap_pyfunction!(ffi_with_broadcast, m)?)?;
    Ok(())
}