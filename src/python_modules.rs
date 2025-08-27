use numpy::PyArray1;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::wrap_pyfunction;

use crate::flexible_array::FlexibleArray;
use crate::models::american::{AmericanModel, AmericanParams};
use crate::models::black76::{Black76, Black76Params};
use crate::models::black_scholes_batch;
use crate::models::black_scholes_model::{BlackScholes, BlackScholesParams};
use crate::models::merton::{MertonModel, MertonParams};
use crate::models::PricingModel;
use crate::validation::validate_inputs;

/// Black-Scholes module for Python
#[pymodule]
pub fn black_scholes(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(bs_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(bs_put_price, m)?)?;
    m.add_function(wrap_pyfunction!(bs_call_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(bs_put_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(bs_greeks, m)?)?;
    m.add_function(wrap_pyfunction!(bs_greeks_batch, m)?)?;
    m.add_function(wrap_pyfunction!(bs_implied_volatility, m)?)?;
    m.add_function(wrap_pyfunction!(bs_implied_volatility_batch, m)?)?;
    m.add_class::<PyGreeks>()?;
    Ok(())
}

/// Calculate Black-Scholes call option price
#[pyfunction]
#[pyo3(name = "call_price")]
#[pyo3(signature = (s, k, t, r, sigma))]
fn bs_call_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    validate_inputs(s, k, t, r, sigma)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let params = BlackScholesParams {
        spot: s,
        strike: k,
        time: t,
        rate: r,
        sigma,
    };

    Ok(BlackScholes::call_price(&params))
}

/// Calculate Black-Scholes put option price
#[pyfunction]
#[pyo3(name = "put_price")]
#[pyo3(signature = (s, k, t, r, sigma))]
fn bs_put_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    validate_inputs(s, k, t, r, sigma)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let params = BlackScholesParams {
        spot: s,
        strike: k,
        time: t,
        rate: r,
        sigma,
    };

    Ok(BlackScholes::put_price(&params))
}

/// Calculate call prices for multiple parameters with broadcasting
#[pyfunction]
#[pyo3(name = "call_price_batch")]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
fn bs_call_price_batch<'py>(
    py: Python<'py>,
    spots: FlexibleArray<'py>,
    strikes: FlexibleArray<'py>,
    times: FlexibleArray<'py>,
    rates: FlexibleArray<'py>,
    sigmas: FlexibleArray<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let spots_arr = spots
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let strikes_arr = strikes
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let times_arr = times
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let rates_arr = rates
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let sigmas_arr = sigmas
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let results = black_scholes_batch::call_price_batch(
        spots_arr,
        strikes_arr,
        times_arr,
        rates_arr,
        sigmas_arr,
    )
    .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    Ok(PyArray1::from_vec_bound(py, results))
}

/// Calculate put prices for multiple parameters with broadcasting
#[pyfunction]
#[pyo3(name = "put_price_batch")]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
fn bs_put_price_batch<'py>(
    py: Python<'py>,
    spots: FlexibleArray<'py>,
    strikes: FlexibleArray<'py>,
    times: FlexibleArray<'py>,
    rates: FlexibleArray<'py>,
    sigmas: FlexibleArray<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let spots_arr = spots
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let strikes_arr = strikes
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let times_arr = times
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let rates_arr = rates
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let sigmas_arr = sigmas
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let results = black_scholes_batch::put_price_batch(
        spots_arr,
        strikes_arr,
        times_arr,
        rates_arr,
        sigmas_arr,
    )
    .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    Ok(PyArray1::from_vec_bound(py, results))
}

/// Calculate implied volatilities for multiple parameters with broadcasting
#[pyfunction]
#[pyo3(name = "implied_volatility_batch")]
#[pyo3(signature = (prices, spots, strikes, times, rates, is_calls))]
fn bs_implied_volatility_batch<'py>(
    py: Python<'py>,
    prices: FlexibleArray<'py>,
    spots: FlexibleArray<'py>,
    strikes: FlexibleArray<'py>,
    times: FlexibleArray<'py>,
    rates: FlexibleArray<'py>,
    is_calls: FlexibleArray<'py>, // Use f64 for bool array (0.0=False, other=True)
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let prices_arr = prices
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let spots_arr = spots
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let strikes_arr = strikes
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let times_arr = times
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let rates_arr = rates
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let is_calls_arr = is_calls
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let results = black_scholes_batch::implied_volatility_batch(
        prices_arr,
        spots_arr,
        strikes_arr,
        times_arr,
        rates_arr,
        is_calls_arr,
    )
    .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    Ok(PyArray1::from_vec_bound(py, results))
}

