//! Black-Scholesグリークス計算モジュール
//!
//! オプションのリスク指標（グリークス）を解析的に計算する関数群を提供。
//! 全ての計算は高精度（相対誤差 < 1e-7）で実行される。

use crate::constants::{BASIS_POINT_MULTIPLIER, DAYS_PER_YEAR};
use crate::math::distributions::{norm_cdf, norm_pdf};

/// グリークス構造体
///
/// オプションの全てのグリークスを格納する構造体
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Greeks {
    pub delta: f64,
    pub gamma: f64,
    pub vega: f64,
    pub theta: f64,
    pub rho: f64,
}

impl Greeks {
    /// 新しいGreeks構造体を作成
    pub fn new(delta: f64, gamma: f64, vega: f64, theta: f64, rho: f64) -> Self {
        Self {
            delta,
            gamma,
            vega,
            theta,
            rho,
        }
    }
}

/// d1パラメータの計算（Black-Scholes共通）
#[inline(always)]
fn calculate_d1(s: f64, k: f64, t: f64, r: f64, v: f64) -> f64 {
    let sqrt_t = t.sqrt();
    (s.ln() - k.ln() + (r + 0.5 * v * v) * t) / (v * sqrt_t)
}

/// d2パラメータの計算（Black-Scholes共通）
#[inline(always)]
fn calculate_d2(d1: f64, v: f64, sqrt_t: f64) -> f64 {
    d1 - v * sqrt_t
}

/// コールオプションのDelta計算
///
/// Delta = ∂C/∂S = N(d1)
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - リスクフリーレート
/// * `v` - インプライドボラティリティ
///
/// # Returns
/// コールオプションのDelta（0から1の範囲）
pub fn delta_call(s: f64, k: f64, t: f64, r: f64, v: f64) -> f64 {
    // エッジケース処理
    if t <= 0.0 {
        return if s > k { 1.0 } else { 0.0 };
    }

    let d1 = calculate_d1(s, k, t, r, v);
    norm_cdf(d1)
}

/// プットオプションのDelta計算
///
/// Delta = ∂P/∂S = -N(-d1) = N(d1) - 1
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - リスクフリーレート
/// * `v` - インプライドボラティリティ
///
/// # Returns
/// プットオプションのDelta（-1から0の範囲）
pub fn delta_put(s: f64, k: f64, t: f64, r: f64, v: f64) -> f64 {
    // エッジケース処理
    if t <= 0.0 {
        return if s < k { -1.0 } else { 0.0 };
    }

    let d1 = calculate_d1(s, k, t, r, v);
    norm_cdf(d1) - 1.0
}

/// オプションのGamma計算（コール・プット共通）
///
/// Gamma = ∂²C/∂S² = ∂²P/∂S² = φ(d1) / (S × σ × √T)
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - リスクフリーレート
/// * `v` - インプライドボラティリティ
///
/// # Returns
/// オプションのGamma（常に正の値）
pub fn gamma(s: f64, k: f64, t: f64, r: f64, v: f64) -> f64 {
    // エッジケース処理
    if t <= 0.0 || v <= 0.0 || s <= 0.0 {
        return 0.0;
    }

    let sqrt_t = t.sqrt();
    let d1 = calculate_d1(s, k, t, r, v);
    norm_pdf(d1) / (s * v * sqrt_t)
}

/// コールオプションのDeltaバッチ計算
///
/// 複数のスポット価格に対してDeltaを一括計算
pub fn delta_call_batch(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    // エッジケース処理
    if t <= 0.0 {
        return spots
            .iter()
            .map(|&s| if s > k { 1.0 } else { 0.0 })
            .collect();
    }

    // 共通項の事前計算
    let sqrt_t = t.sqrt();
    let v_sqrt_t = v * sqrt_t;
    let half_v_squared_t = (r + 0.5 * v * v) * t;
    let k_ln = k.ln();

    spots
        .iter()
        .map(|&s| {
            let d1 = (s.ln() - k_ln + half_v_squared_t) / v_sqrt_t;
            norm_cdf(d1)
        })
        .collect()
}

