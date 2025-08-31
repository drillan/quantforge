//! Black76 model implementation (futures/forwards)

use crate::constants::*;
use crate::error::{QuantForgeError, QuantForgeResult, ValidationBuilder};
use crate::math::distributions::{norm_cdf, norm_pdf};
use crate::math::solvers::newton_raphson;
use crate::traits::{Greeks, OptionModel};

/// Black76 option pricing model for futures and forwards
pub struct Black76;

impl Black76 {
    /// Calculate d1 parameter for Black76
    #[inline]
    fn d1(f: f64, k: f64, t: f64, sigma: f64) -> f64 {
        ((f / k).ln() + 0.5 * sigma * sigma * t) / (sigma * t.sqrt())
    }

    /// Calculate d2 parameter
    #[inline]
    fn d2(d1: f64, sigma: f64, t: f64) -> f64 {
        d1 - sigma * t.sqrt()
    }

    /// Validate input parameters
    fn validate_params(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> QuantForgeResult<()> {
        ValidationBuilder::new()
            .check_positive(f, "forward")
            .check_range(f, MIN_PRICE, MAX_PRICE, "forward")
            .check_positive(k, "strike")
            .check_range(k, MIN_PRICE, MAX_PRICE, "strike")
            .check_positive(t, "time")
            .check_range(t, MIN_TIME, MAX_TIME, "time")
            .check_finite(r, "rate")
            .check_range(r, MIN_RATE, MAX_RATE, "rate")
            .check_positive(sigma, "volatility")
            .check_range(
                sigma,
                MIN_VOLATILITY_PRACTICAL,
                MAX_VOLATILITY,
                "volatility",
            )
            .build()
    }

    /// Core Black76 call price calculation
    pub fn call_price_black76(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> QuantForgeResult<f64> {
        Self::validate_params(f, k, t, r, sigma)?;

        let d1 = Self::d1(f, k, t, sigma);
        let d2 = Self::d2(d1, sigma, t);
        let discount = (-r * t).exp();

        Ok(discount * (f * norm_cdf(d1) - k * norm_cdf(d2)))
    }

    /// Core Black76 put price calculation
    pub fn put_price_black76(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> QuantForgeResult<f64> {
        Self::validate_params(f, k, t, r, sigma)?;

        let d1 = Self::d1(f, k, t, sigma);
        let d2 = Self::d2(d1, sigma, t);
        let discount = (-r * t).exp();

        Ok(discount * (k * norm_cdf(-d2) - f * norm_cdf(-d1)))
    }

    /// Calculate Greeks for Black76
    pub fn greeks_black76(
        f: f64,
        k: f64,
        t: f64,
        r: f64,
        sigma: f64,
        is_call: bool,
    ) -> QuantForgeResult<Greeks> {
        Self::validate_params(f, k, t, r, sigma)?;

        let d1 = Self::d1(f, k, t, sigma);
        let d2 = Self::d2(d1, sigma, t);
        let sqrt_t = t.sqrt();
        let discount = (-r * t).exp();
        let pdf_d1 = norm_pdf(d1);
        let cdf_d1 = norm_cdf(d1);
        let cdf_d2 = norm_cdf(d2);

        // Delta (with respect to forward price)
        let delta = if is_call {
            discount * cdf_d1
        } else {
            discount * (cdf_d1 - 1.0)
        };

        // Gamma (with respect to forward price)
        let gamma = discount * pdf_d1 / (f * sigma * sqrt_t);

        // Vega (scaled by 100 for 1% vol move)
        let vega = discount * f * pdf_d1 * sqrt_t / 100.0;

        // Theta (per calendar day)
        let theta = if is_call {
            (-f * discount * pdf_d1 * sigma / (2.0 * sqrt_t)
                + r * discount * (f * cdf_d1 - k * cdf_d2))
                / 365.0
        } else {
            (-f * discount * pdf_d1 * sigma / (2.0 * sqrt_t)
                + r * discount * (k * norm_cdf(-d2) - f * norm_cdf(-d1)))
                / 365.0
        };

        // Rho (scaled by 100 for 1% rate move)
        let rho = if is_call {
            -t * discount * (f * cdf_d1 - k * cdf_d2) / 100.0
        } else {
            -t * discount * (k * norm_cdf(-d2) - f * norm_cdf(-d1)) / 100.0
        };

        Ok(Greeks {
            delta,
            gamma,
            vega,
            theta,
            rho,
            dividend_rho: None,
        })
    }

    /// Calculate implied volatility for Black76
    pub fn implied_volatility_black76(
        price: f64,
        f: f64,
        k: f64,
        t: f64,
        r: f64,
        is_call: bool,
    ) -> QuantForgeResult<f64> {
        // Validate inputs
        ValidationBuilder::new()
            .check_positive(price, "price")
            .check_positive(f, "forward")
            .check_positive(k, "strike")
            .check_positive(t, "time")
            .check_finite(r, "rate")
            .check_range(r, MIN_RATE, MAX_RATE, "rate")
            .build()?;

        let discount = (-r * t).exp();

        // Check for arbitrage violations
        let intrinsic = if is_call {
            discount * (f - k).max(0.0)
        } else {
            discount * (k - f).max(0.0)
        };

        if price < intrinsic {
            return Err(QuantForgeError::InvalidInput(format!(
                "Price {price} violates arbitrage bounds (intrinsic: {intrinsic})"
            )));
        }

        // Initial guess using Brenner-Subrahmanyam approximation
        let initial_vol = (2.0 * std::f64::consts::PI / t).sqrt() * (price / (f * discount));
        let initial_vol = initial_vol.clamp(MIN_VOLATILITY, MAX_VOLATILITY);

        // Objective function
        let objective = |vol: f64| -> f64 {
            if is_call {
                Self::call_price_black76(f, k, t, r, vol).unwrap_or(0.0) - price
            } else {
                Self::put_price_black76(f, k, t, r, vol).unwrap_or(0.0) - price
            }
        };

        // Derivative (vega)
        let derivative = |vol: f64| -> f64 {
            let d1 = Self::d1(f, k, t, vol);
            discount * f * norm_pdf(d1) * t.sqrt()
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

// Implement OptionModel trait for Black76 using forward = spot convention
impl OptionModel for Black76 {
    fn call_price(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> QuantForgeResult<f64> {
        // For compatibility, treat s as forward price
        Self::call_price_black76(s, k, t, r, sigma)
    }

    fn put_price(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> QuantForgeResult<f64> {
        // For compatibility, treat s as forward price
        Self::put_price_black76(s, k, t, r, sigma)
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
        // For compatibility, treat s as forward price
        Self::greeks_black76(s, k, t, r, sigma, is_call)
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
        // For compatibility, treat s as forward price
        Self::implied_volatility_black76(price, s, k, t, r, is_call)
    }
}
