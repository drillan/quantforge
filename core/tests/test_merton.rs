//! Unit tests for Merton model (dividend-adjusted Black-Scholes)

use approx::assert_relative_eq;
use quantforge_core::models::merton::Merton;
use quantforge_core::traits::OptionModel;

const TOLERANCE: f64 = 1e-6;

#[test]
fn test_call_price_no_dividend() {
    // Using trait implementation (defaults to q=0)
    let model = Merton;
    let price = model.call_price(100.0, 100.0, 1.0, 0.05, 0.2).unwrap();

    // Without dividend, should match Black-Scholes
    // ATM call with these parameters should be around 10.45
    assert_relative_eq!(price, 10.4505835, epsilon = 0.01);
    assert!(price > 0.0);
    assert!(price < 100.0);
}

#[test]
fn test_call_price_with_dividend() {
    // Using static method with dividend
    let price = Merton::call_price_merton(100.0, 100.0, 1.0, 0.05, 0.02, 0.2).unwrap();

    // With dividend, call price should be lower than without
    let no_div_price = Merton::call_price_merton(100.0, 100.0, 1.0, 0.05, 0.0, 0.2).unwrap();

    assert!(price < no_div_price);
    assert!(price > 0.0);
}

#[test]
fn test_put_price_no_dividend() {
    // Using trait implementation (defaults to q=0)
    let model = Merton;
    let price = model.put_price(100.0, 100.0, 1.0, 0.05, 0.2).unwrap();

    // Without dividend, should match Black-Scholes
    // ATM put with these parameters should be around 5.57
    assert_relative_eq!(price, 5.5737705, epsilon = 0.01);
    assert!(price > 0.0);
    assert!(price < 100.0);
}

#[test]
fn test_put_price_with_dividend() {
    // Using static method with dividend
    let price = Merton::put_price_merton(100.0, 100.0, 1.0, 0.05, 0.02, 0.2).unwrap();

    // With dividend, put price should be higher than without
    let no_div_price = Merton::put_price_merton(100.0, 100.0, 1.0, 0.05, 0.0, 0.2).unwrap();

    assert!(price > no_div_price);
    assert!(price > 0.0);
}

#[test]
fn test_put_call_parity_with_dividend() {
    let q = 0.03; // 3% dividend yield
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let sigma = 0.2;

    let call = Merton::call_price_merton(s, k, t, r, q, sigma).unwrap();
    let put = Merton::put_price_merton(s, k, t, r, q, sigma).unwrap();

    // Put-Call parity with dividends: C - P = S * exp(-q*t) - K * exp(-r*t)
    let lhs = call - put;
    let rhs = s * (-q * t).exp() - k * (-r * t).exp();

    assert_relative_eq!(lhs, rhs, epsilon = TOLERANCE);
}

#[test]
fn test_greeks_call_with_dividend() {
    let greeks = Merton::greeks_merton(100.0, 100.0, 1.0, 0.05, 0.02, 0.2, true).unwrap();

    // Delta should be positive but less than no-dividend case
    assert!(greeks.delta > 0.0 && greeks.delta < 1.0);

    // Gamma should be positive
    assert!(greeks.gamma > 0.0);

    // Vega should be positive
    assert!(greeks.vega > 0.0);

    // Theta should be negative for call
    assert!(greeks.theta < 0.0);

    // Rho should be positive for call
    assert!(greeks.rho > 0.0);

    // Dividend rho should be negative for call
    assert!(greeks.dividend_rho.is_some());
    assert!(greeks.dividend_rho.unwrap() < 0.0);
}

