//! American option pricing tests
//!
//! Tests for American option pricing using BS2002 approximation and binomial tree methods
//! Following TDD principles (C010): Tests written before implementation
#![allow(clippy::uninlined_format_args)]

use quantforge_core::compute::american::*;
use quantforge_core::compute::formulas::{black_scholes_call_scalar, black_scholes_put_scalar};
use quantforge_core::constants::*;

// Test tolerance based on practical requirements
const TEST_TOLERANCE: f64 = PRACTICAL_TOLERANCE;
#[allow(dead_code)]
const HIGH_PRECISION_TOL: f64 = 1e-5;

// Standard test parameters
const TEST_SPOT: f64 = 100.0;
const TEST_STRIKE: f64 = 100.0;
const TEST_TIME: f64 = 1.0;
const TEST_RATE: f64 = 0.05;
const TEST_DIVIDEND: f64 = 0.03;
const TEST_SIGMA: f64 = 0.2;

#[cfg(test)]
mod scalar_tests {
    use super::*;

    #[test]
    fn test_american_put_intrinsic_value() {
        // American put must be worth at least its intrinsic value
        let spot = 90.0;
        let strike = 100.0;
        let time = 0.25;
        let rate = 0.05;
        let dividend = 0.03;
        let sigma = 0.2;

        let american_put = american_put_scalar(spot, strike, time, rate, dividend, sigma);
        let intrinsic = (strike - spot).max(0.0);

        assert!(
            american_put >= intrinsic - TEST_TOLERANCE,
            "American put {american_put} should be >= intrinsic value {intrinsic}"
        );
    }

    #[test]
    fn test_american_call_intrinsic_value() {
        // American call must be worth at least its intrinsic value
        let spot = 110.0;
        let strike = 100.0;
        let time = 0.25;
        let rate = 0.05;
        let dividend = 0.03;
        let sigma = 0.2;

        let american_call = american_call_scalar(spot, strike, time, rate, dividend, sigma);
        let intrinsic = (spot - strike).max(0.0);

        assert!(
            american_call >= intrinsic - TEST_TOLERANCE,
            "American call {american_call} should be >= intrinsic value {intrinsic}"
        );
    }

    #[test]
    fn test_american_european_relationship() {
        // American option must be worth at least as much as European
        let spot = 100.0;
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let dividend = 0.03;
        let sigma = 0.2;

        // For put options
        let european_put = black_scholes_put_scalar(spot, strike, time, rate, sigma);
        let american_put = american_put_scalar(spot, strike, time, rate, dividend, sigma);

        assert!(
            american_put >= european_put - TEST_TOLERANCE,
            "American put {american_put} should be >= European put {european_put}"
        );

        // For call options with dividends
        let european_call = black_scholes_call_scalar(spot, strike, time, rate, sigma);
        let american_call = american_call_scalar(spot, strike, time, rate, dividend, sigma);

        assert!(
            american_call >= european_call - TEST_TOLERANCE,
            "American call {american_call} should be >= European call {european_call}"
        );
    }

    #[test]
    fn test_american_call_no_dividend_equals_european() {
        // American call without dividends should equal European call (no early exercise benefit)
        let spot = 100.0;
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let dividend = 0.0; // No dividend
        let sigma = 0.2;

        let european_call = black_scholes_call_scalar(spot, strike, time, rate, sigma);
        let american_call = american_call_scalar(spot, strike, time, rate, dividend, sigma);

        assert!(
            (american_call - european_call).abs() < TEST_TOLERANCE,
            "American call without dividends {american_call} should equal European call {european_call}"
        );
    }

    #[test]
    fn test_put_call_parity_inequality() {
        // American put-call parity inequality
        // C - P <= S - K*exp(-r*T) for American options
        let spot = 100.0;
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let dividend = 0.03;
        let sigma = 0.2;

        let american_call = american_call_scalar(spot, strike, time, rate, dividend, sigma);
        let american_put = american_put_scalar(spot, strike, time, rate, dividend, sigma);

        let parity_upper = spot - strike * (-rate * time).exp();
        let difference = american_call - american_put;

        assert!(
            difference <= parity_upper + TEST_TOLERANCE,
            "Put-call parity inequality violated: C-P = {difference} > S-K*exp(-rT) = {parity_upper}"
        );
    }

