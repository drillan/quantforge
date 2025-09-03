//! Black76 model for futures options - Arrow-native implementation

use arrow::array::builder::Float64Builder;
use arrow::array::{ArrayRef, Float64Array};
use arrow::error::ArrowError;
use std::sync::Arc;

use super::formulas::{black76_call_scalar, black76_d1_d2, black76_put_scalar};
use super::{get_scalar_or_array_value, validate_broadcast_compatibility};
use crate::constants::get_parallel_threshold;
use crate::math::distributions::norm_cdf;

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
        let mut builder = Float64Builder::with_capacity(len);

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

                    black76_call_scalar(f, k, t, r, sigma)
                })
                .collect();

            builder.append_slice(&results);
            Ok(Arc::new(builder.finish()))
        } else {
            // Sequential processing for small arrays
            for i in 0..len {
                let f = get_scalar_or_array_value(forwards, i);
                let k = get_scalar_or_array_value(strikes, i);
                let t = get_scalar_or_array_value(times, i);
                let r = get_scalar_or_array_value(rates, i);
                let sigma = get_scalar_or_array_value(sigmas, i);

                let call_price = black76_call_scalar(f, k, t, r, sigma);
                builder.append_value(call_price);
            }

            Ok(Arc::new(builder.finish()))
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
        let mut builder = Float64Builder::with_capacity(len);

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

                    black76_put_scalar(f, k, t, r, sigma)
                })
                .collect();

            builder.append_slice(&results);
            Ok(Arc::new(builder.finish()))
        } else {
            // Sequential processing for small arrays
            for i in 0..len {
                let f = get_scalar_or_array_value(forwards, i);
                let k = get_scalar_or_array_value(strikes, i);
                let t = get_scalar_or_array_value(times, i);
                let r = get_scalar_or_array_value(rates, i);
                let sigma = get_scalar_or_array_value(sigmas, i);

                let put_price = black76_put_scalar(f, k, t, r, sigma);
                builder.append_value(put_price);
            }

            Ok(Arc::new(builder.finish()))
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
        let mut builder = Float64Builder::with_capacity(len);

        for i in 0..len {
            let f = get_scalar_or_array_value(forwards, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let (d1, _d2) = black76_d1_d2(f, k, t, sigma);

            let delta = if is_call {
                (-r * t).exp() * norm_cdf(d1)
            } else {
                (-r * t).exp() * (norm_cdf(d1) - 1.0)
            };

            builder.append_value(delta);
        }

        Ok(Arc::new(builder.finish()))
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
        let mut builder = Float64Builder::with_capacity(len);

        use crate::math::distributions::norm_pdf;

        for i in 0..len {
            let f = get_scalar_or_array_value(forwards, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let (d1, _d2) = black76_d1_d2(f, k, t, sigma);
            let sqrt_t = t.sqrt();

            let gamma = (-r * t).exp() * norm_pdf(d1) / (f * sigma * sqrt_t);
            builder.append_value(gamma);
        }

        Ok(Arc::new(builder.finish()))
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
        let mut builder = Float64Builder::with_capacity(len);

        use crate::math::distributions::norm_pdf;

        for i in 0..len {
            let f = get_scalar_or_array_value(forwards, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let (d1, _d2) = black76_d1_d2(f, k, t, sigma);
            let sqrt_t = t.sqrt();

            let vega = (-r * t).exp() * f * norm_pdf(d1) * sqrt_t;
            builder.append_value(vega);
        }

        Ok(Arc::new(builder.finish()))
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
        let mut builder = Float64Builder::with_capacity(len);

        use crate::math::distributions::norm_pdf;

        for i in 0..len {
            let f = get_scalar_or_array_value(forwards, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let (d1, d2) = black76_d1_d2(f, k, t, sigma);
            let sqrt_t = t.sqrt();

            let discount = (-r * t).exp();
            let common_term = -discount * f * norm_pdf(d1) * sigma / (2.0 * sqrt_t);

            let theta = if is_call {
                common_term + r * discount * (f * norm_cdf(d1) - k * norm_cdf(d2))
            } else {
                common_term + r * discount * (k * norm_cdf(-d2) - f * norm_cdf(-d1))
            };

            builder.append_value(theta);
        }

        Ok(Arc::new(builder.finish()))
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
        let mut builder = Float64Builder::with_capacity(len);

        for i in 0..len {
            let f = get_scalar_or_array_value(forwards, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let (d1, d2) = black76_d1_d2(f, k, t, sigma);

            let discount = (-r * t).exp();

            let rho = if is_call {
                -t * discount * (f * norm_cdf(d1) - k * norm_cdf(d2))
            } else {
                -t * discount * (k * norm_cdf(-d2) - f * norm_cdf(-d1))
            };

            builder.append_value(rho);
        }

        Ok(Arc::new(builder.finish()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::TEST_TOLERANCE_VEGA;

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
        let expected = 7.577; // Verified calculation
        assert!((prices.value(0) - expected).abs() < TEST_TOLERANCE_VEGA);
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
        let expected = 7.577; // Same as call for F=K ATM option
        assert!((prices.value(0) - expected).abs() < TEST_TOLERANCE_VEGA);
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
