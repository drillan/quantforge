//! Simplified American option implementation for testing
//! Based on Barone-Adesi and Whaley (1987) approximation

use super::formulas::{merton_call_scalar, merton_put_scalar};
use crate::constants::TIME_NEAR_EXPIRY_THRESHOLD;
use crate::math::calculate_d1;
use crate::math::distributions::norm_cdf;

/// Simplified BAW for testing - American call with dividends  
pub fn american_call_simple(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    // Near expiry
    if t < TIME_NEAR_EXPIRY_THRESHOLD {
        return (s - k).max(0.0);
    }

    // Use proper Merton formula for European value with dividends
    let european_value = merton_call_scalar(s, k, t, r, q, sigma);

    // If no dividends, American call = European call
    if q <= 0.0 {
        return european_value;
    }

    // Barone-Adesi-Whaley approximation for early exercise premium
    // Always apply BAW approximation when there are dividends
    let s_star = calculate_critical_price_call(k, t, r, q, sigma);
    if s >= s_star {
        // Immediate exercise optimal
        return s - k;
    }

    // Add early exercise premium
    let a2 = calculate_a2_call(k, t, r, q, sigma);
    let q2 = calculate_q2(r, q, sigma);
    let premium = a2 * (s / s_star).powf(q2);
    european_value + premium.max(0.0)
}

/// Simplified American put using Barone-Adesi-Whaley approximation
pub fn american_put_simple(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    // Near expiry
    if t < TIME_NEAR_EXPIRY_THRESHOLD {
        return (k - s).max(0.0);
    }

    // European put as base using proper Merton formula
    let european_value = merton_put_scalar(s, k, t, r, q, sigma);

    // For deep OTM puts (s >> k), American value ≈ European value
    // Early exercise is never optimal
    if s > k * 1.5 {
        return european_value;
    }

    // BAW approximation for early exercise premium
    let s_star = calculate_critical_price_put(k, t, r, q, sigma);
    if s <= s_star {
        // Immediate exercise optimal
        return k - s;
    }

    // Add early exercise premium
    let a2 = calculate_a2_put(k, t, r, q, sigma);
    let q1 = calculate_q1(r, q, sigma);
    // q1 is negative, so we use it directly to get decreasing premium as s increases
    let premium = a2 * (s / s_star).powf(q1);
    european_value + premium.max(0.0)
}

// Helper functions for BAW approximation

#[inline]
fn calculate_q1(r: f64, q: f64, sigma: f64) -> f64 {
    let b = r - q;
    let sigma_sq = sigma * sigma;
    (-(b - sigma_sq / 2.0) - ((b - sigma_sq / 2.0).powi(2) + 2.0 * sigma_sq * r).sqrt()) / sigma_sq
}

#[inline]
fn calculate_q2(r: f64, q: f64, sigma: f64) -> f64 {
    let b = r - q;
    let sigma_sq = sigma * sigma;
    (-(b - sigma_sq / 2.0) + ((b - sigma_sq / 2.0).powi(2) + 2.0 * sigma_sq * r).sqrt()) / sigma_sq
}

/// Calculate critical price for American call (simplified)
fn calculate_critical_price_call(k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    // Simplified approximation - should use iterative method for accuracy
    let q2 = calculate_q2(r, q, sigma);
    let _n = 2.0 * r / (sigma * sigma);
    let m = 2.0 * (r - q) / (sigma * sigma);

    // Prevent division by zero or invalid values
    if q2 <= 1.0 {
        return f64::INFINITY; // No early exercise
    }

    // Initial guess based on perpetual option
    let s_inf = k * q2 / (q2 - 1.0);

    // Time adjustment factor
    let h = 1.0 - (-q * t).exp();

    // Approximate critical price
    s_inf * (1.0 - h * (1.0 - (k / s_inf).powf(1.0 / m)))
}

/// Calculate critical price for American put (simplified)
fn calculate_critical_price_put(k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    // Simplified approximation
    let q1 = calculate_q1(r, q, sigma);
    let _n = 2.0 * r / (sigma * sigma);
    let m = 2.0 * (r - q) / (sigma * sigma);

    // q1 is typically negative for puts, so q1 - 1 is more negative
    // Prevent invalid values
    if q1 >= 1.0 {
        return 0.0; // No early exercise
    }

    // Initial guess based on perpetual option
    let s_inf = k * q1 / (q1 - 1.0);

    // Time adjustment factor
    let h = 1.0 - (-r * t).exp();

    // Approximate critical price
    s_inf * (1.0 + h * (1.0 - (k / s_inf).powf(1.0 / m)))
}

/// Calculate A2 coefficient for call
fn calculate_a2_call(k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    let s_star = calculate_critical_price_call(k, t, r, q, sigma);
    let q2 = calculate_q2(r, q, sigma);
    let d1 = calculate_d1(s_star, k, t, r, q, sigma);

    (s_star / q2) * (1.0 - (-q * t).exp() * norm_cdf(d1))
}

/// Calculate A2 coefficient for put
fn calculate_a2_put(k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    let s_star = calculate_critical_price_put(k, t, r, q, sigma);
    let q1 = calculate_q1(r, q, sigma);
    let d1 = calculate_d1(s_star, k, t, r, q, sigma);

    -(s_star / q1) * (1.0 - (-q * t).exp() * norm_cdf(-d1))
}
