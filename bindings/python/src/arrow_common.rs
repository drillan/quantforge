//! Common utilities for Arrow Native functions
//!
//! This module provides reusable components for Arrow-based option pricing functions
//! to eliminate code duplication and ensure consistency.

use arrow::array::Float64Array;
use arrow::datatypes::{DataType, Field};
use arrow::error::ArrowError;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3_arrow::{error::PyArrowResult, PyArray};
use std::sync::Arc;

use crate::utils::pyany_to_arrow;

/// Common parameter names for better maintainability
pub mod param_names {
    pub const SPOTS: &str = "spots";
    pub const FORWARDS: &str = "forwards";
    pub const STRIKES: &str = "strikes";
    pub const TIMES: &str = "times";
    pub const RATES: &str = "rates";
    pub const SIGMAS: &str = "sigmas";
}

/// Field names for Arrow result arrays
pub mod field_names {
    pub const CALL_PRICE: &str = "call_price";
    pub const PUT_PRICE: &str = "put_price";
    pub const DELTA: &str = "delta";
    pub const GAMMA: &str = "gamma";
    pub const VEGA: &str = "vega";
    pub const THETA: &str = "theta";
    pub const RHO: &str = "rho";
}

/// Parameter set for Black-Scholes model
pub struct BlackScholesParams {
    pub spots: PyArray,
    pub strikes: PyArray,
    pub times: PyArray,
    pub rates: PyArray,
    pub sigmas: PyArray,
}

/// Parameter set for Black76 model
pub struct Black76Params {
    pub forwards: PyArray,
    pub strikes: PyArray,
    pub times: PyArray,
    pub rates: PyArray,
    pub sigmas: PyArray,
}

/// Convert Python objects to Black-Scholes parameters
pub fn parse_black_scholes_params(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyResult<BlackScholesParams> {
    Ok(BlackScholesParams {
        spots: pyany_to_arrow(py, spots)?,
        strikes: pyany_to_arrow(py, strikes)?,
        times: pyany_to_arrow(py, times)?,
        rates: pyany_to_arrow(py, rates)?,
        sigmas: pyany_to_arrow(py, sigmas)?,
    })
}

/// Convert Python objects to Black76 parameters
pub fn parse_black76_params(
    py: Python,
    forwards: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyResult<Black76Params> {
    Ok(Black76Params {
        forwards: pyany_to_arrow(py, forwards)?,
        strikes: pyany_to_arrow(py, strikes)?,
        times: pyany_to_arrow(py, times)?,
        rates: pyany_to_arrow(py, rates)?,
        sigmas: pyany_to_arrow(py, sigmas)?,
    })
}

/// Extract Float64Arrays from Black-Scholes parameters
pub fn extract_black_scholes_arrays(
    params: &BlackScholesParams,
) -> Result<
    (
        &Float64Array,
        &Float64Array,
        &Float64Array,
        &Float64Array,
        &Float64Array,
    ),
    ArrowError,
> {
    let spots = params
        .spots
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| {
            ArrowError::CastError(format!("{} must be Float64Array", param_names::SPOTS))
        })?;

    let strikes = params
        .strikes
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| {
            ArrowError::CastError(format!("{} must be Float64Array", param_names::STRIKES))
        })?;

    let times = params
        .times
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| {
            ArrowError::CastError(format!("{} must be Float64Array", param_names::TIMES))
        })?;

    let rates = params
        .rates
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| {
            ArrowError::CastError(format!("{} must be Float64Array", param_names::RATES))
        })?;

    let sigmas = params
        .sigmas
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| {
            ArrowError::CastError(format!("{} must be Float64Array", param_names::SIGMAS))
        })?;

    Ok((spots, strikes, times, rates, sigmas))
}

/// Extract Float64Arrays from Black76 parameters
pub fn extract_black76_arrays(
    params: &Black76Params,
) -> Result<
    (
        &Float64Array,
        &Float64Array,
        &Float64Array,
        &Float64Array,
        &Float64Array,
    ),
    ArrowError,
