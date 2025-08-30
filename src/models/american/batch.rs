//! Batch processing functions for American options with broadcasting support

use super::processor::{AmericanCallProcessor, AmericanPutProcessor};
use super::{boundary, greeks::calculate_american_greeks, AmericanModel, AmericanParams};
use crate::broadcast::{ArrayLike, BroadcastIterator};
use crate::error::QuantForgeError;
use crate::models::{Greeks, GreeksBatch, PricingModel};
use crate::optimization::{ParallelStrategy, ProcessingMode};
use crate::traits::BatchProcessorWithDividend;

// GreeksBatch is now imported from greeks_batch module

/// Batch calculate American call option prices with broadcasting support
pub fn call_price_batch(
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    qs: ArrayLike,
    sigmas: ArrayLike,
) -> Result<Vec<f64>, QuantForgeError> {
    let inputs = vec![spots, strikes, times, rates, qs, sigmas];
    let iter = BroadcastIterator::new(inputs)?;
    let size = iter.size_hint().0;

    // Select processing strategy based on data size
    let strategy = ParallelStrategy::select(size);
    let processor = AmericanCallProcessor;

    let results = match strategy.mode() {
        ProcessingMode::Sequential => {
            // Use compute_with for sequential processing (zero-copy)
            iter.compute_with(|vals| {
                compute_single_american_call(
                    vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], &processor,
                )
            })
        }
        _ => {
            // Use compute_parallel_with for parallel processing (thread-local buffering)
            iter.compute_parallel_with(
                |vals| {
                    compute_single_american_call(
                        vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], &processor,
                    )
                },
                strategy.chunk_size(),
            )
        }
    };

    Ok(results)
}

#[inline(always)]
fn compute_single_american_call(
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    processor: &AmericanCallProcessor,
) -> f64 {
    if s <= 0.0 || k <= 0.0 || t < 0.0 || sigma <= 0.0 {
        f64::NAN
    } else if q > r {
        // Dividend arbitrage check
        f64::NAN
    } else {
        let params = processor.create_params_with_dividend(s, k, t, r, q, sigma);
        processor.process_single_with_dividend(&params)
    }
}

/// Batch calculate American put option prices with broadcasting support
pub fn put_price_batch(
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    qs: ArrayLike,
    sigmas: ArrayLike,
) -> Result<Vec<f64>, QuantForgeError> {
    let inputs = vec![spots, strikes, times, rates, qs, sigmas];
    let iter = BroadcastIterator::new(inputs)?;
    let size = iter.size_hint().0;

    // Select processing strategy based on data size
    let strategy = ParallelStrategy::select(size);
    let processor = AmericanPutProcessor;

    let results = match strategy.mode() {
        ProcessingMode::Sequential => {
            // Use compute_with for sequential processing (zero-copy)
            iter.compute_with(|vals| {
                compute_single_american_put(
                    vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], &processor,
                )
            })
        }
        _ => {
            // Use compute_parallel_with for parallel processing (thread-local buffering)
            iter.compute_parallel_with(
                |vals| {
                    compute_single_american_put(
                        vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], &processor,
                    )
                },
                strategy.chunk_size(),
            )
        }
    };

    Ok(results)
}

#[inline(always)]
fn compute_single_american_put(
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    processor: &AmericanPutProcessor,
) -> f64 {
    if s <= 0.0 || k <= 0.0 || t < 0.0 || sigma <= 0.0 {
        f64::NAN
    } else if q > r {
        // Dividend arbitrage check
        f64::NAN
    } else {
        let params = processor.create_params_with_dividend(s, k, t, r, q, sigma);
        processor.process_single_with_dividend(&params)
    }
}

/// Batch calculate implied volatilities for American options with broadcasting support
pub fn implied_volatility_batch(
    prices: ArrayLike,
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    qs: ArrayLike,
    is_calls: ArrayLike,
) -> Result<Vec<f64>, QuantForgeError> {
    let inputs = vec![prices, spots, strikes, times, rates, qs, is_calls];
    let iter = BroadcastIterator::new(inputs)?;
    let size = iter.size_hint().0;

    // Select processing strategy based on data size
    let strategy = ParallelStrategy::select(size);

    let results = match strategy.mode() {
        ProcessingMode::Sequential => {
            // Use compute_with for sequential processing (zero-copy)
            iter.compute_with(|vals| {
                compute_single_american_iv(
                    vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], vals[6],
                )
            })
        }
        _ => {
            // Use compute_parallel_with for parallel processing (thread-local buffering)
            iter.compute_parallel_with(
                |vals| {
                    compute_single_american_iv(
                        vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], vals[6],
                    )
                },
                strategy.chunk_size(),
            )
        }
    };

    Ok(results)
}

