use crate::math::distributions::norm_cdf;

/// ヨーロピアンコールオプション価格計算
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - リスクフリーレート
/// * `v` - インプライドボラティリティ
pub fn bs_call_price(s: f64, k: f64, t: f64, r: f64, v: f64) -> f64 {
    let sqrt_t = t.sqrt();
    let d1 = (s.ln() - k.ln() + (r + v * v / 2.0) * t) / (v * sqrt_t);
    let d2 = d1 - v * sqrt_t;

    s * norm_cdf(d1) - k * (-r * t).exp() * norm_cdf(d2)
}

/// バッチ処理用（将来のSIMD最適化対応）
pub fn bs_call_price_batch(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
    // 共通項の事前計算
    let sqrt_t = t.sqrt();
    let v_sqrt_t = v * sqrt_t;
    let exp_neg_rt = (-r * t).exp();
    let half_v_squared_t = (r + v * v / 2.0) * t;
    let k_ln = k.ln();

    spots
        .iter()
        .map(|&s| {
            let d1 = (s.ln() - k_ln + half_v_squared_t) / v_sqrt_t;
            let d2 = d1 - v_sqrt_t;
            s * norm_cdf(d1) - k * exp_neg_rt * norm_cdf(d2)
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_bs_call_price_atm() {
        // At-the-money option
        let s = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let v = 0.2;

        let price = bs_call_price(s, k, t, r, v);
        // 金融計算に十分な精度（約0.01%）
        assert_relative_eq!(price, 10.450583572185565, epsilon = 1e-3);
    }

    #[test]
    fn test_bs_call_price_batch() {
        let spots = vec![90.0, 100.0, 110.0];
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let v = 0.2;

        let prices = bs_call_price_batch(&spots, k, t, r, v);
        assert_eq!(prices.len(), 3);

        // バッチ結果と単一計算の一致を確認
        for (i, &spot) in spots.iter().enumerate() {
            let single_price = bs_call_price(spot, k, t, r, v);
            assert_relative_eq!(prices[i], single_price, epsilon = 1e-10);
        }
    }

    #[test]
    fn test_bs_call_price_edge_cases() {
        // Deep ITM (In-The-Money)
        let deep_itm = bs_call_price(200.0, 100.0, 1.0, 0.05, 0.2);
        let intrinsic = 200.0 - 100.0 * (-0.05_f64).exp();
        assert!(deep_itm > intrinsic * 0.99); // ほぼ内在価値

        // Deep OTM (Out-of-The-Money)
        let deep_otm = bs_call_price(50.0, 100.0, 1.0, 0.05, 0.2);
        assert!(deep_otm < 1.0); // ほぼゼロ

        // 満期直前
        let near_expiry = bs_call_price(110.0, 100.0, 0.001, 0.05, 0.2);
        assert!(near_expiry > 9.9 && near_expiry < 10.1); // ほぼ内在価値
    }

    #[test]
    fn test_bs_call_price_bounds() {
        // 価格境界のテスト: max(S - K*e^(-rt), 0) <= C <= S
        let test_cases = vec![
            (100.0, 100.0, 1.0, 0.05, 0.2),
            (80.0, 100.0, 0.5, 0.03, 0.25),
            (120.0, 100.0, 2.0, 0.02, 0.3),
        ];

        for (s, k, t, r, v) in test_cases {
            let price = bs_call_price(s, k, t, r, v);
            let lower_bound = (s - k * (-r * t).exp()).max(0.0);
            assert!(price >= lower_bound);
            assert!(price <= s);
        }
    }

    #[test]
    fn test_bs_call_price_zero_volatility() {
        // ボラティリティゼロの場合は内在価値に収束
        let s = 110.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let v = 0.001; // 非常に小さなボラティリティ

        let price = bs_call_price(s, k, t, r, v);
        let intrinsic = s - k * (-r * t).exp();
        assert_relative_eq!(price, intrinsic, epsilon = 0.01);
    }
}
