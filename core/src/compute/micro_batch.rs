//! マイクロバッチ専用最適化
//!
//! 100-1000要素の小規模バッチ処理に特化した最適化実装。
//! ループアンローリングとコンパイラの自動ベクトル化を促進。

use super::formulas::{black_scholes_call_scalar, black_scholes_put_scalar};
use crate::constants::MICRO_BATCH_THRESHOLD;

/// 4要素ループアンローリング版 Black-Scholesコール価格計算
///
/// # Arguments
/// * `spots` - スポット価格配列
/// * `strikes` - 権利行使価格配列
/// * `times` - 満期までの時間配列
/// * `rates` - 無リスク金利配列
/// * `sigmas` - ボラティリティ配列
/// * `output` - 出力先配列
#[inline(always)]
pub fn black_scholes_call_micro_batch(
    spots: &[f64],
    strikes: &[f64],
    times: &[f64],
    rates: &[f64],
    sigmas: &[f64],
    output: &mut [f64],
) {
    let len = spots.len();
    let chunks = len / 4;

    // 4要素単位で処理（コンパイラの自動ベクトル化を促進）
    for i in 0..chunks {
        let idx = i * 4;
        output[idx] = black_scholes_call_scalar(
            spots[idx],
            strikes[idx],
            times[idx],
            rates[idx],
            sigmas[idx],
        );
        output[idx + 1] = black_scholes_call_scalar(
            spots[idx + 1],
            strikes[idx + 1],
            times[idx + 1],
            rates[idx + 1],
            sigmas[idx + 1],
        );
        output[idx + 2] = black_scholes_call_scalar(
            spots[idx + 2],
            strikes[idx + 2],
            times[idx + 2],
            rates[idx + 2],
            sigmas[idx + 2],
        );
        output[idx + 3] = black_scholes_call_scalar(
            spots[idx + 3],
            strikes[idx + 3],
            times[idx + 3],
            rates[idx + 3],
            sigmas[idx + 3],
        );
    }

    // 余りを処理
    for i in (chunks * 4)..len {
        output[i] = black_scholes_call_scalar(spots[i], strikes[i], times[i], rates[i], sigmas[i]);
    }
}

/// 4要素ループアンローリング版 Black-Scholesプット価格計算
#[inline(always)]
pub fn black_scholes_put_micro_batch(
    spots: &[f64],
    strikes: &[f64],
    times: &[f64],
    rates: &[f64],
    sigmas: &[f64],
    output: &mut [f64],
) {
    let len = spots.len();
    let chunks = len / 4;

    // 4要素単位で処理
    for i in 0..chunks {
        let idx = i * 4;
        output[idx] = black_scholes_put_scalar(
            spots[idx],
            strikes[idx],
            times[idx],
            rates[idx],
            sigmas[idx],
        );
        output[idx + 1] = black_scholes_put_scalar(
            spots[idx + 1],
            strikes[idx + 1],
            times[idx + 1],
            rates[idx + 1],
            sigmas[idx + 1],
        );
        output[idx + 2] = black_scholes_put_scalar(
            spots[idx + 2],
            strikes[idx + 2],
            times[idx + 2],
            rates[idx + 2],
            sigmas[idx + 2],
        );
        output[idx + 3] = black_scholes_put_scalar(
            spots[idx + 3],
            strikes[idx + 3],
            times[idx + 3],
            rates[idx + 3],
            sigmas[idx + 3],
        );
    }

    // 余りを処理
    for i in (chunks * 4)..len {
        output[i] = black_scholes_put_scalar(spots[i], strikes[i], times[i], rates[i], sigmas[i]);
    }
}

/// マイクロバッチ最適化が有効かどうかを判定
#[inline(always)]
pub fn should_use_micro_batch(len: usize) -> bool {
    (4..=MICRO_BATCH_THRESHOLD).contains(&len)
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_micro_batch_call() {
        let spots = vec![100.0, 105.0, 110.0, 115.0];
        let strikes = vec![100.0; 4];
        let times = vec![1.0; 4];
        let rates = vec![0.05; 4];
        let sigmas = vec![0.2; 4];
        let mut output = vec![0.0; 4];

        black_scholes_call_micro_batch(&spots, &strikes, &times, &rates, &sigmas, &mut output);

        // 各要素が正しく計算されているか確認
        for (i, &spot) in spots.iter().enumerate() {
            let expected = black_scholes_call_scalar(spot, 100.0, 1.0, 0.05, 0.2);
            assert_relative_eq!(output[i], expected, epsilon = 1e-10);
        }
    }

    #[test]
    fn test_micro_batch_with_remainder() {
        let spots = vec![100.0, 105.0, 110.0, 115.0, 120.0]; // 5要素（余り1）
        let strikes = vec![100.0; 5];
        let times = vec![1.0; 5];
        let rates = vec![0.05; 5];
        let sigmas = vec![0.2; 5];
        let mut output = vec![0.0; 5];

        black_scholes_call_micro_batch(&spots, &strikes, &times, &rates, &sigmas, &mut output);

        // 全要素が正しく計算されているか確認
        for (i, &spot) in spots.iter().enumerate() {
            let expected = black_scholes_call_scalar(spot, 100.0, 1.0, 0.05, 0.2);
            assert_relative_eq!(output[i], expected, epsilon = 1e-10);
        }
    }
}
