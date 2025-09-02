//! Arrow Native Module - pyo3-arrow Zero-Copy Implementation
//!
//! This module provides Apache Arrow FFI integration for zero-copy data exchange
//! between Python and Rust. It uses pyo3-arrow for automatic Arrow data conversion.

use arrow::array::Float64Array;
use arrow::datatypes::{DataType, Field};
use arrow::error::ArrowError;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3_arrow::{error::PyArrowResult, PyArray};
use quantforge_core::compute::{Black76, BlackScholes};
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
            ArrowError::ComputeError(format!("Black-Scholes call price computation failed: {e}"))
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

/// Black-Scholes Greeks calculation using Arrow arrays
///
/// Parameters:
/// - spots: Arrow array of spot prices
/// - strikes: Arrow array of strike prices
/// - times: Arrow array of times to maturity
/// - rates: Arrow array of risk-free rates
/// - sigmas: Arrow array of volatilities
/// - is_call: Boolean flag for call (true) or put (false) option
///
/// Returns Dict[str, Arrow array] of Greeks
#[pyfunction]
#[pyo3(name = "arrow_greeks")]
#[pyo3(signature = (spots, strikes, times, rates, sigmas, is_call))]
pub fn arrow_greeks(
    py: Python,
    spots: PyArray,
    strikes: PyArray,
    times: PyArray,
    rates: PyArray,
    sigmas: PyArray,
    is_call: bool,
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

    // Compute Greeks using quantforge-core BlackScholes (release GIL)
    let (delta_arc, gamma_arc, vega_arc, theta_arc, rho_arc) = py
        .allow_threads(|| {
            let delta = BlackScholes::delta(
                spots_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                sigmas_f64,
                is_call,
            )?;
            let gamma =
                BlackScholes::gamma(spots_f64, strikes_f64, times_f64, rates_f64, sigmas_f64)?;
            let vega =
                BlackScholes::vega(spots_f64, strikes_f64, times_f64, rates_f64, sigmas_f64)?;
            let theta = BlackScholes::theta(
                spots_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                sigmas_f64,
                is_call,
            )?;
            let rho = BlackScholes::rho(
                spots_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                sigmas_f64,
                is_call,
            )?;
            Ok::<_, ArrowError>((delta, gamma, vega, theta, rho))
        })
        .map_err(|e: ArrowError| {
            ArrowError::ComputeError(format!("Greeks computation failed: {e}"))
        })?;

    // Create Python dict to return Greeks
    let result_dict = PyDict::new(py);

    // Add each Greek to the dict
    let delta_field = Arc::new(Field::new("delta", DataType::Float64, false));
    let delta_array = PyArray::new(delta_arc, delta_field);
    result_dict.set_item("delta", delta_array.to_arro3(py)?)?;

    let gamma_field = Arc::new(Field::new("gamma", DataType::Float64, false));
    let gamma_array = PyArray::new(gamma_arc, gamma_field);
    result_dict.set_item("gamma", gamma_array.to_arro3(py)?)?;

    let vega_field = Arc::new(Field::new("vega", DataType::Float64, false));
    let vega_array = PyArray::new(vega_arc, vega_field);
    result_dict.set_item("vega", vega_array.to_arro3(py)?)?;

    let theta_field = Arc::new(Field::new("theta", DataType::Float64, false));
    let theta_array = PyArray::new(theta_arc, theta_field);
    result_dict.set_item("theta", theta_array.to_arro3(py)?)?;

    let rho_field = Arc::new(Field::new("rho", DataType::Float64, false));
    let rho_array = PyArray::new(rho_arc, rho_field);
    result_dict.set_item("rho", rho_array.to_arro3(py)?)?;

    Ok(result_dict.into())
}

/// Black76 call price calculation using Arrow arrays
///
/// Parameters:
/// - forwards: Arrow array of forward prices
/// - strikes: Arrow array of strike prices
/// - times: Arrow array of times to maturity
/// - rates: Arrow array of risk-free rates
/// - sigmas: Arrow array of volatilities
///
/// Returns Arrow array of call prices
#[pyfunction]
#[pyo3(name = "arrow76_call_price")]
#[pyo3(signature = (forwards, strikes, times, rates, sigmas))]
pub fn arrow76_call_price(
    py: Python,
    forwards: PyArray,
    strikes: PyArray,
    times: PyArray,
    rates: PyArray,
    sigmas: PyArray,
) -> PyArrowResult<PyObject> {
    // Extract and downcast arrays
    let forwards_f64 = forwards
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("forwards must be Float64Array".into()))?;
    let strikes_f64 = strikes
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("strikes must be Float64Array".into()))?;
    let times_f64 = times
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("times must be Float64Array".into()))?;
    let rates_f64 = rates
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("rates must be Float64Array".into()))?;
    let sigmas_f64 = sigmas
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("sigmas must be Float64Array".into()))?;

    // Compute with GIL released
    let result_arc = py
        .allow_threads(|| {
            Black76::call_price(forwards_f64, strikes_f64, times_f64, rates_f64, sigmas_f64)
        })
        .map_err(|e| {
            ArrowError::ComputeError(format!("Black76 call price computation failed: {e}"))
        })?;

    // Create field and return
    let field = Arc::new(Field::new("call_price", DataType::Float64, false));
    let py_array = PyArray::new(result_arc, field);
    let result = py_array.to_arro3(py)?;
    Ok(result.into())
}

