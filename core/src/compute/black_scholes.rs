//! Black-Scholes option pricing model - Arrow-native implementation

use arrow::array::{Float64Array, ArrayRef};
use arrow::compute::kernels::arity::{binary, unary};
use arrow::error::ArrowError;
use std::sync::Arc;

use crate::math::distributions::{norm_cdf_array, norm_pdf_array};
use crate::constants::{MIN_PRICE, MAX_PRICE, MIN_TIME, MAX_TIME, MIN_RATE, MAX_RATE, MIN_VOLATILITY_PRACTICAL, MAX_VOLATILITY};
use crate::error::QuantForgeError;

/// Black-Scholes model implementation using Arrow arrays
pub struct BlackScholes;

impl BlackScholes {
    /// Calculate call option price using Black-Scholes formula
    ///
    /// # Arguments
    /// * `spots` - Current spot prices (S)
    /// * `strikes` - Strike prices (K)
    /// * `times` - Time to maturity in years (T)
    /// * `rates` - Risk-free interest rates (r)
    /// * `sigmas` - Volatilities (σ)
    ///
    /// # Returns
    /// Arrow Float64Array of call option prices
    pub fn call_price(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        // Validate input arrays have same length
        Self::validate_array_lengths(spots, strikes, times, rates, sigmas)?;
        
        // Calculate d1 and d2
        let (d1, d2) = Self::calculate_d1_d2(spots, strikes, times, rates, sigmas)?;
        
        // Calculate call price: C = S * N(d1) - K * exp(-r*T) * N(d2)
        let n_d1 = norm_cdf_array(&d1)?;
        let n_d2 = norm_cdf_array(&d2)?;
        
        // S * N(d1)
        let n_d1_array = n_d1.as_any().downcast_ref::<Float64Array>().unwrap();
        let term1: Float64Array = binary(spots, n_d1_array, |s: f64, n: f64| s * n)?;
        
        // K * exp(-r*T)
        let neg_rt: Float64Array = binary(rates, times, |r: f64, t: f64| -(r * t))?;
        let exp_neg_rt: Float64Array = unary(&neg_rt, |x: f64| x.exp());
        let k_discount: Float64Array = binary(strikes, &exp_neg_rt, |k: f64, e: f64| k * e)?;
        
        // K * exp(-r*T) * N(d2)
        let n_d2_array = n_d2.as_any().downcast_ref::<Float64Array>().unwrap();
        let term2: Float64Array = binary(&k_discount, n_d2_array, |kd: f64, n: f64| kd * n)?;
        
        // Final call price
        let result: Float64Array = binary(&term1, &term2, |t1: f64, t2: f64| t1 - t2)?;
        Ok(Arc::new(result))
    }
    
    /// Calculate put option price using put-call parity
    ///
    /// P = C - S + K * exp(-r*T)
    pub fn put_price(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        // Calculate call price
        let call_prices = Self::call_price(spots, strikes, times, rates, sigmas)?;
        let call_array = call_prices.as_any().downcast_ref::<Float64Array>().unwrap();
        
        // Calculate K * exp(-r*T)
        let neg_rt: Float64Array = binary(rates, times, |r: f64, t: f64| -(r * t))?;
        let exp_neg_rt: Float64Array = unary(&neg_rt, |x: f64| x.exp());
        let k_discount: Float64Array = binary(strikes, &exp_neg_rt, |k: f64, e: f64| k * e)?;
        
        // P = C - S + K * exp(-r*T)
        let c_minus_s: Float64Array = binary(call_array, spots, |c: f64, s: f64| c - s)?;
        let result: Float64Array = binary(&c_minus_s, &k_discount, |cs: f64, kd: f64| cs + kd)?;
        Ok(Arc::new(result))
    }
    
