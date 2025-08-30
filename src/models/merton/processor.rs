//! BatchProcessor implementation for Merton model

use crate::models::merton::{MertonModel, MertonParams};
use crate::models::PricingModel;
use crate::traits::{BatchProcessor, BatchProcessorWithDividend};

/// Merton call option processor
pub struct MertonCallProcessor;

/// Merton put option processor
pub struct MertonPutProcessor;

// Implement BatchProcessor first (required by BatchProcessorWithDividend)
impl BatchProcessor for MertonCallProcessor {
    type Params = MertonParams;
    type Output = f64;

    fn create_params(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        MertonParams::new_unchecked(s, k, t, r, 0.0, sigma)
    }

    fn process_single(&self, params: &Self::Params) -> Self::Output {
        MertonModel::call_price(params)
    }
}

impl BatchProcessorWithDividend for MertonCallProcessor {
    type ParamsWithDividend = MertonParams;

    fn create_params_with_dividend(
        &self,
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
    ) -> Self::ParamsWithDividend {
        MertonParams::new_unchecked(s, k, t, r, q, sigma)
    }

    fn process_single_with_dividend(&self, params: &Self::ParamsWithDividend) -> Self::Output {
        MertonModel::call_price(params)
    }
}

// Implement BatchProcessor first (required by BatchProcessorWithDividend)
impl BatchProcessor for MertonPutProcessor {
    type Params = MertonParams;
    type Output = f64;

    fn create_params(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        MertonParams::new_unchecked(s, k, t, r, 0.0, sigma)
    }

    fn process_single(&self, params: &Self::Params) -> Self::Output {
        MertonModel::put_price(params)
    }
}

impl BatchProcessorWithDividend for MertonPutProcessor {
    type ParamsWithDividend = MertonParams;

    fn create_params_with_dividend(
        &self,
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
    ) -> Self::ParamsWithDividend {
        MertonParams::new_unchecked(s, k, t, r, q, sigma)
    }

    fn process_single_with_dividend(&self, params: &Self::ParamsWithDividend) -> Self::Output {
        MertonModel::put_price(params)
    }
}

/// Merton Greeks processor
pub struct MertonGreeksProcessor {
    pub is_call: bool,
}

impl MertonGreeksProcessor {
    pub fn new(is_call: bool) -> Self {
        Self { is_call }
    }
}

// Note: Greeks processing requires special handling due to the is_call parameter
// and will be integrated with the existing greeks_batch function