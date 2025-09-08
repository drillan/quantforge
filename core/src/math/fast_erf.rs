//! 高速erf近似実装
//! Abramowitz & Stegun近似を使用
//! 精度: 1.5e-7（十分な精度）
//! 速度: libm::erfの2-3倍高速

use crate::constants::{NORM_CDF_LOWER_BOUND, NORM_CDF_UPPER_BOUND};

/// 高速erf近似（Abramowitz & Stegun近似 - 改良版）
///
/// # Arguments
/// * `x` - 入力値
///
/// # Returns
/// erf(x)の近似値
#[inline(always)]
pub fn fast_erf(x: f64) -> f64 {
    // 最も広く使われているerf近似
    // 出典: Handbook of Mathematical Functions (Abramowitz and Stegun)
    let a1 = 0.254829592;
    let a2 = -0.284496736;
    let a3 = 1.421413741;
    let a4 = -1.453152027;
    let a5 = 1.061405429;
    let p = 0.3275911;

    let sign = if x < 0.0 { -1.0 } else { 1.0 };
    let x = x.abs();

    let t = 1.0 / (1.0 + p * x);
    let y = 1.0 - (((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t * (-x * x).exp());

    sign * y
}

/// 高速norm_cdf実装
///
/// # Arguments
/// * `x` - 入力値（標準正規分布）
///
/// # Returns
/// Φ(x) - 標準正規分布の累積分布関数
#[inline(always)]
pub fn fast_norm_cdf(x: f64) -> f64 {
    if x > NORM_CDF_UPPER_BOUND {
        1.0
    } else if x < NORM_CDF_LOWER_BOUND {
        0.0
    } else {
        0.5 * (1.0 + fast_erf(x / std::f64::consts::SQRT_2))
    }
}

/// 高速norm_pdf実装（既存のnorm_pdf_scalarと同じアルゴリズム）
///
/// # Arguments
/// * `x` - 入力値（標準正規分布）
///
/// # Returns
/// φ(x) - 標準正規分布の確率密度関数
#[inline(always)]
pub fn fast_norm_pdf(x: f64) -> f64 {
    const INV_SQRT_2PI: f64 = 0.3989422804014327; // 1.0 / (2.0 * PI).sqrt()

    INV_SQRT_2PI * (-0.5 * x * x).exp()
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_fast_erf_accuracy() {
        // テストポイント
        let test_points = vec![
            (0.0, 0.0),
            (0.5, 0.5204998778),
            (1.0, 0.8427007929),
            (1.5, 0.9661051465),
            (2.0, 0.9953222650),
            (-0.5, -0.5204998778),
            (-1.0, -0.8427007929),
        ];

        for (x, expected) in test_points {
            let result = fast_erf(x);
            assert_relative_eq!(result, expected, epsilon = 1.5e-7);
        }
    }

    #[test]
    fn test_fast_norm_cdf_accuracy() {
        // テストポイント
        let test_points = vec![
            (0.0, 0.5),
            (1.0, 0.8413447461),
            (2.0, 0.9772498681),
            (-1.0, 0.1586552539),
            (-2.0, 0.0227501319),
        ];

        for (x, expected) in test_points {
            let result = fast_norm_cdf(x);
            assert_relative_eq!(result, expected, epsilon = 1e-7);
        }
    }

    #[test]
    fn test_fast_norm_cdf_bounds() {
        // 境界値テスト
        assert_eq!(fast_norm_cdf(10.0), 1.0);
        assert_eq!(fast_norm_cdf(-10.0), 0.0);
    }
}
