//! Black76 pricing calculations

use super::Black76Params;
use crate::math::distributions::norm_cdf;

/// Calculate call option price using Black76 model
pub fn call_price(params: &Black76Params) -> f64 {
    if params.validate().is_err() {
        return f64::NAN;
    }

    let d1 = params.d1();
    let d2 = params.d2();
    let discount = params.discount_factor();

    discount * (params.forward * norm_cdf(d1) - params.strike * norm_cdf(d2))
}

/// Calculate put option price using Black76 model
pub fn put_price(params: &Black76Params) -> f64 {
    if params.validate().is_err() {
        return f64::NAN;
    }

    let d1 = params.d1();
    let d2 = params.d2();
    let discount = params.discount_factor();

    discount * (params.strike * norm_cdf(-d2) - params.forward * norm_cdf(-d1))
}

// Batch functions removed - will be reimplemented with full array support

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::NUMERICAL_TOLERANCE;

    #[test]
    fn test_put_call_parity() {
        // Put-Call Parity for Black76: C - P = DF * (F - K)
        let forward = 100.0;
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let sigma = 0.2;

        let params = Black76Params::new(forward, strike, time, rate, sigma);
        let call = call_price(&params);
        let put = put_price(&params);
        let discount = params.discount_factor();

        let parity = call - put;
        let expected = discount * (forward - strike);

        assert!((parity - expected).abs() < NUMERICAL_TOLERANCE);
    }

    #[test]
    fn test_atm_option() {
        // ATM option test
        let forward = 100.0;
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let sigma = 0.2;

        let params = Black76Params::new(forward, strike, time, rate, sigma);
        let call = call_price(&params);
        let put = put_price(&params);

        // For ATM options, call and put should be approximately equal
        // when adjusted for the discount factor
        assert!(call > 0.0);
        assert!(put > 0.0);

        // Put-call parity check
        let _discount = params.discount_factor();
        assert!((call - put).abs() < NUMERICAL_TOLERANCE);
    }

    #[test]
    fn test_deep_itm_call() {
        // Deep ITM call should be approximately F - K (discounted)
        let forward = 150.0;
        let strike = 100.0;
        let time = 0.01; // Short time to maturity
        let rate = 0.05;
        let sigma = 0.2;

        let params = Black76Params::new(forward, strike, time, rate, sigma);
        let call = call_price(&params);
        let discount = params.discount_factor();
        let intrinsic = discount * (forward - strike);

        assert!((call - intrinsic).abs() < 0.01); // Small time value
    }

    #[test]
    fn test_deep_otm_call() {
        // Deep OTM call should be approximately 0
        let forward = 50.0;
        let strike = 100.0;
        let time = 0.01; // Short time to maturity
        let rate = 0.05;
        let sigma = 0.2;

        let params = Black76Params::new(forward, strike, time, rate, sigma);
        let call = call_price(&params);

        assert!(call < 0.001); // Very small value
    }

    // Commented out until batch functions are reimplemented
    // #[test]
    // fn test_batch_processing() {
    //     let forwards = vec![90.0, 95.0, 100.0, 105.0, 110.0];
    //     let strike = 100.0;
    //     let time = 1.0;
    //     let rate = 0.05;
    //     let sigma = 0.2;
    //
    //     let batch_results = call_price_batch(&forwards, strike, time, rate, sigma);
    //
    //     assert_eq!(batch_results.len(), forwards.len());
    //
    //     // Verify each result individually
    //     for (i, &forward) in forwards.iter().enumerate() {
    //         let params = Black76Params::new(forward, strike, time, rate, sigma);
    //         let expected = call_price(&params);
    //         assert!((batch_results[i] - expected).abs() < NUMERICAL_TOLERANCE);
    //     }
    // }

    #[test]
    fn test_boundary_conditions() {
        // Test with very small volatility
        let params = Black76Params::new(100.0, 100.0, 1.0, 0.05, 0.001);
        let call = call_price(&params);
        assert!(call.is_finite());

        // Test with very large volatility
        let params = Black76Params::new(100.0, 100.0, 1.0, 0.05, 5.0);
        let call = call_price(&params);
        assert!(call.is_finite());

        // Test with very short time
        let params = Black76Params::new(100.0, 100.0, 1.0 / 365.0, 0.05, 0.2);
        let call = call_price(&params);
        assert!(call.is_finite());
    }
}
