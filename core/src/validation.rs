//! Input validation utilities for option pricing
//!
//! Provides common validation functions to ensure input parameters are within
//! acceptable ranges for option pricing calculations.

use crate::constants::{
    MAX_PRICE, MAX_RATE, MAX_TIME, MAX_VOLATILITY, MIN_PRICE, MIN_RATE, MIN_TIME, MIN_VOLATILITY,
};

#[cfg(test)]
use crate::constants::{TEST_RATE, TEST_SPOT, TEST_STRIKE, TEST_TIME, TEST_VOLATILITY};

/// Validates that a value is positive
///
/// # Arguments
/// * `value` - The value to validate
/// * `name` - The name of the parameter (for error messages)
///
/// # Returns
/// * `Ok(())` if the value is positive
/// * `Err(String)` with a descriptive error message if the value is not positive
#[inline]
pub fn validate_positive(value: f64, name: &str) -> Result<(), String> {
    if value <= 0.0 {
        Err(format!("{name} must be positive, got {value}"))
    } else {
        Ok(())
    }
}

/// Validates basic option input parameters
///
/// Checks that spot, strike, time to maturity, and volatility are all positive.
///
/// # Arguments
/// * `s` - Spot price
/// * `k` - Strike price
/// * `t` - Time to maturity
/// * `sigma` - Volatility
///
/// # Returns
/// * `Ok(())` if all parameters are valid
/// * `Err(String)` with a descriptive error message if any parameter is invalid
#[inline]
pub fn validate_option_inputs(s: f64, k: f64, t: f64, sigma: f64) -> Result<(), String> {
    validate_positive(s, "Spot price")?;
    validate_positive(k, "Strike price")?;
    validate_positive(t, "Time to maturity")?;
    validate_positive(sigma, "Volatility")?;
    Ok(())
}

/// Validates option inputs with additional range checks
///
/// In addition to positivity checks, verifies that parameters are within
/// practical ranges defined in constants.
///
/// # Arguments
/// * `s` - Spot price
/// * `k` - Strike price
/// * `t` - Time to maturity
/// * `r` - Risk-free rate
/// * `sigma` - Volatility
///
/// # Returns
/// * `Ok(())` if all parameters are valid
/// * `Err(String)` with a descriptive error message if any parameter is invalid
#[inline]
pub fn validate_option_inputs_with_ranges(
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    sigma: f64,
) -> Result<(), String> {
    // Basic positivity checks
    validate_option_inputs(s, k, t, sigma)?;

    // Range checks
    if !(MIN_PRICE..=MAX_PRICE).contains(&s) {
        return Err(format!(
            "Spot price must be between {MIN_PRICE} and {MAX_PRICE}, got {s}"
        ));
    }
    if !(MIN_PRICE..=MAX_PRICE).contains(&k) {
        return Err(format!(
            "Strike price must be between {MIN_PRICE} and {MAX_PRICE}, got {k}"
        ));
    }
    if !(MIN_TIME..=MAX_TIME).contains(&t) {
        return Err(format!(
            "Time to maturity must be between {MIN_TIME} and {MAX_TIME} years, got {t}"
        ));
    }
    if !(MIN_RATE..=MAX_RATE).contains(&r) {
        return Err(format!(
            "Risk-free rate must be between {MIN_RATE} and {MAX_RATE}, got {r}"
        ));
    }
    if !(MIN_VOLATILITY..=MAX_VOLATILITY).contains(&sigma) {
        return Err(format!(
            "Volatility must be between {MIN_VOLATILITY} and {MAX_VOLATILITY}, got {sigma}"
        ));
    }

    Ok(())
}

/// Validates Black76 model inputs
///
/// Checks that forward price, strike, time to maturity, and volatility are all positive.
///
/// # Arguments
/// * `f` - Forward price
/// * `k` - Strike price
/// * `t` - Time to maturity
/// * `sigma` - Volatility
///
/// # Returns
/// * `Ok(())` if all parameters are valid
/// * `Err(String)` with a descriptive error message if any parameter is invalid
#[inline]
pub fn validate_black76_inputs(f: f64, k: f64, t: f64, sigma: f64) -> Result<(), String> {
    validate_positive(f, "Forward price")?;
    validate_positive(k, "Strike price")?;
    validate_positive(t, "Time to maturity")?;
    validate_positive(sigma, "Volatility")?;
    Ok(())
}

/// Validates Merton model inputs (Black-Scholes with dividends)
///
/// Checks that all standard option inputs are positive and dividend yield is non-negative.
///
/// # Arguments
/// * `s` - Spot price
/// * `k` - Strike price
/// * `t` - Time to maturity
/// * `r` - Risk-free rate
/// * `q` - Dividend yield
/// * `sigma` - Volatility
///
/// # Returns
/// * `Ok(())` if all parameters are valid
/// * `Err(String)` with a descriptive error message if any parameter is invalid
#[inline]
pub fn validate_merton_inputs(
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
) -> Result<(), String> {
    validate_option_inputs_with_ranges(s, k, t, r, sigma)?;

    if q < 0.0 {
        return Err(format!("Dividend yield must be non-negative, got {q}"));
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_positive() {
        assert!(validate_positive(1.0, "test").is_ok());
        assert!(validate_positive(0.001, "test").is_ok());
        assert!(validate_positive(0.0, "test").is_err());
        assert!(validate_positive(-1.0, "test").is_err());
    }

    #[test]
    fn test_validate_option_inputs() {
        assert!(validate_option_inputs(TEST_SPOT, TEST_STRIKE, TEST_TIME, TEST_VOLATILITY).is_ok());
        assert!(validate_option_inputs(0.0, TEST_STRIKE, TEST_TIME, TEST_VOLATILITY).is_err());
        assert!(validate_option_inputs(TEST_SPOT, 0.0, TEST_TIME, TEST_VOLATILITY).is_err());
        assert!(validate_option_inputs(TEST_SPOT, TEST_STRIKE, 0.0, TEST_VOLATILITY).is_err());
        assert!(validate_option_inputs(TEST_SPOT, TEST_STRIKE, TEST_TIME, 0.0).is_err());
    }

    #[test]
    fn test_validate_option_inputs_with_ranges() {
        // Valid inputs
        assert!(validate_option_inputs_with_ranges(
            TEST_SPOT,
            TEST_STRIKE,
            TEST_TIME,
            TEST_RATE,
            TEST_VOLATILITY
        )
        .is_ok());

        // Out of range tests
        assert!(validate_option_inputs_with_ranges(
            0.001,
            TEST_STRIKE,
            TEST_TIME,
            TEST_RATE,
            TEST_VOLATILITY
        )
        .is_err()); // s < MIN_PRICE
        assert!(validate_option_inputs_with_ranges(
            TEST_SPOT,
            TEST_STRIKE,
            0.0001,
            TEST_RATE,
            TEST_VOLATILITY
        )
        .is_err()); // t < MIN_TIME
        assert!(validate_option_inputs_with_ranges(
            TEST_SPOT,
            TEST_STRIKE,
            TEST_TIME,
            -2.0,
            TEST_VOLATILITY
        )
        .is_err()); // r < MIN_RATE
        assert!(validate_option_inputs_with_ranges(
            TEST_SPOT,
            TEST_STRIKE,
            TEST_TIME,
            TEST_RATE,
            0.0001
        )
        .is_err());
        // sigma < MIN_VOLATILITY
    }
}
