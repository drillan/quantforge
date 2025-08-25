//! グリークス計算の並列処理版
//!
//! Rayonを使用した高速並列計算実装。
//! 大規模データセット（30,000要素以上）で自動的に並列処理を適用。

use crate::models::greeks::{
    calculate_all_greeks, delta_call, delta_put, gamma, rho_call, rho_put, theta_call, theta_put,
    vega, Greeks,
};
use rayon::prelude::*;

/// 並列処理の閾値（この要素数以上で並列化）
const PARALLEL_THRESHOLD: usize = 30_000;

/// Delta Callバッチ並列計算
pub fn delta_call_batch_parallel(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    if spots.len() < PARALLEL_THRESHOLD {
        // 小規模データは通常のバッチ処理
        crate::models::greeks::delta_call_batch(spots, k, t, r, v)
    } else {
        // 大規模データは並列処理
        spots
            .par_iter()
            .map(|&s| delta_call(s, k, t, r, v))
            .collect()
    }
}

/// Delta Putバッチ並列計算
pub fn delta_put_batch_parallel(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    if spots.len() < PARALLEL_THRESHOLD {
        crate::models::greeks::delta_put_batch(spots, k, t, r, v)
    } else {
        spots
            .par_iter()
            .map(|&s| delta_put(s, k, t, r, v))
            .collect()
    }
}

/// Gammaバッチ並列計算
pub fn gamma_batch_parallel(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    if spots.len() < PARALLEL_THRESHOLD {
        crate::models::greeks::gamma_batch(spots, k, t, r, v)
    } else {
        spots.par_iter().map(|&s| gamma(s, k, t, r, v)).collect()
    }
}

/// Vegaバッチ並列計算
pub fn vega_batch_parallel(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    if spots.len() < PARALLEL_THRESHOLD {
        crate::models::greeks::vega_batch(spots, k, t, r, v)
    } else {
        spots.par_iter().map(|&s| vega(s, k, t, r, v)).collect()
    }
}

/// Theta Callバッチ並列計算
pub fn theta_call_batch_parallel(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    if spots.len() < PARALLEL_THRESHOLD {
        crate::models::greeks::theta_call_batch(spots, k, t, r, v)
    } else {
        spots
            .par_iter()
            .map(|&s| theta_call(s, k, t, r, v))
            .collect()
    }
}

/// Theta Putバッチ並列計算
pub fn theta_put_batch_parallel(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    if spots.len() < PARALLEL_THRESHOLD {
        crate::models::greeks::theta_put_batch(spots, k, t, r, v)
    } else {
        spots
            .par_iter()
            .map(|&s| theta_put(s, k, t, r, v))
            .collect()
    }
}

/// Rho Callバッチ並列計算
pub fn rho_call_batch_parallel(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    if spots.len() < PARALLEL_THRESHOLD {
        crate::models::greeks::rho_call_batch(spots, k, t, r, v)
    } else {
        spots.par_iter().map(|&s| rho_call(s, k, t, r, v)).collect()
    }
}

/// Rho Putバッチ並列計算
pub fn rho_put_batch_parallel(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    if spots.len() < PARALLEL_THRESHOLD {
        crate::models::greeks::rho_put_batch(spots, k, t, r, v)
    } else {
        spots.par_iter().map(|&s| rho_put(s, k, t, r, v)).collect()
    }
}

/// 全グリークスバッチ並列計算
///
/// 複数のスポット価格に対して全グリークスを並列計算
pub fn calculate_all_greeks_batch_parallel(
    spots: &[f64],
    k: f64,
    t: f64,
    r: f64,
    v: f64,
    is_call: bool,
) -> Vec<Greeks> {
    if spots.len() < PARALLEL_THRESHOLD {
        // 小規模データは通常処理
        spots
            .iter()
            .map(|&s| calculate_all_greeks(s, k, t, r, v, is_call))
            .collect()
    } else {
        // 大規模データは並列処理
        spots
            .par_iter()
            .map(|&s| calculate_all_greeks(s, k, t, r, v, is_call))
            .collect()
    }
}

/// Python向けDelta Call並列バッチ処理（ゼロコピー対応準備）
pub fn delta_call_batch_parallel_py(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    delta_call_batch_parallel(spots, k, t, r, v)
}

/// Python向けDelta Put並列バッチ処理（ゼロコピー対応準備）
pub fn delta_put_batch_parallel_py(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    delta_put_batch_parallel(spots, k, t, r, v)
}

