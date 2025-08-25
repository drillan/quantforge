//! インプライドボラティリティ初期推定値算出モジュール
//!
//! Newton-Raphson法の収束を高速化するための初期推定値を提供。
//! モネネスとオプション価格に基づいて最適な推定手法を選択。

use crate::constants::{IV_MAX_VOL, IV_MIN_VOL};
use std::f64::consts::PI;

/// Brenner-Subrahmanyam近似による初期推定値
///
/// ATM（At-The-Money）付近で高精度な近似式。
/// IV ≈ √(2π/T) * (C/S)
///
/// # Arguments
/// * `price` - オプション価格
/// * `s` - 原資産価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - 無リスク金利
///
/// # Returns
/// 初期推定ボラティリティ
pub fn brenner_subrahmanyam(price: f64, s: f64, k: f64, t: f64, r: f64) -> f64 {
    // ATM調整価格
    let forward_price = s * (r * t).exp();
    let atm_adjustment = (forward_price / k).ln().abs();

    // 基本的なBrenner-Subrahmanyam式
    let base_vol = (2.0 * PI / t).sqrt() * (price / s);

    // モネネス調整
    let moneyness_adjustment = 1.0 + 0.5 * atm_adjustment;

    (base_vol * moneyness_adjustment).clamp(IV_MIN_VOL, IV_MAX_VOL)
}

/// Corrado-Miller近似による初期推定値
///
/// OTM（Out-of-The-Money）オプションで精度が高い改良版近似式。
///
/// # Arguments
/// * `price` - オプション価格
/// * `s` - 原資産価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - 無リスク金利
/// * `is_call` - コールオプションの場合true
///
/// # Returns
/// 初期推定ボラティリティ
pub fn corrado_miller(price: f64, s: f64, k: f64, t: f64, r: f64, is_call: bool) -> f64 {
    let discount_factor = (-r * t).exp();
    let forward = s * (r * t).exp();

    // Put-Call変換（プットの場合）
    let c = if is_call {
        price
    } else {
        // Put-Callパリティを使用してコール価格に変換
        price + forward - k * discount_factor
    };

    // Corrado-Miller公式の項を計算
    let x = k * discount_factor;
    let sqrt_t = t.sqrt();

    // 基本項
    let term1 = c - (s - x) / 2.0;
    let term2 = term1 * term1 - ((s - x).powi(2) / PI);

    if term2 <= 0.0 {
        // 数値的に不安定な場合はBrenner-Subrahmanyamにフォールバック
        return brenner_subrahmanyam(price, s, k, t, r);
    }

    let numerator = (2.0 / PI).sqrt() * (c - (s - x) / 2.0 + term2.sqrt());
    let denominator = s + x;

    let vol = numerator / (denominator * sqrt_t);

    vol.clamp(IV_MIN_VOL, IV_MAX_VOL)
}