/// Calculate Greeks for multiple parameters with broadcasting
/// Returns a dictionary with arrays for each Greek
#[pyfunction]
#[pyo3(name = "greeks_batch")]
#[pyo3(signature = (spots, strikes, times, rates, sigmas, is_calls))]
fn bs_greeks_batch<'py>(
    py: Python<'py>,
    spots: FlexibleArray<'py>,
    strikes: FlexibleArray<'py>,
    times: FlexibleArray<'py>,
    rates: FlexibleArray<'py>,
    sigmas: FlexibleArray<'py>,
    is_calls: FlexibleArray<'py>, // Use f64 for bool array
) -> PyResult<Bound<'py, PyDict>> {
    let spots_arr = spots
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let strikes_arr = strikes
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let times_arr = times
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let rates_arr = rates
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let sigmas_arr = sigmas
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let is_calls_arr = is_calls
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let greeks_batch = black_scholes_batch::greeks_batch(
        spots_arr,
        strikes_arr,
        times_arr,
        rates_arr,
        sigmas_arr,
        is_calls_arr,
    )
    .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    // Create dictionary with NumPy arrays
    let dict = PyDict::new_bound(py);
    dict.set_item("delta", PyArray1::from_vec_bound(py, greeks_batch.delta))?;
    dict.set_item("gamma", PyArray1::from_vec_bound(py, greeks_batch.gamma))?;
    dict.set_item("vega", PyArray1::from_vec_bound(py, greeks_batch.vega))?;
    dict.set_item("theta", PyArray1::from_vec_bound(py, greeks_batch.theta))?;
    dict.set_item("rho", PyArray1::from_vec_bound(py, greeks_batch.rho))?;

    Ok(dict)
}

/// Calculate all Greeks for Black-Scholes option
#[pyfunction]
#[pyo3(name = "greeks")]
#[pyo3(signature = (s, k, t, r, sigma, is_call=true))]
fn bs_greeks(s: f64, k: f64, t: f64, r: f64, sigma: f64, is_call: bool) -> PyResult<PyGreeks> {
    validate_inputs(s, k, t, r, sigma)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let params = BlackScholesParams {
        spot: s,
        strike: k,
        time: t,
        rate: r,
        sigma,
    };

    let greeks = BlackScholes::greeks(&params, is_call);

    Ok(PyGreeks {
        delta: greeks.delta,
        gamma: greeks.gamma,
        vega: greeks.vega,
        theta: greeks.theta,
        rho: greeks.rho,
    })
}

/// Calculate implied volatility from Black-Scholes option price
#[pyfunction]
#[pyo3(name = "implied_volatility")]
#[pyo3(signature = (price, s, k, t, r, is_call=true))]
fn bs_implied_volatility(
    price: f64,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    is_call: bool,
) -> PyResult<f64> {
    // Basic parameter validation (not vol since we're solving for it)
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || price <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "All parameters must be positive",
        ));
    }

    let params = BlackScholesParams {
        spot: s,
        strike: k,
        time: t,
        rate: r,
        sigma: 0.2, // Placeholder, not used in IV calculation
    };

    BlackScholes::implied_volatility(price, &params, is_call, None)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

/// Python-friendly Greeks struct
#[pyclass]
#[derive(Clone)]
pub struct PyGreeks {
    #[pyo3(get)]
    pub delta: f64,
    #[pyo3(get)]
    pub gamma: f64,
    #[pyo3(get)]
    pub vega: f64,
    #[pyo3(get)]
    pub theta: f64,
    #[pyo3(get)]
    pub rho: f64,
}

#[pymethods]
impl PyGreeks {
    fn __repr__(&self) -> String {
        format!(
            "Greeks(delta={:.4}, gamma={:.4}, vega={:.4}, theta={:.4}, rho={:.4})",
            self.delta, self.gamma, self.vega, self.theta, self.rho
        )
    }
}

