//! Black-Scholes model Python bindings

use numpy::PyArray1;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use quantforge_core::constants::{CHUNK_SIZE_L1, MICRO_BATCH_THRESHOLD, PARALLEL_THRESHOLD_SMALL};
use quantforge_core::models::black_scholes::BlackScholes;
use quantforge_core::traits::{Greeks, OptionModel};

use crate::converters::{ArrayLike, BroadcastIteratorOptimized};
use crate::error::to_py_err;

/// Register all Black-Scholes functions to a module
pub fn register_functions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(call_price, m)?)?;
    m.add_function(wrap_pyfunction!(put_price, m)?)?;
    m.add_function(wrap_pyfunction!(greeks, m)?)?;
    m.add_function(wrap_pyfunction!(call_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(put_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(greeks_batch, m)?)?;
    m.add_function(wrap_pyfunction!(implied_volatility, m)?)?;
    m.add_function(wrap_pyfunction!(implied_volatility_batch, m)?)?;
    Ok(())
}

/// Calculate Black-Scholes call option price
#[pyfunction]
#[pyo3(signature = (s, k, t, r, sigma))]
fn call_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    let model = BlackScholes;
    model.call_price(s, k, t, r, sigma).map_err(to_py_err)
}

/// Calculate Black-Scholes put option price
#[pyfunction]
#[pyo3(signature = (s, k, t, r, sigma))]
fn put_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    let model = BlackScholes;
    model.put_price(s, k, t, r, sigma).map_err(to_py_err)
}

/// Calculate implied volatility using Black-Scholes model
#[pyfunction]
#[pyo3(signature = (price, s, k, t, r, is_call))]
fn implied_volatility(price: f64, s: f64, k: f64, t: f64, r: f64, is_call: bool) -> PyResult<f64> {
    let model = BlackScholes;
    model
        .implied_volatility(price, s, k, t, r, is_call)
        .map_err(to_py_err)
}

/// Calculate Greeks for Black-Scholes model
#[pyfunction]
#[pyo3(signature = (s, k, t, r, sigma, is_call=true))]
fn greeks<'py>(
    py: Python<'py>,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    sigma: f64,
    is_call: bool,
) -> PyResult<Bound<'py, PyDict>> {
    let model = BlackScholes;
    let greeks = model
        .greeks(s, k, t, r, sigma, is_call)
        .map_err(to_py_err)?;

    let dict = PyDict::new_bound(py);
    dict.set_item("delta", greeks.delta)?;
    dict.set_item("gamma", greeks.gamma)?;
    dict.set_item("vega", greeks.vega)?;
    dict.set_item("theta", greeks.theta)?;
    dict.set_item("rho", greeks.rho)?;

    Ok(dict)
}

