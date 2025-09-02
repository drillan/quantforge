//! Black76 model for futures options - Arrow-native implementation

use arrow::array::{ArrayRef, Float64Array};
use arrow::error::ArrowError;
use std::sync::Arc;

use crate::constants::get_parallel_threshold;
use crate::math::distributions::norm_cdf;
use super::{get_scalar_or_array_value, validate_broadcast_compatibility};

/// Black76 model implementation using Arrow arrays
pub struct Black76;

impl Black76 {
    /// Calculate call option price for futures
    ///
    /// # Arguments
    /// * `forwards` - Forward prices (F)
    /// * `strikes` - Strike prices (K)
    /// * `times` - Time to maturity in years (T)
    /// * `rates` - Risk-free interest rates (r)
    /// * `sigmas` - Volatilities (σ)
    ///
    /// # Returns
    /// Arrow Float64Array of call option prices
    pub fn call_price(
        forwards: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        // Validate arrays for broadcasting compatibility
        let len = validate_broadcast_compatibility(&[forwards, strikes, times, rates, sigmas])?;
        let mut result = Vec::with_capacity(len);

        if len >= get_parallel_threshold() {
            // Parallel processing for large arrays
            use rayon::prelude::*;

            let results: Vec<f64> = (0..len)
                .into_par_iter()
                .map(|i| {
                    let f = get_scalar_or_array_value(forwards, i);
                    let k = get_scalar_or_array_value(strikes, i);
                    let t = get_scalar_or_array_value(times, i);
                    let r = get_scalar_or_array_value(rates, i);
                    let sigma = get_scalar_or_array_value(sigmas, i);

                    // Black76 formula for call
                    let sqrt_t = t.sqrt();
                    let d1 = ((f / k).ln() + (sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
                    let d2 = d1 - sigma * sqrt_t;

                    (-r * t).exp() * (f * norm_cdf(d1) - k * norm_cdf(d2))
                })
                .collect();

            Ok(Arc::new(Float64Array::from(results)))
        } else {
            // Sequential processing for small arrays
            for i in 0..len {
                let f = get_scalar_or_array_value(forwards, i);
                let k = get_scalar_or_array_value(strikes, i);
                let t = get_scalar_or_array_value(times, i);
                let r = get_scalar_or_array_value(rates, i);
                let sigma = get_scalar_or_array_value(sigmas, i);

                // Black76 formula for call
                let sqrt_t = t.sqrt();
                let d1 = ((f / k).ln() + (sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
                let d2 = d1 - sigma * sqrt_t;

                let call_price = (-r * t).exp() * (f * norm_cdf(d1) - k * norm_cdf(d2));
                result.push(call_price);
            }

            Ok(Arc::new(Float64Array::from(result)))
        }
    }

    /// Calculate put option price for futures
    ///
    /// # Arguments
    /// * `forwards` - Forward prices (F)
    /// * `strikes` - Strike prices (K)
    /// * `times` - Time to maturity in years (T)
    /// * `rates` - Risk-free interest rates (r)
    /// * `sigmas` - Volatilities (σ)
    ///
    /// # Returns
    /// Arrow Float64Array of put option prices
    pub fn put_price(
        forwards: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        // Validate arrays for broadcasting compatibility
        let len = validate_broadcast_compatibility(&[forwards, strikes, times, rates, sigmas])?;
        let mut result = Vec::with_capacity(len);

        if len >= get_parallel_threshold() {
            // Parallel processing for large arrays
            use rayon::prelude::*;

            let results: Vec<f64> = (0..len)
                .into_par_iter()
                .map(|i| {
                    let f = get_scalar_or_array_value(forwards, i);
                    let k = get_scalar_or_array_value(strikes, i);
                    let t = get_scalar_or_array_value(times, i);
                    let r = get_scalar_or_array_value(rates, i);
                    let sigma = get_scalar_or_array_value(sigmas, i);

                    // Black76 formula for put
                    let sqrt_t = t.sqrt();
                    let d1 = ((f / k).ln() + (sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
                    let d2 = d1 - sigma * sqrt_t;

                    (-r * t).exp() * (k * norm_cdf(-d2) - f * norm_cdf(-d1))
                })
                .collect();

            Ok(Arc::new(Float64Array::from(results)))
        } else {
            // Sequential processing for small arrays
            for i in 0..len {
                let f = get_scalar_or_array_value(forwards, i);
                let k = get_scalar_or_array_value(strikes, i);
                let t = get_scalar_or_array_value(times, i);
                let r = get_scalar_or_array_value(rates, i);
                let sigma = get_scalar_or_array_value(sigmas, i);

                // Black76 formula for put
                let sqrt_t = t.sqrt();
                let d1 = ((f / k).ln() + (sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
                let d2 = d1 - sigma * sqrt_t;

                let put_price = (-r * t).exp() * (k * norm_cdf(-d2) - f * norm_cdf(-d1));
                result.push(put_price);
            }

            Ok(Arc::new(Float64Array::from(result)))
        }
    }

    /// Calculate delta (∂C/∂F)
    pub fn delta(
        forwards: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
        is_call: bool,
    ) -> Result<ArrayRef, ArrowError> {
        let len = validate_broadcast_compatibility(&[forwards, strikes, times, rates, sigmas])?;
        let mut result = Vec::with_capacity(len);

        for i in 0..len {
            let f = get_scalar_or_array_value(forwards, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let sqrt_t = t.sqrt();
            let d1 = ((f / k).ln() + (sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
            
            let delta = if is_call {
                (-r * t).exp() * norm_cdf(d1)
            } else {
                (-r * t).exp() * (norm_cdf(d1) - 1.0)
            };
            
            result.push(delta);
        }

        Ok(Arc::new(Float64Array::from(result)))
    }

    /// Calculate gamma (∂²C/∂F²)
    pub fn gamma(
        forwards: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        let len = validate_broadcast_compatibility(&[forwards, strikes, times, rates, sigmas])?;
        let mut result = Vec::with_capacity(len);

        use crate::math::distributions::norm_pdf;

        for i in 0..len {
            let f = get_scalar_or_array_value(forwards, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let sqrt_t = t.sqrt();
            let d1 = ((f / k).ln() + (sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
            
            let gamma = (-r * t).exp() * norm_pdf(d1) / (f * sigma * sqrt_t);
            result.push(gamma);
        }

        Ok(Arc::new(Float64Array::from(result)))
    }

    /// Calculate vega (∂C/∂σ)
    pub fn vega(
        forwards: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        let len = validate_broadcast_compatibility(&[forwards, strikes, times, rates, sigmas])?;
        let mut result = Vec::with_capacity(len);

        use crate::math::distributions::norm_pdf;

        for i in 0..len {
            let f = get_scalar_or_array_value(forwards, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let sqrt_t = t.sqrt();
            let d1 = ((f / k).ln() + (sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
            
            let vega = (-r * t).exp() * f * norm_pdf(d1) * sqrt_t;
            result.push(vega);
        }

        Ok(Arc::new(Float64Array::from(result)))
    }

    /// Calculate theta (∂C/∂T)
    pub fn theta(
        forwards: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
        is_call: bool,
    ) -> Result<ArrayRef, ArrowError> {
        let len = validate_broadcast_compatibility(&[forwards, strikes, times, rates, sigmas])?;
        let mut result = Vec::with_capacity(len);

        use crate::math::distributions::norm_pdf;

        for i in 0..len {
            let f = get_scalar_or_array_value(forwards, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let sqrt_t = t.sqrt();
            let d1 = ((f / k).ln() + (sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
            let d2 = d1 - sigma * sqrt_t;
            
            let discount = (-r * t).exp();
            let common_term = -discount * f * norm_pdf(d1) * sigma / (2.0 * sqrt_t);
            
            let theta = if is_call {
                common_term + r * discount * (f * norm_cdf(d1) - k * norm_cdf(d2))
            } else {
                common_term + r * discount * (k * norm_cdf(-d2) - f * norm_cdf(-d1))
            };
            
            result.push(theta);
        }

        Ok(Arc::new(Float64Array::from(result)))
    }

    /// Calculate rho (∂C/∂r)
    pub fn rho(
        forwards: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
        is_call: bool,
    ) -> Result<ArrayRef, ArrowError> {
        let len = validate_broadcast_compatibility(&[forwards, strikes, times, rates, sigmas])?;
        let mut result = Vec::with_capacity(len);

        for i in 0..len {
            let f = get_scalar_or_array_value(forwards, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let sqrt_t = t.sqrt();
            let d1 = ((f / k).ln() + (sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
            let d2 = d1 - sigma * sqrt_t;
            
            let discount = (-r * t).exp();
            
            let rho = if is_call {
                -t * discount * (f * norm_cdf(d1) - k * norm_cdf(d2))
            } else {
                -t * discount * (k * norm_cdf(-d2) - f * norm_cdf(-d1))
            };
            
            result.push(rho);
        }

        Ok(Arc::new(Float64Array::from(result)))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::PRACTICAL_TOLERANCE;

    #[test]
    fn test_call_price() {
        let forwards = Float64Array::from(vec![100.0]);
        let strikes = Float64Array::from(vec![100.0]);
        let times = Float64Array::from(vec![1.0]);
        let rates = Float64Array::from(vec![0.05]);
        let sigmas = Float64Array::from(vec![0.2]);

        let result = Black76::call_price(&forwards, &strikes, &times, &rates, &sigmas).unwrap();
        let prices = result.as_any().downcast_ref::<Float64Array>().unwrap();

        // Expected value for Black76 with F=100, K=100, T=1, r=0.05, sigma=0.2
        // Using exp(-r*T) * (F*N(d1) - K*N(d2))
        let expected = 7.577;  // Verified calculation
        assert!((prices.value(0) - expected).abs() < 0.01);
    }

    #[test]
    fn test_put_price() {
        let forwards = Float64Array::from(vec![100.0]);
        let strikes = Float64Array::from(vec![100.0]);
        let times = Float64Array::from(vec![1.0]);
        let rates = Float64Array::from(vec![0.05]);
        let sigmas = Float64Array::from(vec![0.2]);

        let result = Black76::put_price(&forwards, &strikes, &times, &rates, &sigmas).unwrap();
        let prices = result.as_any().downcast_ref::<Float64Array>().unwrap();

        // Expected value from put-call parity for ATM options (F=K)
        // For Black76 ATM: Call = Put (before discounting)
        let expected = 7.577;  // Same as call for F=K ATM option
        assert!((prices.value(0) - expected).abs() < 0.01);
    }

    #[test]
    fn test_broadcasting() {
        // Test scalar broadcasting
        let forwards = Float64Array::from(vec![100.0, 105.0, 110.0]);
        let strikes = Float64Array::from(vec![100.0]); // scalar
        let times = Float64Array::from(vec![1.0]); // scalar
        let rates = Float64Array::from(vec![0.05]); // scalar
        let sigmas = Float64Array::from(vec![0.2]); // scalar

        let result = Black76::call_price(&forwards, &strikes, &times, &rates, &sigmas).unwrap();
        let prices = result.as_any().downcast_ref::<Float64Array>().unwrap();

        assert_eq!(prices.len(), 3);
        // Prices should increase with forward price
        assert!(prices.value(1) > prices.value(0));
        assert!(prices.value(2) > prices.value(1));
    }
}