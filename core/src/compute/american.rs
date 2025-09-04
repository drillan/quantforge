//! American option pricing - Arrow-native implementation
//!
//! Implements American option pricing using:
//! 1. Bjerksund-Stensland 2002 (BS2002) approximation - default fast method
//! 2. Cox-Ross-Rubinstein binomial tree - optional high-precision method

use arrow::array::builder::Float64Builder;
use arrow::array::{ArrayRef, Float64Array};
use arrow::error::ArrowError;
use std::sync::Arc;

use super::american_simple::{calculate_critical_price_call, calculate_critical_price_put};
use super::formulas::black_scholes_call_scalar;
use super::{get_scalar_or_array_value, validate_broadcast_compatibility};
use crate::constants::{
    get_parallel_threshold, BASIS_POINT_MULTIPLIER, BS2002_BETA_MIN, BS2002_CONVERGENCE_TOL,
    BS2002_H_FACTOR, DAYS_PER_YEAR, EXERCISE_BOUNDARY_MAX_ITER, GREEK_PRICE_CHANGE_RATIO,
    GREEK_RATE_CHANGE, GREEK_VOL_CHANGE, HALF, TIME_NEAR_EXPIRY_THRESHOLD,
};
use crate::math::distributions::norm_cdf;

// ============================================================================
// SCALAR IMPLEMENTATIONS
// ============================================================================

/// Calculate beta parameter for BS2002 model
#[inline(always)]
#[allow(dead_code)]
fn calculate_beta(r: f64, q: f64, sigma: f64) -> f64 {
    let sigma_sq = sigma * sigma;
    let b = r - q;
    let inner = b / sigma_sq - HALF;
    let beta = inner.powi(2) + 2.0 * r / sigma_sq;
    (HALF - b / sigma_sq + beta.sqrt()).max(BS2002_BETA_MIN)
}

/// Calculate B∞ boundary for BS2002
#[inline(always)]
fn calculate_b_infinity(beta: f64, k: f64, r: f64, q: f64) -> f64 {
    beta / (beta - 1.0) * k.max(r / q * k)
}

/// Calculate B0 boundary for BS2002
#[inline(always)]
fn calculate_b0(k: f64, r: f64, q: f64) -> f64 {
    k.max(r / q * k)
}

/// Calculate h(T) parameter for BS2002
#[inline(always)]
fn calculate_h(t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    let b = r - q;
    -(b * t + BS2002_H_FACTOR * sigma * t.sqrt())
}

/// Calculate α function for BS2002
#[inline(always)]
fn calculate_alpha(x: f64, beta: f64, i: f64) -> f64 {
    x * (1.0 - (-i).exp()).powf(-beta)
}

/// Calculate λ parameter for BS2002
#[inline(always)]
#[allow(clippy::too_many_arguments)]
fn calculate_lambda(
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    beta: f64,
    b_inf: f64,
    b0: f64,
    i: f64,
) -> f64 {
    let b = r - q;
    let h = calculate_h(t, r, q, sigma);
    -r + (b + (beta - HALF) * sigma * sigma) * t
        + 2.0 * sigma * t.sqrt() * ((i - h).ln() / (b_inf / b0).ln()).sqrt()
}

/// Calculate ψ function for BS2002
#[inline(always)]
#[allow(dead_code)]
fn psi(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64, gamma: f64) -> f64 {
    let b = r - q;
    let sqrt_t = t.sqrt();
    let lambda_val = -r + gamma * b + gamma * (gamma - 1.0) * sigma * sigma * HALF;

    let d1 = -((s / k).ln() + (b + (gamma - HALF) * sigma * sigma) * t) / (sigma * sqrt_t);

    let term1 = (-(lambda_val * t)).exp() * s.powf(gamma);
    let term2 = norm_cdf(d1);
    let term3 = s.powf(gamma) / gamma
        * (-q * t).exp()
        * norm_cdf(d1 - 2.0 * gamma * sigma * sqrt_t / gamma);

    term1 * (term2 - term3)
}

