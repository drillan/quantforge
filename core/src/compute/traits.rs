//! 汎用的な計算トレイトとパターン
//!
//! コード重複を削減するための共通トレイトとジェネリック実装

use crate::constants::PARALLEL_THRESHOLD_SMALL;
use crate::error::QuantForgeResult;
use crate::math::{calculate_black76_d1_d2, calculate_d1_d2};
use rayon::prelude::*;

/// オプション価格計算エンジンの共通トレイト
pub trait OptionPricingEngine: Send + Sync {
    type Params: Send + Sync;
    type Output: Send;

    /// 単一計算
    fn compute_single(&self, params: &Self::Params) -> QuantForgeResult<Self::Output>;

    /// バッチ計算（デフォルト実装）
    fn compute_batch(&self, params_list: &[Self::Params]) -> Vec<QuantForgeResult<Self::Output>> {
        if params_list.len() < PARALLEL_THRESHOLD_SMALL {
            // 逐次処理
            params_list
                .iter()
                .map(|params| self.compute_single(params))
                .collect()
        } else {
            // Rayon並列処理
            params_list
                .par_iter()
                .map(|params| self.compute_single(params))
                .collect()
        }
    }
}

/// d1, d2パラメータ計算の汎用トレイト
pub trait D1D2Calculator {
    /// d1, d2を計算
    fn calculate_d1_d2(&self) -> (f64, f64);
}

/// Black-Scholesパラメータ構造体
pub struct BlackScholesD1D2 {
    pub s: f64,
    pub k: f64,
    pub t: f64,
    pub r: f64,
    pub sigma: f64,
}

impl D1D2Calculator for BlackScholesD1D2 {
    #[inline(always)]
    fn calculate_d1_d2(&self) -> (f64, f64) {
        calculate_d1_d2(self.s, self.k, self.t, self.r, 0.0, self.sigma)
    }
}

/// Black76パラメータ構造体
pub struct Black76D1D2 {
    pub f: f64,
    pub k: f64,
    pub t: f64,
    pub sigma: f64,
}

impl D1D2Calculator for Black76D1D2 {
    #[inline(always)]
    fn calculate_d1_d2(&self) -> (f64, f64) {
        calculate_black76_d1_d2(self.f, self.k, self.t, self.sigma)
    }
}

/// Mertonパラメータ構造体
pub struct MertonD1D2 {
    pub s: f64,
    pub k: f64,
    pub t: f64,
    pub r: f64,
    pub q: f64,
    pub sigma: f64,
}

impl D1D2Calculator for MertonD1D2 {
    #[inline(always)]
    fn calculate_d1_d2(&self) -> (f64, f64) {
        calculate_d1_d2(self.s, self.k, self.t, self.r, self.q, self.sigma)
    }
}

/// 入力検証パターンの汎用実装
pub trait ValidationPattern {
    /// 基本的な入力検証
    fn validate_basic_inputs(s: f64, k: f64, t: f64, sigma: f64) -> QuantForgeResult<()> {
        use crate::error::ValidationBuilder;

        ValidationBuilder::new()
            .check_positive(s, "s")
            .check_positive(k, "k")
            .check_positive(t, "t")
            .check_positive(sigma, "sigma")
            .build()
    }

    /// 拡張入力検証（金利を含む）
    fn validate_extended_inputs(
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        sigma: f64,
    ) -> QuantForgeResult<()> {
        use crate::error::ValidationBuilder;

        ValidationBuilder::new()
            .check_positive(s, "s")
            .check_positive(k, "k")
            .check_positive(t, "t")
            .check_finite(r, "r")
            .check_positive(sigma, "sigma")
            .build()
    }

    /// Merton用検証（配当を含む）
    fn validate_merton_inputs(
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
    ) -> QuantForgeResult<()> {
        use crate::error::ValidationBuilder;

        ValidationBuilder::new()
            .check_positive(s, "s")
            .check_positive(k, "k")
            .check_positive(t, "t")
            .check_finite(r, "r")
            .check_finite(q, "q")
            .check_positive(sigma, "sigma")
            .build()
    }
}

/// Greeks計算パターンの汎用実装
pub trait GreeksCalculator {
    type Params;
    type Output;

    fn calculate_delta(&self, params: &Self::Params, is_call: bool) -> f64;
    fn calculate_gamma(&self, params: &Self::Params) -> f64;
    fn calculate_vega(&self, params: &Self::Params) -> f64;
    fn calculate_theta(&self, params: &Self::Params, is_call: bool) -> f64;
    fn calculate_rho(&self, params: &Self::Params, is_call: bool) -> f64;

    /// 全Greeksを一度に計算（効率的）
    fn calculate_all_greeks(&self, params: &Self::Params, is_call: bool) -> Self::Output;
}

/// バッチ処理の汎用パターン
pub fn apply_parallel<T, F, R>(data: &[T], operation: F) -> Vec<R>
where
    T: Send + Sync,
    F: Fn(&T) -> R + Send + Sync,
    R: Send,
{
    if data.len() < PARALLEL_THRESHOLD_SMALL {
        // 逐次処理
        data.iter().map(operation).collect()
    } else {
        // Rayon並列処理
        data.par_iter().map(operation).collect()
    }
}

/// 配列処理の汎用パターン（インプレース）
pub fn process_in_place<F>(input: &[f64], output: &mut [f64], operation: F)
where
    F: Fn(f64) -> f64 + Send + Sync,
{
    if input.len() < PARALLEL_THRESHOLD_SMALL {
        // 逐次処理
        for (i, &val) in input.iter().enumerate() {
            output[i] = operation(val);
        }
    } else {
        // Rayon並列処理（チャンク単位）
        const CHUNK_SIZE: usize = 1024;
        input
            .par_chunks(CHUNK_SIZE)
            .zip(output.par_chunks_mut(CHUNK_SIZE))
            .for_each(|(inp, out)| {
                for (i, &val) in inp.iter().enumerate() {
                    out[i] = operation(val);
                }
            });
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::TEST_RATE;

    #[test]
    fn test_d1_d2_calculation() {
        let bs_params = BlackScholesD1D2 {
            s: 100.0,
            k: 100.0,
            t: 1.0,
            r: TEST_RATE,
            sigma: 0.2,
        };

        let (d1, d2) = bs_params.calculate_d1_d2();
        assert!(d1.is_finite());
        assert!(d2.is_finite());
        assert!(d2 < d1);
    }

    #[test]
    fn test_parallel_threshold() {
        let small_data: Vec<f64> = vec![1.0; 100];
        let large_data: Vec<f64> = vec![1.0; 20_000];

        let small_result = apply_parallel(&small_data, |&x| x * 2.0);
        let large_result = apply_parallel(&large_data, |&x| x * 2.0);

        assert_eq!(small_result.len(), 100);
        assert_eq!(large_result.len(), 20_000);
    }
}