/// プットオプションのDeltaバッチ計算
///
/// 複数のスポット価格に対してDeltaを一括計算
pub fn delta_put_batch(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    // エッジケース処理
    if t <= 0.0 {
        return spots
            .iter()
            .map(|&s| if s < k { -1.0 } else { 0.0 })
            .collect();
    }

    // 共通項の事前計算
    let sqrt_t = t.sqrt();
    let v_sqrt_t = v * sqrt_t;
    let half_v_squared_t = (r + 0.5 * v * v) * t;
    let k_ln = k.ln();

    spots
        .iter()
        .map(|&s| {
            let d1 = (s.ln() - k_ln + half_v_squared_t) / v_sqrt_t;
            norm_cdf(d1) - 1.0
        })
        .collect()
}

/// Gammaバッチ計算
///
/// 複数のスポット価格に対してGammaを一括計算
pub fn gamma_batch(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    // エッジケース処理
    if t <= 0.0 || v <= 0.0 {
        return vec![0.0; spots.len()];
    }

    // 共通項の事前計算
    let sqrt_t = t.sqrt();
    let v_sqrt_t = v * sqrt_t;
    let half_v_squared_t = (r + 0.5 * v * v) * t;
    let k_ln = k.ln();

    spots
        .iter()
        .map(|&s| {
            if s <= 0.0 {
                0.0
            } else {
                let d1 = (s.ln() - k_ln + half_v_squared_t) / v_sqrt_t;
                norm_pdf(d1) / (s * v_sqrt_t)
            }
        })
        .collect()
}

/// オプションのVega計算（コール・プット共通）
///
/// Vega = ∂C/∂σ = ∂P/∂σ = S × φ(d1) × √T / 100
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - リスクフリーレート
/// * `v` - インプライドボラティリティ
///
/// # Returns
/// オプションのVega（1%ボラティリティ変化に対する感応度）
pub fn vega(s: f64, k: f64, t: f64, r: f64, v: f64) -> f64 {
    // エッジケース処理
    if t <= 0.0 || s <= 0.0 {
        return 0.0;
    }

    let sqrt_t = t.sqrt();
    let d1 = calculate_d1(s, k, t, r, v);
    s * norm_pdf(d1) * sqrt_t / BASIS_POINT_MULTIPLIER
}

/// コールオプションのTheta計算
///
/// Theta = -∂C/∂t = -[S×φ(d1)×σ/(2√T) + r×K×e^(-rT)×N(d2)] / 365
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - リスクフリーレート
/// * `v` - インプライドボラティリティ
///
/// # Returns
/// コールオプションのTheta（1日あたりの時間価値減少）
pub fn theta_call(s: f64, k: f64, t: f64, r: f64, v: f64) -> f64 {
    // エッジケース処理
    if t <= 0.0 {
        return 0.0;
    }

    let sqrt_t = t.sqrt();
    let d1 = calculate_d1(s, k, t, r, v);
    let d2 = calculate_d2(d1, v, sqrt_t);
    let exp_neg_rt = (-r * t).exp();

    -(s * norm_pdf(d1) * v / (2.0 * sqrt_t) + r * k * exp_neg_rt * norm_cdf(d2)) / DAYS_PER_YEAR
}

/// プットオプションのTheta計算
///
/// Theta = -∂P/∂t = -[S×φ(d1)×σ/(2√T) - r×K×e^(-rT)×N(-d2)] / 365
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - リスクフリーレート
/// * `v` - インプライドボラティリティ
///
/// # Returns
/// プットオプションのTheta（1日あたりの時間価値減少）
pub fn theta_put(s: f64, k: f64, t: f64, r: f64, v: f64) -> f64 {
    // エッジケース処理
    if t <= 0.0 {
        return 0.0;
    }

    let sqrt_t = t.sqrt();
    let d1 = calculate_d1(s, k, t, r, v);
    let d2 = calculate_d2(d1, v, sqrt_t);
    let exp_neg_rt = (-r * t).exp();

    -(s * norm_pdf(d1) * v / (2.0 * sqrt_t) - r * k * exp_neg_rt * norm_cdf(-d2)) / DAYS_PER_YEAR
}

