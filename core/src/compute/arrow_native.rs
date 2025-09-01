//! Apache Arrow ネイティブ実装
//!
//! 真のゼロコピー処理を実現するArrowファーストの実装。
//! NumPy変換を介さない直接的なArrow配列処理。

use crate::compute::black76::Black76;
use crate::compute::black_scholes::BlackScholes;
use crate::compute::merton::Merton;
use crate::error::QuantForgeError;
use arrow::array::{ArrayRef, Float64Array};

/// Arrow Native計算エンジン
///
/// 既存のArrow最適化済みモジュールへのファサード
pub struct ArrowNativeCompute;

impl ArrowNativeCompute {
    /// Black-Scholesコール価格計算（真のゼロコピー）
    pub fn black_scholes_call_price(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, QuantForgeError> {
        BlackScholes::call_price(spots, strikes, times, rates, sigmas)
            .map_err(|e| QuantForgeError::Arrow(e))
    }

    /// Black-Scholesプット価格計算（真のゼロコピー）
    pub fn black_scholes_put_price(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, QuantForgeError> {
        BlackScholes::put_price(spots, strikes, times, rates, sigmas)
            .map_err(|e| QuantForgeError::Arrow(e))
    }

    /// Black76コール価格計算（真のゼロコピー）
    pub fn black76_call_price(
        forwards: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, QuantForgeError> {
        Black76::call_price(forwards, strikes, times, rates, sigmas)
            .map_err(|e| QuantForgeError::Arrow(e))
    }

    /// Black76プット価格計算（真のゼロコピー）
    pub fn black76_put_price(
        forwards: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, QuantForgeError> {
        Black76::put_price(forwards, strikes, times, rates, sigmas)
            .map_err(|e| QuantForgeError::Arrow(e))
    }

    /// Mertonコール価格計算（配当付き、真のゼロコピー）
    pub fn merton_call_price(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        dividend_yields: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, QuantForgeError> {
        Merton::call_price(spots, strikes, times, rates, dividend_yields, sigmas)
            .map_err(|e| QuantForgeError::Arrow(e))
    }

    /// Mertonプット価格計算（配当付き、真のゼロコピー）
    pub fn merton_put_price(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        dividend_yields: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, QuantForgeError> {
        Merton::put_price(spots, strikes, times, rates, dividend_yields, sigmas)
            .map_err(|e| QuantForgeError::Arrow(e))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_black_scholes_call_price() {
        let spots = Float64Array::from(vec![100.0, 105.0, 110.0]);
        let strikes = Float64Array::from(vec![100.0, 100.0, 100.0]);
        let times = Float64Array::from(vec![1.0, 1.0, 1.0]);
        let rates = Float64Array::from(vec![0.05, 0.05, 0.05]);
        let sigmas = Float64Array::from(vec![0.2, 0.2, 0.2]);

        let result =
            ArrowNativeCompute::black_scholes_call_price(&spots, &strikes, &times, &rates, &sigmas)
                .unwrap();

        let result_array = result.as_any().downcast_ref::<Float64Array>().unwrap();

        // 期待値（既存実装から）
        assert_relative_eq!(result_array.value(0), 10.45058, epsilon = 0.00001);
        assert!(result_array.value(1) > result_array.value(0)); // スポットが高いほど価格も高い
        assert!(result_array.value(2) > result_array.value(1));
    }

    #[test]
    fn test_shape_mismatch() {
        let spots = Float64Array::from(vec![100.0, 105.0]);
        let strikes = Float64Array::from(vec![100.0]); // 長さが異なる
        let times = Float64Array::from(vec![1.0, 1.0]);
        let rates = Float64Array::from(vec![0.05, 0.05]);
        let sigmas = Float64Array::from(vec![0.2, 0.2]);

        let result =
            ArrowNativeCompute::black_scholes_call_price(&spots, &strikes, &times, &rates, &sigmas);

        assert!(result.is_err());
    }
}
