//! Arrow Native Module - pyo3-arrow Zero-Copy Implementation
//!
//! This module provides Apache Arrow FFI integration for zero-copy data exchange
//! between Python and Rust. It uses pyo3-arrow for automatic Arrow data conversion.

use arrow::array::Float64Array;
use arrow::error::ArrowError;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use pyo3_arrow::error::PyArrowResult;
use quantforge_core::compute::formulas::{
    black76_call_scalar, black76_put_scalar, black_scholes_call_scalar, black_scholes_put_scalar,
    merton_call_scalar, merton_put_scalar,
};
use quantforge_core::compute::{Black76, BlackScholes, Merton};

use crate::arrow_common::{
    create_greeks_dict, extract_black76_arrays, extract_black_scholes_arrays,
    extract_boolean_array, field_names, parse_black76_params, parse_black_scholes_params,
    parse_is_calls_param, parse_merton_params, validate_black76_arrays,
    validate_black76_scalar_inputs_detailed, validate_black_scholes_arrays_with_rates,
    validate_scalar_inputs_detailed, wrap_result_array,
};

/// Black-Scholes call price calculation using Arrow arrays
///
/// Parameters:
/// - spots: Spot prices (float or Arrow array)
/// - strikes: Strike prices (float or Arrow array)  
/// - times: Times to maturity (float or Arrow array)
/// - rates: Risk-free rates (float or Arrow array)
/// - sigmas: Volatilities (float or Arrow array)
///
/// Returns Arrow array of call prices
#[pyfunction]
#[pyo3(name = "arrow_call_price")]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
pub fn arrow_call_price(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject> {
    // Parse parameters using common function
    let params = parse_black_scholes_params(py, spots, strikes, times, rates, sigmas)?;

    // Extract arrays
    let (spots_f64, strikes_f64, times_f64, rates_f64, sigmas_f64) =
        extract_black_scholes_arrays(&params)?;

    // Validate arrays
    validate_black_scholes_arrays_with_rates(
        spots_f64,
        strikes_f64,
        times_f64,
        rates_f64,
        sigmas_f64,
    )?;

    // Compute call prices using quantforge-core BlackScholes
    // Release GIL for computation
    let result_arc = py
        .allow_threads(|| {
            BlackScholes::call_price(spots_f64, strikes_f64, times_f64, rates_f64, sigmas_f64)
        })
        .map_err(|e| {
            ArrowError::ComputeError(format!("Black-Scholes call price computation failed: {e}"))
        })?;

    // Wrap result using common function
    wrap_result_array(py, result_arc, field_names::CALL_PRICE)
}

/// Black-Scholes put price calculation using Arrow arrays
///
/// Parameters:
/// - spots: Spot prices (float or Arrow array)
/// - strikes: Strike prices (float or Arrow array)
/// - times: Times to maturity (float or Arrow array)
/// - rates: Risk-free rates (float or Arrow array)
/// - sigmas: Volatilities (float or Arrow array)
///
/// Returns Arrow array of put prices
#[pyfunction]
#[pyo3(name = "arrow_put_price")]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
pub fn arrow_put_price(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject> {
    // Parse parameters using common function
    let params = parse_black_scholes_params(py, spots, strikes, times, rates, sigmas)?;

    // Extract arrays
    let (spots_f64, strikes_f64, times_f64, rates_f64, sigmas_f64) =
        extract_black_scholes_arrays(&params)?;

    // Validate arrays
    validate_black_scholes_arrays_with_rates(
        spots_f64,
        strikes_f64,
        times_f64,
        rates_f64,
        sigmas_f64,
    )?;

    // Compute put prices using quantforge-core BlackScholes
    // Release GIL for computation
    let result_arc = py
        .allow_threads(|| {
            BlackScholes::put_price(spots_f64, strikes_f64, times_f64, rates_f64, sigmas_f64)
        })
        .map_err(|e| {
            ArrowError::ComputeError(format!("Black-Scholes put price computation failed: {e}"))
        })?;

    // Wrap result using common function
    wrap_result_array(py, result_arc, field_names::PUT_PRICE)
}

/// Black-Scholes Greeks calculation using Arrow arrays
///
/// Parameters:
/// - spots: Spot prices (float or Arrow array)
/// - strikes: Strike prices (float or Arrow array)
/// - times: Times to maturity (float or Arrow array)
/// - rates: Risk-free rates (float or Arrow array)
/// - sigmas: Volatilities (float or Arrow array)
/// - is_call: Boolean flag for call (true) or put (false) option
///
/// Returns Dict[str, Arrow array] of Greeks
#[pyfunction]
#[pyo3(name = "arrow_greeks")]
#[pyo3(signature = (spots, strikes, times, rates, sigmas, is_call))]
pub fn arrow_greeks(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
    is_call: bool,
) -> PyArrowResult<PyObject> {
    // Parse parameters using common function
    let params = parse_black_scholes_params(py, spots, strikes, times, rates, sigmas)?;

    // Extract arrays
    let (spots_f64, strikes_f64, times_f64, rates_f64, sigmas_f64) =
        extract_black_scholes_arrays(&params)?;

    // Validate arrays
    validate_black_scholes_arrays_with_rates(
        spots_f64,
        strikes_f64,
        times_f64,
        rates_f64,
        sigmas_f64,
    )?;

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

    // Create Python dict using common function
    let result_dict = create_greeks_dict(py, delta_arc, gamma_arc, vega_arc, theta_arc, rho_arc)?;
    Ok(result_dict.into())
}

/// Black76 call price calculation using Arrow arrays
///
/// Parameters:
/// - forwards: Forward prices (float or Arrow array)
/// - strikes: Strike prices (float or Arrow array)
/// - times: Times to maturity (float or Arrow array)
/// - rates: Risk-free rates (float or Arrow array)
/// - sigmas: Volatilities (float or Arrow array)
///
/// Returns Arrow array of call prices
#[pyfunction]
#[pyo3(name = "arrow76_call_price")]
#[pyo3(signature = (forwards, strikes, times, rates, sigmas))]
pub fn arrow76_call_price(
    py: Python,
    forwards: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject> {
    // Parse parameters using common function
    let params = parse_black76_params(py, forwards, strikes, times, rates, sigmas)?;

    // Extract arrays
    let (forwards_f64, strikes_f64, times_f64, rates_f64, sigmas_f64) =
        extract_black76_arrays(&params)?;

    // Validate arrays
    validate_black76_arrays(forwards_f64, strikes_f64, times_f64, sigmas_f64)?;

    // Compute with GIL released
    let result_arc = py
        .allow_threads(|| {
            Black76::call_price(forwards_f64, strikes_f64, times_f64, rates_f64, sigmas_f64)
        })
        .map_err(|e| {
            ArrowError::ComputeError(format!("Black76 call price computation failed: {e}"))
        })?;

    // Wrap result using common function
    wrap_result_array(py, result_arc, field_names::CALL_PRICE)
}

/// Black76 put price calculation using Arrow arrays
#[pyfunction]
#[pyo3(name = "arrow76_put_price")]
#[pyo3(signature = (forwards, strikes, times, rates, sigmas))]
pub fn arrow76_put_price(
    py: Python,
    forwards: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject> {
    // Parse parameters using common function
    let params = parse_black76_params(py, forwards, strikes, times, rates, sigmas)?;

    // Extract arrays
    let (forwards_f64, strikes_f64, times_f64, rates_f64, sigmas_f64) =
        extract_black76_arrays(&params)?;

    // Validate arrays
    validate_black76_arrays(forwards_f64, strikes_f64, times_f64, sigmas_f64)?;

    // Compute with GIL released
    let result_arc = py
        .allow_threads(|| {
            Black76::put_price(forwards_f64, strikes_f64, times_f64, rates_f64, sigmas_f64)
        })
        .map_err(|e| {
            ArrowError::ComputeError(format!("Black76 put price computation failed: {e}"))
        })?;

    // Wrap result using common function
    wrap_result_array(py, result_arc, field_names::PUT_PRICE)
}

/// Black76 Greeks calculation using Arrow arrays
#[pyfunction]
#[pyo3(name = "arrow76_greeks")]
#[pyo3(signature = (forwards, strikes, times, rates, sigmas, is_call))]
pub fn arrow76_greeks(
    py: Python,
    forwards: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
    is_call: bool,
) -> PyArrowResult<PyObject> {
    // Parse parameters using common function
    let params = parse_black76_params(py, forwards, strikes, times, rates, sigmas)?;

    // Extract arrays
    let (forwards_f64, strikes_f64, times_f64, rates_f64, sigmas_f64) =
        extract_black76_arrays(&params)?;

    // Validate arrays
    validate_black76_arrays(forwards_f64, strikes_f64, times_f64, sigmas_f64)?;

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

    // Create Python dict using common function
    let result_dict = create_greeks_dict(py, delta_arc, gamma_arc, vega_arc, theta_arc, rho_arc)?;
    Ok(result_dict.into())
}

// ============================================================================
// Scalar Functions
// ============================================================================

/// Black-Scholes call price (scalar version)
#[pyfunction]
pub fn call_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    validate_scalar_inputs_detailed(s, k, t, r, sigma)?;
    Ok(black_scholes_call_scalar(s, k, t, r, sigma))
}

/// Black-Scholes put price (scalar version)
#[pyfunction]
pub fn put_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    validate_scalar_inputs_detailed(s, k, t, r, sigma)?;
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
    validate_scalar_inputs_detailed(s, k, t, r, sigma)?;

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
    validate_black76_scalar_inputs_detailed(f, k, t, r, sigma)?;
    Ok(black76_call_scalar(f, k, t, r, sigma))
}

/// Black76 put price (scalar version)
#[pyfunction]
pub fn black76_put_price(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    validate_black76_scalar_inputs_detailed(f, k, t, r, sigma)?;
    Ok(black76_put_scalar(f, k, t, r, sigma))
}

/// Merton call price (scalar version with dividends)
#[pyfunction]
pub fn merton_call_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    validate_scalar_inputs_detailed(s, k, t, r, sigma)?;
    // Allow negative dividend (storage cost) within reasonable range
    if !(-1.0..=1.0).contains(&q) {
        return Err(PyValueError::new_err(format!(
            "dividend_yield out of range [-1.0, 1.0] (got {q})"
        )));
    }
    Ok(merton_call_scalar(s, k, t, r, q, sigma))
}

/// Merton put price (scalar version with dividends)
#[pyfunction]
pub fn merton_put_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    validate_scalar_inputs_detailed(s, k, t, r, sigma)?;
    // Allow negative dividend (storage cost) within reasonable range
    if !(-1.0..=1.0).contains(&q) {
        return Err(PyValueError::new_err(format!(
            "dividend_yield out of range [-1.0, 1.0] (got {q})"
        )));
    }
    Ok(merton_put_scalar(s, k, t, r, q, sigma))
}

