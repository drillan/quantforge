//! Python bindings for market pricing utilities

use pyo3::prelude::*;
use quantforge_core::market_utils::{
    mid_price as core_mid_price, mid_price_with_config as core_mid_price_with_config,
    spread as core_spread, spread_pct as core_spread_pct, weighted_mid_price,
    weighted_mid_price_with_config, AbnormalSpreadHandling as CoreAbnormalSpreadHandling,
    CrossedSpreadHandling as CoreCrossedSpreadHandling, MarketPricingConfig as CorePricingConfig,
};

/// Python wrapper for MarketPricingConfig
#[pyclass(name = "PricingConfig")]
#[derive(Clone)]
pub struct PyPricingConfig {
    inner: CorePricingConfig,
}

#[pymethods]
impl PyPricingConfig {
    /// Create a new PricingConfig with default threshold
    #[new]
    #[pyo3(signature = ())]
    fn new() -> PyResult<Self> {
        Ok(Self {
            inner: CorePricingConfig::default(),
        })
    }

    /// Create a custom PricingConfig
    ///
    /// Args:
    ///     max_spread_pct: Maximum spread as percentage (e.g., 0.5 for 50%). Pass None to disable threshold.
    ///     abnormal_handling: How to handle abnormal spreads ('return_nan', 'log_and_continue', 'return_error')
    ///     crossed_handling: How to handle crossed spreads ('return_nan', 'swap_and_continue', 'return_error')
    #[staticmethod]
    #[pyo3(signature = (max_spread_pct=None, abnormal_handling="return_nan", crossed_handling="return_nan"))]
    fn with_config(
        max_spread_pct: Option<f64>,
        abnormal_handling: &str,
        crossed_handling: &str,
    ) -> PyResult<Self> {
        let abnormal = match abnormal_handling {
            "return_nan" => CoreAbnormalSpreadHandling::ReturnNaN,
            "log_and_continue" => CoreAbnormalSpreadHandling::LogAndContinue,
            "return_error" => CoreAbnormalSpreadHandling::ReturnError,
            _ => {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                    "Invalid abnormal_handling: {abnormal_handling}. Use 'return_nan', 'log_and_continue', or 'return_error'"
                )))
            }
        };

        let crossed = match crossed_handling {
            "return_nan" => CoreCrossedSpreadHandling::ReturnNaN,
            "swap_and_continue" => CoreCrossedSpreadHandling::SwapAndContinue,
            "return_error" => CoreCrossedSpreadHandling::ReturnError,
            _ => {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                    "Invalid crossed_handling: {crossed_handling}. Use 'return_nan', 'swap_and_continue', or 'return_error'"
                )))
            }
        };

        Ok(Self {
            inner: CorePricingConfig {
                max_spread_pct,
                abnormal_handling: abnormal,
                crossed_handling: crossed,
            },
        })
    }

    /// Get the maximum spread percentage threshold
    #[getter]
    fn max_spread_pct(&self) -> Option<f64> {
        self.inner.max_spread_pct
    }

    /// Get the abnormal spread handling strategy
    #[getter]
    fn abnormal_handling(&self) -> &str {
        match self.inner.abnormal_handling {
            CoreAbnormalSpreadHandling::ReturnNaN => "return_nan",
            CoreAbnormalSpreadHandling::LogAndContinue => "log_and_continue",
            CoreAbnormalSpreadHandling::ReturnError => "return_error",
        }
    }

    /// Get the crossed spread handling strategy
    #[getter]
    fn crossed_handling(&self) -> &str {
        match self.inner.crossed_handling {
            CoreCrossedSpreadHandling::ReturnNaN => "return_nan",
            CoreCrossedSpreadHandling::SwapAndContinue => "swap_and_continue",
            CoreCrossedSpreadHandling::ReturnError => "return_error",
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "PricingConfig(max_spread_pct={:?}, abnormal_handling='{}', crossed_handling='{}')",
            self.inner.max_spread_pct,
            self.abnormal_handling(),
            self.crossed_handling()
        )
    }
}