/// 適応型初期推定値選択
///
/// オプションの特性（モネネス、満期、価格レベル）に基づいて
/// 最適な初期推定手法を選択。
///
/// # Arguments
/// * `price` - オプション価格
/// * `s` - 原資産価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - 無リスク金利
/// * `is_call` - コールオプションの場合true
///
/// # Returns
/// 最適化された初期推定ボラティリティ
pub fn adaptive_initial_guess(price: f64, s: f64, k: f64, t: f64, r: f64, is_call: bool) -> f64 {
    // モネネスの計算
    let forward = s * (r * t).exp();
    let moneyness = forward / k;
    let log_moneyness = moneyness.ln().abs();

    // 満期までの時間による調整
    const SHORT_MATURITY_THRESHOLD: f64 = 0.1; // 36.5日
    const DEEP_OTM_THRESHOLD: f64 = 0.3; // log(moneyness) > 0.3はDeep OTM

    let initial_vol = if t < SHORT_MATURITY_THRESHOLD {
        // 短期満期：価格ベースの簡易推定
        if log_moneyness < 0.1 {
            // ATM付近
            (2.0 * PI / t).sqrt() * (price / s) * 1.2
        } else {
            // OTM：より高いボラティリティを初期値に
            (2.0 * PI / t).sqrt() * (price / s) * 1.5
        }
    } else if log_moneyness < 0.1 {
        // ATM付近：Brenner-Subrahmanyam
        brenner_subrahmanyam(price, s, k, t, r)
    } else if log_moneyness < DEEP_OTM_THRESHOLD {
        // 軽度OTM：Corrado-Miller
        corrado_miller(price, s, k, t, r, is_call)
    } else {
        // Deep OTM：両方の加重平均
        let bs_vol = brenner_subrahmanyam(price, s, k, t, r);
        let cm_vol = corrado_miller(price, s, k, t, r, is_call);

        // Deep OTMほどCorrado-Millerの重みを増やす
        let weight = (log_moneyness - 0.1) / (DEEP_OTM_THRESHOLD - 0.1);
        bs_vol * (1.0 - weight) + cm_vol * weight
    };

    // エッジケース処理：極端な値の調整
    if initial_vol < IV_MIN_VOL * 2.0 {
        // 非常に低い推定値の場合、収束しにくいので少し高めに調整
        IV_MIN_VOL * 5.0
    } else if initial_vol > IV_MAX_VOL * 0.8 {
        // 非常に高い推定値の場合、中間値から開始
        IV_MAX_VOL * 0.5
    } else {
        initial_vol
    }
}

/// エッジケース判定
///
/// インプライドボラティリティ計算が困難なエッジケースを検出。
///
/// # Arguments
/// * `price` - オプション価格
/// * `s` - 原資産価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - 無リスク金利
/// * `is_call` - コールオプションの場合true
///
/// # Returns
/// エッジケースの場合true
pub fn is_edge_case(price: f64, s: f64, k: f64, t: f64, r: f64, is_call: bool) -> bool {
    let discount_factor = (-r * t).exp();

    // 内在価値の計算（正しい計算式）
    let intrinsic_value = if is_call {
        (s - k * discount_factor).max(0.0)
    } else {
        (k * discount_factor - s).max(0.0)
    };

    // エッジケース条件
    const DEEP_ITM_THRESHOLD: f64 = 0.99; // 価格の99%以上が内在価値
    const NEAR_EXPIRY_THRESHOLD: f64 = 0.001; // 0.365日以下
    const PRICE_TOLERANCE: f64 = 1e-10;

    // Deep ITM判定
    if intrinsic_value > 0.0 && price > intrinsic_value {
        let time_value_ratio = (price - intrinsic_value) / price;
        if time_value_ratio < 1.0 - DEEP_ITM_THRESHOLD {
            return true;
        }
    }

    // 満期直前判定
    if t < NEAR_EXPIRY_THRESHOLD {
        return true;
    }

    // 価格が極端に小さい
    if price < PRICE_TOLERANCE {
        return true;
    }

    // 無裁定条件違反チェック
    let lower_bound = intrinsic_value;
    let upper_bound = if is_call { s } else { k * discount_factor };

    if price < lower_bound * 0.999 || price > upper_bound * 1.001 {
        return true;
    }

    false
}

