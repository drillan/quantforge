//! Arrow Native Module - pyo3-arrow Zero-Copy Implementation
//!
//! This module provides Apache Arrow FFI integration for zero-copy data exchange
//! between Python and Rust. It uses pyo3-arrow for automatic Arrow data conversion.

use arrow::array::Float64Array;
use arrow::datatypes::{DataType, Field};
use arrow::error::ArrowError;
use pyo3::prelude::*;
use pyo3_arrow::{error::PyArrowResult, PyArray};
use quantforge_core::compute::BlackScholes;
use std::sync::Arc;

/// Black-Scholes call price calculation using Arrow arrays
///
/// Parameters:
/// - spots: Arrow array of spot prices
/// - strikes: Arrow array of strike prices  
/// - times: Arrow array of times to maturity
/// - rates: Arrow array of risk-free rates
/// - sigmas: Arrow array of volatilities
///
/// Returns Arrow array of call prices
#[pyfunction]
#[pyo3(name = "arrow_call_price")]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
pub fn arrow_call_price(
    py: Python,
    spots: PyArray,
    strikes: PyArray,
    times: PyArray,
    rates: PyArray,
    sigmas: PyArray,
) -> PyArrowResult<PyObject> {
    // Extract Arrow arrays from PyArray wrappers
    let spots_array = spots.as_ref();
    let strikes_array = strikes.as_ref();
    let times_array = times.as_ref();
    let rates_array = rates.as_ref();
    let sigmas_array = sigmas.as_ref();

    // Downcast to Float64Array
    let spots_f64 = spots_array
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("spots must be Float64Array".into()))?;
    let strikes_f64 = strikes_array
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("strikes must be Float64Array".into()))?;
    let times_f64 = times_array
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("times must be Float64Array".into()))?;
    let rates_f64 = rates_array
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("rates must be Float64Array".into()))?;
    let sigmas_f64 = sigmas_array
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("sigmas must be Float64Array".into()))?;

    // Compute call prices using quantforge-core BlackScholes
    // Release GIL for computation
    let result_arc = py
        .allow_threads(|| {
            BlackScholes::call_price(spots_f64, strikes_f64, times_f64, rates_f64, sigmas_f64)
        })
        .map_err(|e| {
            ArrowError::ComputeError(format!(
                "Black-Scholes call price computation failed: {e}"
            ))
        })?;

    // Create field for the result
    let field = Arc::new(Field::new("call_price", DataType::Float64, false));

    // Wrap in PyArray with Arc to manage lifetime
    let py_array = PyArray::new(result_arc, field);

    // Convert to Python object using to_arro3
    let result = py_array.to_arro3(py)?;
    Ok(result.into())
}

/// Black-Scholes put price calculation using Arrow arrays
///
/// Parameters:
/// - spots: Arrow array of spot prices
/// - strikes: Arrow array of strike prices
/// - times: Arrow array of times to maturity
/// - rates: Arrow array of risk-free rates
/// - sigmas: Arrow array of volatilities
///
/// Returns Arrow array of put prices
#[pyfunction]
#[pyo3(name = "arrow_put_price")]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
pub fn arrow_put_price(
    py: Python,
    spots: PyArray,
    strikes: PyArray,
    times: PyArray,
    rates: PyArray,
    sigmas: PyArray,
) -> PyArrowResult<PyObject> {
    // Extract Arrow arrays from PyArray wrappers
    let spots_array = spots.as_ref();
    let strikes_array = strikes.as_ref();
    let times_array = times.as_ref();
    let rates_array = rates.as_ref();
    let sigmas_array = sigmas.as_ref();

    // Downcast to Float64Array
    let spots_f64 = spots_array
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("spots must be Float64Array".into()))?;
    let strikes_f64 = strikes_array
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("strikes must be Float64Array".into()))?;
    let times_f64 = times_array
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("times must be Float64Array".into()))?;
    let rates_f64 = rates_array
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("rates must be Float64Array".into()))?;
    let sigmas_f64 = sigmas_array
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("sigmas must be Float64Array".into()))?;

    // Compute put prices using quantforge-core BlackScholes
    // Release GIL for computation
    let result_arc = py
        .allow_threads(|| {
            BlackScholes::put_price(spots_f64, strikes_f64, times_f64, rates_f64, sigmas_f64)
        })
        .map_err(|e| {
            ArrowError::ComputeError(format!("Black-Scholes put price computation failed: {e}"))
        })?;

    // Create field for the result
    let field = Arc::new(Field::new("put_price", DataType::Float64, false));

    // Wrap in PyArray with Arc to manage lifetime
    let py_array = PyArray::new(result_arc, field);

    // Convert to Python object using to_arro3
    let result = py_array.to_arro3(py)?;
    Ok(result.into())
}

/// Module registration
pub fn register_arrow_functions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(arrow_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(arrow_put_price, m)?)?;
    Ok(())
}
