//! Batch processing for Black-Scholes model with broadcasting support

use crate::broadcast::{ArrayLike, BroadcastIterator};
use crate::error::QuantForgeError;
use crate::models::black_scholes_model::{BlackScholes, BlackScholesParams};
use crate::models::{Greeks, GreeksBatch, PricingModel};
use crate::optimization::{ParallelStrategy, ProcessingMode};

/// Calculate call prices with full array support and broadcasting
pub fn call_price_batch(
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    sigmas: ArrayLike,
) -> Result<Vec<f64>, QuantForgeError> {
    let inputs = vec![spots, strikes, times, rates, sigmas];
    let iter = BroadcastIterator::new(inputs)?;
    let size = iter.size_hint().0;

    // Select processing strategy based on data size
    let strategy = ParallelStrategy::select(size);

    let results = match strategy.mode() {
        ProcessingMode::Sequential => {
            // Use compute_with for sequential processing (zero-copy)
            iter.compute_with(|vals| {
                compute_single_call_price(vals[0], vals[1], vals[2], vals[3], vals[4])
            })
        }
        _ => {
            // Use compute_parallel_with for parallel processing (thread-local buffering)
            iter.compute_parallel_with(
                |vals| compute_single_call_price(vals[0], vals[1], vals[2], vals[3], vals[4]),
                strategy.chunk_size(),
            )
        }
    };

    Ok(results)
}

#[inline(always)]
fn compute_single_call_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> f64 {
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        f64::NAN
    } else {
        let params = BlackScholesParams {
            spot: s,
            strike: k,
            time: t,
            rate: r,
            sigma,
        };
        BlackScholes::call_price(&params)
    }
}

/// Calculate put prices with full array support and broadcasting
pub fn put_price_batch(
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    sigmas: ArrayLike,
) -> Result<Vec<f64>, QuantForgeError> {
    let inputs = vec![spots, strikes, times, rates, sigmas];
    let iter = BroadcastIterator::new(inputs)?;
    let size = iter.size_hint().0;

    // Select processing strategy based on data size
    let strategy = ParallelStrategy::select(size);

    let results = match strategy.mode() {
        ProcessingMode::Sequential => {
            // Use compute_with for sequential processing (zero-copy)
            iter.compute_with(|vals| {
                compute_single_put_price(vals[0], vals[1], vals[2], vals[3], vals[4])
            })
        }
        _ => {
            // Use compute_parallel_with for parallel processing (thread-local buffering)
            iter.compute_parallel_with(
                |vals| compute_single_put_price(vals[0], vals[1], vals[2], vals[3], vals[4]),
                strategy.chunk_size(),
            )
        }
    };

    Ok(results)
}

#[inline(always)]
fn compute_single_put_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> f64 {
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        f64::NAN
    } else {
        let params = BlackScholesParams {
            spot: s,
            strike: k,
            time: t,
            rate: r,
            sigma,
        };
        BlackScholes::put_price(&params)
    }
}

/// Calculate implied volatilities with full array support and broadcasting
pub fn implied_volatility_batch(
    prices: ArrayLike,
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    is_calls: ArrayLike,
) -> Result<Vec<f64>, QuantForgeError> {
    let inputs = vec![prices, spots, strikes, times, rates, is_calls];
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
fn compute_single_iv(price: f64, s: f64, k: f64, t: f64, r: f64, is_call_val: f64) -> f64 {
    if price <= 0.0 || s <= 0.0 || k <= 0.0 || t <= 0.0 {
        f64::NAN
    } else {
        let params = BlackScholesParams {
            spot: s,
            strike: k,
            time: t,
            rate: r,
            sigma: 0.2, // Initial guess
        };
        let is_call = is_call_val != 0.0;
        BlackScholes::implied_volatility(price, &params, is_call, None).unwrap_or(f64::NAN)
    }
}

/// Calculate Greeks with full array support and broadcasting
/// Returns vectors of each Greek value
pub fn greeks_batch(
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    sigmas: ArrayLike,
    is_calls: ArrayLike,
) -> Result<GreeksBatch, QuantForgeError> {
    let inputs = vec![spots, strikes, times, rates, sigmas, is_calls];
    let iter = BroadcastIterator::new(inputs)?;
    let size = iter.size_hint().0;

    // Select processing strategy based on data size
    let strategy = ParallelStrategy::select(size);

    let results = match strategy.mode() {
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

    // Unpack results into separate vectors
    let mut delta = Vec::with_capacity(size);
    let mut gamma = Vec::with_capacity(size);
    let mut vega = Vec::with_capacity(size);
    let mut theta = Vec::with_capacity(size);
    let mut rho = Vec::with_capacity(size);
    let mut dividend_rho = Vec::with_capacity(size);

    for result in results {
        delta.push(result.delta);
        gamma.push(result.gamma);
        vega.push(result.vega);
        theta.push(result.theta);
        rho.push(result.rho);
        dividend_rho.push(0.0); // No dividend sensitivity for standard BS
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
fn compute_single_greeks(s: f64, k: f64, t: f64, r: f64, sigma: f64, is_call_val: f64) -> Greeks {
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        Greeks {
            delta: f64::NAN,
            gamma: f64::NAN,
            vega: f64::NAN,
            theta: f64::NAN,
            rho: f64::NAN,
        }
    } else {
        let params = BlackScholesParams {
            spot: s,
            strike: k,
            time: t,
            rate: r,
            sigma,
        };
        let is_call = is_call_val != 0.0;
        BlackScholes::greeks(&params, is_call)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_call_price_batch_broadcasting() {
        // Test with mixed scalars and arrays
        let spots = ArrayLike::Array(&[95.0, 100.0, 105.0]);
        let strikes = ArrayLike::Scalar(100.0);
        let times = ArrayLike::Scalar(1.0);
        let rates = ArrayLike::Scalar(0.05);
        let sigmas = ArrayLike::Array(&[0.18, 0.20, 0.22]);

        let results = call_price_batch(spots, strikes, times, rates, sigmas).unwrap();
        assert_eq!(results.len(), 3);

        // Verify all results are valid prices
        for price in &results {
            assert!(price.is_finite() && *price >= 0.0);
        }
    }

    #[test]
    fn test_greeks_batch_broadcasting() {
        // Test Greeks calculation with broadcasting
        let spots = ArrayLike::Array(&[100.0]);
        let strikes = ArrayLike::Array(&[95.0, 100.0, 105.0]);
        let times = ArrayLike::Scalar(1.0);
        let rates = ArrayLike::Scalar(0.05);
        let sigmas = ArrayLike::Scalar(0.20);
        let is_calls = ArrayLike::Scalar(1.0); // True

        let greeks = greeks_batch(spots, strikes, times, rates, sigmas, is_calls).unwrap();
        assert_eq!(greeks.delta.len(), 3);
        assert_eq!(greeks.gamma.len(), 3);
        assert_eq!(greeks.vega.len(), 3);
        assert_eq!(greeks.theta.len(), 3);
        assert_eq!(greeks.rho.len(), 3);

        // Verify all Greeks are valid
        for i in 0..3 {
            assert!(greeks.delta[i].is_finite());
            assert!(greeks.gamma[i].is_finite());
            assert!(greeks.vega[i].is_finite());
            assert!(greeks.theta[i].is_finite());
            assert!(greeks.rho[i].is_finite());
        }
    }
}