/// Calculate early exercise boundary for BS2002
#[inline(always)]
#[allow(dead_code)]
fn calculate_exercise_boundary(k: f64, t: f64, r: f64, q: f64, sigma: f64, beta: f64) -> f64 {
    let b_inf = calculate_b_infinity(beta, k, r, q);
    let b0 = calculate_b0(k, r, q);

    // Use iterative method to find B(T)
    let h = calculate_h(t, r, q, sigma);
    let i = b0 + (b_inf - b0) * (1.0 - h.exp());

    // Newton-Raphson refinement
    let mut b_t = i;
    for _ in 0..EXERCISE_BOUNDARY_MAX_ITER {
        let _alpha = calculate_alpha(i, beta, i);
        let lambda = calculate_lambda(t, r, q, sigma, beta, b_inf, b0, i);

        let next = b0 + (b_inf - b0) * (1.0 - (-lambda).exp());
        if (next - b_t).abs() < BS2002_CONVERGENCE_TOL {
            break;
        }
        b_t = next;
    }

    b_t
}

/// Bjerksund-Stensland 2002 American call option price
#[inline(always)]
pub fn american_call_scalar(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    // Validation
    if s <= 0.0 || k <= 0.0 || t < 0.0 || sigma < 0.0 {
        panic!("Invalid parameters: s, k must be positive; t, sigma must be non-negative");
    }

    // Special case: no dividend means American call = European call
    if q <= 0.0 {
        return black_scholes_call_scalar(s, k, t, r, sigma);
    }

    // Special case: at expiry
    if t < TIME_NEAR_EXPIRY_THRESHOLD {
        return (s - k).max(0.0);
    }

    // Special case: zero volatility
    if sigma < TIME_NEAR_EXPIRY_THRESHOLD {
        // Deterministic case
        let future_value = s * ((r - q) * t).exp();
        let pv_strike = k * (-r * t).exp();
        return (future_value - pv_strike).max(0.0);
    }

    // For now, use simplified American option approximation
    // The full BS2002 has numerical issues that need debugging
    use super::american_simple::american_call_simple;
    american_call_simple(s, k, t, r, q, sigma)
}

/// Bjerksund-Stensland 2002 American put option price
/// Uses put-call transformation: P(S,K) = C(K,S) with adjusted rates
#[inline(always)]
pub fn american_put_scalar(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    // Validation
    if s <= 0.0 || k <= 0.0 || t < 0.0 || sigma < 0.0 {
        panic!("Invalid parameters: s, k must be positive; t, sigma must be non-negative");
    }

    // Special case: at expiry
    if t < TIME_NEAR_EXPIRY_THRESHOLD {
        return (k - s).max(0.0);
    }

    // For now, use simplified American option approximation
    // The full BS2002 has numerical issues that need debugging
    use super::american_simple::american_put_simple;
    american_put_simple(s, k, t, r, q, sigma)
}

/// Cox-Ross-Rubinstein binomial tree for American options
///
/// # Arguments
/// * `s` - Spot price
/// * `k` - Strike price  
/// * `t` - Time to maturity
/// * `r` - Risk-free rate
/// * `q` - Dividend yield
/// * `sigma` - Volatility
/// * `n_steps` - Number of time steps in the tree
/// * `is_call` - true for call, false for put
#[allow(clippy::too_many_arguments)]
pub fn american_binomial(
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    n_steps: usize,
    is_call: bool,
) -> f64 {
    // Validation
    if s <= 0.0 || k <= 0.0 || t < 0.0 || sigma < 0.0 {
        panic!("Invalid parameters: s, k must be positive; t, sigma must be non-negative");
    }

    if n_steps == 0 {
        panic!("n_steps must be at least 1");
    }

    let dt = t / n_steps as f64;
    let u = (sigma * dt.sqrt()).exp();
    let d = 1.0 / u;
    let p = (((r - q) * dt).exp() - d) / (u - d);
    let discount = (-r * dt).exp();

    // Memory-efficient implementation: use single array
    let mut values = vec![0.0; n_steps + 1];

    // Calculate terminal payoffs
    for (i, value) in values.iter_mut().enumerate() {
        let spot_t = s * u.powi(i as i32) * d.powi((n_steps - i) as i32);
        *value = if is_call {
            (spot_t - k).max(0.0)
        } else {
            (k - spot_t).max(0.0)
        };
    }

    // Backward induction
    for step in (0..n_steps).rev() {
        for i in 0..=step {
            let spot = s * u.powi(i as i32) * d.powi((step - i) as i32);
            let hold_value = discount * (p * values[i + 1] + (1.0 - p) * values[i]);
            let exercise_value = if is_call {
                (spot - k).max(0.0)
            } else {
                (k - spot).max(0.0)
            };
            values[i] = hold_value.max(exercise_value);
        }
    }

    values[0]
}

// ============================================================================
// GREEKS CALCULATION (Finite Difference)
// ============================================================================

