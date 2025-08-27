use crate::models::{
    american::{self, AmericanParams},
    batch_helpers,
    black_scholes_model::{BlackScholes, BlackScholesParams},
    merton, GreeksBatch, PricingModel,
};
use crate::traits::generic_batch::{
    BatchParams, IVBatchParams, ImpliedVolatilityBatch, OptionModelBatch, PriceBatch,
};

/// Black-Scholes model batch implementation
pub struct BlackScholesBatch;

impl OptionModelBatch for BlackScholesBatch {
    type Error = String;

    fn calculate_greeks_batch(params: BatchParams) -> Result<GreeksBatch, Self::Error> {
        batch_helpers::greeks_batch_vec(
            params.spots,
            params.strikes,
            params.times,
            params.rates,
            params.qs,
            params.sigmas,
            params.is_calls,
        )
        .map_err(|e| e.to_string())
    }
}

impl ImpliedVolatilityBatch for BlackScholesBatch {
    type Error = String;

    fn calculate_iv_batch(params: IVBatchParams) -> Result<Vec<f64>, Self::Error> {
        batch_helpers::implied_volatility_batch_vec(
            params.prices,
            params.spots,
            params.strikes,
            params.times,
            params.rates,
            params.qs,
            params.is_calls,
        )
        .map_err(|e| e.to_string())
    }
}

impl PriceBatch for BlackScholesBatch {
    type Error = String;

    fn calculate_price_batch(params: BatchParams) -> Result<Vec<f64>, Self::Error> {
        let BatchParams {
            spots,
            strikes,
            times,
            rates,
            qs,
            sigmas,
            is_calls,
        } = params;

        if is_calls.iter().all(|&c| c) {
            batch_helpers::call_price_batch_vec(spots, strikes, times, rates, qs, sigmas)
                .map_err(|e| e.to_string())
        } else if is_calls.iter().all(|&c| !c) {
            batch_helpers::put_price_batch_vec(spots, strikes, times, rates, qs, sigmas)
                .map_err(|e| e.to_string())
        } else {
            // Mixed calls and puts
            let mut results = Vec::with_capacity(spots.len());
            for i in 0..spots.len() {
                let bs_params = BlackScholesParams {
                    spot: spots[i],
                    strike: strikes[i],
                    time: times[i],
                    rate: rates[i],
                    sigma: sigmas[i],
                };
                let price = if is_calls[i] {
                    BlackScholes::call_price(&bs_params)
                } else {
                    BlackScholes::put_price(&bs_params)
                };
                results.push(price);
            }
            Ok(results)
        }
    }
}

/// Black76 model batch implementation
pub struct Black76Batch;

impl OptionModelBatch for Black76Batch {
    type Error = String;

    fn calculate_greeks_batch(params: BatchParams) -> Result<GreeksBatch, Self::Error> {
        // Black76 uses spots as futures price, so q is effectively 0 (_qs unused)
        batch_helpers::b76_greeks_batch_vec(
            params.spots,
            params.strikes,
            params.times,
            params.rates,
            params.sigmas,
            params.is_calls,
        )
        .map_err(|e| e.to_string())
    }
}

impl ImpliedVolatilityBatch for Black76Batch {
    type Error = String;

    fn calculate_iv_batch(params: IVBatchParams) -> Result<Vec<f64>, Self::Error> {
        batch_helpers::b76_implied_volatility_batch_vec(
            params.prices,
            params.spots,
            params.strikes,
            params.times,
            params.rates,
            params.is_calls,
        )
        .map_err(|e| e.to_string())
    }
}

/// Merton model batch implementation
pub struct MertonBatch;

impl OptionModelBatch for MertonBatch {
    type Error = String;

    fn calculate_greeks_batch(params: BatchParams) -> Result<GreeksBatch, Self::Error> {
        batch_helpers::merton_greeks_batch_vec(
            params.spots,
            params.strikes,
            params.times,
            params.rates,
            params.qs,
            params.sigmas,
            params.is_calls,
        )
        .map_err(|e| e.to_string())
    }
}