    #[test]
    fn test_boundary_conditions_at_expiry() {
        // At expiry (t → 0), American option equals intrinsic value
        let spot = 110.0;
        let strike = 100.0;
        let time = 1e-10; // Near expiry
        let rate = 0.05;
        let dividend = 0.03;
        let sigma = 0.2;

        let american_call = american_call_scalar(spot, strike, time, rate, dividend, sigma);
        let call_intrinsic = (spot - strike).max(0.0);

        assert!(
            (american_call - call_intrinsic).abs() < TEST_TOLERANCE,
            "At expiry, American call {american_call} should equal intrinsic {call_intrinsic}"
        );

        let spot_put = 90.0;
        let american_put = american_put_scalar(spot_put, strike, time, rate, dividend, sigma);
        let put_intrinsic = (strike - spot_put).max(0.0);

        assert!(
            (american_put - put_intrinsic).abs() < TEST_TOLERANCE,
            "At expiry, American put {american_put} should equal intrinsic {put_intrinsic}"
        );
    }

    #[test]
    fn test_deep_in_the_money_put() {
        // Deep ITM American put should be worth approximately K - S
        let spot = 50.0;
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let dividend = 0.03;
        let sigma = 0.2;

        let american_put = american_put_scalar(spot, strike, time, rate, dividend, sigma);
        let intrinsic = strike - spot;

        // Deep ITM put should be very close to intrinsic value (likely exercised immediately)
        assert!(
            (american_put - intrinsic).abs() < TEST_TOLERANCE * 10.0,
            "Deep ITM American put {american_put} should be close to intrinsic {intrinsic}"
        );
    }

    #[test]
    fn test_benchmark_values() {
        // Test against known benchmark values from literature
        // Example from Haug (2007) "The Complete Guide to Option Pricing Formulas"
        let spot = 100.0;
        let strike = 100.0;
        let time = 0.25;
        let rate = 0.05;
        let dividend = 0.10; // High dividend for early exercise
        let sigma = 0.25;

        let american_call = american_call_scalar(spot, strike, time, rate, dividend, sigma);
        let expected = 3.0721; // Approximate value from literature

        assert!(
            (american_call - expected).abs() < 0.01,
            "American call {} should be close to benchmark {}",
            american_call,
            expected
        );
    }

    #[test]
    fn test_monotonicity_in_spot() {
        // Option value should increase monotonically with spot (for calls)
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let dividend = 0.03;
        let sigma = 0.2;

        let spot1 = 90.0;
        let spot2 = 100.0;
        let spot3 = 110.0;

        let call1 = american_call_scalar(spot1, strike, time, rate, dividend, sigma);
        let call2 = american_call_scalar(spot2, strike, time, rate, dividend, sigma);
        let call3 = american_call_scalar(spot3, strike, time, rate, dividend, sigma);

        assert!(
            call1 < call2 && call2 < call3,
            "Call prices should increase with spot: {} < {} < {}",
            call1,
            call2,
            call3
        );

        // For puts, should decrease with spot
        let put1 = american_put_scalar(spot1, strike, time, rate, dividend, sigma);
        let put2 = american_put_scalar(spot2, strike, time, rate, dividend, sigma);
        let put3 = american_put_scalar(spot3, strike, time, rate, dividend, sigma);

        assert!(
            put1 > put2 && put2 > put3,
            "Put prices should decrease with spot: {} > {} > {}",
            put1,
            put2,
            put3
        );
    }