/// Black76 module for Python
#[pymodule]
pub fn black76(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(b76_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(b76_put_price, m)?)?;
    m.add_function(wrap_pyfunction!(b76_call_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(b76_put_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(b76_greeks, m)?)?;
    m.add_function(wrap_pyfunction!(b76_greeks_batch, m)?)?;
    m.add_function(wrap_pyfunction!(b76_implied_volatility, m)?)?;
    m.add_function(wrap_pyfunction!(b76_implied_volatility_batch, m)?)?;
    m.add_class::<PyGreeks>()?;
    Ok(())
}

/// Calculate Black76 call option price
#[pyfunction]
#[pyo3(name = "call_price")]
#[pyo3(signature = (f, k, t, r, sigma))]
fn b76_call_price(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    if f <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "f, k, t, and sigma must be positive",
        ));
    }
    if !f.is_finite() || !k.is_finite() || !t.is_finite() || !r.is_finite() || !sigma.is_finite() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "All parameters must be finite",
        ));
    }

    let params = Black76Params::new(f, k, t, r, sigma);
    Ok(Black76::call_price(&params))
}

/// Calculate Black76 put option price
#[pyfunction]
#[pyo3(name = "put_price")]
#[pyo3(signature = (f, k, t, r, sigma))]
fn b76_put_price(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    if f <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "f, k, t, and sigma must be positive",
        ));
    }
    if !f.is_finite() || !k.is_finite() || !t.is_finite() || !r.is_finite() || !sigma.is_finite() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "All parameters must be finite",
        ));
    }

    let params = Black76Params::new(f, k, t, r, sigma);
    Ok(Black76::put_price(&params))
}

/// Calculate call prices with broadcasting support
#[pyfunction]
#[pyo3(name = "call_price_batch")]
#[pyo3(signature = (fs, ks, ts, rs, sigmas))]
fn b76_call_price_batch<'py>(
    py: Python<'py>,
    fs: FlexibleArray<'py>,
    ks: FlexibleArray<'py>,
    ts: FlexibleArray<'py>,
    rs: FlexibleArray<'py>,
    sigmas: FlexibleArray<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    use crate::models::black76;

    let fs_array = fs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let ks_array = ks
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let ts_array = ts
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let rs_array = rs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let sigmas_array = sigmas
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    let results = black76::call_price_batch(fs_array, ks_array, ts_array, rs_array, sigmas_array)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    Ok(PyArray1::from_vec_bound(py, results))
}

/// Calculate put prices with broadcasting support
#[pyfunction]
#[pyo3(name = "put_price_batch")]
#[pyo3(signature = (fs, ks, ts, rs, sigmas))]
fn b76_put_price_batch<'py>(
    py: Python<'py>,
    fs: FlexibleArray<'py>,
    ks: FlexibleArray<'py>,
    ts: FlexibleArray<'py>,
    rs: FlexibleArray<'py>,
    sigmas: FlexibleArray<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    use crate::models::black76;

    let fs_array = fs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let ks_array = ks
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let ts_array = ts
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let rs_array = rs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let sigmas_array = sigmas
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    let results = black76::put_price_batch(fs_array, ks_array, ts_array, rs_array, sigmas_array)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    Ok(PyArray1::from_vec_bound(py, results))
}

/// Calculate all Greeks for Black76 option
#[pyfunction]
#[pyo3(name = "greeks")]
#[pyo3(signature = (f, k, t, r, sigma, is_call=true))]
fn b76_greeks(f: f64, k: f64, t: f64, r: f64, sigma: f64, is_call: bool) -> PyResult<PyGreeks> {
    if f <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "f, k, t, and sigma must be positive",
        ));
    }
    if !f.is_finite() || !k.is_finite() || !t.is_finite() || !r.is_finite() || !sigma.is_finite() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "All parameters must be finite",
        ));
    }

    let params = Black76Params::new(f, k, t, r, sigma);
    let greeks = Black76::greeks(&params, is_call);

    Ok(PyGreeks {
        delta: greeks.delta,
        gamma: greeks.gamma,
        vega: greeks.vega,
        theta: greeks.theta,
        rho: greeks.rho,
    })
}

/// Calculate implied volatility from Black76 option price
#[pyfunction]
#[pyo3(name = "implied_volatility")]
#[pyo3(signature = (price, f, k, t, r, is_call=true))]
fn b76_implied_volatility(
    price: f64,
    f: f64,
    k: f64,
    t: f64,
    r: f64,
    is_call: bool,
) -> PyResult<f64> {
    // Basic parameter validation
    if f <= 0.0 || k <= 0.0 || t <= 0.0 || price <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "All parameters must be positive",
        ));
    }
    if !f.is_finite() || !k.is_finite() || !t.is_finite() || !r.is_finite() || !price.is_finite() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "All parameters must be finite",
        ));
    }

    let params = Black76Params::new(f, k, t, r, 0.2); // sigma is placeholder

    Black76::implied_volatility(price, &params, is_call, None)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

