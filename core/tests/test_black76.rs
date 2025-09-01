//! Unit tests for Black76 model

use approx::assert_relative_eq;
use quantforge_core::models::black76::Black76;
use quantforge_core::traits::OptionModel;

const TOLERANCE: f64 = 1e-6;

#[test]
fn test_call_price_atm() {
    let model = Black76;
    // For Black76, we use forward price instead of spot
    let f = 100.0;
    let price = model.call_price(f, 100.0, 1.0, 0.05, 0.2).unwrap();

    // ATM call should be around 7.58 for these parameters
    assert_relative_eq!(price, 7.577, epsilon = 0.01);
    assert!(price > 0.0);
    assert!(price < f);
}

#[test]
fn test_call_price_itm() {
    let model = Black76;
    let f = 110.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let sigma = 0.2;

    let price = model.call_price(f, k, t, r, sigma).unwrap();
    let discounted_intrinsic = (f - k) * (-r * t).exp();

    assert!(price > discounted_intrinsic);
    assert!(price < f * (-r * t).exp());
}

#[test]
fn test_call_price_otm() {
    let model = Black76;
    let price = model.call_price(90.0, 100.0, 1.0, 0.05, 0.2).unwrap();

    assert!(price > 0.0);
    assert!(price < 10.0);
}

#[test]
fn test_put_price_atm() {
    let model = Black76;
    let price = model.put_price(100.0, 100.0, 1.0, 0.05, 0.2).unwrap();

    // ATM put should be around 7.58 for these parameters (same as call due to forward neutrality)
    assert_relative_eq!(price, 7.577, epsilon = 0.01);
    assert!(price > 0.0);
    assert!(price < 100.0);
}

#[test]
fn test_put_price_itm() {
    let model = Black76;
    let f = 90.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let sigma = 0.2;

    let price = model.put_price(f, k, t, r, sigma).unwrap();
    let discounted_intrinsic = (k - f) * (-r * t).exp();

    assert!(price > discounted_intrinsic);
    assert!(price < k * (-r * t).exp());
}

#[test]
fn test_put_price_otm() {
    let model = Black76;
    let price = model.put_price(110.0, 100.0, 1.0, 0.05, 0.2).unwrap();

    assert!(price > 0.0);
    assert!(price < 10.0);
}

#[test]
fn test_put_call_parity() {
    let model = Black76;
    let f = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let sigma = 0.2;

    let call = model.call_price(f, k, t, r, sigma).unwrap();
    let put = model.put_price(f, k, t, r, sigma).unwrap();

    // Put-Call parity for Black76: C - P = exp(-r*t) * (F - K)
    let lhs = call - put;
    let rhs = (-r * t).exp() * (f - k);

    assert_relative_eq!(lhs, rhs, epsilon = TOLERANCE);
}

#[test]
fn test_greeks_call() {
    let model = Black76;
    let greeks = model.greeks(100.0, 100.0, 1.0, 0.05, 0.2, true).unwrap();

    // Delta for ATM call should be around 0.5 (discounted)
    assert!(greeks.delta > 0.4 && greeks.delta < 0.6);

    // Gamma should be positive
    assert!(greeks.gamma > 0.0);

    // Vega should be positive
    assert!(greeks.vega > 0.0);

    // Theta should be negative for call
    assert!(greeks.theta < 0.0);

    // Rho for Black76 is different from Black-Scholes
    // It can be positive or negative depending on moneyness
}

#[test]
fn test_greeks_put() {
    let model = Black76;
    let greeks = model.greeks(100.0, 100.0, 1.0, 0.05, 0.2, false).unwrap();

    // Delta for ATM put should be around -0.5 (discounted)
    assert!(greeks.delta > -0.6 && greeks.delta < -0.4);

    // Gamma should be positive (same as call)
    assert!(greeks.gamma > 0.0);

    // Vega should be positive (same as call)
    assert!(greeks.vega > 0.0);

    // Theta should be negative
    assert!(greeks.theta < 0.0);
}

#[test]
fn test_implied_volatility_call() {
    let model = Black76;
    let f = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let sigma_true = 0.2;

    // Calculate price with known volatility
    let price = model.call_price(f, k, t, r, sigma_true).unwrap();

    // Recover volatility from price
    let iv = model.implied_volatility(price, f, k, t, r, true).unwrap();

    assert_relative_eq!(iv, sigma_true, epsilon = 1e-4);
}

#[test]
fn test_implied_volatility_put() {
    let model = Black76;
    let f = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let sigma_true = 0.2;

    // Calculate price with known volatility
    let price = model.put_price(f, k, t, r, sigma_true).unwrap();

    // Recover volatility from price
    let iv = model.implied_volatility(price, f, k, t, r, false).unwrap();

    assert_relative_eq!(iv, sigma_true, epsilon = 1e-4);
}

#[test]
fn test_invalid_inputs() {
    let model = Black76;

    // Negative forward price
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
fn test_extreme_values() {
    let model = Black76;

    // Very short time to expiry
    let price = model.call_price(105.0, 100.0, 0.001, 0.05, 0.2).unwrap();
    let expected = 5.0 * (-0.05_f64 * 0.001).exp();
    assert_relative_eq!(price, expected, epsilon = 0.1);

    // Very long time to expiry with high discount
    let price = model.call_price(100.0, 100.0, 10.0, 0.05, 0.2).unwrap();
    assert!(price > 10.0 && price < 40.0);

    // Very high volatility
    let price = model.call_price(100.0, 100.0, 1.0, 0.05, 1.0).unwrap();
    assert!(price > 20.0 && price < 40.0);

    // Very low volatility
    let price = model.call_price(110.0, 100.0, 1.0, 0.05, 0.01).unwrap();
    let expected = (110.0 - 100.0) * (-0.05_f64).exp();
    assert_relative_eq!(price, expected, epsilon = 0.1);
}

#[test]
fn test_forward_vs_spot_relationship() {
    let model = Black76;

    // When forward equals spot * exp(r*t), Black76 and Black-Scholes should give similar results
    let s = 100.0;
    let r = 0.05;
    let t = 1.0;
    let rt_product: f64 = r * t;
    let f = s * rt_product.exp(); // Forward price from spot
    let k = 100.0;
    let sigma = 0.2;

    let price = model.call_price(f, k, t, r, sigma).unwrap();

    // This should be close to Black-Scholes price
    // Expected around 12.3 for these parameters
    assert!(price > 10.0 && price < 15.0);
}
