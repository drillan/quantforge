//! Greeks calculations for American options

use super::{pricing, AmericanParams};
use crate::constants::NUMERICAL_TOLERANCE;
use crate::models::Greeks;

/// Calculate all Greeks for American options
pub fn calculate_american_greeks(params: &AmericanParams, is_call: bool) -> Greeks {
    // Use finite difference method for American Greeks
    // This is more accurate than analytical approximations for American options

    let _base_price = if is_call {
        pricing::american_call_price(params)
    } else {
        pricing::american_put_price(params)
    };

    // Delta: ∂V/∂S
    let delta = calculate_delta(params, is_call);

    // Gamma: ∂²V/∂S²
    let gamma = calculate_gamma(params, is_call);

    // Vega: ∂V/∂σ
    let vega = calculate_vega(params, is_call);

    // Theta: -∂V/∂T (negative because we measure time decay)
    let theta = calculate_theta(params, is_call);

    // Rho: ∂V/∂r
    let rho = calculate_rho(params, is_call);

    Greeks {
        delta,
        gamma,
        vega,
        theta,
        rho,
    }
}

/// Calculate Delta using central finite difference
fn calculate_delta(params: &AmericanParams, is_call: bool) -> f64 {
    let h = params.s * 0.001; // 0.1% bump

    let params_up = AmericanParams {
        s: params.s + h,
        ..*params
    };

    let params_down = AmericanParams {
        s: params.s - h,
        ..*params
    };

    let price_up = if is_call {
        pricing::american_call_price(&params_up)
    } else {
        pricing::american_put_price(&params_up)
    };

    let price_down = if is_call {
        pricing::american_call_price(&params_down)
    } else {
        pricing::american_put_price(&params_down)
    };

    (price_up - price_down) / (2.0 * h)
}

/// Calculate Gamma using central finite difference
fn calculate_gamma(params: &AmericanParams, is_call: bool) -> f64 {
    let h = params.s * 0.001; // 0.1% bump

    let params_up = AmericanParams {
        s: params.s + h,
        ..*params
    };

    let params_center = *params;

    let params_down = AmericanParams {
        s: params.s - h,
        ..*params
    };

    let price_up = if is_call {
        pricing::american_call_price(&params_up)
    } else {
        pricing::american_put_price(&params_up)
    };

    let price_center = if is_call {
        pricing::american_call_price(&params_center)
    } else {
        pricing::american_put_price(&params_center)
    };

    let price_down = if is_call {
        pricing::american_call_price(&params_down)
    } else {
        pricing::american_put_price(&params_down)
    };

    (price_up - 2.0 * price_center + price_down) / (h * h)
}

/// Calculate Vega using central finite difference
fn calculate_vega(params: &AmericanParams, is_call: bool) -> f64 {
    let h = 0.001; // 0.1% absolute volatility bump

    let params_up = AmericanParams {
        sigma: params.sigma + h,
        ..*params
    };

    let params_down = AmericanParams {
        sigma: (params.sigma - h).max(0.001), // Keep positive
        ..*params
    };

    let price_up = if is_call {
        pricing::american_call_price(&params_up)
    } else {
        pricing::american_put_price(&params_up)
    };

    let price_down = if is_call {
        pricing::american_call_price(&params_down)
    } else {
        pricing::american_put_price(&params_down)
    };

    // Return vega per 1% change (multiply by 0.01)
    (price_up - price_down) / (2.0 * h) * 0.01
}

/// Calculate Theta using forward finite difference
fn calculate_theta(params: &AmericanParams, is_call: bool) -> f64 {
    // For theta, we use a small time bump
    let h = 1.0 / 365.0; // One day

    // Don't go negative in time
    if params.t < h {
        // Near expiry, use smaller bump
        let small_h = params.t * 0.01;
        if small_h < NUMERICAL_TOLERANCE {
            return 0.0; // At expiry
        }

        let params_future = AmericanParams {
            t: params.t - small_h,
            ..*params
        };

        let price_now = if is_call {
            pricing::american_call_price(params)
        } else {
            pricing::american_put_price(params)
        };

        let price_future = if is_call {
            pricing::american_call_price(&params_future)
        } else {
            pricing::american_put_price(&params_future)
        };

        // Theta = -dV/dT where T is time to maturity
        // As time passes, T decreases, so we compute (V(T) - V(T-h))/h
        // This gives us -dV/dT (negative because option loses value as time passes)
        return -(price_now - price_future) / small_h / 365.0;
    }

    let params_future = AmericanParams {
        t: params.t - h,
        ..*params
    };

    let price_now = if is_call {
        pricing::american_call_price(params)
    } else {
        pricing::american_put_price(params)
    };

    let price_future = if is_call {
        pricing::american_call_price(&params_future)
    } else {
        pricing::american_put_price(&params_future)
    };

    // Theta = -dV/dT where T is time to maturity
    // Return daily theta (negative for time decay)
    -(price_now - price_future) / h / 365.0
}

/// Calculate Rho using central finite difference
fn calculate_rho(params: &AmericanParams, is_call: bool) -> f64 {
    let h = 0.0001; // 1 basis point

    let params_up = AmericanParams {
        r: params.r + h,
        ..*params
    };

    let params_down = AmericanParams {
        r: params.r - h,
        ..*params
    };

    let price_up = if is_call {
        pricing::american_call_price(&params_up)
    } else {
        pricing::american_put_price(&params_up)
    };

    let price_down = if is_call {
        pricing::american_call_price(&params_down)
    } else {
        pricing::american_put_price(&params_down)
    };

    // Return rho per 1% change
    (price_up - price_down) / (2.0 * h) * 0.01
}