#[inline(always)]
fn compute_single_american_iv(
    price: f64,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    is_call_val: f64,
) -> f64 {
    if price <= 0.0 || s <= 0.0 || k <= 0.0 || t < 0.0 {
        f64::NAN
    } else if q > r {
        // Dividend arbitrage check
        f64::NAN
    } else {
        let params = AmericanParams::new_unchecked(s, k, t, r, q, 0.2);
        match AmericanModel::implied_volatility(price, &params, is_call_val > 0.5, None) {
            Ok(sigma) => sigma,
            Err(_) => f64::NAN,
        }
    }
}

/// Batch calculate Greeks for American options with broadcasting support
pub fn greeks_batch(
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    qs: ArrayLike,
    sigmas: ArrayLike,
    is_calls: ArrayLike,
) -> Result<GreeksBatch, QuantForgeError> {
    let inputs = vec![spots, strikes, times, rates, qs, sigmas, is_calls];
    let iter = BroadcastIterator::new(inputs)?;
    let size = iter.size_hint().0;

    // Select processing strategy based on data size
    let strategy = ParallelStrategy::select(size);

    let results: Vec<Greeks> = match strategy.mode() {
        ProcessingMode::Sequential => {
            // Use compute_with for sequential processing (zero-copy)
            iter.compute_with(|vals| {
                compute_single_american_greeks(
                    vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], vals[6],
                )
            })
        }
        _ => {
            // Use compute_parallel_with for parallel processing (thread-local buffering)
            iter.compute_parallel_with(
                |vals| {
                    compute_single_american_greeks(
                        vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], vals[6],
                    )
                },
                strategy.chunk_size(),
            )
        }
    };

    // Unpack into separate vectors
    let mut delta = Vec::with_capacity(size);
    let mut gamma = Vec::with_capacity(size);
    let mut vega = Vec::with_capacity(size);
    let mut theta = Vec::with_capacity(size);
    let mut rho = Vec::with_capacity(size);
    let mut dividend_rho = Vec::with_capacity(size);

    for greeks in results {
        delta.push(greeks.delta);
        gamma.push(greeks.gamma);
        vega.push(greeks.vega);
        theta.push(greeks.theta);
        rho.push(greeks.rho);
        // For American options, dividend_rho is the sensitivity to dividend yield
        // We'll calculate it as negative delta (approximation)
        dividend_rho.push(-greeks.delta);
    }

    Ok(GreeksBatch {
        delta,
        gamma,
        vega,
        theta,
        rho,
        dividend_rho,
    })
}

#[inline(always)]
fn compute_single_american_greeks(
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    is_call_val: f64,
) -> Greeks {
    if s <= 0.0 || k <= 0.0 || t < 0.0 || sigma <= 0.0 {
        Greeks {
            delta: f64::NAN,
            gamma: f64::NAN,
            vega: f64::NAN,
            theta: f64::NAN,
            rho: f64::NAN,
        }
    } else if q > r {
        // Dividend arbitrage check
        Greeks {
            delta: f64::NAN,
            gamma: f64::NAN,
            vega: f64::NAN,
            theta: f64::NAN,
            rho: f64::NAN,
        }
    } else {
        let params = AmericanParams::new_unchecked(s, k, t, r, q, sigma);
        calculate_american_greeks(&params, is_call_val > 0.5)
    }
}

/// Batch calculate exercise boundaries for American options with broadcasting support
pub fn exercise_boundary_batch(
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    qs: ArrayLike,
    sigmas: ArrayLike,
    is_calls: ArrayLike,
) -> Result<Vec<f64>, QuantForgeError> {
    let inputs = vec![spots, strikes, times, rates, qs, sigmas, is_calls];
    let iter = BroadcastIterator::new(inputs)?;
    let size = iter.size_hint().0;

    // Select processing strategy based on data size
    let strategy = ParallelStrategy::select(size);

    let results = match strategy.mode() {
        ProcessingMode::Sequential => {
            // Use compute_with for sequential processing (zero-copy)
            iter.compute_with(|vals| {
                compute_single_boundary(
                    vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], vals[6],
                )
            })
        }
        _ => {
            // Use compute_parallel_with for parallel processing (thread-local buffering)
            iter.compute_parallel_with(
                |vals| {
                    compute_single_boundary(
                        vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], vals[6],
                    )
                },
                strategy.chunk_size(),
            )
        }
    };

    Ok(results)
}

#[inline(always)]
fn compute_single_boundary(
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    is_call_val: f64,
) -> f64 {
    if s <= 0.0 || k <= 0.0 || t < 0.0 || sigma <= 0.0 {
        f64::NAN
    } else if q > r {
        // Dividend arbitrage check
        f64::NAN
    } else {
        let params = AmericanParams::new_unchecked(s, k, t, r, q, sigma);
        boundary::exercise_boundary(&params, is_call_val > 0.5)
    }
}
