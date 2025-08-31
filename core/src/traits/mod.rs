//! Core traits for option pricing models

use crate::error::QuantForgeResult;

/// Greeks output structure
#[derive(Debug, Clone, Copy)]
pub struct Greeks {
    pub delta: f64,
    pub gamma: f64,
    pub vega: f64,
    pub theta: f64,
    pub rho: f64,
    pub dividend_rho: Option<f64>,
}

/// Core trait for all option pricing models
pub trait OptionModel {
    /// Calculate call option price
    fn call_price(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> QuantForgeResult<f64>;

    /// Calculate put option price
    fn put_price(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> QuantForgeResult<f64>;

    /// Calculate all Greeks
    fn greeks(
        &self,
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        sigma: f64,
        is_call: bool,
    ) -> QuantForgeResult<Greeks>;

    /// Calculate implied volatility
    fn implied_volatility(
        &self,
        price: f64,
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        is_call: bool,
    ) -> QuantForgeResult<f64>;
}

/// Trait for batch processing operations
pub trait BatchProcessor {
    /// Process a batch of inputs in parallel
    fn process_batch<F, T>(&self, inputs: &[T], processor: F) -> Vec<QuantForgeResult<f64>>
    where
        F: Fn(&T) -> QuantForgeResult<f64> + Sync + Send,
        T: Sync + Send;
}
