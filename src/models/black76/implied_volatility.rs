//! Black76 implied volatility calculations

use super::{pricing, Black76Params};
use crate::constants::{IV_MAX_ITERATIONS, IV_TOLERANCE_PRICE};
use crate::error::QuantForgeError;

/// Maximum volatility for IV calculation
const MAX_VOLATILITY: f64 = 10.0;
/// Minimum volatility for IV calculation
const MIN_VOLATILITY: f64 = 0.001;

/// Calculate implied volatility using Newton-Raphson method
pub fn calculate_iv(
    market_price: f64,
    params: &Black76Params,
    is_call: bool,
    initial_guess: Option<f64>,
) -> Result<f64, QuantForgeError> {
    // Validate inputs
    if market_price <= 0.0 {
        return Err(QuantForgeError::InvalidInput(
            "Market price must be positive".to_string(),
        ));
    }

    // Check if price is within arbitrage bounds
    let discount = params.discount_factor();
    let intrinsic = if is_call {
        discount * (params.forward - params.strike).max(0.0)
    } else {
        discount * (params.strike - params.forward).max(0.0)
    };

    if market_price < intrinsic {
        return Err(QuantForgeError::InvalidInput(
            "Market price violates arbitrage bounds".to_string(),
        ));
    }

    // Initial guess using Brenner-Subrahmanyam approximation
    let mut sigma = match initial_guess {
        Some(guess) if guess > MIN_VOLATILITY && guess < MAX_VOLATILITY => guess,
        _ => {
            // Brenner-Subrahmanyam approximation for ATM options
            let sqrt_2pi = (2.0 * std::f64::consts::PI).sqrt();
            (market_price / (params.forward * discount)) * sqrt_2pi / params.time.sqrt()
        }
    };

    // Ensure initial guess is within bounds
    sigma = sigma.clamp(MIN_VOLATILITY, MAX_VOLATILITY);

    // Newton-Raphson iteration
    for _ in 0..IV_MAX_ITERATIONS {
        let mut test_params = *params;
        test_params.sigma = sigma;

        // Calculate option price with current sigma
        let price = if is_call {
            pricing::call_price(&test_params)
        } else {
            pricing::put_price(&test_params)
        };

        // Calculate vega (derivative with respect to sigma)
        let d1 = test_params.d1();
        let vega = discount * params.forward * normal_pdf(d1) * params.time.sqrt();

        // Check convergence
        let price_diff = price - market_price;
        if price_diff.abs() < IV_TOLERANCE_PRICE {
            return Ok(sigma);
        }

        // Avoid division by zero
        if vega.abs() < 1e-10 {
            // Try Brent's method as fallback
            return calculate_iv_brent(market_price, params, is_call);
        }

        // Newton-Raphson update
        let delta_sigma = price_diff / vega;
        sigma -= delta_sigma;

        // Keep sigma within bounds
        sigma = sigma.clamp(MIN_VOLATILITY, MAX_VOLATILITY);

        // Check if we've converged in terms of sigma change
        if delta_sigma.abs() < IV_TOLERANCE_PRICE {
            return Ok(sigma);
        }
    }

    // If Newton-Raphson doesn't converge, try Brent's method
    calculate_iv_brent(market_price, params, is_call)
}

/// Calculate implied volatility using Brent's method (fallback)
fn calculate_iv_brent(
    market_price: f64,
    params: &Black76Params,
    is_call: bool,
) -> Result<f64, QuantForgeError> {
    let mut a = MIN_VOLATILITY;
    let mut b = MAX_VOLATILITY;

    // Function to evaluate price difference
    let price_diff = |sigma: f64| -> f64 {
        let mut test_params = *params;
        test_params.sigma = sigma;
        let price = if is_call {
            pricing::call_price(&test_params)
        } else {
            pricing::put_price(&test_params)
        };
        price - market_price
    };

    let mut fa = price_diff(a);
    let mut fb = price_diff(b);

    // Check if root is bracketed
    if fa * fb > 0.0 {
        return Err(QuantForgeError::BracketingFailed);
    }

    let mut c = b;
    let mut fc = fb;
    let mut d = 0.0;
    let mut e = 0.0;

    for _ in 0..IV_MAX_ITERATIONS {
        if fb * fc > 0.0 {
            c = a;
            fc = fa;
            d = b - a;
            e = d;
        }

        if fc.abs() < fb.abs() {
            a = b;
            b = c;
            c = a;
            fa = fb;
            fb = fc;
            fc = fa;
        }

        let tol = 2.0 * f64::EPSILON * b.abs() + IV_TOLERANCE_PRICE;
        let m = 0.5 * (c - b);

        if m.abs() <= tol || fb.abs() < IV_TOLERANCE_PRICE {
            return Ok(b);
        }

        if e.abs() >= tol && fa.abs() > fb.abs() {
            let s = fb / fa;
            let (p, q) = if (a - c).abs() < f64::EPSILON {
                let p = 2.0 * m * s;
                let q = 1.0 - s;
                (p, q)
            } else {
                let q = fa / fc;
                let r = fb / fc;
                let p = s * (2.0 * m * q * (q - r) - (b - a) * (r - 1.0));
                let q = (q - 1.0) * (r - 1.0) * (s - 1.0);
                (p, q)
            };

            let q = if q > 0.0 { -q } else { q };
            let p = p.abs();

            if 2.0 * p < (3.0 * m * q - (tol * q).abs()).min(e * q.abs()) {
                e = d;
                d = p / q;
            } else {
                d = m;
                e = d;
            }
        } else {
            d = m;
            e = d;
        }

        a = b;
        fa = fb;

        if d.abs() > tol {
            b += d;
        } else {
            b += if m > 0.0 { tol } else { -tol };
        }

        fb = price_diff(b);
    }

    Err(QuantForgeError::ConvergenceFailed(IV_MAX_ITERATIONS))
}