/// Calculate simple mid price from bid and ask
///
/// Args:
///     bid: Bid price
///     ask: Ask price
///
/// Returns:
///     Mid price, or NaN if inputs are invalid or spread exceeds default threshold (50%)
#[pyfunction]
#[pyo3(name = "mid_price")]
pub fn py_mid_price(bid: f64, ask: f64) -> f64 {
    core_mid_price(bid, ask)
}

/// Calculate simple mid price with custom configuration
///
/// Args:
///     bid: Bid price
///     ask: Ask price
///     config: PricingConfig object with custom settings
///
/// Returns:
///     Mid price, or NaN based on configuration
#[pyfunction]
#[pyo3(name = "mid_price_with_config")]
pub fn py_mid_price_with_config(bid: f64, ask: f64, config: &PyPricingConfig) -> f64 {
    core_mid_price_with_config(bid, ask, &config.inner)
}

/// Calculate quantity-weighted mid price
///
/// Args:
///     bid: Bid price
///     bid_qty: Bid quantity (optional)
///     ask: Ask price
///     ask_qty: Ask quantity (optional)
///
/// Returns:
///     Weighted mid price, or simple mid if quantities are missing/invalid
#[pyfunction]
#[pyo3(name = "weighted_mid_price")]
#[pyo3(signature = (bid, ask, bid_qty=None, ask_qty=None))]
pub fn py_weighted_mid_price(
    bid: f64,
    ask: f64,
    bid_qty: Option<f64>,
    ask_qty: Option<f64>,
) -> f64 {
    weighted_mid_price(bid, bid_qty, ask, ask_qty)
}

/// Calculate quantity-weighted mid price with custom configuration
///
/// Args:
///     bid: Bid price
///     bid_qty: Bid quantity (optional)
///     ask: Ask price
///     ask_qty: Ask quantity (optional)
///     config: PricingConfig object with custom settings
///
/// Returns:
///     Weighted mid price, or simple mid if quantities are missing/invalid
#[pyfunction]
#[pyo3(name = "weighted_mid_price_with_config")]
#[pyo3(signature = (bid, ask, config, bid_qty=None, ask_qty=None))]
pub fn py_weighted_mid_price_with_config(
    bid: f64,
    ask: f64,
    config: &PyPricingConfig,
    bid_qty: Option<f64>,
    ask_qty: Option<f64>,
) -> f64 {
    weighted_mid_price_with_config(bid, bid_qty, ask, ask_qty, &config.inner)
}

/// Calculate absolute spread (ask - bid)
///
/// Args:
///     bid: Bid price
///     ask: Ask price
///
/// Returns:
///     Absolute spread (can be negative if crossed)
#[pyfunction]
#[pyo3(name = "spread")]
pub fn py_spread(bid: f64, ask: f64) -> f64 {
    core_spread(bid, ask)
}

/// Calculate spread as percentage of mid price
///
/// Args:
///     bid: Bid price
///     ask: Ask price
///
/// Returns:
///     Spread percentage, or NaN if crossed or mid is zero
#[pyfunction]
#[pyo3(name = "spread_pct")]
pub fn py_spread_pct(bid: f64, ask: f64) -> f64 {
    core_spread_pct(bid, ask)
}

// =============================================================================
// Batch Processing Functions
// =============================================================================

use arrow::array::Float64Array;
use numpy::{IntoPyArray, PyArrayLike1};
use quantforge_core::market_utils::{
    mid_price_batch as core_mid_price_batch,
    mid_price_batch_with_config as core_mid_price_batch_with_config,
    mid_price_batch_with_metrics as core_mid_price_batch_with_metrics,
    spread_batch as core_spread_batch, spread_pct_batch as core_spread_pct_batch,
    weighted_mid_price_batch as core_weighted_mid_price_batch,
    weighted_mid_price_batch_with_config as core_weighted_mid_price_batch_with_config,
    BatchMetrics as CoreBatchMetrics,
};

/// Python wrapper for BatchMetrics
#[pyclass(name = "BatchMetrics")]
#[derive(Clone)]
pub struct PyBatchMetrics {
    inner: CoreBatchMetrics,
}

#[pymethods]
impl PyBatchMetrics {
    /// Get total number of elements processed
    #[getter]
    fn total_processed(&self) -> usize {
        self.inner.total_processed
    }

    /// Get number of NaN results
    #[getter]
    fn nan_count(&self) -> usize {
        self.inner.nan_count
    }

