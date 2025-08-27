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

    // Deep OTMで数値誤差による負値を防ぐ
    (s * norm_cdf(d1) - k * (-r * t).exp() * norm_cdf(d2)).max(0.0)
}

/// ヨーロピアンプットオプション価格計算
///
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間（年）
/// * `r` - リスクフリーレート
/// * `v` - インプライドボラティリティ
pub fn bs_put_price(s: f64, k: f64, t: f64, r: f64, v: f64) -> f64 {
    let sqrt_t = t.sqrt();
    let d1 = (s.ln() - k.ln() + (r + v * v / 2.0) * t) / (v * sqrt_t);
    let d2 = d1 - v * sqrt_t;

    // Deep OTMで数値誤差による負値を防ぐ
    (k * (-r * t).exp() * norm_cdf(-d2) - s * norm_cdf(-d1)).max(0.0)
}

/// バッチ処理用
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
            // Deep OTMで数値誤差による負値を防ぐ
            (s * norm_cdf(d1) - k * exp_neg_rt * norm_cdf(d2)).max(0.0)
        })
        .collect()
}

/// プットオプションのバッチ処理用
pub fn bs_put_price_batch(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64> {
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
            // Deep OTMで数値誤差による負値を防ぐ
            (k * exp_neg_rt * norm_cdf(-d2) - s * norm_cdf(-d1)).max(0.0)
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::{NUMERICAL_TOLERANCE, PRACTICAL_TOLERANCE};
    use approx::assert_relative_eq;

    /// テストヘルパー: オプションパラメータ構造体
    struct TestOption {
        spot: f64,
        strike: f64,
        time: f64,
        rate: f64,
        vol: f64,
    }

    impl TestOption {
        /// ATMオプションのデフォルトパラメータ
        fn atm() -> Self {
            Self {
                spot: 100.0,
                strike: 100.0,
                time: 1.0,
                rate: 0.05,
                vol: 0.2,
            }
        }

        /// スポット価格を変更
        fn with_spot(mut self, spot: f64) -> Self {
            self.spot = spot;
            self
        }

        /// ボラティリティを変更
        fn with_vol(mut self, vol: f64) -> Self {
            self.vol = vol;
            self
        }

        /// 満期までの時間を変更
        fn with_time(mut self, time: f64) -> Self {
            self.time = time;
            self
        }

        /// オプション価格を計算
        fn price(&self) -> f64 {
            bs_call_price(self.spot, self.strike, self.time, self.rate, self.vol)
        }

        /// 価格アサーション（相対誤差チェック）
        fn assert_price_near(&self, expected: f64, epsilon: f64) {
            let actual = self.price();
            assert_relative_eq!(actual, expected, epsilon = epsilon);
        }

        /// 価格境界チェック
        fn assert_price_in_bounds(&self) {
            let price = self.price();
            let lower_bound = (self.spot - self.strike * (-self.rate * self.time).exp()).max(0.0);
            assert!(
                price >= lower_bound,
                "Price {price} below lower bound {lower_bound}"
            );
            assert!(
                price <= self.spot,
                "Price {price} above spot price {}",
                self.spot
            );
        }
    }

    #[test]
    fn test_bs_call_price_atm() {
        // At-the-money option using helper
        let option = TestOption::atm();
        option.assert_price_near(10.450583572185565, PRACTICAL_TOLERANCE);
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

        // バッチ結果と単一計算の一致を確認（高精度で検証）
        for (i, &spot) in spots.iter().enumerate() {
            let single_price = bs_call_price(spot, k, t, r, v);
            assert_relative_eq!(prices[i], single_price, epsilon = NUMERICAL_TOLERANCE);
        }
    }

    #[test]
    fn test_bs_call_price_edge_cases() {
        // Deep ITM (In-The-Money)
        let deep_itm_option = TestOption::atm().with_spot(200.0);
        let intrinsic =
            deep_itm_option.spot - deep_itm_option.strike * (-deep_itm_option.rate).exp();
        let deep_itm = deep_itm_option.price();
        assert!(deep_itm > intrinsic * 0.99); // ほぼ内在価値

        // Deep OTM (Out-of-The-Money)
        let deep_otm = TestOption::atm().with_spot(50.0).price();
        assert!(deep_otm < 1.0); // ほぼゼロ

        // 満期直前
        let near_expiry = TestOption::atm().with_spot(110.0).with_time(0.001).price();
        assert!(near_expiry > 9.9 && near_expiry < 10.1); // ほぼ内在価値
    }

    #[test]
    fn test_bs_call_price_bounds() {
        // 価格境界のテスト: max(S - K*e^(-rt), 0) <= C <= S
        let test_cases = vec![
            TestOption::atm(),
            TestOption::atm()
                .with_spot(80.0)
                .with_time(0.5)
                .with_vol(0.25),
            TestOption::atm()
                .with_spot(120.0)
                .with_time(2.0)
                .with_vol(0.3),
        ];

        for option in test_cases {
            option.assert_price_in_bounds();
        }
    }

    #[test]
    fn test_bs_call_price_zero_volatility() {
        // ボラティリティゼロの場合は内在価値に収束
        let option = TestOption::atm().with_spot(110.0).with_vol(0.001); // 非常に小さなボラティリティ

        let intrinsic = option.spot - option.strike * (-option.rate * option.time).exp();
        option.assert_price_near(intrinsic, 0.01);
    }

    #[test]
    fn test_bs_put_price_atm() {
        // At-the-money put option
        let s = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let v = 0.2;

        let put_price = bs_put_price(s, k, t, r, v);
        // 期待値は参考実装から計算: scipy.stats.norm.cdf(-d1), norm.cdf(-d2)を使用
        assert_relative_eq!(put_price, 5.573526022657734, epsilon = PRACTICAL_TOLERANCE);
    }

    #[test]
    fn test_bs_put_price_batch() {
        let spots = vec![90.0, 100.0, 110.0];
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let v = 0.2;

        let prices = bs_put_price_batch(&spots, k, t, r, v);
        assert_eq!(prices.len(), 3);

        // バッチ結果と単一計算の一致を確認
        for (i, &spot) in spots.iter().enumerate() {
            let single_price = bs_put_price(spot, k, t, r, v);
            assert_relative_eq!(prices[i], single_price, epsilon = NUMERICAL_TOLERANCE);
        }
    }

    #[test]
    fn test_put_call_parity() {
        // Put-Call パリティの検証: C - P = S - K*exp(-r*T)
        let s = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let v = 0.2;

        let call = bs_call_price(s, k, t, r, v);
        let put = bs_put_price(s, k, t, r, v);

        let parity_lhs = call - put;
        let parity_rhs = s - k * (-r * t).exp();

        assert_relative_eq!(parity_lhs, parity_rhs, epsilon = NUMERICAL_TOLERANCE);
    }

    #[test]
    fn test_bs_put_price_edge_cases() {
        // Deep ITM Put (S << K)
        let deep_itm_put = bs_put_price(50.0, 100.0, 1.0, 0.05, 0.2);
        let intrinsic = 100.0 * (-0.05_f64).exp() - 50.0;
        assert!(deep_itm_put > intrinsic * 0.99); // ほぼ内在価値

        // Deep OTM Put (S >> K)
        let deep_otm_put = bs_put_price(200.0, 100.0, 1.0, 0.05, 0.2);
        assert!(deep_otm_put < 0.01); // ほぼゼロ

        // 満期直前のITM Put
        let near_expiry_put = bs_put_price(90.0, 100.0, 0.001, 0.05, 0.2);
        assert!(near_expiry_put > 9.9 && near_expiry_put < 10.1); // ほぼ内在価値
    }

    #[test]
    fn test_bs_put_price_bounds() {
        // プット価格境界のテスト: max(K*e^(-rt) - S, 0) <= P <= K*e^(-rt)
        let test_cases = vec![
            (100.0, 100.0, 1.0, 0.05, 0.2),
            (80.0, 100.0, 0.5, 0.05, 0.25),
            (120.0, 100.0, 2.0, 0.05, 0.3),
        ];

        for (s, k, t, r, v) in test_cases {
            let put_price = bs_put_price(s, k, t, r, v);
            let lower_bound = (k * (-r * t).exp() - s).max(0.0);
            let upper_bound = k * (-r * t).exp();

            assert!(
                put_price >= lower_bound,
                "Put price {put_price} below lower bound {lower_bound}"
            );
            assert!(
                put_price <= upper_bound,
                "Put price {put_price} above upper bound {upper_bound}"
            );
        }
    }
}