#[test]
fn test_greeks_put_with_dividend() {
    let greeks = Merton::greeks_merton(100.0, 100.0, 1.0, 0.05, 0.02, 0.2, false).unwrap();

    // Delta should be negative
    assert!(greeks.delta < 0.0 && greeks.delta > -1.0);

    // Gamma should be positive (same as call)
    assert!(greeks.gamma > 0.0);

    // Vega should be positive (same as call)
    assert!(greeks.vega > 0.0);

    // Theta for put with dividend
    // Can be positive or negative depending on parameters

    // Rho should be negative for put
    assert!(greeks.rho < 0.0);

    // Dividend rho should be positive for put
    assert!(greeks.dividend_rho.is_some());
    assert!(greeks.dividend_rho.unwrap() > 0.0);
}

#[test]
fn test_implied_volatility_call_with_dividend() {
    let q = 0.02;
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let sigma_true = 0.2;

    // Calculate price with known volatility
    let price = Merton::call_price_merton(s, k, t, r, q, sigma_true).unwrap();

    // Recover volatility from price
    let iv = Merton::implied_volatility_merton(price, s, k, t, r, q, true).unwrap();

    assert_relative_eq!(iv, sigma_true, epsilon = 1e-4);
}

#[test]
fn test_implied_volatility_put_with_dividend() {
    let q = 0.02;
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let sigma_true = 0.2;

    // Calculate price with known volatility
    let price = Merton::put_price_merton(s, k, t, r, q, sigma_true).unwrap();

    // Recover volatility from price
    let iv = Merton::implied_volatility_merton(price, s, k, t, r, q, false).unwrap();

    assert_relative_eq!(iv, sigma_true, epsilon = 1e-4);
}

#[test]
fn test_high_dividend_effect() {
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let sigma = 0.2;

    let call_low = Merton::call_price_merton(s, k, t, r, 0.01, sigma).unwrap(); // 1% dividend
    let call_high = Merton::call_price_merton(s, k, t, r, 0.10, sigma).unwrap(); // 10% dividend

    let put_low = Merton::put_price_merton(s, k, t, r, 0.01, sigma).unwrap();
    let put_high = Merton::put_price_merton(s, k, t, r, 0.10, sigma).unwrap();

    // Higher dividend should decrease call value
    assert!(call_high < call_low);

    // Higher dividend should increase put value
    assert!(put_high > put_low);
}

#[test]
fn test_invalid_inputs() {
    let model = Merton;

    // Negative spot price
    assert!(model.call_price(-100.0, 100.0, 1.0, 0.05, 0.2).is_err());

    // Negative strike
    assert!(model.call_price(100.0, -100.0, 1.0, 0.05, 0.2).is_err());

    // Negative time
    assert!(model.call_price(100.0, 100.0, -1.0, 0.05, 0.2).is_err());

    // Negative volatility
    assert!(model.call_price(100.0, 100.0, 1.0, 0.05, -0.2).is_err());

    // Zero volatility
    assert!(model.call_price(100.0, 100.0, 1.0, 0.05, 0.0).is_err());
}

#[test]
fn test_extreme_dividend_values() {
    // Very high dividend (50% yield)
    let price = Merton::call_price_merton(100.0, 100.0, 1.0, 0.05, 0.5, 0.2).unwrap();

    // Call should be worth very little with such high dividend
    assert!(price < 2.0);

    // Put should be worth more
    let put_price = Merton::put_price_merton(100.0, 100.0, 1.0, 0.05, 0.5, 0.2).unwrap();
    assert!(put_price > 30.0);
}

#[test]
fn test_dividend_adjustment_formula() {
    // Test that Merton model correctly adjusts spot price
    let q = 0.03;
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let sigma = 0.2;

    // The model should effectively use S * exp(-q*t) as adjusted spot
    let qt_product: f64 = q * t;
    let adjusted_spot = s * (-qt_product).exp();

    // Call price should be consistent with this adjustment
    let call = Merton::call_price_merton(s, k, t, r, q, sigma).unwrap();

    // Create a no-dividend model and price with adjusted spot
    let model = Merton;
    let expected_call = model.call_price(adjusted_spot, k, t, r, sigma).unwrap();

    // These should be approximately equal
    assert_relative_eq!(call, expected_call, epsilon = 0.01);
}