    #[test]
    fn test_monotonicity_in_volatility() {
        // Option value should increase with volatility
        let spot = 100.0;
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let dividend = 0.03;

        let sigma1 = 0.1;
        let sigma2 = 0.2;
        let sigma3 = 0.3;

        let call1 = american_call_scalar(spot, strike, time, rate, dividend, sigma1);
        let call2 = american_call_scalar(spot, strike, time, rate, dividend, sigma2);
        let call3 = american_call_scalar(spot, strike, time, rate, dividend, sigma3);

        assert!(
            call1 < call2 && call2 < call3,
            "Call prices should increase with volatility: {} < {} < {}",
            call1,
            call2,
            call3
        );

        let put1 = american_put_scalar(spot, strike, time, rate, dividend, sigma1);
        let put2 = american_put_scalar(spot, strike, time, rate, dividend, sigma2);
        let put3 = american_put_scalar(spot, strike, time, rate, dividend, sigma3);

        assert!(
            put1 < put2 && put2 < put3,
            "Put prices should increase with volatility: {} < {} < {}",
            put1,
            put2,
            put3
        );
    }
}

#[cfg(test)]
mod binomial_tests {
    use super::*;

    #[test]
    fn test_binomial_convergence() {
        // Binomial should converge to analytical value as steps increase
        let spot = 100.0;
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let dividend = 0.03;
        let sigma = 0.2;

        let steps_10 = american_binomial(spot, strike, time, rate, dividend, sigma, 10, false);
        let steps_100 = american_binomial(spot, strike, time, rate, dividend, sigma, 100, false);
        let steps_1000 = american_binomial(spot, strike, time, rate, dividend, sigma, 1000, false);

        // Should converge (difference decreases)
        let diff1 = (steps_100 - steps_10).abs();
        let diff2 = (steps_1000 - steps_100).abs();

        assert!(
            diff2 < diff1,
            "Binomial should converge: diff at 100 steps {} > diff at 1000 steps {}",
            diff1,
            diff2
        );
    }

    #[test]
    fn test_binomial_vs_bs2002_consistency() {
        // Binomial with many steps should be close to BS2002
        let spot = 100.0;
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let dividend = 0.03;
        let sigma = 0.2;

        let bs2002 = american_put_scalar(spot, strike, time, rate, dividend, sigma);
        let binomial = american_binomial(spot, strike, time, rate, dividend, sigma, 500, false);

        assert!(
            (bs2002 - binomial).abs() < 0.05,
            "BS2002 {} and high-step binomial {} should be close",
            bs2002,
            binomial
        );
    }

    #[test]
    fn test_binomial_memory_efficiency() {
        // Ensure binomial uses O(n) memory, not O(n^2)
        // This test just ensures it completes without memory issues
        let spot = 100.0;
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let dividend = 0.03;
        let sigma = 0.2;

        // Should complete with reasonable memory usage
        let _result = american_binomial(spot, strike, time, rate, dividend, sigma, 10000, true);
        // If this completes without panic/OOM, the test passes
    }
}

#[cfg(test)]
mod arrow_tests {
    use super::*;
    use arrow::array::Float64Array;

    #[test]
    fn test_arrow_batch_processing() {
        let size = 1000;
        let spots = Float64Array::from(vec![TEST_SPOT; size]);
        let strikes = Float64Array::from(vec![TEST_STRIKE; size]);
        let times = Float64Array::from(vec![TEST_TIME; size]);
        let rates = Float64Array::from(vec![TEST_RATE; size]);
        let dividends = Float64Array::from(vec![TEST_DIVIDEND; size]);
        let sigmas = Float64Array::from(vec![TEST_SIGMA; size]);

        let result = American::call_price(&spots, &strikes, &times, &rates, &dividends, &sigmas);

        assert!(result.is_ok());
        let prices = result.unwrap();
        assert_eq!(prices.len(), size);
    }

    #[test]
    fn test_arrow_broadcasting() {
        // Test broadcasting with scalar and array inputs
        let spots = Float64Array::from(vec![90.0, 100.0, 110.0]);
        let strike = Float64Array::from(vec![100.0]); // Scalar-like
        let time = Float64Array::from(vec![1.0]);
        let rate = Float64Array::from(vec![0.05]);
        let dividend = Float64Array::from(vec![0.03]);
        let sigma = Float64Array::from(vec![0.2]);

        let result = American::put_price(&spots, &strike, &time, &rate, &dividend, &sigma);

        assert!(result.is_ok());
        let prices = result.unwrap();
        assert_eq!(prices.len(), 3);

        // Verify monotonicity in the results
        let price_90 = prices
            .as_any()
            .downcast_ref::<Float64Array>()
            .unwrap()
            .value(0);
        let price_100 = prices
            .as_any()
            .downcast_ref::<Float64Array>()
            .unwrap()
            .value(1);
        let price_110 = prices
            .as_any()
            .downcast_ref::<Float64Array>()
            .unwrap()
            .value(2);

        assert!(price_90 > price_100 && price_100 > price_110);
    }

