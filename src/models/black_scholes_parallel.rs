use crate::math::distributions::norm_cdf;
use rayon::prelude::*;

// 並列化の閾値（ZERO HARDCODE準拠）
const PARALLEL_THRESHOLD: usize = 10000;  // 並列化する最小要素数
const CHUNK_SIZE: usize = 8192;           // L1キャッシュに収まる最適サイズ

/// 並列化されたバッチ価格計算
///
/// # Arguments
/// * `spots` - スポット価格の配列
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - リスクフリーレート
/// * `v` - インプライドボラティリティ
///
/// # Returns
/// 各スポット価格に対応するコールオプション価格
pub fn bs_call_price_batch_parallel(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    // 小規模データはシングルスレッドで処理
    if spots.len() < PARALLEL_THRESHOLD {
        return super::bs_call_price_batch(spots, k, t, r, v);
    }
    
    // 共通項の事前計算
    let sqrt_t = t.sqrt();
    let v_sqrt_t = v * sqrt_t;
    let exp_neg_rt = (-r * t).exp();
    let half_v_squared_t = (r + v * v / 2.0) * t;
    let k_ln = k.ln();
    
    // Rayonによる並列処理
    spots
        .par_chunks(CHUNK_SIZE)
        .flat_map(|chunk| {
            chunk
                .iter()
                .map(|&s| {
                    let d1 = (s.ln() - k_ln + half_v_squared_t) / v_sqrt_t;
                    let d2 = d1 - v_sqrt_t;
                    // Deep OTMでの負値防止
                    (s * norm_cdf(d1) - k * exp_neg_rt * norm_cdf(d2)).max(0.0)
                })
                .collect::<Vec<_>>()
        })
        .collect()
}

/// 並列化されたバッチ価格計算（PyO3バインディング用）
pub fn bs_call_price_batch_parallel_py(spots: Vec<f64>, k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    bs_call_price_batch_parallel(&spots, k, t, r, v)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::NUMERICAL_TOLERANCE;
    use approx::assert_relative_eq;

    #[test]
    fn test_parallel_consistency() {
        // 大規模データセットで並列版と非並列版の一致を確認
        let n = 50000;
        let spots: Vec<f64> = (0..n).map(|i| 50.0 + (i as f64) * 0.002).collect();
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let v = 0.2;

        let sequential = super::super::bs_call_price_batch(&spots, k, t, r, v);
        let parallel = bs_call_price_batch_parallel(&spots, k, t, r, v);

        assert_eq!(sequential.len(), parallel.len());
        
        // 各要素が一致することを確認
        for (i, (s, p)) in sequential.iter().zip(parallel.iter()).enumerate() {
            assert_relative_eq!(s, p, epsilon = NUMERICAL_TOLERANCE);
            if (s - p).abs() > NUMERICAL_TOLERANCE {
                panic!("不一致 at index {i}: sequential={s}, parallel={p}");
            }
        }
    }

    #[test]
    fn test_small_batch_fallback() {
        // 小規模バッチではシングルスレッド実行
        let spots = vec![90.0, 100.0, 110.0];
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let v = 0.2;

        let result = bs_call_price_batch_parallel(&spots, k, t, r, v);
        assert_eq!(result.len(), 3);
        
        // 値の妥当性確認
        assert!(result[0] < result[1]); // OTM < ATM
        assert!(result[1] < result[2]); // ATM < ITM
    }

    #[test]
    fn test_chunk_processing() {
        // チャンク境界での正しい処理を確認
        let n = CHUNK_SIZE * 3 + 100; // 3チャンク + 端数
        let spots: Vec<f64> = vec![100.0; n];
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let v = 0.2;

        let result = bs_call_price_batch_parallel(&spots, k, t, r, v);
        assert_eq!(result.len(), n);
        
        // 全要素が同じ値（ATM価格）
        let expected = result[0];
        for price in &result {
            assert_relative_eq!(price, &expected, epsilon = NUMERICAL_TOLERANCE);
        }
    }
}