    /// Get number of crossed spreads
    #[getter]
    fn crossed_spreads(&self) -> usize {
        self.inner.crossed_spreads
    }

    /// Get number of abnormal spreads
    #[getter]
    fn abnormal_spreads(&self) -> usize {
        self.inner.abnormal_spreads
    }

    /// Get mean spread percentage
    #[getter]
    fn mean_spread_pct(&self) -> f64 {
        self.inner.mean_spread_pct
    }

    /// Get maximum spread percentage
    #[getter]
    fn max_spread_pct(&self) -> f64 {
        self.inner.max_spread_pct
    }

    fn __repr__(&self) -> String {
        format!(
            "BatchMetrics(total={}, nan={}, crossed={}, abnormal={}, mean_spread={:.2}%, max_spread={:.2}%)",
            self.inner.total_processed,
            self.inner.nan_count,
            self.inner.crossed_spreads,
            self.inner.abnormal_spreads,
            self.inner.mean_spread_pct * 100.0,
            self.inner.max_spread_pct * 100.0
        )
    }
}

/// Calculate mid prices for batch of bid/ask prices
///
/// Args:
///     bids: Bid prices (numpy array or scalar)
///     asks: Ask prices (numpy array or scalar)
///
/// Returns:
///     Array of mid prices
#[pyfunction]
#[pyo3(name = "mid_price_batch")]
pub fn py_mid_price_batch<'py>(
    py: Python<'py>,
    bids: PyArrayLike1<'_, f64>,
    asks: PyArrayLike1<'_, f64>,
) -> PyResult<Bound<'py, numpy::PyArray1<f64>>> {
    let bids_vec: Vec<f64> = bids.as_slice()?.to_vec();
    let asks_vec: Vec<f64> = asks.as_slice()?.to_vec();
    let bids_array = Float64Array::from(bids_vec);
    let asks_array = Float64Array::from(asks_vec);

    let result = core_mid_price_batch(&bids_array, &asks_array)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

    let result_array = result
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("Expected Float64Array"))?;

    let values: Vec<f64> = result_array.values().to_vec();
    Ok(values.into_pyarray(py))
}

/// Calculate mid prices with custom configuration
///
/// Args:
///     bids: Bid prices (numpy array or scalar)
///     asks: Ask prices (numpy array or scalar)
///     config: PricingConfig object
///
/// Returns:
///     Array of mid prices
#[pyfunction]
#[pyo3(name = "mid_price_batch_with_config")]
pub fn py_mid_price_batch_with_config<'py>(
    py: Python<'py>,
    bids: PyArrayLike1<'_, f64>,
    asks: PyArrayLike1<'_, f64>,
    config: &PyPricingConfig,
) -> PyResult<Bound<'py, numpy::PyArray1<f64>>> {
    let bids_vec: Vec<f64> = bids.as_slice()?.to_vec();
    let asks_vec: Vec<f64> = asks.as_slice()?.to_vec();
    let bids_array = Float64Array::from(bids_vec);
    let asks_array = Float64Array::from(asks_vec);

    let result = core_mid_price_batch_with_config(&bids_array, &asks_array, &config.inner)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

    let result_array = result
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("Expected Float64Array"))?;

    let values: Vec<f64> = result_array.values().to_vec();
    Ok(values.into_pyarray(py))
}

/// Calculate mid prices and collect metrics
///
/// Args:
///     bids: Bid prices (numpy array)
///     asks: Ask prices (numpy array)
///     config: PricingConfig object
///
/// Returns:
///     Tuple of (mid prices array, BatchMetrics)
#[pyfunction]
#[pyo3(name = "mid_price_batch_with_metrics")]
pub fn py_mid_price_batch_with_metrics<'py>(
    py: Python<'py>,
    bids: PyArrayLike1<'_, f64>,
    asks: PyArrayLike1<'_, f64>,
    config: &PyPricingConfig,
) -> PyResult<(Bound<'py, numpy::PyArray1<f64>>, PyBatchMetrics)> {
    let bids_vec: Vec<f64> = bids.as_slice()?.to_vec();
    let asks_vec: Vec<f64> = asks.as_slice()?.to_vec();
    let bids_array = Float64Array::from(bids_vec);
    let asks_array = Float64Array::from(asks_vec);

    let (result, metrics) =
        core_mid_price_batch_with_metrics(&bids_array, &asks_array, &config.inner)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

    let result_array = result
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("Expected Float64Array"))?;

    let values: Vec<f64> = result_array.values().to_vec();
    let py_metrics = PyBatchMetrics { inner: metrics };

    Ok((values.into_pyarray(py), py_metrics))
}