/// American call price using BS2002 approximation
#[pyfunction]
#[pyo3(signature = (s, k, t, r, q, sigma))]
pub fn american_call_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    validate_scalar_inputs_detailed(s, k, t, r, sigma)?;
    // Allow negative dividend (storage cost) within reasonable range
    if !(-1.0..=1.0).contains(&q) {
        return Err(PyValueError::new_err(format!(
            "dividend_yield out of range [-1.0, 1.0] (got {q})"
        )));
    }
    Ok(quantforge_core::compute::american::american_call_scalar(
        s, k, t, r, q, sigma,
    ))
}

/// American put price using BS2002 approximation
#[pyfunction]
#[pyo3(signature = (s, k, t, r, q, sigma))]
pub fn american_put_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    validate_scalar_inputs_detailed(s, k, t, r, sigma)?;
    // Allow negative dividend (storage cost) within reasonable range
    if !(-1.0..=1.0).contains(&q) {
        return Err(PyValueError::new_err(format!(
            "dividend_yield out of range [-1.0, 1.0] (got {q})"
        )));
    }
    Ok(quantforge_core::compute::american::american_put_scalar(
        s, k, t, r, q, sigma,
    ))
}

/// American option binomial tree pricing
#[pyfunction]
#[pyo3(signature = (s, k, t, r, q, sigma, n_steps=100, is_call=true))]
#[allow(clippy::too_many_arguments)]
pub fn american_binomial(
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    n_steps: usize,
    is_call: bool,
) -> PyResult<f64> {
    validate_scalar_inputs_detailed(s, k, t, r, sigma)?;
    // Allow negative dividend (storage cost) within reasonable range
    if !(-1.0..=1.0).contains(&q) {
        return Err(PyValueError::new_err(format!(
            "dividend_yield out of range [-1.0, 1.0] (got {q})"
        )));
    }
    if n_steps == 0 {
        return Err(PyValueError::new_err("n_steps must be at least 1"));
    }
    Ok(quantforge_core::compute::american::american_binomial(
        s, k, t, r, q, sigma, n_steps, is_call,
    ))
}

