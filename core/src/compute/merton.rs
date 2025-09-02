//! Merton model with dividend yield - Arrow-native implementation

use arrow::array::builder::Float64Builder;
use arrow::array::{ArrayRef, Float64Array};
use arrow::error::ArrowError;
use std::sync::Arc;

use super::formulas::{merton_call_scalar, merton_put_scalar};
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
