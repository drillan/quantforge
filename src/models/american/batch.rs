//! Batch processing functions for American options with broadcasting support

use super::{boundary, greeks::calculate_american_greeks, AmericanModel, AmericanParams};
use crate::broadcast::{ArrayLike, BroadcastIterator};
use crate::error::QuantForgeError;
use crate::models::{Greeks, GreeksBatch, PricingModel};
use rayon::prelude::*;

const PARALLELIZATION_THRESHOLD: usize = 10_000;

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

    if size > PARALLELIZATION_THRESHOLD {
        let values: Vec<_> = iter.collect();
        let results = values
            .par_iter()
            .map(|vals| {
                let params = AmericanParams::new_unchecked(
                    vals[0], vals[1], vals[2], vals[3], vals[4], vals[5],
                );

                // Validate inputs
                if params.s <= 0.0 || params.k <= 0.0 || params.t < 0.0 || params.sigma <= 0.0 {
                    f64::NAN
                } else if params.q > params.r {
                    // Dividend arbitrage check
                    f64::NAN
                } else {
                    AmericanModel::call_price(&params)
                }
            })
            .collect();
        Ok(results)
    } else {
        let mut results = Vec::with_capacity(size);
        for vals in iter {
            let params =
                AmericanParams::new_unchecked(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]);

            // Validate inputs
            if params.s <= 0.0 || params.k <= 0.0 || params.t < 0.0 || params.sigma <= 0.0 {
                results.push(f64::NAN);
            } else if params.q > params.r {
                // Dividend arbitrage check
                results.push(f64::NAN);
            } else {
                results.push(AmericanModel::call_price(&params));
            }
        }
        Ok(results)
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

    if size > PARALLELIZATION_THRESHOLD {
        let values: Vec<_> = iter.collect();
        let results = values
            .par_iter()
            .map(|vals| {
                let params = AmericanParams::new_unchecked(
                    vals[0], vals[1], vals[2], vals[3], vals[4], vals[5],
                );

                // Validate inputs
                if params.s <= 0.0 || params.k <= 0.0 || params.t < 0.0 || params.sigma <= 0.0 {
                    f64::NAN
                } else if params.q > params.r {
                    // Dividend arbitrage check
                    f64::NAN
                } else {
                    AmericanModel::put_price(&params)
                }
            })
            .collect();
        Ok(results)
    } else {
        let mut results = Vec::with_capacity(size);
        for vals in iter {
            let params =
                AmericanParams::new_unchecked(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]);

            // Validate inputs
            if params.s <= 0.0 || params.k <= 0.0 || params.t < 0.0 || params.sigma <= 0.0 {
                results.push(f64::NAN);
            } else if params.q > params.r {
                // Dividend arbitrage check
                results.push(f64::NAN);
            } else {
                results.push(AmericanModel::put_price(&params));
            }
        }
        Ok(results)
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

    if size > PARALLELIZATION_THRESHOLD {
        let values: Vec<_> = iter.collect();
        let results = values
            .par_iter()
            .map(|vals| {
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
            })
            .collect();
        Ok(results)
    } else {
        let mut results = Vec::with_capacity(size);
        for vals in iter {
            // Use initial guess of 0.2 for volatility
            let params =
                AmericanParams::new_unchecked(vals[1], vals[2], vals[3], vals[4], vals[5], 0.2);

            // Validate inputs
            if params.s <= 0.0 || params.k <= 0.0 || params.t < 0.0 || vals[0] <= 0.0 {
                results.push(f64::NAN);
            } else if params.q > params.r {
                // Dividend arbitrage check
                results.push(f64::NAN);
            } else {
                let iv = match AmericanModel::implied_volatility(
                    vals[0],
                    &params,
                    vals[6] > 0.5,
                    None,
                ) {
                    Ok(sigma) => sigma,
                    Err(_) => f64::NAN,
                };
                results.push(iv);
            }
        }
        Ok(results)
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

    let mut delta = Vec::with_capacity(size);
    let mut gamma = Vec::with_capacity(size);
    let mut vega = Vec::with_capacity(size);
    let mut theta = Vec::with_capacity(size);
    let mut rho = Vec::with_capacity(size);
    let mut dividend_rho = Vec::with_capacity(size);

    if size > PARALLELIZATION_THRESHOLD {
        let values: Vec<_> = iter.collect();
        let results: Vec<Greeks> = values
            .par_iter()
            .map(|vals| {
                let params = AmericanParams::new_unchecked(
                    vals[0], vals[1], vals[2], vals[3], vals[4], vals[5],
                );

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
            })
            .collect();

        // Unpack into separate vectors
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
    } else {
        for vals in iter {
            let params =
                AmericanParams::new_unchecked(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]);

            // Validate inputs
            if params.s <= 0.0 || params.k <= 0.0 || params.t < 0.0 || params.sigma <= 0.0 {
                delta.push(f64::NAN);
                gamma.push(f64::NAN);
                vega.push(f64::NAN);
                theta.push(f64::NAN);
                rho.push(f64::NAN);
                dividend_rho.push(f64::NAN);
            } else if params.q > params.r {
                // Dividend arbitrage check
                delta.push(f64::NAN);
                gamma.push(f64::NAN);
                vega.push(f64::NAN);
                theta.push(f64::NAN);
                rho.push(f64::NAN);
                dividend_rho.push(f64::NAN);
            } else {
                let greeks = calculate_american_greeks(&params, vals[6] > 0.5);
                delta.push(greeks.delta);
                gamma.push(greeks.gamma);
                vega.push(greeks.vega);
                theta.push(greeks.theta);
                rho.push(greeks.rho);
                // For American options, dividend_rho is the sensitivity to dividend yield
                // We'll calculate it as negative delta (approximation)
                dividend_rho.push(-greeks.delta);
            }
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

    if size > PARALLELIZATION_THRESHOLD {
        let values: Vec<_> = iter.collect();
        let results = values
            .par_iter()
            .map(|vals| {
                let params = AmericanParams::new_unchecked(
                    vals[0], vals[1], vals[2], vals[3], vals[4], vals[5],
                );

                // Validate inputs
                if params.s <= 0.0 || params.k <= 0.0 || params.t < 0.0 || params.sigma <= 0.0 {
                    f64::NAN
                } else if params.q > params.r {
                    // Dividend arbitrage check
                    f64::NAN
                } else {
                    boundary::exercise_boundary(&params, vals[6] > 0.5)
                }
            })
            .collect();
        Ok(results)
    } else {
        let mut results = Vec::with_capacity(size);
        for vals in iter {
            let params =
                AmericanParams::new_unchecked(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]);

            // Validate inputs
            if params.s <= 0.0 || params.k <= 0.0 || params.t < 0.0 || params.sigma <= 0.0 {
                results.push(f64::NAN);
            } else if params.q > params.r {
                // Dividend arbitrage check
                results.push(f64::NAN);
            } else {
                results.push(boundary::exercise_boundary(&params, vals[6] > 0.5));
            }
        }
        Ok(results)
    }
}
