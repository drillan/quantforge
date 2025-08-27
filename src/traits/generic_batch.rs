use crate::flexible_array::FlexibleArray;
use crate::models::GreeksBatch;
use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::fmt::Debug;

/// Parameters for batch option calculations
#[derive(Debug, Clone)]
pub struct BatchParams {
    pub spots: Vec<f64>,
    pub strikes: Vec<f64>,
    pub times: Vec<f64>,
    pub rates: Vec<f64>,
    pub qs: Vec<f64>,
    pub sigmas: Vec<f64>,
    pub is_calls: Vec<bool>,
}

/// Generic batch processing trait for option models
pub trait OptionModelBatch: Send + Sync {
    type Error: Debug + ToString;

    /// Calculate Greeks for a batch of options
    fn calculate_greeks_batch(params: BatchParams) -> Result<GreeksBatch, Self::Error>;

    /// Generic Python wrapper for Greeks batch calculation
    #[allow(clippy::too_many_arguments)]
    fn py_greeks_batch<'py>(
        py: Python<'py>,
        spots: FlexibleArray<'py>,
        strikes: FlexibleArray<'py>,
        times: FlexibleArray<'py>,
        rates: FlexibleArray<'py>,
        qs: FlexibleArray<'py>,
        sigmas: FlexibleArray<'py>,
        is_calls: FlexibleArray<'py>,
    ) -> PyResult<Bound<'py, PyDict>> {
        // Convert flexible arrays to Vec with unified error handling
        let spots_vec = spots
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let strikes_vec = strikes
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let times_vec = times
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let rates_vec = rates
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let qs_vec = qs
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let sigmas_vec = sigmas
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let is_calls_vec: Vec<bool> = is_calls
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec()
            .into_iter()
            .map(|v| v != 0.0)
            .collect();

        // Call the specific model implementation
        let greeks_batch = Self::calculate_greeks_batch(BatchParams {
            spots: spots_vec,
            strikes: strikes_vec,
            times: times_vec,
            rates: rates_vec,
            qs: qs_vec,
            sigmas: sigmas_vec,
            is_calls: is_calls_vec,
        })
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

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
}

/// Parameters for batch implied volatility calculations
#[derive(Debug, Clone)]
pub struct IVBatchParams {
    pub prices: Vec<f64>,
    pub spots: Vec<f64>,
    pub strikes: Vec<f64>,
    pub times: Vec<f64>,
    pub rates: Vec<f64>,
    pub qs: Vec<f64>,
    pub is_calls: Vec<bool>,
}

/// Generic batch processing for implied volatility
pub trait ImpliedVolatilityBatch: Send + Sync {
    type Error: Debug + ToString;

    fn calculate_iv_batch(params: IVBatchParams) -> Result<Vec<f64>, Self::Error>;

    #[allow(clippy::too_many_arguments)]
    fn py_iv_batch<'py>(
        py: Python<'py>,
        prices: PyReadonlyArray1<'py, f64>,
        spots: FlexibleArray<'py>,
        strikes: FlexibleArray<'py>,
        times: FlexibleArray<'py>,
        rates: FlexibleArray<'py>,
        qs: FlexibleArray<'py>,
        is_calls: FlexibleArray<'py>,
    ) -> PyResult<Bound<'py, PyArray1<f64>>> {
        let prices_vec = prices.as_slice()?.to_vec();
        let spots_vec = spots
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let strikes_vec = strikes
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let times_vec = times
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let rates_vec = rates
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let qs_vec = qs
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let is_calls_vec: Vec<bool> = is_calls
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec()
            .into_iter()
            .map(|v| v != 0.0)
            .collect();

        let results = Self::calculate_iv_batch(IVBatchParams {
            prices: prices_vec,
            spots: spots_vec,
            strikes: strikes_vec,
            times: times_vec,
            rates: rates_vec,
            qs: qs_vec,
            is_calls: is_calls_vec,
        })
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        Ok(PyArray1::from_vec_bound(py, results))
    }
}

/// Generic batch processing for option prices
pub trait PriceBatch: Send + Sync {
    type Error: Debug + ToString;

    fn calculate_price_batch(params: BatchParams) -> Result<Vec<f64>, Self::Error>;

    #[allow(clippy::too_many_arguments)]
    fn py_price_batch<'py>(
        py: Python<'py>,
        spots: FlexibleArray<'py>,
        strikes: FlexibleArray<'py>,
        times: FlexibleArray<'py>,
        rates: FlexibleArray<'py>,
        qs: FlexibleArray<'py>,
        sigmas: FlexibleArray<'py>,
        is_calls: FlexibleArray<'py>,
    ) -> PyResult<Bound<'py, PyArray1<f64>>> {
        let spots_vec = spots
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let strikes_vec = strikes
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let times_vec = times
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let rates_vec = rates
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let qs_vec = qs
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let sigmas_vec = sigmas
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec();
        let is_calls_vec: Vec<bool> = is_calls
            .to_array_like()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?
            .to_vec()
            .into_iter()
            .map(|v| v != 0.0)
            .collect();

        let prices = Self::calculate_price_batch(BatchParams {
            spots: spots_vec,
            strikes: strikes_vec,
            times: times_vec,
            rates: rates_vec,
            qs: qs_vec,
            sigmas: sigmas_vec,
            is_calls: is_calls_vec,
        })
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        Ok(PyArray1::from_vec_bound(py, prices))
    }
}
