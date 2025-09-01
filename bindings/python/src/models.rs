//! Arrow-native model implementations with Python bindings

use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::arrow_convert::{
    all_same_length, arrayref_to_numpy, broadcast_to_length, find_broadcast_length,
    numpy_to_arrow_direct,
};
use crate::error::arrow_to_py_err;

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
    // Direct scalar computation to avoid array overhead
    use quantforge_core::math::distributions::norm_cdf;

    // Validate inputs
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "s, k, t, and sigma must be positive",
        ));
    }

    // Black-Scholes formula (direct scalar computation)
    let sqrt_t = t.sqrt();
    let d1 = ((s / k).ln() + (r + sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;

    let call_price = s * norm_cdf(d1) - k * (-r * t).exp() * norm_cdf(d2);

    Ok(call_price)
}

/// Calculate Black-Scholes put option price (scalar)
#[pyfunction]
#[pyo3(signature = (s, k, t, r, sigma))]
pub fn put_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // Direct scalar computation to avoid array overhead
    use quantforge_core::math::distributions::norm_cdf;

    // Validate inputs
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "s, k, t, and sigma must be positive",
        ));
    }

    // Black-Scholes formula (direct scalar computation)
    let sqrt_t = t.sqrt();
    let d1 = ((s / k).ln() + (r + sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;

    let put_price = k * (-r * t).exp() * norm_cdf(-d2) - s * norm_cdf(-d1);

    Ok(put_price)
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
    // Check if all arrays have the same length (Fast Path)
    let arrays = vec![&spots, &strikes, &times, &rates, &sigmas];

    if all_same_length(&arrays) {
        // Fast Path: Direct conversion without broadcasting
        let spots_arrow = numpy_to_arrow_direct(spots).map_err(arrow_to_py_err)?;
        let strikes_arrow = numpy_to_arrow_direct(strikes).map_err(arrow_to_py_err)?;
        let times_arrow = numpy_to_arrow_direct(times).map_err(arrow_to_py_err)?;
        let rates_arrow = numpy_to_arrow_direct(rates).map_err(arrow_to_py_err)?;
        let sigmas_arrow = numpy_to_arrow_direct(sigmas).map_err(arrow_to_py_err)?;

        // Release GIL for computation
        let result = py
            .allow_threads(|| {
                BlackScholes::call_price(
                    &spots_arrow,
                    &strikes_arrow,
                    &times_arrow,
                    &rates_arrow,
                    &sigmas_arrow,
                )
            })
            .map_err(arrow_to_py_err)?;

        return arrayref_to_numpy(py, result);
    }

    // Regular Path: Need broadcasting
    let target_len = find_broadcast_length(&arrays).map_err(arrow_to_py_err)?;

    // Broadcast all arrays to same length
    let spots_arrow = broadcast_to_length(spots, target_len).map_err(arrow_to_py_err)?;
    let strikes_arrow = broadcast_to_length(strikes, target_len).map_err(arrow_to_py_err)?;
    let times_arrow = broadcast_to_length(times, target_len).map_err(arrow_to_py_err)?;
    let rates_arrow = broadcast_to_length(rates, target_len).map_err(arrow_to_py_err)?;
    let sigmas_arrow = broadcast_to_length(sigmas, target_len).map_err(arrow_to_py_err)?;

    // Release GIL for computation
    let result = py
        .allow_threads(|| {
            BlackScholes::call_price(
                &spots_arrow,
                &strikes_arrow,
                &times_arrow,
                &rates_arrow,
                &sigmas_arrow,
            )
        })
        .map_err(arrow_to_py_err)?;

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
    // Check if all arrays have the same length (Fast Path)
    let arrays = vec![&spots, &strikes, &times, &rates, &sigmas];

    if all_same_length(&arrays) {
        // Fast Path: Direct conversion without broadcasting
        let spots_arrow = numpy_to_arrow_direct(spots).map_err(arrow_to_py_err)?;
        let strikes_arrow = numpy_to_arrow_direct(strikes).map_err(arrow_to_py_err)?;
        let times_arrow = numpy_to_arrow_direct(times).map_err(arrow_to_py_err)?;
        let rates_arrow = numpy_to_arrow_direct(rates).map_err(arrow_to_py_err)?;
        let sigmas_arrow = numpy_to_arrow_direct(sigmas).map_err(arrow_to_py_err)?;

        // Release GIL for computation
        let result = py
            .allow_threads(|| {
                BlackScholes::put_price(
                    &spots_arrow,
                    &strikes_arrow,
                    &times_arrow,
                    &rates_arrow,
                    &sigmas_arrow,
                )
            })
            .map_err(arrow_to_py_err)?;

        return arrayref_to_numpy(py, result);
    }

    // Regular Path: Need broadcasting
    let target_len = find_broadcast_length(&arrays).map_err(arrow_to_py_err)?;

    // Broadcast all arrays to same length
    let spots_arrow = broadcast_to_length(spots, target_len).map_err(arrow_to_py_err)?;
    let strikes_arrow = broadcast_to_length(strikes, target_len).map_err(arrow_to_py_err)?;
    let times_arrow = broadcast_to_length(times, target_len).map_err(arrow_to_py_err)?;
    let rates_arrow = broadcast_to_length(rates, target_len).map_err(arrow_to_py_err)?;
    let sigmas_arrow = broadcast_to_length(sigmas, target_len).map_err(arrow_to_py_err)?;

    // Release GIL for computation
    let result = py
        .allow_threads(|| {
            BlackScholes::put_price(
                &spots_arrow,
                &strikes_arrow,
                &times_arrow,
                &rates_arrow,
                &sigmas_arrow,
            )
        })
        .map_err(arrow_to_py_err)?;

    // Convert result back to NumPy
    arrayref_to_numpy(py, result)
}

/// Calculate Black-Scholes call option price (batch) WITHOUT validation
///
/// ⚠️ WARNING: This function skips input validation for performance.
/// Use only when inputs are pre-validated. Invalid inputs may cause
/// incorrect results or undefined behavior.
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
pub fn call_price_batch_unsafe<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    strikes: PyReadonlyArray1<f64>,
    times: PyReadonlyArray1<f64>,
    rates: PyReadonlyArray1<f64>,
    sigmas: PyReadonlyArray1<f64>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // Check if all arrays have the same length (Fast Path)
    let arrays = vec![&spots, &strikes, &times, &rates, &sigmas];

    if all_same_length(&arrays) {
        // Fast Path: Direct conversion without broadcasting
        let spots_arrow = numpy_to_arrow_direct(spots).map_err(arrow_to_py_err)?;
        let strikes_arrow = numpy_to_arrow_direct(strikes).map_err(arrow_to_py_err)?;
        let times_arrow = numpy_to_arrow_direct(times).map_err(arrow_to_py_err)?;
        let rates_arrow = numpy_to_arrow_direct(rates).map_err(arrow_to_py_err)?;
        let sigmas_arrow = numpy_to_arrow_direct(sigmas).map_err(arrow_to_py_err)?;

        // Release GIL for computation (using unchecked version)
        let result = py
            .allow_threads(|| {
                BlackScholes::call_price_unchecked(
                    &spots_arrow,
                    &strikes_arrow,
                    &times_arrow,
                    &rates_arrow,
                    &sigmas_arrow,
                )
            })
            .map_err(arrow_to_py_err)?;

        return arrayref_to_numpy(py, result);
    }

    // Regular Path: Need broadcasting
    let target_len = find_broadcast_length(&arrays).map_err(arrow_to_py_err)?;

    // Broadcast all arrays to same length
    let spots_arrow = broadcast_to_length(spots, target_len).map_err(arrow_to_py_err)?;
    let strikes_arrow = broadcast_to_length(strikes, target_len).map_err(arrow_to_py_err)?;
    let times_arrow = broadcast_to_length(times, target_len).map_err(arrow_to_py_err)?;
    let rates_arrow = broadcast_to_length(rates, target_len).map_err(arrow_to_py_err)?;
    let sigmas_arrow = broadcast_to_length(sigmas, target_len).map_err(arrow_to_py_err)?;

    // Release GIL for computation (using unchecked version)
    let result = py
        .allow_threads(|| {
            BlackScholes::call_price_unchecked(
                &spots_arrow,
                &strikes_arrow,
                &times_arrow,
                &rates_arrow,
                &sigmas_arrow,
            )
        })
        .map_err(arrow_to_py_err)?;

    // Convert result back to NumPy
    arrayref_to_numpy(py, result)
}

