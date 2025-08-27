//! Helper functions for batch processing with Vec inputs
//!
//! This module provides wrapper functions that convert between Vec and ArrayLike types
//! to enable unified batch processing across the codebase.
//!
//! Functions are organized by model:
//! - Black-Scholes: greeks_batch_vec, implied_volatility_batch_vec, etc.
//! - Black76: b76_greeks_batch_vec, b76_implied_volatility_batch_vec, etc.
//! - Merton: merton_greeks_batch_vec, merton_implied_volatility_batch_vec, etc.
//! - American: american_greeks_batch_vec, american_implied_volatility_batch_vec, etc.

use crate::broadcast::ArrayLike;
use crate::error::QuantForgeError;
use crate::models::GreeksBatch;

/// Convert Vec inputs to ArrayLike and call the batch Greeks function
pub fn greeks_batch_vec(
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    _qs: Vec<f64>,
    sigmas: Vec<f64>,
    is_calls: Vec<bool>,
) -> Result<GreeksBatch, QuantForgeError> {
    // Convert Vec<bool> to Vec<f64> for ArrayLike compatibility
    let is_calls_f64: Vec<f64> = is_calls
        .iter()
        .map(|&c| if c { 1.0 } else { 0.0 })
        .collect();

    crate::models::black_scholes_batch::greeks_batch(
        ArrayLike::Array(&spots),
        ArrayLike::Array(&strikes),
        ArrayLike::Array(&times),
        ArrayLike::Array(&rates),
        ArrayLike::Array(&sigmas),
        ArrayLike::Array(&is_calls_f64),
    )
}

/// Convert Vec inputs to ArrayLike and call the batch implied volatility function
pub fn implied_volatility_batch_vec(
    prices: Vec<f64>,
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    _qs: Vec<f64>,
    is_calls: Vec<bool>,
) -> Result<Vec<f64>, QuantForgeError> {
    // Convert Vec<bool> to Vec<f64> for ArrayLike compatibility
    let is_calls_f64: Vec<f64> = is_calls
        .iter()
        .map(|&c| if c { 1.0 } else { 0.0 })
        .collect();

    crate::models::black_scholes_batch::implied_volatility_batch(
        ArrayLike::Array(&prices),
        ArrayLike::Array(&spots),
        ArrayLike::Array(&strikes),
        ArrayLike::Array(&times),
        ArrayLike::Array(&rates),
        ArrayLike::Array(&is_calls_f64),
    )
}

/// Convert Vec inputs to ArrayLike and call the batch call price function
pub fn call_price_batch_vec(
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    _qs: Vec<f64>,
    sigmas: Vec<f64>,
) -> Result<Vec<f64>, QuantForgeError> {
    crate::models::black_scholes_batch::call_price_batch(
        ArrayLike::Array(&spots),
        ArrayLike::Array(&strikes),
        ArrayLike::Array(&times),
        ArrayLike::Array(&rates),
        ArrayLike::Array(&sigmas),
    )
}

/// Convert Vec inputs to ArrayLike and call the batch put price function
pub fn put_price_batch_vec(
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    _qs: Vec<f64>,
    sigmas: Vec<f64>,
) -> Result<Vec<f64>, QuantForgeError> {
    crate::models::black_scholes_batch::put_price_batch(
        ArrayLike::Array(&spots),
        ArrayLike::Array(&strikes),
        ArrayLike::Array(&times),
        ArrayLike::Array(&rates),
        ArrayLike::Array(&sigmas),
    )
}

// Black76 model helpers
pub fn b76_greeks_batch_vec(
    forwards: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    sigmas: Vec<f64>,
    is_calls: Vec<bool>,
) -> Result<GreeksBatch, QuantForgeError> {
    let is_calls_f64: Vec<f64> = is_calls
        .iter()
        .map(|&c| if c { 1.0 } else { 0.0 })
        .collect();

    crate::models::black76::greeks_batch(
        ArrayLike::Array(&forwards),
        ArrayLike::Array(&strikes),
        ArrayLike::Array(&times),
        ArrayLike::Array(&rates),
        ArrayLike::Array(&sigmas),
        ArrayLike::Array(&is_calls_f64),
    )
}

pub fn b76_implied_volatility_batch_vec(
    prices: Vec<f64>,
    forwards: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    is_calls: Vec<bool>,
) -> Result<Vec<f64>, QuantForgeError> {
    let is_calls_f64: Vec<f64> = is_calls
        .iter()
        .map(|&c| if c { 1.0 } else { 0.0 })
        .collect();

    crate::models::black76::implied_volatility_batch(
        ArrayLike::Array(&prices),
        ArrayLike::Array(&forwards),
        ArrayLike::Array(&strikes),
        ArrayLike::Array(&times),
        ArrayLike::Array(&rates),
        ArrayLike::Array(&is_calls_f64),
    )
}

