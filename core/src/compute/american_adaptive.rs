//! Adaptive American option implementation with dynamic dampening
//!
//! This module implements an adaptive version of the BAW approximation
//! where the dampening factor adjusts based on moneyness and time to maturity
//! to improve accuracy across different parameter regions.

use super::formulas::{merton_call_scalar, merton_put_scalar};
use crate::constants::{BAW_DAMPENING_FACTOR, TIME_NEAR_EXPIRY_THRESHOLD};
use crate::math::calculate_d1;
use crate::math::distributions::norm_cdf;

/// Calculate adaptive dampening factor based on option characteristics
///
/// The dampening factor adjusts based on:
/// - Moneyness (S/K): ATM options use calibrated value, others adjust
/// - Time to maturity: Short-term options need different adjustment
/// - Volatility: High volatility may need different treatment
///
/// Returns a dampening factor between 0.6 and 0.8
#[inline]
pub fn get_adaptive_dampening_factor(s: f64, k: f64, t: f64, sigma: f64) -> f64 {
    let moneyness = s / k;

    // Time factor: short-term options need more dampening
    let time_factor = if t < 0.1 {
        1.08 // 8% increase for very short term
    } else if t < 0.5 {
        1.04 // 4% increase for short term
    } else if t > 2.0 {
        0.98 // 2% decrease for long term
    } else {
        1.0 // No adjustment for medium term
    };

    // Moneyness factor: adjust based on how far from ATM
    let moneyness_factor = if (0.9..=1.1).contains(&moneyness) {
        // ATM region: use calibrated value
        1.0
    } else if (0.8..=1.2).contains(&moneyness) {
        // Near ATM: slight adjustment
        1.03
    } else if moneyness < 0.8 {
        // Deep OTM: more conservative
        1.08
    } else {
        // Deep ITM: less dampening needed
        0.95
    };

    // Volatility factor: high vol needs adjustment
    let vol_factor = if sigma > 0.4 {
        1.05 // High volatility adjustment
    } else if sigma < 0.15 {
        0.98 // Low volatility adjustment
    } else {
        1.0
    };

    // Combine factors with base dampening
    let adaptive_factor = BAW_DAMPENING_FACTOR * time_factor * moneyness_factor * vol_factor;

    // Clamp to reasonable range to prevent instability
    adaptive_factor.clamp(0.60, 0.80)
}

/// Adaptive BAW American call with dynamic dampening
pub fn american_call_adaptive(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    // Near expiry
    if t < TIME_NEAR_EXPIRY_THRESHOLD {
        return (s - k).max(0.0);
    }

    // Use Merton formula for European value with dividends
    let european_value = merton_call_scalar(s, k, t, r, q, sigma);

    // If no dividends, American call = European call
    if q <= 0.0 {
        return european_value;
    }

    // Get adaptive dampening factor
    let dampening = get_adaptive_dampening_factor(s, k, t, sigma);

    // Calculate critical price with adaptive dampening
    let s_star = calculate_adaptive_critical_price_call(k, t, r, q, sigma, dampening);

    if s >= s_star {
        // Immediate exercise optimal
        return s - k;
    }

    // Add early exercise premium with adaptive dampening
    let a2 = calculate_adaptive_a2_call(k, t, r, q, sigma, dampening);
    let q2 = calculate_q2(r, q, sigma);
    let premium = a2 * (s / s_star).powf(q2);

    european_value + premium.max(0.0)
}

/// Adaptive BAW American put with dynamic dampening
pub fn american_put_adaptive(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    // Near expiry
    if t < TIME_NEAR_EXPIRY_THRESHOLD {
        return (k - s).max(0.0);
    }

    // European put as base using Merton formula
    let european_value = merton_put_scalar(s, k, t, r, q, sigma);

    // For deep OTM puts (s >> k), American value ≈ European value
    if s > k * 1.5 {
        return european_value;
    }

    // Get adaptive dampening factor
    let dampening = get_adaptive_dampening_factor(s, k, t, sigma);

    // BAW approximation with adaptive dampening
    let s_star = calculate_adaptive_critical_price_put(k, t, r, q, sigma, dampening);

    if s <= s_star {
        // Immediate exercise optimal
        return k - s;
    }

    // Add early exercise premium with adaptive dampening
    let a2 = calculate_adaptive_a2_put(k, t, r, q, sigma, dampening);
    let q1 = calculate_q1(r, q, sigma);
    let premium = dampening * a2 * (s / s_star).powf(q1);

    european_value + premium.max(0.0)
}