> {
    let forwards = params
        .forwards
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| {
            ArrowError::CastError(format!("{} must be Float64Array", param_names::FORWARDS))
        })?;

    let strikes = params
        .strikes
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| {
            ArrowError::CastError(format!("{} must be Float64Array", param_names::STRIKES))
        })?;

    let times = params
        .times
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| {
            ArrowError::CastError(format!("{} must be Float64Array", param_names::TIMES))
        })?;

    let rates = params
        .rates
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| {
            ArrowError::CastError(format!("{} must be Float64Array", param_names::RATES))
        })?;

    let sigmas = params
        .sigmas
        .as_ref()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| {
            ArrowError::CastError(format!("{} must be Float64Array", param_names::SIGMAS))
        })?;

    Ok((forwards, strikes, times, rates, sigmas))
}

/// Wrap computation result in PyArray with field name
pub fn wrap_result_array(
    py: Python,
    result_arc: Arc<dyn arrow::array::Array>,
    field_name: &str,
) -> PyArrowResult<PyObject> {
    let field = Arc::new(Field::new(field_name, DataType::Float64, false));
    let py_array = PyArray::new(result_arc, field);
    let result = py_array.to_arro3(py)?;
    Ok(result.into())
}

/// Create Python dict for Greeks results
pub fn create_greeks_dict<'py>(
    py: Python<'py>,
    delta_arc: Arc<dyn arrow::array::Array>,
    gamma_arc: Arc<dyn arrow::array::Array>,
    vega_arc: Arc<dyn arrow::array::Array>,
    theta_arc: Arc<dyn arrow::array::Array>,
    rho_arc: Arc<dyn arrow::array::Array>,
) -> PyArrowResult<Bound<'py, PyDict>> {
    let result_dict = PyDict::new(py);

    // Delta
    let delta_field = Arc::new(Field::new(field_names::DELTA, DataType::Float64, false));
    let delta_array = PyArray::new(delta_arc, delta_field);
    result_dict.set_item(field_names::DELTA, delta_array.to_arro3(py)?)?;

    // Gamma
    let gamma_field = Arc::new(Field::new(field_names::GAMMA, DataType::Float64, false));
    let gamma_array = PyArray::new(gamma_arc, gamma_field);
    result_dict.set_item(field_names::GAMMA, gamma_array.to_arro3(py)?)?;

    // Vega
    let vega_field = Arc::new(Field::new(field_names::VEGA, DataType::Float64, false));
    let vega_array = PyArray::new(vega_arc, vega_field);
    result_dict.set_item(field_names::VEGA, vega_array.to_arro3(py)?)?;

    // Theta
    let theta_field = Arc::new(Field::new(field_names::THETA, DataType::Float64, false));
    let theta_array = PyArray::new(theta_arc, theta_field);
    result_dict.set_item(field_names::THETA, theta_array.to_arro3(py)?)?;

    // Rho
    let rho_field = Arc::new(Field::new(field_names::RHO, DataType::Float64, false));
    let rho_array = PyArray::new(rho_arc, rho_field);
    result_dict.set_item(field_names::RHO, rho_array.to_arro3(py)?)?;

    Ok(result_dict)
}

/// Validate scalar inputs for option pricing
#[inline(always)]
pub fn validate_scalar_inputs(s: f64, k: f64, t: f64, sigma: f64) -> PyResult<()> {
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(PyValueError::new_err("s, k, t, and sigma must be positive"));
    }
    Ok(())
}

/// Validate Black76 scalar inputs
#[inline(always)]
pub fn validate_black76_scalar_inputs(f: f64, k: f64, t: f64, sigma: f64) -> PyResult<()> {
    if f <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(PyValueError::new_err("f, k, t, and sigma must be positive"));
    }
    Ok(())
}