/// Python向けGamma並列バッチ処理（ゼロコピー対応準備）
pub fn gamma_batch_parallel_py(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    gamma_batch_parallel(spots, k, t, r, v)
}

/// Python向けVega並列バッチ処理（ゼロコピー対応準備）
pub fn vega_batch_parallel_py(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    vega_batch_parallel(spots, k, t, r, v)
}

/// Python向けTheta Call並列バッチ処理（ゼロコピー対応準備）
pub fn theta_call_batch_parallel_py(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    theta_call_batch_parallel(spots, k, t, r, v)
}

/// Python向けTheta Put並列バッチ処理（ゼロコピー対応準備）
pub fn theta_put_batch_parallel_py(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    theta_put_batch_parallel(spots, k, t, r, v)
}

/// Python向けRho Call並列バッチ処理（ゼロコピー対応準備）
pub fn rho_call_batch_parallel_py(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    rho_call_batch_parallel(spots, k, t, r, v)
}

/// Python向けRho Put並列バッチ処理（ゼロコピー対応準備）
pub fn rho_put_batch_parallel_py(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    rho_put_batch_parallel(spots, k, t, r, v)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::NUMERICAL_TOLERANCE;
    use approx::assert_relative_eq;

    #[test]
    fn test_parallel_consistency() {
        // 並列化閾値未満のデータ
        let small_spots: Vec<f64> = (0..100).map(|i| 90.0 + i as f64 * 0.2).collect();
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let v = 0.2;

        // Delta Call
        let parallel_deltas = delta_call_batch_parallel(&small_spots, k, t, r, v);
        let serial_deltas = crate::models::greeks::delta_call_batch(&small_spots, k, t, r, v);
        for i in 0..small_spots.len() {
            assert_relative_eq!(
                parallel_deltas[i],
                serial_deltas[i],
                epsilon = NUMERICAL_TOLERANCE
            );
        }

        // Gamma
        let parallel_gammas = gamma_batch_parallel(&small_spots, k, t, r, v);
        let serial_gammas = crate::models::greeks::gamma_batch(&small_spots, k, t, r, v);
        for i in 0..small_spots.len() {
            assert_relative_eq!(
                parallel_gammas[i],
                serial_gammas[i],
                epsilon = NUMERICAL_TOLERANCE
            );
        }

        // Vega
        let parallel_vegas = vega_batch_parallel(&small_spots, k, t, r, v);
        let serial_vegas = crate::models::greeks::vega_batch(&small_spots, k, t, r, v);
        for i in 0..small_spots.len() {
            assert_relative_eq!(
                parallel_vegas[i],
                serial_vegas[i],
                epsilon = NUMERICAL_TOLERANCE
            );
        }
    }

    #[test]
    fn test_large_batch_parallel() {
        // 並列化閾値を超えるデータ（実際のテストではもっと小さいデータで確認）
        let large_spots: Vec<f64> = (0..1000).map(|i| 80.0 + i as f64 * 0.04).collect();
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let v = 0.2;

        // 全グリークス並列計算
        let greeks_call = calculate_all_greeks_batch_parallel(&large_spots, k, t, r, v, true);
        assert_eq!(greeks_call.len(), large_spots.len());

        // 最初と最後の要素を確認
        let first_greeks = calculate_all_greeks(large_spots[0], k, t, r, v, true);
        assert_relative_eq!(
            greeks_call[0].delta,
            first_greeks.delta,
            epsilon = NUMERICAL_TOLERANCE
        );

        let last_idx = large_spots.len() - 1;
        let last_greeks = calculate_all_greeks(large_spots[last_idx], k, t, r, v, true);
        assert_relative_eq!(
            greeks_call[last_idx].delta,
            last_greeks.delta,
            epsilon = NUMERICAL_TOLERANCE
        );
    }

    #[test]
    fn test_python_wrappers() {
        let spots = vec![90.0, 100.0, 110.0];
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let v = 0.2;

        // Python向けラッパーのテスト
        let delta_call = delta_call_batch_parallel_py(&spots, k, t, r, v);
        assert_eq!(delta_call.len(), spots.len());

        let gamma = gamma_batch_parallel_py(&spots, k, t, r, v);
        assert_eq!(gamma.len(), spots.len());

        let vega = vega_batch_parallel_py(&spots, k, t, r, v);
        assert_eq!(vega.len(), spots.len());
    }
}