/// American option Greeks calculation
#[pyfunction]
#[pyo3(signature = (s, k, t, r, q, sigma, is_call=true))]
#[allow(clippy::too_many_arguments)]
pub fn american_greeks(
    py: Python,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    is_call: bool,
) -> PyResult<PyObject> {
    validate_scalar_inputs_detailed(s, k, t, r, sigma)?;
    if !(-1.0..=1.0).contains(&q) {
        return Err(PyValueError::new_err(format!(
            "dividend_yield out of range [-1.0, 1.0] (got {q})"
        )));
    }

    let delta = if is_call {
        quantforge_core::compute::american::american_call_delta(s, k, t, r, q, sigma)
    } else {
        quantforge_core::compute::american::american_put_delta(s, k, t, r, q, sigma)
    };

    let gamma = quantforge_core::compute::american::american_call_gamma(s, k, t, r, q, sigma);

    let vega = if is_call {
        quantforge_core::compute::american::american_call_vega(s, k, t, r, q, sigma)
    } else {
        quantforge_core::compute::american::american_put_vega(s, k, t, r, q, sigma)
    };

    let theta = if is_call {
        quantforge_core::compute::american::american_call_theta(s, k, t, r, q, sigma)
    } else {
        quantforge_core::compute::american::american_put_theta(s, k, t, r, q, sigma)
    };

    let rho = if is_call {
        quantforge_core::compute::american::american_call_rho(s, k, t, r, q, sigma)
    } else {
        quantforge_core::compute::american::american_put_rho(s, k, t, r, q, sigma)
    };

    let greeks_dict = PyDict::new(py);
    greeks_dict.set_item("delta", delta)?;
    greeks_dict.set_item("gamma", gamma)?;
    greeks_dict.set_item("vega", vega)?;
    greeks_dict.set_item("theta", theta)?;
    greeks_dict.set_item("rho", rho)?;
    greeks_dict.set_item("dividend_rho", 0.0)?; // Not implemented yet

    Ok(greeks_dict.into())
}

/// American option implied volatility using Newton-Raphson
#[pyfunction]
#[pyo3(signature = (price, s, k, t, r, q, is_call=true, initial_guess=0.2, tolerance=1e-6, max_iterations=100))]
#[allow(clippy::too_many_arguments)]
pub fn american_implied_volatility(
    price: f64,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    is_call: bool,
    initial_guess: f64,
    tolerance: f64,
    max_iterations: usize,
) -> PyResult<f64> {
    validate_scalar_inputs_detailed(s, k, t, r, 0.2)?; // Use dummy sigma for validation
    if !(-1.0..=1.0).contains(&q) {
        return Err(PyValueError::new_err(format!(
            "dividend_yield out of range [-1.0, 1.0] (got {q})"
        )));
    }

    // Simple Newton-Raphson for now (not optimal but works)
    let mut sigma = initial_guess;

    for _ in 0..max_iterations {
        let calc_price = if is_call {
            quantforge_core::compute::american::american_call_scalar(s, k, t, r, q, sigma)
        } else {
            quantforge_core::compute::american::american_put_scalar(s, k, t, r, q, sigma)
        };

        let vega = if is_call {
            quantforge_core::compute::american::american_call_vega(s, k, t, r, q, sigma)
        } else {
            quantforge_core::compute::american::american_put_vega(s, k, t, r, q, sigma)
        };

        let diff = calc_price - price;
        if diff.abs() < tolerance {
            return Ok(sigma);
        }

        // Newton-Raphson update
        sigma -= diff / (vega * 100.0); // vega is per 1% change

        // Keep sigma in reasonable bounds
        sigma = sigma.clamp(0.001, 5.0);
    }

    Err(PyValueError::new_err("Failed to converge"))
}

