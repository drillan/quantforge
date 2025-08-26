use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

use crate::models::black76::{Black76, Black76Params};
use crate::models::black_scholes_model::{BlackScholes, BlackScholesParams};
use crate::models::merton::{MertonModel, MertonParams};
use crate::models::PricingModel;
use crate::traits::{BatchProcessor, BatchProcessorWithDividend};
use crate::validation::validate_inputs;

/// Generic call option processor
struct CallOptionProcessor<M: PricingModel> {
    _phantom: std::marker::PhantomData<M>,
}

impl<M: PricingModel> BatchProcessor for CallOptionProcessor<M>
where
    M::Params: Send + Sync,
{
    type Params = M::Params;
    type Output = f64;
    
    fn create_params(&self, price: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        unimplemented!("Specialized implementations required")
    }
    
    fn process_single(&self, params: &Self::Params) -> Self::Output {
        M::call_price(params)
    }
}

/// Generic put option processor
struct PutOptionProcessor<M: PricingModel> {
    _phantom: std::marker::PhantomData<M>,
}

impl<M: PricingModel> BatchProcessor for PutOptionProcessor<M>
where
    M::Params: Send + Sync,
{
    type Params = M::Params;
    type Output = f64;
    
    fn create_params(&self, price: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        unimplemented!("Specialized implementations required")
    }
    
    fn process_single(&self, params: &Self::Params) -> Self::Output {
        M::put_price(params)
    }
}

/// Specialized implementation for Black-Scholes call
struct BSCallProcessor;

impl BatchProcessor for BSCallProcessor {
    type Params = BlackScholesParams;
    type Output = f64;
    
    fn create_params(&self, spot: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        BlackScholesParams {
            spot,
            strike: k,
            time: t,
            rate: r,
            sigma,
        }
    }
    
    fn process_single(&self, params: &Self::Params) -> Self::Output {
        BlackScholes::call_price(params)
    }
}

/// Specialized implementation for Black-Scholes put
struct BSPutProcessor;

impl BatchProcessor for BSPutProcessor {
    type Params = BlackScholesParams;
    type Output = f64;
    
    fn create_params(&self, spot: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        BlackScholesParams {
            spot,
            strike: k,
            time: t,
            rate: r,
            sigma,
        }
    }
    
    fn process_single(&self, params: &Self::Params) -> Self::Output {
        BlackScholes::put_price(params)
    }
}

/// Specialized implementation for Black76 call
struct B76CallProcessor;

impl BatchProcessor for B76CallProcessor {
    type Params = Black76Params;
    type Output = f64;
    
    fn create_params(&self, forward: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        Black76Params::new(forward, k, t, r, sigma)
    }
    
    fn process_single(&self, params: &Self::Params) -> Self::Output {
        Black76::call_price(params)
    }
}

/// Specialized implementation for Black76 put
struct B76PutProcessor;

impl BatchProcessor for B76PutProcessor {
    type Params = Black76Params;
    type Output = f64;
    
    fn create_params(&self, forward: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        Black76Params::new(forward, k, t, r, sigma)
    }
    
    fn process_single(&self, params: &Self::Params) -> Self::Output {
        Black76::put_price(params)
    }
}

/// Merton model processors with dividend support
struct MertonCallProcessor;

impl BatchProcessor for MertonCallProcessor {
    type Params = MertonParams;
    type Output = f64;
    
    fn create_params(&self, spot: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        MertonParams {
            spot,
            strike: k,
            time: t,
            rate: r,
            div_yield: 0.0,
            sigma,
        }
    }
    
    fn process_single(&self, params: &Self::Params) -> Self::Output {
        MertonModel::call_price(params)
    }
}

impl BatchProcessorWithDividend for MertonCallProcessor {
    type ParamsWithDividend = MertonParams;
    
    fn create_params_with_dividend(
        &self,
        spot: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
    ) -> Self::ParamsWithDividend {
        MertonParams {
            spot,
            strike: k,
            time: t,
            rate: r,
            div_yield: q,
            sigma,
        }
    }
    
    fn process_single_with_dividend(&self, params: &Self::ParamsWithDividend) -> Self::Output {
        MertonModel::call_price(params)
    }
}

struct MertonPutProcessor;

impl BatchProcessor for MertonPutProcessor {
    type Params = MertonParams;
    type Output = f64;
    
    fn create_params(&self, spot: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        MertonParams {
            spot,
            strike: k,
            time: t,
            rate: r,
            div_yield: 0.0,
            sigma,
        }
    }
    
    fn process_single(&self, params: &Self::Params) -> Self::Output {
        MertonModel::put_price(params)
    }
}

impl BatchProcessorWithDividend for MertonPutProcessor {
    type ParamsWithDividend = MertonParams;
    
    fn create_params_with_dividend(
        &self,
        spot: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
    ) -> Self::ParamsWithDividend {
        MertonParams {
            spot,
            strike: k,
            time: t,
            rate: r,
            div_yield: q,
            sigma,
        }
    }
    
