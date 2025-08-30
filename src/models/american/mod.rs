//! American option pricing models
//!
//! Implementation of the Bjerksund-Stensland 2002 model for American option pricing.
//! This module provides high-performance analytical approximation for American options
//! with early exercise features.

mod batch;
mod boundary;
mod greeks;
mod implied_volatility;
mod pricing;
mod processor;

use crate::error::QuantForgeError;
use crate::models::{Greeks, PricingModel};

/// Parameters for American option pricing
#[derive(Debug, Clone, Copy)]
pub struct AmericanParams {
    /// Spot price (current price of underlying asset)
    pub s: f64,
    /// Strike price (exercise price)
    pub k: f64,
    /// Time to maturity (in years)
    pub t: f64,
    /// Risk-free rate
    pub r: f64,
    /// Dividend yield (continuous)
    pub q: f64,
    /// Volatility (annualized)
    pub sigma: f64,
}

impl AmericanParams {
    /// Create new American option parameters with validation
    pub fn new(
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
    ) -> Result<Self, QuantForgeError> {
        // Validation
        if s <= 0.0 {
            return Err(QuantForgeError::ValidationError {
                context: "s must be positive".into(),
            });
        }
        if k <= 0.0 {
            return Err(QuantForgeError::ValidationError {
                context: "k must be positive".into(),
            });
        }
        if t < 0.0 {
            return Err(QuantForgeError::ValidationError {
                context: "t must be non-negative".into(),
            });
        }
        if sigma <= 0.0 {
            return Err(QuantForgeError::ValidationError {
                context: "sigma must be positive".into(),
            });
        }

        // Check for dividend arbitrage condition
        if q > r {
            return Err(QuantForgeError::ValidationError {
                context: "Dividend yield (q) cannot exceed risk-free rate (r) to prevent arbitrage"
                    .into(),
            });
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

    /// Create new American option parameters without validation (for batch operations)
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

    /// Cost of carry parameter (b = r - q)
    #[inline]
    pub fn b(&self) -> f64 {
        self.r - self.q
    }
}

/// American option pricing model using Bjerksund-Stensland 2002
pub struct AmericanModel;

impl PricingModel for AmericanModel {
    type Params = AmericanParams;

    fn call_price(params: &Self::Params) -> f64 {
        pricing::american_call_price(params)
    }

    fn put_price(params: &Self::Params) -> f64 {
        pricing::american_put_price(params)
    }

    fn greeks(params: &Self::Params, is_call: bool) -> Greeks {
        greeks::calculate_american_greeks(params, is_call)
    }

    fn implied_volatility(
        price: f64,
        params: &Self::Params,
        is_call: bool,
        initial_guess: Option<f64>,
    ) -> Result<f64, QuantForgeError> {
        implied_volatility::calculate_american_iv(price, params, is_call, initial_guess)
    }
}

// Batch processing functions
impl AmericanModel {
    // Batch functions removed - will be reimplemented with full array support
}

// Public API functions
pub use batch::{
    call_price_batch, exercise_boundary_batch, greeks_batch, implied_volatility_batch,
    put_price_batch,
};
pub use boundary::exercise_boundary;
pub use pricing::{american_call_price, american_put_price};
