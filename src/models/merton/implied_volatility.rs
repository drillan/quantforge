//! Merton model implied volatility calculation.

use crate::constants::{IV_MAX_ITERATIONS, IV_TOLERANCE_PRICE};
use crate::error::QuantForgeError;
use crate::models::iv_initial_guess::adaptive_initial_guess;
use crate::models::merton::greeks::vega;
use crate::models::merton::pricing::{call_price, put_price};

/// Calculate implied volatility for a Merton model option using Newton-Raphson method.
///
/// # Arguments
/// * `price` - Observed option price
/// * `s` - Spot price
/// * `k` - Strike price
/// * `t` - Time to maturity (years)
/// * `r` - Risk-free rate
/// * `q` - Dividend yield
/// * `is_call` - true for call, false for put
/// * `initial_guess` - Optional initial guess for volatility
///
/// # Returns
/// Result containing the implied volatility or an error
#[allow(clippy::too_many_arguments)]
pub fn calculate_implied_volatility(
    price: f64,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    is_call: bool,
    initial_guess: Option<f64>,
) -> Result<f64, QuantForgeError> {
    // Input validation
    if price <= 0.0 {
        return Err(QuantForgeError::InvalidInput(
            "Option price must be positive".to_string(),
        ));
    }

    if s <= 0.0 || k <= 0.0 {
        return Err(QuantForgeError::InvalidInput(
            "Spot and strike must be positive".to_string(),
        ));
    }

    if t <= 0.0 {
        return Err(QuantForgeError::InvalidInput(
            "Time to maturity must be positive".to_string(),
        ));
    }

    // Check if price is within arbitrage bounds
    let intrinsic_value = if is_call {
        (s * (-q * t).exp() - k * (-r * t).exp()).max(0.0)
    } else {
        (k * (-r * t).exp() - s * (-q * t).exp()).max(0.0)
    };

    if price < intrinsic_value {
        return Err(QuantForgeError::InvalidInput(format!(
            "Price {price} is below intrinsic value {intrinsic_value}"
        )));
    }

    // Maximum possible value
    let max_value = if is_call {
        s * (-q * t).exp()
    } else {
        k * (-r * t).exp()
    };

    if price > max_value {
        return Err(QuantForgeError::InvalidInput(format!(
            "Price {price} exceeds maximum value {max_value}"
        )));
    }

    // Initial guess for implied volatility
    let mut sigma = initial_guess.unwrap_or_else(|| {
        // Use the common initial guess function
        adaptive_initial_guess(price, s, k, t, r, is_call)
    });

    // Newton-Raphson iteration
    for _ in 0..IV_MAX_ITERATIONS {
        // Calculate option price and vega
        let model_price = if is_call {
            call_price(s, k, t, r, q, sigma)
        } else {
            put_price(s, k, t, r, q, sigma)
        };

        let price_diff = model_price - price;

        // Check convergence
        if price_diff.abs() < IV_TOLERANCE_PRICE {
            return Ok(sigma);
        }

        // Calculate vega for Newton-Raphson update
        let option_vega = vega(s, k, t, r, q, sigma) * 100.0; // Convert back from per 1% to per 1

        // Check for zero vega (avoid division by zero)
        if option_vega.abs() < 1e-10 {
            return Err(QuantForgeError::ConvergenceFailed(IV_MAX_ITERATIONS));
        }

        // Newton-Raphson update
        let delta_sigma = price_diff / option_vega;
        sigma -= delta_sigma;

        // Ensure sigma remains positive
        if sigma <= 0.0 {
            sigma = 0.001; // Reset to small positive value
        }

        // Cap sigma at reasonable maximum
        if sigma > 5.0 {
            sigma = 5.0;
        }
    }

    Err(QuantForgeError::ConvergenceFailed(IV_MAX_ITERATIONS))
}

/// Calculate implied volatility for a batch of option prices.
///
/// # Arguments
/// * `prices` - Array of observed option prices
/// * `s` - Spot price
/// * `k` - Strike price
/// * `t` - Time to maturity (years)
/// * `r` - Risk-free rate
/// * `q` - Dividend yield
/// * `is_call` - true for call, false for put
///
/// # Returns
/// Vector of Results containing implied volatilities or errors
pub fn implied_volatility_batch(
    prices: &[f64],
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    is_call: bool,
) -> Vec<Result<f64, QuantForgeError>> {
    prices
        .iter()
        .map(|&price| calculate_implied_volatility(price, s, k, t, r, q, is_call, None))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::merton::pricing::{call_price, put_price};
    use approx::assert_relative_eq;

    const TEST_TOLERANCE: f64 = 1e-5;

    #[test]
    fn test_implied_volatility_recovery() {
        // Test that we can recover the volatility used to generate a price
        let s = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let q = 0.02;
        let true_sigma = 0.25;

        // Generate prices
        let call_price_val = call_price(s, k, t, r, q, true_sigma);
        let put_price_val = put_price(s, k, t, r, q, true_sigma);

        // Recover implied volatilities
        let call_iv =
            calculate_implied_volatility(call_price_val, s, k, t, r, q, true, None).unwrap();
        let put_iv =
            calculate_implied_volatility(put_price_val, s, k, t, r, q, false, None).unwrap();

        // Check recovery accuracy
        assert_relative_eq!(call_iv, true_sigma, epsilon = TEST_TOLERANCE);
        assert_relative_eq!(put_iv, true_sigma, epsilon = TEST_TOLERANCE);
    }

    #[test]
    fn test_implied_volatility_with_zero_dividend() {
        // Test that q=0 gives same IV as Black-Scholes
        let s = 100.0;
        let k = 110.0;
        let t = 0.5;
        let r = 0.05;
        let q = 0.0;
        let true_sigma = 0.30;

        let call_price_val = call_price(s, k, t, r, q, true_sigma);
        let call_iv =
            calculate_implied_volatility(call_price_val, s, k, t, r, q, true, None).unwrap();

        assert_relative_eq!(call_iv, true_sigma, epsilon = TEST_TOLERANCE);
    }

    #[test]
    fn test_implied_volatility_error_cases() {
        let s = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let q = 0.02;

        // Negative price
        let result = calculate_implied_volatility(-10.0, s, k, t, r, q, true, None);
        assert!(result.is_err());

        // Price below intrinsic value
        let intrinsic = (s * (-q * t).exp() - k * (-r * t).exp()).max(0.0);
        let result = calculate_implied_volatility(intrinsic * 0.5, s, k, t, r, q, true, None);
        assert!(result.is_err());

        // Price above maximum value
        let max_val = s * (-q * t).exp();
        let result = calculate_implied_volatility(max_val * 1.5, s, k, t, r, q, true, None);
        assert!(result.is_err());
    }

    #[test]
    fn test_implied_volatility_batch() {
        let s = 100.0;
        let k = 100.0;
        let t = 0.25;
        let r = 0.05;
        let q = 0.03;

        // Generate prices for different volatilities
        let sigmas = [0.15, 0.20, 0.25, 0.30, 0.35];
        let prices: Vec<f64> = sigmas
            .iter()
            .map(|&sigma| call_price(s, k, t, r, q, sigma))
            .collect();

        // Calculate implied volatilities
        let results = implied_volatility_batch(&prices, s, k, t, r, q, true);

        // Check recovery
        for (i, result) in results.iter().enumerate() {
            let iv = result.as_ref().unwrap();
            assert_relative_eq!(*iv, sigmas[i], epsilon = TEST_TOLERANCE);
        }
    }
}
