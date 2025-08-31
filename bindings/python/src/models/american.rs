//! American model Python bindings

use numpy::PyArray1;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use quantforge_core::constants::{CHUNK_SIZE_L1, PARALLEL_THRESHOLD_SMALL};
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
#[pyo3(signature = (s, k, t, r, q, sigma, is_call))]
#[allow(clippy::too_many_arguments)]
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
    // Create broadcast iterator (while holding GIL)
    let inputs = vec![&spots, &strikes, &times, &rates, &dividend_yields, &sigmas];
    let iter =
        BroadcastIterator::new(inputs).map_err(pyo3::exceptions::PyValueError::new_err)?;

    // Release GIL and use zero-copy computation
    let results = py.allow_threads(move || {
        if iter.len() < PARALLEL_THRESHOLD_SMALL {
            // Sequential processing for small data
            iter.compute_with(|values| {
                American::call_price_american(
                    values[0], values[1], values[2], values[3], values[4], values[5],
                )
                .unwrap_or(f64::NAN)
            })
        } else {
            // Parallel processing for large data
            iter.compute_parallel_with(
                |values| {
                    American::call_price_american(
                        values[0], values[1], values[2], values[3], values[4], values[5],
                    )
                    .unwrap_or(f64::NAN)
                },
                CHUNK_SIZE_L1,
            )
        }
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
    // Create broadcast iterator (while holding GIL)
    let inputs = vec![&spots, &strikes, &times, &rates, &dividend_yields, &sigmas];
    let iter =
        BroadcastIterator::new(inputs).map_err(pyo3::exceptions::PyValueError::new_err)?;

    // Release GIL and use zero-copy computation
    let results = py.allow_threads(move || {
        if iter.len() < PARALLEL_THRESHOLD_SMALL {
            // Sequential processing for small data
            iter.compute_with(|values| {
                American::put_price_american(
                    values[0], values[1], values[2], values[3], values[4], values[5],
                )
                .unwrap_or(f64::NAN)
            })
        } else {
            // Parallel processing for large data
            iter.compute_parallel_with(
                |values| {
                    American::put_price_american(
                        values[0], values[1], values[2], values[3], values[4], values[5],
                    )
                    .unwrap_or(f64::NAN)
                },
                CHUNK_SIZE_L1,
            )
        }
    });

    Ok(PyArray1::from_vec_bound(py, results))
}

/// Batch calculation of implied volatilities
#[pyfunction]
#[pyo3(signature = (prices, spots, strikes, times, rates, dividend_yields, is_call))]
fn implied_volatility_batch<'py>(
    py: Python<'py>,
    prices: ArrayLike<'py>,
    spots: ArrayLike<'py>,
    strikes: ArrayLike<'py>,
    times: ArrayLike<'py>,
    rates: ArrayLike<'py>,
    dividend_yields: ArrayLike<'py>,
    is_call: bool,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // Create broadcast iterator (while holding GIL)
    let inputs = vec![&prices, &spots, &strikes, &times, &rates, &dividend_yields];
    let iter =
        BroadcastIterator::new(inputs).map_err(pyo3::exceptions::PyValueError::new_err)?;

    // Release GIL and use zero-copy computation
    let results = py.allow_threads(move || {
        if iter.len() < PARALLEL_THRESHOLD_SMALL {
            // Sequential processing for small data
            iter.compute_with(|values| {
                American::implied_volatility_american(
                    values[0], values[1], values[2], values[3], values[4], values[5], is_call,
                )
                .unwrap_or(f64::NAN)
            })
        } else {
            // Parallel processing for large data
            iter.compute_parallel_with(
                |values| {
                    American::implied_volatility_american(
                        values[0], values[1], values[2], values[3], values[4], values[5], is_call,
                    )
                    .unwrap_or(f64::NAN)
                },
                CHUNK_SIZE_L1,
            )
        }
    });

    Ok(PyArray1::from_vec_bound(py, results))
}