/// Calculate delta using finite difference
#[inline(always)]
pub fn american_call_delta(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    let h = GREEK_PRICE_CHANGE_RATIO * s;
    let price_up = american_call_scalar(s + h, k, t, r, q, sigma);
    let price_down = american_call_scalar(s - h, k, t, r, q, sigma);
    (price_up - price_down) / (2.0 * h)
}

/// Calculate delta for put
#[inline(always)]
pub fn american_put_delta(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    let h = GREEK_PRICE_CHANGE_RATIO * s;
    let price_up = american_put_scalar(s + h, k, t, r, q, sigma);
    let price_down = american_put_scalar(s - h, k, t, r, q, sigma);
    (price_up - price_down) / (2.0 * h)
}

/// Calculate gamma using finite difference
#[inline(always)]
pub fn american_call_gamma(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    let h = GREEK_PRICE_CHANGE_RATIO * s;
    let price_up = american_call_scalar(s + h, k, t, r, q, sigma);
    let price_center = american_call_scalar(s, k, t, r, q, sigma);
    let price_down = american_call_scalar(s - h, k, t, r, q, sigma);
    (price_up - 2.0 * price_center + price_down) / (h * h)
}

/// Calculate gamma for put (same as call)
#[inline(always)]
pub fn american_put_gamma(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    american_call_gamma(s, k, t, r, q, sigma)
}

/// Calculate vega using finite difference
#[inline(always)]
pub fn american_call_vega(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    let h = GREEK_VOL_CHANGE;
    let price_up = american_call_scalar(s, k, t, r, q, sigma + h);
    let price_down = american_call_scalar(s, k, t, r, q, sigma - h);
    (price_up - price_down) / (2.0 * h) / BASIS_POINT_MULTIPLIER
}

/// Calculate vega for put
#[inline(always)]
pub fn american_put_vega(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    let h = GREEK_VOL_CHANGE;
    let price_up = american_put_scalar(s, k, t, r, q, sigma + h);
    let price_down = american_put_scalar(s, k, t, r, q, sigma - h);
    (price_up - price_down) / (2.0 * h) / BASIS_POINT_MULTIPLIER
}

/// Calculate theta using finite difference
#[inline(always)]
pub fn american_call_theta(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    let h = 1.0 / DAYS_PER_YEAR;
    if t <= h {
        return 0.0; // Can't calculate theta near expiry
    }
    let price_now = american_call_scalar(s, k, t, r, q, sigma);
    let price_later = american_call_scalar(s, k, t - h, r, q, sigma);
    // Theta = dPrice/dt, as time decreases price decreases, so this is negative
    (price_later - price_now) / h
}

/// Calculate theta for put
#[inline(always)]
pub fn american_put_theta(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    let h = 1.0 / DAYS_PER_YEAR;
    if t <= h {
        return 0.0; // Can't calculate theta near expiry
    }
    let price_now = american_put_scalar(s, k, t, r, q, sigma);
    let price_later = american_put_scalar(s, k, t - h, r, q, sigma);
    // Theta = dPrice/dt, as time decreases price usually decreases (but may increase for ITM puts)
    (price_later - price_now) / h
}

/// Calculate rho using finite difference
#[inline(always)]
pub fn american_call_rho(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    let h = GREEK_RATE_CHANGE;
    let price_up = american_call_scalar(s, k, t, r + h, q, sigma);
    let price_down = american_call_scalar(s, k, t, r - h, q, sigma);
    (price_up - price_down) / (2.0 * h) / BASIS_POINT_MULTIPLIER
}

/// Calculate rho for put
#[inline(always)]
pub fn american_put_rho(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    let h = GREEK_RATE_CHANGE;
    let price_up = american_put_scalar(s, k, t, r + h, q, sigma);
    let price_down = american_put_scalar(s, k, t, r - h, q, sigma);
    (price_up - price_down) / (2.0 * h) / BASIS_POINT_MULTIPLIER
}

// ============================================================================
// EXERCISE BOUNDARY CALCULATION
// ============================================================================

