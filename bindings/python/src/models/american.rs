//! American option model Python bindings

use numpy::PyArray1;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use quantforge_core::models::american::American;
use quantforge_core::traits::Greeks;

use crate::converters::{ArrayLike, BroadcastIterator};
use crate::error::to_py_err;

/// Create the american Python module
pub fn create_module(py: Python<'_>) -> PyResult<Bound<'_, PyModule>> {
    let m = PyModule::new_bound(py, "american")?;

    // Register functions
    m.add_function(wrap_pyfunction!(call_price, &m)?)?;
    m.add_function(wrap_pyfunction!(put_price, &m)?)?;
    m.add_function(wrap_pyfunction!(implied_volatility, &m)?)?;
    m.add_function(wrap_pyfunction!(greeks, &m)?)?;

    // Batch functions
    m.add_function(wrap_pyfunction!(call_price_batch, &m)?)?;
    m.add_function(wrap_pyfunction!(put_price_batch, &m)?)?;
    m.add_function(wrap_pyfunction!(implied_volatility_batch, &m)?)?;
    m.add_function(wrap_pyfunction!(greeks_batch, &m)?)?;

    Ok(m)
}

/// Calculate American call option price
#[pyfunction]
#[pyo3(signature = (s, k, t, r, q, sigma))]
fn call_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    American::call_price_american(s, k, t, r, q, sigma).map_err(to_py_err)
}

/// Calculate American put option price
#[pyfunction]
#[pyo3(signature = (s, k, t, r, q, sigma))]
fn put_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    American::put_price_american(s, k, t, r, q, sigma).map_err(to_py_err)
}

/// Calculate implied volatility using American model
#[pyfunction]
#[pyo3(signature = (price, s, k, t, r, q, is_call))]
fn implied_volatility(
    price: f64,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    is_call: bool,
) -> PyResult<f64> {
    American::implied_volatility_american(price, s, k, t, r, q, is_call).map_err(to_py_err)
}

/// Calculate Greeks for American model
#[pyfunction]
#[pyo3(signature = (s, k, t, r, q, sigma, is_call=true))]
fn greeks<'py>(
    py: Python<'py>,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    is_call: bool,
) -> PyResult<Bound<'py, PyDict>> {
    let greeks = American::greeks_american(s, k, t, r, q, sigma, is_call).map_err(to_py_err)?;

    let dict = PyDict::new_bound(py);
    dict.set_item("delta", greeks.delta)?;
    dict.set_item("gamma", greeks.gamma)?;
    dict.set_item("vega", greeks.vega)?;
    dict.set_item("theta", greeks.theta)?;
    dict.set_item("rho", greeks.rho)?;
    if let Some(dividend_rho) = greeks.dividend_rho {
        dict.set_item("dividend_rho", dividend_rho)?;
    }

    Ok(dict)
}

/// Batch calculation of American call prices
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, dividend_yields, sigmas))]
fn call_price_batch<'py>(
    py: Python<'py>,
    spots: ArrayLike<'py>,
    strikes: ArrayLike<'py>,
    times: ArrayLike<'py>,
    rates: ArrayLike<'py>,
    dividend_yields: ArrayLike<'py>,
    sigmas: ArrayLike<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // Create broadcast iterator and collect input data (while holding GIL)
    let inputs = vec![&spots, &strikes, &times, &rates, &dividend_yields, &sigmas];
    let iter = BroadcastIterator::new(inputs).map_err(pyo3::exceptions::PyValueError::new_err)?;

    // Collect all input combinations
    let input_data: Vec<Vec<f64>> = iter.collect();
    let len = input_data.len();

    // Prepare data arrays
    let mut spots_vec = Vec::with_capacity(len);
    let mut strikes_vec = Vec::with_capacity(len);
    let mut times_vec = Vec::with_capacity(len);
    let mut rates_vec = Vec::with_capacity(len);
    let mut dividend_yields_vec = Vec::with_capacity(len);
    let mut sigmas_vec = Vec::with_capacity(len);

    for values in input_data {
        spots_vec.push(values[0]);
        strikes_vec.push(values[1]);
        times_vec.push(values[2]);
        rates_vec.push(values[3]);
        dividend_yields_vec.push(values[4]);
        sigmas_vec.push(values[5]);
    }

    // Release GIL for computation
    let results = py.allow_threads(move || {
        // For now, use sequential processing for American options
        // TODO: Implement optimized batch processing
        let mut results = Vec::with_capacity(len);

        for i in 0..len {
            let price = American::call_price_american(
                spots_vec[i],
                strikes_vec[i],
                times_vec[i],
                rates_vec[i],
                dividend_yields_vec[i],
                sigmas_vec[i],
            )
            .unwrap_or(f64::NAN);
            results.push(price);
        }

        results
    });

    Ok(PyArray1::from_vec_bound(py, results))
}