    fn process_single_with_dividend(&self, params: &Self::ParamsWithDividend) -> Self::Output {
        MertonModel::put_price(params)
    }
}

/// Black-Scholes module implementation using generic processors
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
    let processor = BSCallProcessor;
    processor.process_batch(py, spots, k, t, r, sigma, "spot")
}

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
    let processor = BSPutProcessor;
    processor.process_batch(py, spots, k, t, r, sigma, "spot")
}

// Greeks and implied volatility remain the same for now
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
        theta: greeks.theta,
        vega: greeks.vega,
        rho: greeks.rho,
    })
}

#[pyfunction]
#[pyo3(name = "implied_volatility")]
#[pyo3(signature = (price, s, k, t, r, is_call=true, initial_guess=None))]
fn bs_implied_volatility(
    price: f64,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    is_call: bool,
    initial_guess: Option<f64>,
) -> PyResult<f64> {
    if price <= 0.0 || s <= 0.0 || k <= 0.0 || t <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "price, s, k, and t must be positive",
        ));
    }
    
    let params = BlackScholesParams {
        spot: s,
        strike: k,
        time: t,
        rate: r,
        sigma: 0.0,
    };
    
    BlackScholes::implied_volatility(&params, price, is_call, initial_guess)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

/// Black76 module implementation using generic processors
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

#[pyfunction]
#[pyo3(name = "call_price")]
#[pyo3(signature = (f, k, t, r, sigma))]
fn b76_call_price(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    if f <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "f, k, t, and sigma must be positive",
        ));
    }
    
    let params = Black76Params::new(f, k, t, r, sigma);
    Ok(Black76::call_price(&params))
}

#[pyfunction]
#[pyo3(name = "put_price")]
#[pyo3(signature = (f, k, t, r, sigma))]
fn b76_put_price(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    if f <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "f, k, t, and sigma must be positive",
        ));
    }
    
    let params = Black76Params::new(f, k, t, r, sigma);
    Ok(Black76::put_price(&params))
}

#[pyfunction]
#[pyo3(name = "call_price_batch")]
#[pyo3(signature = (fs, k, t, r, sigma))]
fn b76_call_price_batch<'py>(
    py: Python<'py>,
    fs: PyReadonlyArray1<f64>,
    k: f64,
    t: f64,
    r: f64,
    sigma: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let processor = B76CallProcessor;
    processor.process_batch(py, fs, k, t, r, sigma, "forward")
}

#[pyfunction]
#[pyo3(name = "put_price_batch")]
#[pyo3(signature = (fs, k, t, r, sigma))]
fn b76_put_price_batch<'py>(
    py: Python<'py>,
    fs: PyReadonlyArray1<f64>,
    k: f64,
    t: f64,
    r: f64,
    sigma: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let processor = B76PutProcessor;
    processor.process_batch(py, fs, k, t, r, sigma, "forward")
}

#[pyfunction]
#[pyo3(name = "greeks")]
#[pyo3(signature = (f, k, t, r, sigma, is_call=true))]
fn b76_greeks(f: f64, k: f64, t: f64, r: f64, sigma: f64, is_call: bool) -> PyResult<PyGreeks> {
    if f <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "f, k, t, and sigma must be positive",
        ));
    }
    
    let params = Black76Params::new(f, k, t, r, sigma);
    let greeks = Black76::greeks(&params, is_call);
    
    Ok(PyGreeks {
        delta: greeks.delta,
        gamma: greeks.gamma,
        theta: greeks.theta,
        vega: greeks.vega,
        rho: greeks.rho,
    })
}

#[pyfunction]
#[pyo3(name = "implied_volatility")]
#[pyo3(signature = (price, f, k, t, r, is_call=true, initial_guess=None))]
fn b76_implied_volatility(
    price: f64,
    f: f64,
    k: f64,
    t: f64,
    r: f64,
    is_call: bool,
    initial_guess: Option<f64>,
) -> PyResult<f64> {
    if price <= 0.0 || f <= 0.0 || k <= 0.0 || t <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "price, f, k, and t must be positive",
        ));
    }
    
    let params = Black76Params::new(f, k, t, r, 0.0);
    Black76::implied_volatility(&params, price, is_call, initial_guess)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

/// Merton module implementation using generic processors
#[pymodule]
pub fn merton(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(merton_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(merton_put_price, m)?)?;
    m.add_function(wrap_pyfunction!(merton_call_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(merton_put_price_batch, m)?)?;
    m.add_function(wrap_pyfunction!(merton_call_price_batch_q, m)?)?;
    m.add_function(wrap_pyfunction!(merton_put_price_batch_q, m)?)?;
    m.add_function(wrap_pyfunction!(merton_greeks, m)?)?;
    m.add_function(wrap_pyfunction!(merton_implied_volatility, m)?)?;
    Ok(())
}

#[pyfunction]
#[pyo3(name = "call_price")]
#[pyo3(signature = (s, k, t, r, q, sigma))]
fn merton_call_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    validate_inputs(s, k, t, r, sigma)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    
    let params = MertonParams {
        spot: s,
        strike: k,
        time: t,
        rate: r,
        div_yield: q,
        sigma,
    };
    
    Ok(MertonModel::call_price(&params))
}

