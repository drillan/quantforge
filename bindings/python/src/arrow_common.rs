//! Common utilities for Arrow Native functions
//!
//! This module provides reusable components for Arrow-based option pricing functions
//! to eliminate code duplication and ensure consistency.

use arrow::array::{BooleanArray, Float64Array};
use arrow::datatypes::{DataType, Field};
use arrow::error::ArrowError;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3_arrow::{error::PyArrowResult, PyArray};
use quantforge_core::constants::{
    MAX_PRICE, MAX_RATE, MAX_TIME, MAX_VOLATILITY, MIN_PRICE, MIN_RATE, MIN_TIME,
    MIN_VOLATILITY_PRACTICAL,
};
use std::sync::Arc;

use crate::utils::pyany_to_arrow;

/// Common parameter names for better maintainability
#[allow(dead_code)]
pub mod param_names {
    pub const PRICES: &str = "prices";
    pub const SPOTS: &str = "spots";
    pub const FORWARDS: &str = "forwards";
    pub const STRIKES: &str = "strikes";
    pub const TIMES: &str = "times";
    pub const RATES: &str = "rates";
    pub const SIGMAS: &str = "sigmas";
    pub const DIVIDEND_YIELDS: &str = "dividend_yields";
    pub const IS_CALLS: &str = "is_calls";
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
    pub const IMPLIED_VOLATILITY: &str = "implied_volatility";
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

/// Parameter set for Merton model
#[allow(dead_code)]
pub struct MertonParams {
    pub spots: PyArray,
    pub strikes: PyArray,
    pub times: PyArray,
    pub rates: PyArray,
    pub dividend_yields: PyArray,
    pub sigmas: PyArray,
}

/// Parameter set for implied volatility calculation
#[allow(dead_code)]
pub struct ImpliedVolatilityParams {
    pub prices: PyArray,
    pub is_calls: PyArray,
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

/// Validate scalar inputs with detailed error messages
#[inline(always)]
pub fn validate_scalar_inputs_detailed(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<()> {
    // Check for NaN and Inf first
    if s.is_nan() || !s.is_finite() {
        return Err(PyValueError::new_err(format!("spot must be finite (got {s})"))); 
    }
    if k.is_nan() || !k.is_finite() {
        return Err(PyValueError::new_err(format!("strike must be finite (got {k})"))); 
    }
    if t.is_nan() || !t.is_finite() {
        return Err(PyValueError::new_err(format!("time must be finite (got {t})"))); 
    }
    if r.is_nan() || !r.is_finite() {
        return Err(PyValueError::new_err(format!("rate must be finite (got {r})"))); 
    }
    if sigma.is_nan() || !sigma.is_finite() {
        return Err(PyValueError::new_err(format!("volatility must be finite (got {sigma})"))); 
    }

    // Check for positive values where required
    if s <= 0.0 {
        return Err(PyValueError::new_err(format!("spot must be positive (got {s})"))); 
    }
    if k <= 0.0 {
        return Err(PyValueError::new_err(format!("strike must be positive (got {k})"))); 
    }
    if t <= 0.0 {
        return Err(PyValueError::new_err(format!("time must be positive (got {t})"))); 
    }
    if sigma <= 0.0 {
        return Err(PyValueError::new_err(format!("volatility must be positive (got {sigma})"))); 
    }

    // Check valid ranges
    if s < MIN_PRICE || s >= MAX_PRICE {
        return Err(PyValueError::new_err(format!(
            "spot out of range [{MIN_PRICE}, {MAX_PRICE}) (got {s})"
        )));
    }
    if k < MIN_PRICE || k >= MAX_PRICE {
        return Err(PyValueError::new_err(format!(
            "strike out of range [{MIN_PRICE}, {MAX_PRICE}) (got {k})"
        )));
    }
    if t < MIN_TIME || t > MAX_TIME {
        return Err(PyValueError::new_err(format!(
            "time out of range [{MIN_TIME}, {MAX_TIME}] (got {t})"
        )));
    }
    if r < MIN_RATE || r > MAX_RATE {
        return Err(PyValueError::new_err(format!(
            "rate out of range [{MIN_RATE}, {MAX_RATE}] (got {r})"
        )));
    }
    if sigma < MIN_VOLATILITY_PRACTICAL || sigma > MAX_VOLATILITY {
        return Err(PyValueError::new_err(format!(
            "volatility out of range [{MIN_VOLATILITY_PRACTICAL}, {MAX_VOLATILITY}] (got {sigma})"
        )));
    }

    Ok(())
}

/// Validate Black76 scalar inputs with detailed error messages
#[inline(always)]
pub fn validate_black76_scalar_inputs_detailed(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<()> {
    // Check for NaN and Inf first
    if f.is_nan() || !f.is_finite() {
        return Err(PyValueError::new_err(format!("forward must be finite (got {f})"))); 
    }
    if k.is_nan() || !k.is_finite() {
        return Err(PyValueError::new_err(format!("strike must be finite (got {k})"))); 
    }
    if t.is_nan() || !t.is_finite() {
        return Err(PyValueError::new_err(format!("time must be finite (got {t})"))); 
    }
    if r.is_nan() || !r.is_finite() {
        return Err(PyValueError::new_err(format!("rate must be finite (got {r})"))); 
    }
    if sigma.is_nan() || !sigma.is_finite() {
        return Err(PyValueError::new_err(format!("volatility must be finite (got {sigma})"))); 
    }

    // Check for positive values where required
    if f <= 0.0 {
        return Err(PyValueError::new_err(format!("forward must be positive (got {f})"))); 
    }
    if k <= 0.0 {
        return Err(PyValueError::new_err(format!("strike must be positive (got {k})"))); 
    }
    if t <= 0.0 {
        return Err(PyValueError::new_err(format!("time must be positive (got {t})"))); 
    }
    if sigma <= 0.0 {
        return Err(PyValueError::new_err(format!("volatility must be positive (got {sigma})"))); 
    }

    // Check valid ranges
    if f < MIN_PRICE || f >= MAX_PRICE {
        return Err(PyValueError::new_err(format!(
            "forward out of range [{MIN_PRICE}, {MAX_PRICE}) (got {f})"
        )));
    }
    if k < MIN_PRICE || k >= MAX_PRICE {
        return Err(PyValueError::new_err(format!(
            "strike out of range [{MIN_PRICE}, {MAX_PRICE}) (got {k})"
        )));
    }
    if t < MIN_TIME || t > MAX_TIME {
        return Err(PyValueError::new_err(format!(
            "time out of range [{MIN_TIME}, {MAX_TIME}] (got {t})"
        )));
    }
    if r < MIN_RATE || r > MAX_RATE {
        return Err(PyValueError::new_err(format!(
            "rate out of range [{MIN_RATE}, {MAX_RATE}] (got {r})"
        )));
    }
    if sigma < MIN_VOLATILITY_PRACTICAL || sigma > MAX_VOLATILITY {
        return Err(PyValueError::new_err(format!(
            "volatility out of range [{MIN_VOLATILITY_PRACTICAL}, {MAX_VOLATILITY}] (got {sigma})"
        )));
    }

    Ok(())
}

/// Validate Black-Scholes array inputs
pub fn validate_black_scholes_arrays(
    spots: &Float64Array,
    strikes: &Float64Array,
    times: &Float64Array,
    sigmas: &Float64Array,
) -> Result<(), ArrowError> {
    // Check for NaN and negative values in spots
    for (i, &val) in spots.values().iter().enumerate() {
        if val.is_nan() || !val.is_finite() {
            return Err(ArrowError::ComputeError(format!(
                "spot must be finite (got {val} at index {i})"
            )));
        }
        if val <= 0.0 {
            return Err(ArrowError::ComputeError(format!(
                "spot must be positive (got {val} at index {i})"
            )));
        }
    }

    // Check for NaN and negative values in strikes
    for (i, &val) in strikes.values().iter().enumerate() {
        if val.is_nan() || !val.is_finite() {
            return Err(ArrowError::ComputeError(format!(
                "strike must be finite (got {val} at index {i})"
            )));
        }
        if val <= 0.0 {
            return Err(ArrowError::ComputeError(format!(
                "strike must be positive (got {val} at index {i})"
            )));
        }
    }

    // Check for NaN and negative values in times
    for (i, &val) in times.values().iter().enumerate() {
        if val.is_nan() || !val.is_finite() {
            return Err(ArrowError::ComputeError(format!(
                "time must be finite (got {val} at index {i})"
            )));
        }
        if val <= 0.0 {
            return Err(ArrowError::ComputeError(format!(
                "time must be positive (got {val} at index {i})"
            )));
        }
    }

    // Check for NaN and negative values in sigmas
    for (i, &val) in sigmas.values().iter().enumerate() {
        if val.is_nan() || !val.is_finite() {
            return Err(ArrowError::ComputeError(format!(
                "sigma must be finite (got {val} at index {i})"
            )));
        }
        if val <= 0.0 {
            return Err(ArrowError::ComputeError(format!(
                "sigma must be positive (got {val} at index {i})"
            )));
        }
    }

    Ok(())
}

/// Validate Black-Scholes array inputs with rate validation
pub fn validate_black_scholes_arrays_with_rates(
    spots: &Float64Array,
    strikes: &Float64Array,
    times: &Float64Array,
    rates: &Float64Array,
    sigmas: &Float64Array,
) -> Result<(), ArrowError> {
    // Validate main parameters
    validate_black_scholes_arrays(spots, strikes, times, sigmas)?;

    // Validate rates
    for (i, &val) in rates.values().iter().enumerate() {
        if val.is_nan() || !val.is_finite() {
            return Err(ArrowError::ComputeError(format!(
                "rate must be finite (got {val} at index {i})"
            )));
        }
        if val < MIN_RATE || val > MAX_RATE {
            return Err(ArrowError::ComputeError(format!(
                "rate out of range [{MIN_RATE}, {MAX_RATE}] (got {val} at index {i})"
            )));
        }
    }

    Ok(())
}

/// Validate Black76 array inputs
pub fn validate_black76_arrays(
    forwards: &Float64Array,
    strikes: &Float64Array,
    times: &Float64Array,
    sigmas: &Float64Array,
) -> Result<(), ArrowError> {
    // Check for NaN and negative values in forwards
    for (i, &val) in forwards.values().iter().enumerate() {
        if val.is_nan() || !val.is_finite() {
            return Err(ArrowError::ComputeError(format!(
                "forward must be finite (got {val} at index {i})"
            )));
        }
        if val <= 0.0 {
            return Err(ArrowError::ComputeError(format!(
                "forward must be positive (got {val} at index {i})"
            )));
        }
    }

    // Check for NaN and negative values in strikes
    for (i, &val) in strikes.values().iter().enumerate() {
        if val.is_nan() || !val.is_finite() {
            return Err(ArrowError::ComputeError(format!(
                "strike must be finite (got {val} at index {i})"
            )));
        }
        if val <= 0.0 {
            return Err(ArrowError::ComputeError(format!(
                "strike must be positive (got {val} at index {i})"
            )));
        }
    }

    // Check for NaN and negative values in times
    for (i, &val) in times.values().iter().enumerate() {
        if val.is_nan() || !val.is_finite() {
            return Err(ArrowError::ComputeError(format!(
                "time must be finite (got {val} at index {i})"
            )));
        }
        if val <= 0.0 {
            return Err(ArrowError::ComputeError(format!(
                "time must be positive (got {val} at index {i})"
            )));
        }
    }

    // Check for NaN and negative values in sigmas
    for (i, &val) in sigmas.values().iter().enumerate() {
        if val.is_nan() || !val.is_finite() {
            return Err(ArrowError::ComputeError(format!(
                "sigma must be finite (got {val} at index {i})"
            )));
        }
        if val <= 0.0 {
            return Err(ArrowError::ComputeError(format!(
                "sigma must be positive (got {val} at index {i})"
            )));
        }
    }

    Ok(())
}

/// Convert Python objects to Merton parameters
pub fn parse_merton_params(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    dividend_yields: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyResult<MertonParams> {
    Ok(MertonParams {
        spots: pyany_to_arrow(py, spots)?,
        strikes: pyany_to_arrow(py, strikes)?,
        times: pyany_to_arrow(py, times)?,
        rates: pyany_to_arrow(py, rates)?,
        dividend_yields: pyany_to_arrow(py, dividend_yields)?,
        sigmas: pyany_to_arrow(py, sigmas)?,
    })
}

/// Parse is_calls parameter (handle both scalar bool and array)
pub fn parse_is_calls_param(_py: Python, is_calls: &Bound<'_, PyAny>) -> PyResult<PyArray> {
    // Try to extract as bool first (scalar case)
    if let Ok(scalar_bool) = is_calls.extract::<bool>() {
        // Create a single-element boolean array
        let bool_array = BooleanArray::from(vec![scalar_bool]);
        let field = Arc::new(Field::new(param_names::IS_CALLS, DataType::Boolean, false));
        Ok(PyArray::new(Arc::new(bool_array), field))
    } else {
        // Try to extract as PyArray
        if let Ok(array) = is_calls.extract::<PyArray>() {
            return Ok(array);
        }

        // Check if it has a tolist method (likely a NumPy array)
        if is_calls.hasattr("tolist")? {
            // Convert NumPy array to Python list, then to Arrow array
            let py_list = is_calls.call_method0("tolist")?;
            if let Ok(vec) = py_list.extract::<Vec<bool>>() {
                let bool_array = BooleanArray::from(vec);
                let field = Arc::new(Field::new(param_names::IS_CALLS, DataType::Boolean, false));
                return Ok(PyArray::new(Arc::new(bool_array), field));
            }
            // Try single value from 1-element array
            if let Ok(scalar) = py_list.extract::<bool>() {
                let bool_array = BooleanArray::from(vec![scalar]);
                let field = Arc::new(Field::new(param_names::IS_CALLS, DataType::Boolean, false));
                return Ok(PyArray::new(Arc::new(bool_array), field));
            }
        }

        Err(PyValueError::new_err(format!(
            "Expected bool, numpy array, or arrow array for is_calls, got {}",
            is_calls.get_type().name()?
        )))
    }
}

/// Extract BooleanArray from PyArray
pub fn extract_boolean_array(py_array: &PyArray) -> Result<&BooleanArray, ArrowError> {
    py_array
        .as_ref()
        .as_any()
        .downcast_ref::<BooleanArray>()
        .ok_or_else(|| ArrowError::CastError("is_calls must be BooleanArray".to_string()))
}