/// Calculate Black-Scholes put option price (batch) WITHOUT validation
///
/// ⚠️ WARNING: This function skips input validation for performance.
/// Use only when inputs are pre-validated. Invalid inputs may cause
/// incorrect results or undefined behavior.
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
pub fn put_price_batch_unsafe<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    strikes: PyReadonlyArray1<f64>,
    times: PyReadonlyArray1<f64>,
    rates: PyReadonlyArray1<f64>,
    sigmas: PyReadonlyArray1<f64>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // Check if all arrays have the same length (Fast Path)
    let arrays = vec![&spots, &strikes, &times, &rates, &sigmas];

    if all_same_length(&arrays) {
        // Fast Path: Direct conversion without broadcasting
        let spots_arrow = numpy_to_arrow_direct(spots).map_err(arrow_to_py_err)?;
        let strikes_arrow = numpy_to_arrow_direct(strikes).map_err(arrow_to_py_err)?;
        let times_arrow = numpy_to_arrow_direct(times).map_err(arrow_to_py_err)?;
        let rates_arrow = numpy_to_arrow_direct(rates).map_err(arrow_to_py_err)?;
        let sigmas_arrow = numpy_to_arrow_direct(sigmas).map_err(arrow_to_py_err)?;

        // Release GIL for computation (using unchecked version)
        let result = py
            .allow_threads(|| {
                BlackScholes::put_price_unchecked(
                    &spots_arrow,
                    &strikes_arrow,
                    &times_arrow,
                    &rates_arrow,
                    &sigmas_arrow,
                )
            })
            .map_err(arrow_to_py_err)?;

        return arrayref_to_numpy(py, result);
    }

    // Regular Path: Need broadcasting
    let target_len = find_broadcast_length(&arrays).map_err(arrow_to_py_err)?;

    // Broadcast all arrays to same length
    let spots_arrow = broadcast_to_length(spots, target_len).map_err(arrow_to_py_err)?;
    let strikes_arrow = broadcast_to_length(strikes, target_len).map_err(arrow_to_py_err)?;
    let times_arrow = broadcast_to_length(times, target_len).map_err(arrow_to_py_err)?;
    let rates_arrow = broadcast_to_length(rates, target_len).map_err(arrow_to_py_err)?;
    let sigmas_arrow = broadcast_to_length(sigmas, target_len).map_err(arrow_to_py_err)?;

    // Release GIL for computation (using unchecked version)
    let result = py
        .allow_threads(|| {
            BlackScholes::put_price_unchecked(
                &spots_arrow,
                &strikes_arrow,
                &times_arrow,
                &rates_arrow,
                &sigmas_arrow,
            )
        })
        .map_err(arrow_to_py_err)?;

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
    // Direct scalar computation to avoid array overhead
    use quantforge_core::math::distributions::{norm_cdf, norm_pdf};

    // Validate inputs
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "s, k, t, and sigma must be positive",
        ));
    }

    // Calculate d1 and d2
    let sqrt_t = t.sqrt();
    let d1 = ((s / k).ln() + (r + sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;

    // Calculate Greeks
    let n_d1 = norm_cdf(d1);
    let n_d2 = norm_cdf(d2);
    let phi_d1 = norm_pdf(d1);

    // Delta
    let delta = if is_call { n_d1 } else { n_d1 - 1.0 };

    // Gamma (same for call and put)
    let gamma = phi_d1 / (s * sigma * sqrt_t);

    // Vega (same for call and put)
    let vega = s * phi_d1 * sqrt_t / 100.0; // Divide by 100 for convention

    // Theta
    let term1 = -s * phi_d1 * sigma / (2.0 * sqrt_t);
    let theta = if is_call {
        (term1 - r * k * (-r * t).exp() * n_d2) / 365.0 // Daily theta
    } else {
        (term1 + r * k * (-r * t).exp() * norm_cdf(-d2)) / 365.0
    };

    // Rho
    let rho = if is_call {
        k * t * (-r * t).exp() * n_d2 / 100.0 // Divide by 100 for convention
    } else {
        -k * t * (-r * t).exp() * norm_cdf(-d2) / 100.0
    };

    // Create Python dict with scalar values
    let dict = PyDict::new(py);
    dict.set_item("delta", delta)?;
    dict.set_item("gamma", gamma)?;
    dict.set_item("vega", vega)?;
    dict.set_item("theta", theta)?;
    dict.set_item("rho", rho)?;

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
    let greeks_struct = py
        .allow_threads(|| {
            calculate_greeks(
                "black_scholes",
                &spots_arrow,
                &strikes_arrow,
                &times_arrow,
                &rates_arrow,
                &sigmas_arrow,
                is_call,
            )
        })
        .map_err(arrow_to_py_err)?;

    // Create Python dict with NumPy arrays
    let dict = PyDict::new(py);

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
    use quantforge_core::math::distributions::{norm_cdf, norm_pdf};

    // Validate inputs
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || price <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "price, s, k, and t must be positive",
        ));
    }

    // Check for arbitrage violations
    let intrinsic = if is_call {
        (s - k * (-r * t).exp()).max(0.0)
    } else {
        (k * (-r * t).exp() - s).max(0.0)
    };

    if price < intrinsic {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Option price violates arbitrage bounds",
        ));
    }

    // Newton-Raphson method for implied volatility
    let mut sigma = 0.2; // Initial guess
    let tolerance = 1e-6;
    let max_iterations = 50;

    for _ in 0..max_iterations {
        // Calculate option price with current sigma
        let sqrt_t = t.sqrt();
        let d1 = ((s / k).ln() + (r + sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
        let d2 = d1 - sigma * sqrt_t;

        let computed_price = if is_call {
            s * norm_cdf(d1) - k * (-r * t).exp() * norm_cdf(d2)
        } else {
            k * (-r * t).exp() * norm_cdf(-d2) - s * norm_cdf(-d1)
        };

        // Calculate vega (derivative with respect to sigma)
        let vega = s * norm_pdf(d1) * sqrt_t;

        // Check for convergence
        let diff = computed_price - price;
        if diff.abs() < tolerance {
            return Ok(sigma);
        }

        // Newton-Raphson update
        sigma -= diff / vega;

        // Keep sigma in reasonable bounds
        sigma = sigma.max(0.001).min(5.0);
    }

    Err(pyo3::exceptions::PyRuntimeError::new_err(
        "Implied volatility failed to converge",
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
        "Batch implied volatility not yet implemented in Arrow-native version",
    ))
}

// ============================================================================
// Black76 Model (Futures)
// ============================================================================

/// Calculate Black76 call option price (scalar)
#[pyfunction]
#[pyo3(name = "call_price")]
#[pyo3(signature = (f, k, t, r, sigma))]
pub fn black76_call_price(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // TODO: Implement using Arrow-native Black76 kernel from core
    Err(pyo3::exceptions::PyNotImplementedError::new_err(
        "Black76 not yet implemented in Arrow-native version",
    ))
}

/// Calculate Black76 put option price (scalar)
#[pyfunction]
#[pyo3(name = "put_price")]
#[pyo3(signature = (f, k, t, r, sigma))]
pub fn black76_put_price(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // TODO: Implement using Arrow-native Black76 kernel from core
    Err(pyo3::exceptions::PyNotImplementedError::new_err(
        "Black76 not yet implemented in Arrow-native version",
    ))
}

// ============================================================================
// Merton Model (Dividends)
// ============================================================================

/// Calculate Merton model call option price (scalar)
#[pyfunction]
#[pyo3(name = "call_price")]
#[pyo3(signature = (s, k, t, r, q, sigma))]
pub fn merton_call_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    // TODO: Implement using Arrow-native Merton kernel from core
    Err(pyo3::exceptions::PyNotImplementedError::new_err(
        "Merton model not yet implemented in Arrow-native version",
    ))
}

/// Calculate Merton model put option price (scalar)
#[pyfunction]
#[pyo3(name = "put_price")]
#[pyo3(signature = (s, k, t, r, q, sigma))]
pub fn merton_put_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    // TODO: Implement using Arrow-native Merton kernel from core
    Err(pyo3::exceptions::PyNotImplementedError::new_err(
        "Merton model not yet implemented in Arrow-native version",
    ))
}

// ============================================================================
// American Options
// ============================================================================

/// Calculate American call option price (scalar)
#[pyfunction]
#[pyo3(name = "call_price")]
#[pyo3(signature = (s, k, t, r, sigma))]
pub fn american_call_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // TODO: Implement using Arrow-native American kernel from core
    Err(pyo3::exceptions::PyNotImplementedError::new_err(
        "American options not yet implemented in Arrow-native version",
    ))
}

/// Calculate American put option price (scalar)
#[pyfunction]
#[pyo3(name = "put_price")]
#[pyo3(signature = (s, k, t, r, sigma))]
pub fn american_put_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // TODO: Implement using Arrow-native American kernel from core
    Err(pyo3::exceptions::PyNotImplementedError::new_err(
        "American options not yet implemented in Arrow-native version",
    ))
}