/// Calculate implied volatility for multiple option prices (Black76)
#[pyfunction]
#[pyo3(name = "implied_volatility_batch")]
#[pyo3(signature = (prices, fs, ks, ts, rs, is_calls))]
fn b76_implied_volatility_batch<'py>(
    py: Python<'py>,
    prices: FlexibleArray<'py>,
    fs: FlexibleArray<'py>,
    ks: FlexibleArray<'py>,
    ts: FlexibleArray<'py>,
    rs: FlexibleArray<'py>,
    is_calls: FlexibleArray<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    use crate::models::black76;

    let prices_array = prices
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let fs_array = fs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let ks_array = ks
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let ts_array = ts
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let rs_array = rs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let is_calls_array = is_calls
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    let results = black76::implied_volatility_batch(
        prices_array,
        fs_array,
        ks_array,
        ts_array,
        rs_array,
        is_calls_array,
    )
    .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    Ok(PyArray1::from_vec_bound(py, results))
}

/// Calculate Greeks with broadcasting support (Black76)
#[pyfunction]
#[pyo3(name = "greeks_batch")]
#[pyo3(signature = (fs, ks, ts, rs, sigmas, is_calls))]
fn b76_greeks_batch<'py>(
    py: Python<'py>,
    fs: FlexibleArray<'py>,
    ks: FlexibleArray<'py>,
    ts: FlexibleArray<'py>,
    rs: FlexibleArray<'py>,
    sigmas: FlexibleArray<'py>,
    is_calls: FlexibleArray<'py>,
) -> PyResult<Bound<'py, PyDict>> {
    use crate::models::black76;

    let fs_array = fs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let ks_array = ks
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let ts_array = ts
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let rs_array = rs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let sigmas_array = sigmas
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let is_calls_array = is_calls
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    let greeks_batch = black76::greeks_batch(
        fs_array,
        ks_array,
        ts_array,
        rs_array,
        sigmas_array,
        is_calls_array,
    )
    .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    // Convert to dictionary format
    let dict = PyDict::new_bound(py);
    dict.set_item("delta", PyArray1::from_vec_bound(py, greeks_batch.delta))?;
    dict.set_item("gamma", PyArray1::from_vec_bound(py, greeks_batch.gamma))?;
    dict.set_item("vega", PyArray1::from_vec_bound(py, greeks_batch.vega))?;
    dict.set_item("theta", PyArray1::from_vec_bound(py, greeks_batch.theta))?;
    dict.set_item("rho", PyArray1::from_vec_bound(py, greeks_batch.rho))?;

    Ok(dict)
}

/// Merton model module for Python
#[pymodule]
pub fn merton(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(merton_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(merton_put_price, m)?)?;
    m.add_function(wrap_pyfunction!(merton_call_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(merton_put_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(merton_greeks, m)?)?;
    m.add_function(wrap_pyfunction!(merton_greeks_batch, m)?)?;
    m.add_function(wrap_pyfunction!(merton_implied_volatility, m)?)?;
    m.add_function(wrap_pyfunction!(merton_implied_volatility_batch, m)?)?;
    m.add_class::<PyMertonGreeks>()?;
    Ok(())
}

/// Calculate Merton model call option price
#[pyfunction]
#[pyo3(name = "call_price")]
#[pyo3(signature = (s, k, t, r, q, sigma))]
fn merton_call_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    if s <= 0.0 || k <= 0.0 || t < 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "s, k must be positive; t must be non-negative; sigma must be positive",
        ));
    }
    if !s.is_finite()
        || !k.is_finite()
        || !t.is_finite()
        || !r.is_finite()
        || !q.is_finite()
        || !sigma.is_finite()
    {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "All parameters must be finite",
        ));
    }

    let params = MertonParams::new_unchecked(s, k, t, r, q, sigma);
    Ok(MertonModel::call_price(&params))
}

