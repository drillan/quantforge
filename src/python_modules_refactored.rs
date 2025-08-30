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

/// Generic macro for creating batch price functions
macro_rules! impl_batch_price_fn {
    (
        $fn_name:ident,
        $batch_fn:path,
        $doc:literal
    ) => {
        #[doc = $doc]
        #[pyfunction]
        #[pyo3(name = stringify!($fn_name))]
        #[pyo3(signature = (spots, strikes, times, rates, sigmas))]
        fn $fn_name<'py>(
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

            let results = $batch_fn(
                spots_arr,
                strikes_arr,
                times_arr,
                rates_arr,
                sigmas_arr,
            )
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

            Ok(PyArray1::from_vec_bound(py, results))
        }
    };
}

/// Generic macro for creating batch price functions with dividend yield
macro_rules! impl_batch_price_fn_with_q {
    (
        $fn_name:ident,
        $batch_fn:path,
        $doc:literal
    ) => {
        #[doc = $doc]
        #[pyfunction]
        #[pyo3(name = stringify!($fn_name))]
        #[pyo3(signature = (spots, strikes, times, rates, dividend_yields, sigmas))]
        fn $fn_name<'py>(
            py: Python<'py>,
            spots: FlexibleArray<'py>,
            strikes: FlexibleArray<'py>,
            times: FlexibleArray<'py>,
            rates: FlexibleArray<'py>,
            dividend_yields: FlexibleArray<'py>,
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
            let dividend_yields_arr = dividend_yields
                .to_array_like()
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
            let sigmas_arr = sigmas
                .to_array_like()
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

            let results = $batch_fn(
                spots_arr,
                strikes_arr,
                times_arr,
                rates_arr,
                dividend_yields_arr,
                sigmas_arr,
            )
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

            Ok(PyArray1::from_vec_bound(py, results))
        }
    };
}

/// Generic macro for creating IV batch functions
macro_rules! impl_iv_batch_fn {
    (
        $fn_name:ident,
        $batch_fn:path,
        $doc:literal
    ) => {
        #[doc = $doc]
        #[pyfunction]
        #[pyo3(name = stringify!($fn_name))]
        #[pyo3(signature = (prices, spots, strikes, times, rates, sigmas, is_calls))]
        fn $fn_name<'py>(
            py: Python<'py>,
            prices: FlexibleArray<'py>,
            spots: FlexibleArray<'py>,
            strikes: FlexibleArray<'py>,
            times: FlexibleArray<'py>,
            rates: FlexibleArray<'py>,
            sigmas: FlexibleArray<'py>,
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
            let sigmas_arr = sigmas
                .to_array_like()
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
            let is_calls_arr = is_calls
                .to_bool_array()
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

            let results = $batch_fn(
                prices_arr,
                spots_arr,
                strikes_arr,
                times_arr,
                rates_arr,
                sigmas_arr,
                is_calls_arr,
            )
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

            Ok(PyArray1::from_vec_bound(py, results))
        }
    };
}

/// Generic macro for creating Greeks batch functions
macro_rules! impl_greeks_batch_fn {
    (
        $fn_name:ident,
        $batch_fn:path,
        $doc:literal
    ) => {
        #[doc = $doc]
        #[pyfunction]
        #[pyo3(name = stringify!($fn_name))]
        #[pyo3(signature = (spots, strikes, times, rates, sigmas, is_calls))]
        fn $fn_name<'py>(
            py: Python<'py>,
            spots: FlexibleArray<'py>,
            strikes: FlexibleArray<'py>,
            times: FlexibleArray<'py>,
            rates: FlexibleArray<'py>,
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
            let sigmas_arr = sigmas
                .to_array_like()
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
            let is_calls_arr = is_calls
                .to_bool_array()
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

            let greeks_results = $batch_fn(
                spots_arr,
                strikes_arr,
                times_arr,
                rates_arr,
                sigmas_arr,
                is_calls_arr,
            )
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

            let dict = PyDict::new_bound(py);
            dict.set_item("delta", PyArray1::from_vec_bound(py, greeks_results.delta))?;
            dict.set_item("gamma", PyArray1::from_vec_bound(py, greeks_results.gamma))?;
            dict.set_item("theta", PyArray1::from_vec_bound(py, greeks_results.theta))?;
            dict.set_item("vega", PyArray1::from_vec_bound(py, greeks_results.vega))?;
            dict.set_item("rho", PyArray1::from_vec_bound(py, greeks_results.rho))?;

            Ok(dict)
        }
    };
}