/// コールオプションのRho計算
///
/// Rho = ∂C/∂r = K×T×e^(-rT)×N(d2) / 100
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - リスクフリーレート
/// * `v` - インプライドボラティリティ
///
/// # Returns
/// コールオプションのRho（1%金利変化に対する感応度）
pub fn rho_call(s: f64, k: f64, t: f64, r: f64, v: f64) -> f64 {
    // エッジケース処理
    if t <= 0.0 {
        return 0.0;
    }

    let sqrt_t = t.sqrt();
    let d1 = calculate_d1(s, k, t, r, v);
    let d2 = calculate_d2(d1, v, sqrt_t);
    let exp_neg_rt = (-r * t).exp();

    k * t * exp_neg_rt * norm_cdf(d2) / BASIS_POINT_MULTIPLIER
}

/// プットオプションのRho計算
///
/// Rho = ∂P/∂r = -K×T×e^(-rT)×N(-d2) / 100
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - リスクフリーレート
/// * `v` - インプライドボラティリティ
///
/// # Returns
/// プットオプションのRho（1%金利変化に対する感応度）
pub fn rho_put(s: f64, k: f64, t: f64, r: f64, v: f64) -> f64 {
    // エッジケース処理
    if t <= 0.0 {
        return 0.0;
    }

    let sqrt_t = t.sqrt();
    let d1 = calculate_d1(s, k, t, r, v);
    let d2 = calculate_d2(d1, v, sqrt_t);
    let exp_neg_rt = (-r * t).exp();

    -k * t * exp_neg_rt * norm_cdf(-d2) / BASIS_POINT_MULTIPLIER
}

/// 全グリークス一括計算
///
/// 全てのグリークスを効率的に一括計算する。
/// 共通の中間計算を再利用することで計算効率を向上。
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - リスクフリーレート
/// * `v` - インプライドボラティリティ
/// * `is_call` - コールオプションの場合はtrue、プットの場合はfalse
///
/// # Returns
/// 全グリークスを含むGreeks構造体
pub fn calculate_all_greeks(s: f64, k: f64, t: f64, r: f64, v: f64, is_call: bool) -> Greeks {
    // エッジケース処理
    if t <= 0.0 {
        return Greeks::new(
            if is_call {
                if s > k {
                    1.0
                } else {
                    0.0
                }
            } else if s < k {
                -1.0
            } else {
                0.0
            },
            0.0,
            0.0,
            0.0,
            0.0,
        );
    }

    // 共通計算
    let sqrt_t = t.sqrt();
    let d1 = calculate_d1(s, k, t, r, v);
    let d2 = calculate_d2(d1, v, sqrt_t);
    let nd1 = norm_cdf(d1);
    let nd2 = norm_cdf(d2);
    let pd1 = norm_pdf(d1);
    let exp_neg_rt = (-r * t).exp();

    // Delta
    let delta = if is_call { nd1 } else { nd1 - 1.0 };

    // Gamma（コール・プット共通）
    let gamma = if v > 0.0 && s > 0.0 {
        pd1 / (s * v * sqrt_t)
    } else {
        0.0
    };

    // Vega（コール・プット共通）
    let vega = s * pd1 * sqrt_t / BASIS_POINT_MULTIPLIER;

    // Theta
    let common_theta = s * pd1 * v / (2.0 * sqrt_t);
    let theta = if is_call {
        -(common_theta + r * k * exp_neg_rt * nd2) / DAYS_PER_YEAR
    } else {
        -(common_theta - r * k * exp_neg_rt * norm_cdf(-d2)) / DAYS_PER_YEAR
    };

    // Rho
    let rho = if is_call {
        k * t * exp_neg_rt * nd2 / BASIS_POINT_MULTIPLIER
    } else {
        -k * t * exp_neg_rt * norm_cdf(-d2) / BASIS_POINT_MULTIPLIER
    };

    Greeks::new(delta, gamma, vega, theta, rho)
}

