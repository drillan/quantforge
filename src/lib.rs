#![allow(clippy::useless_conversion)]

use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;

pub mod error;
pub mod math;
pub mod models;
pub mod validation;

use crate::models::black_scholes;
use crate::validation::validate_inputs;

/// Python向け: 単一計算
#[pyfunction]
#[pyo3(signature = (s, k, t, r, v))]
fn calculate_call_price(s: f64, k: f64, t: f64, r: f64, v: f64) -> PyResult<f64> {
    validate_inputs(s, k, t, r, v)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    Ok(black_scholes::bs_call_price(s, k, t, r, v))
}

/// Python向け: NumPy配列バッチ処理（ゼロコピー）
#[pyfunction]
#[pyo3(signature = (spots, k, t, r, v))]
fn calculate_call_price_batch<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    k: f64,
    t: f64,
    r: f64,
    v: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let spots = spots.as_slice()?;
    let results = black_scholes::bs_call_price_batch(spots, k, t, r, v);
    Ok(PyArray1::from_vec_bound(py, results))
}

/// A Python module implemented in Rust.
#[pymodule]
fn quantforge(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calculate_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_call_price_batch, m)?)?;
    Ok(())
}