/// Generic macro for creating Greeks batch functions with dividend yield
macro_rules! impl_greeks_batch_fn_with_q {
    (
        $fn_name:ident,
        $batch_fn:path,
        $doc:literal
    ) => {
        #[doc = $doc]
        #[pyfunction]
        #[pyo3(name = stringify!($fn_name))]
        #[pyo3(signature = (spots, strikes, times, rates, dividend_yields, sigmas, is_calls))]
        fn $fn_name<'py>(
            py: Python<'py>,
            spots: FlexibleArray<'py>,
            strikes: FlexibleArray<'py>,
            times: FlexibleArray<'py>,
            rates: FlexibleArray<'py>,
            dividend_yields: FlexibleArray<'py>,
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
            let dividend_yields_arr = dividend_yields
                .to_array_like()
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
            let sigmas_arr = sigmas
                .to_array_like()
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
            let is_calls_arr = is_calls
                .to_bool_array()
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

            let greeks_results = $batch_fn(
                spots_arr,
                strikes_arr,
                times_arr,
                rates_arr,
                dividend_yields_arr,
                sigmas_arr,
                is_calls_arr,
            )
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

            let dict = PyDict::new_bound(py);
            dict.set_item("delta", PyArray1::from_vec_bound(py, greeks_results.delta))?;
            dict.set_item("gamma", PyArray1::from_vec_bound(py, greeks_results.gamma))?;
            dict.set_item("theta", PyArray1::from_vec_bound(py, greeks_results.theta))?;
            dict.set_item("vega", PyArray1::from_vec_bound(py, greeks_results.vega))?;
            dict.set_item("rho", PyArray1::from_vec_bound(py, greeks_results.rho))?;
            dict.set_item("dividend_rho", PyArray1::from_vec_bound(py, greeks_results.dividend_rho))?;

            Ok(dict)
        }
    };
}

// Black-Scholes batch functions
impl_batch_price_fn!(
    bs_call_price_batch,
    black_scholes_batch::call_price_batch,
    "Calculate Black-Scholes call prices for multiple parameters with broadcasting"
);

impl_batch_price_fn!(
    bs_put_price_batch,
    black_scholes_batch::put_price_batch,
    "Calculate Black-Scholes put prices for multiple parameters with broadcasting"
);

impl_greeks_batch_fn!(
    bs_greeks_batch,
    black_scholes_batch::greeks_batch,
    "Calculate Black-Scholes Greeks for multiple parameters"
);

impl_iv_batch_fn!(
    bs_implied_volatility_batch,
    black_scholes_batch::implied_volatility_batch,
    "Calculate Black-Scholes implied volatility for multiple options"
);

// Black76 batch functions
use crate::models::black76::batch;

impl_batch_price_fn!(
    b76_call_price_batch,
    batch::call_price_batch,
    "Calculate Black76 call prices for multiple parameters with broadcasting"
);

impl_batch_price_fn!(
    b76_put_price_batch,
    batch::put_price_batch,
    "Calculate Black76 put prices for multiple parameters with broadcasting"
);

impl_greeks_batch_fn!(
    b76_greeks_batch,
    batch::greeks_batch,
    "Calculate Black76 Greeks for multiple parameters"
);

impl_iv_batch_fn!(
    b76_implied_volatility_batch,
    batch::implied_volatility_batch,
    "Calculate Black76 implied volatility for multiple options"
);

// Merton batch functions
use crate::models::merton;

impl_batch_price_fn_with_q!(
    merton_call_price_batch,
    merton::call_price_batch,
    "Calculate Merton call prices for multiple parameters with broadcasting"
);

impl_batch_price_fn_with_q!(
    merton_put_price_batch,
    merton::put_price_batch,
    "Calculate Merton put prices for multiple parameters with broadcasting"
);

impl_greeks_batch_fn_with_q!(
    merton_greeks_batch,
    merton::greeks_batch,
    "Calculate Merton Greeks for multiple parameters"
);

// American batch functions
use crate::models::american;

impl_batch_price_fn_with_q!(
    american_call_price_batch,
    american::call_price_batch,
    "Calculate American call prices for multiple parameters with broadcasting"
);

impl_batch_price_fn_with_q!(
    american_put_price_batch,
    american::put_price_batch,
    "Calculate American put prices for multiple parameters with broadcasting"
);

impl_greeks_batch_fn_with_q!(
    american_greeks_batch,
    american::greeks_batch,
    "Calculate American Greeks for multiple parameters"
);

// Module initialization using generic macro
macro_rules! init_module {
    (
        $module:ident,
        functions: [$($func:ident),*],
        classes: [$($class:ty),*]
    ) => {
        #[pymodule]
        pub fn $module(m: &Bound<'_, PyModule>) -> PyResult<()> {
            $(
                m.add_function(wrap_pyfunction!($func, m)?)?;
            )*
            $(
                m.add_class::<$class>()?;
            )*
            Ok(())
        }
    };
}

// Initialize Black-Scholes module
init_module!(
    black_scholes,
    functions: [
        bs_call_price,
        bs_put_price,
        bs_call_price_batch,
        bs_put_price_batch,
        bs_greeks,
        bs_greeks_batch,
        bs_implied_volatility,
        bs_implied_volatility_batch
    ],
    classes: [PyGreeks]
);

// Initialize Black76 module
init_module!(
    black76,
    functions: [
        b76_call_price,
        b76_put_price,
        b76_call_price_batch,
        b76_put_price_batch,
        b76_greeks,
        b76_greeks_batch,
        b76_implied_volatility,
        b76_implied_volatility_batch
    ],
    classes: [PyGreeks]
);

// Initialize Merton module
init_module!(
    merton,
    functions: [
        merton_call_price,
        merton_put_price,
        merton_call_price_batch,
        merton_put_price_batch,
        merton_greeks,
        merton_greeks_batch,
        merton_implied_volatility,
        merton_implied_volatility_batch
    ],
    classes: [PyGreeks]
);

// Initialize American module
init_module!(
    american,
    functions: [
        american_call_price,
        american_put_price,
        american_call_price_batch,
        american_put_price_batch,
        american_greeks,
        american_greeks_batch,
        american_implied_volatility,
        american_implied_volatility_batch,
        american_exercise_boundary,
        american_exercise_boundary_batch
    ],
    classes: []
);