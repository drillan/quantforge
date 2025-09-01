//! Unit tests for Black-Scholes model

use approx::assert_relative_eq;
use quantforge_core::models::black_scholes::BlackScholes;
use quantforge_core::traits::OptionModel;

const TOLERANCE: f64 = 1e-6;

#[test]
fn test_call_price_atm() {
    let model = BlackScholes;
    let price = model.call_price(100.0, 100.0, 1.0, 0.05, 0.2).unwrap();

    // ATM call with these parameters should be around 10.45
    assert_relative_eq!(price, 10.4505835, epsilon = 0.01);
    assert!(price > 0.0);
    assert!(price < 100.0);
}

#[test]
fn test_call_price_itm() {
    let model = BlackScholes;
    let price = model.call_price(110.0, 100.0, 1.0, 0.05, 0.2).unwrap();

    let intrinsic = 110.0 - 100.0 * (-0.05_f64).exp();
    assert!(price > intrinsic);
    assert!(price < 110.0);
}

#[test]
fn test_call_price_otm() {
    let model = BlackScholes;
    let price = model.call_price(90.0, 100.0, 1.0, 0.05, 0.2).unwrap();

    assert!(price > 0.0);
    assert!(price < 10.0);
}

#[test]
fn test_call_price_deep_itm() {
    let model = BlackScholes;
    let price = model.call_price(200.0, 100.0, 1.0, 0.05, 0.2).unwrap();

    let intrinsic = 200.0 - 100.0 * (-0.05_f64).exp();
    assert_relative_eq!(price, intrinsic, epsilon = 1.0);
}

#[test]
fn test_call_price_deep_otm() {
    let model = BlackScholes;
    let price = model.call_price(50.0, 100.0, 1.0, 0.05, 0.2).unwrap();

    assert!(price < 0.01);
}

#[test]
fn test_put_price_atm() {
    let model = BlackScholes;
    let price = model.put_price(100.0, 100.0, 1.0, 0.05, 0.2).unwrap();

    // ATM put with these parameters should be around 5.57
    assert_relative_eq!(price, 5.5737705, epsilon = 0.01);
    assert!(price > 0.0);
    assert!(price < 100.0);
}

#[test]
fn test_put_price_itm() {
    let model = BlackScholes;
    let price = model.put_price(90.0, 100.0, 1.0, 0.05, 0.2).unwrap();

    let intrinsic = 100.0 * (-0.05_f64).exp() - 90.0;
    assert!(price > intrinsic);
    assert!(price < 100.0);
}

#[test]
fn test_put_price_otm() {
    let model = BlackScholes;
    let price = model.put_price(110.0, 100.0, 1.0, 0.05, 0.2).unwrap();

    assert!(price > 0.0);
    assert!(price < 10.0);
}

#[test]
fn test_put_call_parity() {
    let model = BlackScholes;
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let sigma = 0.2;

    let call = model.call_price(s, k, t, r, sigma).unwrap();
    let put = model.put_price(s, k, t, r, sigma).unwrap();

    // Put-Call parity: C - P = S - K * exp(-r*t)
    let lhs = call - put;
    let rhs = s - k * (-r * t).exp();

    assert_relative_eq!(lhs, rhs, epsilon = TOLERANCE);
}

#[test]
fn test_greeks_call() {
    let model = BlackScholes;
    let greeks = model.greeks(100.0, 100.0, 1.0, 0.05, 0.2, true).unwrap();

    // Delta for ATM call should be around 0.64
    assert!(greeks.delta > 0.5 && greeks.delta < 0.7);

    // Gamma should be positive
    assert!(greeks.gamma > 0.0);

    // Vega should be positive
    assert!(greeks.vega > 0.0);

    // Theta should be negative for call
    assert!(greeks.theta < 0.0);

    // Rho should be positive for call
    assert!(greeks.rho > 0.0);
}

#[test]
fn test_greeks_put() {
    let model = BlackScholes;
    let greeks = model.greeks(100.0, 100.0, 1.0, 0.05, 0.2, false).unwrap();

    // Delta for ATM put should be around -0.36
    assert!(greeks.delta > -0.5 && greeks.delta < -0.3);

    // Gamma should be positive (same as call)
    assert!(greeks.gamma > 0.0);

    // Vega should be positive (same as call)
    assert!(greeks.vega > 0.0);

    // Theta for put can be negative or positive depending on parameters
    // For ATM put with positive rate, theta is usually negative
    assert!(greeks.theta < 0.0);

    // Rho should be negative for put
    assert!(greeks.rho < 0.0);
}

#[test]
fn test_implied_volatility_call() {
    let model = BlackScholes;
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let sigma_true = 0.2;

    // Calculate price with known volatility
    let price = model.call_price(s, k, t, r, sigma_true).unwrap();

    // Recover volatility from price
    let iv = model.implied_volatility(price, s, k, t, r, true).unwrap();

    assert_relative_eq!(iv, sigma_true, epsilon = 1e-4);
}

#[test]
fn test_implied_volatility_put() {
    let model = BlackScholes;
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let sigma_true = 0.2;

    // Calculate price with known volatility
    let price = model.put_price(s, k, t, r, sigma_true).unwrap();

    // Recover volatility from price
    let iv = model.implied_volatility(price, s, k, t, r, false).unwrap();

    assert_relative_eq!(iv, sigma_true, epsilon = 1e-4);
}

#[test]
fn test_invalid_inputs() {
    let model = BlackScholes;

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
fn test_extreme_values() {
    let model = BlackScholes;

    // Very short time to expiry
    let price = model.call_price(105.0, 100.0, 0.001, 0.05, 0.2).unwrap();
    assert_relative_eq!(price, 5.0, epsilon = 0.1);

    // Very long time to expiry
    let price = model.call_price(100.0, 100.0, 10.0, 0.05, 0.2).unwrap();
    assert!(price > 30.0 && price < 70.0);

    // Very high volatility
    let price = model.call_price(100.0, 100.0, 1.0, 0.05, 1.0).unwrap();
    assert!(price > 30.0 && price < 50.0);

    // Very low volatility
    let price = model.call_price(110.0, 100.0, 1.0, 0.05, 0.01).unwrap();
    let intrinsic = 110.0 - 100.0 * (-0.05_f64).exp();
    assert_relative_eq!(price, intrinsic, epsilon = 0.1);
}
