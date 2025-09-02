//! Arrow Native Module - pyo3-arrow Zero-Copy Implementation
//!
//! This module provides Apache Arrow FFI integration for zero-copy data exchange
//! between Python and Rust. It uses pyo3-arrow for automatic Arrow data conversion.

use arrow::array::Float64Array;
use arrow::datatypes::{DataType, Field};
use arrow::error::ArrowError;
use pyo3::exceptions::{PyNotImplementedError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3_arrow::{error::PyArrowResult, PyArray};
use quantforge_core::compute::formulas::{
    black76_call_scalar, black76_put_scalar, black_scholes_call_scalar, black_scholes_put_scalar,
    merton_call_scalar, merton_put_scalar,
};
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

// ============================================================================
// Scalar Functions
// ============================================================================

/// Black-Scholes call price (scalar version)
#[pyfunction]
pub fn call_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // Validate inputs
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(PyValueError::new_err("s, k, t, and sigma must be positive"));
    }
    Ok(black_scholes_call_scalar(s, k, t, r, sigma))
}

/// Black-Scholes put price (scalar version)
#[pyfunction]
pub fn put_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // Validate inputs
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(PyValueError::new_err("s, k, t, and sigma must be positive"));
    }
    Ok(black_scholes_put_scalar(s, k, t, r, sigma))
}

/// Calculate all Greeks for Black-Scholes (scalar version)
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
    // Validate inputs
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(PyValueError::new_err("s, k, t, and sigma must be positive"));
    }

    // Calculate all Greeks using scalar arrays of size 1
    let spots = Float64Array::from(vec![s]);
    let strikes = Float64Array::from(vec![k]);
    let times = Float64Array::from(vec![t]);
    let rates = Float64Array::from(vec![r]);
    let sigmas = Float64Array::from(vec![sigma]);

    // Calculate each Greek
    let delta_arc = BlackScholes::delta(&spots, &strikes, &times, &rates, &sigmas, is_call)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let gamma_arc = BlackScholes::gamma(&spots, &strikes, &times, &rates, &sigmas)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let vega_arc = BlackScholes::vega(&spots, &strikes, &times, &rates, &sigmas)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let theta_arc = BlackScholes::theta(&spots, &strikes, &times, &rates, &sigmas, is_call)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let rho_arc = BlackScholes::rho(&spots, &strikes, &times, &rates, &sigmas, is_call)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;

    // Downcast to Float64Array and extract scalar values
    let delta_f64 = delta_arc
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyValueError::new_err("Failed to downcast delta"))?;
    let gamma_f64 = gamma_arc
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyValueError::new_err("Failed to downcast gamma"))?;
    let vega_f64 = vega_arc
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyValueError::new_err("Failed to downcast vega"))?;
    let theta_f64 = theta_arc
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyValueError::new_err("Failed to downcast theta"))?;
    let rho_f64 = rho_arc
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyValueError::new_err("Failed to downcast rho"))?;

    // Extract scalar values and return as dict
    let dict = PyDict::new(py);
    dict.set_item("delta", delta_f64.value(0))?;
    dict.set_item("gamma", gamma_f64.value(0))?;
    dict.set_item("vega", vega_f64.value(0))?;
    dict.set_item("theta", theta_f64.value(0))?;
    dict.set_item("rho", rho_f64.value(0))?;

    Ok(dict)
}

/// Black76 call price (scalar version)
#[pyfunction]
pub fn black76_call_price(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // Validate inputs
    if f <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(PyValueError::new_err("f, k, t, and sigma must be positive"));
    }
    Ok(black76_call_scalar(f, k, t, r, sigma))
}

/// Black76 put price (scalar version)
#[pyfunction]
pub fn black76_put_price(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // Validate inputs
    if f <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(PyValueError::new_err("f, k, t, and sigma must be positive"));
    }
    Ok(black76_put_scalar(f, k, t, r, sigma))
}

/// Merton call price (scalar version with dividends)
#[pyfunction]
pub fn merton_call_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    // Validate inputs
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 || q < 0.0 {
        return Err(PyValueError::new_err(
            "s, k, t, and sigma must be positive; q must be non-negative",
        ));
    }
    Ok(merton_call_scalar(s, k, t, r, q, sigma))
}

/// Merton put price (scalar version with dividends)
#[pyfunction]
pub fn merton_put_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    // Validate inputs
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 || q < 0.0 {
        return Err(PyValueError::new_err(
            "s, k, t, and sigma must be positive; q must be non-negative",
        ));
    }
    Ok(merton_put_scalar(s, k, t, r, q, sigma))
}

/// American call price (placeholder)
#[pyfunction]
pub fn american_call_price(_s: f64, _k: f64, _t: f64, _r: f64, _sigma: f64) -> PyResult<f64> {
    Err(PyNotImplementedError::new_err(
        "American options not yet implemented",
    ))
}

/// American put price (placeholder)
#[pyfunction]
pub fn american_put_price(_s: f64, _k: f64, _t: f64, _r: f64, _sigma: f64) -> PyResult<f64> {
    Err(PyNotImplementedError::new_err(
        "American options not yet implemented",
    ))
}

// ============================================================================
// Implied Volatility Functions
// ============================================================================

