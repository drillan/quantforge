//! Batch processing functions for Merton model with broadcasting support

use super::MertonParams;
use crate::broadcast::{ArrayLike, BroadcastIterator};
use crate::error::QuantForgeError;
use crate::models::merton::{greeks::calculate_merton_greeks, MertonGreeks, MertonModel};
use crate::models::PricingModel;
use rayon::prelude::*;

const PARALLELIZATION_THRESHOLD: usize = 10_000;

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

    if size > PARALLELIZATION_THRESHOLD {
        let values: Vec<_> = iter.collect();
        let results = values
            .par_iter()
            .map(|vals| {
                let params = MertonParams::new_unchecked(
                    vals[0], vals[1], vals[2], vals[3], vals[4], vals[5],
                );
                MertonModel::call_price(&params)
            })
            .collect();
        Ok(results)
    } else {
        let mut results = Vec::with_capacity(size);
        for vals in iter {
            let params =
                MertonParams::new_unchecked(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]);
            results.push(MertonModel::call_price(&params));
        }
        Ok(results)
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

    if size > PARALLELIZATION_THRESHOLD {
        let values: Vec<_> = iter.collect();
        let results = values
            .par_iter()
            .map(|vals| {
                let params = MertonParams::new_unchecked(
                    vals[0], vals[1], vals[2], vals[3], vals[4], vals[5],
                );
                MertonModel::put_price(&params)
            })
            .collect();
        Ok(results)
    } else {
        let mut results = Vec::with_capacity(size);
        for vals in iter {
            let params =
                MertonParams::new_unchecked(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]);
            results.push(MertonModel::put_price(&params));
        }
        Ok(results)
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

    if size > PARALLELIZATION_THRESHOLD {
        let values: Vec<_> = iter.collect();
        let results = values
            .par_iter()
            .map(|vals| {
                let params =
                    MertonParams::new_unchecked(vals[1], vals[2], vals[3], vals[4], vals[5], 0.2);
                match MertonModel::implied_volatility(vals[0], &params, vals[6] > 0.5, None) {
                    Ok(sigma) => sigma,
                    Err(_) => f64::NAN,
                }
            })
            .collect();
        Ok(results)
    } else {
        let mut results = Vec::with_capacity(size);
        for vals in iter {
            let params =
                MertonParams::new_unchecked(vals[1], vals[2], vals[3], vals[4], vals[5], 0.2);
            let iv = match MertonModel::implied_volatility(vals[0], &params, vals[6] > 0.5, None) {
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

    let greeks_list: Vec<MertonGreeks> = if size > PARALLELIZATION_THRESHOLD {
        let values: Vec<_> = iter.collect();
        values
            .par_iter()
            .map(|vals| {
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
            .collect()
    } else {
        let mut results = Vec::with_capacity(size);
        for vals in iter {
            results.push(calculate_merton_greeks(
                vals[0],
                vals[1],
                vals[2],
                vals[3],
                vals[4],
                vals[5],
                vals[6] > 0.5,
            ));
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
        dividend_rho: greeks_list.iter().map(|g| g.dividend_rho).collect(),
    })
}

/// Batch Greeks result structure (arrays of each Greek)
pub struct GreeksBatch {
    pub delta: Vec<f64>,
    pub gamma: Vec<f64>,
    pub vega: Vec<f64>,
    pub theta: Vec<f64>,
    pub rho: Vec<f64>,
    pub dividend_rho: Vec<f64>,
}

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