/// American call option price batch processing
#[pyfunction]
pub fn american_call_price_batch(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    dividend_yields: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyResult<PyObject> {
    // For now, use simple Python list approach
    // TODO: Implement proper Arrow batch processing
    let spots_list = spots.extract::<Vec<f64>>()?;
    let strikes_list = strikes.extract::<Vec<f64>>()?;
    let times_list = times.extract::<Vec<f64>>()?;
    let rates_list = rates.extract::<Vec<f64>>()?;
    let divs_list = dividend_yields.extract::<Vec<f64>>()?;
    let sigmas_list = sigmas.extract::<Vec<f64>>()?;

    let len = spots_list.len();
    let mut results = Vec::with_capacity(len);

    for i in 0..len {
        let price = quantforge_core::compute::american::american_call_scalar(
            spots_list[i],
            strikes_list[i],
            times_list[i],
            rates_list[i],
            divs_list[i],
            sigmas_list[i],
        );
        results.push(price);
    }

    Ok(PyList::new(py, results)?.into())
}

/// American put option price batch processing
#[pyfunction]
pub fn american_put_price_batch(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    dividend_yields: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyResult<PyObject> {
    // For now, use simple Python list approach
    // TODO: Implement proper Arrow batch processing
    let spots_list = spots.extract::<Vec<f64>>()?;
    let strikes_list = strikes.extract::<Vec<f64>>()?;
    let times_list = times.extract::<Vec<f64>>()?;
    let rates_list = rates.extract::<Vec<f64>>()?;
    let divs_list = dividend_yields.extract::<Vec<f64>>()?;
    let sigmas_list = sigmas.extract::<Vec<f64>>()?;

    let len = spots_list.len();
    let mut results = Vec::with_capacity(len);

    for i in 0..len {
        let price = quantforge_core::compute::american::american_put_scalar(
            spots_list[i],
            strikes_list[i],
            times_list[i],
            rates_list[i],
            divs_list[i],
            sigmas_list[i],
        );
        results.push(price);
    }

    Ok(PyList::new(py, results)?.into())
}

/// American option Greeks batch processing
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, dividend_yields, sigmas, is_call=true))]
#[allow(clippy::too_many_arguments)]
pub fn american_greeks_batch(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    dividend_yields: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
    is_call: bool,
) -> PyResult<PyObject> {
    // For now, use simple Python list approach
    let s_array = spots.extract::<Vec<f64>>()?;
    let k_array = strikes.extract::<Vec<f64>>()?;
    let t_array = times.extract::<Vec<f64>>()?;
    let r_array = rates.extract::<Vec<f64>>()?;
    let q_array = dividend_yields.extract::<Vec<f64>>()?;
    let sigma_array = sigmas.extract::<Vec<f64>>()?;

    let len = s_array.len();

    let mut delta_vec = Vec::with_capacity(len);
    let mut gamma_vec = Vec::with_capacity(len);
    let mut vega_vec = Vec::with_capacity(len);
    let mut theta_vec = Vec::with_capacity(len);
    let mut rho_vec = Vec::with_capacity(len);

    for i in 0..len {
        let s = s_array[i];
        let k = k_array[i];
        let t = t_array[i];
        let r = r_array[i];
        let q = q_array[i];
        let sigma = sigma_array[i];

        let delta = if is_call {
            quantforge_core::compute::american::american_call_delta(s, k, t, r, q, sigma)
        } else {
            quantforge_core::compute::american::american_put_delta(s, k, t, r, q, sigma)
        };

        let gamma = quantforge_core::compute::american::american_call_gamma(s, k, t, r, q, sigma);

        let vega = if is_call {
            quantforge_core::compute::american::american_call_vega(s, k, t, r, q, sigma)
        } else {
            quantforge_core::compute::american::american_put_vega(s, k, t, r, q, sigma)
        };

        let theta = if is_call {
            quantforge_core::compute::american::american_call_theta(s, k, t, r, q, sigma)
        } else {
            quantforge_core::compute::american::american_put_theta(s, k, t, r, q, sigma)
        };

        let rho = if is_call {
            quantforge_core::compute::american::american_call_rho(s, k, t, r, q, sigma)
        } else {
            quantforge_core::compute::american::american_put_rho(s, k, t, r, q, sigma)
        };

        delta_vec.push(delta);
        gamma_vec.push(gamma);
        vega_vec.push(vega);
        theta_vec.push(theta);
        rho_vec.push(rho);
    }

    // Create output dictionary
    let greeks_dict = PyDict::new(py);
    greeks_dict.set_item("delta", delta_vec)?;
    greeks_dict.set_item("gamma", gamma_vec)?;
    greeks_dict.set_item("vega", vega_vec)?;
    greeks_dict.set_item("theta", theta_vec)?;
    greeks_dict.set_item("rho", rho_vec)?;
    greeks_dict.set_item("dividend_rho", vec![0.0; len])?;

    Ok(greeks_dict.into())
}

/// American option implied volatility batch processing
#[pyfunction]
#[pyo3(signature = (option_prices, spots, strikes, times, rates, dividend_yields, is_call=true))]
#[allow(clippy::too_many_arguments)]
pub fn american_implied_volatility_batch(
    py: Python,
    option_prices: &Bound<'_, PyAny>,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    dividend_yields: &Bound<'_, PyAny>,
    is_call: bool,
) -> PyResult<PyObject> {
    let price_array = option_prices.extract::<Vec<f64>>()?;
    let s_array = spots.extract::<Vec<f64>>()?;
    let k_array = strikes.extract::<Vec<f64>>()?;
    let t_array = times.extract::<Vec<f64>>()?;
    let r_array = rates.extract::<Vec<f64>>()?;
    let q_array = dividend_yields.extract::<Vec<f64>>()?;

    let len = price_array.len();

    let mut results = Vec::with_capacity(len);

    for i in 0..len {
        let price = price_array[i];
        let s = s_array[i];
        let k = k_array[i];
        let t = t_array[i];
        let r = r_array[i];
        let q = q_array[i];

        // Simple Newton-Raphson implied volatility
        let mut sigma = 0.2; // Initial guess
        let mut converged = false;

        for _ in 0..100 {
            let calc_price = if is_call {
                quantforge_core::compute::american::american_call_scalar(s, k, t, r, q, sigma)
            } else {
                quantforge_core::compute::american::american_put_scalar(s, k, t, r, q, sigma)
            };

            let vega = if is_call {
                quantforge_core::compute::american::american_call_vega(s, k, t, r, q, sigma)
            } else {
                quantforge_core::compute::american::american_put_vega(s, k, t, r, q, sigma)
            };

            let diff = calc_price - price;
            if diff.abs() < 1e-6 {
                converged = true;
                break;
            }

            sigma -= diff / (vega * 100.0);
            sigma = sigma.clamp(0.001, 5.0);
        }

        results.push(if converged { sigma } else { f64::NAN });
    }

    Ok(PyList::new(py, results)?.into())
}

// ============================================================================
// Black76 Additional Functions
// ============================================================================

/// Black76 Greeks calculation (scalar version)
#[pyfunction]
#[pyo3(name = "greeks")]
#[pyo3(signature = (f, k, t, r, sigma, is_call=true))]
pub fn black76_greeks<'py>(
    py: Python<'py>,
    f: f64,
    k: f64,
    t: f64,
    r: f64,
    sigma: f64,
    is_call: bool,
) -> PyResult<Bound<'py, PyDict>> {
    validate_black76_scalar_inputs_detailed(f, k, t, r, sigma)?;

    // Use Black76 struct from quantforge_core
    let forwards = Float64Array::from(vec![f]);
    let strikes = Float64Array::from(vec![k]);
    let times = Float64Array::from(vec![t]);
    let rates = Float64Array::from(vec![r]);
    let sigmas = Float64Array::from(vec![sigma]);

    // Calculate each Greek using Black76 struct
    let delta_arc = Black76::delta(&forwards, &strikes, &times, &rates, &sigmas, is_call)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let gamma_arc = Black76::gamma(&forwards, &strikes, &times, &rates, &sigmas)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let vega_arc = Black76::vega(&forwards, &strikes, &times, &rates, &sigmas)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let theta_arc = Black76::theta(&forwards, &strikes, &times, &rates, &sigmas, is_call)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let rho_arc = Black76::rho(&forwards, &strikes, &times, &rates, &sigmas, is_call)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;

    // Extract scalar values
    let delta = delta_arc
        .as_any()
        .downcast_ref::<Float64Array>()
        .unwrap()
        .value(0);
    let gamma = gamma_arc
        .as_any()
        .downcast_ref::<Float64Array>()
        .unwrap()
        .value(0);
    let vega = vega_arc
        .as_any()
        .downcast_ref::<Float64Array>()
        .unwrap()
        .value(0);
    let theta = theta_arc
        .as_any()
        .downcast_ref::<Float64Array>()
        .unwrap()
        .value(0);
    let rho = rho_arc
        .as_any()
        .downcast_ref::<Float64Array>()
        .unwrap()
        .value(0);

    // Create Python dict
    let dict = PyDict::new(py);
    dict.set_item("delta", delta)?;
    dict.set_item("gamma", gamma)?;
    dict.set_item("vega", vega)?;
    dict.set_item("theta", theta)?;
    dict.set_item("rho", rho)?;

    Ok(dict)
}

