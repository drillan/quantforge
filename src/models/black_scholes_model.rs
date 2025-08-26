use crate::error::QuantForgeError;
use crate::math::distributions::norm_cdf;
use crate::models::greeks;
use crate::models::implied_volatility as iv;
use crate::models::{Greeks, PricingModel};

/// Black-Scholes pricing model
pub struct BlackScholes;

/// Parameters for Black-Scholes model
#[derive(Debug, Clone)]
pub struct BlackScholesParams {
    pub spot: f64,   // Spot price
    pub strike: f64, // Strike price
    pub time: f64,   // Time to maturity
    pub rate: f64,   // Risk-free rate
    pub sigma: f64,  // Volatility (implied vol)
}

impl PricingModel for BlackScholes {
    type Params = BlackScholesParams;

    fn call_price(params: &Self::Params) -> f64 {
        let sqrt_t = params.time.sqrt();
        let d1 = (params.spot.ln() - params.strike.ln()
            + (params.rate + params.sigma * params.sigma / 2.0) * params.time)
            / (params.sigma * sqrt_t);
        let d2 = d1 - params.sigma * sqrt_t;

        // Prevent negative values for deep OTM due to numerical errors
        (params.spot * norm_cdf(d1)
            - params.strike * (-params.rate * params.time).exp() * norm_cdf(d2))
        .max(0.0)
    }

    fn put_price(params: &Self::Params) -> f64 {
        let sqrt_t = params.time.sqrt();
        let d1 = (params.spot.ln() - params.strike.ln()
            + (params.rate + params.sigma * params.sigma / 2.0) * params.time)
            / (params.sigma * sqrt_t);
        let d2 = d1 - params.sigma * sqrt_t;

        // Prevent negative values for deep OTM due to numerical errors
        (params.strike * (-params.rate * params.time).exp() * norm_cdf(-d2)
            - params.spot * norm_cdf(-d1))
        .max(0.0)
    }

    fn greeks(params: &Self::Params, is_call: bool) -> Greeks {
        greeks::calculate_all_greeks(
            params.spot,
            params.strike,
            params.time,
            params.rate,
            params.sigma,
            is_call,
        )
    }

    fn implied_volatility(
        price: f64,
        params: &Self::Params,
        is_call: bool,
        _initial_guess: Option<f64>,
    ) -> Result<f64, QuantForgeError> {
        if is_call {
            iv::implied_volatility_call(price, params.spot, params.strike, params.time, params.rate)
        } else {
            iv::implied_volatility_put(price, params.spot, params.strike, params.time, params.rate)
        }
    }
}

// Batch processing functions
impl BlackScholes {
    /// Calculate call prices for multiple spots
    pub fn call_price_batch(spots: &[f64], k: f64, t: f64, r: f64, sigma: f64) -> Vec<f64> {
        // Common terms pre-calculation
        let sqrt_t = t.sqrt();
        let v_sqrt_t = sigma * sqrt_t;
        let exp_neg_rt = (-r * t).exp();
        let half_v_squared_t = (r + sigma * sigma / 2.0) * t;
        let k_ln = k.ln();

        spots
            .iter()
            .map(|&s| {
                let d1 = (s.ln() - k_ln + half_v_squared_t) / v_sqrt_t;
                let d2 = d1 - v_sqrt_t;
                // Prevent negative values for deep OTM
                (s * norm_cdf(d1) - k * exp_neg_rt * norm_cdf(d2)).max(0.0)
            })
            .collect()
    }

    /// Calculate put prices for multiple spots
    pub fn put_price_batch(spots: &[f64], k: f64, t: f64, r: f64, sigma: f64) -> Vec<f64> {
        // Common terms pre-calculation
        let sqrt_t = t.sqrt();
        let v_sqrt_t = sigma * sqrt_t;
        let exp_neg_rt = (-r * t).exp();
        let half_v_squared_t = (r + sigma * sigma / 2.0) * t;
        let k_ln = k.ln();

        spots
            .iter()
            .map(|&s| {
                let d1 = (s.ln() - k_ln + half_v_squared_t) / v_sqrt_t;
                let d2 = d1 - v_sqrt_t;
                // Prevent negative values for deep OTM
                (k * exp_neg_rt * norm_cdf(-d2) - s * norm_cdf(-d1)).max(0.0)
            })
            .collect()
    }
}