impl ImpliedVolatilityBatch for MertonBatch {
    type Error = String;

    fn calculate_iv_batch(params: IVBatchParams) -> Result<Vec<f64>, Self::Error> {
        batch_helpers::merton_implied_volatility_batch_vec(
            params.prices,
            params.spots,
            params.strikes,
            params.times,
            params.rates,
            params.qs,
            params.is_calls,
        )
        .map_err(|e| e.to_string())
    }
}

impl PriceBatch for MertonBatch {
    type Error = String;

    fn calculate_price_batch(params: BatchParams) -> Result<Vec<f64>, Self::Error> {
        let BatchParams {
            spots,
            strikes,
            times,
            rates,
            qs,
            sigmas,
            is_calls,
        } = params;

        if is_calls.iter().all(|&c| c) {
            batch_helpers::merton_call_price_batch_vec(spots, strikes, times, rates, qs, sigmas)
                .map_err(|e| e.to_string())
        } else if is_calls.iter().all(|&c| !c) {
            batch_helpers::merton_put_price_batch_vec(spots, strikes, times, rates, qs, sigmas)
                .map_err(|e| e.to_string())
        } else {
            // Mixed calls and puts
            let mut results = Vec::with_capacity(spots.len());
            for i in 0..spots.len() {
                let price = if is_calls[i] {
                    merton::call_price(spots[i], strikes[i], times[i], rates[i], qs[i], sigmas[i])
                } else {
                    merton::put_price(spots[i], strikes[i], times[i], rates[i], qs[i], sigmas[i])
                };
                results.push(price);
            }
            Ok(results)
        }
    }
}

/// American model batch implementation
pub struct AmericanBatch;

impl OptionModelBatch for AmericanBatch {
    type Error = String;

    fn calculate_greeks_batch(params: BatchParams) -> Result<GreeksBatch, Self::Error> {
        batch_helpers::american_greeks_batch_vec(
            params.spots,
            params.strikes,
            params.times,
            params.rates,
            params.qs,
            params.sigmas,
            params.is_calls,
        )
        .map_err(|e| e.to_string())
    }
}

impl ImpliedVolatilityBatch for AmericanBatch {
    type Error = String;

    fn calculate_iv_batch(params: IVBatchParams) -> Result<Vec<f64>, Self::Error> {
        batch_helpers::american_implied_volatility_batch_vec(
            params.prices,
            params.spots,
            params.strikes,
            params.times,
            params.rates,
            params.qs,
            params.is_calls,
        )
        .map_err(|e| e.to_string())
    }
}

impl PriceBatch for AmericanBatch {
    type Error = String;

    fn calculate_price_batch(params: BatchParams) -> Result<Vec<f64>, Self::Error> {
        let BatchParams {
            spots,
            strikes,
            times,
            rates,
            qs,
            sigmas,
            is_calls,
        } = params;

        if is_calls.iter().all(|&c| c) {
            batch_helpers::american_call_price_batch_vec(spots, strikes, times, rates, qs, sigmas)
                .map_err(|e| e.to_string())
        } else if is_calls.iter().all(|&c| !c) {
            batch_helpers::american_put_price_batch_vec(spots, strikes, times, rates, qs, sigmas)
                .map_err(|e| e.to_string())
        } else {
            // Mixed calls and puts
            let mut results = Vec::with_capacity(spots.len());
            for i in 0..spots.len() {
                let am_params = AmericanParams {
                    s: spots[i],
                    k: strikes[i],
                    t: times[i],
                    r: rates[i],
                    q: qs[i],
                    sigma: sigmas[i],
                };
                let price = if is_calls[i] {
                    american::american_call_price(&am_params)
                } else {
                    american::american_put_price(&am_params)
                };
                results.push(price);
            }
            Ok(results)
        }
    }
}