/// Batch calculation of Black-Scholes call prices
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
fn call_price_batch<'py>(
    py: Python<'py>,
    spots: ArrayLike<'py>,
    strikes: ArrayLike<'py>,
    times: ArrayLike<'py>,
    rates: ArrayLike<'py>,
    sigmas: ArrayLike<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // Determine the output size (max length of all inputs)
    let mut max_len = 1;
    for arr in [&spots, &strikes, &times, &rates, &sigmas] {
        let len = arr.len();
        if len > 1 && max_len > 1 && len != max_len {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Shape mismatch: cannot broadcast arrays of different lengths"
            )));
        }
        max_len = max_len.max(len);
    }

    if max_len == 0 {
        return Ok(PyArray1::from_vec_bound(py, Vec::new()));
    }

    // Micro-batch optimization for small arrays (< 200 elements)
    if max_len < MICRO_BATCH_THRESHOLD {
        // Direct processing without BroadcastIteratorOptimized overhead
        // First collect all values while holding GIL
        let mut values_buffer = Vec::with_capacity(max_len * 5);
        
        for i in 0..max_len {
            values_buffer.push(spots.get_broadcast(i).unwrap_or(f64::NAN));
            values_buffer.push(strikes.get_broadcast(i).unwrap_or(f64::NAN));
            values_buffer.push(times.get_broadcast(i).unwrap_or(f64::NAN));
            values_buffer.push(rates.get_broadcast(i).unwrap_or(f64::NAN));
            values_buffer.push(sigmas.get_broadcast(i).unwrap_or(f64::NAN));
        }
        
        // Now process without GIL
        let results = py.allow_threads(move || {
            let model = BlackScholes;
            let mut results = Vec::with_capacity(max_len);
            
            for i in 0..max_len {
                let idx = i * 5;
                let price = model
                    .call_price(
                        values_buffer[idx],
                        values_buffer[idx + 1],
                        values_buffer[idx + 2],
                        values_buffer[idx + 3],
                        values_buffer[idx + 4],
                    )
                    .unwrap_or(f64::NAN);
                results.push(price);
            }
            
            results
        });
        
        return Ok(PyArray1::from_vec_bound(py, results));
    }

    // For larger arrays, use BroadcastIteratorOptimized
    let inputs = vec![&spots, &strikes, &times, &rates, &sigmas];
    let iter = BroadcastIteratorOptimized::new(inputs).map_err(pyo3::exceptions::PyValueError::new_err)?;

    // Release GIL and use zero-copy computation
    let results = py.allow_threads(move || {
        let model = BlackScholes;

        if iter.len() < PARALLEL_THRESHOLD_SMALL {
            // Sequential processing for small data
            iter.compute_with(|values| {
                model
                    .call_price(values[0], values[1], values[2], values[3], values[4])
                    .unwrap_or(f64::NAN)
            })
        } else {
            // Parallel processing for large data
            iter.compute_parallel_with(
                |values| {
                    model
                        .call_price(values[0], values[1], values[2], values[3], values[4])
                        .unwrap_or(f64::NAN)
                },
                CHUNK_SIZE_L1,
            )
        }
    });

    Ok(PyArray1::from_vec_bound(py, results))
}

/// Batch calculation of Black-Scholes put prices
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
fn put_price_batch<'py>(
    py: Python<'py>,
    spots: ArrayLike<'py>,
    strikes: ArrayLike<'py>,
    times: ArrayLike<'py>,
    rates: ArrayLike<'py>,
    sigmas: ArrayLike<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // Determine the output size (max length of all inputs)
    let mut max_len = 1;
    for arr in [&spots, &strikes, &times, &rates, &sigmas] {
        let len = arr.len();
        if len > 1 && max_len > 1 && len != max_len {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Shape mismatch: cannot broadcast arrays of different lengths"
            )));
        }
        max_len = max_len.max(len);
    }

    if max_len == 0 {
        return Ok(PyArray1::from_vec_bound(py, Vec::new()));
    }

    // Micro-batch optimization for small arrays (< 200 elements)
    if max_len < MICRO_BATCH_THRESHOLD {
        // Direct processing without BroadcastIteratorOptimized overhead
        // First collect all values while holding GIL
        let mut values_buffer = Vec::with_capacity(max_len * 5);
        
        for i in 0..max_len {
            values_buffer.push(spots.get_broadcast(i).unwrap_or(f64::NAN));
            values_buffer.push(strikes.get_broadcast(i).unwrap_or(f64::NAN));
            values_buffer.push(times.get_broadcast(i).unwrap_or(f64::NAN));
            values_buffer.push(rates.get_broadcast(i).unwrap_or(f64::NAN));
            values_buffer.push(sigmas.get_broadcast(i).unwrap_or(f64::NAN));
        }
        
        // Now process without GIL
        let results = py.allow_threads(move || {
            let model = BlackScholes;
            let mut results = Vec::with_capacity(max_len);
            
            for i in 0..max_len {
                let idx = i * 5;
                let price = model
                    .put_price(
                        values_buffer[idx],
                        values_buffer[idx + 1],
                        values_buffer[idx + 2],
                        values_buffer[idx + 3],
                        values_buffer[idx + 4],
                    )
                    .unwrap_or(f64::NAN);
                results.push(price);
            }
            
            results
        });
        
        return Ok(PyArray1::from_vec_bound(py, results));
    }

    // For larger arrays, use BroadcastIteratorOptimized
    let inputs = vec![&spots, &strikes, &times, &rates, &sigmas];
    let iter = BroadcastIteratorOptimized::new(inputs).map_err(pyo3::exceptions::PyValueError::new_err)?;

    // Release GIL and use zero-copy computation
    let results = py.allow_threads(move || {
        let model = BlackScholes;

        if iter.len() < PARALLEL_THRESHOLD_SMALL {
            // Sequential processing for small data
            iter.compute_with(|values| {
                model
                    .put_price(values[0], values[1], values[2], values[3], values[4])
                    .unwrap_or(f64::NAN)
            })
        } else {
            // Parallel processing for large data
            iter.compute_parallel_with(
                |values| {
                    model
                        .put_price(values[0], values[1], values[2], values[3], values[4])
                        .unwrap_or(f64::NAN)
                },
                CHUNK_SIZE_L1,
            )
        }
    });

    Ok(PyArray1::from_vec_bound(py, results))
}

