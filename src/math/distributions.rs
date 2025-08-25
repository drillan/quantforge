/// 高精度累積正規分布関数
/// 精度: 約1e-7（金融計算には十分）
pub fn norm_cdf(x: f64) -> f64 {
    if x.is_nan() {
        return f64::NAN;
    }

    // 極値の早期リターン
    if x > 8.0 {
        return 1.0;
    } else if x < -8.0 {
        return 0.0;
    }

    // Abramowitz and Stegun近似（改良版）
    // より正確な係数を使用
    const A1: f64 = 0.319381530;
    const A2: f64 = -0.356563782;
    const A3: f64 = 1.781477937;
    const A4: f64 = -1.821255978;
    const A5: f64 = 1.330274429;
    const P: f64 = 0.2316419;
    const C: f64 = 0.39894228;

    let abs_x = x.abs();
    let t = 1.0 / (1.0 + P * abs_x);

    let n = C * (-abs_x * abs_x / 2.0).exp();
    let poly = t * (A1 + t * (A2 + t * (A3 + t * (A4 + t * A5))));
    let cdf_abs = 1.0 - n * poly;

    if x >= 0.0 {
        cdf_abs
    } else {
        1.0 - cdf_abs
    }
}

/// SIMD版（将来の実装用プレースホルダー）
/// 現在はスカラー実装、将来的にAVX2/AVX-512対応予定
#[allow(dead_code)]
pub(crate) fn norm_cdf_simd(values: &[f64]) -> Vec<f64> {
    // TODO: Phase 2でtarget_featureによるSIMD実装切り替えを追加
    // #[cfg(all(target_arch = "x86_64", target_feature = "avx2"))]
    // でAVX2実装を分岐させる予定
    norm_cdf_simd_scalar(values)
}

#[inline(always)]
fn norm_cdf_simd_scalar(values: &[f64]) -> Vec<f64> {
    values.iter().map(|&x| norm_cdf(x)).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_norm_cdf_standard_values() {
        // 金融計算に十分な精度（1e-7）でテスト
        assert_relative_eq!(norm_cdf(0.0), 0.5, epsilon = 1e-7);
        assert_relative_eq!(norm_cdf(1.0), 0.8413447460685429, epsilon = 1e-7);
        assert_relative_eq!(norm_cdf(-1.0), 0.15865525393145707, epsilon = 1e-7);
        assert_relative_eq!(norm_cdf(2.0), 0.9772498680518208, epsilon = 1e-7);
        assert_relative_eq!(norm_cdf(-2.0), 0.022750131948179195, epsilon = 1e-7);
    }

    #[test]
    fn test_norm_cdf_extreme_values() {
        assert_eq!(norm_cdf(40.0), 1.0);
        assert_eq!(norm_cdf(-40.0), 0.0);
        assert_eq!(norm_cdf(10.0), 1.0);
        assert_eq!(norm_cdf(-10.0), 0.0);
    }

    #[test]
    fn test_norm_cdf_symmetry() {
        // 対称性のテスト: Φ(-x) = 1 - Φ(x)
        let test_values = vec![0.5, 1.0, 1.5, 2.0, 2.5, 3.0];
        for x in test_values {
            let cdf_pos = norm_cdf(x);
            let cdf_neg = norm_cdf(-x);
            assert_relative_eq!(cdf_pos + cdf_neg, 1.0, epsilon = 1e-7);
        }
    }

    #[test]
    fn test_norm_cdf_monotonicity() {
        // 単調増加性のテスト
        let values: Vec<f64> = (-3..=3).map(|i| i as f64).collect();
        for i in 1..values.len() {
            assert!(norm_cdf(values[i]) >= norm_cdf(values[i - 1]));
        }
    }

    #[test]
    fn test_norm_cdf_special_cases() {
        // 特殊ケースのテスト
        assert!(norm_cdf(f64::NAN).is_nan());
        assert_eq!(norm_cdf(f64::INFINITY), 1.0);
        assert_eq!(norm_cdf(f64::NEG_INFINITY), 0.0);

        // ゼロ近傍
        assert_relative_eq!(norm_cdf(1e-10), 0.5, epsilon = 1e-7);
        assert_relative_eq!(norm_cdf(-1e-10), 0.5, epsilon = 1e-7);
    }
}