/// Calculate Merton model put option price
#[pyfunction]
#[pyo3(name = "put_price")]
#[pyo3(signature = (s, k, t, r, q, sigma))]
fn merton_put_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    if s <= 0.0 || k <= 0.0 || t < 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "s, k must be positive; t must be non-negative; sigma must be positive",
        ));
    }
    if !s.is_finite()
        || !k.is_finite()
        || !t.is_finite()
        || !r.is_finite()
        || !q.is_finite()
        || !sigma.is_finite()
    {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "All parameters must be finite",
        ));
    }

    let params = MertonParams::new_unchecked(s, k, t, r, q, sigma);
    Ok(MertonModel::put_price(&params))
}

/// Calculate call prices with broadcasting support
#[pyfunction]
#[pyo3(name = "call_price_batch")]
#[pyo3(signature = (spots, strikes, times, rates, qs, sigmas))]
fn merton_call_price_batch<'py>(
    py: Python<'py>,
    spots: FlexibleArray<'py>,
    strikes: FlexibleArray<'py>,
    times: FlexibleArray<'py>,
    rates: FlexibleArray<'py>,
    qs: FlexibleArray<'py>,
    sigmas: FlexibleArray<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    use crate::models::merton;

    let spots_array = spots
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let strikes_array = strikes
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let times_array = times
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let rates_array = rates
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let qs_array = qs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let sigmas_array = sigmas
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    let results = merton::call_price_batch(
        spots_array,
        strikes_array,
        times_array,
        rates_array,
        qs_array,
        sigmas_array,
    )
    .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    Ok(PyArray1::from_vec_bound(py, results))
}

/// Calculate put prices with broadcasting support
#[pyfunction]
#[pyo3(name = "put_price_batch")]
#[pyo3(signature = (spots, strikes, times, rates, qs, sigmas))]
fn merton_put_price_batch<'py>(
    py: Python<'py>,
    spots: FlexibleArray<'py>,
    strikes: FlexibleArray<'py>,
    times: FlexibleArray<'py>,
    rates: FlexibleArray<'py>,
    qs: FlexibleArray<'py>,
    sigmas: FlexibleArray<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    use crate::models::merton;

    let spots_array = spots
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let strikes_array = strikes
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let times_array = times
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let rates_array = rates
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let qs_array = qs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let sigmas_array = sigmas
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    let results = merton::put_price_batch(
        spots_array,
        strikes_array,
        times_array,
        rates_array,
        qs_array,
        sigmas_array,
    )
    .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    Ok(PyArray1::from_vec_bound(py, results))
}

/// Calculate all Greeks for Merton model option
#[pyfunction]
#[pyo3(name = "greeks")]
#[pyo3(signature = (s, k, t, r, q, sigma, is_call=true))]
fn merton_greeks(
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    is_call: bool,
) -> PyResult<PyMertonGreeks> {
    if s <= 0.0 || k <= 0.0 || t < 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "s, k must be positive; t must be non-negative; sigma must be positive",
        ));
    }
    if !s.is_finite()
        || !k.is_finite()
        || !t.is_finite()
        || !r.is_finite()
        || !q.is_finite()
        || !sigma.is_finite()
    {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "All parameters must be finite",
        ));
    }

    let greeks =
        crate::models::merton::greeks::calculate_merton_greeks(s, k, t, r, q, sigma, is_call);

    Ok(PyMertonGreeks {
        delta: greeks.delta,
        gamma: greeks.gamma,
        vega: greeks.vega,
        theta: greeks.theta,
        rho: greeks.rho,
        dividend_rho: greeks.dividend_rho,
    })
}

/// Calculate implied volatility from Merton model option price
#[pyfunction]
#[pyo3(name = "implied_volatility")]
#[pyo3(signature = (price, s, k, t, r, q, is_call=true))]
fn merton_implied_volatility(
    price: f64,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    is_call: bool,
) -> PyResult<f64> {
    // Basic parameter validation
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || price <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "s, k, t, and price must be positive",
        ));
    }
    if !s.is_finite()
        || !k.is_finite()
        || !t.is_finite()
        || !r.is_finite()
        || !q.is_finite()
        || !price.is_finite()
    {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "All parameters must be finite",
        ));
    }

    crate::models::merton::implied_volatility::calculate_implied_volatility(
        price, s, k, t, r, q, is_call, None,
    )
    .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

