//! Merton model implementation (Black-Scholes with dividends)

use crate::constants::*;
use crate::error::{QuantForgeError, QuantForgeResult, ValidationBuilder};
use crate::math::distributions::{norm_cdf, norm_pdf};
use crate::math::solvers::newton_raphson;
use crate::traits::{Greeks, OptionModel};

/// Merton option pricing model (Black-Scholes with continuous dividend yield)
pub struct Merton;

impl Merton {
    /// Calculate d1 parameter with dividend yield
    #[inline]
    fn d1(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
        ((s / k).ln() + (r - q + 0.5 * sigma * sigma) * t) / (sigma * t.sqrt())
    }

    /// Calculate d2 parameter
    #[inline]
    fn d2(d1: f64, sigma: f64, t: f64) -> f64 {
        d1 - sigma * t.sqrt()
    }

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

    /// Core Merton call price calculation
    pub fn call_price_merton(
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
    ) -> QuantForgeResult<f64> {
        Self::validate_params(s, k, t, r, q, sigma)?;

        let d1 = Self::d1(s, k, t, r, q, sigma);
        let d2 = Self::d2(d1, sigma, t);
        let discount_r = (-r * t).exp();
        let discount_q = (-q * t).exp();

        Ok(s * discount_q * norm_cdf(d1) - k * discount_r * norm_cdf(d2))
    }

    /// Core Merton put price calculation
    pub fn put_price_merton(
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
    ) -> QuantForgeResult<f64> {
        Self::validate_params(s, k, t, r, q, sigma)?;

        let d1 = Self::d1(s, k, t, r, q, sigma);
        let d2 = Self::d2(d1, sigma, t);
        let discount_r = (-r * t).exp();
        let discount_q = (-q * t).exp();

        Ok(k * discount_r * norm_cdf(-d2) - s * discount_q * norm_cdf(-d1))
    }

    /// Calculate Greeks for Merton model
    pub fn greeks_merton(
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
        is_call: bool,
    ) -> QuantForgeResult<Greeks> {
        Self::validate_params(s, k, t, r, q, sigma)?;

        let d1 = Self::d1(s, k, t, r, q, sigma);
        let d2 = Self::d2(d1, sigma, t);
        let sqrt_t = t.sqrt();
        let discount_r = (-r * t).exp();
        let discount_q = (-q * t).exp();
        let pdf_d1 = norm_pdf(d1);
        let cdf_d1 = norm_cdf(d1);
        let cdf_d2 = norm_cdf(d2);

        // Delta
        let delta = if is_call {
            discount_q * cdf_d1
        } else {
            discount_q * (cdf_d1 - 1.0)
        };

        // Gamma
        let gamma = discount_q * pdf_d1 / (s * sigma * sqrt_t);

        // Vega (scaled by 100 for 1% vol move)
        let vega = s * discount_q * pdf_d1 * sqrt_t / 100.0;

        // Theta (per calendar day)
        let theta = if is_call {
            (-s * discount_q * pdf_d1 * sigma / (2.0 * sqrt_t) + q * s * discount_q * cdf_d1
                - r * k * discount_r * cdf_d2)
                / 365.0
        } else {
            (-s * discount_q * pdf_d1 * sigma / (2.0 * sqrt_t) - q * s * discount_q * norm_cdf(-d1)
                + r * k * discount_r * norm_cdf(-d2))
                / 365.0
        };

        // Rho (scaled by 100 for 1% rate move)
        let rho = if is_call {
            k * t * discount_r * cdf_d2 / 100.0
        } else {
            -k * t * discount_r * norm_cdf(-d2) / 100.0
        };

        // Dividend rho (scaled by 100 for 1% dividend yield move)
        let dividend_rho = if is_call {
            -s * t * discount_q * cdf_d1 / 100.0
        } else {
            s * t * discount_q * norm_cdf(-d1) / 100.0
        };

        Ok(Greeks {
            delta,
            gamma,
            vega,
            theta,
            rho,
            dividend_rho: Some(dividend_rho),
        })
    }

    /// Calculate implied volatility for Merton model
    pub fn implied_volatility_merton(
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
            .check_finite(r, "rate")
            .check_range(r, MIN_RATE, MAX_RATE, "rate")
            .check_finite(q, "dividend_yield")
            .build()?;

        let discount_r = (-r * t).exp();
        let discount_q = (-q * t).exp();

        // Check for arbitrage violations
        let intrinsic = if is_call {
            (s * discount_q - k * discount_r).max(0.0)
        } else {
            (k * discount_r - s * discount_q).max(0.0)
        };

        if price < intrinsic {
            return Err(QuantForgeError::InvalidInput(format!(
                "Price {price} violates arbitrage bounds (intrinsic: {intrinsic})"
            )));
        }

        // Initial guess using Brenner-Subrahmanyam approximation
        let forward = s * ((r - q) * t).exp();
        let initial_vol = (2.0 * std::f64::consts::PI / t).sqrt() * (price / forward);
        let initial_vol = initial_vol.clamp(MIN_VOLATILITY, MAX_VOLATILITY);

        // Objective function
        let objective = |vol: f64| -> f64 {
            if is_call {
                Self::call_price_merton(s, k, t, r, q, vol).unwrap_or(0.0) - price
            } else {
                Self::put_price_merton(s, k, t, r, q, vol).unwrap_or(0.0) - price
            }
        };

        // Derivative (vega)
        let derivative = |vol: f64| -> f64 {
            let d1 = Self::d1(s, k, t, r, q, vol);
            s * discount_q * norm_pdf(d1) * t.sqrt()
        };

        // Solve using Newton-Raphson with bounds checking
        let result = newton_raphson(
            objective,
            derivative,
            initial_vol,
            IV_TOLERANCE,
            MAX_IV_ITERATIONS,
        )?;

        // Ensure result is within valid range
        Ok(result.clamp(MIN_VOLATILITY, MAX_VOLATILITY))
    }
}

// Implement OptionModel trait for Merton (default q=0 for compatibility)
impl OptionModel for Merton {
    fn call_price(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> QuantForgeResult<f64> {
        // Default to zero dividend yield for trait compatibility
        Self::call_price_merton(s, k, t, r, 0.0, sigma)
    }

    fn put_price(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> QuantForgeResult<f64> {
        // Default to zero dividend yield for trait compatibility
        Self::put_price_merton(s, k, t, r, 0.0, sigma)
    }

    fn greeks(
        &self,
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        sigma: f64,
        is_call: bool,
    ) -> QuantForgeResult<Greeks> {
        // Default to zero dividend yield for trait compatibility
        Self::greeks_merton(s, k, t, r, 0.0, sigma, is_call)
    }

    fn implied_volatility(
        &self,
        price: f64,
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        is_call: bool,
    ) -> QuantForgeResult<f64> {
        // Default to zero dividend yield for trait compatibility
        Self::implied_volatility_merton(price, s, k, t, r, 0.0, is_call)
    }
}