#[pyfunction]
#[pyo3(name = "put_price")]
#[pyo3(signature = (s, k, t, r, q, sigma))]
fn merton_put_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    validate_inputs(s, k, t, r, sigma)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    
    let params = MertonParams {
        spot: s,
        strike: k,
        time: t,
        rate: r,
        div_yield: q,
        sigma,
    };
    
    Ok(MertonModel::put_price(&params))
}

#[pyfunction]
#[pyo3(name = "call_price_batch")]
#[pyo3(signature = (spots, k, t, r, sigma))]
fn merton_call_price_batch<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    k: f64,
    t: f64,
    r: f64,
    sigma: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let processor = MertonCallProcessor;
    processor.process_batch(py, spots, k, t, r, sigma, "spot")
}

#[pyfunction]
#[pyo3(name = "put_price_batch")]
#[pyo3(signature = (spots, k, t, r, sigma))]
fn merton_put_price_batch<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    k: f64,
    t: f64,
    r: f64,
    sigma: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let processor = MertonPutProcessor;
    processor.process_batch(py, spots, k, t, r, sigma, "spot")
}

#[pyfunction]
#[pyo3(name = "call_price_batch_q")]
#[pyo3(signature = (spots, k, t, r, q, sigma))]
fn merton_call_price_batch_q<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let processor = MertonCallProcessor;
    processor.process_batch_with_dividend(py, spots, k, t, r, q, sigma, "spot")
}

#[pyfunction]
#[pyo3(name = "put_price_batch_q")]
#[pyo3(signature = (spots, k, t, r, q, sigma))]
fn merton_put_price_batch_q<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let processor = MertonPutProcessor;
    processor.process_batch_with_dividend(py, spots, k, t, r, q, sigma, "spot")
}

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
    validate_inputs(s, k, t, r, sigma)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    
    let params = MertonParams {
        spot: s,
        strike: k,
        time: t,
        rate: r,
        div_yield: q,
        sigma,
    };
    
    let greeks = MertonModel::greeks(&params, is_call);
    
    Ok(PyMertonGreeks {
        delta: greeks.delta,
        gamma: greeks.gamma,
        theta: greeks.theta,
        vega: greeks.vega,
        rho: greeks.rho,
        psi: greeks.psi,
    })
}

#[pyfunction]
#[pyo3(name = "implied_volatility")]
#[pyo3(signature = (price, s, k, t, r, q, is_call=true, initial_guess=None))]
fn merton_implied_volatility(
    price: f64,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    is_call: bool,
    initial_guess: Option<f64>,
) -> PyResult<f64> {
    if price <= 0.0 || s <= 0.0 || k <= 0.0 || t <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "price, s, k, and t must be positive",
        ));
    }
    
    let params = MertonParams {
        spot: s,
        strike: k,
        time: t,
        rate: r,
        div_yield: q,
        sigma: 0.0,
    };
    
    MertonModel::implied_volatility(&params, price, is_call, initial_guess)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

/// Greeks data class for Python
#[pyclass(name = "Greeks")]
#[derive(Clone)]
pub struct PyGreeks {
    #[pyo3(get)]
    pub delta: f64,
    #[pyo3(get)]
    pub gamma: f64,
    #[pyo3(get)]
    pub theta: f64,
    #[pyo3(get)]
    pub vega: f64,
    #[pyo3(get)]
    pub rho: f64,
}

#[pymethods]
impl PyGreeks {
    fn __repr__(&self) -> String {
        format!(
            "Greeks(delta={:.6}, gamma={:.6}, theta={:.6}, vega={:.6}, rho={:.6})",
            self.delta, self.gamma, self.theta, self.vega, self.rho
        )
    }
}

/// Merton Greeks data class for Python
#[pyclass(name = "MertonGreeks")]
#[derive(Clone)]
pub struct PyMertonGreeks {
    #[pyo3(get)]
    pub delta: f64,
    #[pyo3(get)]
    pub gamma: f64,
    #[pyo3(get)]
    pub theta: f64,
    #[pyo3(get)]
    pub vega: f64,
    #[pyo3(get)]
    pub rho: f64,
    #[pyo3(get)]
    pub psi: f64,
}

#[pymethods]
impl PyMertonGreeks {
    fn __repr__(&self) -> String {
        format!(
            "MertonGreeks(delta={:.6}, gamma={:.6}, theta={:.6}, vega={:.6}, rho={:.6}, psi={:.6})",
            self.delta, self.gamma, self.theta, self.vega, self.rho, self.psi
        )
    }
}