/// Black76 call price batch calculation
#[pyfunction]
pub fn black76_call_price_batch(
    py: Python,
    forwards: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject> {
    // Use existing arrow76_call_price function
    arrow76_call_price(py, forwards, strikes, times, rates, sigmas)
}

/// Black76 put price batch calculation
#[pyfunction]
pub fn black76_put_price_batch(
    py: Python,
    forwards: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject> {
    // Use existing arrow76_put_price function
    arrow76_put_price(py, forwards, strikes, times, rates, sigmas)
}

/// Black76 Greeks batch calculation
#[pyfunction]
#[pyo3(name = "greeks_batch")]
#[pyo3(signature = (forwards, strikes, times, rates, sigmas, is_calls=true))]
pub fn black76_greeks_batch(
    py: Python,
    forwards: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
    is_calls: bool,
) -> PyArrowResult<PyObject> {
    // Use existing arrow76_greeks function
    arrow76_greeks(py, forwards, strikes, times, rates, sigmas, is_calls)
}

/// Black76 implied volatility (scalar)
#[pyfunction]
#[pyo3(signature = (price, f, k, t, r, is_call=true))]
pub fn black76_implied_volatility(
    price: f64,
    f: f64,
    k: f64,
    t: f64,
    r: f64,
    is_call: bool,
) -> PyResult<f64> {
    // Validate inputs
    if price <= 0.0 || f <= 0.0 || k <= 0.0 || t <= 0.0 {
        return Err(PyValueError::new_err("price, f, k, and t must be positive"));
    }

    // Newton-Raphson method for Black76
    let mut sigma = 0.3; // Initial guess
    let max_iterations = 100;
    let tolerance = 1e-6;

    for _ in 0..max_iterations {
        let calc_price = if is_call {
            black76_call_scalar(f, k, t, r, sigma)
        } else {
            black76_put_scalar(f, k, t, r, sigma)
        };

        let diff = calc_price - price;
        if diff.abs() < tolerance {
            return Ok(sigma);
        }

        // Calculate vega for Newton-Raphson update
        let forwards = Float64Array::from(vec![f]);
        let strikes = Float64Array::from(vec![k]);
        let times = Float64Array::from(vec![t]);
        let rates = Float64Array::from(vec![r]);
        let sigmas = Float64Array::from(vec![sigma]);

        let vega_arc = Black76::vega(&forwards, &strikes, &times, &rates, &sigmas)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        let vega_value = vega_arc
            .as_any()
            .downcast_ref::<Float64Array>()
            .unwrap()
            .value(0);

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

/// Black76 implied volatility batch calculation
///
/// Parameters:
/// - prices: Market prices (float or Arrow array)
/// - forwards: Forward prices (float or Arrow array)
/// - strikes: Strike prices (float or Arrow array)
/// - times: Times to maturity (float or Arrow array)
/// - rates: Risk-free rates (float or Arrow array)
/// - is_calls: Call/Put flags (bool or Arrow array)
///
/// Returns Arrow array of implied volatilities
#[pyfunction]
pub fn black76_implied_volatility_batch(
    py: Python,
    prices: &Bound<'_, PyAny>,
    forwards: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    is_calls: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject> {
    // Parse price array separately
    use crate::utils::pyany_to_arrow;
    let prices_array = pyany_to_arrow(py, prices)?;
    let prices_f64 = prices_array
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("prices must be Float64Array".to_string()))?;

    // Parse other parameters using common function (sigmas is dummy here)
    let params = parse_black76_params(py, forwards, strikes, times, rates, forwards)?;
    let is_calls_array = parse_is_calls_param(py, is_calls)?;

    // Extract arrays
    let (forwards_f64, strikes_f64, times_f64, rates_f64, _) = extract_black76_arrays(&params)?;
    let is_calls_bool = extract_boolean_array(&is_calls_array)?;

    // Compute implied volatility using quantforge-core Black76
    // Release GIL for computation
    let result_arc = py
        .allow_threads(|| {
            Black76::implied_volatility(
                prices_f64,
                forwards_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                is_calls_bool,
            )
        })
        .map_err(|e| {
            ArrowError::ComputeError(format!(
                "Black76 implied volatility computation failed: {e}"
            ))
        })?;

    // Wrap result using common function
    wrap_result_array(py, result_arc, field_names::IMPLIED_VOLATILITY)
}

// ============================================================================
// Merton Additional Functions
// ============================================================================

/// Merton Greeks calculation (scalar version)
#[pyfunction]
#[pyo3(signature = (s, k, t, r, q, sigma, is_call=true))]
#[allow(clippy::too_many_arguments)]
pub fn merton_greeks<'py>(
    py: Python<'py>,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    is_call: bool,
) -> PyResult<Bound<'py, PyDict>> {
    validate_scalar_inputs_detailed(s, k, t, r, sigma)?;
    // Allow negative dividend (storage cost) within reasonable range
    if !(-1.0..=1.0).contains(&q) {
        return Err(PyValueError::new_err(format!(
            "dividend_yield out of range [-1.0, 1.0] (got {q})"
        )));
    }

    // Use Merton-specific Greeks from core implementation
    let spots = Float64Array::from(vec![s]);
    let strikes = Float64Array::from(vec![k]);
    let times = Float64Array::from(vec![t]);
    let rates = Float64Array::from(vec![r]);
    let sigmas = Float64Array::from(vec![sigma]);
    let dividend_yields = Float64Array::from(vec![q]);

    // Use Merton Greeks which properly account for dividends
    let delta_arc = Merton::delta(
        &spots,
        &strikes,
        &times,
        &rates,
        &dividend_yields,
        &sigmas,
        is_call,
    )
    .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let gamma_arc = Merton::gamma(&spots, &strikes, &times, &rates, &dividend_yields, &sigmas)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let vega_arc = Merton::vega(&spots, &strikes, &times, &rates, &dividend_yields, &sigmas)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let theta_arc = Merton::theta(
        &spots,
        &strikes,
        &times,
        &rates,
        &dividend_yields,
        &sigmas,
        is_call,
    )
    .map_err(|e| PyValueError::new_err(e.to_string()))?;
    let rho_arc = Merton::rho(
        &spots,
        &strikes,
        &times,
        &rates,
        &dividend_yields,
        &sigmas,
        is_call,
    )
    .map_err(|e| PyValueError::new_err(e.to_string()))?;

    // Extract scalar values
    let delta = delta_arc
        .as_any()
        .downcast_ref::<Float64Array>()
        .unwrap()
        .value(0);
    let gamma = gamma_arc
        .as_any()
        .downcast_ref::<Float64Array>()
        .unwrap()
        .value(0);
    let vega = vega_arc
        .as_any()
        .downcast_ref::<Float64Array>()
        .unwrap()
        .value(0);
    let theta = theta_arc
        .as_any()
        .downcast_ref::<Float64Array>()
        .unwrap()
        .value(0);
    let rho = rho_arc
        .as_any()
        .downcast_ref::<Float64Array>()
        .unwrap()
        .value(0);

    // Add dividend_rho from Merton model
    let dividend_rho_arc = Merton::dividend_rho(
        &spots,
        &strikes,
        &times,
        &rates,
        &dividend_yields,
        &sigmas,
        is_call,
    )
    .map_err(|e| PyValueError::new_err(e.to_string()))?;

    let dividend_rho = dividend_rho_arc
        .as_any()
        .downcast_ref::<Float64Array>()
        .unwrap()
        .value(0);

    // Create Python dict
    let dict = PyDict::new(py);
    dict.set_item("delta", delta)?;
    dict.set_item("gamma", gamma)?;
    dict.set_item("vega", vega)?;
    dict.set_item("theta", theta)?;
    dict.set_item("rho", rho)?;
    dict.set_item("dividend_rho", dividend_rho)?;

    Ok(dict)
}

/// Merton call price calculation using Arrow arrays
///
/// Parameters:
/// - spots: Spot prices (float or Arrow array)
/// - strikes: Strike prices (float or Arrow array)
/// - times: Times to maturity (float or Arrow array)
/// - rates: Risk-free rates (float or Arrow array)
/// - dividend_yields: Dividend yields (float or Arrow array)
/// - sigmas: Volatilities (float or Arrow array)
///
/// Returns Arrow array of call prices
#[pyfunction]
#[pyo3(name = "arrow_merton_call_price")]
#[pyo3(signature = (spots, strikes, times, rates, dividend_yields, sigmas))]
pub fn arrow_merton_call_price(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    dividend_yields: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject> {
    // Parse parameters using Merton-specific function
    let params = parse_merton_params(py, spots, strikes, times, rates, dividend_yields, sigmas)?;

    // Extract arrays
    let spots_f64 = params
        .spots
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("spots must be Float64Array".to_string()))?;
    let strikes_f64 = params
        .strikes
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("strikes must be Float64Array".to_string()))?;
    let times_f64 = params
        .times
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("times must be Float64Array".to_string()))?;
    let rates_f64 = params
        .rates
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("rates must be Float64Array".to_string()))?;
    let dividend_yields_f64 = params
        .dividend_yields
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("dividend_yields must be Float64Array".to_string()))?;
    let sigmas_f64 = params
        .sigmas
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("sigmas must be Float64Array".to_string()))?;

    // Validate arrays
    validate_black_scholes_arrays_with_rates(
        spots_f64,
        strikes_f64,
        times_f64,
        rates_f64,
        sigmas_f64,
    )?;

    // Compute using Merton model with GIL released
    let result_arc = py
        .allow_threads(|| {
            Merton::call_price(
                spots_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                dividend_yields_f64,
                sigmas_f64,
            )
        })
        .map_err(|e| {
            ArrowError::ComputeError(format!("Merton call price computation failed: {e}"))
        })?;

    wrap_result_array(py, result_arc, field_names::CALL_PRICE)
}

