use crate::models::{
    american::{self, AmericanParams},
    batch_helpers,
    black_scholes_model::{BlackScholes, BlackScholesParams},
    merton, GreeksBatch,
};
use crate::traits::generic_batch::{
    BatchParams, IVBatchParams, ImpliedVolatilityBatch, OptionModelBatch, PriceBatch,
};

/// Generic macro for implementing batch traits to reduce code duplication
macro_rules! impl_batch_traits {
    (
        $model:ident,
        greeks => $greeks_fn:ident,
        iv => $iv_fn:ident,
        uses_q: $uses_q:expr
    ) => {
        impl OptionModelBatch for $model {
            type Error = String;

            fn calculate_greeks_batch(params: BatchParams) -> Result<GreeksBatch, Self::Error> {
                if $uses_q {
                    batch_helpers::$greeks_fn(
                        params.spots,
                        params.strikes,
                        params.times,
                        params.rates,
                        params.qs,
                        params.sigmas,
                        params.is_calls,
                    )
                    .map_err(|e| e.to_string())
                } else {
                    // For Black76: q is not used
                    batch_helpers::$greeks_fn(
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
        }

        impl ImpliedVolatilityBatch for $model {
            type Error = String;

            fn calculate_iv_batch(params: IVBatchParams) -> Result<Vec<f64>, Self::Error> {
                if $uses_q {
                    batch_helpers::$iv_fn(
                        params.prices,
                        params.spots,
                        params.strikes,
                        params.times,
                        params.rates,
                        params.qs,
                        params.is_calls,
                    )
                    .map_err(|e| e.to_string())
                } else {
                    // For Black76: q is not used
                    batch_helpers::$iv_fn(
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
        }
    };
}

/// Generic macro for implementing PriceBatch trait
macro_rules! impl_price_batch {
    (
        $model:ident,
        call => $call_fn:path,
        put => $put_fn:path,
        mixed => $mixed_handler:expr
    ) => {
        impl PriceBatch for $model {
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
                    $call_fn(spots, strikes, times, rates, qs, sigmas)
                        .map_err(|e| e.to_string())
                } else if is_calls.iter().all(|&c| !c) {
                    $put_fn(spots, strikes, times, rates, qs, sigmas)
                        .map_err(|e| e.to_string())
                } else {
                    // Mixed calls and puts
                    $mixed_handler(spots, strikes, times, rates, qs, sigmas, is_calls)
                }
            }
        }
    };
}

/// Black-Scholes model batch implementation
pub struct BlackScholesBatch;

impl_batch_traits!(
    BlackScholesBatch,
    greeks => greeks_batch_vec,
    iv => implied_volatility_batch_vec,
    uses_q: true
);

impl_price_batch!(
    BlackScholesBatch,
    call => batch_helpers::call_price_batch_vec,
    put => batch_helpers::put_price_batch_vec,
    mixed => |spots: Vec<f64>, strikes: Vec<f64>, times: Vec<f64>, rates: Vec<f64>, _qs: Vec<f64>, sigmas: Vec<f64>, is_calls: Vec<bool>| {
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
);

/// Black76 model batch implementation
pub struct Black76Batch;

impl_batch_traits!(
    Black76Batch,
    greeks => b76_greeks_batch_vec,
    iv => b76_implied_volatility_batch_vec,
    uses_q: false
);

// Black76 doesn't have PriceBatch implementation in the original

/// Merton model batch implementation
pub struct MertonBatch;

impl_batch_traits!(
    MertonBatch,
    greeks => merton_greeks_batch_vec,
    iv => merton_implied_volatility_batch_vec,
    uses_q: true
);

impl_price_batch!(
    MertonBatch,
    call => batch_helpers::merton_call_price_batch_vec,
    put => batch_helpers::merton_put_price_batch_vec,
    mixed => |spots: Vec<f64>, strikes: Vec<f64>, times: Vec<f64>, rates: Vec<f64>, qs: Vec<f64>, sigmas: Vec<f64>, is_calls: Vec<bool>| {
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
);

/// American model batch implementation
pub struct AmericanBatch;

impl_batch_traits!(
    AmericanBatch,
    greeks => american_greeks_batch_vec,
    iv => american_implied_volatility_batch_vec,
    uses_q: true
);

impl_price_batch!(
    AmericanBatch,
    call => batch_helpers::american_call_price_batch_vec,
    put => batch_helpers::american_put_price_batch_vec,
    mixed => |spots: Vec<f64>, strikes: Vec<f64>, times: Vec<f64>, rates: Vec<f64>, qs: Vec<f64>, sigmas: Vec<f64>, is_calls: Vec<bool>| {
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
);