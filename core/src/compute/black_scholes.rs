//! Black-Scholes option pricing model - Arrow-native implementation

use arrow::array::builder::Float64Builder;
use arrow::array::{ArrayRef, BooleanArray, Float64Array};
use arrow::error::ArrowError;
use std::sync::Arc;

use super::formulas::{black_scholes_call_scalar, black_scholes_d1_d2, black_scholes_put_scalar};
use super::{get_scalar_or_array_value, validate_broadcast_compatibility};
use crate::constants::{get_parallel_threshold, PUT_DELTA_ADJUSTMENT, THETA_DENOMINATOR_FACTOR};

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

        // Handle empty arrays
        if len == 0 {
            return Ok(Arc::new(Float64Builder::new().finish()));
        }

        let mut builder = Float64Builder::with_capacity(len);

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

                    black_scholes_call_scalar(s, k, t, r, sigma)
                })
                .collect();

            builder.append_slice(&results);
            Ok(Arc::new(builder.finish()))
        } else {
            // Sequential processing for small arrays (avoid parallel overhead)
            for i in 0..len {
                let s = get_scalar_or_array_value(spots, i);
                let k = get_scalar_or_array_value(strikes, i);
                let t = get_scalar_or_array_value(times, i);
                let r = get_scalar_or_array_value(rates, i);
                let sigma = get_scalar_or_array_value(sigmas, i);

                let call_price = black_scholes_call_scalar(s, k, t, r, sigma);
                builder.append_value(call_price);
            }

            Ok(Arc::new(builder.finish()))
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

        // Handle empty arrays
        if len == 0 {
            return Ok(Arc::new(Float64Builder::new().finish()));
        }

        let mut builder = Float64Builder::with_capacity(len);

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

                    black_scholes_put_scalar(s, k, t, r, sigma)
                })
                .collect();

            builder.append_slice(&results);
            Ok(Arc::new(builder.finish()))
        } else {
            // Sequential processing for small arrays
            for i in 0..len {
                let s = get_scalar_or_array_value(spots, i);
                let k = get_scalar_or_array_value(strikes, i);
                let t = get_scalar_or_array_value(times, i);
                let r = get_scalar_or_array_value(rates, i);
                let sigma = get_scalar_or_array_value(sigmas, i);

                let put_price = black_scholes_put_scalar(s, k, t, r, sigma);
                builder.append_value(put_price);
            }

            Ok(Arc::new(builder.finish()))
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
        let mut builder = Float64Builder::with_capacity(len);

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

                    black_scholes_call_scalar(s, k, t, r, sigma)
                })
                .collect();

            builder.append_slice(&results);
            Ok(Arc::new(builder.finish()))
        } else {
            // Sequential processing for small arrays (avoid parallel overhead)
            for i in 0..len {
                let s = spots.value(i);
                let k = strikes.value(i);
                let t = times.value(i);
                let r = rates.value(i);
                let sigma = sigmas.value(i);

                let call_price = black_scholes_call_scalar(s, k, t, r, sigma);
                builder.append_value(call_price);
            }

            Ok(Arc::new(builder.finish()))
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
        let mut builder = Float64Builder::with_capacity(len);

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

                    black_scholes_put_scalar(s, k, t, r, sigma)
                })
                .collect();

            builder.append_slice(&results);
            Ok(Arc::new(builder.finish()))
        } else {
            // Sequential processing for small arrays
            for i in 0..len {
                let s = spots.value(i);
                let k = strikes.value(i);
                let t = times.value(i);
                let r = rates.value(i);
                let sigma = sigmas.value(i);

                let put_price = black_scholes_put_scalar(s, k, t, r, sigma);
                builder.append_value(put_price);
            }

            Ok(Arc::new(builder.finish()))
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
        let mut d1_builder = Float64Builder::with_capacity(len);
        let mut d2_builder = Float64Builder::with_capacity(len);

        for i in 0..len {
            let s = get_scalar_or_array_value(spots, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let (d1, d2) = black_scholes_d1_d2(s, k, t, r, sigma);

            d1_builder.append_value(d1);
            d2_builder.append_value(d2);
        }

        Ok((d1_builder.finish(), d2_builder.finish()))
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

        let mut builder = Float64Builder::with_capacity(d1.len());
        for i in 0..d1.len() {
            let n_d1 = norm_cdf(d1.value(i));
            let delta = if is_call {
                n_d1
            } else {
                n_d1 - PUT_DELTA_ADJUSTMENT
            };
            builder.append_value(delta);
        }
        Ok(Arc::new(builder.finish()))
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

        // Handle empty arrays
        if len == 0 {
            return Ok(Arc::new(Float64Builder::new().finish()));
        }

        let mut builder = Float64Builder::with_capacity(len);

        for i in 0..len {
            let s = get_scalar_or_array_value(spots, i);
            let t = get_scalar_or_array_value(times, i);
            let sigma = get_scalar_or_array_value(sigmas, i);
            let phi_d1 = norm_pdf(d1.value(i));
            let gamma = phi_d1 / (s * sigma * t.sqrt());
            builder.append_value(gamma);
        }
        Ok(Arc::new(builder.finish()))
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

        // Handle empty arrays
        if len == 0 {
            return Ok(Arc::new(Float64Builder::new().finish()));
        }

        let mut builder = Float64Builder::with_capacity(len);

        for i in 0..len {
            let s = get_scalar_or_array_value(spots, i);
            let t = get_scalar_or_array_value(times, i);
            let phi_d1 = norm_pdf(d1.value(i));
            let vega = s * phi_d1 * t.sqrt();
            builder.append_value(vega);
        }
        Ok(Arc::new(builder.finish()))
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

        // Handle empty arrays
        if len == 0 {
            return Ok(Arc::new(Float64Builder::new().finish()));
        }

        let mut builder = Float64Builder::with_capacity(len);

        for i in 0..len {
            let s = get_scalar_or_array_value(spots, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let sigma = get_scalar_or_array_value(sigmas, i);

            let phi_d1 = norm_pdf(d1.value(i));
            let common_term = -(s * phi_d1 * sigma) / (THETA_DENOMINATOR_FACTOR * t.sqrt());

            let theta = if is_call {
                let n_d2 = norm_cdf(d2.value(i));
                common_term - r * k * (-r * t).exp() * n_d2
            } else {
                let n_neg_d2 = norm_cdf(-d2.value(i));
                common_term + r * k * (-r * t).exp() * n_neg_d2
            };

            builder.append_value(theta);
        }
        Ok(Arc::new(builder.finish()))
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

        // Handle empty arrays
        if len == 0 {
            return Ok(Arc::new(Float64Builder::new().finish()));
        }

        let mut builder = Float64Builder::with_capacity(len);

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

            builder.append_value(rho);
        }
        Ok(Arc::new(builder.finish()))
    }

    /// Calculate implied volatility using Newton-Raphson method
    ///
    /// # Arguments
    /// * `prices` - Market prices of options
    /// * `spots` - Current spot prices (S)
    /// * `strikes` - Strike prices (K)
    /// * `times` - Time to maturity in years (T)
    /// * `rates` - Risk-free interest rates (r)
    /// * `is_calls` - Boolean array indicating call (true) or put (false)
    ///
    /// # Returns
    /// Arrow Float64Array of implied volatilities
    pub fn implied_volatility(
        prices: &Float64Array,
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        is_calls: &BooleanArray,
    ) -> Result<ArrayRef, ArrowError> {
        // Validate arrays for broadcasting compatibility
        let len = validate_broadcast_compatibility(&[prices, spots, strikes, times, rates])?;

        // Validate boolean array length
        if is_calls.len() != 1 && is_calls.len() != len {
            return Err(ArrowError::ComputeError(format!(
                "Boolean array length {} must be 1 or match other arrays length {}",
                is_calls.len(),
                len
            )));
        }

        let mut builder = Float64Builder::with_capacity(len);

        // Newton-Raphson parameters
        use crate::constants::{MAX_VOLATILITY, MIN_VOLATILITY, VEGA_MIN_THRESHOLD};
        const INITIAL_SIGMA: f64 = 0.2;
        const MAX_ITERATIONS: i32 = 100;
        const TOLERANCE: f64 = 1e-8;
        const MIN_VEGA: f64 = VEGA_MIN_THRESHOLD;

        if len >= get_parallel_threshold() {
            // Parallel processing for large arrays
            use rayon::prelude::*;

            let results: Vec<f64> = (0..len)
                .into_par_iter()
                .map(|i| {
                    let price = get_scalar_or_array_value(prices, i);
                    let s = get_scalar_or_array_value(spots, i);
                    let k = get_scalar_or_array_value(strikes, i);
                    let t = get_scalar_or_array_value(times, i);
                    let r = get_scalar_or_array_value(rates, i);
                    let is_call = if is_calls.len() == 1 {
                        is_calls.value(0)
                    } else {
                        is_calls.value(i)
                    };

                    // Validate inputs
                    if price <= 0.0 || s <= 0.0 || k <= 0.0 || t <= 0.0 {
                        return f64::NAN;
                    }

                    // Check arbitrage bounds
                    let intrinsic = if is_call {
                        (s - k * (-r * t).exp()).max(0.0)
                    } else {
                        (k * (-r * t).exp() - s).max(0.0)
                    };

                    if price < intrinsic {
                        return f64::NAN;
                    }

                    // Newton-Raphson iteration
                    let mut sigma = INITIAL_SIGMA;

                    for _ in 0..MAX_ITERATIONS {
                        let calc_price = if is_call {
                            black_scholes_call_scalar(s, k, t, r, sigma)
                        } else {
                            black_scholes_put_scalar(s, k, t, r, sigma)
                        };

                        let diff = calc_price - price;
                        if diff.abs() < TOLERANCE {
                            return sigma;
                        }

                        // Calculate vega
                        let (d1, _) = black_scholes_d1_d2(s, k, t, r, sigma);
                        let vega = s
                            * (t.sqrt())
                            * (1.0 / (2.0 * std::f64::consts::PI).sqrt())
                            * (-d1 * d1 / 2.0).exp();

                        if vega < MIN_VEGA {
                            return f64::NAN;
                        }

                        sigma -= diff / vega;

                        // Keep sigma in valid range
                        sigma = sigma.clamp(MIN_VOLATILITY, MAX_VOLATILITY);
                    }

                    // Failed to converge
                    f64::NAN
                })
                .collect();

            builder.append_slice(&results);
            Ok(Arc::new(builder.finish()))
        } else {
            // Sequential processing for small arrays
            for i in 0..len {
                let price = get_scalar_or_array_value(prices, i);
                let s = get_scalar_or_array_value(spots, i);
                let k = get_scalar_or_array_value(strikes, i);
                let t = get_scalar_or_array_value(times, i);
                let r = get_scalar_or_array_value(rates, i);
                let is_call = if is_calls.len() == 1 {
                    is_calls.value(0)
                } else {
                    is_calls.value(i)
                };

                // Validate inputs
                if price <= 0.0 || s <= 0.0 || k <= 0.0 || t <= 0.0 {
                    builder.append_value(f64::NAN);
                    continue;
                }

                // Check arbitrage bounds
                let intrinsic = if is_call {
                    (s - k * (-r * t).exp()).max(0.0)
                } else {
                    (k * (-r * t).exp() - s).max(0.0)
                };

                if price < intrinsic {
                    builder.append_value(f64::NAN);
                    continue;
                }

                // Newton-Raphson iteration
                let mut sigma = INITIAL_SIGMA;
                let mut converged = false;

                for _ in 0..MAX_ITERATIONS {
                    let calc_price = if is_call {
                        black_scholes_call_scalar(s, k, t, r, sigma)
                    } else {
                        black_scholes_put_scalar(s, k, t, r, sigma)
                    };

                    let diff = calc_price - price;
                    if diff.abs() < TOLERANCE {
                        converged = true;
                        break;
                    }

                    // Calculate vega
                    let (d1, _) = black_scholes_d1_d2(s, k, t, r, sigma);
                    let vega = s
                        * (t.sqrt())
                        * (1.0 / (2.0 * std::f64::consts::PI).sqrt())
                        * (-d1 * d1 / 2.0).exp();

                    if vega < MIN_VEGA {
                        break;
                    }

                    sigma -= diff / vega;

                    // Keep sigma in valid range
                    sigma = sigma.clamp(MIN_VOLATILITY, MAX_VOLATILITY);
                }

                builder.append_value(if converged { sigma } else { f64::NAN });
            }

            Ok(Arc::new(builder.finish()))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::{PRACTICAL_TOLERANCE, TEST_RATE, TEST_TOLERANCE_VEGA};

    #[test]
    fn test_call_price() {
        let spots = Float64Array::from(vec![100.0]);
        let strikes = Float64Array::from(vec![100.0]);
        let times = Float64Array::from(vec![1.0]);
        let rates = Float64Array::from(vec![TEST_RATE]);
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
        let rates = Float64Array::from(vec![TEST_RATE]);
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
        let rates = Float64Array::from(vec![TEST_RATE]);
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
        assert!((vega_val - 37.524).abs() < TEST_TOLERANCE_VEGA);
    }
}