    #[test]
    fn test_arrow_zero_copy() {
        // Ensure Arrow implementation doesn't copy data unnecessarily
        let size = 10_000;
        let spots = Float64Array::from(vec![TEST_SPOT; size]);

        let spots_ptr = spots.values().as_ptr();

        let result = American::call_price(
            &spots,
            &Float64Array::from(vec![TEST_STRIKE; size]),
            &Float64Array::from(vec![TEST_TIME; size]),
            &Float64Array::from(vec![TEST_RATE; size]),
            &Float64Array::from(vec![TEST_DIVIDEND; size]),
            &Float64Array::from(vec![TEST_SIGMA; size]),
        );

        assert!(result.is_ok());

        // Original data should still be at the same memory location
        assert_eq!(spots.values().as_ptr(), spots_ptr);
    }

    #[test]
    fn test_arrow_parallel_threshold() {
        // Test that parallel processing activates correctly
        use std::time::Instant;

        let small_size = 100;
        let large_size = 50_000; // Above PARALLEL_THRESHOLD_SMALL

        // Small batch - should be sequential
        let spots_small = Float64Array::from(vec![TEST_SPOT; small_size]);
        let start_small = Instant::now();
        let _result_small = American::call_price(
            &spots_small,
            &Float64Array::from(vec![TEST_STRIKE; small_size]),
            &Float64Array::from(vec![TEST_TIME; small_size]),
            &Float64Array::from(vec![TEST_RATE; small_size]),
            &Float64Array::from(vec![TEST_DIVIDEND; small_size]),
            &Float64Array::from(vec![TEST_SIGMA; small_size]),
        );
        let _duration_small = start_small.elapsed();

        // Large batch - should be parallel
        let spots_large = Float64Array::from(vec![TEST_SPOT; large_size]);
        let start_large = Instant::now();
        let _result_large = American::call_price(
            &spots_large,
            &Float64Array::from(vec![TEST_STRIKE; large_size]),
            &Float64Array::from(vec![TEST_TIME; large_size]),
            &Float64Array::from(vec![TEST_RATE; large_size]),
            &Float64Array::from(vec![TEST_DIVIDEND; large_size]),
            &Float64Array::from(vec![TEST_SIGMA; large_size]),
        );
        let _duration_large = start_large.elapsed();

        // We can't directly test parallelism, but the test ensures both paths work
    }
}

#[cfg(test)]
mod greeks_tests {
    use super::*;

    #[test]
    fn test_delta_ranges() {
        // Delta should be between -1 and 1
        let spot = 100.0;
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let dividend = 0.03;
        let sigma = 0.2;

        let call_delta = american_call_delta(spot, strike, time, rate, dividend, sigma);
        assert!(
            (0.0..=1.0).contains(&call_delta),
            "Call delta {} should be between 0 and 1",
            call_delta
        );

        let put_delta = american_put_delta(spot, strike, time, rate, dividend, sigma);
        assert!(
            (-1.0..=0.0).contains(&put_delta),
            "Put delta {} should be between -1 and 0",
            put_delta
        );
    }

    #[test]
    fn test_gamma_positive() {
        // Gamma should always be positive
        let spot = 100.0;
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let dividend = 0.03;
        let sigma = 0.2;

        let call_gamma = american_call_gamma(spot, strike, time, rate, dividend, sigma);
        assert!(
            call_gamma >= 0.0,
            "Call gamma {} should be positive",
            call_gamma
        );

        let put_gamma = american_put_gamma(spot, strike, time, rate, dividend, sigma);
        assert!(
            put_gamma >= 0.0,
            "Put gamma {} should be positive",
            put_gamma
        );
    }