/// Merton call price batch calculation
#[pyfunction]
pub fn merton_call_price_batch(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    dividend_yields: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject> {
    // Use existing arrow_merton_call_price function
    arrow_merton_call_price(py, spots, strikes, times, rates, dividend_yields, sigmas)
}

/// Merton put price calculation using Arrow arrays
///
/// Parameters:
/// - spots: Spot prices (float or Arrow array)
/// - strikes: Strike prices (float or Arrow array)
/// - times: Times to maturity (float or Arrow array)
/// - rates: Risk-free rates (float or Arrow array)
/// - dividend_yields: Dividend yields (float or Arrow array)
/// - sigmas: Volatilities (float or Arrow array)
///
/// Returns Arrow array of put prices
#[pyfunction]
#[pyo3(name = "arrow_merton_put_price")]
#[pyo3(signature = (spots, strikes, times, rates, dividend_yields, sigmas))]
pub fn arrow_merton_put_price(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    dividend_yields: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject> {
    // Parse parameters using Merton-specific function
    let params = parse_merton_params(py, spots, strikes, times, rates, dividend_yields, sigmas)?;

    // Extract arrays
    let spots_f64 = params
        .spots
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("spots must be Float64Array".to_string()))?;
    let strikes_f64 = params
        .strikes
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("strikes must be Float64Array".to_string()))?;
    let times_f64 = params
        .times
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("times must be Float64Array".to_string()))?;
    let rates_f64 = params
        .rates
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("rates must be Float64Array".to_string()))?;
    let dividend_yields_f64 = params
        .dividend_yields
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("dividend_yields must be Float64Array".to_string()))?;
    let sigmas_f64 = params
        .sigmas
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("sigmas must be Float64Array".to_string()))?;

    // Validate arrays
    validate_black_scholes_arrays_with_rates(
        spots_f64,
        strikes_f64,
        times_f64,
        rates_f64,
        sigmas_f64,
    )?;

    // Compute using Merton model with GIL released
    let result_arc = py
        .allow_threads(|| {
            Merton::put_price(
                spots_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                dividend_yields_f64,
                sigmas_f64,
            )
        })
        .map_err(|e| {
            ArrowError::ComputeError(format!("Merton put price computation failed: {e}"))
        })?;

    wrap_result_array(py, result_arc, field_names::PUT_PRICE)
}