/// Black76 put price calculation using Arrow arrays
#[pyfunction]
#[pyo3(name = "arrow76_put_price")]
#[pyo3(signature = (forwards, strikes, times, rates, sigmas))]
pub fn arrow76_put_price(
    py: Python,
    forwards: PyArray,
    strikes: PyArray,
    times: PyArray,
    rates: PyArray,
    sigmas: PyArray,
) -> PyArrowResult<PyObject> {
    // Extract and downcast arrays
    let forwards_f64 = forwards
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("forwards must be Float64Array".into()))?;
    let strikes_f64 = strikes
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("strikes must be Float64Array".into()))?;
    let times_f64 = times
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("times must be Float64Array".into()))?;
    let rates_f64 = rates
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("rates must be Float64Array".into()))?;
    let sigmas_f64 = sigmas
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("sigmas must be Float64Array".into()))?;

    // Compute with GIL released
    let result_arc = py
        .allow_threads(|| {
            Black76::put_price(forwards_f64, strikes_f64, times_f64, rates_f64, sigmas_f64)
        })
        .map_err(|e| {
            ArrowError::ComputeError(format!("Black76 put price computation failed: {e}"))
        })?;

    // Create field and return
    let field = Arc::new(Field::new("put_price", DataType::Float64, false));
    let py_array = PyArray::new(result_arc, field);
    let result = py_array.to_arro3(py)?;
    Ok(result.into())
}

/// Black76 Greeks calculation using Arrow arrays
#[pyfunction]
#[pyo3(name = "arrow76_greeks")]
#[pyo3(signature = (forwards, strikes, times, rates, sigmas, is_call))]
pub fn arrow76_greeks(
    py: Python,
    forwards: PyArray,
    strikes: PyArray,
    times: PyArray,
    rates: PyArray,
    sigmas: PyArray,
    is_call: bool,
) -> PyArrowResult<PyObject> {
    // Extract and downcast arrays
    let forwards_f64 = forwards
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("forwards must be Float64Array".into()))?;
    let strikes_f64 = strikes
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("strikes must be Float64Array".into()))?;
    let times_f64 = times
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("times must be Float64Array".into()))?;
    let rates_f64 = rates
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("rates must be Float64Array".into()))?;
    let sigmas_f64 = sigmas
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("sigmas must be Float64Array".into()))?;

    // Compute Greeks with GIL released
    let (delta_arc, gamma_arc, vega_arc, theta_arc, rho_arc) = py
        .allow_threads(|| {
            let delta = Black76::delta(
                forwards_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                sigmas_f64,
                is_call,
            )?;
            let gamma =
                Black76::gamma(forwards_f64, strikes_f64, times_f64, rates_f64, sigmas_f64)?;
            let vega = Black76::vega(forwards_f64, strikes_f64, times_f64, rates_f64, sigmas_f64)?;
            let theta = Black76::theta(
                forwards_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                sigmas_f64,
                is_call,
            )?;
            let rho = Black76::rho(
                forwards_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                sigmas_f64,
                is_call,
            )?;
            Ok::<_, ArrowError>((delta, gamma, vega, theta, rho))
        })
        .map_err(|e: ArrowError| {
            ArrowError::ComputeError(format!("Black76 Greeks computation failed: {e}"))
        })?;

    // Create Python dict
    let result_dict = PyDict::new(py);

    // Add each Greek
    let delta_field = Arc::new(Field::new("delta", DataType::Float64, false));
    let delta_array = PyArray::new(delta_arc, delta_field);
    result_dict.set_item("delta", delta_array.to_arro3(py)?)?;

    let gamma_field = Arc::new(Field::new("gamma", DataType::Float64, false));
    let gamma_array = PyArray::new(gamma_arc, gamma_field);
    result_dict.set_item("gamma", gamma_array.to_arro3(py)?)?;

    let vega_field = Arc::new(Field::new("vega", DataType::Float64, false));
    let vega_array = PyArray::new(vega_arc, vega_field);
    result_dict.set_item("vega", vega_array.to_arro3(py)?)?;

    let theta_field = Arc::new(Field::new("theta", DataType::Float64, false));
    let theta_array = PyArray::new(theta_arc, theta_field);
    result_dict.set_item("theta", theta_array.to_arro3(py)?)?;

    let rho_field = Arc::new(Field::new("rho", DataType::Float64, false));
    let rho_array = PyArray::new(rho_arc, rho_field);
    result_dict.set_item("rho", rho_array.to_arro3(py)?)?;

    Ok(result_dict.into())
}

/// Module registration
pub fn register_arrow_functions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(arrow_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(arrow_put_price, m)?)?;
    m.add_function(wrap_pyfunction!(arrow_greeks, m)?)?;
    m.add_function(wrap_pyfunction!(arrow76_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(arrow76_put_price, m)?)?;
    m.add_function(wrap_pyfunction!(arrow76_greeks, m)?)?;
    Ok(())
}
