#![allow(clippy::useless_conversion)]

use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;

pub mod constants;
pub mod error;
pub mod math;
pub mod models;
pub mod validation;

use crate::models::{
    black_scholes, black_scholes_parallel, greeks, greeks_parallel, implied_volatility,
};
use crate::validation::validate_inputs;
use std::collections::HashMap;

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

/// Python向け: Delta Call計算
#[pyfunction]
#[pyo3(signature = (s, k, t, r, v))]
fn calculate_delta_call(s: f64, k: f64, t: f64, r: f64, v: f64) -> PyResult<f64> {
    // 満期時（t=0）は特別処理されるのでバリデーションをスキップ
    if t > 0.0 {
        validate_inputs(s, k, t, r, v)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    } else if !s.is_finite() || s <= 0.0 || !k.is_finite() || k <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Invalid spot or strike price",
        ));
    }
    Ok(greeks::delta_call(s, k, t, r, v))
}

/// Python向け: Delta Put計算
#[pyfunction]
#[pyo3(signature = (s, k, t, r, v))]
fn calculate_delta_put(s: f64, k: f64, t: f64, r: f64, v: f64) -> PyResult<f64> {
    // 満期時（t=0）は特別処理されるのでバリデーションをスキップ
    if t > 0.0 {
        validate_inputs(s, k, t, r, v)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    } else if !s.is_finite() || s <= 0.0 || !k.is_finite() || k <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Invalid spot or strike price",
        ));
    }
    Ok(greeks::delta_put(s, k, t, r, v))
}

/// Python向け: Gamma計算
#[pyfunction]
#[pyo3(signature = (s, k, t, r, v))]
fn calculate_gamma(s: f64, k: f64, t: f64, r: f64, v: f64) -> PyResult<f64> {
    // 満期時（t=0）は特別処理されるのでバリデーションをスキップ
    if t > 0.0 {
        validate_inputs(s, k, t, r, v)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    } else if !s.is_finite() || s <= 0.0 || !k.is_finite() || k <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Invalid spot or strike price",
        ));
    }
    Ok(greeks::gamma(s, k, t, r, v))
}

/// Python向け: Vega計算
#[pyfunction]
#[pyo3(signature = (s, k, t, r, v))]
fn calculate_vega(s: f64, k: f64, t: f64, r: f64, v: f64) -> PyResult<f64> {
    // 満期時（t=0）は特別処理されるのでバリデーションをスキップ
    if t > 0.0 {
        validate_inputs(s, k, t, r, v)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    } else if !s.is_finite() || s <= 0.0 || !k.is_finite() || k <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Invalid spot or strike price",
        ));
    }
    Ok(greeks::vega(s, k, t, r, v))
}

/// Python向け: Theta Call計算
#[pyfunction]
#[pyo3(signature = (s, k, t, r, v))]
fn calculate_theta_call(s: f64, k: f64, t: f64, r: f64, v: f64) -> PyResult<f64> {
    // 満期時（t=0）は特別処理されるのでバリデーションをスキップ
    if t > 0.0 {
        validate_inputs(s, k, t, r, v)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    } else if !s.is_finite() || s <= 0.0 || !k.is_finite() || k <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Invalid spot or strike price",
        ));
    }
    Ok(greeks::theta_call(s, k, t, r, v))
}

/// Python向け: Theta Put計算
#[pyfunction]
#[pyo3(signature = (s, k, t, r, v))]
fn calculate_theta_put(s: f64, k: f64, t: f64, r: f64, v: f64) -> PyResult<f64> {
    // 満期時（t=0）は特別処理されるのでバリデーションをスキップ
    if t > 0.0 {
        validate_inputs(s, k, t, r, v)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    } else if !s.is_finite() || s <= 0.0 || !k.is_finite() || k <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Invalid spot or strike price",
        ));
    }
    Ok(greeks::theta_put(s, k, t, r, v))
}

/// Python向け: Rho Call計算
#[pyfunction]
#[pyo3(signature = (s, k, t, r, v))]
fn calculate_rho_call(s: f64, k: f64, t: f64, r: f64, v: f64) -> PyResult<f64> {
    // 満期時（t=0）は特別処理されるのでバリデーションをスキップ
    if t > 0.0 {
        validate_inputs(s, k, t, r, v)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    } else if !s.is_finite() || s <= 0.0 || !k.is_finite() || k <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Invalid spot or strike price",
        ));
    }
    Ok(greeks::rho_call(s, k, t, r, v))
}

/// Python向け: Rho Put計算
#[pyfunction]
#[pyo3(signature = (s, k, t, r, v))]
fn calculate_rho_put(s: f64, k: f64, t: f64, r: f64, v: f64) -> PyResult<f64> {
    // 満期時（t=0）は特別処理されるのでバリデーションをスキップ
    if t > 0.0 {
        validate_inputs(s, k, t, r, v)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    } else if !s.is_finite() || s <= 0.0 || !k.is_finite() || k <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Invalid spot or strike price",
        ));
    }
    Ok(greeks::rho_put(s, k, t, r, v))
}

