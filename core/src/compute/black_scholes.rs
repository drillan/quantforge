//! Black-Scholes option pricing model - Arrow-native implementation

use arrow::array::{ArrayRef, Float64Array};
use arrow::error::ArrowError;
use std::sync::Arc;

use crate::constants::get_parallel_threshold;
use super::{get_scalar_or_array_value, validate_broadcast_compatibility};

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
        // Validate arrays for broadcasting compatibility
        let len = validate_broadcast_compatibility(&[spots, strikes, times, rates, sigmas])?;
        let mut result = Vec::with_capacity(len);

        // Use direct scalar computation for efficiency (avoiding intermediate arrays)
        use crate::math::distributions::norm_cdf;

        if len >= get_parallel_threshold() {
            // Parallel processing for large arrays
            use rayon::prelude::*;

            let results: Vec<f64> = (0..len)
                .into_par_iter()
                .map(|i| {
                    let s = get_scalar_or_array_value(spots, i);
                    let k = get_scalar_or_array_value(strikes, i);
                    let t = get_scalar_or_array_value(times, i);
                    let r = get_scalar_or_array_value(rates, i);
                    let sigma = get_scalar_or_array_value(sigmas, i);

                    // Black-Scholes formula
                    let sqrt_t = t.sqrt();
                    let d1 = ((s / k).ln() + (r + sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
                    let d2 = d1 - sigma * sqrt_t;

                    s * norm_cdf(d1) - k * (-r * t).exp() * norm_cdf(d2)
                })
                .collect();

            Ok(Arc::new(Float64Array::from(results)))
        } else {
            // Sequential processing for small arrays (avoid parallel overhead)
            for i in 0..len {
                let s = get_scalar_or_array_value(spots, i);
                let k = get_scalar_or_array_value(strikes, i);
                let t = get_scalar_or_array_value(times, i);
                let r = get_scalar_or_array_value(rates, i);
                let sigma = get_scalar_or_array_value(sigmas, i);

                // Black-Scholes formula
                let sqrt_t = t.sqrt();
                let d1 = ((s / k).ln() + (r + sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
                let d2 = d1 - sigma * sqrt_t;

                let call_price = s * norm_cdf(d1) - k * (-r * t).exp() * norm_cdf(d2);
                result.push(call_price);
            }

            Ok(Arc::new(Float64Array::from(result)))
        }
    }

    /// Calculate put option price using Black-Scholes formula
    ///
    /// P = K * exp(-r*T) * N(-d2) - S * N(-d1)
    pub fn put_price(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        // Validate arrays for broadcasting compatibility
        let len = validate_broadcast_compatibility(&[spots, strikes, times, rates, sigmas])?;
        let mut result = Vec::with_capacity(len);

        // Use direct scalar computation for efficiency
        use crate::math::distributions::norm_cdf;

        if len >= get_parallel_threshold() {
            // Parallel processing for large arrays
            use rayon::prelude::*;

            let results: Vec<f64> = (0..len)
                .into_par_iter()
                .map(|i| {
                    let s = get_scalar_or_array_value(spots, i);
                    let k = get_scalar_or_array_value(strikes, i);
                    let t = get_scalar_or_array_value(times, i);
                    let r = get_scalar_or_array_value(rates, i);
                    let sigma = get_scalar_or_array_value(sigmas, i);

                    // Black-Scholes formula for put
                    let sqrt_t = t.sqrt();
                    let d1 = ((s / k).ln() + (r + sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
                    let d2 = d1 - sigma * sqrt_t;

                    k * (-r * t).exp() * norm_cdf(-d2) - s * norm_cdf(-d1)
                })
                .collect();

            Ok(Arc::new(Float64Array::from(results)))
        } else {
            // Sequential processing for small arrays
            for i in 0..len {
                let s = get_scalar_or_array_value(spots, i);
                let k = get_scalar_or_array_value(strikes, i);
                let t = get_scalar_or_array_value(times, i);
                let r = get_scalar_or_array_value(rates, i);
                let sigma = get_scalar_or_array_value(sigmas, i);

                // Black-Scholes formula for put
                let sqrt_t = t.sqrt();
                let d1 = ((s / k).ln() + (r + sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
                let d2 = d1 - sigma * sqrt_t;

                let put_price = k * (-r * t).exp() * norm_cdf(-d2) - s * norm_cdf(-d1);
                result.push(put_price);
            }

            Ok(Arc::new(Float64Array::from(result)))
        }
    }

    /// Calculate call option price WITHOUT validation (unsafe version)
    ///
    /// ⚠️ WARNING: This function skips all input validation for performance.
    /// Use only when inputs are pre-validated.
    ///
    /// # Arguments
    /// * `spots` - Current spot prices (S) - must be positive
    /// * `strikes` - Strike prices (K) - must be positive
    /// * `times` - Time to maturity in years (T) - must be positive
    /// * `rates` - Risk-free interest rates (r)
    /// * `sigmas` - Volatilities (σ) - must be positive
    ///
    /// # Returns
    /// Arrow Float64Array of call option prices
    pub fn call_price_unchecked(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        // Skip validation for performance
        let len = spots.len();
        let mut result = Vec::with_capacity(len);

        // Use direct scalar computation for efficiency (avoiding intermediate arrays)
        use crate::math::distributions::norm_cdf;

        if len >= get_parallel_threshold() {
            // Parallel processing for large arrays
            use rayon::prelude::*;

            let results: Vec<f64> = (0..len)
                .into_par_iter()
                .map(|i| {
                    let s = spots.value(i);
                    let k = strikes.value(i);
                    let t = times.value(i);
                    let r = rates.value(i);
                    let sigma = sigmas.value(i);

                    // Black-Scholes formula
                    let sqrt_t = t.sqrt();
                    let d1 = ((s / k).ln() + (r + sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
                    let d2 = d1 - sigma * sqrt_t;

                    s * norm_cdf(d1) - k * (-r * t).exp() * norm_cdf(d2)
                })
                .collect();

            Ok(Arc::new(Float64Array::from(results)))
        } else {
            // Sequential processing for small arrays (avoid parallel overhead)
            for i in 0..len {
                let s = spots.value(i);
                let k = strikes.value(i);
                let t = times.value(i);
                let r = rates.value(i);
                let sigma = sigmas.value(i);

                // Black-Scholes formula
                let sqrt_t = t.sqrt();
                let d1 = ((s / k).ln() + (r + sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
                let d2 = d1 - sigma * sqrt_t;

                let call_price = s * norm_cdf(d1) - k * (-r * t).exp() * norm_cdf(d2);
                result.push(call_price);
            }

            Ok(Arc::new(Float64Array::from(result)))
        }
    }

    /// Calculate put option price WITHOUT validation (unsafe version)
    ///
    /// ⚠️ WARNING: This function skips all input validation for performance.
    /// Use only when inputs are pre-validated.
    ///
    /// P = K * exp(-r*T) * N(-d2) - S * N(-d1)
    pub fn put_price_unchecked(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        // Skip validation for performance
        let len = spots.len();
        let mut result = Vec::with_capacity(len);

        // Use direct scalar computation for efficiency
        use crate::math::distributions::norm_cdf;

        if len >= get_parallel_threshold() {
            // Parallel processing for large arrays
            use rayon::prelude::*;

            let results: Vec<f64> = (0..len)
                .into_par_iter()
                .map(|i| {
                    let s = spots.value(i);
                    let k = strikes.value(i);
                    let t = times.value(i);
                    let r = rates.value(i);
                    let sigma = sigmas.value(i);

                    // Black-Scholes formula for put
                    let sqrt_t = t.sqrt();
                    let d1 = ((s / k).ln() + (r + sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
                    let d2 = d1 - sigma * sqrt_t;

                    k * (-r * t).exp() * norm_cdf(-d2) - s * norm_cdf(-d1)
                })
                .collect();

            Ok(Arc::new(Float64Array::from(results)))
        } else {
            // Sequential processing for small arrays
            for i in 0..len {
                let s = spots.value(i);
                let k = strikes.value(i);
                let t = times.value(i);
                let r = rates.value(i);
                let sigma = sigmas.value(i);

                // Black-Scholes formula for put
                let sqrt_t = t.sqrt();
                let d1 = ((s / k).ln() + (r + sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
                let d2 = d1 - sigma * sqrt_t;

                let put_price = k * (-r * t).exp() * norm_cdf(-d2) - s * norm_cdf(-d1);
                result.push(put_price);
            }

            Ok(Arc::new(Float64Array::from(result)))
        }
    }

    /// Calculate d1 and d2 parameters with broadcasting support
    fn calculate_d1_d2(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<(Float64Array, Float64Array), ArrowError> {
        let len = validate_broadcast_compatibility(&[spots, strikes, times, rates, sigmas])?;
        let mut d1_values = Vec::with_capacity(len);
        let mut d2_values = Vec::with_capacity(len);
        
        for i in 0..len {
            let s = get_scalar_or_array_value(spots, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let sigma = get_scalar_or_array_value(sigmas, i);
            
            let sqrt_t = t.sqrt();
            let d1 = ((s / k).ln() + (r + sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
            let d2 = d1 - sigma * sqrt_t;
            
            d1_values.push(d1);
            d2_values.push(d2);
        }

        Ok((Float64Array::from(d1_values), Float64Array::from(d2_values)))
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
        use crate::math::distributions::norm_cdf;
        
        let mut result = Vec::with_capacity(d1.len());
        for i in 0..d1.len() {
            let n_d1 = norm_cdf(d1.value(i));
            let delta = if is_call { n_d1 } else { n_d1 - 1.0 };
            result.push(delta);
        }
        Ok(Arc::new(Float64Array::from(result)))
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
        use crate::math::distributions::norm_pdf;
        
        let len = validate_broadcast_compatibility(&[spots, strikes, times, rates, sigmas])?;
        let mut result = Vec::with_capacity(len);
        
        for i in 0..len {
            let s = get_scalar_or_array_value(spots, i);
            let t = get_scalar_or_array_value(times, i);
            let sigma = get_scalar_or_array_value(sigmas, i);
            let phi_d1 = norm_pdf(d1.value(i));
            let gamma = phi_d1 / (s * sigma * t.sqrt());
            result.push(gamma);
        }
        Ok(Arc::new(Float64Array::from(result)))
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
        use crate::math::distributions::norm_pdf;
        
        let len = validate_broadcast_compatibility(&[spots, strikes, times, rates, sigmas])?;
        let mut result = Vec::with_capacity(len);
        
        for i in 0..len {
            let s = get_scalar_or_array_value(spots, i);
            let t = get_scalar_or_array_value(times, i);
            let phi_d1 = norm_pdf(d1.value(i));
            let vega = s * phi_d1 * t.sqrt();
            result.push(vega);
        }
        Ok(Arc::new(Float64Array::from(result)))
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
        use crate::math::distributions::{norm_cdf, norm_pdf};
        
        let len = validate_broadcast_compatibility(&[spots, strikes, times, rates, sigmas])?;
        let mut result = Vec::with_capacity(len);
        
        for i in 0..len {
            let s = get_scalar_or_array_value(spots, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let sigma = get_scalar_or_array_value(sigmas, i);
            
            let phi_d1 = norm_pdf(d1.value(i));
            let common_term = -(s * phi_d1 * sigma) / (2.0 * t.sqrt());
            
            let theta = if is_call {
                let n_d2 = norm_cdf(d2.value(i));
                common_term - r * k * (-r * t).exp() * n_d2
            } else {
                let n_neg_d2 = norm_cdf(-d2.value(i));
                common_term + r * k * (-r * t).exp() * n_neg_d2
            };
            
            result.push(theta);
        }
        Ok(Arc::new(Float64Array::from(result)))
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
        use crate::math::distributions::norm_cdf;
        
        let len = validate_broadcast_compatibility(&[spots, strikes, times, rates, sigmas])?;
        let mut result = Vec::with_capacity(len);
        
        for i in 0..len {
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            
            let k_t_exp = k * t * (-r * t).exp();
            
            let rho = if is_call {
                k_t_exp * norm_cdf(d2.value(i))
            } else {
                -k_t_exp * norm_cdf(-d2.value(i))
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
        let delta_val = delta
            .as_any()
            .downcast_ref::<Float64Array>()
            .unwrap()
            .value(0);
        assert!((delta_val - 0.6368).abs() < PRACTICAL_TOLERANCE);

        // Test gamma
        let gamma = BlackScholes::gamma(&spots, &strikes, &times, &rates, &sigmas).unwrap();
        let gamma_val = gamma
            .as_any()
            .downcast_ref::<Float64Array>()
            .unwrap()
            .value(0);
        assert!((gamma_val - 0.0188).abs() < PRACTICAL_TOLERANCE);

        // Test vega
        let vega = BlackScholes::vega(&spots, &strikes, &times, &rates, &sigmas).unwrap();
        let vega_val = vega
            .as_any()
            .downcast_ref::<Float64Array>()
            .unwrap()
            .value(0);
        assert!((vega_val - 37.524).abs() < 0.01);
    }
}
