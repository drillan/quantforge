//! Early exercise boundary calculation for American options

use super::pricing::AmericanParams;
use crate::constants::BS2002_H_FACTOR;
use crate::error::QuantForgeResult;

/// Calculate the early exercise boundary for American options
///
/// Returns the critical stock price at which early exercise becomes optimal
pub fn calculate_exercise_boundary(
    params: &AmericanParams,
    is_call: bool,
) -> QuantForgeResult<f64> {
    if is_call {
        calculate_call_boundary(params)
    } else {
        calculate_put_boundary(params)
    }
}

/// Calculate the early exercise boundary for American call options
fn calculate_call_boundary(params: &AmericanParams) -> QuantForgeResult<f64> {
    // For non-dividend paying calls, boundary is infinity (never exercise early)
    if params.q <= 0.0 {
        return Ok(f64::INFINITY);
    }

    // If time is very small, boundary approaches strike
    if params.t < 1e-10 {
        return Ok(params.k);
    }

    let b = params.r - params.q;
    let v2 = params.sigma * params.sigma;

    // Calculate beta
    let beta = calculate_beta(params.r, b, v2);

    // Calculate B∞ and B0
    let b_infinity = beta * params.k / (beta - 1.0);
    let b_zero = if b >= params.r {
        params.k
    } else {
        params.k.max(params.r * params.k / b)
    };

    // Calculate h(T) and the trigger price
    let h_t = -(b * params.t + BS2002_H_FACTOR * params.sigma * params.t.sqrt());
    // Use exp_m1 for numerical stability: 1 - exp(h_t) = -exp_m1(h_t)
    let boundary = b_zero + (b_infinity - b_zero) * (-h_t.exp_m1());

    Ok(boundary)
}

/// Calculate the early exercise boundary for American put options
fn calculate_put_boundary(params: &AmericanParams) -> QuantForgeResult<f64> {
    // For puts, we use the put-call transformation
    // The boundary for a put is found by transforming the call boundary

    // If time is very small, boundary approaches strike
    if params.t < 1e-10 {
        return Ok(params.k);
    }

    // Transform parameters for put boundary calculation
    let transformed = AmericanParams {
        s: params.k, // Swap S and K
        k: params.s,
        t: params.t,
        r: params.q, // Swap r and q
        q: params.r,
        sigma: params.sigma,
    };

    // Calculate boundary for transformed problem
    let b = transformed.r - transformed.q;
    let v2 = transformed.sigma * transformed.sigma;

    // Calculate beta for transformed problem
    let beta = calculate_beta(transformed.r, b, v2);

    // Calculate B∞ and B0 for transformed problem
    let b_infinity = beta * transformed.k / (beta - 1.0);
    let b_zero = if b >= transformed.r {
        transformed.k
    } else {
        transformed.k.max(transformed.r * transformed.k / b)
    };

    // Calculate h(T) and the trigger price for transformed problem
    let h_t = -(b * transformed.t + BS2002_H_FACTOR * transformed.sigma * transformed.t.sqrt());
    // Use exp_m1 for numerical stability: 1 - exp(h_t) = -exp_m1(h_t)
    let transformed_boundary = b_zero + (b_infinity - b_zero) * (-h_t.exp_m1());

    // Transform back to get put boundary
    // For a put, the boundary is typically expressed as the critical stock price
    // below which early exercise is optimal
    // Check for numerical stability
    if transformed_boundary <= 0.0
        || transformed_boundary.is_nan()
        || transformed_boundary.is_infinite()
    {
        return Ok(params.k); // Return strike as safe default
    }

    let ratio = params.k * params.k / transformed_boundary;
    if ratio.is_nan() || ratio.is_infinite() || ratio < 0.0 {
        return Ok(params.k); // Return strike as safe default
    }

    Ok(ratio)
}

/// Calculate the beta parameter (same as in pricing module)
fn calculate_beta(r: f64, b: f64, v2: f64) -> f64 {
    let beta = (0.5 - b / v2) + ((b / v2 - 0.5).powi(2) + 2.0 * r / v2).sqrt();
    beta.max(0.5) // Use BS2002_BETA_MIN = 0.5
}

/// Calculate time-dependent exercise boundary using iterative method
///
/// This function calculates the exercise boundary at a specific time point
/// using Newton-Raphson iteration
pub fn calculate_boundary_at_time(
    params: &AmericanParams,
    target_time: f64,
    is_call: bool,
) -> QuantForgeResult<f64> {
    // Validate inputs
    if target_time <= 0.0 || target_time > params.t {
        return Ok(if is_call { f64::INFINITY } else { 0.0 });
    }

    // Create params for the target time
    let mut time_params = *params;
    time_params.t = target_time;

    // Use the simplified boundary calculation
    calculate_exercise_boundary(&time_params, is_call)
}

/// Calculate the exercise boundary curve over multiple time points
///
/// Returns a vector of (time, boundary_price) pairs
pub fn calculate_boundary_curve(
    params: &AmericanParams,
    num_points: usize,
    is_call: bool,
) -> QuantForgeResult<Vec<(f64, f64)>> {
    let mut curve = Vec::with_capacity(num_points);

    for i in 0..num_points {
        let t = params.t * (i as f64 + 1.0) / num_points as f64;
        let boundary = calculate_boundary_at_time(params, t, is_call)?;
        curve.push((t, boundary));
    }

    Ok(curve)
}