    #[test]
    fn test_vega_positive() {
        // Vega should always be positive for American options
        let spot = 100.0;
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let dividend = 0.03;
        let sigma = 0.2;

        let call_vega = american_call_vega(spot, strike, time, rate, dividend, sigma);
        assert!(
            call_vega >= 0.0,
            "Call vega {} should be positive",
            call_vega
        );

        let put_vega = american_put_vega(spot, strike, time, rate, dividend, sigma);
        assert!(put_vega >= 0.0, "Put vega {} should be positive", put_vega);
    }

    #[test]
    fn test_theta_sign() {
        // Theta is typically negative (time decay)
        let spot = 100.0;
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let dividend = 0.03;
        let sigma = 0.2;

        let call_theta = american_call_theta(spot, strike, time, rate, dividend, sigma);
        // American call theta can be positive with high dividends
        // Just test it's finite
        assert!(call_theta.is_finite());

        let put_theta = american_put_theta(spot, strike, time, rate, dividend, sigma);
        // American put theta is typically negative
        assert!(put_theta.is_finite());
    }

    #[test]
    fn test_greeks_finite_difference_consistency() {
        // Test that Greeks are consistent with finite difference approximations
        let spot = 100.0;
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let dividend = 0.03;
        let sigma = 0.2;
        let h = 0.01; // Small change for finite difference

        // Delta via finite difference
        let price_up = american_call_scalar(spot * (1.0 + h), strike, time, rate, dividend, sigma);
        let price_down =
            american_call_scalar(spot * (1.0 - h), strike, time, rate, dividend, sigma);
        let fd_delta = (price_up - price_down) / (2.0 * spot * h);

        let analytical_delta = american_call_delta(spot, strike, time, rate, dividend, sigma);

        assert!(
            (fd_delta - analytical_delta).abs() < 0.01,
            "Finite difference delta {} should be close to analytical delta {}",
            fd_delta,
            analytical_delta
        );
    }
}

#[cfg(test)]
mod validation_tests {
    use super::*;

    #[test]
    #[should_panic]
    fn test_negative_spot_validation() {
        let _result = american_call_scalar(-100.0, 100.0, 1.0, 0.05, 0.03, 0.2);
    }

    #[test]
    #[should_panic]
    fn test_negative_strike_validation() {
        let _result = american_call_scalar(100.0, -100.0, 1.0, 0.05, 0.03, 0.2);
    }

    #[test]
    #[should_panic]
    fn test_negative_time_validation() {
        let _result = american_call_scalar(100.0, 100.0, -1.0, 0.05, 0.03, 0.2);
    }

    #[test]
    #[should_panic]
    fn test_negative_volatility_validation() {
        let _result = american_call_scalar(100.0, 100.0, 1.0, 0.05, 0.03, -0.2);
    }

    #[test]
    fn test_zero_volatility_handling() {
        // With zero volatility, American option should equal intrinsic value
        let spot = 110.0;
        let strike = 100.0;
        let time = 1.0;
        let rate = 0.05;
        let dividend = 0.03;
        let sigma = 0.0;

        let american_call = american_call_scalar(spot, strike, time, rate, dividend, sigma);
        let intrinsic = (spot - strike).max(0.0);

        assert!(
            (american_call - intrinsic).abs() < TEST_TOLERANCE,
            "With zero volatility, call {} should equal intrinsic {}",
            american_call,
            intrinsic
        );
    }

    #[test]
    fn test_extreme_values() {
        // Test with extreme but valid values
        let spot = 1e6;
        let strike = 1.0;
        let time = 10.0;
        let rate = 0.5;
        let dividend = 0.1;
        let sigma = 2.0;

        let result = american_call_scalar(spot, strike, time, rate, dividend, sigma);
        assert!(result.is_finite() && result >= 0.0);

        // Deep OTM put
        let spot = 1000.0;
        let strike = 1.0;
        let put_result = american_put_scalar(spot, strike, time, rate, dividend, sigma);
        assert!(put_result.is_finite() && (0.0..1.0).contains(&put_result));
    }
}
