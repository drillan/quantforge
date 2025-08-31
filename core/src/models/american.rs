//! American option pricing model using Bjerksund-Stensland 2002
//!
//! This module provides an analytical approximation for American option pricing
//! with early exercise features. Similar to the Merton model, American options
//! require dividend yield as an additional parameter.

pub mod pricing;
pub mod greeks;
pub mod boundary;

use crate::constants::*;
use crate::error::{QuantForgeError, QuantForgeResult, ValidationBuilder};
use crate::math::solvers::newton_raphson;
use crate::traits::{Greeks, OptionModel};
use self::greeks::calculate_american_greeks;
use self::pricing::{american_call_price, american_put_price, AmericanParams};

/// American option pricing model
///
/// Implements the Bjerksund-Stensland 2002 approximation for American options.
/// Note: The OptionModel trait methods assume q=0 (no dividend) due to trait limitations.
/// For dividend-paying assets, use the static methods with explicit dividend parameter.
pub struct American;

impl American {
    /// Validate input parameters including dividend yield
    fn validate_params(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> QuantForgeResult<()> {
        ValidationBuilder::new()
            .check_positive(s, "spot")
            .check_range(s, MIN_PRICE, MAX_PRICE, "spot")
            .check_positive(k, "strike")
            .check_range(k, MIN_PRICE, MAX_PRICE, "strike")
            .check_positive(t, "time")
            .check_range(t, MIN_TIME, MAX_TIME, "time")
            .check_finite(r, "rate")
            .check_range(r, MIN_RATE, MAX_RATE, "rate")
            .check_finite(q, "dividend_yield")
            .check_positive(sigma, "volatility")
            .check_range(
                sigma,
                MIN_VOLATILITY_PRACTICAL,
                MAX_VOLATILITY,
                "volatility",
            )
            .build()
    }

    /// Core American call price calculation with dividend yield
    pub fn call_price_american(
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
    ) -> QuantForgeResult<f64> {
        Self::validate_params(s, k, t, r, q, sigma)?;
        
        let params = AmericanParams {
            s,
            k,
            t,
            r,
            q,
            sigma,
        };
        
        american_call_price(&params)
    }

    /// Core American put price calculation with dividend yield
    pub fn put_price_american(
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
    ) -> QuantForgeResult<f64> {
        Self::validate_params(s, k, t, r, q, sigma)?;
        
        let params = AmericanParams {
            s,
            k,
            t,
            r,
            q,
            sigma,
        };
        
        american_put_price(&params)
    }

    /// Calculate Greeks for American model with dividend yield
    pub fn greeks_american(
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
        is_call: bool,
    ) -> QuantForgeResult<Greeks> {
        Self::validate_params(s, k, t, r, q, sigma)?;
        
        let params = AmericanParams {
            s,
            k,
            t,
            r,
            q,
            sigma,
        };
        
        calculate_american_greeks(&params, is_call)
    }

    /// Calculate implied volatility for American options
    pub fn implied_volatility_american(
        price: f64,
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        is_call: bool,
    ) -> QuantForgeResult<f64> {
        // Validate inputs
        ValidationBuilder::new()
            .check_positive(price, "price")
            .check_positive(s, "spot")
            .check_positive(k, "strike")
            .check_positive(t, "time")
            .build()?;

        // Check price bounds
        let intrinsic = if is_call {
            (s - k).max(0.0)
        } else {
            (k - s).max(0.0)
        };

        if price < intrinsic {
            return Err(QuantForgeError::CalculationError(
                format!("Price {price:.4} is below intrinsic value {intrinsic:.4}")
            ));
        }

        // Initial guess using at-the-money approximation
        let initial_vol = ((2.0 * std::f64::consts::PI / t).sqrt() * (price / s)).min(MAX_VOLATILITY);

        // Objective function: find sigma such that calculated_price - market_price = 0
        let f = |sigma_test: f64| -> f64 {
            if sigma_test <= 0.0 || sigma_test > MAX_VOLATILITY {
                return f64::INFINITY;
            }
            
            let calculated_price = if is_call {
                Self::call_price_american(s, k, t, r, q, sigma_test)
            } else {
                Self::put_price_american(s, k, t, r, q, sigma_test)
            };
            
            calculated_price.unwrap_or(f64::INFINITY) - price
        };

        // Derivative (vega) for Newton-Raphson
        let df = |sigma_test: f64| -> f64 {
            if sigma_test <= 0.0 || sigma_test > MAX_VOLATILITY {
                return 0.0;
            }
            
            let params = AmericanParams {
                s,
                k,
                t,
                r,
                q,
                sigma: sigma_test,
            };
            
            let greeks = calculate_american_greeks(&params, is_call);
            greeks.map(|g| g.vega * 100.0).unwrap_or(0.0)
        };

        // Use Newton-Raphson solver
        newton_raphson(
            f,
            df,
            initial_vol,
            IV_TOLERANCE_PRICE,
            MAX_IV_ITERATIONS,
        )
    }
}

impl OptionModel for American {
    /// Calculate call price (assumes q=0 for trait compatibility)
    fn call_price(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> QuantForgeResult<f64> {
        American::call_price_american(s, k, t, r, 0.0, sigma)
    }

    /// Calculate put price (assumes q=0 for trait compatibility)
    fn put_price(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> QuantForgeResult<f64> {
        American::put_price_american(s, k, t, r, 0.0, sigma)
    }

    /// Calculate Greeks (assumes q=0 for trait compatibility)
    fn greeks(
        &self,
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        sigma: f64,
        is_call: bool,
    ) -> QuantForgeResult<Greeks> {
        American::greeks_american(s, k, t, r, 0.0, sigma, is_call)
    }

    /// Calculate implied volatility (assumes q=0 for trait compatibility)
    fn implied_volatility(
        &self,
        price: f64,
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        is_call: bool,
    ) -> QuantForgeResult<f64> {
        American::implied_volatility_american(price, s, k, t, r, 0.0, is_call)
    }
}