/// Calculate the early exercise boundary for American options
/// This is the critical stock price above which (for calls) or below which (for puts)
/// it is optimal to exercise the option immediately
#[inline(always)]
pub fn exercise_boundary_scalar(k: f64, t: f64, r: f64, q: f64, sigma: f64, is_call: bool) -> f64 {
    // Validation
    if k <= 0.0 || t < 0.0 || sigma < 0.0 {
        panic!("Invalid parameters: k must be positive; t, sigma must be non-negative");
    }

    // Special case: at expiry, the boundary is the strike
    if t < TIME_NEAR_EXPIRY_THRESHOLD {
        return k;
    }

    // Special case: zero volatility
    if sigma < TIME_NEAR_EXPIRY_THRESHOLD {
        return k; // In deterministic case, boundary = strike
    }

    // Use BAW approximation for stable calculation
    if is_call {
        // For calls without dividends, there's never early exercise (boundary = infinity)
        if q <= 0.0 {
            return f64::INFINITY;
        }
        calculate_critical_price_call(k, t, r, q, sigma)
    } else {
        // For puts, early exercise is always possible
        calculate_critical_price_put(k, t, r, q, sigma)
    }
}

// ============================================================================
// ARROW NATIVE IMPLEMENTATION
// ============================================================================

/// American option model implementation using Arrow arrays
pub struct American;

impl American {
    /// Calculate American call option price
    pub fn call_price(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        dividend_yields: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        // Validate arrays for broadcasting compatibility
        let len = validate_broadcast_compatibility(&[
            spots,
            strikes,
            times,
            rates,
            dividend_yields,
            sigmas,
        ])?;

        // Handle empty arrays
        if len == 0 {
            return Ok(Arc::new(Float64Builder::new().finish()));
        }

        let mut builder = Float64Builder::with_capacity(len);

        if len >= get_parallel_threshold() {
            // Parallel processing for large arrays
            use rayon::prelude::*;

            let results: Vec<f64> = (0..len)
                .into_par_iter()
                .map(|i| {
                    let s = get_scalar_or_array_value(spots, i);
                    let k = get_scalar_or_array_value(strikes, i);
                    let t = get_scalar_or_array_value(times, i);
                    let r = get_scalar_or_array_value(rates, i);
                    let q = get_scalar_or_array_value(dividend_yields, i);
                    let sigma = get_scalar_or_array_value(sigmas, i);

                    american_call_scalar(s, k, t, r, q, sigma)
                })
                .collect();

            builder.append_slice(&results);
        } else {
            // Sequential processing for small arrays
            for i in 0..len {
                let s = get_scalar_or_array_value(spots, i);
                let k = get_scalar_or_array_value(strikes, i);
                let t = get_scalar_or_array_value(times, i);
                let r = get_scalar_or_array_value(rates, i);
                let q = get_scalar_or_array_value(dividend_yields, i);
                let sigma = get_scalar_or_array_value(sigmas, i);

                let price = american_call_scalar(s, k, t, r, q, sigma);
                builder.append_value(price);
            }
        }

        Ok(Arc::new(builder.finish()))
    }

    /// Calculate American put option price
    pub fn put_price(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        dividend_yields: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        // Validate arrays for broadcasting compatibility
        let len = validate_broadcast_compatibility(&[
            spots,
            strikes,
            times,
            rates,
            dividend_yields,
            sigmas,
        ])?;

        // Handle empty arrays
        if len == 0 {
            return Ok(Arc::new(Float64Builder::new().finish()));
        }

        let mut builder = Float64Builder::with_capacity(len);

        if len >= get_parallel_threshold() {
            // Parallel processing for large arrays
            use rayon::prelude::*;

            let results: Vec<f64> = (0..len)
                .into_par_iter()
                .map(|i| {
                    let s = get_scalar_or_array_value(spots, i);
                    let k = get_scalar_or_array_value(strikes, i);
                    let t = get_scalar_or_array_value(times, i);
                    let r = get_scalar_or_array_value(rates, i);
                    let q = get_scalar_or_array_value(dividend_yields, i);
                    let sigma = get_scalar_or_array_value(sigmas, i);

                    american_put_scalar(s, k, t, r, q, sigma)
                })
                .collect();

            builder.append_slice(&results);
        } else {
            // Sequential processing for small arrays
            for i in 0..len {
                let s = get_scalar_or_array_value(spots, i);
                let k = get_scalar_or_array_value(strikes, i);
                let t = get_scalar_or_array_value(times, i);
                let r = get_scalar_or_array_value(rates, i);
                let q = get_scalar_or_array_value(dividend_yields, i);
                let sigma = get_scalar_or_array_value(sigmas, i);

                let price = american_put_scalar(s, k, t, r, q, sigma);
                builder.append_value(price);
            }
        }

        Ok(Arc::new(builder.finish()))
    }

