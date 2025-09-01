//! Fixed greeks_batch function

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

            for i in 0..len {
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

                results.push(
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

        // Extract results into separate vectors
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