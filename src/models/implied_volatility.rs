//! インプライドボラティリティ計算モジュール
//!
//! 市場価格からBlack-Scholesインプライドボラティリティを逆算。
//! Newton-Raphson法とBrent法のハイブリッドアプローチで高速かつ確実な収束を実現。

use crate::constants::{IV_MAX_VOL, IV_MIN_VOL, IV_TOLERANCE_PRICE, NEWTON_MAX_ATTEMPTS};
use crate::error::QuantForgeError;
use crate::math::solvers::hybrid_solver;
use crate::models::black_scholes::{bs_call_price, bs_put_price};
use crate::models::greeks;
use crate::models::iv_initial_guess::{adaptive_initial_guess, handle_edge_case, is_edge_case};
use rayon::prelude::*;

/// コールオプションのインプライドボラティリティ計算
///
/// # Arguments
/// * `price` - 市場価格
/// * `s` - 原資産価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - 無リスク金利
///
/// # Returns
/// * `Ok(iv)` - インプライドボラティリティ
/// * `Err` - 収束失敗または入力エラー
pub fn implied_volatility_call(
    price: f64,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
) -> Result<f64, QuantForgeError> {
    implied_volatility(price, s, k, t, r, true)
}

/// プットオプションのインプライドボラティリティ計算
///
/// # Arguments
/// * `price` - 市場価格
/// * `s` - 原資産価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - 無リスク金利
///
/// # Returns
/// * `Ok(iv)` - インプライドボラティリティ
/// * `Err` - 収束失敗または入力エラー
pub fn implied_volatility_put(
    price: f64,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
) -> Result<f64, QuantForgeError> {
    implied_volatility(price, s, k, t, r, false)
}

/// 汎用インプライドボラティリティ計算（内部関数）
///
/// # Arguments
/// * `price` - 市場価格
/// * `s` - 原資産価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - 無リスク金利
/// * `is_call` - コールオプションの場合true
///
/// # Returns
/// * `Ok(iv)` - インプライドボラティリティ
/// * `Err` - 収束失敗または入力エラー
fn implied_volatility(
    price: f64,
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    is_call: bool,
) -> Result<f64, QuantForgeError> {
    // 基本的な入力検証（ボラティリティは除く）
    if !s.is_finite() || !k.is_finite() || !t.is_finite() || !r.is_finite() || !price.is_finite() {
        return Err(QuantForgeError::InvalidNumericValue);
    }

    if s <= 0.0 {
        return Err(QuantForgeError::InvalidSpotPrice(format!(
            "Spot price must be positive, got {s}"
        )));
    }

    if k <= 0.0 {
        return Err(QuantForgeError::InvalidStrikePrice(format!(
            "Strike price must be positive, got {k}"
        )));
    }

    if t <= 0.0 {
        return Err(QuantForgeError::InvalidTime(format!(
            "Time must be positive, got {t}"
        )));
    }

    if price <= 0.0 {
        return Err(QuantForgeError::InvalidMarketPrice(format!(
            "Market price must be positive, got {price}"
        )));
    }

    // 無裁定条件のチェック
    let discount_factor = (-r * t).exp();

    let intrinsic_value = if is_call {
        (s - k * discount_factor).max(0.0)
    } else {
        (k * discount_factor - s).max(0.0)
    };

    let upper_bound = if is_call { s } else { k * discount_factor };

    if price < intrinsic_value * 0.999 {
        return Err(QuantForgeError::NoArbitrageBreach(format!(
            "Option price {price} below intrinsic value {intrinsic_value}"
        )));
    }

    if price > upper_bound * 1.001 {
        return Err(QuantForgeError::NoArbitrageBreach(format!(
            "Option price {price} above upper bound {upper_bound}"
        )));
    }

    // エッジケース処理
    if is_edge_case(price, s, k, t, r, is_call) {
        if let Some(edge_iv) = handle_edge_case(price, s, k, t, r, is_call) {
            return Ok(edge_iv);
        }
    }

    // 初期推定値の計算
    let initial_guess = adaptive_initial_guess(price, s, k, t, r, is_call);

    // 目的関数：計算価格 - 市場価格
    let objective = |vol: f64| -> f64 {
        if vol <= 0.0 {
            return f64::INFINITY;
        }
        let calc_price = if is_call {
            bs_call_price(s, k, t, r, vol)
        } else {
            bs_put_price(s, k, t, r, vol)
        };
        calc_price - price
    };

    // 導関数：Vega
    let derivative = |vol: f64| -> f64 {
        if vol <= 0.0 {
            return 0.0;
        }
        let vega_value = greeks::vega(s, k, t, r, vol);
        // Vegaを100で割る必要がある（BASIS_POINT_MULTIPLIERの逆）
        vega_value * 100.0
    };

    // ハイブリッドソルバーで解く
    let result = hybrid_solver(
        objective,
        derivative,
        initial_guess,
        IV_MIN_VOL,
        IV_MAX_VOL,
        IV_TOLERANCE_PRICE,
    )?;

    // 最終検証
    let final_price = if is_call {
        bs_call_price(s, k, t, r, result)
    } else {
        bs_put_price(s, k, t, r, result)
    };

    if (final_price - price).abs() > IV_TOLERANCE_PRICE * 10.0 {
        return Err(QuantForgeError::ConvergenceFailed(NEWTON_MAX_ATTEMPTS));
    }

    Ok(result)
}

