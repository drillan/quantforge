//! Batch processing for American options with parallel processing

use super::{pricing, AmericanParams};
use rayon::prelude::*;

/// Batch calculate call prices with parallel processing
pub fn call_price_batch(spots: &[f64], k: f64, t: f64, r: f64, q: f64, sigma: f64) -> Vec<f64> {
    // Use parallel processing for large batches
    if spots.len() > 1000 {
        spots
            .par_iter()
            .map(|&s| {
                let params = AmericanParams {
                    s,
                    k,
                    t,
                    r,
                    q,
                    sigma,
                };
                pricing::american_call_price(&params)
            })
            .collect()
    } else {
        // For smaller batches, use sequential processing
        spots
            .iter()
            .map(|&s| {
                let params = AmericanParams {
                    s,
                    k,
                    t,
                    r,
                    q,
                    sigma,
                };
                pricing::american_call_price(&params)
            })
            .collect()
    }
}

/// Batch calculate put prices with parallel processing
pub fn put_price_batch(spots: &[f64], k: f64, t: f64, r: f64, q: f64, sigma: f64) -> Vec<f64> {
    // Use parallel processing for large batches
    if spots.len() > 1000 {
        spots
            .par_iter()
            .map(|&s| {
                let params = AmericanParams {
                    s,
                    k,
                    t,
                    r,
                    q,
                    sigma,
                };
                pricing::american_put_price(&params)
            })
            .collect()
    } else {
        // For smaller batches, use sequential processing
        spots
            .iter()
            .map(|&s| {
                let params = AmericanParams {
                    s,
                    k,
                    t,
                    r,
                    q,
                    sigma,
                };
                pricing::american_put_price(&params)
            })
            .collect()
    }
}

/// Parallel batch calculation for multiple parameter sets
pub fn price_batch_parallel(params_list: &[AmericanParams], is_call: bool) -> Vec<f64> {
    params_list
        .par_iter()
        .map(|params| {
            if is_call {
                pricing::american_call_price(params)
            } else {
                pricing::american_put_price(params)
            }
        })
        .collect()
}