/// Batch calculation of Greeks
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, dividend_yields, sigmas, is_call))]
#[allow(clippy::too_many_arguments)]
fn greeks_batch<'py>(
    py: Python<'py>,
    spots: ArrayLike<'py>,
    strikes: ArrayLike<'py>,
    times: ArrayLike<'py>,
    rates: ArrayLike<'py>,
    dividend_yields: ArrayLike<'py>,
    sigmas: ArrayLike<'py>,
    is_call: bool,
) -> PyResult<Bound<'py, PyDict>> {
    // Create broadcast iterator (while holding GIL)
    let inputs = vec![&spots, &strikes, &times, &rates, &dividend_yields, &sigmas];
    let iter =
        BroadcastIterator::new(inputs).map_err(pyo3::exceptions::PyValueError::new_err)?;
    let len = iter.len();

    // Release GIL and compute Greeks
    let (deltas, gammas, vegas, thetas, rhos, dividend_rhos) = py.allow_threads(move || {
        let greeks_results = if len < PARALLEL_THRESHOLD_SMALL {
            // Sequential processing for small data
            let mut results = Vec::with_capacity(len);
            let mut param_buffer = [0.0; 6];

            for i in 0..len {
                // Get parameters
                for (j, arr) in iter.arrays.iter().enumerate() {
                    param_buffer[j] = arr[i];
                }

                results.push(
                    American::greeks_american(
                        param_buffer[0],
                        param_buffer[1],
                        param_buffer[2],
                        param_buffer[3],
                        param_buffer[4],
                        param_buffer[5],
                        is_call,
                    )
                    .unwrap_or(Greeks {
                        delta: f64::NAN,
                        gamma: f64::NAN,
                        vega: f64::NAN,
                        theta: f64::NAN,
                        rho: f64::NAN,
                        dividend_rho: Some(f64::NAN),
                    }),
                );
            }
            results
        } else {
            // Parallel processing for large data
            use rayon::prelude::*;

            (0..len)
                .into_par_iter()
                .chunks(CHUNK_SIZE_L1)
                .flat_map(|chunk| {
                    let mut chunk_results = Vec::with_capacity(chunk.len());
                    let mut param_buffer = [0.0; 6];

                    for i in chunk {
                        // Get parameters
                        for (j, arr) in iter.arrays.iter().enumerate() {
                            param_buffer[j] = arr[i];
                        }

                        chunk_results.push(
                            American::greeks_american(
                                param_buffer[0],
                                param_buffer[1],
                                param_buffer[2],
                                param_buffer[3],
                                param_buffer[4],
                                param_buffer[5],
                                is_call,
                            )
                            .unwrap_or(Greeks {
                                delta: f64::NAN,
                                gamma: f64::NAN,
                                vega: f64::NAN,
                                theta: f64::NAN,
                                rho: f64::NAN,
                                dividend_rho: Some(f64::NAN),
                            }),
                        );
                    }

                    chunk_results
                })
                .collect()
        };

        // Extract individual Greeks vectors
        let mut deltas = Vec::with_capacity(greeks_results.len());
        let mut gammas = Vec::with_capacity(greeks_results.len());
        let mut vegas = Vec::with_capacity(greeks_results.len());
        let mut thetas = Vec::with_capacity(greeks_results.len());
        let mut rhos = Vec::with_capacity(greeks_results.len());
        let mut dividend_rhos = Vec::with_capacity(greeks_results.len());

        for greeks in greeks_results {
            deltas.push(greeks.delta);
            gammas.push(greeks.gamma);
            vegas.push(greeks.vega);
            thetas.push(greeks.theta);
            rhos.push(greeks.rho);
            dividend_rhos.push(greeks.dividend_rho.unwrap_or(0.0));
        }

        (deltas, gammas, vegas, thetas, rhos, dividend_rhos)
    });

    // Create output dictionary
    let dict = PyDict::new_bound(py);
    dict.set_item("delta", PyArray1::from_vec_bound(py, deltas))?;
    dict.set_item("gamma", PyArray1::from_vec_bound(py, gammas))?;
    dict.set_item("vega", PyArray1::from_vec_bound(py, vegas))?;
    dict.set_item("theta", PyArray1::from_vec_bound(py, thetas))?;
    dict.set_item("rho", PyArray1::from_vec_bound(py, rhos))?;
    dict.set_item("dividend_rho", PyArray1::from_vec_bound(py, dividend_rhos))?;

    Ok(dict)
}
