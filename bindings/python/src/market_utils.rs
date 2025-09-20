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
    /// Create a new PricingConfig
    ///
    /// Args:
    ///     max_spread_pct: Maximum spread as percentage (e.g., 0.5 for 50%). None means no limit.
    ///     abnormal_handling: How to handle abnormal spreads ('return_nan', 'log_and_continue', 'return_error')
    ///     crossed_handling: How to handle crossed spreads ('return_nan', 'swap_and_continue', 'return_error')
    #[new]
    #[pyo3(signature = (max_spread_pct=None, abnormal_handling="return_nan", crossed_handling="return_nan"))]
    fn new(
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

/// Register the market_utils module with Python
pub fn register_module(parent_module: &Bound<'_, PyModule>) -> PyResult<()> {
    let market_utils_module = PyModule::new(parent_module.py(), "market_utils")?;

    // Add configuration class
    market_utils_module.add_class::<PyPricingConfig>()?;

    // Add functions
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

    parent_module.add_submodule(&market_utils_module)?;
    Ok(())
}