/// Batch calculation of American put prices
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, dividend_yields, sigmas))]
fn put_price_batch<'py>(
    py: Python<'py>,
    spots: ArrayLike<'py>,
    strikes: ArrayLike<'py>,
    times: ArrayLike<'py>,
    rates: ArrayLike<'py>,
    dividend_yields: ArrayLike<'py>,
    sigmas: ArrayLike<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // Create broadcast iterator and collect input data (while holding GIL)
    let inputs = vec![&spots, &strikes, &times, &rates, &dividend_yields, &sigmas];
    let iter = BroadcastIterator::new(inputs).map_err(pyo3::exceptions::PyValueError::new_err)?;

    // Collect all input combinations
    let input_data: Vec<Vec<f64>> = iter.collect();
    let len = input_data.len();

    // Prepare data arrays
    let mut spots_vec = Vec::with_capacity(len);
    let mut strikes_vec = Vec::with_capacity(len);
    let mut times_vec = Vec::with_capacity(len);
    let mut rates_vec = Vec::with_capacity(len);
    let mut dividend_yields_vec = Vec::with_capacity(len);
    let mut sigmas_vec = Vec::with_capacity(len);

    for values in input_data {
        spots_vec.push(values[0]);
        strikes_vec.push(values[1]);
        times_vec.push(values[2]);
        rates_vec.push(values[3]);
        dividend_yields_vec.push(values[4]);
        sigmas_vec.push(values[5]);
    }

    // Release GIL for computation
    let results = py.allow_threads(move || {
        // For now, use sequential processing for American options
        // TODO: Implement optimized batch processing
        let mut results = Vec::with_capacity(len);

        for i in 0..len {
            let price = American::put_price_american(
                spots_vec[i],
                strikes_vec[i],
                times_vec[i],
                rates_vec[i],
                dividend_yields_vec[i],
                sigmas_vec[i],
            )
            .unwrap_or(f64::NAN);
            results.push(price);
        }

        results
    });

    Ok(PyArray1::from_vec_bound(py, results))
}

/// Batch calculation of implied volatility
#[pyfunction]
#[pyo3(signature = (prices, spots, strikes, times, rates, dividend_yields, is_calls))]
fn implied_volatility_batch<'py>(
    py: Python<'py>,
    prices: ArrayLike<'py>,
    spots: ArrayLike<'py>,
    strikes: ArrayLike<'py>,
    times: ArrayLike<'py>,
    rates: ArrayLike<'py>,
    dividend_yields: ArrayLike<'py>,
    is_calls: ArrayLike<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // Create broadcast iterator and collect input data (while holding GIL)
    let inputs = vec![
        &prices,
        &spots,
        &strikes,
        &times,
        &rates,
        &dividend_yields,
        &is_calls,
    ];
    let iter = BroadcastIterator::new(inputs).map_err(pyo3::exceptions::PyValueError::new_err)?;

    // Collect all input combinations
    let input_data: Vec<Vec<f64>> = iter.collect();
    let len = input_data.len();

    // Prepare data arrays
    let mut prices_vec = Vec::with_capacity(len);
    let mut spots_vec = Vec::with_capacity(len);
    let mut strikes_vec = Vec::with_capacity(len);
    let mut times_vec = Vec::with_capacity(len);
    let mut rates_vec = Vec::with_capacity(len);
    let mut dividend_yields_vec = Vec::with_capacity(len);
    let mut is_calls_vec = Vec::with_capacity(len);

    for values in input_data {
        prices_vec.push(values[0]);
        spots_vec.push(values[1]);
        strikes_vec.push(values[2]);
        times_vec.push(values[3]);
        rates_vec.push(values[4]);
        dividend_yields_vec.push(values[5]);
        is_calls_vec.push(values[6] != 0.0);
    }

    // Release GIL for computation
    let results = py.allow_threads(move || {
        let mut results = Vec::with_capacity(len);

        for i in 0..len {
            let iv = American::implied_volatility_american(
                prices_vec[i],
                spots_vec[i],
                strikes_vec[i],
                times_vec[i],
                rates_vec[i],
                dividend_yields_vec[i],
                is_calls_vec[i],
            )
            .unwrap_or(f64::NAN);
            results.push(iv);
        }

        results
    });

    Ok(PyArray1::from_vec_bound(py, results))
}

