//! Batch processing functions for Black76 model with broadcasting support

use super::{calculate_greeks, call_price, put_price, Black76Params};
use crate::broadcast::{ArrayLike, BroadcastIterator};
use crate::error::QuantForgeError;
use crate::models::black76::implied_volatility::calculate_iv;
use crate::models::Greeks;
use rayon::prelude::*;

const PARALLELIZATION_THRESHOLD: usize = 10_000;

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

    if size > PARALLELIZATION_THRESHOLD {
        let values: Vec<_> = iter.collect();
        let results = values
            .par_iter()
            .map(|vals| {
                let params = Black76Params::new(vals[0], vals[1], vals[2], vals[3], vals[4]);
                call_price(&params)
            })
            .collect();
        Ok(results)
    } else {
        let mut results = Vec::with_capacity(size);
        for vals in iter {
            let params = Black76Params::new(vals[0], vals[1], vals[2], vals[3], vals[4]);
            results.push(call_price(&params));
        }
        Ok(results)
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

    if size > PARALLELIZATION_THRESHOLD {
        let values: Vec<_> = iter.collect();
        let results = values
            .par_iter()
            .map(|vals| {
                let params = Black76Params::new(vals[0], vals[1], vals[2], vals[3], vals[4]);
                put_price(&params)
            })
            .collect();
        Ok(results)
    } else {
        let mut results = Vec::with_capacity(size);
        for vals in iter {
            let params = Black76Params::new(vals[0], vals[1], vals[2], vals[3], vals[4]);
            results.push(put_price(&params));
        }
        Ok(results)
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

    if size > PARALLELIZATION_THRESHOLD {
        let values: Vec<_> = iter.collect();
        let results = values
            .par_iter()
            .map(|vals| {
                let params = Black76Params::new(vals[1], vals[2], vals[3], vals[4], 0.2);
                match calculate_iv(vals[0], &params, vals[5] > 0.5, None) {
                    Ok(sigma) => sigma,
                    Err(_) => f64::NAN,
                }
            })
            .collect();
        Ok(results)
    } else {
        let mut results = Vec::with_capacity(size);
        for vals in iter {
            let params = Black76Params::new(vals[1], vals[2], vals[3], vals[4], 0.2);
            let iv = match calculate_iv(vals[0], &params, vals[5] > 0.5, None) {
                Ok(sigma) => sigma,
                Err(_) => f64::NAN,
            };
            results.push(iv);
        }
        Ok(results)
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

    let greeks_list: Vec<Greeks> = if size > PARALLELIZATION_THRESHOLD {
        let values: Vec<_> = iter.collect();
        values
            .par_iter()
            .map(|vals| {
                let params = Black76Params::new(vals[0], vals[1], vals[2], vals[3], vals[4]);
                calculate_greeks(&params, vals[5] > 0.5)
            })
            .collect()
    } else {
        let mut results = Vec::with_capacity(size);
        for vals in iter {
            let params = Black76Params::new(vals[0], vals[1], vals[2], vals[3], vals[4]);
            results.push(calculate_greeks(&params, vals[5] > 0.5));
        }
        results
    };

    // Convert list of Greeks to GreeksBatch
    Ok(GreeksBatch {
        delta: greeks_list.iter().map(|g| g.delta).collect(),
        gamma: greeks_list.iter().map(|g| g.gamma).collect(),
        vega: greeks_list.iter().map(|g| g.vega).collect(),
        theta: greeks_list.iter().map(|g| g.theta).collect(),
        rho: greeks_list.iter().map(|g| g.rho).collect(),
    })
}

/// Batch Greeks result structure (arrays of each Greek)
pub struct GreeksBatch {
    pub delta: Vec<f64>,
    pub gamma: Vec<f64>,
    pub vega: Vec<f64>,
    pub theta: Vec<f64>,
    pub rho: Vec<f64>,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::NUMERICAL_TOLERANCE;

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