// Merton model helpers
pub fn merton_greeks_batch_vec(
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    qs: Vec<f64>,
    sigmas: Vec<f64>,
    is_calls: Vec<bool>,
) -> Result<GreeksBatch, QuantForgeError> {
    let is_calls_f64: Vec<f64> = is_calls
        .iter()
        .map(|&c| if c { 1.0 } else { 0.0 })
        .collect();

    crate::models::merton::greeks_batch(
        ArrayLike::Array(&spots),
        ArrayLike::Array(&strikes),
        ArrayLike::Array(&times),
        ArrayLike::Array(&rates),
        ArrayLike::Array(&qs),
        ArrayLike::Array(&sigmas),
        ArrayLike::Array(&is_calls_f64),
    )
}

pub fn merton_implied_volatility_batch_vec(
    prices: Vec<f64>,
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    qs: Vec<f64>,
    is_calls: Vec<bool>,
) -> Result<Vec<f64>, QuantForgeError> {
    let is_calls_f64: Vec<f64> = is_calls
        .iter()
        .map(|&c| if c { 1.0 } else { 0.0 })
        .collect();

    crate::models::merton::implied_volatility_batch(
        ArrayLike::Array(&prices),
        ArrayLike::Array(&spots),
        ArrayLike::Array(&strikes),
        ArrayLike::Array(&times),
        ArrayLike::Array(&rates),
        ArrayLike::Array(&qs),
        ArrayLike::Array(&is_calls_f64),
    )
}

pub fn merton_call_price_batch_vec(
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    qs: Vec<f64>,
    sigmas: Vec<f64>,
) -> Result<Vec<f64>, QuantForgeError> {
    crate::models::merton::call_price_batch(
        ArrayLike::Array(&spots),
        ArrayLike::Array(&strikes),
        ArrayLike::Array(&times),
        ArrayLike::Array(&rates),
        ArrayLike::Array(&qs),
        ArrayLike::Array(&sigmas),
    )
}

pub fn merton_put_price_batch_vec(
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    qs: Vec<f64>,
    sigmas: Vec<f64>,
) -> Result<Vec<f64>, QuantForgeError> {
    crate::models::merton::put_price_batch(
        ArrayLike::Array(&spots),
        ArrayLike::Array(&strikes),
        ArrayLike::Array(&times),
        ArrayLike::Array(&rates),
        ArrayLike::Array(&qs),
        ArrayLike::Array(&sigmas),
    )
}

// American model helpers
pub fn american_greeks_batch_vec(
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    qs: Vec<f64>,
    sigmas: Vec<f64>,
    is_calls: Vec<bool>,
) -> Result<GreeksBatch, QuantForgeError> {
    let is_calls_f64: Vec<f64> = is_calls
        .iter()
        .map(|&c| if c { 1.0 } else { 0.0 })
        .collect();

    crate::models::american::greeks_batch(
        ArrayLike::Array(&spots),
        ArrayLike::Array(&strikes),
        ArrayLike::Array(&times),
        ArrayLike::Array(&rates),
        ArrayLike::Array(&qs),
        ArrayLike::Array(&sigmas),
        ArrayLike::Array(&is_calls_f64),
    )
}

pub fn american_implied_volatility_batch_vec(
    prices: Vec<f64>,
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    qs: Vec<f64>,
    is_calls: Vec<bool>,
) -> Result<Vec<f64>, QuantForgeError> {
    let is_calls_f64: Vec<f64> = is_calls
        .iter()
        .map(|&c| if c { 1.0 } else { 0.0 })
        .collect();

    crate::models::american::implied_volatility_batch(
        ArrayLike::Array(&prices),
        ArrayLike::Array(&spots),
        ArrayLike::Array(&strikes),
        ArrayLike::Array(&times),
        ArrayLike::Array(&rates),
        ArrayLike::Array(&qs),
        ArrayLike::Array(&is_calls_f64),
    )
}

pub fn american_call_price_batch_vec(
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    qs: Vec<f64>,
    sigmas: Vec<f64>,
) -> Result<Vec<f64>, QuantForgeError> {
    crate::models::american::call_price_batch(
        ArrayLike::Array(&spots),
        ArrayLike::Array(&strikes),
        ArrayLike::Array(&times),
        ArrayLike::Array(&rates),
        ArrayLike::Array(&qs),
        ArrayLike::Array(&sigmas),
    )
}

pub fn american_put_price_batch_vec(
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    qs: Vec<f64>,
    sigmas: Vec<f64>,
) -> Result<Vec<f64>, QuantForgeError> {
    crate::models::american::put_price_batch(
        ArrayLike::Array(&spots),
        ArrayLike::Array(&strikes),
        ArrayLike::Array(&times),
        ArrayLike::Array(&rates),
        ArrayLike::Array(&qs),
        ArrayLike::Array(&sigmas),
    )
}