/// Batch calculation of implied volatility
#[pyfunction]
#[pyo3(signature = (prices, spots, strikes, times, rates, is_calls))]
fn implied_volatility_batch<'py>(
    py: Python<'py>,
    prices: ArrayLike<'py>,
    spots: ArrayLike<'py>,
    strikes: ArrayLike<'py>,
    times: ArrayLike<'py>,
    rates: ArrayLike<'py>,
    is_calls: ArrayLike<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // Create broadcast iterator (while holding GIL)
    let inputs = vec![&prices, &spots, &strikes, &times, &rates, &is_calls];
    let iter = BroadcastIteratorOptimized::new(inputs).map_err(pyo3::exceptions::PyValueError::new_err)?;

    // Release GIL and use zero-copy computation
    let results = py.allow_threads(move || {
        let model = BlackScholes;

        if iter.len() < PARALLEL_THRESHOLD_SMALL {
            // Sequential processing for small data
            iter.compute_with(|values| {
                let price = values[0];
                let is_call = values[5] != 0.0;

                model
                    .implied_volatility(price, values[1], values[2], values[3], values[4], is_call)
                    .unwrap_or(f64::NAN)
            })
        } else {
            // Parallel processing for large data
            iter.compute_parallel_with(
                |values| {
                    let price = values[0];
                    let is_call = values[5] != 0.0;

                    model
                        .implied_volatility(
                            price, values[1], values[2], values[3], values[4], is_call,
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
#[pyo3(signature = (spots, strikes, times, rates, sigmas, is_calls=None))]
fn greeks_batch<'py>(
    py: Python<'py>,
    spots: ArrayLike<'py>,
    strikes: ArrayLike<'py>,
    times: ArrayLike<'py>,
    rates: ArrayLike<'py>,
    sigmas: ArrayLike<'py>,
    is_calls: Option<ArrayLike<'py>>,
) -> PyResult<Bound<'py, PyDict>> {
    // Create broadcast iterator (while holding GIL)
    let inputs = vec![&spots, &strikes, &times, &rates, &sigmas];
    let iter = BroadcastIteratorOptimized::new(inputs).map_err(pyo3::exceptions::PyValueError::new_err)?;

    // Handle is_calls parameter (default to True if not provided)
    let is_calls_iter = if let Some(is_calls_array) = is_calls {
        let is_calls_inputs = vec![&is_calls_array];
        let is_calls_it = BroadcastIteratorOptimized::new(is_calls_inputs)
            .map_err(pyo3::exceptions::PyValueError::new_err)?;

        // Ensure both iterators have same length
        if iter.len() != is_calls_it.len() && is_calls_it.len() > 1 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Shape mismatch between parameter arrays and is_calls",
            ));
        }
        Some(is_calls_it)
    } else {
        None
    };

    let len = iter.len();

    // Release GIL for computation
    let (delta_vec, gamma_vec, vega_vec, theta_vec, rho_vec) = py.allow_threads(move || {
        let model = BlackScholes;

        // Compute greeks with zero-copy
        let greeks_results = if iter.len() < PARALLEL_THRESHOLD_SMALL {
            // Sequential processing for small data
            let mut results = Vec::with_capacity(len);
            let mut param_buffer = [0.0; 5];

            for i in 0..len {
                // Get parameters using get_value_at
                param_buffer[0] = iter.get_value_at(0, i);
                param_buffer[1] = iter.get_value_at(1, i);
                param_buffer[2] = iter.get_value_at(2, i);
                param_buffer[3] = iter.get_value_at(3, i);
                param_buffer[4] = iter.get_value_at(4, i);
                
                // Get is_call (default to True if not provided)
                let is_call = if let Some(ref is_calls_it) = is_calls_iter {
                    is_calls_it.get_value_at(0, i) != 0.0
                } else {
                    true // Default to Call option
                };

                results.push(
                    model
                        .greeks(
                            param_buffer[0],
                            param_buffer[1],
                            param_buffer[2],
                            param_buffer[3],
                            param_buffer[4],
                            is_call,
                        )
                        .unwrap_or(Greeks {
                            delta: f64::NAN,
                            gamma: f64::NAN,
                            vega: f64::NAN,
                            theta: f64::NAN,
                            rho: f64::NAN,
                            dividend_rho: None,
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

                    for i in chunk {
                        // Get parameters using get_value_at
                        let s = iter.get_value_at(0, i);
                        let k = iter.get_value_at(1, i);
                        let t = iter.get_value_at(2, i);
                        let r = iter.get_value_at(3, i);
                        let sigma = iter.get_value_at(4, i);
                        
                        // Get is_call (default to True if not provided)
                        let is_call = if let Some(ref is_calls_it) = is_calls_iter {
                            is_calls_it.get_value_at(0, i) != 0.0
                        } else {
                            true // Default to Call option
                        };

                        chunk_results.push(
                            model
                                .greeks(s, k, t, r, sigma, is_call)
                                .unwrap_or(Greeks {
                                    delta: f64::NAN,
                                    gamma: f64::NAN,
                                    vega: f64::NAN,
                                    theta: f64::NAN,
                                    rho: f64::NAN,
                                    dividend_rho: None,
                                }),
                        );
                    }

                    chunk_results
                })
                .collect()
        };

        // Separate into individual vectors
        let mut delta_vec = Vec::with_capacity(len);
        let mut gamma_vec = Vec::with_capacity(len);
        let mut vega_vec = Vec::with_capacity(len);
        let mut theta_vec = Vec::with_capacity(len);
        let mut rho_vec = Vec::with_capacity(len);

        for greeks in greeks_results {
            delta_vec.push(greeks.delta);
            gamma_vec.push(greeks.gamma);
            vega_vec.push(greeks.vega);
            theta_vec.push(greeks.theta);
            rho_vec.push(greeks.rho);
        }

        (delta_vec, gamma_vec, vega_vec, theta_vec, rho_vec)
    });

    // Create output dictionary
    let dict = PyDict::new_bound(py);
    dict.set_item("delta", PyArray1::from_vec_bound(py, delta_vec))?;
    dict.set_item("gamma", PyArray1::from_vec_bound(py, gamma_vec))?;
    dict.set_item("vega", PyArray1::from_vec_bound(py, vega_vec))?;
    dict.set_item("theta", PyArray1::from_vec_bound(py, theta_vec))?;
    dict.set_item("rho", PyArray1::from_vec_bound(py, rho_vec))?;

    Ok(dict)
}
