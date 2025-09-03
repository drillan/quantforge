//! 共通のオプション価格計算フォーミュラ
//!
//! Black-Scholes、Black76などのモデルで共通使用される計算ロジックを集約。
//! コード重複を排除し、保守性と一貫性を向上。

use crate::constants::{HALF, VOL_SQUARED_HALF};
use crate::math::distributions::norm_cdf;

/// Black-Scholes d1, d2パラメータ計算
///
/// Black-Scholesモデルの核心パラメータd1とd2を計算。
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - 無リスク金利
/// * `sigma` - ボラティリティ
///
/// # Returns
/// (d1, d2) のタプル
#[inline(always)]
pub fn black_scholes_d1_d2(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> (f64, f64) {
    let sqrt_t = t.sqrt();
    let d1 = ((s / k).ln() + (r + sigma * sigma / VOL_SQUARED_HALF) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;
    (d1, d2)
}

/// Black76 d1, d2パラメータ計算
///
/// Black76モデル（先物オプション）の核心パラメータd1とd2を計算。
///
/// # Arguments
/// * `f` - フォワード価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `sigma` - ボラティリティ
///
/// # Returns
/// (d1, d2) のタプル
#[inline(always)]
pub fn black76_d1_d2(f: f64, k: f64, t: f64, sigma: f64) -> (f64, f64) {
    let sqrt_t = t.sqrt();
    let d1 = ((f / k).ln() + (sigma * sigma * HALF) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;
    (d1, d2)
}

/// Black-Scholesコールオプション価格（スカラー版）
///
/// 単一のコールオプション価格を計算。
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - 無リスク金利
/// * `sigma` - ボラティリティ
///
/// # Returns
/// コールオプション価格
#[inline(always)]
pub fn black_scholes_call_scalar(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> f64 {
    let (d1, d2) = black_scholes_d1_d2(s, k, t, r, sigma);
    s * norm_cdf(d1) - k * (-r * t).exp() * norm_cdf(d2)
}

/// Black-Scholesプットオプション価格（スカラー版）
///
/// 単一のプットオプション価格を計算。
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - 無リスク金利
/// * `sigma` - ボラティリティ
///
/// # Returns
/// プットオプション価格
#[inline(always)]
pub fn black_scholes_put_scalar(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> f64 {
    let (d1, d2) = black_scholes_d1_d2(s, k, t, r, sigma);
    k * (-r * t).exp() * norm_cdf(-d2) - s * norm_cdf(-d1)
}

/// Black76コールオプション価格（スカラー版）
///
/// 単一の先物コールオプション価格を計算。
///
/// # Arguments
/// * `f` - フォワード価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - 無リスク金利（割引用）
/// * `sigma` - ボラティリティ
///
/// # Returns
/// コールオプション価格
#[inline(always)]
pub fn black76_call_scalar(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> f64 {
    let (d1, d2) = black76_d1_d2(f, k, t, sigma);
    let discount = (-r * t).exp();
    discount * (f * norm_cdf(d1) - k * norm_cdf(d2))
}

/// Black76プットオプション価格（スカラー版）
///
/// 単一の先物プットオプション価格を計算。
///
/// # Arguments
/// * `f` - フォワード価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - 無リスク金利（割引用）
/// * `sigma` - ボラティリティ
///
/// # Returns
/// プットオプション価格
#[inline(always)]
pub fn black76_put_scalar(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> f64 {
    let (d1, d2) = black76_d1_d2(f, k, t, sigma);
    let discount = (-r * t).exp();
    discount * (k * norm_cdf(-d2) - f * norm_cdf(-d1))
}

/// Merton配当付きBlack-Scholes d1, d2パラメータ計算
///
/// 連続配当利回りを考慮したd1, d2を計算。
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - 無リスク金利
/// * `q` - 配当利回り
/// * `sigma` - ボラティリティ
///
/// # Returns
/// (d1, d2)のタプル
#[inline(always)]
pub fn merton_d1_d2(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> (f64, f64) {
    let sqrt_t = t.sqrt();
    let d1 = ((s / k).ln() + (r - q + sigma * sigma / VOL_SQUARED_HALF) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;
    (d1, d2)
}

/// Merton配当付きBlack-Scholesコールオプション価格（スカラー版）
///
/// 連続配当利回りを考慮したコールオプション価格を計算。
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - 無リスク金利
/// * `q` - 配当利回り
/// * `sigma` - ボラティリティ
///
/// # Returns
/// コールオプション価格
#[inline(always)]
pub fn merton_call_scalar(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    let (d1, d2) = merton_d1_d2(s, k, t, r, q, sigma);
    s * (-q * t).exp() * norm_cdf(d1) - k * (-r * t).exp() * norm_cdf(d2)
}

/// Merton配当付きBlack-Scholesプットオプション価格（スカラー版）
///
/// 連続配当利回りを考慮したプットオプション価格を計算。
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - 無リスク金利
/// * `q` - 配当利回り
/// * `sigma` - ボラティリティ
///
/// # Returns
/// プットオプション価格
#[inline(always)]
pub fn merton_put_scalar(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    let (d1, d2) = merton_d1_d2(s, k, t, r, q, sigma);
    k * (-r * t).exp() * norm_cdf(-d2) - s * (-q * t).exp() * norm_cdf(-d1)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::{PRACTICAL_TOLERANCE, TEST_BS_PRICE_LOWER, TEST_BS_PRICE_UPPER};

    #[test]
    fn test_black_scholes_call_scalar() {
        let s = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let sigma = 0.2;

        let price = black_scholes_call_scalar(s, k, t, r, sigma);

        // ATMオプションの期待値（概算）
        assert!(
            price > TEST_BS_PRICE_LOWER && price < TEST_BS_PRICE_UPPER,
            "Price = {price}"
        );
    }

    #[test]
    fn test_black_scholes_put_scalar() {
        let s = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let sigma = 0.2;

        let call_price = black_scholes_call_scalar(s, k, t, r, sigma);
        let put_price = black_scholes_put_scalar(s, k, t, r, sigma);

        // プット・コール・パリティの検証
        let parity = call_price - put_price - (s - k * (-r * t).exp());
        assert!(
            parity.abs() < PRACTICAL_TOLERANCE,
            "Put-Call parity violation: {parity}"
        );
    }

    #[test]
    fn test_black76_call_scalar() {
        let f = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let sigma = 0.2;

        let price = black76_call_scalar(f, k, t, r, sigma);

        // ATM先物オプションの期待値（概算）
        assert!(price > 7.0 && price < 11.0, "Price = {price}");
    }

    #[test]
    fn test_merton_call_scalar() {
        let s = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let q = 0.02; // 2%配当利回り
        let sigma = 0.2;

        let price = merton_call_scalar(s, k, t, r, q, sigma);

        // 配当ありオプションの期待値
        assert!(price > 6.0 && price < 10.0, "Price = {price}");
    }
}
