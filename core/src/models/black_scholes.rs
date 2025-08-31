//! Black-Scholes model implementation

use crate::constants::*;
use crate::error::{QuantForgeError, QuantForgeResult, ValidationBuilder};
use crate::math::distributions::{norm_cdf, norm_pdf};
use crate::math::solvers::newton_raphson;
use crate::traits::{Greeks, OptionModel};
use rayon::prelude::*;

/// Black-Scholes option pricing model
pub struct BlackScholes;

impl BlackScholes {
    /// Calculate d1 parameter
    #[inline]
    fn d1(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> f64 {
        ((s / k).ln() + (r + 0.5 * sigma * sigma) * t) / (sigma * t.sqrt())
    }

    /// Calculate d2 parameter
    #[inline]
    fn d2(d1: f64, sigma: f64, t: f64) -> f64 {
        d1 - sigma * t.sqrt()
    }

    /// Validate input parameters
    fn validate_params(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> QuantForgeResult<()> {
        ValidationBuilder::new()
            .check_positive(s, "spot")
            .check_range(s, MIN_PRICE, MAX_PRICE, "spot")
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
}

impl OptionModel for BlackScholes {
    fn call_price(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> QuantForgeResult<f64> {
        Self::validate_params(s, k, t, r, sigma)?;

        let d1 = Self::d1(s, k, t, r, sigma);
        let d2 = Self::d2(d1, sigma, t);
        let discount = (-r * t).exp();

        Ok(s * norm_cdf(d1) - k * discount * norm_cdf(d2))
    }

    fn put_price(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> QuantForgeResult<f64> {
        Self::validate_params(s, k, t, r, sigma)?;

        let d1 = Self::d1(s, k, t, r, sigma);
        let d2 = Self::d2(d1, sigma, t);
        let discount = (-r * t).exp();

        Ok(k * discount * norm_cdf(-d2) - s * norm_cdf(-d1))
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
        Self::validate_params(s, k, t, r, sigma)?;

        let d1 = Self::d1(s, k, t, r, sigma);
        let d2 = Self::d2(d1, sigma, t);
        let sqrt_t = t.sqrt();
        let discount = (-r * t).exp();
        let pdf_d1 = norm_pdf(d1);
        let cdf_d1 = norm_cdf(d1);
        let cdf_d2 = norm_cdf(d2);

        let delta = if is_call { cdf_d1 } else { cdf_d1 - 1.0 };

        let gamma = pdf_d1 / (s * sigma * sqrt_t);
        let vega = s * pdf_d1 * sqrt_t / 100.0; // Scaled by 100 for 1% vol move

        let theta = if is_call {
            (-s * pdf_d1 * sigma / (2.0 * sqrt_t) - r * k * discount * cdf_d2) / 365.0
        } else {
            (-s * pdf_d1 * sigma / (2.0 * sqrt_t) + r * k * discount * norm_cdf(-d2)) / 365.0
        };

        let rho = if is_call {
            k * t * discount * cdf_d2 / 100.0 // Scaled by 100 for 1% rate move
        } else {
            -k * t * discount * norm_cdf(-d2) / 100.0
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

    fn implied_volatility(
        &self,
        price: f64,
        s: f64,
        k: f64,
        t: f64,
        r: f64,
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
            .build()?;

        // Check for arbitrage violations
        let intrinsic = if is_call {
            (s - k * (-r * t).exp()).max(0.0)
        } else {
            (k * (-r * t).exp() - s).max(0.0)
        };

        if price < intrinsic {
            return Err(QuantForgeError::InvalidInput(format!(
                "Price {price} violates arbitrage bounds (intrinsic: {intrinsic})"
            )));
        }

        // Initial guess using Brenner-Subrahmanyam approximation
        let initial_vol = (2.0 * std::f64::consts::PI / t).sqrt() * (price / s);
        let initial_vol = initial_vol.clamp(MIN_VOLATILITY, MAX_VOLATILITY);

        // Objective function
        let objective = |vol: f64| -> f64 {
            if is_call {
                self.call_price(s, k, t, r, vol).unwrap_or(0.0) - price
            } else {
                self.put_price(s, k, t, r, vol).unwrap_or(0.0) - price
            }
        };

        // Derivative (vega)
        let derivative = |vol: f64| -> f64 {
            let d1 = Self::d1(s, k, t, r, vol);
            s * norm_pdf(d1) * t.sqrt()
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

/// Batch processing implementation
impl BlackScholes {
    /// Process call prices in batch
    pub fn call_price_batch(
        &self,
        spots: &[f64],
        strikes: &[f64],
        times: &[f64],
        rates: &[f64],
        sigmas: &[f64],
    ) -> Vec<QuantForgeResult<f64>> {
        let len = spots.len();

        // Determine processing strategy based on size
        if len < PARALLEL_THRESHOLD_SMALL {
            // Sequential processing for small batches
            spots
                .iter()
                .zip(strikes.iter())
                .zip(times.iter())
                .zip(rates.iter())
                .zip(sigmas.iter())
                .map(|((((s, k), t), r), sigma)| self.call_price(*s, *k, *t, *r, *sigma))
                .collect()
        } else {
            // Parallel processing for large batches
            let chunk_size = if len < PARALLEL_THRESHOLD_MEDIUM {
                CHUNK_SIZE_L1
            } else {
                CHUNK_SIZE_L2
            };

            spots
                .par_chunks(chunk_size)
                .zip(strikes.par_chunks(chunk_size))
                .zip(times.par_chunks(chunk_size))
                .zip(rates.par_chunks(chunk_size))
                .zip(sigmas.par_chunks(chunk_size))
                .flat_map(|((((s_chunk, k_chunk), t_chunk), r_chunk), sigma_chunk)| {
                    s_chunk
                        .iter()
                        .zip(k_chunk.iter())
                        .zip(t_chunk.iter())
                        .zip(r_chunk.iter())
                        .zip(sigma_chunk.iter())
                        .map(|((((s, k), t), r), sigma)| self.call_price(*s, *k, *t, *r, *sigma))
                        .collect::<Vec<_>>()
                })
                .collect()
        }
    }
}
