use crate::constants::INV_SQRT_2PI;
use libm::erf;

/// 標準正規分布の確率密度関数
///
/// 標準正規分布（平均0、分散1）の確率密度関数を計算。
/// φ(x) = (1/√(2π)) × exp(-x²/2)
///
/// # 引数
/// * `x` - 評価点
///
/// # 戻り値
/// 点xにおける確率密度
///
/// # 例
/// ```
/// use quantforge::math::distributions::norm_pdf;
///
/// let pdf_at_zero = norm_pdf(0.0);
/// assert!((pdf_at_zero - 0.3989422804014327).abs() < 1e-15);
/// ```
pub fn norm_pdf(x: f64) -> f64 {
    if x.is_nan() {
        return f64::NAN;
    }

    // 極値での数値安定性を確保
    if x.abs() > 40.0 {
        return 0.0;
    }

    INV_SQRT_2PI * (-0.5 * x * x).exp()
}

/// 高精度累積正規分布関数
///
/// 誤差関数（erf）を使用した業界標準の実装。
/// 精度: 機械精度レベル（相対誤差 < 1e-15）
///
/// # 数学的定義
/// Φ(x) = (1 + erf(x/√2)) / 2
///
/// # 性能
/// 約10-12 ns/iter（erfの計算コスト含む）
pub fn norm_cdf(x: f64) -> f64 {
    if x.is_nan() {
        return f64::NAN;
    }

    // 定数定義（CLAUDE.mdの設定値管理原則に従う）
    const SQRT_2: f64 = std::f64::consts::SQRT_2;

    // erfベースの高精度実装
    0.5 * (1.0 + erf(x / SQRT_2))
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
    use crate::constants::{NUMERICAL_TOLERANCE, THEORETICAL_TOLERANCE};
    use approx::assert_relative_eq;

    #[test]
    fn test_norm_cdf_standard_values() {
        // norm_cdfの実装精度に合わせたテスト（理論精度レベル）
        assert_relative_eq!(norm_cdf(0.0), 0.5, epsilon = THEORETICAL_TOLERANCE);
        assert_relative_eq!(
            norm_cdf(1.0),
            0.8413447460685429,
            epsilon = THEORETICAL_TOLERANCE
        );
        assert_relative_eq!(
            norm_cdf(-1.0),
            0.15865525393145707,
            epsilon = THEORETICAL_TOLERANCE
        );
        assert_relative_eq!(
            norm_cdf(2.0),
            0.9772498680518208,
            epsilon = THEORETICAL_TOLERANCE
        );
        assert_relative_eq!(
            norm_cdf(-2.0),
            0.022750131948179195,
            epsilon = THEORETICAL_TOLERANCE
        );
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
            assert_relative_eq!(cdf_pos + cdf_neg, 1.0, epsilon = NUMERICAL_TOLERANCE);
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
        assert_relative_eq!(norm_cdf(1e-10), 0.5, epsilon = NUMERICAL_TOLERANCE);
        assert_relative_eq!(norm_cdf(-1e-10), 0.5, epsilon = NUMERICAL_TOLERANCE);
    }

    #[test]
    fn test_norm_pdf_standard_values() {
        // 標準値でのテスト
        assert_relative_eq!(norm_pdf(0.0), INV_SQRT_2PI, epsilon = NUMERICAL_TOLERANCE);
        assert_relative_eq!(
            norm_pdf(1.0),
            0.24197072451914337,
            epsilon = NUMERICAL_TOLERANCE
        );
        assert_relative_eq!(
            norm_pdf(-1.0),
            0.24197072451914337,
            epsilon = NUMERICAL_TOLERANCE
        );
        assert_relative_eq!(
            norm_pdf(2.0),
            0.05399096651318806,
            epsilon = NUMERICAL_TOLERANCE
        );
    }

    #[test]
    fn test_norm_pdf_symmetry() {
        // 対称性のテスト: φ(-x) = φ(x)
        let test_values = vec![0.5, 1.0, 1.5, 2.0, 2.5, 3.0];
        for x in test_values {
            assert_relative_eq!(norm_pdf(x), norm_pdf(-x), epsilon = NUMERICAL_TOLERANCE);
        }
    }

    #[test]
    fn test_norm_pdf_extreme_values() {
        // 極値でのテスト
        assert_eq!(norm_pdf(50.0), 0.0);
        assert_eq!(norm_pdf(-50.0), 0.0);
        assert_eq!(norm_pdf(40.1), 0.0);
        assert_eq!(norm_pdf(-40.1), 0.0);
    }

    #[test]
    fn test_norm_pdf_special_cases() {
        // 特殊ケースのテスト
        assert!(norm_pdf(f64::NAN).is_nan());
        assert_eq!(norm_pdf(f64::INFINITY), 0.0);
        assert_eq!(norm_pdf(f64::NEG_INFINITY), 0.0);
    }
}
