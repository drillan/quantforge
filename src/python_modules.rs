use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

use crate::models::black76::{Black76, Black76Params};
use crate::models::black_scholes_model::{BlackScholes, BlackScholesParams};
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
    m.add_function(wrap_pyfunction!(bs_implied_volatility, m)?)?;
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

/// Calculate call prices for multiple spots
#[pyfunction]
#[pyo3(name = "call_price_batch")]
#[pyo3(signature = (spots, k, t, r, sigma))]
fn bs_call_price_batch<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    k: f64,
    t: f64,
    r: f64,
    sigma: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // Validate common parameters
    validate_inputs(100.0, k, t, r, sigma)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let spots_slice = spots.as_slice()?;

    // Validate each spot price
    for &s in spots_slice {
        if !s.is_finite() || s <= 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "All spot prices must be positive and finite",
            ));
        }
    }

    let results = BlackScholes::call_price_batch(spots_slice, k, t, r, sigma);
    Ok(PyArray1::from_vec_bound(py, results))
}

/// Calculate put prices for multiple spots
#[pyfunction]
#[pyo3(name = "put_price_batch")]
#[pyo3(signature = (spots, k, t, r, sigma))]
fn bs_put_price_batch<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    k: f64,
    t: f64,
    r: f64,
    sigma: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // Validate common parameters
    validate_inputs(100.0, k, t, r, sigma)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let spots_slice = spots.as_slice()?;

    // Validate each spot price
    for &s in spots_slice {
        if !s.is_finite() || s <= 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "All spot prices must be positive and finite",
            ));
        }
    }

    let results = BlackScholes::put_price_batch(spots_slice, k, t, r, sigma);
    Ok(PyArray1::from_vec_bound(py, results))
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
    m.add_function(wrap_pyfunction!(b76_implied_volatility, m)?)?;
    Ok(())
}

/// Calculate Black76 call option price
#[pyfunction]
#[pyo3(name = "call_price")]
#[pyo3(signature = (forward, strike, time, rate, sigma))]
fn b76_call_price(forward: f64, strike: f64, time: f64, rate: f64, sigma: f64) -> PyResult<f64> {
    if forward <= 0.0 || strike <= 0.0 || time <= 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "forward, strike, time, and sigma must be positive",
        ));
    }
    if !forward.is_finite()
        || !strike.is_finite()
        || !time.is_finite()
        || !rate.is_finite()
        || !sigma.is_finite()
    {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "All parameters must be finite",
        ));
    }

    let params = Black76Params::new(forward, strike, time, rate, sigma);
    Ok(Black76::call_price(&params))
}

/// Calculate Black76 put option price
#[pyfunction]
#[pyo3(name = "put_price")]
#[pyo3(signature = (forward, strike, time, rate, sigma))]
fn b76_put_price(forward: f64, strike: f64, time: f64, rate: f64, sigma: f64) -> PyResult<f64> {
    if forward <= 0.0 || strike <= 0.0 || time <= 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "forward, strike, time, and sigma must be positive",
        ));
    }
    if !forward.is_finite()
        || !strike.is_finite()
        || !time.is_finite()
        || !rate.is_finite()
        || !sigma.is_finite()
    {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "All parameters must be finite",
        ));
    }

    let params = Black76Params::new(forward, strike, time, rate, sigma);
    Ok(Black76::put_price(&params))
}

/// Calculate call prices for multiple forwards
#[pyfunction]
#[pyo3(name = "call_price_batch")]
#[pyo3(signature = (forwards, strike, time, rate, sigma))]
fn b76_call_price_batch<'py>(
    py: Python<'py>,
    forwards: PyReadonlyArray1<f64>,
    strike: f64,
    time: f64,
    rate: f64,
    sigma: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // Validate common parameters
    if strike <= 0.0 || time <= 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "strike, time, and sigma must be positive",
        ));
    }

    let forwards_slice = forwards.as_slice()?;

    // Validate each forward price
    for &f in forwards_slice {
        if !f.is_finite() || f <= 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "All forward prices must be positive and finite",
            ));
        }
    }

    let results: Vec<f64> = forwards_slice
        .iter()
        .map(|&forward| {
            let params = Black76Params::new(forward, strike, time, rate, sigma);
            Black76::call_price(&params)
        })
        .collect();

    Ok(PyArray1::from_vec_bound(py, results))
}

/// Calculate put prices for multiple forwards
#[pyfunction]
#[pyo3(name = "put_price_batch")]
#[pyo3(signature = (forwards, strike, time, rate, sigma))]
fn b76_put_price_batch<'py>(
    py: Python<'py>,
    forwards: PyReadonlyArray1<f64>,
    strike: f64,
    time: f64,
    rate: f64,
    sigma: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // Validate common parameters
    if strike <= 0.0 || time <= 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "strike, time, and sigma must be positive",
        ));
    }

    let forwards_slice = forwards.as_slice()?;

    // Validate each forward price
    for &f in forwards_slice {
        if !f.is_finite() || f <= 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "All forward prices must be positive and finite",
            ));
        }
    }

    let results: Vec<f64> = forwards_slice
        .iter()
        .map(|&forward| {
            let params = Black76Params::new(forward, strike, time, rate, sigma);
            Black76::put_price(&params)
        })
        .collect();

    Ok(PyArray1::from_vec_bound(py, results))
}

/// Calculate all Greeks for Black76 option
#[pyfunction]
#[pyo3(name = "greeks")]
#[pyo3(signature = (forward, strike, time, rate, sigma, is_call=true))]
fn b76_greeks(
    forward: f64,
    strike: f64,
    time: f64,
    rate: f64,
    sigma: f64,
    is_call: bool,
) -> PyResult<PyGreeks> {
    if forward <= 0.0 || strike <= 0.0 || time <= 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "forward, strike, time, and sigma must be positive",
        ));
    }
    if !forward.is_finite()
        || !strike.is_finite()
        || !time.is_finite()
        || !rate.is_finite()
        || !sigma.is_finite()
    {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "All parameters must be finite",
        ));
    }

    let params = Black76Params::new(forward, strike, time, rate, sigma);
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
