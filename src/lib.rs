#![allow(clippy::useless_conversion)]

use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;

pub mod constants;
pub mod error;
pub mod math;
pub mod models;
pub mod validation;

use crate::models::{black_scholes, black_scholes_parallel};
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
    // 共通パラメータのバリデーション（スポット価格は100.0を仮値として使用）
    validate_inputs(100.0, k, t, r, v)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let spots = spots.as_slice()?;

    // 各スポット価格のバリデーション
    for &s in spots {
        if !s.is_finite() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Input contains NaN or infinite values",
            ));
        }
        if s <= 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Spot price must be positive, got {s}"
            )));
        }
    }

    // 大規模データは並列処理を使用（30000要素以上で並列化が効果的）
    let results = if spots.len() >= 30000 {
        black_scholes_parallel::bs_call_price_batch_parallel(spots, k, t, r, v)
    } else {
        black_scholes::bs_call_price_batch(spots, k, t, r, v)
    };
    Ok(PyArray1::from_vec_bound(py, results))
}

/// Python向け: プット単一計算
#[pyfunction]
#[pyo3(signature = (s, k, t, r, v))]
fn calculate_put_price(s: f64, k: f64, t: f64, r: f64, v: f64) -> PyResult<f64> {
    validate_inputs(s, k, t, r, v)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    Ok(black_scholes::bs_put_price(s, k, t, r, v))
}

/// Python向け: プットのNumPy配列バッチ処理（ゼロコピー）
#[pyfunction]
#[pyo3(signature = (spots, k, t, r, v))]
fn calculate_put_price_batch<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    k: f64,
    t: f64,
    r: f64,
    v: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // 共通パラメータのバリデーション（スポット価格は100.0を仮値として使用）
    validate_inputs(100.0, k, t, r, v)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let spots = spots.as_slice()?;

    // 各スポット価格のバリデーション
    for &s in spots {
        if !s.is_finite() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Input contains NaN or infinite values",
            ));
        }
        if s <= 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Spot price must be positive, got {s}"
            )));
        }
    }

    // 大規模データは並列処理を使用（30000要素以上で並列化が効果的）
    let results = if spots.len() >= 30000 {
        black_scholes_parallel::bs_put_price_batch_parallel(spots, k, t, r, v)
    } else {
        black_scholes::bs_put_price_batch(spots, k, t, r, v)
    };
    Ok(PyArray1::from_vec_bound(py, results))
}

/// A Python module implemented in Rust.
#[pymodule]
fn quantforge(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calculate_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_call_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_put_price, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_put_price_batch, m)?)?;
    Ok(())
}
