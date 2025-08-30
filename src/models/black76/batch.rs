//! Batch processing functions for Black76 model with broadcasting support

use super::processor::{Black76CallProcessor, Black76PutProcessor};
use super::{calculate_greeks, Black76Params};
use crate::broadcast::{ArrayLike, BroadcastIterator};
use crate::error::QuantForgeError;
use crate::models::black76::implied_volatility::calculate_iv;
use crate::models::{Greeks, GreeksBatch};
use crate::optimization::{ParallelStrategy, ProcessingMode};
use crate::traits::BatchProcessor;

/// Batch calculate call option prices with broadcasting support
pub fn call_price_batch(
    forwards: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    sigmas: ArrayLike,
) -> Result<Vec<f64>, QuantForgeError> {
    let inputs = vec![forwards, strikes, times, rates, sigmas];
    let iter = BroadcastIterator::new(inputs)?;
    let size = iter.size_hint().0;

    // Select processing strategy based on data size
    let strategy = ParallelStrategy::select(size);
    let processor = Black76CallProcessor;

    let results = match strategy.mode() {
        ProcessingMode::Sequential => {
            // Use compute_with for sequential processing (zero-copy)
            iter.compute_with(|vals| {
                compute_single_call(vals[0], vals[1], vals[2], vals[3], vals[4], &processor)
            })
        }
        _ => {
            // Use compute_parallel_with for parallel processing (thread-local buffering)
            iter.compute_parallel_with(
                |vals| compute_single_call(vals[0], vals[1], vals[2], vals[3], vals[4], &processor),
                strategy.chunk_size(),
            )
        }
    };

    Ok(results)
}

#[inline(always)]
fn compute_single_call(
    f: f64,
    k: f64,
    t: f64,
    r: f64,
    sigma: f64,
    processor: &Black76CallProcessor,
) -> f64 {
    if f <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        f64::NAN
    } else {
        let params = processor.create_params(f, k, t, r, sigma);
        processor.process_single(&params)
    }
}

/// Batch calculate put option prices with broadcasting support
pub fn put_price_batch(
    forwards: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    sigmas: ArrayLike,
) -> Result<Vec<f64>, QuantForgeError> {
    let inputs = vec![forwards, strikes, times, rates, sigmas];
    let iter = BroadcastIterator::new(inputs)?;
    let size = iter.size_hint().0;

    // Select processing strategy based on data size
    let strategy = ParallelStrategy::select(size);
    let processor = Black76PutProcessor;

    let results = match strategy.mode() {
        ProcessingMode::Sequential => {
            // Use compute_with for sequential processing (zero-copy)
            iter.compute_with(|vals| {
                compute_single_put(vals[0], vals[1], vals[2], vals[3], vals[4], &processor)
            })
        }
        _ => {
            // Use compute_parallel_with for parallel processing (thread-local buffering)
            iter.compute_parallel_with(
                |vals| compute_single_put(vals[0], vals[1], vals[2], vals[3], vals[4], &processor),
                strategy.chunk_size(),
            )
        }
    };

    Ok(results)
}

#[inline(always)]
fn compute_single_put(
    f: f64,
    k: f64,
    t: f64,
    r: f64,
    sigma: f64,
    processor: &Black76PutProcessor,
) -> f64 {
    if f <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        f64::NAN
    } else {
        let params = processor.create_params(f, k, t, r, sigma);
        processor.process_single(&params)
    }
}

/// Batch calculate implied volatilities with broadcasting support
pub fn implied_volatility_batch(
    prices: ArrayLike,
    forwards: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    is_calls: ArrayLike,
) -> Result<Vec<f64>, QuantForgeError> {
    let inputs = vec![prices, forwards, strikes, times, rates, is_calls];
    let iter = BroadcastIterator::new(inputs)?;
    let size = iter.size_hint().0;

    // Select processing strategy based on data size
    let strategy = ParallelStrategy::select(size);

    let results = match strategy.mode() {
        ProcessingMode::Sequential => {
            // Use compute_with for sequential processing (zero-copy)
            iter.compute_with(|vals| {
                compute_single_iv(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5])
            })
        }
        _ => {
            // Use compute_parallel_with for parallel processing (thread-local buffering)
            iter.compute_parallel_with(
                |vals| compute_single_iv(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]),
                strategy.chunk_size(),
            )
        }
    };

    Ok(results)
}