/// Merton put price batch calculation
#[pyfunction]
pub fn merton_put_price_batch(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    dividend_yields: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject> {
    // Use existing arrow_merton_put_price function
    arrow_merton_put_price(py, spots, strikes, times, rates, dividend_yields, sigmas)
}

/// Merton Greeks calculation using Arrow arrays
///
/// Parameters:
/// - spots: Spot prices (float or Arrow array)
/// - strikes: Strike prices (float or Arrow array)
/// - times: Times to maturity (float or Arrow array)
/// - rates: Risk-free rates (float or Arrow array)
/// - dividend_yields: Dividend yields (float or Arrow array)
/// - sigmas: Volatilities (float or Arrow array)
/// - is_call: Boolean flag for call (true) or put (false) option
///
/// Returns Dict[str, Arrow array] of Greeks
#[pyfunction]
#[pyo3(name = "arrow_merton_greeks")]
#[pyo3(signature = (spots, strikes, times, rates, dividend_yields, sigmas, is_call))]
#[allow(clippy::too_many_arguments)]
pub fn arrow_merton_greeks(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    dividend_yields: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
    is_call: bool,
) -> PyArrowResult<PyObject> {
    // Parse parameters using Merton-specific function
    let params = parse_merton_params(py, spots, strikes, times, rates, dividend_yields, sigmas)?;

    // Extract arrays
    let spots_f64 = params
        .spots
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("spots must be Float64Array".to_string()))?;
    let strikes_f64 = params
        .strikes
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("strikes must be Float64Array".to_string()))?;
    let times_f64 = params
        .times
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("times must be Float64Array".to_string()))?;
    let rates_f64 = params
        .rates
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("rates must be Float64Array".to_string()))?;
    let dividend_yields_f64 = params
        .dividend_yields
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("dividend_yields must be Float64Array".to_string()))?;
    let sigmas_f64 = params
        .sigmas
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("sigmas must be Float64Array".to_string()))?;

    // Validate arrays
    validate_black_scholes_arrays_with_rates(
        spots_f64,
        strikes_f64,
        times_f64,
        rates_f64,
        sigmas_f64,
    )?;

    // Compute Greeks using quantforge-core Merton (release GIL)
    let (delta_arc, gamma_arc, vega_arc, theta_arc, rho_arc, dividend_rho_arc) = py
        .allow_threads(|| {
            let delta = Merton::delta(
                spots_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                dividend_yields_f64,
                sigmas_f64,
                is_call,
            )?;
            let gamma = Merton::gamma(
                spots_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                dividend_yields_f64,
                sigmas_f64,
            )?;
            let vega = Merton::vega(
                spots_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                dividend_yields_f64,
                sigmas_f64,
            )?;
            let theta = Merton::theta(
                spots_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                dividend_yields_f64,
                sigmas_f64,
                is_call,
            )?;
            let rho = Merton::rho(
                spots_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                dividend_yields_f64,
                sigmas_f64,
                is_call,
            )?;
            let dividend_rho = Merton::dividend_rho(
                spots_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                dividend_yields_f64,
                sigmas_f64,
                is_call,
            )?;
            Ok::<_, ArrowError>((delta, gamma, vega, theta, rho, dividend_rho))
        })
        .map_err(|e: ArrowError| {
            ArrowError::ComputeError(format!("Merton Greeks computation failed: {e}"))
        })?;

    // Create Python dict with all Greeks including dividend_rho
    use crate::arrow_common::create_merton_greeks_dict;
    let result_dict = create_merton_greeks_dict(
        py,
        delta_arc,
        gamma_arc,
        vega_arc,
        theta_arc,
        rho_arc,
        dividend_rho_arc,
    )?;
    Ok(result_dict.into())
}

/// Merton Greeks batch calculation
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, dividend_yields, sigmas, is_calls=true))]
#[allow(clippy::too_many_arguments)]
pub fn merton_greeks_batch(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    dividend_yields: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
    is_calls: bool,
) -> PyArrowResult<PyObject> {
    // Use existing arrow_merton_greeks function
    arrow_merton_greeks(
        py,
        spots,
        strikes,
        times,
        rates,
        dividend_yields,
        sigmas,
        is_calls,
    )
}

