//! Implied volatility calculation for American options

use super::{pricing, AmericanParams};
use crate::constants::{IV_MAX_ITERATIONS, IV_MAX_VOL, IV_MIN_VOL, IV_TOLERANCE_PRICE};
use crate::error::QuantForgeError;

/// Calculate implied volatility for American options using bisection method
pub fn calculate_american_iv(
    target_price: f64,
    params: &AmericanParams,
    is_call: bool,
    initial_guess: Option<f64>,
) -> Result<f64, QuantForgeError> {
    // Validate inputs
    if target_price <= 0.0 {
        return Err(QuantForgeError::ValidationError {
            context: "Option price must be positive".into(),
        });
    }

    // Check intrinsic value bounds
    let intrinsic = if is_call {
        (params.s - params.k).max(0.0)
    } else {
        (params.k - params.s).max(0.0)
    };

    if target_price < intrinsic {
        return Err(QuantForgeError::ValidationError {
            context: format!("Option price {target_price} is below intrinsic value {intrinsic}"),
        });
    }

    // For American options, use bisection method as it's more robust
    // than Newton-Raphson due to discontinuities at exercise boundary
    bisection_implied_vol(target_price, params, is_call, initial_guess)
}

/// Bisection method for implied volatility
fn bisection_implied_vol(
    target_price: f64,
    params: &AmericanParams,
    is_call: bool,
    initial_guess: Option<f64>,
) -> Result<f64, QuantForgeError> {
    // Set initial bounds
    let mut vol_low = IV_MIN_VOL;
    let mut vol_high = IV_MAX_VOL;

    // If initial guess provided, use it to narrow the search range
    if let Some(guess) = initial_guess {
        if guess > IV_MIN_VOL && guess < IV_MAX_VOL {
            // Search around the initial guess
            vol_low = (guess * 0.5).max(IV_MIN_VOL);
            vol_high = (guess * 2.0).min(IV_MAX_VOL);
        }
    }

    // Calculate prices at bounds
    let mut params_low = *params;
    params_low.sigma = vol_low;
    let price_low = if is_call {
        pricing::american_call_price(&params_low)
    } else {
        pricing::american_put_price(&params_low)
    };

    if (price_low - target_price).abs() < IV_TOLERANCE_PRICE {
        return Ok(vol_low);
    }

    let mut params_high = *params;
    params_high.sigma = vol_high;
    let price_high = if is_call {
        pricing::american_call_price(&params_high)
    } else {
        pricing::american_put_price(&params_high)
    };

    if (price_high - target_price).abs() < IV_TOLERANCE_PRICE {
        return Ok(vol_high);
    }

    // Check if target price is within bounds
    if price_low > target_price {
        // Even the lowest volatility gives a price too high
        // Try extending the lower bound
        vol_low = IV_MIN_VOL / 10.0;
        params_low.sigma = vol_low;
        let new_price_low = if is_call {
            pricing::american_call_price(&params_low)
        } else {
            pricing::american_put_price(&params_low)
        };

        if new_price_low > target_price {
            return Err(QuantForgeError::ConvergenceError {
                iterations: 0,
                details: "Target price is below achievable range".into(),
            });
        }
    }

    if price_high < target_price {
        // Even the highest volatility gives a price too low
        return Err(QuantForgeError::ConvergenceError {
            iterations: 0,
            details: "Target price is above achievable range".into(),
        });
    }

    // Bisection iteration
    for _ in 0..IV_MAX_ITERATIONS {
        let vol_mid = (vol_low + vol_high) * 0.5;

        let mut params_mid = *params;
        params_mid.sigma = vol_mid;
        let price_mid = if is_call {
            pricing::american_call_price(&params_mid)
        } else {
            pricing::american_put_price(&params_mid)
        };

        // Check convergence
        if (price_mid - target_price).abs() < IV_TOLERANCE_PRICE {
            return Ok(vol_mid);
        }

        // Check if interval is too small
        if (vol_high - vol_low) < IV_MIN_VOL * 0.01 {
            // Return the best estimate
            return Ok(vol_mid);
        }

        // Update bounds
        if price_mid > target_price {
            vol_high = vol_mid;
        } else {
            vol_low = vol_mid;
        }
    }

    // If we get here, we didn't converge
    Err(QuantForgeError::ConvergenceError {
        iterations: IV_MAX_ITERATIONS as u32,
        details: "IV calculation failed to converge".into(),
    })
}