/// Calculate weighted mid prices for batch
///
/// Args:
///     bids: Bid prices (numpy array)
///     bid_qtys: Bid quantities (optional numpy array)
///     asks: Ask prices (numpy array)
///     ask_qtys: Ask quantities (optional numpy array)
///
/// Returns:
///     Array of weighted mid prices
#[pyfunction]
#[pyo3(name = "weighted_mid_price_batch")]
#[pyo3(signature = (bids, asks, bid_qtys=None, ask_qtys=None))]
pub fn py_weighted_mid_price_batch<'py>(
    py: Python<'py>,
    bids: PyArrayLike1<'_, f64>,
    asks: PyArrayLike1<'_, f64>,
    bid_qtys: Option<PyArrayLike1<'_, f64>>,
    ask_qtys: Option<PyArrayLike1<'_, f64>>,
) -> PyResult<Bound<'py, numpy::PyArray1<f64>>> {
    let bids_vec: Vec<f64> = bids.as_slice()?.to_vec();
    let asks_vec: Vec<f64> = asks.as_slice()?.to_vec();
    let bids_array = Float64Array::from(bids_vec);
    let asks_array = Float64Array::from(asks_vec);

    let bid_qtys_array = bid_qtys.map(|q| Float64Array::from(q.as_slice().unwrap().to_vec()));
    let ask_qtys_array = ask_qtys.map(|q| Float64Array::from(q.as_slice().unwrap().to_vec()));

    let result = core_weighted_mid_price_batch(
        &bids_array,
        bid_qtys_array.as_ref(),
        &asks_array,
        ask_qtys_array.as_ref(),
    )
    .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

    let result_array = result
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("Expected Float64Array"))?;

    let values: Vec<f64> = result_array.values().to_vec();
    Ok(values.into_pyarray(py))
}

/// Calculate weighted mid prices with configuration
///
/// Args:
///     bids: Bid prices (numpy array)
///     bid_qtys: Bid quantities (optional numpy array)
///     asks: Ask prices (numpy array)
///     ask_qtys: Ask quantities (optional numpy array)
///     config: PricingConfig object
///
/// Returns:
///     Array of weighted mid prices
#[pyfunction]
#[pyo3(name = "weighted_mid_price_batch_with_config")]
#[pyo3(signature = (bids, asks, config, bid_qtys=None, ask_qtys=None))]
pub fn py_weighted_mid_price_batch_with_config<'py>(
    py: Python<'py>,
    bids: PyArrayLike1<'_, f64>,
    asks: PyArrayLike1<'_, f64>,
    config: &PyPricingConfig,
    bid_qtys: Option<PyArrayLike1<'_, f64>>,
    ask_qtys: Option<PyArrayLike1<'_, f64>>,
) -> PyResult<Bound<'py, numpy::PyArray1<f64>>> {
    let bids_vec: Vec<f64> = bids.as_slice()?.to_vec();
    let asks_vec: Vec<f64> = asks.as_slice()?.to_vec();
    let bids_array = Float64Array::from(bids_vec);
    let asks_array = Float64Array::from(asks_vec);

    let bid_qtys_array = bid_qtys.map(|q| Float64Array::from(q.as_slice().unwrap().to_vec()));
    let ask_qtys_array = ask_qtys.map(|q| Float64Array::from(q.as_slice().unwrap().to_vec()));

    let result = core_weighted_mid_price_batch_with_config(
        &bids_array,
        bid_qtys_array.as_ref(),
        &asks_array,
        ask_qtys_array.as_ref(),
        &config.inner,
    )
    .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

    let result_array = result
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("Expected Float64Array"))?;

    let values: Vec<f64> = result_array.values().to_vec();
    Ok(values.into_pyarray(py))
}

