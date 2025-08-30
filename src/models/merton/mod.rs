//! Merton model for options on dividend-paying assets.
//!
//! The Merton model extends the Black-Scholes model to handle assets that pay
//! continuous dividends at a rate `q`. It is commonly used for:
//! - Stock options with dividend yields
//! - Index options (e.g., S&P 500)
//! - Foreign exchange options (where `q` represents the foreign interest rate)

use crate::error::QuantForgeError;
use crate::models::{Greeks, PricingModel};

pub mod batch;
pub mod greeks;
pub mod implied_volatility;
pub mod pricing;
pub mod processor;

pub use batch::{call_price_batch, greeks_batch, implied_volatility_batch, put_price_batch};
pub use greeks::*;
pub use implied_volatility::*;
pub use pricing::*;

/// Parameters for the Merton model
#[derive(Debug, Clone, Copy)]
pub struct MertonParams {
    /// Spot price of the underlying asset
    pub s: f64,
    /// Strike price of the option
    pub k: f64,
    /// Time to maturity (in years)
    pub t: f64,
    /// Risk-free interest rate
    pub r: f64,
    /// Dividend yield
    pub q: f64,
    /// Volatility of the underlying asset
    pub sigma: f64,
}

impl MertonParams {
    /// Create new Merton model parameters with validation
    pub fn new(
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
    ) -> Result<Self, QuantForgeError> {
        // Validate inputs
        if s <= 0.0 {
            return Err(QuantForgeError::InvalidInput(
                "s must be positive".to_string(),
            ));
        }
        if k <= 0.0 {
            return Err(QuantForgeError::InvalidInput(
                "k must be positive".to_string(),
            ));
        }
        if t < 0.0 {
            return Err(QuantForgeError::InvalidInput(
                "t must be non-negative".to_string(),
            ));
        }
        if sigma <= 0.0 {
            return Err(QuantForgeError::InvalidInput(
                "sigma must be positive".to_string(),
            ));
        }

        Ok(Self {
            s,
            k,
            t,
            r,
            q,
            sigma,
        })
    }

    /// Create parameters without validation (for performance-critical paths)
    #[inline]
    pub fn new_unchecked(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> Self {
        Self {
            s,
            k,
            t,
            r,
            q,
            sigma,
        }
    }
}

/// Merton model implementation
pub struct MertonModel;

impl PricingModel for MertonModel {
    type Params = MertonParams;

    fn call_price(params: &Self::Params) -> f64 {
        pricing::call_price(
            params.s,
            params.k,
            params.t,
            params.r,
            params.q,
            params.sigma,
        )
    }

    fn put_price(params: &Self::Params) -> f64 {
        pricing::put_price(
            params.s,
            params.k,
            params.t,
            params.r,
            params.q,
            params.sigma,
        )
    }

    fn greeks(params: &Self::Params, is_call: bool) -> Greeks {
        greeks::calculate_greeks(
            params.s,
            params.k,
            params.t,
            params.r,
            params.q,
            params.sigma,
            is_call,
        )
    }

    fn implied_volatility(
        price: f64,
        params: &Self::Params,
        is_call: bool,
        initial_guess: Option<f64>,
    ) -> Result<f64, QuantForgeError> {
        implied_volatility::calculate_implied_volatility(
            price,
            params.s,
            params.k,
            params.t,
            params.r,
            params.q,
            is_call,
            initial_guess,
        )
    }
}

// Batch processing functions
impl MertonModel {
    // Batch functions removed - will be reimplemented with full array support
}
