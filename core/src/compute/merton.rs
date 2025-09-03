//! Merton model with dividend yield - Arrow-native implementation

use arrow::array::builder::Float64Builder;
use arrow::array::{ArrayRef, BooleanArray, Float64Array};
use arrow::error::ArrowError;
use std::sync::Arc;

use super::formulas::{merton_call_scalar, merton_d1_d2, merton_put_scalar};
use super::{get_scalar_or_array_value, validate_broadcast_compatibility};
use crate::constants::get_parallel_threshold;

/// Merton model implementation using Arrow arrays
pub struct Merton;

impl Merton {
    /// Calculate call option price with dividend yield
    ///
    /// # Arguments
    /// * `spots` - Current spot prices (S)
    /// * `strikes` - Strike prices (K)
    /// * `times` - Time to maturity in years (T)
    /// * `rates` - Risk-free interest rates (r)
    /// * `dividend_yields` - Continuous dividend yields (q)
    /// * `sigmas` - Volatilities (σ)
    ///
    /// # Returns
    /// Arrow Float64Array of call option prices
    pub fn call_price(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        dividend_yields: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        // Validate arrays for broadcasting compatibility
        let len = validate_broadcast_compatibility(&[
            spots,
            strikes,
            times,
            rates,
            dividend_yields,
            sigmas,
        ])?;
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
                    let q = get_scalar_or_array_value(dividend_yields, i);
                    let sigma = get_scalar_or_array_value(sigmas, i);

                    merton_call_scalar(s, k, t, r, q, sigma)
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
                let q = get_scalar_or_array_value(dividend_yields, i);
                let sigma = get_scalar_or_array_value(sigmas, i);

                let call_price = merton_call_scalar(s, k, t, r, q, sigma);
                builder.append_value(call_price);
            }

