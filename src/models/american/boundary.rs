//! Early exercise boundary calculations for American options

use super::AmericanParams;
use crate::constants::BS2002_H_FACTOR;

/// Calculate the early exercise boundary for American options
///
/// Returns the critical stock price at which early exercise becomes optimal
pub fn exercise_boundary(params: &AmericanParams, is_call: bool) -> f64 {
    if is_call {
        calculate_call_boundary(params)
    } else {
        calculate_put_boundary(params)
    }
}

/// Calculate the early exercise boundary for American call options
fn calculate_call_boundary(params: &AmericanParams) -> f64 {
    // For non-dividend calls, no early exercise
    if params.q == 0.0 {
        return f64::INFINITY;
    }

    let b = params.b();
    let v2 = params.sigma * params.sigma;

    // Calculate beta
    let beta = calculate_beta(params.r, b, v2);

    // Calculate B∞ (asymptotic boundary)
    let b_infinity = beta * params.k / (beta - 1.0);

    // Calculate B0 (immediate exercise boundary)
    let b_zero = if b >= params.r {
        params.k
    } else {
        params.k.max(params.r * params.k / b)
    };

    // Calculate h(T) and the trigger price I
    let h_t = -(b * params.t + BS2002_H_FACTOR * params.sigma * params.t.sqrt());
    b_zero + (b_infinity - b_zero) * (1.0 - h_t.exp())
}

/// Calculate the early exercise boundary for American put options
fn calculate_put_boundary(params: &AmericanParams) -> f64 {
    // Use put-call transformation to get put boundary
    let transformed = AmericanParams {
        s: params.k,
        k: params.s,
        t: params.t,
        r: params.q,
        q: params.r,
        sigma: params.sigma,
    };

    let call_boundary = calculate_call_boundary(&transformed);

    // Transform back to put boundary
    // The put boundary is K^2 / call_boundary
    if call_boundary.is_infinite() {
        0.0
    } else {
        params.k * params.k / call_boundary
    }
}

/// Calculate the beta parameter (same as in pricing module)
fn calculate_beta(r: f64, b: f64, v2: f64) -> f64 {
    let beta = (0.5 - b / v2) + ((b / v2 - 0.5).powi(2) + 2.0 * r / v2).sqrt();
    beta.max(0.5) // Ensure beta >= 0.5 for stability
}

/// Calculate the time-dependent exercise boundary
///
/// This function calculates the optimal exercise boundary as a function of time
#[allow(dead_code)]
pub fn exercise_boundary_at_time(
    params: &AmericanParams,
    time_to_expiry: f64,
    is_call: bool,
) -> f64 {
    let mut adjusted_params = *params;
    adjusted_params.t = time_to_expiry;

    exercise_boundary(&adjusted_params, is_call)
}

/// Check if immediate exercise is optimal
#[allow(dead_code)]
pub fn should_exercise(params: &AmericanParams, is_call: bool) -> bool {
    let boundary = exercise_boundary(params, is_call);

    if is_call {
        params.s >= boundary
    } else {
        params.s <= boundary
    }
}