/// Vegaバッチ計算
///
/// 複数のスポット価格に対してVegaを一括計算
pub fn vega_batch(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    if t <= 0.0 {
        return vec![0.0; spots.len()];
    }

    let sqrt_t = t.sqrt();
    let v_sqrt_t = v * sqrt_t;
    let half_v_squared_t = (r + 0.5 * v * v) * t;
    let k_ln = k.ln();

    spots
        .iter()
        .map(|&s| {
            if s <= 0.0 {
                0.0
            } else {
                let d1 = (s.ln() - k_ln + half_v_squared_t) / v_sqrt_t;
                s * norm_pdf(d1) * sqrt_t / BASIS_POINT_MULTIPLIER
            }
        })
        .collect()
}

/// コールThetaバッチ計算
pub fn theta_call_batch(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    if t <= 0.0 {
        return vec![0.0; spots.len()];
    }

    let sqrt_t = t.sqrt();
    let v_sqrt_t = v * sqrt_t;
    let half_v_squared_t = (r + 0.5 * v * v) * t;
    let k_ln = k.ln();
    let exp_neg_rt = (-r * t).exp();

    spots
        .iter()
        .map(|&s| {
            let d1 = (s.ln() - k_ln + half_v_squared_t) / v_sqrt_t;
            let d2 = d1 - v_sqrt_t;
            -(s * norm_pdf(d1) * v / (2.0 * sqrt_t) + r * k * exp_neg_rt * norm_cdf(d2))
                / DAYS_PER_YEAR
        })
        .collect()
}

/// プットThetaバッチ計算
pub fn theta_put_batch(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    if t <= 0.0 {
        return vec![0.0; spots.len()];
    }

    let sqrt_t = t.sqrt();
    let v_sqrt_t = v * sqrt_t;
    let half_v_squared_t = (r + 0.5 * v * v) * t;
    let k_ln = k.ln();
    let exp_neg_rt = (-r * t).exp();

    spots
        .iter()
        .map(|&s| {
            let d1 = (s.ln() - k_ln + half_v_squared_t) / v_sqrt_t;
            let d2 = d1 - v_sqrt_t;
            -(s * norm_pdf(d1) * v / (2.0 * sqrt_t) - r * k * exp_neg_rt * norm_cdf(-d2))
                / DAYS_PER_YEAR
        })
        .collect()
}

/// コールRhoバッチ計算
pub fn rho_call_batch(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    if t <= 0.0 {
        return vec![0.0; spots.len()];
    }

    let sqrt_t = t.sqrt();
    let v_sqrt_t = v * sqrt_t;
    let half_v_squared_t = (r + 0.5 * v * v) * t;
    let k_ln = k.ln();
    let exp_neg_rt = (-r * t).exp();

    spots
        .iter()
        .map(|&s| {
            let d1 = (s.ln() - k_ln + half_v_squared_t) / v_sqrt_t;
            let d2 = d1 - v_sqrt_t;
            k * t * exp_neg_rt * norm_cdf(d2) / BASIS_POINT_MULTIPLIER
        })
        .collect()
}

