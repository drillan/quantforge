//! Greeks calculation for American options using numerical differentiation

use crate::error::QuantForgeResult;
use crate::traits::Greeks;
use super::pricing::{american_call_price, american_put_price, AmericanParams};

/// Calculate Greeks for American options using finite difference methods
pub fn calculate_american_greeks(params: &AmericanParams, is_call: bool) -> QuantForgeResult<Greeks> {
    // Choose price function based on option type
    let price_fn = if is_call {
        american_call_price
    } else {
        american_put_price
    };

    // Calculate base price
    let base_price = price_fn(params)?;

    // Calculate Delta using central difference
    let delta = calculate_delta(params, price_fn)?;

    // Calculate Gamma using central difference
    let gamma = calculate_gamma(params, price_fn)?;

    // Calculate Vega using central difference
    let vega = calculate_vega(params, price_fn)?;

    // Calculate Theta using forward difference (negative time direction)
    let theta = calculate_theta(params, price_fn, base_price)?;

    // Calculate Rho using central difference
    let rho = calculate_rho(params, price_fn)?;

    // Calculate Dividend Rho using central difference
    let dividend_rho = calculate_dividend_rho(params, price_fn)?;

    Ok(Greeks {
        delta,
        gamma,
        vega,
        theta,
        rho,
        dividend_rho: Some(dividend_rho),
    })
}

/// Calculate Delta using central difference
fn calculate_delta(
    params: &AmericanParams,
    price_fn: fn(&AmericanParams) -> QuantForgeResult<f64>,
) -> QuantForgeResult<f64> {
    let h = params.s * 0.001; // 0.1% of spot price
    
    let mut params_up = *params;
    params_up.s = params.s + h;
    let price_up = price_fn(&params_up)?;

    let mut params_down = *params;
    params_down.s = params.s - h;
    let price_down = price_fn(&params_down)?;

    Ok((price_up - price_down) / (2.0 * h))
}

/// Calculate Gamma using central difference on Delta
fn calculate_gamma(
    params: &AmericanParams,
    price_fn: fn(&AmericanParams) -> QuantForgeResult<f64>,
) -> QuantForgeResult<f64> {
    let h = params.s * 0.001; // 0.1% of spot price
    
    let base_price = price_fn(params)?;

    let mut params_up = *params;
    params_up.s = params.s + h;
    let price_up = price_fn(&params_up)?;

    let mut params_down = *params;
    params_down.s = params.s - h;
    let price_down = price_fn(&params_down)?;

    Ok((price_up - 2.0 * base_price + price_down) / (h * h))
}

/// Calculate Vega using central difference
fn calculate_vega(
    params: &AmericanParams,
    price_fn: fn(&AmericanParams) -> QuantForgeResult<f64>,
) -> QuantForgeResult<f64> {
    let h = 0.001; // 0.1% volatility change
    
    let mut params_up = *params;
    params_up.sigma = params.sigma + h;
    let price_up = price_fn(&params_up)?;

    let mut params_down = *params;
    params_down.sigma = (params.sigma - h).max(0.001); // Ensure positive volatility
    let price_down = price_fn(&params_down)?;

    // Return vega per 1% change (multiply by 0.01)
    Ok((price_up - price_down) / (2.0 * h) * 0.01)
}

/// Calculate Theta using forward difference (time decay)
fn calculate_theta(
    params: &AmericanParams,
    price_fn: fn(&AmericanParams) -> QuantForgeResult<f64>,
    base_price: f64,
) -> QuantForgeResult<f64> {
    let h: f64 = 1.0 / 365.0; // One day
    
    // For very short time to maturity, use smaller step
    let h_actual = h.min(params.t * 0.01);
    
    let mut params_forward = *params;
    params_forward.t = (params.t - h_actual).max(0.0);
    let price_forward = price_fn(&params_forward)?;

    // Return theta per day (negative because time decay)
    Ok(-(base_price - price_forward) / h_actual / 365.0)
}

/// Calculate Rho using central difference
fn calculate_rho(
    params: &AmericanParams,
    price_fn: fn(&AmericanParams) -> QuantForgeResult<f64>,
) -> QuantForgeResult<f64> {
    let h = 0.0001; // 1 basis point
    
    let mut params_up = *params;
    params_up.r = params.r + h;
    let price_up = price_fn(&params_up)?;

    let mut params_down = *params;
    params_down.r = params.r - h;
    let price_down = price_fn(&params_down)?;

    // Return rho per 1% change (multiply by 0.01)
    Ok((price_up - price_down) / (2.0 * h) * 0.01)
}

/// Calculate Dividend Rho using central difference
fn calculate_dividend_rho(
    params: &AmericanParams,
    price_fn: fn(&AmericanParams) -> QuantForgeResult<f64>,
) -> QuantForgeResult<f64> {
    let h = 0.0001; // 1 basis point
    
    let mut params_up = *params;
    params_up.q = params.q + h;
    let price_up = price_fn(&params_up)?;

    let mut params_down = *params;
    params_down.q = (params.q - h).max(0.0); // Ensure non-negative dividend
    let price_down = price_fn(&params_down)?;

    // Return dividend rho per 1% change (multiply by 0.01)
    Ok((price_up - price_down) / (2.0 * h) * 0.01)
}