/// Calculate absolute spreads for batch
///
/// Args:
///     bids: Bid prices (numpy array)
///     asks: Ask prices (numpy array)
///
/// Returns:
///     Array of spreads (ask - bid)
#[pyfunction]
#[pyo3(name = "spread_batch")]
pub fn py_spread_batch<'py>(
    py: Python<'py>,
    bids: PyArrayLike1<'_, f64>,
    asks: PyArrayLike1<'_, f64>,
) -> PyResult<Bound<'py, numpy::PyArray1<f64>>> {
    let bids_vec: Vec<f64> = bids.as_slice()?.to_vec();
    let asks_vec: Vec<f64> = asks.as_slice()?.to_vec();
    let bids_array = Float64Array::from(bids_vec);
    let asks_array = Float64Array::from(asks_vec);

    let result = core_spread_batch(&bids_array, &asks_array)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

    let result_array = result
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("Expected Float64Array"))?;

    let values: Vec<f64> = result_array.values().to_vec();
    Ok(values.into_pyarray(py))
}

/// Calculate spread percentages for batch
///
/// Args:
///     bids: Bid prices (numpy array)
///     asks: Ask prices (numpy array)
///
/// Returns:
///     Array of spread percentages
#[pyfunction]
#[pyo3(name = "spread_pct_batch")]
pub fn py_spread_pct_batch<'py>(
    py: Python<'py>,
    bids: PyArrayLike1<'_, f64>,
    asks: PyArrayLike1<'_, f64>,
) -> PyResult<Bound<'py, numpy::PyArray1<f64>>> {
    let bids_vec: Vec<f64> = bids.as_slice()?.to_vec();
    let asks_vec: Vec<f64> = asks.as_slice()?.to_vec();
    let bids_array = Float64Array::from(bids_vec);
    let asks_array = Float64Array::from(asks_vec);

    let result = core_spread_pct_batch(&bids_array, &asks_array)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

    let result_array = result
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("Expected Float64Array"))?;

    let values: Vec<f64> = result_array.values().to_vec();
    Ok(values.into_pyarray(py))
}

/// Register the market_utils module with Python
pub fn register_module(parent_module: &Bound<'_, PyModule>) -> PyResult<()> {
    let market_utils_module = PyModule::new(parent_module.py(), "market_utils")?;

    // Add configuration class
    market_utils_module.add_class::<PyPricingConfig>()?;
    market_utils_module.add_class::<PyBatchMetrics>()?;

    // Add single-value functions
    market_utils_module.add_function(wrap_pyfunction!(py_mid_price, &market_utils_module)?)?;
    market_utils_module.add_function(wrap_pyfunction!(
        py_mid_price_with_config,
        &market_utils_module
    )?)?;
    market_utils_module.add_function(wrap_pyfunction!(
        py_weighted_mid_price,
        &market_utils_module
    )?)?;
    market_utils_module.add_function(wrap_pyfunction!(
        py_weighted_mid_price_with_config,
        &market_utils_module
    )?)?;
    market_utils_module.add_function(wrap_pyfunction!(py_spread, &market_utils_module)?)?;
    market_utils_module.add_function(wrap_pyfunction!(py_spread_pct, &market_utils_module)?)?;

    // Add batch processing functions
    market_utils_module
        .add_function(wrap_pyfunction!(py_mid_price_batch, &market_utils_module)?)?;
    market_utils_module.add_function(wrap_pyfunction!(
        py_mid_price_batch_with_config,
        &market_utils_module
    )?)?;
    market_utils_module.add_function(wrap_pyfunction!(
        py_mid_price_batch_with_metrics,
        &market_utils_module
    )?)?;
    market_utils_module.add_function(wrap_pyfunction!(
        py_weighted_mid_price_batch,
        &market_utils_module
    )?)?;
    market_utils_module.add_function(wrap_pyfunction!(
        py_weighted_mid_price_batch_with_config,
        &market_utils_module
    )?)?;
    market_utils_module.add_function(wrap_pyfunction!(py_spread_batch, &market_utils_module)?)?;
    market_utils_module
        .add_function(wrap_pyfunction!(py_spread_pct_batch, &market_utils_module)?)?;

    parent_module.add_submodule(&market_utils_module)?;
    Ok(())
}