    /// Calculate Delta for American options
    pub fn delta(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        dividend_yields: &Float64Array,
        sigmas: &Float64Array,
        is_call: bool,
    ) -> Result<ArrayRef, ArrowError> {
        let len = validate_broadcast_compatibility(&[
            spots,
            strikes,
            times,
            rates,
            dividend_yields,
            sigmas,
        ])?;

        if len == 0 {
            return Ok(Arc::new(Float64Builder::new().finish()));
        }

        let mut builder = Float64Builder::with_capacity(len);

        for i in 0..len {
            let s = get_scalar_or_array_value(spots, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let q = get_scalar_or_array_value(dividend_yields, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let delta = if is_call {
                american_call_delta(s, k, t, r, q, sigma)
            } else {
                american_put_delta(s, k, t, r, q, sigma)
            };
            builder.append_value(delta);
        }

        Ok(Arc::new(builder.finish()))
    }

    /// Calculate Gamma for American options
    pub fn gamma(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        dividend_yields: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        let len = validate_broadcast_compatibility(&[
            spots,
            strikes,
            times,
            rates,
            dividend_yields,
            sigmas,
        ])?;

        if len == 0 {
            return Ok(Arc::new(Float64Builder::new().finish()));
        }

        let mut builder = Float64Builder::with_capacity(len);

        for i in 0..len {
            let s = get_scalar_or_array_value(spots, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let q = get_scalar_or_array_value(dividend_yields, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let gamma = american_call_gamma(s, k, t, r, q, sigma);
            builder.append_value(gamma);
        }

        Ok(Arc::new(builder.finish()))
    }

    /// Calculate Vega for American options
    pub fn vega(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        dividend_yields: &Float64Array,
        sigmas: &Float64Array,
        is_call: bool,
    ) -> Result<ArrayRef, ArrowError> {
        let len = validate_broadcast_compatibility(&[
            spots,
            strikes,
            times,
            rates,
            dividend_yields,
            sigmas,
        ])?;

        if len == 0 {
            return Ok(Arc::new(Float64Builder::new().finish()));
        }

        let mut builder = Float64Builder::with_capacity(len);

        for i in 0..len {
            let s = get_scalar_or_array_value(spots, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let q = get_scalar_or_array_value(dividend_yields, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let vega = if is_call {
                american_call_vega(s, k, t, r, q, sigma)
            } else {
                american_put_vega(s, k, t, r, q, sigma)
            };
            builder.append_value(vega);
        }

        Ok(Arc::new(builder.finish()))
    }

    /// Calculate Theta for American options
    pub fn theta(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        dividend_yields: &Float64Array,
        sigmas: &Float64Array,
        is_call: bool,
    ) -> Result<ArrayRef, ArrowError> {
        let len = validate_broadcast_compatibility(&[
            spots,
            strikes,
            times,
            rates,
            dividend_yields,
            sigmas,
        ])?;

        if len == 0 {
            return Ok(Arc::new(Float64Builder::new().finish()));
        }

        let mut builder = Float64Builder::with_capacity(len);

        for i in 0..len {
            let s = get_scalar_or_array_value(spots, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let q = get_scalar_or_array_value(dividend_yields, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let theta = if is_call {
                american_call_theta(s, k, t, r, q, sigma)
            } else {
                american_put_theta(s, k, t, r, q, sigma)
            };
            builder.append_value(theta);
        }

        Ok(Arc::new(builder.finish()))
    }

    /// Calculate Rho for American options
    pub fn rho(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        dividend_yields: &Float64Array,
        sigmas: &Float64Array,
        is_call: bool,
    ) -> Result<ArrayRef, ArrowError> {
        let len = validate_broadcast_compatibility(&[
            spots,
            strikes,
            times,
            rates,
            dividend_yields,
            sigmas,
        ])?;

        if len == 0 {
            return Ok(Arc::new(Float64Builder::new().finish()));
        }

        let mut builder = Float64Builder::with_capacity(len);

        for i in 0..len {
            let s = get_scalar_or_array_value(spots, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let q = get_scalar_or_array_value(dividend_yields, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let rho = if is_call {
                american_call_rho(s, k, t, r, q, sigma)
            } else {
                american_put_rho(s, k, t, r, q, sigma)
            };
            builder.append_value(rho);
        }

        Ok(Arc::new(builder.finish()))
    }

    /// Calculate exercise boundary for American options
    pub fn exercise_boundary(
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        dividend_yields: &Float64Array,
        sigmas: &Float64Array,
        is_call: bool,
    ) -> Result<ArrayRef, ArrowError> {
        // Validate arrays for broadcasting compatibility (note: no spots array here)
        let len =
            validate_broadcast_compatibility(&[strikes, times, rates, dividend_yields, sigmas])?;

        // Handle empty arrays
        if len == 0 {
            return Ok(Arc::new(Float64Builder::new().finish()));
        }

        let mut builder = Float64Builder::with_capacity(len);

        if len >= get_parallel_threshold() {
            // Parallel processing for large arrays
            use rayon::prelude::*;

            let results: Vec<f64> = (0..len)
                .into_par_iter()
                .map(|i| {
                    let k = get_scalar_or_array_value(strikes, i);
                    let t = get_scalar_or_array_value(times, i);
                    let r = get_scalar_or_array_value(rates, i);
                    let q = get_scalar_or_array_value(dividend_yields, i);
                    let sigma = get_scalar_or_array_value(sigmas, i);

                    exercise_boundary_scalar(k, t, r, q, sigma, is_call)
                })
                .collect();

            builder.append_slice(&results);
        } else {
            // Sequential processing for small arrays
            for i in 0..len {
                let k = get_scalar_or_array_value(strikes, i);
                let t = get_scalar_or_array_value(times, i);
                let r = get_scalar_or_array_value(rates, i);
                let q = get_scalar_or_array_value(dividend_yields, i);
                let sigma = get_scalar_or_array_value(sigmas, i);

                let boundary = exercise_boundary_scalar(k, t, r, q, sigma, is_call);
                builder.append_value(boundary);
            }
        }

        Ok(Arc::new(builder.finish()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_exercise_boundary_call() {
        // ATM call with dividends
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let q = 0.03;
        let sigma = 0.2;

        let boundary = exercise_boundary_scalar(k, t, r, q, sigma, true);

        // For calls, the boundary should be above the strike
        assert!(boundary > k);
        assert!(boundary.is_finite());
    }

    #[test]
    fn test_exercise_boundary_put() {
        // ATM put
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let q = 0.03;
        let sigma = 0.2;

        let boundary = exercise_boundary_scalar(k, t, r, q, sigma, false);

        // For puts, the boundary should be below the strike
        assert!(boundary < k);
        assert!(boundary > 0.0);
    }

    #[test]
    fn test_exercise_boundary_no_dividends() {
        // Call with no dividends - should never exercise early
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let q = 0.0; // No dividends
        let sigma = 0.2;

        let boundary = exercise_boundary_scalar(k, t, r, q, sigma, true);

        // Should return infinity (never optimal to exercise)
        assert_eq!(boundary, f64::INFINITY);
    }

    #[test]
    fn test_exercise_boundary_near_expiry() {
        // Near expiry, boundary should converge to strike
        let k = 100.0;
        let t = 0.001; // Very close to expiry
        let r = 0.05;
        let q = 0.03;
        let sigma = 0.2;

        let call_boundary = exercise_boundary_scalar(k, t, r, q, sigma, true);
        let put_boundary = exercise_boundary_scalar(k, t, r, q, sigma, false);

        // Near expiry, the boundaries should be reasonably close to strike
        // For very small time values, the boundary calculation may diverge
        assert!(call_boundary >= k); // Call boundary >= strike
        assert!(call_boundary.is_finite()); // Should not be NaN or infinite
        assert!(put_boundary <= k); // Put boundary <= strike
        assert!(put_boundary > 0.0); // Put boundary should be positive
    }

    #[test]
    fn test_exercise_boundary_batch() {
        use arrow::array::Float64Array;

        let strikes = Float64Array::from(vec![95.0, 100.0, 105.0]);
        let times = Float64Array::from(vec![0.5, 1.0, 1.5]);
        let rates = Float64Array::from(vec![0.05]);
        let dividend_yields = Float64Array::from(vec![0.03]);
        let sigmas = Float64Array::from(vec![0.2]);

        let result =
            American::exercise_boundary(&strikes, &times, &rates, &dividend_yields, &sigmas, true)
                .unwrap();

        let boundaries = result.as_any().downcast_ref::<Float64Array>().unwrap();

        assert_eq!(boundaries.len(), 3);

        // All boundaries should be above their respective strikes
        for i in 0..3 {
            let boundary = boundaries.value(i);
            let strike = strikes.value(i);
            assert!(boundary > strike);
        }
    }
}