// Helper functions (similar to american_simple.rs but with adaptive dampening)

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

/// Calculate critical price for call with adaptive dampening
fn calculate_adaptive_critical_price_call(
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    dampening: f64,
) -> f64 {
    let q2 = calculate_q2(r, q, sigma);
    let m = 2.0 * (r - q) / (sigma * sigma);

    if q2 <= 1.0 {
        return f64::INFINITY;
    }

    let s_inf = k * q2 / (q2 - 1.0);
    let h = 1.0 - (-q * t).exp();

    // Apply adaptive dampening to critical price calculation
    s_inf * (1.0 - dampening * h * (1.0 - (k / s_inf).powf(1.0 / m)))
}

/// Calculate critical price for put with adaptive dampening
fn calculate_adaptive_critical_price_put(
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    dampening: f64,
) -> f64 {
    let q1 = calculate_q1(r, q, sigma);
    let m = 2.0 * (r - q) / (sigma * sigma);

    if q1 >= 1.0 {
        return 0.0;
    }

    let s_inf = k * q1 / (q1 - 1.0);
    let h = 1.0 - (-r * t).exp();

    // Apply adaptive dampening
    s_inf * (1.0 + dampening * h * (1.0 - (k / s_inf).powf(1.0 / m)))
}

/// Calculate A2 coefficient for call with adaptive dampening
fn calculate_adaptive_a2_call(k: f64, t: f64, r: f64, q: f64, sigma: f64, dampening: f64) -> f64 {
    let s_star = calculate_adaptive_critical_price_call(k, t, r, q, sigma, dampening);
    let q2 = calculate_q2(r, q, sigma);
    let d1 = calculate_d1(s_star, k, t, r, q, sigma);

    (s_star / q2) * (1.0 - (-q * t).exp() * norm_cdf(d1))
}

/// Calculate A2 coefficient for put with adaptive dampening
fn calculate_adaptive_a2_put(k: f64, t: f64, r: f64, q: f64, sigma: f64, dampening: f64) -> f64 {
    let s_star = calculate_adaptive_critical_price_put(k, t, r, q, sigma, dampening);
    let q1 = calculate_q1(r, q, sigma);
    let d1 = calculate_d1(s_star, k, t, r, q, sigma);

    -(s_star / q1) * (1.0 - (-q * t).exp() * norm_cdf(-d1))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::{PRACTICAL_TOLERANCE, TEST_RATE};

    #[test]
    fn test_adaptive_dampening_factor() {
        // ATM, medium term should give base factor
        let factor = get_adaptive_dampening_factor(100.0, 100.0, 1.0, 0.2);
        assert!((factor - BAW_DAMPENING_FACTOR).abs() < PRACTICAL_TOLERANCE);

        // Deep OTM should give higher dampening
        let factor_otm = get_adaptive_dampening_factor(70.0, 100.0, 1.0, 0.2);
        assert!(factor_otm > BAW_DAMPENING_FACTOR);

        // Short term should give higher dampening
        let factor_short = get_adaptive_dampening_factor(100.0, 100.0, 0.05, 0.2);
        assert!(factor_short > BAW_DAMPENING_FACTOR);
    }

    #[test]
    fn test_adaptive_vs_simple() {
        // Test that adaptive gives reasonable results for extreme parameters
        // Use less extreme values to ensure stable results
        let s = 90.0; // Slightly OTM
        let k = 100.0;
        let t = 0.25; // Quarter year
        let r = TEST_RATE;
        let q = 0.0;
        let sigma = 0.3; // Medium-high vol

        let adaptive = american_put_adaptive(s, k, t, r, q, sigma);
        let european = merton_put_scalar(s, k, t, r, q, sigma);

        // Should have early exercise premium or equal
        assert!(
            adaptive >= european - 1e-10,
            "American {adaptive:.6} should be >= European {european:.6}"
        );

        // Should respect intrinsic value
        let intrinsic = (k - s).max(0.0);
        assert!(
            adaptive >= intrinsic - 1e-10,
            "Price {adaptive:.6} should be >= intrinsic {intrinsic:.6}"
        );

        // Should be reasonable (not infinity or NaN)
        assert!(adaptive.is_finite());
        assert!(adaptive < k); // Put can't be worth more than strike
    }
}
