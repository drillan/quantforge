//! Black-Scholes mathematical functions
//!
//! Common mathematical functions for Black-Scholes and related models.

use crate::constants::HALF;

/// Calculate Black-Scholes d1 and d2 parameters
///
/// # Arguments
/// * `s` - Spot price
/// * `k` - Strike price
/// * `t` - Time to maturity
/// * `r` - Risk-free rate
/// * `q` - Dividend yield (0 for no dividends)
/// * `sigma` - Volatility
///
/// # Returns
/// (d1, d2) tuple
#[inline(always)]
pub fn calculate_d1_d2(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> (f64, f64) {
    let sqrt_t = t.sqrt();
    let variance_term = sigma * sigma * HALF;
    let d1 = ((s / k).ln() + (r - q + variance_term) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;
    (d1, d2)
}

/// Calculate Black76 d1 and d2 parameters
///
/// # Arguments
/// * `f` - Forward price
/// * `k` - Strike price
/// * `t` - Time to maturity
/// * `sigma` - Volatility
///
/// # Returns
/// (d1, d2) tuple
#[inline(always)]
pub fn calculate_black76_d1_d2(f: f64, k: f64, t: f64, sigma: f64) -> (f64, f64) {
    let sqrt_t = t.sqrt();
    let d1 = ((f / k).ln() + (sigma * sigma * HALF) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;
    (d1, d2)
}

/// Calculate d1 parameter only (for efficiency when d2 not needed)
///
/// # Arguments
/// * `s` - Spot price
/// * `k` - Strike price
/// * `t` - Time to maturity
/// * `r` - Risk-free rate
/// * `q` - Dividend yield (0 for no dividends)
/// * `sigma` - Volatility
///
/// # Returns
/// d1 value
#[inline(always)]
pub fn calculate_d1(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    let sqrt_t = t.sqrt();
    let variance_term = sigma * sigma * HALF;
    ((s / k).ln() + (r - q + variance_term) * t) / (sigma * sqrt_t)
}

/// Calculate d2 from d1
///
/// # Arguments
/// * `d1` - d1 parameter
/// * `sigma` - Volatility
/// * `sqrt_t` - Square root of time to maturity
///
/// # Returns
/// d2 value
#[inline(always)]
pub fn d1_to_d2(d1: f64, sigma: f64, sqrt_t: f64) -> f64 {
    d1 - sigma * sqrt_t
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::{PRACTICAL_TOLERANCE, TEST_RATE};

    #[test]
    fn test_d1_d2_calculation() {
        let (d1, d2) = calculate_d1_d2(100.0, 100.0, 1.0, TEST_RATE, 0.0, 0.2);
        assert!((d1 - 0.35).abs() < PRACTICAL_TOLERANCE * 10.0);
        assert!((d2 - 0.15).abs() < PRACTICAL_TOLERANCE * 10.0);
    }

    #[test]
    fn test_black76_d1_d2() {
        let (d1, d2) = calculate_black76_d1_d2(100.0, 100.0, 1.0, 0.2);
        assert!((d1 - 0.1).abs() < PRACTICAL_TOLERANCE * 10.0);
        assert!((d2 - -0.1).abs() < PRACTICAL_TOLERANCE * 10.0);
    }
}
