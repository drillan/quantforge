//! BatchProcessor implementation for American options
//!
//! Provides unified batch processing interface for American options
//! using the Bjerksund-Stensland 2002 approximation.

use crate::models::american::{AmericanModel, AmericanParams};
use crate::models::PricingModel;
use crate::traits::{BatchProcessor, BatchProcessorWithDividend};

/// Processor for American call options
pub struct AmericanCallProcessor;

/// Processor for American put options
pub struct AmericanPutProcessor;

/// Processor for American Greeks
pub struct AmericanGreeksProcessor {
    pub is_call: bool,
}

// ============================================================================
// BatchProcessor implementations (required as base trait)
// ============================================================================

impl BatchProcessor for AmericanCallProcessor {
    type Params = AmericanParams;
    type Output = f64;

    fn create_params(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        // American options typically have dividends, but we provide q=0 for base trait
        AmericanParams::new_unchecked(s, k, t, r, 0.0, sigma)
    }

    fn process_single(&self, params: &Self::Params) -> Self::Output {
        AmericanModel::call_price(params)
    }
}

impl BatchProcessor for AmericanPutProcessor {
    type Params = AmericanParams;
    type Output = f64;

    fn create_params(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        // American options typically have dividends, but we provide q=0 for base trait
        AmericanParams::new_unchecked(s, k, t, r, 0.0, sigma)
    }

    fn process_single(&self, params: &Self::Params) -> Self::Output {
        AmericanModel::put_price(params)
    }
}

// ============================================================================
// BatchProcessorWithDividend implementations (main interface for American)
// ============================================================================

impl BatchProcessorWithDividend for AmericanCallProcessor {
    type ParamsWithDividend = AmericanParams;

    fn create_params_with_dividend(
        &self,
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
    ) -> Self::ParamsWithDividend {
        AmericanParams::new_unchecked(s, k, t, r, q, sigma)
    }

    fn process_single_with_dividend(&self, params: &Self::ParamsWithDividend) -> Self::Output {
        AmericanModel::call_price(params)
    }
}

impl BatchProcessorWithDividend for AmericanPutProcessor {
    type ParamsWithDividend = AmericanParams;

    fn create_params_with_dividend(
        &self,
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
    ) -> Self::ParamsWithDividend {
        AmericanParams::new_unchecked(s, k, t, r, q, sigma)
    }

    fn process_single_with_dividend(&self, params: &Self::ParamsWithDividend) -> Self::Output {
        AmericanModel::put_price(params)
    }
}

// ============================================================================
// Greeks Processor (special handling for finite difference calculations)
// ============================================================================

impl BatchProcessor for AmericanGreeksProcessor {
    type Params = AmericanParams;
    type Output = crate::models::Greeks;

    fn create_params(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        AmericanParams::new_unchecked(s, k, t, r, 0.0, sigma)
    }

    fn process_single(&self, params: &Self::Params) -> Self::Output {
        AmericanModel::greeks(params, self.is_call)
    }
}

impl BatchProcessorWithDividend for AmericanGreeksProcessor {
    type ParamsWithDividend = AmericanParams;

    fn create_params_with_dividend(
        &self,
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
    ) -> Self::ParamsWithDividend {
        AmericanParams::new_unchecked(s, k, t, r, q, sigma)
    }

    fn process_single_with_dividend(&self, params: &Self::ParamsWithDividend) -> Self::Output {
        AmericanModel::greeks(params, self.is_call)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_call_processor() {
        let processor = AmericanCallProcessor;
        let params = processor.create_params_with_dividend(100.0, 100.0, 1.0, 0.05, 0.02, 0.2);
        let price = processor.process_single_with_dividend(&params);
        assert!(price > 0.0);
    }

    #[test]
    fn test_put_processor() {
        let processor = AmericanPutProcessor;
        let params = processor.create_params_with_dividend(100.0, 100.0, 1.0, 0.05, 0.02, 0.2);
        let price = processor.process_single_with_dividend(&params);
        assert!(price > 0.0);
    }

    #[test]
    fn test_greeks_processor() {
        let processor = AmericanGreeksProcessor { is_call: true };
        let params = processor.create_params_with_dividend(100.0, 100.0, 1.0, 0.05, 0.02, 0.2);
        let greeks = processor.process_single_with_dividend(&params);
        assert!(!greeks.delta.is_nan());
        assert!(!greeks.gamma.is_nan());
    }
}
