//! Batch processing for Black-Scholes model with broadcasting support

use crate::broadcast::{ArrayLike, BroadcastIterator};
use crate::error::QuantForgeError;
use crate::models::black_scholes_model::{BlackScholes, BlackScholesParams};
use crate::models::{GreeksBatch, PricingModel};
use crate::optimization::ParallelStrategy;

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

    // Use dynamic parallel strategy
    let values: Vec<_> = iter.collect();
    let strategy = ParallelStrategy::select(size);

    let results = strategy.process_batch(&values, |vals| {
        let params = BlackScholesParams {
            spot: vals[0],
            strike: vals[1],
            time: vals[2],
            rate: vals[3],
            sigma: vals[4],
        };

        // Validate inputs
        if params.spot <= 0.0 || params.strike <= 0.0 || params.time <= 0.0 || params.sigma <= 0.0 {
            f64::NAN
        } else {
            BlackScholes::call_price(&params)
        }
    });

    Ok(results)
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

    // Use dynamic parallel strategy
    let values: Vec<_> = iter.collect();
    let strategy = ParallelStrategy::select(size);

    let results = strategy.process_batch(&values, |vals| {
        let params = BlackScholesParams {
            spot: vals[0],
            strike: vals[1],
            time: vals[2],
            rate: vals[3],
            sigma: vals[4],
        };

        // Validate inputs
        if params.spot <= 0.0 || params.strike <= 0.0 || params.time <= 0.0 || params.sigma <= 0.0 {
            f64::NAN
        } else {
            BlackScholes::put_price(&params)
        }
    });

    Ok(results)
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

    // Use dynamic parallel strategy
    let values: Vec<_> = iter.collect();
    let strategy = ParallelStrategy::select(size);

    let results = strategy.process_batch(&values, |vals| {
        let price = vals[0];
        let params = BlackScholesParams {
            spot: vals[1],
            strike: vals[2],
            time: vals[3],
            rate: vals[4],
            sigma: 0.2, // Initial guess
        };
        let is_call = vals[5] != 0.0; // Convert to bool

        // Validate inputs
        if price <= 0.0 || params.spot <= 0.0 || params.strike <= 0.0 || params.time <= 0.0 {
            f64::NAN
        } else {
            BlackScholes::implied_volatility(price, &params, is_call, None).unwrap_or(f64::NAN)
        }
    });

    Ok(results)
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

    let mut delta = Vec::with_capacity(size);
    let mut gamma = Vec::with_capacity(size);
    let mut vega = Vec::with_capacity(size);
    let mut theta = Vec::with_capacity(size);
    let mut rho = Vec::with_capacity(size);
    let mut dividend_rho = Vec::with_capacity(size); // For consistency, though BS doesn't use dividends

    for vals in iter {
        let params = BlackScholesParams {
            spot: vals[0],
            strike: vals[1],
            time: vals[2],
            rate: vals[3],
            sigma: vals[4],
        };
        let is_call = vals[5] != 0.0; // Convert to bool

        // Validate inputs
        if params.spot <= 0.0 || params.strike <= 0.0 || params.time <= 0.0 || params.sigma <= 0.0 {
            delta.push(f64::NAN);
            gamma.push(f64::NAN);
            vega.push(f64::NAN);
            theta.push(f64::NAN);
            rho.push(f64::NAN);
            dividend_rho.push(0.0); // No dividend sensitivity for standard BS
        } else {
            let greeks = BlackScholes::greeks(&params, is_call);
            delta.push(greeks.delta);
            gamma.push(greeks.gamma);
            vega.push(greeks.vega);
            theta.push(greeks.theta);
            rho.push(greeks.rho);
            dividend_rho.push(0.0); // No dividend sensitivity for standard BS
        }
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
