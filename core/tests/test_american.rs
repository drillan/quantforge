//! Tests for American option pricing model

use approx::assert_relative_eq;
use quantforge_core::models::American;

const TOLERANCE: f64 = 1e-3;

#[test]
fn test_american_call_no_dividend() {
    // When q=0, American call equals European call
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let q = 0.0;
    let sigma = 0.2;

    let price = American::call_price_american(s, k, t, r, q, sigma).unwrap();
    
    // Expected value from Black-Scholes (European)
    // For ATM option: approximately 10.45
    assert_relative_eq!(price, 10.45, epsilon = 0.1);
}

#[test]
fn test_american_call_with_dividend() {
    // American call with dividend should have early exercise premium
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let q = 0.02;  // 2% dividend yield
    let sigma = 0.2;

    let price = American::call_price_american(s, k, t, r, q, sigma).unwrap();
    
    // Expected value from reference implementation
    // Should be slightly higher than European due to early exercise
    assert!(price > 8.0 && price < 10.0);
}

#[test]
fn test_american_put_no_dividend() {
    // American put should be worth more than European put even without dividend
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let q = 0.0;
    let sigma = 0.2;

    let price = American::put_price_american(s, k, t, r, q, sigma).unwrap();
    
    // Expected value should be higher than European put (approximately 5.57)
    assert!(price > 5.57);
    assert!(price < 7.0);  // Reasonable upper bound
}

#[test]
fn test_american_put_deep_itm() {
    // Deep ITM American put should be close to intrinsic value
    let s = 80.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let q = 0.0;
    let sigma = 0.2;

    let price = American::put_price_american(s, k, t, r, q, sigma).unwrap();
    let intrinsic = k - s;
    
    // Should be at least intrinsic value
    assert!(price >= intrinsic);
    // But not too much higher for deep ITM
    assert!(price < intrinsic * 1.1);
}

#[test]
fn test_american_call_deep_itm() {
    // Deep ITM American call with dividend
    let s = 120.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let q = 0.03;  // 3% dividend yield
    let sigma = 0.2;

    let price = American::call_price_american(s, k, t, r, q, sigma).unwrap();
    let intrinsic = s - k;
    
    // Should be at least intrinsic value
    assert!(price >= intrinsic);
}

#[test]
fn test_american_put_call_transformation() {
    // Test the put-call transformation used in the implementation
    // P(S,K,T,r,q,σ) = C(K,S,T,q,r,σ)
    let s = 100.0;
    let k = 110.0;
    let t = 0.5;
    let r = 0.05;
    let q = 0.02;
    let sigma = 0.25;

    let put_price = American::put_price_american(s, k, t, r, q, sigma).unwrap();
    let transformed_call = American::call_price_american(k, s, t, q, r, sigma).unwrap();
    
    // The relationship is exact for the BS2002 model
    assert_relative_eq!(put_price, transformed_call, epsilon = TOLERANCE);
}

#[test]
fn test_american_greeks_call() {
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let q = 0.02;
    let sigma = 0.2;

    let greeks = American::greeks_american(s, k, t, r, q, sigma, true).unwrap();
    
    // Delta for ATM call should be around 0.5
    assert!(greeks.delta > 0.4 && greeks.delta < 0.6);
    
    // Gamma should be positive
    assert!(greeks.gamma > 0.0);
    
    // Vega should be positive
    assert!(greeks.vega > 0.0);
    
    // Theta should be negative (time decay)
    assert!(greeks.theta < 0.0);
}

#[test]
fn test_american_greeks_put() {
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let q = 0.02;
    let sigma = 0.2;

    let greeks = American::greeks_american(s, k, t, r, q, sigma, false).unwrap();
    
    // Delta for ATM put should be around -0.5
    assert!(greeks.delta > -0.6 && greeks.delta < -0.4);
    
    // Gamma should be positive
    assert!(greeks.gamma > 0.0);
    
    // Vega should be positive
    assert!(greeks.vega > 0.0);
}

#[test]
fn test_american_price_bounds() {
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let q = 0.02;
    let sigma = 0.2;

    let call_price = American::call_price_american(s, k, t, r, q, sigma).unwrap();
    let put_price = American::put_price_american(s, k, t, r, q, sigma).unwrap();
    
    // Call price bounds
    let call_intrinsic = (s - k).max(0.0);
    assert!(call_price >= call_intrinsic);
    assert!(call_price <= s);
    
    // Put price bounds  
    let put_intrinsic = (k - s).max(0.0);
    assert!(put_price >= put_intrinsic);
    assert!(put_price <= k);
}

#[test]
fn test_american_near_expiry() {
    // Near expiry, option value approaches intrinsic value
    let s = 105.0;
    let k = 100.0;
    let t = 0.001;  // Very small time to expiry (about 8.76 hours)
    let r = 0.05;
    let q = 0.02;
    let sigma = 0.2;

    let call_price = American::call_price_american(s, k, t, r, q, sigma).unwrap();
    let put_price = American::put_price_american(s, k, t, r, q, sigma).unwrap();
    
    // Call is ITM, should be close to intrinsic value
    assert_relative_eq!(call_price, 5.0, epsilon = 0.1);
    // Put is OTM, should be close to 0
    assert!(put_price < 0.1);
}

#[test]
fn test_american_high_volatility() {
    // Test with high volatility
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let q = 0.02;
    let sigma = 0.8;  // High volatility

    let call_price = American::call_price_american(s, k, t, r, q, sigma).unwrap();
    let put_price = American::put_price_american(s, k, t, r, q, sigma).unwrap();
    
    // With high volatility, both options should be valuable
    assert!(call_price > 20.0);
    assert!(put_price > 20.0);
}

#[test]
fn test_american_option_model_trait() {
    // Test the OptionModel trait implementation (assumes q=0)
    use quantforge_core::traits::OptionModel;
    
    let model = American;
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let sigma = 0.2;
    
    let call_price = model.call_price(s, k, t, r, sigma).unwrap();
    let put_price = model.put_price(s, k, t, r, sigma).unwrap();
    
    // Should give valid prices
    assert!(call_price > 0.0);
    assert!(put_price > 0.0);
    
    // Greeks through trait
    let greeks = model.greeks(s, k, t, r, sigma, true).unwrap();
    assert!(greeks.delta > 0.0 && greeks.delta < 1.0);
}

#[test]
fn test_american_exercise_boundary() {
    use quantforge_core::models::american::boundary::calculate_exercise_boundary;
    use quantforge_core::models::american::pricing::AmericanParams;
    
    let params = AmericanParams {
        s: 100.0,
        k: 100.0,
        t: 1.0,
        r: 0.05,
        q: 0.03,
        sigma: 0.2,
    };
    
    // Call boundary with dividend
    let call_boundary = calculate_exercise_boundary(&params, true).unwrap();
    // Should be above strike for call
    assert!(call_boundary > params.k);
    
    // Put boundary
    let put_boundary = calculate_exercise_boundary(&params, false).unwrap();
    // Should be below strike for put
    assert!(put_boundary < params.k);
}