/// Python向け: 全グリークス計算
#[pyfunction]
#[pyo3(signature = (s, k, t, r, v, is_call))]
fn calculate_all_greeks(
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    v: f64,
    is_call: bool,
) -> PyResult<HashMap<String, f64>> {
    validate_inputs(s, k, t, r, v)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let greeks = greeks::calculate_all_greeks(s, k, t, r, v, is_call);

    let mut result = HashMap::new();
    result.insert("delta".to_string(), greeks.delta);
    result.insert("gamma".to_string(), greeks.gamma);
    result.insert("vega".to_string(), greeks.vega);
    result.insert("theta".to_string(), greeks.theta);
    result.insert("rho".to_string(), greeks.rho);

    Ok(result)
}

/// Python向け: Delta Callバッチ計算（並列処理対応）
#[pyfunction]
#[pyo3(signature = (spots, k, t, r, v))]
fn calculate_delta_call_batch<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    k: f64,
    t: f64,
    r: f64,
    v: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // 共通パラメータのバリデーション
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

    // 大規模データは並列処理を使用
    let results = if spots.len() >= 30000 {
        greeks_parallel::delta_call_batch_parallel(spots, k, t, r, v)
    } else {
        greeks::delta_call_batch(spots, k, t, r, v)
    };
    Ok(PyArray1::from_vec_bound(py, results))
}

/// Python向け: Gammaバッチ計算（並列処理対応）
#[pyfunction]
#[pyo3(signature = (spots, k, t, r, v))]
fn calculate_gamma_batch<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    k: f64,
    t: f64,
    r: f64,
    v: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // 共通パラメータのバリデーション
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

    // 大規模データは並列処理を使用
    let results = if spots.len() >= 30000 {
        greeks_parallel::gamma_batch_parallel(spots, k, t, r, v)
    } else {
        greeks::gamma_batch(spots, k, t, r, v)
    };
    Ok(PyArray1::from_vec_bound(py, results))
}

/// インプライドボラティリティ計算（コール）
#[pyfunction]
#[pyo3(signature = (price, s, k, t, r))]
fn calculate_implied_volatility_call(price: f64, s: f64, k: f64, t: f64, r: f64) -> PyResult<f64> {
    implied_volatility::implied_volatility_call(price, s, k, t, r)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
}

/// インプライドボラティリティ計算（プット）
#[pyfunction]
#[pyo3(signature = (price, s, k, t, r))]
fn calculate_implied_volatility_put(price: f64, s: f64, k: f64, t: f64, r: f64) -> PyResult<f64> {
    implied_volatility::implied_volatility_put(price, s, k, t, r)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
}

/// インプライドボラティリティバッチ計算
#[pyfunction]
#[pyo3(signature = (prices, spots, strikes, times, rates, is_calls))]
fn calculate_implied_volatility_batch<'py>(
    py: Python<'py>,
    prices: PyReadonlyArray1<f64>,
    spots: PyReadonlyArray1<f64>,
    strikes: PyReadonlyArray1<f64>,
    times: PyReadonlyArray1<f64>,
    rates: PyReadonlyArray1<f64>,
    is_calls: PyReadonlyArray1<bool>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let prices = prices.as_slice()?;
    let spots = spots.as_slice()?;
    let strikes = strikes.as_slice()?;
    let times = times.as_slice()?;
    let rates = rates.as_slice()?;
    let is_calls = is_calls.as_slice()?;

    // 長さチェック
    let len = prices.len();
    if spots.len() != len
        || strikes.len() != len
        || times.len() != len
        || rates.len() != len
        || is_calls.len() != len
    {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "All input arrays must have the same length",
        ));
    }

    // 並列化の閾値判定
    let results = if len > 1000 {
        implied_volatility::implied_volatility_batch_parallel(
            prices, spots, strikes, times, rates, is_calls,
        )
    } else {
        implied_volatility::implied_volatility_batch(prices, spots, strikes, times, rates, is_calls)
    };

    Ok(PyArray1::from_vec_bound(py, results))
}

/// A Python module implemented in Rust.
#[pymodule]
fn quantforge(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // 価格計算
    m.add_function(wrap_pyfunction!(calculate_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_call_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_put_price, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_put_price_batch, m)?)?;

    // グリークス単一計算
    m.add_function(wrap_pyfunction!(calculate_delta_call, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_delta_put, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_gamma, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_vega, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_theta_call, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_theta_put, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_rho_call, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_rho_put, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_all_greeks, m)?)?;

    // グリークスバッチ計算
    m.add_function(wrap_pyfunction!(calculate_delta_call_batch, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_gamma_batch, m)?)?;

    // インプライドボラティリティ計算
    m.add_function(wrap_pyfunction!(calculate_implied_volatility_call, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_implied_volatility_put, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_implied_volatility_batch, m)?)?;

    Ok(())
}