/// Calculate implied volatility using Newton-Raphson method
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
    // Validate inputs
    if price <= 0.0 || s <= 0.0 || k <= 0.0 || t <= 0.0 {
        return Err(PyValueError::new_err("price, s, k, and t must be positive"));
    }

    // Check for arbitrage bounds
    let intrinsic = if is_call {
        (s - k * (-r * t).exp()).max(0.0)
    } else {
        (k * (-r * t).exp() - s).max(0.0)
    };

    if price < intrinsic {
        return Err(PyValueError::new_err(
            "Option price violates arbitrage bounds",
        ));
    }

    // Newton-Raphson iteration
    let mut sigma = 0.3; // Initial guess
    let max_iterations = 100;
    let tolerance = 1e-8;

    for _ in 0..max_iterations {
        let calc_price = if is_call {
            black_scholes_call_scalar(s, k, t, r, sigma)
        } else {
            black_scholes_put_scalar(s, k, t, r, sigma)
        };

        let diff = calc_price - price;
        if diff.abs() < tolerance {
            return Ok(sigma);
        }

        // Calculate vega for Newton-Raphson update
        let spots = Float64Array::from(vec![s]);
        let strikes = Float64Array::from(vec![k]);
        let times = Float64Array::from(vec![t]);
        let rates = Float64Array::from(vec![r]);
        let sigmas = Float64Array::from(vec![sigma]);

        let vega_arc = BlackScholes::vega(&spots, &strikes, &times, &rates, &sigmas)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        let vega_f64 = vega_arc
            .as_any()
            .downcast_ref::<Float64Array>()
            .ok_or_else(|| PyValueError::new_err("Failed to downcast vega"))?;
        let vega_value = vega_f64.value(0);

        if vega_value < 1e-10 {
            return Err(PyValueError::new_err("Vega too small for convergence"));
        }

        sigma -= diff / vega_value;

        // Keep sigma positive
        if sigma <= 0.0 {
            sigma = 0.001;
        }
    }

    Err(PyValueError::new_err(
        "Failed to converge in implied volatility calculation",
    ))
}

// ============================================================================
// Batch Functions (Arrow-based)
// ============================================================================

/// Black-Scholes call price batch calculation
#[pyfunction]
pub fn call_price_batch(
    py: Python,
    spots: PyArray,
    strikes: PyArray,
    times: PyArray,
    rates: PyArray,
    sigmas: PyArray,
) -> PyArrowResult<PyObject> {
    // Direct call to arrow function
    arrow_call_price(py, spots, strikes, times, rates, sigmas)
}

/// Black-Scholes put price batch calculation
#[pyfunction]
pub fn put_price_batch(
    py: Python,
    spots: PyArray,
    strikes: PyArray,
    times: PyArray,
    rates: PyArray,
    sigmas: PyArray,
) -> PyArrowResult<PyObject> {
    // Direct call to arrow function
    arrow_put_price(py, spots, strikes, times, rates, sigmas)
}

/// Black-Scholes Greeks batch calculation
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, sigmas, is_call=true))]
pub fn greeks_batch(
    py: Python,
    spots: PyArray,
    strikes: PyArray,
    times: PyArray,
    rates: PyArray,
    sigmas: PyArray,
    is_call: bool,
) -> PyArrowResult<PyObject> {
    // Direct call to arrow function
    arrow_greeks(py, spots, strikes, times, rates, sigmas, is_call)
}

/// Implied volatility batch calculation (placeholder)
#[pyfunction]
pub fn implied_volatility_batch(
    _py: Python,
    _prices: PyArray,
    _spots: PyArray,
    _strikes: PyArray,
    _times: PyArray,
    _rates: PyArray,
    _is_call: bool,
) -> PyArrowResult<PyObject> {
    Err(pyo3_arrow::error::PyArrowError::PyErr(
        PyNotImplementedError::new_err("Batch implied volatility not yet implemented"),
    ))
}

// ============================================================================
// Fast No-Validation Batch Functions
// ============================================================================

/// Black-Scholes call price batch without validation (for performance)
#[pyfunction]
#[pyo3(name = "call_price_batch_no_validation")]
pub fn call_price_batch_no_validation(
    py: Python,
    spots: PyArray,
    strikes: PyArray,
    times: PyArray,
    rates: PyArray,
    sigmas: PyArray,
) -> PyArrowResult<PyObject> {
    // Directly call the arrow function without any validation
    // This is the same as arrow_call_price but with a different name
    arrow_call_price(py, spots, strikes, times, rates, sigmas)
}

/// Black-Scholes put price batch without validation (for performance)
#[pyfunction]
#[pyo3(name = "put_price_batch_no_validation")]
pub fn put_price_batch_no_validation(
    py: Python,
    spots: PyArray,
    strikes: PyArray,
    times: PyArray,
    rates: PyArray,
    sigmas: PyArray,
) -> PyArrowResult<PyObject> {
    // Directly call the arrow function without any validation
    arrow_put_price(py, spots, strikes, times, rates, sigmas)
}

/// Module registration
pub fn register_arrow_functions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Arrow batch functions
    m.add_function(wrap_pyfunction!(arrow_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(arrow_put_price, m)?)?;
    m.add_function(wrap_pyfunction!(arrow_greeks, m)?)?;
    m.add_function(wrap_pyfunction!(arrow76_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(arrow76_put_price, m)?)?;
    m.add_function(wrap_pyfunction!(arrow76_greeks, m)?)?;

    // Scalar functions
    m.add_function(wrap_pyfunction!(call_price, m)?)?;
    m.add_function(wrap_pyfunction!(put_price, m)?)?;
    m.add_function(wrap_pyfunction!(greeks, m)?)?;
    m.add_function(wrap_pyfunction!(black76_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(black76_put_price, m)?)?;
    m.add_function(wrap_pyfunction!(merton_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(merton_put_price, m)?)?;
    m.add_function(wrap_pyfunction!(american_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(american_put_price, m)?)?;

    // Implied volatility
    m.add_function(wrap_pyfunction!(implied_volatility, m)?)?;

    // No-validation batch functions
    m.add_function(wrap_pyfunction!(call_price_batch_no_validation, m)?)?;
    m.add_function(wrap_pyfunction!(put_price_batch_no_validation, m)?)?;

    Ok(())
}