/// Calculate implied volatility for multiple option prices (Merton)
#[pyfunction]
#[pyo3(name = "implied_volatility_batch")]
#[pyo3(signature = (prices, spots, strikes, times, rates, qs, is_calls))]
fn merton_implied_volatility_batch<'py>(
    py: Python<'py>,
    prices: FlexibleArray<'py>,
    spots: FlexibleArray<'py>,
    strikes: FlexibleArray<'py>,
    times: FlexibleArray<'py>,
    rates: FlexibleArray<'py>,
    qs: FlexibleArray<'py>,
    is_calls: FlexibleArray<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    use crate::models::merton;

    let prices_array = prices
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let spots_array = spots
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let strikes_array = strikes
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let times_array = times
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let rates_array = rates
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let qs_array = qs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let is_calls_array = is_calls
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    let results = merton::implied_volatility_batch(
        prices_array,
        spots_array,
        strikes_array,
        times_array,
        rates_array,
        qs_array,
        is_calls_array,
    )
    .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    Ok(PyArray1::from_vec_bound(py, results))
}

/// Calculate Greeks with broadcasting support (Merton)
#[pyfunction]
#[pyo3(name = "greeks_batch")]
#[pyo3(signature = (spots, strikes, times, rates, qs, sigmas, is_calls))]
fn merton_greeks_batch<'py>(
    py: Python<'py>,
    spots: FlexibleArray<'py>,
    strikes: FlexibleArray<'py>,
    times: FlexibleArray<'py>,
    rates: FlexibleArray<'py>,
    qs: FlexibleArray<'py>,
    sigmas: FlexibleArray<'py>,
    is_calls: FlexibleArray<'py>,
) -> PyResult<Bound<'py, PyDict>> {
    use crate::models::merton;

    let spots_array = spots
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let strikes_array = strikes
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let times_array = times
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let rates_array = rates
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let qs_array = qs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let sigmas_array = sigmas
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let is_calls_array = is_calls
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    let greeks_batch = merton::greeks_batch(
        spots_array,
        strikes_array,
        times_array,
        rates_array,
        qs_array,
        sigmas_array,
        is_calls_array,
    )
    .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    // Convert to dictionary format
    let dict = PyDict::new_bound(py);
    dict.set_item("delta", PyArray1::from_vec_bound(py, greeks_batch.delta))?;
    dict.set_item("gamma", PyArray1::from_vec_bound(py, greeks_batch.gamma))?;
    dict.set_item("vega", PyArray1::from_vec_bound(py, greeks_batch.vega))?;
    dict.set_item("theta", PyArray1::from_vec_bound(py, greeks_batch.theta))?;
    dict.set_item("rho", PyArray1::from_vec_bound(py, greeks_batch.rho))?;
    dict.set_item(
        "dividend_rho",
        PyArray1::from_vec_bound(py, greeks_batch.dividend_rho),
    )?;

    Ok(dict)
}

/// Python-friendly Merton Greeks struct with dividend_rho
#[pyclass]
#[derive(Clone)]
pub struct PyMertonGreeks {
    #[pyo3(get)]
    pub delta: f64,
    #[pyo3(get)]
    pub gamma: f64,
    #[pyo3(get)]
    pub vega: f64,
    #[pyo3(get)]
    pub theta: f64,
    #[pyo3(get)]
    pub rho: f64,
    #[pyo3(get)]
    pub dividend_rho: f64,
}

#[pymethods]
impl PyMertonGreeks {
    fn __repr__(&self) -> String {
        format!(
            "MertonGreeks(delta={:.4}, gamma={:.4}, vega={:.4}, theta={:.4}, rho={:.4}, dividend_rho={:.4})",
            self.delta, self.gamma, self.vega, self.theta, self.rho, self.dividend_rho
        )
    }
}

/// American option module for Python
#[pymodule]
pub fn american(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(american_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(american_put_price, m)?)?;
    m.add_function(wrap_pyfunction!(american_call_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(american_put_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(american_greeks, m)?)?;
    m.add_function(wrap_pyfunction!(american_greeks_batch, m)?)?;
    m.add_function(wrap_pyfunction!(american_implied_volatility, m)?)?;
    m.add_function(wrap_pyfunction!(american_implied_volatility_batch, m)?)?;
    m.add_function(wrap_pyfunction!(american_exercise_boundary, m)?)?;
    m.add_function(wrap_pyfunction!(american_exercise_boundary_batch, m)?)?;
    m.add_class::<PyGreeks>()?;
    Ok(())
}

/// Calculate American call option price using Bjerksund-Stensland 2002
#[pyfunction]
#[pyo3(name = "call_price")]
#[pyo3(signature = (s, k, t, r, q, sigma))]
fn american_call_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    // Create and validate parameters
    let params = AmericanParams::new(s, k, t, r, q, sigma)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    Ok(AmericanModel::call_price(&params))
}

/// Calculate American put option price using Bjerksund-Stensland 2002
#[pyfunction]
#[pyo3(name = "put_price")]
#[pyo3(signature = (s, k, t, r, q, sigma))]
fn american_put_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    // Create and validate parameters
    let params = AmericanParams::new(s, k, t, r, q, sigma)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    Ok(AmericanModel::put_price(&params))
}