#[inline(always)]
fn compute_single_iv(price: f64, f: f64, k: f64, t: f64, r: f64, is_call_val: f64) -> f64 {
    if price <= 0.0 || f <= 0.0 || k <= 0.0 || t <= 0.0 {
        f64::NAN
    } else {
        let params = Black76Params::new(f, k, t, r, 0.2);
        match calculate_iv(price, &params, is_call_val > 0.5, None) {
            Ok(sigma) => sigma,
            Err(_) => f64::NAN,
        }
    }
}

/// Batch calculate Greeks with broadcasting support
pub fn greeks_batch(
    forwards: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    sigmas: ArrayLike,
    is_calls: ArrayLike,
) -> Result<GreeksBatch, QuantForgeError> {
    let inputs = vec![forwards, strikes, times, rates, sigmas, is_calls];
    let iter = BroadcastIterator::new(inputs)?;
    let size = iter.size_hint().0;

    // Select processing strategy based on data size
    let strategy = ParallelStrategy::select(size);

    let greeks_list: Vec<Greeks> = match strategy.mode() {
        ProcessingMode::Sequential => {
            // Use compute_with for sequential processing (zero-copy)
            iter.compute_with(|vals| {
                compute_single_greeks(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5])
            })
        }
        _ => {
            // Use compute_parallel_with for parallel processing (thread-local buffering)
            iter.compute_parallel_with(
                |vals| compute_single_greeks(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]),
                strategy.chunk_size(),
            )
        }
    };

    // Convert list of Greeks to GreeksBatch
    Ok(GreeksBatch {
        delta: greeks_list.iter().map(|g| g.delta).collect(),
        gamma: greeks_list.iter().map(|g| g.gamma).collect(),
        vega: greeks_list.iter().map(|g| g.vega).collect(),
        theta: greeks_list.iter().map(|g| g.theta).collect(),
        rho: greeks_list.iter().map(|g| g.rho).collect(),
        dividend_rho: vec![0.0; size], // Black76 doesn't use dividends
    })
}

#[inline(always)]
fn compute_single_greeks(f: f64, k: f64, t: f64, r: f64, sigma: f64, is_call_val: f64) -> Greeks {
    if f <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        Greeks {
            delta: f64::NAN,
            gamma: f64::NAN,
            vega: f64::NAN,
            theta: f64::NAN,
            rho: f64::NAN,
        }
    } else {
        let params = Black76Params::new(f, k, t, r, sigma);
        calculate_greeks(&params, is_call_val > 0.5)
    }
}

// GreeksBatch is now imported from greeks_batch module

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::NUMERICAL_TOLERANCE;
    use crate::models::black76::call_price;

    #[test]
    fn test_call_price_batch() {
        let forwards = ArrayLike::Array(&[90.0, 100.0, 110.0]);
        let strikes = ArrayLike::Scalar(100.0);
        let times = ArrayLike::Scalar(1.0);
        let rates = ArrayLike::Scalar(0.05);
        let sigmas = ArrayLike::Scalar(0.2);

        let prices = call_price_batch(forwards, strikes, times, rates, sigmas).unwrap();

        assert_eq!(prices.len(), 3);
        assert!(prices.iter().all(|&p| p > 0.0 && p.is_finite()));

        // Check individual values match
        for (i, &forward) in [90.0, 100.0, 110.0].iter().enumerate() {
            let params = Black76Params::new(forward, 100.0, 1.0, 0.05, 0.2);
            let expected = call_price(&params);
            assert!((prices[i] - expected).abs() < NUMERICAL_TOLERANCE);
        }
    }

    #[test]
    fn test_broadcasting() {
        let forwards = ArrayLike::Array(&[100.0, 105.0]);
        let strikes = ArrayLike::Scalar(100.0);
        let times = ArrayLike::Scalar(1.0);
        let rates = ArrayLike::Scalar(0.05);
        let sigmas = ArrayLike::Scalar(0.2);

        let prices = call_price_batch(forwards, strikes, times, rates, sigmas).unwrap();
        assert_eq!(prices.len(), 2);
    }
}