/// バッチインプライドボラティリティ計算
///
/// 複数のオプション価格から一括でIVを計算。
///
/// # Arguments
/// * `prices` - 市場価格の配列
/// * `spots` - 原資産価格の配列
/// * `strikes` - 権利行使価格の配列
/// * `times` - 満期までの時間の配列
/// * `rates` - 無リスク金利の配列
/// * `is_calls` - コール/プットフラグの配列
///
/// # Returns
/// * インプライドボラティリティの配列（エラーの場合はNaN）
pub fn implied_volatility_batch(
    prices: &[f64],
    spots: &[f64],
    strikes: &[f64],
    times: &[f64],
    rates: &[f64],
    is_calls: &[bool],
) -> Vec<f64> {
    // 入力配列の長さチェック
    let len = prices.len();
    if spots.len() != len
        || strikes.len() != len
        || times.len() != len
        || rates.len() != len
        || is_calls.len() != len
    {
        return vec![f64::NAN; len];
    }

    // 逐次処理
    prices
        .iter()
        .zip(spots.iter())
        .zip(strikes.iter())
        .zip(times.iter())
        .zip(rates.iter())
        .zip(is_calls.iter())
        .map(|(((((price, s), k), t), r), is_call)| {
            implied_volatility(*price, *s, *k, *t, *r, *is_call).unwrap_or(f64::NAN)
        })
        .collect()
}