/// Calculate call prices for multiple spots
#[pyfunction]
#[pyo3(name = "call_price_batch")]
#[pyo3(signature = (spots, strikes, times, rates, qs, sigmas))]
fn american_call_price_batch<'py>(
    py: Python<'py>,
    spots: FlexibleArray<'py>,
    strikes: FlexibleArray<'py>,
    times: FlexibleArray<'py>,
    rates: FlexibleArray<'py>,
    qs: FlexibleArray<'py>,
    sigmas: FlexibleArray<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let spots_arr = spots
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let strikes_arr = strikes
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let times_arr = times
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let rates_arr = rates
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let qs_arr = qs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let sigmas_arr = sigmas
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let results = crate::models::american::call_price_batch(
        spots_arr,
        strikes_arr,
        times_arr,
        rates_arr,
        qs_arr,
        sigmas_arr,
    )
    .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    Ok(PyArray1::from_vec_bound(py, results))
}

/// Calculate put prices for multiple spots
#[pyfunction]
#[pyo3(name = "put_price_batch")]
#[pyo3(signature = (spots, strikes, times, rates, qs, sigmas))]
fn american_put_price_batch<'py>(
    py: Python<'py>,
    spots: FlexibleArray<'py>,
    strikes: FlexibleArray<'py>,
    times: FlexibleArray<'py>,
    rates: FlexibleArray<'py>,
    qs: FlexibleArray<'py>,
    sigmas: FlexibleArray<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let spots_arr = spots
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let strikes_arr = strikes
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let times_arr = times
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let rates_arr = rates
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let qs_arr = qs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let sigmas_arr = sigmas
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let results = crate::models::american::put_price_batch(
        spots_arr,
        strikes_arr,
        times_arr,
        rates_arr,
        qs_arr,
        sigmas_arr,
    )
    .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    Ok(PyArray1::from_vec_bound(py, results))
}

/// Calculate all Greeks for American option
#[pyfunction]
#[pyo3(name = "greeks")]
#[pyo3(signature = (s, k, t, r, q, sigma, is_call=true))]
fn american_greeks(
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    is_call: bool,
) -> PyResult<PyGreeks> {
    // Create and validate parameters
    let params = AmericanParams::new(s, k, t, r, q, sigma)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let greeks = AmericanModel::greeks(&params, is_call);

    Ok(PyGreeks {
        delta: greeks.delta,
        gamma: greeks.gamma,
        vega: greeks.vega,
        theta: greeks.theta,
        rho: greeks.rho,
    })
}

/// Calculate implied volatility from American option price
#[pyfunction]
#[pyo3(name = "implied_volatility")]
#[pyo3(signature = (price, s, k, t, r, q, is_call=true, initial_guess=None))]
#[allow(clippy::too_many_arguments)]
fn american_implied_volatility(
    price: f64,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    is_call: bool,
    initial_guess: Option<f64>,
) -> PyResult<f64> {
    // Basic parameter validation (sigma will be solved for)
    if s <= 0.0 || k <= 0.0 || t < 0.0 || price <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "s, k, and price must be positive; t must be non-negative",
        ));
    }

    // Check dividend arbitrage
    if q > r {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Dividend yield (q) cannot exceed risk-free rate (r) to prevent arbitrage",
        ));
    }

    // Create params with dummy sigma for IV calculation
    let params = AmericanParams {
        s,
        k,
        t,
        r,
        q,
        sigma: 0.3,
    };

    AmericanModel::implied_volatility(price, &params, is_call, initial_guess)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

