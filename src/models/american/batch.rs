//! Batch processing functions for American options with broadcasting support

use super::processor::{AmericanCallProcessor, AmericanGreeksProcessor, AmericanPutProcessor};
use super::{boundary, greeks::calculate_american_greeks, AmericanModel, AmericanParams};
use crate::broadcast::{ArrayLike, BroadcastIterator};
use crate::error::QuantForgeError;
use crate::models::{Greeks, GreeksBatch, PricingModel};
use crate::optimization::ParallelStrategy;
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

    // Collect all values for parallel processing
    let values: Vec<[f64; 6]> = iter
        .map(|vals| [vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]])
        .collect();

    // Use dynamic parallelization strategy
    let strategy = ParallelStrategy::select(size);
    let processor = AmericanCallProcessor;

    Ok(strategy.process_batch(&values, |vals| {
        let params = processor
            .create_params_with_dividend(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]);

        // Validate inputs
        if params.s <= 0.0 || params.k <= 0.0 || params.t < 0.0 || params.sigma <= 0.0 {
            f64::NAN
        } else if params.q > params.r {
            // Dividend arbitrage check
            f64::NAN
        } else {
            processor.process_single_with_dividend(&params)
        }
    }))
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

    // Collect all values for parallel processing
    let values: Vec<[f64; 6]> = iter
        .map(|vals| [vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]])
        .collect();

    // Use dynamic parallelization strategy
    let strategy = ParallelStrategy::select(size);
    let processor = AmericanPutProcessor;

    Ok(strategy.process_batch(&values, |vals| {
        let params = processor
            .create_params_with_dividend(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]);

        // Validate inputs
        if params.s <= 0.0 || params.k <= 0.0 || params.t < 0.0 || params.sigma <= 0.0 {
            f64::NAN
        } else if params.q > params.r {
            // Dividend arbitrage check
            f64::NAN
        } else {
            processor.process_single_with_dividend(&params)
        }
    }))
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

    // Collect all values for parallel processing
    let values: Vec<[f64; 7]> = iter
        .map(|vals| {
            [
                vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], vals[6],
            ]
        })
        .collect();

    // Use dynamic parallelization strategy
    let strategy = ParallelStrategy::select(size);

    Ok(strategy.process_batch(&values, |vals| {
        // Use initial guess of 0.2 for volatility
        let params =
            AmericanParams::new_unchecked(vals[1], vals[2], vals[3], vals[4], vals[5], 0.2);

        // Validate inputs
        if params.s <= 0.0 || params.k <= 0.0 || params.t < 0.0 || vals[0] <= 0.0 {
            f64::NAN
        } else if params.q > params.r {
            // Dividend arbitrage check
            f64::NAN
        } else {
            match AmericanModel::implied_volatility(vals[0], &params, vals[6] > 0.5, None) {
                Ok(sigma) => sigma,
                Err(_) => f64::NAN,
            }
        }
    }))
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

    // Collect all values for parallel processing
    let values: Vec<[f64; 7]> = iter
        .map(|vals| {
            [
                vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], vals[6],
            ]
        })
        .collect();

    // Use dynamic parallelization strategy
    let strategy = ParallelStrategy::select(size);
    let processor = AmericanGreeksProcessor { is_call: true }; // Will be overridden per element

    let results: Vec<Greeks> = strategy.process_batch(&values, |vals| {
        let params = processor
            .create_params_with_dividend(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]);

        // Validate inputs
        if params.s <= 0.0 || params.k <= 0.0 || params.t < 0.0 || params.sigma <= 0.0 {
            Greeks {
                delta: f64::NAN,
                gamma: f64::NAN,
                vega: f64::NAN,
                theta: f64::NAN,
                rho: f64::NAN,
            }
        } else if params.q > params.r {
            // Dividend arbitrage check
            Greeks {
                delta: f64::NAN,
                gamma: f64::NAN,
                vega: f64::NAN,
                theta: f64::NAN,
                rho: f64::NAN,
            }
        } else {
            calculate_american_greeks(&params, vals[6] > 0.5)
        }
    });

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

    // Collect all values for parallel processing
    let values: Vec<[f64; 7]> = iter
        .map(|vals| {
            [
                vals[0], vals[1], vals[2], vals[3], vals[4], vals[5], vals[6],
            ]
        })
        .collect();

    // Use dynamic parallelization strategy
    let strategy = ParallelStrategy::select(size);

    Ok(strategy.process_batch(&values, |vals| {
        let params =
            AmericanParams::new_unchecked(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]);

        // Validate inputs
        if params.s <= 0.0 || params.k <= 0.0 || params.t < 0.0 || params.sigma <= 0.0 {
            f64::NAN
        } else if params.q > params.r {
            // Dividend arbitrage check
            f64::NAN
        } else {
            boundary::exercise_boundary(&params, vals[6] > 0.5)
        }
    }))
}