// Batch functions removed - will be reimplemented with full array support

// Helper function for normal PDF
fn normal_pdf(x: f64) -> f64 {
    crate::math::distributions::norm_pdf(x)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_iv_recovery() {
        // Test that we can recover the original volatility
        let original_sigma = 0.25;
        let params = Black76Params::new(100.0, 100.0, 1.0, 0.05, original_sigma);

        // Calculate option price with known volatility
        let call_price = pricing::call_price(&params);

        // Recover implied volatility
        let params_no_sigma = Black76Params::new(100.0, 100.0, 1.0, 0.05, 0.2); // dummy sigma
        let recovered_iv = calculate_iv(call_price, &params_no_sigma, true, None).unwrap();

        // Should recover the original volatility within tolerance
        assert!((recovered_iv - original_sigma).abs() < 0.001);
    }

    #[test]
    fn test_iv_different_strikes() {
        let forward = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let true_sigma = 0.3;

        for strike in [80.0, 90.0, 100.0, 110.0, 120.0] {
            let params = Black76Params::new(forward, strike, time, rate, true_sigma);
            let call_price = pricing::call_price(&params);

            let params_no_sigma = Black76Params::new(forward, strike, time, rate, 0.2);
            let recovered_iv = calculate_iv(call_price, &params_no_sigma, true, None).unwrap();

            assert!((recovered_iv - true_sigma).abs() < 0.001);
        }
    }

    #[test]
    fn test_iv_edge_cases() {
        let params = Black76Params::new(100.0, 100.0, 1.0, 0.05, 0.2);

        // Negative price should error
        let result = calculate_iv(-10.0, &params, true, None);
        assert!(result.is_err());

        // Price below intrinsic value should error
        let intrinsic = params.discount_factor() * (params.forward - params.strike).max(0.0);
        let result = calculate_iv(intrinsic * 0.5, &params, true, None);
        assert!(result.is_err());
    }

    #[test]
    fn test_iv_high_volatility() {
        // Test with high volatility
        let high_sigma = 2.0;
        let params = Black76Params::new(100.0, 100.0, 1.0, 0.05, high_sigma);
        let call_price = pricing::call_price(&params);

        let params_no_sigma = Black76Params::new(100.0, 100.0, 1.0, 0.05, 0.2);
        let recovered_iv = calculate_iv(call_price, &params_no_sigma, true, None).unwrap();

        assert!((recovered_iv - high_sigma).abs() < 0.01);
    }

    // Commented out until batch functions are reimplemented
    // #[test]
    // fn test_iv_batch() {
    //     let forwards = vec![95.0, 100.0, 105.0];
    //     let strike = 100.0;
    //     let time = 1.0;
    //     let rate = 0.05;
    //     let true_sigma = 0.25;
    //
    //     // Calculate prices with known volatility
    //     let prices: Vec<f64> = forwards
    //         .iter()
    //         .map(|&forward| {
    //             let params = Black76Params::new(forward, strike, time, rate, true_sigma);
    //             pricing::call_price(&params)
    //         })
    //         .collect();
    //
    //     let is_calls = vec![true, true, true];
    //
    //     let results = calculate_iv_batch(&prices, &forwards, strike, time, rate, &is_calls);
    //
    //     for result in results {
    //         let iv = result.unwrap();
    //         assert!((iv - true_sigma).abs() < 0.001);
    //     }
    // }
}