/// Batch calculation of Greeks
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, dividend_yields, sigmas, is_calls=None))]
fn greeks_batch<'py>(
    py: Python<'py>,
    spots: ArrayLike<'py>,
    strikes: ArrayLike<'py>,
    times: ArrayLike<'py>,
    rates: ArrayLike<'py>,
    dividend_yields: ArrayLike<'py>,
    sigmas: ArrayLike<'py>,
    is_calls: Option<ArrayLike<'py>>,
) -> PyResult<Bound<'py, PyDict>> {
    // Convert is_calls to bool vec (while holding GIL), default to all Calls
    let is_calls_vec: Vec<bool> = if let Some(is_calls_array) = is_calls {
        is_calls_array
            .to_vec()?
            .into_iter()
            .map(|v| v != 0.0)
            .collect()
    } else {
        vec![true; 1] // Will be broadcast to match input size
    };

    // Create broadcast iterator and collect input data
    let inputs = vec![&spots, &strikes, &times, &rates, &dividend_yields, &sigmas];
    let iter = BroadcastIterator::new(inputs).map_err(pyo3::exceptions::PyValueError::new_err)?;

    // Collect all input combinations
    let input_data: Vec<Vec<f64>> = iter.collect();
    let len = input_data.len();

    // Prepare data arrays
    let mut spots_vec = Vec::with_capacity(len);
    let mut strikes_vec = Vec::with_capacity(len);
    let mut times_vec = Vec::with_capacity(len);
    let mut rates_vec = Vec::with_capacity(len);
    let mut dividend_yields_vec = Vec::with_capacity(len);
    let mut sigmas_vec = Vec::with_capacity(len);

    for values in input_data {
        spots_vec.push(values[0]);
        strikes_vec.push(values[1]);
        times_vec.push(values[2]);
        rates_vec.push(values[3]);
        dividend_yields_vec.push(values[4]);
        sigmas_vec.push(values[5]);
    }

    // Release GIL for computation
    let (delta_vec, gamma_vec, vega_vec, theta_vec, rho_vec, dividend_rho_vec) =
        py.allow_threads(move || {
            let mut delta_vec = Vec::with_capacity(len);
            let mut gamma_vec = Vec::with_capacity(len);
            let mut vega_vec = Vec::with_capacity(len);
            let mut theta_vec = Vec::with_capacity(len);
            let mut rho_vec = Vec::with_capacity(len);
            let mut dividend_rho_vec = Vec::with_capacity(len);

            for i in 0..len {
                let is_call = is_calls_vec.get(i).copied().unwrap_or(true);
                let greeks = American::greeks_american(
                    spots_vec[i],
                    strikes_vec[i],
                    times_vec[i],
                    rates_vec[i],
                    dividend_yields_vec[i],
                    sigmas_vec[i],
                    is_call,
                )
                .unwrap_or(Greeks {
                    delta: f64::NAN,
                    gamma: f64::NAN,
                    vega: f64::NAN,
                    theta: f64::NAN,
                    rho: f64::NAN,
                    dividend_rho: Some(f64::NAN),
                });

                delta_vec.push(greeks.delta);
                gamma_vec.push(greeks.gamma);
                vega_vec.push(greeks.vega);
                theta_vec.push(greeks.theta);
                rho_vec.push(greeks.rho);
                dividend_rho_vec.push(greeks.dividend_rho.unwrap_or(f64::NAN));
            }

            (
                delta_vec,
                gamma_vec,
                vega_vec,
                theta_vec,
                rho_vec,
                dividend_rho_vec,
            )
        });

    // Create output dictionary
    let dict = PyDict::new_bound(py);
    dict.set_item("delta", PyArray1::from_vec_bound(py, delta_vec))?;
    dict.set_item("gamma", PyArray1::from_vec_bound(py, gamma_vec))?;
    dict.set_item("vega", PyArray1::from_vec_bound(py, vega_vec))?;
    dict.set_item("theta", PyArray1::from_vec_bound(py, theta_vec))?;
    dict.set_item("rho", PyArray1::from_vec_bound(py, rho_vec))?;
    dict.set_item(
        "dividend_rho",
        PyArray1::from_vec_bound(py, dividend_rho_vec),
    )?;

    Ok(dict)
}
