//! Batch processing functions for Merton model with broadcasting support

use super::processor::{MertonCallProcessor, MertonPutProcessor};
use super::{MertonModel, MertonParams};
use crate::broadcast::{ArrayLike, BroadcastIterator};
use crate::error::QuantForgeError;
use crate::models::merton::{greeks::calculate_merton_greeks, MertonGreeks};
use crate::models::{GreeksBatch, PricingModel};
use crate::optimization::{ParallelStrategy, ProcessingMode};
use crate::traits::BatchProcessorWithDividend;

/// Batch calculate call option prices with broadcasting support
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
    let processor = MertonCallProcessor;

    let results = match strategy.mode() {
        ProcessingMode::Sequential => {
            // Use compute_with for sequential processing (zero-copy)
            iter.compute_with(|vals| {
                compute_single_call(
                    vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], &processor,
                )
            })
        }
        _ => {
            // Use compute_parallel_with for parallel processing (thread-local buffering)
            iter.compute_parallel_with(
                |vals| {
                    compute_single_call(
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
fn compute_single_call(
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    processor: &MertonCallProcessor,
) -> f64 {
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        f64::NAN
    } else {
        let params = processor.create_params_with_dividend(s, k, t, r, q, sigma);
        processor.process_single_with_dividend(&params)
    }
}

/// Batch calculate put option prices with broadcasting support
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
    let processor = MertonPutProcessor;

    let results = match strategy.mode() {
        ProcessingMode::Sequential => {
            // Use compute_with for sequential processing (zero-copy)
            iter.compute_with(|vals| {
                compute_single_put(
                    vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], &processor,
                )
            })
        }
        _ => {
            // Use compute_parallel_with for parallel processing (thread-local buffering)
            iter.compute_parallel_with(
                |vals| {
                    compute_single_put(
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
fn compute_single_put(
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    processor: &MertonPutProcessor,
) -> f64 {
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        f64::NAN
    } else {
        let params = processor.create_params_with_dividend(s, k, t, r, q, sigma);
        processor.process_single_with_dividend(&params)
    }
}

/// Batch calculate implied volatilities with broadcasting support
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
                compute_single_iv(
                    vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], vals[6],
                )
            })
        }
        _ => {
            // Use compute_parallel_with for parallel processing (thread-local buffering)
            iter.compute_parallel_with(
                |vals| {
                    compute_single_iv(
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
fn compute_single_iv(price: f64, s: f64, k: f64, t: f64, r: f64, q: f64, is_call_val: f64) -> f64 {
    if price <= 0.0 || s <= 0.0 || k <= 0.0 || t <= 0.0 {
        f64::NAN
    } else {
        let params = MertonParams::new_unchecked(s, k, t, r, q, 0.2);
        match MertonModel::implied_volatility(price, &params, is_call_val > 0.5, None) {
            Ok(sigma) => sigma,
            Err(_) => f64::NAN,
        }
    }
}

/// Batch calculate Greeks with broadcasting support
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

    let greeks_list: Vec<MertonGreeks> = match strategy.mode() {
        ProcessingMode::Sequential => {
            // Use compute_with for sequential processing (zero-copy)
            iter.compute_with(|vals| {
                calculate_merton_greeks(
                    vals[0],
                    vals[1],
                    vals[2],
                    vals[3],
                    vals[4],
                    vals[5],
                    vals[6] > 0.5,
                )
            })
        }
        _ => {
            // Use compute_parallel_with for parallel processing (thread-local buffering)
            iter.compute_parallel_with(
                |vals| {
                    calculate_merton_greeks(
                        vals[0],
                        vals[1],
                        vals[2],
                        vals[3],
                        vals[4],
                        vals[5],
                        vals[6] > 0.5,
                    )
                },
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
        dividend_rho: greeks_list.iter().map(|g| g.dividend_rho).collect(),
    })
}

// GreeksBatch is now imported from greeks_batch module

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::NUMERICAL_TOLERANCE;

    #[test]
    fn test_call_price_batch() {
        let spots = ArrayLike::Array(&[95.0, 100.0, 105.0]);
        let strikes = ArrayLike::Scalar(100.0);
        let times = ArrayLike::Scalar(1.0);
        let rates = ArrayLike::Scalar(0.05);
        let qs = ArrayLike::Scalar(0.02);
        let sigmas = ArrayLike::Scalar(0.2);

        let prices = call_price_batch(spots, strikes, times, rates, qs, sigmas).unwrap();

        assert_eq!(prices.len(), 3);
        assert!(prices.iter().all(|&p| p > 0.0 && p.is_finite()));

        // Check individual values match
        for (i, &spot) in [95.0, 100.0, 105.0].iter().enumerate() {
            let params = MertonParams::new_unchecked(spot, 100.0, 1.0, 0.05, 0.02, 0.2);
            let expected = MertonModel::call_price(&params);
            assert!((prices[i] - expected).abs() < NUMERICAL_TOLERANCE);
        }
    }

    #[test]
    fn test_broadcasting() {
        let spots = ArrayLike::Array(&[100.0, 105.0]);
        let strikes = ArrayLike::Scalar(100.0);
        let times = ArrayLike::Scalar(1.0);
        let rates = ArrayLike::Scalar(0.05);
        let qs = ArrayLike::Scalar(0.02);
        let sigmas = ArrayLike::Scalar(0.2);

        let prices = call_price_batch(spots, strikes, times, rates, qs, sigmas).unwrap();
        assert_eq!(prices.len(), 2);
    }

    #[test]
    fn test_put_price_batch() {
        let spots = ArrayLike::Array(&[95.0, 100.0, 105.0]);
        let strikes = ArrayLike::Scalar(100.0);
        let times = ArrayLike::Scalar(1.0);
        let rates = ArrayLike::Scalar(0.05);
        let qs = ArrayLike::Scalar(0.02);
        let sigmas = ArrayLike::Scalar(0.2);

        let prices = put_price_batch(spots, strikes, times, rates, qs, sigmas).unwrap();

        assert_eq!(prices.len(), 3);
        assert!(prices.iter().all(|&p| p > 0.0 && p.is_finite()));
    }
}