/// エッジケース処理
///
/// エッジケースに対する特別な処理を実行。
///
/// # Arguments
/// * `price` - オプション価格
/// * `s` - 原資産価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - 無リスク金利
/// * `is_call` - コールオプションの場合true
///
/// # Returns
/// * `Some(iv)` - エッジケース用の推定ボラティリティ
/// * `None` - 通常処理を継続すべき場合
pub fn handle_edge_case(price: f64, s: f64, k: f64, t: f64, r: f64, is_call: bool) -> Option<f64> {
    let discount_factor = (-r * t).exp();

    // 内在価値の計算（正しい計算式）
    let intrinsic_value = if is_call {
        (s - k * discount_factor).max(0.0)
    } else {
        (k * discount_factor - s).max(0.0)
    };

    // Deep ITMの場合：低ボラティリティ
    if intrinsic_value > 0.0 && price > intrinsic_value {
        let time_value = price - intrinsic_value;
        if time_value < price * 0.01 {
            // 時間価値が1%未満：極めて低いIV
            return Some(IV_MIN_VOL * 2.0);
        }
    }

    // 満期直前の場合：価格から直接推定
    if t < 0.001 {
        let moneyness = (s / k).ln();
        if moneyness.abs() < 0.01 {
            // ATM：高ボラティリティ
            return Some(1.0);
        } else if (is_call && moneyness > 0.0) || (!is_call && moneyness < 0.0) {
            // ITM：低ボラティリティ
            return Some(IV_MIN_VOL * 5.0);
        } else {
            // OTM：中程度のボラティリティ
            return Some(0.3);
        }
    }

    None
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_brenner_subrahmanyam_atm() {
        // ATMオプションのテスト
        let price = 10.0;
        let s = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;

        let vol = brenner_subrahmanyam(price, s, k, t, r);

        // 妥当な範囲内であることを確認
        assert!(vol > IV_MIN_VOL);
        assert!(vol < IV_MAX_VOL);
        assert!(vol > 0.2 && vol < 0.3); // ATMの典型的な範囲
    }

    #[test]
    fn test_corrado_miller_otm() {
        // OTMコールオプションのテスト
        let price = 2.0;
        let s = 100.0;
        let k = 110.0;
        let t = 0.5;
        let r = 0.05;

        let vol = corrado_miller(price, s, k, t, r, true);

        // 妥当な範囲内であることを確認
        assert!(vol > IV_MIN_VOL);
        assert!(vol < IV_MAX_VOL);
    }

    #[test]
    fn test_adaptive_initial_guess() {
        // 様々なケースでのテスト
        let test_cases = vec![
            // (price, s, k, t, r, is_call)
            (10.0, 100.0, 100.0, 1.0, 0.05, true), // ATM
            (2.0, 100.0, 110.0, 0.5, 0.05, true),  // OTM Call
            (2.0, 100.0, 90.0, 0.5, 0.05, false),  // OTM Put
            (15.0, 100.0, 90.0, 1.0, 0.05, true),  // ITM Call
            (0.5, 100.0, 150.0, 0.1, 0.05, true),  // Deep OTM, short maturity
        ];

        for (price, s, k, t, r, is_call) in test_cases {
            let vol = adaptive_initial_guess(price, s, k, t, r, is_call);
            assert!(vol >= IV_MIN_VOL);
            assert!(vol <= IV_MAX_VOL);
        }
    }

    #[test]
    fn test_edge_case_detection() {
        // Deep ITMケース
        assert!(is_edge_case(49.9, 150.0, 100.0, 0.5, 0.05, true));

        // 満期直前ケース
        assert!(is_edge_case(5.0, 100.0, 95.0, 0.0001, 0.05, true));

        // 通常ケース
        assert!(!is_edge_case(10.0, 100.0, 100.0, 1.0, 0.05, true));
    }

    #[test]
    fn test_handle_edge_case() {
        // Deep ITMケース - 内在価値に非常に近い価格
        let s = 150.0;
        let k = 100.0;
        let t = 0.5;
        let r = 0.05;
        // 内在価値 = 150 - 100 * exp(-0.05 * 0.5) ≈ 52.47
        let price = 52.48; // 時間価値がほぼゼロ

        let result = handle_edge_case(price, s, k, t, r, true);
        assert!(result.is_some());
        if let Some(vol) = result {
            assert!(vol < 0.1); // Deep ITMは低ボラティリティ
        }

        // 満期直前ATMケース
        let result = handle_edge_case(1.0, 100.0, 100.0, 0.0005, 0.05, true);
        assert!(result.is_some());
        if let Some(vol) = result {
            assert!(vol > 0.5); // 満期直前ATMは高ボラティリティ
        }

        // 通常ケース（Noneを返す）
        let result = handle_edge_case(10.0, 100.0, 100.0, 1.0, 0.05, true);
        assert!(result.is_none());
    }
}
