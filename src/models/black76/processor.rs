//! BatchProcessor implementation for Black76 model

use crate::models::black76::{Black76, Black76Params};
use crate::models::PricingModel;
use crate::traits::BatchProcessor;

/// Black76 call option processor
pub struct Black76CallProcessor;

/// Black76 put option processor
pub struct Black76PutProcessor;

impl BatchProcessor for Black76CallProcessor {
    type Params = Black76Params;
    type Output = f64;

    fn create_params(&self, f: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        Black76Params::new(f, k, t, r, sigma)
    }

    fn process_single(&self, params: &Self::Params) -> Self::Output {
        Black76::call_price(params)
    }
}

impl BatchProcessor for Black76PutProcessor {
    type Params = Black76Params;
    type Output = f64;

    fn create_params(&self, f: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        Black76Params::new(f, k, t, r, sigma)
    }

    fn process_single(&self, params: &Self::Params) -> Self::Output {
        Black76::put_price(params)
    }
}

/// Black76 Greeks processor
pub struct Black76GreeksProcessor {
    pub is_call: bool,
}

impl Black76GreeksProcessor {
    pub fn new(is_call: bool) -> Self {
        Self { is_call }
    }
}

// Note: Greeks processing requires special handling due to the is_call parameter
// and will be integrated with the existing greeks_batch function