/// Merton implied volatility (scalar)
#[pyfunction]
#[pyo3(signature = (price, s, k, t, r, q, is_call=true))]
pub fn merton_implied_volatility(
    price: f64,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    is_call: bool,
) -> PyResult<f64> {
    // Validate inputs
    if price <= 0.0 || s <= 0.0 || k <= 0.0 || t <= 0.0 {
        return Err(PyValueError::new_err("price, s, k, and t must be positive"));
    }
    // Allow negative dividend (storage cost) within reasonable range
    if !(-1.0..=1.0).contains(&q) {
        return Err(PyValueError::new_err(format!(
            "dividend_yield out of range [-1.0, 1.0] (got {q})"
        )));
    }

    // Newton-Raphson method for Merton
    let mut sigma = 0.3; // Initial guess
    let max_iterations = 100;
    let tolerance = 1e-6;

    for _ in 0..max_iterations {
        let calc_price = if is_call {
            merton_call_scalar(s, k, t, r, q, sigma)
        } else {
            merton_put_scalar(s, k, t, r, q, sigma)
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
        let vega_value = vega_arc
            .as_any()
            .downcast_ref::<Float64Array>()
            .unwrap()
            .value(0);

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

/// Merton implied volatility batch calculation
///
/// Parameters:
/// - prices: Market prices (float or Arrow array)
/// - spots: Spot prices (float or Arrow array)
/// - strikes: Strike prices (float or Arrow array)
/// - times: Times to maturity (float or Arrow array)
/// - rates: Risk-free rates (float or Arrow array)
/// - dividend_yields: Dividend yields (float or Arrow array)
/// - is_calls: Call/Put flags (bool or Arrow array)
///
/// Returns Arrow array of implied volatilities
#[pyfunction]
#[pyo3(name = "implied_volatility_batch")]
#[allow(clippy::too_many_arguments)]
pub fn merton_implied_volatility_batch(
    py: Python,
    prices: &Bound<'_, PyAny>,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    dividend_yields: &Bound<'_, PyAny>,
    is_calls: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject> {
    // Parse price array separately
    use crate::utils::pyany_to_arrow;
    let prices_array = pyany_to_arrow(py, prices)?;
    let prices_f64 = prices_array
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("prices must be Float64Array".to_string()))?;

    // Parse other parameters using common function (sigmas is dummy here)
    let params = parse_merton_params(py, spots, strikes, times, rates, dividend_yields, spots)?;
    let is_calls_array = parse_is_calls_param(py, is_calls)?;

    // Extract arrays
    let spots_f64 = params
        .spots
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("spots must be Float64Array".to_string()))?;
    let strikes_f64 = params
        .strikes
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("strikes must be Float64Array".to_string()))?;
    let times_f64 = params
        .times
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("times must be Float64Array".to_string()))?;
    let rates_f64 = params
        .rates
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("rates must be Float64Array".to_string()))?;
    let dividend_yields_f64 = params
        .dividend_yields
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("dividend_yields must be Float64Array".to_string()))?;
    let is_calls_bool = extract_boolean_array(&is_calls_array)?;

    // Compute implied volatility using quantforge-core Merton
    // Release GIL for computation
    let result_arc = py
        .allow_threads(|| {
            Merton::implied_volatility(
                prices_f64,
                spots_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                dividend_yields_f64,
                is_calls_bool,
            )
        })
        .map_err(|e| {
            ArrowError::ComputeError(format!("Merton implied volatility computation failed: {e}"))
        })?;

    // Wrap result using common function
    wrap_result_array(py, result_arc, field_names::IMPLIED_VOLATILITY)
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
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject> {
    // Direct call to arrow function
    arrow_call_price(py, spots, strikes, times, rates, sigmas)
}

/// Black-Scholes put price batch calculation
#[pyfunction]
pub fn put_price_batch(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject> {
    // Direct call to arrow function
    arrow_put_price(py, spots, strikes, times, rates, sigmas)
}

/// Black-Scholes Greeks batch calculation
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, sigmas, is_call=true))]
pub fn greeks_batch(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
    is_call: bool,
) -> PyArrowResult<PyObject> {
    // Direct call to arrow function
    arrow_greeks(py, spots, strikes, times, rates, sigmas, is_call)
}

/// Black-Scholes implied volatility batch calculation
///
/// Parameters:
/// - prices: Market prices (float or Arrow array)
/// - spots: Spot prices (float or Arrow array)
/// - strikes: Strike prices (float or Arrow array)
/// - times: Times to maturity (float or Arrow array)
/// - rates: Risk-free rates (float or Arrow array)
/// - is_calls: Call/Put flags (bool or Arrow array)
///
/// Returns Arrow array of implied volatilities
#[pyfunction]
pub fn implied_volatility_batch(
    py: Python,
    prices: &Bound<'_, PyAny>,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    is_calls: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject> {
    // Parse price array separately
    use crate::utils::pyany_to_arrow;
    let prices_array = pyany_to_arrow(py, prices)?;
    let prices_f64 = prices_array
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| ArrowError::CastError("prices must be Float64Array".to_string()))?;

    // Parse other parameters using common function (sigmas is dummy here)
    let params = parse_black_scholes_params(py, spots, strikes, times, rates, spots)?;
    let is_calls_array = parse_is_calls_param(py, is_calls)?;

    // Extract arrays
    let (spots_f64, strikes_f64, times_f64, rates_f64, _) = extract_black_scholes_arrays(&params)?;
    let is_calls_bool = extract_boolean_array(&is_calls_array)?;

    // Compute implied volatility using quantforge-core BlackScholes
    // Release GIL for computation
    let result_arc = py
        .allow_threads(|| {
            BlackScholes::implied_volatility(
                prices_f64,
                spots_f64,
                strikes_f64,
                times_f64,
                rates_f64,
                is_calls_bool,
            )
        })
        .map_err(|e| {
            ArrowError::ComputeError(format!("Implied volatility computation failed: {e}"))
        })?;

    // Wrap result using common function
    wrap_result_array(py, result_arc, field_names::IMPLIED_VOLATILITY)
}

// ============================================================================
// Fast No-Validation Batch Functions
// ============================================================================

/// Black-Scholes call price batch without validation (for performance)
#[pyfunction]
#[pyo3(name = "call_price_batch_no_validation")]
pub fn call_price_batch_no_validation(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
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
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
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

    // Black76 functions
    m.add_function(wrap_pyfunction!(black76_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(black76_put_price, m)?)?;
    m.add_function(wrap_pyfunction!(black76_greeks, m)?)?;
    m.add_function(wrap_pyfunction!(black76_implied_volatility, m)?)?;
    m.add_function(wrap_pyfunction!(black76_call_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(black76_put_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(black76_greeks_batch, m)?)?;
    m.add_function(wrap_pyfunction!(black76_implied_volatility_batch, m)?)?;

    // Merton Arrow functions
    m.add_function(wrap_pyfunction!(arrow_merton_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(arrow_merton_put_price, m)?)?;
    m.add_function(wrap_pyfunction!(arrow_merton_greeks, m)?)?;

    // Merton scalar and batch functions
    m.add_function(wrap_pyfunction!(merton_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(merton_put_price, m)?)?;
    m.add_function(wrap_pyfunction!(merton_greeks, m)?)?;
    m.add_function(wrap_pyfunction!(merton_implied_volatility, m)?)?;
    m.add_function(wrap_pyfunction!(merton_call_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(merton_put_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(merton_greeks_batch, m)?)?;
    m.add_function(wrap_pyfunction!(merton_implied_volatility_batch, m)?)?;

    // American functions (placeholder)
    m.add_function(wrap_pyfunction!(american_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(american_put_price, m)?)?;

    // Implied volatility
    m.add_function(wrap_pyfunction!(implied_volatility, m)?)?;

    // No-validation batch functions
    m.add_function(wrap_pyfunction!(call_price_batch_no_validation, m)?)?;
    m.add_function(wrap_pyfunction!(put_price_batch_no_validation, m)?)?;

    Ok(())
}