            Ok(Arc::new(builder.finish()))
        }
    }

    /// Calculate put option price with dividend yield
    ///
    /// # Arguments
    /// * `spots` - Current spot prices (S)
    /// * `strikes` - Strike prices (K)
    /// * `times` - Time to maturity in years (T)
    /// * `rates` - Risk-free interest rates (r)
    /// * `dividend_yields` - Continuous dividend yields (q)
    /// * `sigmas` - Volatilities (σ)
    ///
    /// # Returns
    /// Arrow Float64Array of put option prices
    pub fn put_price(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        dividend_yields: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        // Validate arrays for broadcasting compatibility
        let len = validate_broadcast_compatibility(&[
            spots,
            strikes,
            times,
            rates,
            dividend_yields,
            sigmas,
        ])?;
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
                    let q = get_scalar_or_array_value(dividend_yields, i);
                    let sigma = get_scalar_or_array_value(sigmas, i);

                    merton_put_scalar(s, k, t, r, q, sigma)
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
                let q = get_scalar_or_array_value(dividend_yields, i);
                let sigma = get_scalar_or_array_value(sigmas, i);

                let put_price = merton_put_scalar(s, k, t, r, q, sigma);
                builder.append_value(put_price);
            }

            Ok(Arc::new(builder.finish()))
        }
    }

    /// Calculate implied volatility using Newton-Raphson method for Merton model
    ///
    /// # Arguments
    /// * `prices` - Market prices of options
    /// * `spots` - Current spot prices (S)
    /// * `strikes` - Strike prices (K)
    /// * `times` - Time to maturity in years (T)
    /// * `rates` - Risk-free interest rates (r)
    /// * `dividend_yields` - Continuous dividend yields (q)
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
        dividend_yields: &Float64Array,
        is_calls: &BooleanArray,
    ) -> Result<ArrayRef, ArrowError> {
        // Validate arrays for broadcasting compatibility
        let len = validate_broadcast_compatibility(&[
            prices,
            spots,
            strikes,
            times,
            rates,
            dividend_yields,
        ])?;

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
        const INITIAL_SIGMA: f64 = 0.2;
        const MAX_ITERATIONS: i32 = 100;
        const TOLERANCE: f64 = 1e-8;
        const MIN_SIGMA: f64 = 0.001;
        const MAX_SIGMA: f64 = 10.0;
        const MIN_VEGA: f64 = 1e-10;

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
                    let q = get_scalar_or_array_value(dividend_yields, i);
                    let is_call = if is_calls.len() == 1 {
                        is_calls.value(0)
                    } else {
                        is_calls.value(i)
                    };

                    // Validate inputs
                    if price <= 0.0 || s <= 0.0 || k <= 0.0 || t <= 0.0 {
                        return f64::NAN;
                    }

                    // Check arbitrage bounds with dividend adjustment
                    let intrinsic = if is_call {
                        (s * (-q * t).exp() - k * (-r * t).exp()).max(0.0)
                    } else {
                        (k * (-r * t).exp() - s * (-q * t).exp()).max(0.0)
                    };

                    if price < intrinsic {
                        return f64::NAN;
                    }

                    // Newton-Raphson iteration
                    let mut sigma = INITIAL_SIGMA;

                    for _ in 0..MAX_ITERATIONS {
                        let calc_price = if is_call {
                            merton_call_scalar(s, k, t, r, q, sigma)
                        } else {
                            merton_put_scalar(s, k, t, r, q, sigma)
                        };

                        let diff = calc_price - price;
                        if diff.abs() < TOLERANCE {
                            return sigma;
                        }

                        // Calculate vega for Merton (similar to Black-Scholes with dividend adjustment)
                        let (d1, _) = merton_d1_d2(s, k, t, r, q, sigma);
                        let vega = s
                            * (-q * t).exp()
                            * (t.sqrt())
                            * (1.0 / (2.0 * std::f64::consts::PI).sqrt())
                            * (-d1 * d1 / 2.0).exp();

                        if vega < MIN_VEGA {
                            return f64::NAN;
                        }

                        sigma -= diff / vega;

                        // Keep sigma in valid range
                        sigma = sigma.clamp(MIN_SIGMA, MAX_SIGMA);
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
                let q = get_scalar_or_array_value(dividend_yields, i);
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

                // Check arbitrage bounds with dividend adjustment
                let intrinsic = if is_call {
                    (s * (-q * t).exp() - k * (-r * t).exp()).max(0.0)
                } else {
                    (k * (-r * t).exp() - s * (-q * t).exp()).max(0.0)
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
                        merton_call_scalar(s, k, t, r, q, sigma)
                    } else {
                        merton_put_scalar(s, k, t, r, q, sigma)
                    };

                    let diff = calc_price - price;
                    if diff.abs() < TOLERANCE {
                        converged = true;
                        break;
                    }

                    // Calculate vega for Merton
                    let (d1, _) = merton_d1_d2(s, k, t, r, q, sigma);
                    let vega = s
                        * (-q * t).exp()
                        * (t.sqrt())
                        * (1.0 / (2.0 * std::f64::consts::PI).sqrt())
                        * (-d1 * d1 / 2.0).exp();

                    if vega < MIN_VEGA {
                        break;
                    }

                    sigma -= diff / vega;

                    // Keep sigma in valid range
                    sigma = sigma.clamp(MIN_SIGMA, MAX_SIGMA);
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
    use crate::constants::PRACTICAL_TOLERANCE;

    #[test]
    fn test_merton_call_price() {
        let spots = Float64Array::from(vec![100.0]);
        let strikes = Float64Array::from(vec![100.0]);
        let times = Float64Array::from(vec![1.0]);
        let rates = Float64Array::from(vec![0.05]);
        let dividend_yields = Float64Array::from(vec![0.02]);
        let sigmas = Float64Array::from(vec![0.2]);

        let result =
            Merton::call_price(&spots, &strikes, &times, &rates, &dividend_yields, &sigmas)
                .unwrap();
        let array = result.as_any().downcast_ref::<Float64Array>().unwrap();

        // 配当付きオプションは配当なしより安くなる
        assert!(array.value(0) > 6.0 && array.value(0) < 10.0);
    }

    #[test]
    fn test_merton_put_call_parity() {
        let spots = Float64Array::from(vec![100.0]);
        let strikes = Float64Array::from(vec![100.0]);
        let times = Float64Array::from(vec![1.0]);
        let rates = Float64Array::from(vec![0.05]);
        let dividend_yields = Float64Array::from(vec![0.02]);
        let sigmas = Float64Array::from(vec![0.2]);

        let call_result =
            Merton::call_price(&spots, &strikes, &times, &rates, &dividend_yields, &sigmas)
                .unwrap();
        let put_result =
            Merton::put_price(&spots, &strikes, &times, &rates, &dividend_yields, &sigmas).unwrap();

        let call_array = call_result.as_any().downcast_ref::<Float64Array>().unwrap();
        let put_array = put_result.as_any().downcast_ref::<Float64Array>().unwrap();

        let s = spots.value(0);
        let k = strikes.value(0);
        let t = times.value(0);
        let r = rates.value(0);
        let q = dividend_yields.value(0);

        // Put-Call parity for dividend-paying assets
        // C - P = S*exp(-q*T) - K*exp(-r*T)
        let parity =
            call_array.value(0) - put_array.value(0) - (s * (-q * t).exp() - k * (-r * t).exp());

        assert!(
            parity.abs() < PRACTICAL_TOLERANCE,
            "Put-Call parity violation: {parity}"
        );
    }
}
