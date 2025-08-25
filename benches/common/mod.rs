/// ベンチマーク用共通パラメータモジュール
pub mod test_params {
    /// デフォルトのオプション価格計算パラメータ
    pub struct DefaultParams;

    impl DefaultParams {
        pub const STRIKE: f64 = 100.0;
        pub const TIME_TO_MATURITY: f64 = 1.0;
        pub const RISK_FREE_RATE: f64 = 0.05;
        pub const VOLATILITY: f64 = 0.2;
    }

    /// ATM（At-The-Money）オプションのパラメータ生成
    pub fn atm_params(spot: f64) -> (f64, f64, f64, f64, f64) {
        (
            spot,
            DefaultParams::STRIKE,
            DefaultParams::TIME_TO_MATURITY,
            DefaultParams::RISK_FREE_RATE,
            DefaultParams::VOLATILITY,
        )
    }

    /// ITM（In-The-Money）オプションのパラメータ生成
    /// spot_premium: ストライクからの乖離率（例: 0.1 = 10% ITM）
    pub fn itm_params(spot_premium: f64) -> (f64, f64, f64, f64, f64) {
        let spot = DefaultParams::STRIKE * (1.0 + spot_premium);
        atm_params(spot)
    }

    /// OTM（Out-of-The-Money）オプションのパラメータ生成
    /// spot_discount: ストライクからの乖離率（例: 0.1 = 10% OTM）
    pub fn otm_params(spot_discount: f64) -> (f64, f64, f64, f64, f64) {
        let spot = DefaultParams::STRIKE * (1.0 - spot_discount);
        atm_params(spot)
    }

    /// カスタムパラメータセット生成（満期バリエーション用）
    #[allow(dead_code)]
    pub fn params_with_maturity(spot: f64, time_to_maturity: f64) -> (f64, f64, f64, f64, f64) {
        (
            spot,
            DefaultParams::STRIKE,
            time_to_maturity,
            DefaultParams::RISK_FREE_RATE,
            DefaultParams::VOLATILITY,
        )
    }

    /// カスタムパラメータセット生成（ボラティリティバリエーション用）
    #[allow(dead_code)]
    pub fn params_with_volatility(spot: f64, volatility: f64) -> (f64, f64, f64, f64, f64) {
        (
            spot,
            DefaultParams::STRIKE,
            DefaultParams::TIME_TO_MATURITY,
            DefaultParams::RISK_FREE_RATE,
            volatility,
        )
    }

    /// バッチ処理用スポット価格生成
    pub fn generate_spot_range(size: usize, min: f64, max: f64) -> Vec<f64> {
        (0..size)
            .map(|i| min + (i as f64 / size as f64) * (max - min))
            .collect()
    }
}
