//! Merton model pricing functions for dividend-paying assets.

use crate::math::distributions::norm_cdf;

/// Calculate the d1 parameter for the Merton model.
/// d1 = (ln(S/K) + (r - q + σ²/2)T) / (σ√T)
#[inline(always)]
pub fn calculate_d1(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    if t <= 0.0 {
        // At expiry, handle based on moneyness
        return if s > k {
            f64::INFINITY
        } else if s < k {
            f64::NEG_INFINITY
        } else {
            0.0
        };
    }

    let sqrt_t = t.sqrt();
    let sigma_sqrt_t = sigma * sqrt_t;

    ((s / k).ln() + (r - q + 0.5 * sigma * sigma) * t) / sigma_sqrt_t
}

/// Calculate the d2 parameter for the Merton model.
/// d2 = d1 - σ√T
#[inline(always)]
pub fn calculate_d2(d1: f64, t: f64, sigma: f64) -> f64 {
    if t <= 0.0 {
        return d1;
    }
    d1 - sigma * t.sqrt()
}

/// Calculate the call option price using the Merton model.
///
/// # Arguments
/// * `s` - Spot price
/// * `k` - Strike price  
/// * `t` - Time to maturity (years)
/// * `r` - Risk-free rate
/// * `q` - Dividend yield
/// * `sigma` - Volatility
///
/// # Formula
/// Call = S * e^(-qT) * N(d1) - K * e^(-rT) * N(d2)
pub fn call_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    // Handle special cases
    if t <= 0.0 {
        return (s - k).max(0.0);
    }

    if s <= 0.0 || k <= 0.0 || sigma <= 0.0 {
        return 0.0;
    }

    // Calculate d1 and d2
    let d1 = calculate_d1(s, k, t, r, q, sigma);
    let d2 = calculate_d2(d1, t, sigma);

    // Calculate discount factors
    let exp_neg_qt = (-q * t).exp();
    let exp_neg_rt = (-r * t).exp();

    // Merton call formula
    (s * exp_neg_qt * norm_cdf(d1) - k * exp_neg_rt * norm_cdf(d2)).max(0.0)
}

/// Calculate the put option price using the Merton model.
///
/// # Arguments
/// * `s` - Spot price
/// * `k` - Strike price
/// * `t` - Time to maturity (years)
/// * `r` - Risk-free rate
/// * `q` - Dividend yield
/// * `sigma` - Volatility
///
/// # Formula
/// Put = K * e^(-rT) * N(-d2) - S * e^(-qT) * N(-d1)
pub fn put_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    // Handle special cases
    if t <= 0.0 {
        return (k - s).max(0.0);
    }

    if s <= 0.0 || k <= 0.0 || sigma <= 0.0 {
        return if s <= 0.0 { k } else { 0.0 };
    }

    // Calculate d1 and d2
    let d1 = calculate_d1(s, k, t, r, q, sigma);
    let d2 = calculate_d2(d1, t, sigma);

    // Calculate discount factors
    let exp_neg_qt = (-q * t).exp();
    let exp_neg_rt = (-r * t).exp();

    // Merton put formula
    (k * exp_neg_rt * norm_cdf(-d2) - s * exp_neg_qt * norm_cdf(-d1)).max(0.0)
}

// Batch functions removed - will be reimplemented with full array support

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    const TEST_TOLERANCE: f64 = 1e-6;

    #[test]
    fn test_merton_reduces_to_black_scholes() {
        // When q=0, Merton should equal Black-Scholes
        let s = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let q = 0.0; // No dividend
        let sigma = 0.20;

        let merton_call = call_price(s, k, t, r, q, sigma);
        let merton_put = put_price(s, k, t, r, q, sigma);

        // Compare with Black-Scholes values (calculated separately)
        let bs_call = 10.450583572185565;
        let bs_put = 5.573526022256971;

        assert_relative_eq!(merton_call, bs_call, epsilon = TEST_TOLERANCE);
        assert_relative_eq!(merton_put, bs_put, epsilon = TEST_TOLERANCE);
    }

    #[test]
    fn test_put_call_parity() {
        // C - P = S*exp(-q*T) - K*exp(-r*T)
        let s = 100.0;
        let k = 110.0;
        let t = 0.5;
        let r = 0.05;
        let q = 0.03;
        let sigma = 0.25;

        let call = call_price(s, k, t, r, q, sigma);
        let put = put_price(s, k, t, r, q, sigma);

        let expected = s * (-q * t).exp() - k * (-r * t).exp();
        let actual = call - put;

        assert_relative_eq!(actual, expected, epsilon = 1e-10);
    }

    #[test]
    fn test_dividend_effect() {
        // Higher dividend should decrease call value and increase put value
        let s = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let sigma = 0.20;

        let call_no_div = call_price(s, k, t, r, 0.0, sigma);
        let call_with_div = call_price(s, k, t, r, 0.03, sigma);

        let put_no_div = put_price(s, k, t, r, 0.0, sigma);
        let put_with_div = put_price(s, k, t, r, 0.03, sigma);

        assert!(call_with_div < call_no_div);
        assert!(put_with_div > put_no_div);
    }

    // Commented out until batch functions are reimplemented
    // #[test]
    // fn test_batch_consistency() {
    //     let spots = vec![90.0, 95.0, 100.0, 105.0, 110.0];
    //     let k = 100.0;
    //     let t = 0.25;
    //     let r = 0.05;
    //     let q = 0.02;
    //     let sigma = 0.30;
    //
    //     let batch_calls = call_price_batch(&spots, k, t, r, q, sigma);
    //     let batch_puts = put_price_batch(&spots, k, t, r, q, sigma);
    //
    //     for (i, &s) in spots.iter().enumerate() {
    //         let single_call = call_price(s, k, t, r, q, sigma);
    //         let single_put = put_price(s, k, t, r, q, sigma);
    //
    //         assert_relative_eq!(batch_calls[i], single_call, epsilon = TEST_TOLERANCE);
    //         assert_relative_eq!(batch_puts[i], single_put, epsilon = TEST_TOLERANCE);
    //     }
    // }

    // Commented out until batch functions are reimplemented
    // #[test]
    // fn test_batch_q_consistency() {
    //     let s = 100.0;
    //     let k = 100.0;
    //     let t = 0.5;
    //     let r = 0.05;
    //     let qs = vec![0.0, 0.01, 0.02, 0.03, 0.04];
    //     let sigma = 0.25;
    //
    //     let batch_calls = call_price_batch_q(s, k, t, r, &qs, sigma);
    //     let batch_puts = put_price_batch_q(s, k, t, r, &qs, sigma);
    //
    //     for (i, &q) in qs.iter().enumerate() {
    //         let single_call = call_price(s, k, t, r, q, sigma);
    //         let single_put = put_price(s, k, t, r, q, sigma);
    //
    //         assert_relative_eq!(batch_calls[i], single_call, epsilon = TEST_TOLERANCE);
    //         assert_relative_eq!(batch_puts[i], single_put, epsilon = TEST_TOLERANCE);
    //     }
    // }
}