/// プットRhoバッチ計算
pub fn rho_put_batch(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    if t <= 0.0 {
        return vec![0.0; spots.len()];
    }

    let sqrt_t = t.sqrt();
    let v_sqrt_t = v * sqrt_t;
    let half_v_squared_t = (r + 0.5 * v * v) * t;
    let k_ln = k.ln();
    let exp_neg_rt = (-r * t).exp();

    spots
        .iter()
        .map(|&s| {
            let d1 = (s.ln() - k_ln + half_v_squared_t) / v_sqrt_t;
            let d2 = d1 - v_sqrt_t;
            -k * t * exp_neg_rt * norm_cdf(-d2) / BASIS_POINT_MULTIPLIER
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::NUMERICAL_TOLERANCE;
    use approx::assert_relative_eq;

    #[test]
    fn test_delta_call_standard() {
        // ATMオプション
        let delta = delta_call(100.0, 100.0, 1.0, 0.05, 0.2);
        assert_relative_eq!(delta, 0.6368306517096883, epsilon = NUMERICAL_TOLERANCE);

        // ITMオプション
        let delta_itm = delta_call(110.0, 100.0, 1.0, 0.05, 0.2);
        assert!(delta_itm > 0.6368306517096883);
        assert!(delta_itm < 1.0);

        // OTMオプション
        let delta_otm = delta_call(90.0, 100.0, 1.0, 0.05, 0.2);
        assert!(delta_otm < 0.6368306517096883);
        assert!(delta_otm > 0.0);
    }

    #[test]
    fn test_delta_put_standard() {
        // ATMオプション
        let delta = delta_put(100.0, 100.0, 1.0, 0.05, 0.2);
        assert_relative_eq!(delta, -0.363_169_348_290_311_7, epsilon = NUMERICAL_TOLERANCE);

        // ITMプット（S < K）
        let delta_itm = delta_put(90.0, 100.0, 1.0, 0.05, 0.2);
        assert!(delta_itm < -0.363_169_348_290_311_7);
        assert!(delta_itm > -1.0);

        // OTMプット（S > K）
        let delta_otm = delta_put(110.0, 100.0, 1.0, 0.05, 0.2);
        assert!(delta_otm > -0.363_169_348_290_311_7);
        assert!(delta_otm < 0.0);
    }

    #[test]
    fn test_delta_put_call_parity() {
        // Put-Callパリティ: Delta_call - Delta_put = 1
        let s = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let v = 0.2;

        let delta_c = delta_call(s, k, t, r, v);
        let delta_p = delta_put(s, k, t, r, v);

        assert_relative_eq!(delta_c - delta_p, 1.0, epsilon = NUMERICAL_TOLERANCE);
    }

    #[test]
    fn test_gamma_standard() {
        // ATMオプション
        let g = gamma(100.0, 100.0, 1.0, 0.05, 0.2);
        // 実際の計算値に基づく期待値
        assert_relative_eq!(g, 0.018762017345846895, epsilon = NUMERICAL_TOLERANCE);

        // Gammaは常に正
        assert!(g > 0.0);

        // ITMとOTMでGammaは正
        let g_itm = gamma(110.0, 100.0, 1.0, 0.05, 0.2);
        let g_otm = gamma(90.0, 100.0, 1.0, 0.05, 0.2);
        assert!(g_itm > 0.0);
        assert!(g_otm > 0.0);
    }

    #[test]
    fn test_gamma_peak_at_atm() {
        // GammaはATM付近で最大値を取る
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let v = 0.2;

        let gamma_atm = gamma(100.0, k, t, r, v);
        let _gamma_slightly_itm = gamma(105.0, k, t, r, v);
        let _gamma_slightly_otm = gamma(95.0, k, t, r, v);
        let gamma_deep_itm = gamma(150.0, k, t, r, v);
        let gamma_deep_otm = gamma(50.0, k, t, r, v);

        // ATM付近が最大（若干のずれは許容）
        assert!(gamma_atm > gamma_deep_itm);
        assert!(gamma_atm > gamma_deep_otm);

        // Deep ITM/OTMではGammaは小さい
        assert!(gamma_deep_itm < 0.001);
        assert!(gamma_deep_otm < 0.001);
    }

    #[test]
    fn test_edge_cases() {
        // 満期時のDelta
        assert_eq!(delta_call(110.0, 100.0, 0.0, 0.05, 0.2), 1.0);
        assert_eq!(delta_call(90.0, 100.0, 0.0, 0.05, 0.2), 0.0);
        assert_eq!(delta_put(90.0, 100.0, 0.0, 0.05, 0.2), -1.0);
        assert_eq!(delta_put(110.0, 100.0, 0.0, 0.05, 0.2), 0.0);

        // 満期時のGamma
        assert_eq!(gamma(100.0, 100.0, 0.0, 0.05, 0.2), 0.0);

        // ゼロボラティリティ
        assert_eq!(gamma(100.0, 100.0, 1.0, 0.05, 0.0), 0.0);
    }

    #[test]
    fn test_vega_standard() {
        // ATMオプション
        let v = vega(100.0, 100.0, 1.0, 0.05, 0.2);
        // S * φ(d1) * √T / 100の計算結果
        assert_relative_eq!(v, 0.375_240_346_916_937_9, epsilon = NUMERICAL_TOLERANCE);

        // Vegaは常に正
        assert!(v > 0.0);

        // 満期近くでVegaは小さくなる
        let v_short = vega(100.0, 100.0, 0.1, 0.05, 0.2);
        assert!(v_short < v);
    }

    #[test]
    fn test_theta_call_standard() {
        // ATMコールオプション
        let theta = theta_call(100.0, 100.0, 1.0, 0.05, 0.2);
        // Thetaは負（時間価値の減少）
        assert!(theta < 0.0);

        // 実際の計算値との比較（1日あたりの減少）
        assert_relative_eq!(theta, -0.01757267820941972, epsilon = NUMERICAL_TOLERANCE);
    }

    #[test]
    fn test_theta_put_standard() {
        // ATMプットオプション
        let theta = theta_put(100.0, 100.0, 1.0, 0.05, 0.2);
        // プットのThetaも通常負
        assert!(theta < 0.0);

        // コールより絶対値が小さい（金利効果）
        let theta_call = theta_call(100.0, 100.0, 1.0, 0.05, 0.2);
        assert!(theta.abs() < theta_call.abs());
    }

    #[test]
    fn test_rho_call_standard() {
        // ATMコールオプション
        let rho = rho_call(100.0, 100.0, 1.0, 0.05, 0.2);
        // コールのRhoは正
        assert!(rho > 0.0);

        // 実際の計算値との比較（1%金利変化に対する感応度）
        assert_relative_eq!(rho, 0.5323248154537634, epsilon = NUMERICAL_TOLERANCE);
    }

    #[test]
    fn test_rho_put_standard() {
        // ATMプットオプション
        let rho = rho_put(100.0, 100.0, 1.0, 0.05, 0.2);
        // プットのRhoは負
        assert!(rho < 0.0);

        // 実際の計算値との比較
        assert_relative_eq!(rho, -0.4189046090469506, epsilon = NUMERICAL_TOLERANCE);
    }

    #[test]
    fn test_greeks_edge_cases_extended() {
        // 満期時のVega
        assert_eq!(vega(100.0, 100.0, 0.0, 0.05, 0.2), 0.0);

        // 満期時のTheta
        assert_eq!(theta_call(100.0, 100.0, 0.0, 0.05, 0.2), 0.0);
        assert_eq!(theta_put(100.0, 100.0, 0.0, 0.05, 0.2), 0.0);

        // 満期時のRho
        assert_eq!(rho_call(100.0, 100.0, 0.0, 0.05, 0.2), 0.0);
        assert_eq!(rho_put(100.0, 100.0, 0.0, 0.05, 0.2), 0.0);
    }

    #[test]
    fn test_calculate_all_greeks() {
        // コールオプション
        let greeks_call = calculate_all_greeks(100.0, 100.0, 1.0, 0.05, 0.2, true);

        // 個別計算と比較
        assert_relative_eq!(
            greeks_call.delta,
            delta_call(100.0, 100.0, 1.0, 0.05, 0.2),
            epsilon = NUMERICAL_TOLERANCE
        );
        assert_relative_eq!(
            greeks_call.gamma,
            gamma(100.0, 100.0, 1.0, 0.05, 0.2),
            epsilon = NUMERICAL_TOLERANCE
        );
        assert_relative_eq!(
            greeks_call.vega,
            vega(100.0, 100.0, 1.0, 0.05, 0.2),
            epsilon = NUMERICAL_TOLERANCE
        );
        assert_relative_eq!(
            greeks_call.theta,
            theta_call(100.0, 100.0, 1.0, 0.05, 0.2),
            epsilon = NUMERICAL_TOLERANCE
        );
        assert_relative_eq!(
            greeks_call.rho,
            rho_call(100.0, 100.0, 1.0, 0.05, 0.2),
            epsilon = NUMERICAL_TOLERANCE
        );

        // プットオプション
        let greeks_put = calculate_all_greeks(100.0, 100.0, 1.0, 0.05, 0.2, false);

        assert_relative_eq!(
            greeks_put.delta,
            delta_put(100.0, 100.0, 1.0, 0.05, 0.2),
            epsilon = NUMERICAL_TOLERANCE
        );
        assert_relative_eq!(
            greeks_put.gamma,
            gamma(100.0, 100.0, 1.0, 0.05, 0.2),
            epsilon = NUMERICAL_TOLERANCE
        );
        assert_relative_eq!(
            greeks_put.vega,
            vega(100.0, 100.0, 1.0, 0.05, 0.2),
            epsilon = NUMERICAL_TOLERANCE
        );
        assert_relative_eq!(
            greeks_put.theta,
            theta_put(100.0, 100.0, 1.0, 0.05, 0.2),
            epsilon = NUMERICAL_TOLERANCE
        );
        assert_relative_eq!(
            greeks_put.rho,
            rho_put(100.0, 100.0, 1.0, 0.05, 0.2),
            epsilon = NUMERICAL_TOLERANCE
        );
    }

    #[test]
    fn test_batch_consistency() {
        let spots = vec![90.0, 100.0, 110.0];
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let v = 0.2;

        // Delta Call
        let batch_deltas = delta_call_batch(&spots, k, t, r, v);
        for (i, &spot) in spots.iter().enumerate() {
            let single_delta = delta_call(spot, k, t, r, v);
            assert_relative_eq!(batch_deltas[i], single_delta, epsilon = NUMERICAL_TOLERANCE);
        }

        // Delta Put
        let batch_deltas_put = delta_put_batch(&spots, k, t, r, v);
        for (i, &spot) in spots.iter().enumerate() {
            let single_delta = delta_put(spot, k, t, r, v);
            assert_relative_eq!(
                batch_deltas_put[i],
                single_delta,
                epsilon = NUMERICAL_TOLERANCE
            );
        }

        // Gamma
        let batch_gammas = gamma_batch(&spots, k, t, r, v);
        for (i, &spot) in spots.iter().enumerate() {
            let single_gamma = gamma(spot, k, t, r, v);
            assert_relative_eq!(batch_gammas[i], single_gamma, epsilon = NUMERICAL_TOLERANCE);
        }

        // Vega
        let batch_vegas = vega_batch(&spots, k, t, r, v);
        for (i, &spot) in spots.iter().enumerate() {
            let single_vega = vega(spot, k, t, r, v);
            assert_relative_eq!(batch_vegas[i], single_vega, epsilon = NUMERICAL_TOLERANCE);
        }

        // Theta Call
        let batch_thetas_call = theta_call_batch(&spots, k, t, r, v);
        for (i, &spot) in spots.iter().enumerate() {
            let single_theta = theta_call(spot, k, t, r, v);
            assert_relative_eq!(
                batch_thetas_call[i],
                single_theta,
                epsilon = NUMERICAL_TOLERANCE
            );
        }

        // Theta Put
        let batch_thetas_put = theta_put_batch(&spots, k, t, r, v);
        for (i, &spot) in spots.iter().enumerate() {
            let single_theta = theta_put(spot, k, t, r, v);
            assert_relative_eq!(
                batch_thetas_put[i],
                single_theta,
                epsilon = NUMERICAL_TOLERANCE
            );
        }

        // Rho Call
        let batch_rhos_call = rho_call_batch(&spots, k, t, r, v);
        for (i, &spot) in spots.iter().enumerate() {
            let single_rho = rho_call(spot, k, t, r, v);
            assert_relative_eq!(
                batch_rhos_call[i],
                single_rho,
                epsilon = NUMERICAL_TOLERANCE
            );
        }

        // Rho Put
        let batch_rhos_put = rho_put_batch(&spots, k, t, r, v);
        for (i, &spot) in spots.iter().enumerate() {
            let single_rho = rho_put(spot, k, t, r, v);
            assert_relative_eq!(batch_rhos_put[i], single_rho, epsilon = NUMERICAL_TOLERANCE);
        }
    }
}