    /// Calculate d1 and d2 parameters
    fn calculate_d1_d2(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<(Float64Array, Float64Array), ArrowError> {
        // ln(S/K)
        let s_over_k: Float64Array = binary(spots, strikes, |s: f64, k: f64| s / k)?;
        let ln_s_over_k: Float64Array = unary(&s_over_k, |x: f64| x.ln());
        
        // (r + 0.5 * sigma^2) * T
        let sigma_squared: Float64Array = unary(sigmas, |s: f64| s * s);
        let half_sigma_squared: Float64Array = unary(&sigma_squared, |s: f64| 0.5 * s);
        let r_plus_half_sigma2: Float64Array = binary(rates, &half_sigma_squared, |r: f64, s: f64| r + s)?;
        let drift_term: Float64Array = binary(&r_plus_half_sigma2, times, |x: f64, t: f64| x * t)?;
        
        // sigma * sqrt(T)
        let sqrt_t: Float64Array = unary(times, |t: f64| t.sqrt());
        let sigma_sqrt_t: Float64Array = binary(sigmas, &sqrt_t, |s: f64, t: f64| s * t)?;
        
        // d1 = (ln(S/K) + (r + 0.5*sigma^2)*T) / (sigma * sqrt(T))
        let numerator: Float64Array = binary(&ln_s_over_k, &drift_term, |a: f64, b: f64| a + b)?;
        let d1: Float64Array = binary(&numerator, &sigma_sqrt_t, |num: f64, den: f64| num / den)?;
        
        // d2 = d1 - sigma * sqrt(T)
        let d2: Float64Array = binary(&d1, &sigma_sqrt_t, |d1_val: f64, s_sqrt_t: f64| d1_val - s_sqrt_t)?;
        
        Ok((d1.clone(), d2.clone()))
    }
    
    /// Validate that all input arrays have the same length
    fn validate_array_lengths(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<(), ArrowError> {
        let len = spots.len();
        
        if strikes.len() != len || times.len() != len || rates.len() != len || sigmas.len() != len {
            return Err(ArrowError::InvalidArgumentError(
                format!("All arrays must have the same length. Got: spots={}, strikes={}, times={}, rates={}, sigmas={}",
                    spots.len(), strikes.len(), times.len(), rates.len(), sigmas.len())
            ));
        }
        
        Ok(())
    }
    
    /// Calculate delta (∂C/∂S)
    pub fn delta(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
        is_call: bool,
    ) -> Result<ArrayRef, ArrowError> {
        let (d1, _) = Self::calculate_d1_d2(spots, strikes, times, rates, sigmas)?;
        
        if is_call {
            // Call delta = N(d1)
            norm_cdf_array(&d1)
        } else {
            // Put delta = N(d1) - 1
            let n_d1 = norm_cdf_array(&d1)?;
            let n_d1_array = n_d1.as_any().downcast_ref::<Float64Array>().unwrap();
            let result: Float64Array = unary(n_d1_array, |n: f64| n - 1.0);
            Ok(Arc::new(result))
        }
    }
    
    /// Calculate gamma (∂²C/∂S²)
    pub fn gamma(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        let (d1, _) = Self::calculate_d1_d2(spots, strikes, times, rates, sigmas)?;
        
        // gamma = φ(d1) / (S * σ * √T)
        let phi_d1 = norm_pdf_array(&d1)?;
        let sigma_sqrt_t: Float64Array = binary(sigmas, times, |s: f64, t: f64| s * t.sqrt())?;
        let s_sigma_sqrt_t: Float64Array = binary(spots, &sigma_sqrt_t, |s: f64, sst: f64| s * sst)?;
        
        let phi_d1_array = phi_d1.as_any().downcast_ref::<Float64Array>().unwrap();
        let result: Float64Array = binary(phi_d1_array, &s_sigma_sqrt_t, |phi: f64, denom: f64| phi / denom)?;
        Ok(Arc::new(result))
    }
    
    /// Calculate vega (∂C/∂σ)
    pub fn vega(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        let (d1, _) = Self::calculate_d1_d2(spots, strikes, times, rates, sigmas)?;
        
        // vega = S * φ(d1) * √T
        let phi_d1 = norm_pdf_array(&d1)?;
        let sqrt_t: Float64Array = unary(times, |t: f64| t.sqrt());
        let s_phi: Float64Array = binary(spots, phi_d1.as_any().downcast_ref::<Float64Array>().unwrap(), |s: f64, phi: f64| s * phi)?;
        
        let result: Float64Array = binary(&s_phi, &sqrt_t, |sp: f64, st: f64| sp * st)?;
        Ok(Arc::new(result))
    }
    
    /// Calculate theta (∂C/∂T)
    pub fn theta(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
        is_call: bool,
    ) -> Result<ArrayRef, ArrowError> {
        let (d1, d2) = Self::calculate_d1_d2(spots, strikes, times, rates, sigmas)?;
        
        // Common term: -(S * φ(d1) * σ) / (2 * √T)
        let phi_d1 = norm_pdf_array(&d1)?;
        let s_phi_sigma: Float64Array = binary(spots, sigmas, |s: f64, sig: f64| s * sig)?;
        let s_phi_sigma: Float64Array = binary(&s_phi_sigma, phi_d1.as_any().downcast_ref::<Float64Array>().unwrap(), |x: f64, phi: f64| x * phi)?;
        let two_sqrt_t: Float64Array = unary(times, |t: f64| 2.0 * t.sqrt());
        let common_term: Float64Array = binary(&s_phi_sigma, &two_sqrt_t, |num: f64, den: f64| -num / den)?;
        
        if is_call {
            // Call theta = common_term - r * K * exp(-r*T) * N(d2)
            let n_d2 = norm_cdf_array(&d2)?;
            let neg_rt: Float64Array = binary(rates, times, |r: f64, t: f64| -(r * t))?;
            let exp_neg_rt: Float64Array = unary(&neg_rt, |x: f64| x.exp());
            let r_k_exp: Float64Array = binary(rates, strikes, |r: f64, k: f64| r * k)?;
            let r_k_exp: Float64Array = binary(&r_k_exp, &exp_neg_rt, |x: f64, e: f64| x * e)?;
            let n_d2_array = n_d2.as_any().downcast_ref::<Float64Array>().unwrap();
            let second_term: Float64Array = binary(&r_k_exp, n_d2_array, |x: f64, n: f64| -x * n)?;
            
            let result: Float64Array = binary(&common_term, &second_term, |c: f64, s: f64| c + s)?;
            Ok(Arc::new(result))
        } else {
            // Put theta = common_term + r * K * exp(-r*T) * N(-d2)
            let neg_d2: Float64Array = unary(&d2, |x: f64| -x);
            let n_neg_d2 = norm_cdf_array(&neg_d2)?;
            let neg_rt: Float64Array = binary(rates, times, |r: f64, t: f64| -(r * t))?;
            let exp_neg_rt: Float64Array = unary(&neg_rt, |x: f64| x.exp());
            let r_k_exp: Float64Array = binary(rates, strikes, |r: f64, k: f64| r * k)?;
            let r_k_exp: Float64Array = binary(&r_k_exp, &exp_neg_rt, |x: f64, e: f64| x * e)?;
            let n_neg_d2_array = n_neg_d2.as_any().downcast_ref::<Float64Array>().unwrap();
            let second_term: Float64Array = binary(&r_k_exp, n_neg_d2_array, |x: f64, n: f64| x * n)?;
            
            let result: Float64Array = binary(&common_term, &second_term, |c: f64, s: f64| c + s)?;
            Ok(Arc::new(result))
        }
    }
    
    /// Calculate rho (∂C/∂r)
    pub fn rho(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
        is_call: bool,
    ) -> Result<ArrayRef, ArrowError> {
        let (_, d2) = Self::calculate_d1_d2(spots, strikes, times, rates, sigmas)?;
        
        // K * T * exp(-r*T)
        let neg_rt: Float64Array = binary(rates, times, |r: f64, t: f64| -(r * t))?;
        let exp_neg_rt: Float64Array = unary(&neg_rt, |x: f64| x.exp());
        let k_t_exp: Float64Array = binary(strikes, times, |k: f64, t: f64| k * t)?;
        let k_t_exp_discounted: Float64Array = binary(&k_t_exp, &exp_neg_rt, |x: f64, e: f64| x * e)?;
        
        if is_call {
            // Call rho = K * T * exp(-r*T) * N(d2)
            let n_d2 = norm_cdf_array(&d2)?;
            let n_d2_array = n_d2.as_any().downcast_ref::<Float64Array>().unwrap();
            let result: Float64Array = binary(&k_t_exp_discounted, n_d2_array, |x: f64, n: f64| x * n)?;
            Ok(Arc::new(result))
        } else {
            // Put rho = -K * T * exp(-r*T) * N(-d2)
            let neg_d2 = unary(&d2, |x: f64| -x);
            let n_neg_d2 = norm_cdf_array(&neg_d2)?;
            let n_neg_d2_array = n_neg_d2.as_any().downcast_ref::<Float64Array>().unwrap();
            let result: Float64Array = binary(&k_t_exp_discounted, n_neg_d2_array, |x: f64, n: f64| -x * n)?;
            Ok(Arc::new(result))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::PRACTICAL_TOLERANCE;
    
    #[test]
    fn test_call_price() {
        let spots = Float64Array::from(vec![100.0]);
        let strikes = Float64Array::from(vec![100.0]);
        let times = Float64Array::from(vec![1.0]);
        let rates = Float64Array::from(vec![0.05]);
        let sigmas = Float64Array::from(vec![0.2]);
        
        let result = BlackScholes::call_price(&spots, &strikes, &times, &rates, &sigmas).unwrap();
        let prices = result.as_any().downcast_ref::<Float64Array>().unwrap();
        
        // Expected value from standard Black-Scholes
        let expected = 10.4506;
        assert!((prices.value(0) - expected).abs() < PRACTICAL_TOLERANCE);
    }
    
    #[test]
    fn test_put_price() {
        let spots = Float64Array::from(vec![100.0]);
        let strikes = Float64Array::from(vec![100.0]);
        let times = Float64Array::from(vec![1.0]);
        let rates = Float64Array::from(vec![0.05]);
        let sigmas = Float64Array::from(vec![0.2]);
        
        let result = BlackScholes::put_price(&spots, &strikes, &times, &rates, &sigmas).unwrap();
        let prices = result.as_any().downcast_ref::<Float64Array>().unwrap();
        
        // Expected value from put-call parity
        let expected = 5.5735;
        assert!((prices.value(0) - expected).abs() < PRACTICAL_TOLERANCE);
    }
    
    #[test]
    fn test_greeks() {
        let spots = Float64Array::from(vec![100.0]);
        let strikes = Float64Array::from(vec![100.0]);
        let times = Float64Array::from(vec![1.0]);
        let rates = Float64Array::from(vec![0.05]);
        let sigmas = Float64Array::from(vec![0.2]);
        
        // Test delta
        let delta = BlackScholes::delta(&spots, &strikes, &times, &rates, &sigmas, true).unwrap();
        let delta_val = delta.as_any().downcast_ref::<Float64Array>().unwrap().value(0);
        assert!((delta_val - 0.6368).abs() < PRACTICAL_TOLERANCE);
        
        // Test gamma
        let gamma = BlackScholes::gamma(&spots, &strikes, &times, &rates, &sigmas).unwrap();
        let gamma_val = gamma.as_any().downcast_ref::<Float64Array>().unwrap().value(0);
        assert!((gamma_val - 0.0188).abs() < PRACTICAL_TOLERANCE);
        
        // Test vega
        let vega = BlackScholes::vega(&spots, &strikes, &times, &rates, &sigmas).unwrap();
        let vega_val = vega.as_any().downcast_ref::<Float64Array>().unwrap().value(0);
        assert!((vega_val - 37.524).abs() < 0.01);
    }
}