/// Calculate implied volatility for multiple option prices (American)
#[pyfunction]
#[pyo3(name = "implied_volatility_batch")]
#[pyo3(signature = (prices, spots, strikes, times, rates, qs, is_calls))]
fn american_implied_volatility_batch<'py>(
    py: Python<'py>,
    prices: FlexibleArray<'py>,
    spots: FlexibleArray<'py>,
    strikes: FlexibleArray<'py>,
    times: FlexibleArray<'py>,
    rates: FlexibleArray<'py>,
    qs: FlexibleArray<'py>,
    is_calls: FlexibleArray<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let prices_arr = prices
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let spots_arr = spots
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let strikes_arr = strikes
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let times_arr = times
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let rates_arr = rates
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let qs_arr = qs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let is_calls_arr = is_calls
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let results = crate::models::american::implied_volatility_batch(
        prices_arr,
        spots_arr,
        strikes_arr,
        times_arr,
        rates_arr,
        qs_arr,
        is_calls_arr,
    )
    .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    Ok(PyArray1::from_vec_bound(py, results))
}

/// Calculate Greeks for multiple spot prices (American)
#[pyfunction]
#[pyo3(name = "greeks_batch")]
#[pyo3(signature = (spots, strikes, times, rates, qs, sigmas, is_calls))]
fn american_greeks_batch<'py>(
    py: Python<'py>,
    spots: FlexibleArray<'py>,
    strikes: FlexibleArray<'py>,
    times: FlexibleArray<'py>,
    rates: FlexibleArray<'py>,
    qs: FlexibleArray<'py>,
    sigmas: FlexibleArray<'py>,
    is_calls: FlexibleArray<'py>,
) -> PyResult<Bound<'py, PyDict>> {
    let spots_arr = spots
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let strikes_arr = strikes
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let times_arr = times
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let rates_arr = rates
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let qs_arr = qs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let sigmas_arr = sigmas
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let is_calls_arr = is_calls
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let greeks_batch = crate::models::american::greeks_batch(
        spots_arr,
        strikes_arr,
        times_arr,
        rates_arr,
        qs_arr,
        sigmas_arr,
        is_calls_arr,
    )
    .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    // Create dictionary with NumPy arrays
    let dict = PyDict::new_bound(py);
    dict.set_item("delta", PyArray1::from_vec_bound(py, greeks_batch.delta))?;
    dict.set_item("gamma", PyArray1::from_vec_bound(py, greeks_batch.gamma))?;
    dict.set_item("vega", PyArray1::from_vec_bound(py, greeks_batch.vega))?;
    dict.set_item("theta", PyArray1::from_vec_bound(py, greeks_batch.theta))?;
    dict.set_item("rho", PyArray1::from_vec_bound(py, greeks_batch.rho))?;
    dict.set_item(
        "dividend_rho",
        PyArray1::from_vec_bound(py, greeks_batch.dividend_rho),
    )?;

    Ok(dict)
}

/// Calculate early exercise boundary for American option
#[pyfunction]
#[pyo3(name = "exercise_boundary")]
#[pyo3(signature = (s, k, t, r, q, sigma, is_call=true))]
fn american_exercise_boundary(
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    is_call: bool,
) -> PyResult<f64> {
    // Create and validate parameters
    let params = AmericanParams::new(s, k, t, r, q, sigma)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    Ok(crate::models::american::exercise_boundary(&params, is_call))
}

/// Calculate early exercise boundaries for multiple spot prices
#[pyfunction]
#[pyo3(name = "exercise_boundary_batch")]
#[pyo3(signature = (spots, strikes, times, rates, qs, sigmas, is_calls))]
fn american_exercise_boundary_batch<'py>(
    py: Python<'py>,
    spots: FlexibleArray<'py>,
    strikes: FlexibleArray<'py>,
    times: FlexibleArray<'py>,
    rates: FlexibleArray<'py>,
    qs: FlexibleArray<'py>,
    sigmas: FlexibleArray<'py>,
    is_calls: FlexibleArray<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let spots_arr = spots
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let strikes_arr = strikes
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let times_arr = times
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let rates_arr = rates
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let qs_arr = qs
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let sigmas_arr = sigmas
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let is_calls_arr = is_calls
        .to_array_like()
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let results = crate::models::american::exercise_boundary_batch(
        spots_arr,
        strikes_arr,
        times_arr,
        rates_arr,
        qs_arr,
        sigmas_arr,
        is_calls_arr,
    )
    .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    Ok(PyArray1::from_vec_bound(py, results))
}