/// 並列バッチインプライドボラティリティ計算
///
/// Rayonを使用して複数のオプション価格から並列でIVを計算。
/// 大量のオプション価格を高速に処理する場合に使用。
///
/// # Arguments
/// * `prices` - 市場価格の配列
/// * `spots` - 原資産価格の配列
/// * `strikes` - 権利行使価格の配列
/// * `times` - 満期までの時間の配列
/// * `rates` - 無リスク金利の配列
/// * `is_calls` - コール/プットフラグの配列
///
/// # Returns
/// * インプライドボラティリティの配列（エラーの場合はNaN）
pub fn implied_volatility_batch_parallel(
    prices: &[f64],
    spots: &[f64],
    strikes: &[f64],
    times: &[f64],
    rates: &[f64],
    is_calls: &[bool],
) -> Vec<f64> {
    // 入力配列の長さチェック
    let len = prices.len();
    if spots.len() != len
        || strikes.len() != len
        || times.len() != len
        || rates.len() != len
        || is_calls.len() != len
    {
        return vec![f64::NAN; len];
    }

    // 並列処理の閾値（小規模データ用）
    use crate::constants::PARALLEL_THRESHOLD_SMALL;

    if len < PARALLEL_THRESHOLD_SMALL {
        // 少量の場合は逐次処理
        return implied_volatility_batch(prices, spots, strikes, times, rates, is_calls);
    }

    // 並列処理
    prices
        .par_iter()
        .zip(spots.par_iter())
        .zip(strikes.par_iter())
        .zip(times.par_iter())
        .zip(rates.par_iter())
        .zip(is_calls.par_iter())
        .map(|(((((price, s), k), t), r), is_call)| {
            implied_volatility(*price, *s, *k, *t, *r, *is_call).unwrap_or(f64::NAN)
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::PRACTICAL_TOLERANCE;

    #[test]
    fn test_implied_volatility_call_atm() {
        // ATMコールオプションのテスト
        let s = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let true_vol = 0.25;

        // 真のボラティリティで価格を計算
        let price = bs_call_price(s, k, t, r, true_vol);

        // IVを逆算
        let iv = implied_volatility_call(price, s, k, t, r)
            .expect("IV calculation should succeed for valid call option parameters");

        // 誤差チェック
        assert!((iv - true_vol).abs() < 1e-6);
    }

    #[test]
    fn test_implied_volatility_put_otm() {
        // OTMプットオプションのテスト
        let s = 100.0;
        let k = 90.0;
        let t = 0.5;
        let r = 0.05;
        let true_vol = 0.3;

        // 真のボラティリティで価格を計算
        let price = bs_put_price(s, k, t, r, true_vol);

        // IVを逆算
        let iv = implied_volatility_put(price, s, k, t, r)
            .expect("IV calculation should succeed for valid put option parameters");

        // 誤差チェック
        assert!((iv - true_vol).abs() < 1e-6);
    }

    #[test]
    fn test_implied_volatility_edge_cases() {
        // Deep ITMコール - 内在価値に近い適切な価格を使用
        let s = 150.0;
        let k = 100.0;
        let t = 0.5;
        let r = 0.05;
        // 内在価値 = 150 - 100 * exp(-0.05 * 0.5) ≈ 52.47
        // 時間価値を少し加えた価格
        let price = 52.5;

        let result = implied_volatility_call(price, s, k, t, r);
        assert!(result.is_ok());
        assert!(
            result.expect("Deep OTM put IV should calculate successfully") < 0.1,
            "Deep OTM put should have low volatility"
        );

        // 満期直前 - より現実的な価格を使用
        let s = 100.0;
        let k = 100.0;
        let t = 0.001; // 0.365日
        let r = 0.05;
        let price = 0.5; // ATMで満期直前の現実的な価格

        let result = implied_volatility_call(price, s, k, t, r);
        assert!(result.is_ok());
    }

    #[test]
    fn test_implied_volatility_no_arbitrage() {
        // 無裁定条件違反のテスト
        let s = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;

        // 価格が低すぎる
        let result = implied_volatility_call(0.01, s, k, t, r);
        assert!(matches!(result, Err(QuantForgeError::NoArbitrageBreach(_))));

        // 価格が高すぎる
        let result = implied_volatility_call(101.0, s, k, t, r);
        assert!(matches!(result, Err(QuantForgeError::NoArbitrageBreach(_))));
    }

    #[test]
    fn test_implied_volatility_batch() {
        let prices = vec![10.0, 5.0, 15.0];
        let spots = vec![100.0, 100.0, 100.0];
        let strikes = vec![100.0, 110.0, 90.0];
        let times = vec![1.0, 0.5, 1.0];
        let rates = vec![0.05, 0.05, 0.05];
        let is_calls = vec![true, true, true];

        let ivs = implied_volatility_batch(&prices, &spots, &strikes, &times, &rates, &is_calls);

        assert_eq!(ivs.len(), 3);
        for iv in &ivs {
            assert!(iv.is_finite());
            assert!(*iv > IV_MIN_VOL);
            assert!(*iv < IV_MAX_VOL);
        }
    }

    #[test]
    fn test_implied_volatility_consistency() {
        // 価格→IV→価格の往復テスト
        let test_cases = vec![
            (100.0, 100.0, 1.0, 0.05, 0.25, true),  // ATM Call
            (100.0, 110.0, 0.5, 0.05, 0.3, true),   // OTM Call
            (100.0, 90.0, 0.5, 0.05, 0.3, false),   // OTM Put
            (100.0, 90.0, 1.0, 0.05, 0.2, true),    // ITM Call
            (100.0, 110.0, 1.0, 0.05, 0.35, false), // ITM Put
        ];

        for (s, k, t, r, true_vol, is_call) in test_cases {
            // Step 1: ボラティリティから価格を計算
            let price = if is_call {
                bs_call_price(s, k, t, r, true_vol)
            } else {
                bs_put_price(s, k, t, r, true_vol)
            };

            // Step 2: 価格からIVを逆算
            let iv = implied_volatility(price, s, k, t, r, is_call)
                .expect("Round-trip IV calculation should succeed with known valid inputs");

            // Step 3: IVから価格を再計算
            let recalc_price = if is_call {
                bs_call_price(s, k, t, r, iv)
            } else {
                bs_put_price(s, k, t, r, iv)
            };

            // 往復誤差チェック
            assert!((recalc_price - price).abs() < PRACTICAL_TOLERANCE);
            assert!((iv - true_vol).abs() < 1e-5);
        }
    }
}
