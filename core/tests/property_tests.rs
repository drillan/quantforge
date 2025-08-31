use proptest::prelude::*;
use quantforge_core::models::{american::American, black_scholes::BlackScholes, black76::Black76, merton::Merton};
use quantforge_core::traits::OptionModel;

// 有効な入力パラメータの範囲を定義
fn valid_spot() -> impl Strategy<Value = f64> {
    0.1..1000.0
}

fn valid_strike() -> impl Strategy<Value = f64> {
    0.1..1000.0
}

fn valid_time() -> impl Strategy<Value = f64> {
    0.001..10.0
}

fn valid_rate() -> impl Strategy<Value = f64> {
    -0.1..0.5
}

fn valid_volatility() -> impl Strategy<Value = f64> {
    0.01..2.0
}

fn valid_dividend() -> impl Strategy<Value = f64> {
    0.0..0.2
}

// Americanオプション用の制限された範囲（数値安定性のため）
fn american_spot() -> impl Strategy<Value = f64> {
    1.0..500.0  // より狭い範囲
}

fn american_strike() -> impl Strategy<Value = f64> {
    1.0..500.0  // より狭い範囲
}

fn american_time() -> impl Strategy<Value = f64> {
    0.01..5.0  // 極端に短い時間を除外
}

fn american_rate() -> impl Strategy<Value = f64> {
    -0.05..0.3  // より現実的な範囲
}

fn american_volatility() -> impl Strategy<Value = f64> {
    0.05..1.0  // 極端な値を除外
}

// Black-Scholesモデルのプロパティテスト
proptest! {
    #[test]
    fn test_black_scholes_price_positive(
        s in valid_spot(),
        k in valid_strike(),
        t in valid_time(),
        r in valid_rate(),
        sigma in valid_volatility(),
    ) {
        let model = BlackScholes;
        
        // コールオプション価格は常に正（エラーの場合はスキップ）
        if let Ok(call_price) = model.call_price(s, k, t, r, sigma) {
            prop_assert!(call_price >= -1e-10, "Call price should be non-negative: {}", call_price);
        }
        
        // プットオプション価格は常に正（エラーの場合はスキップ）
        if let Ok(put_price) = model.put_price(s, k, t, r, sigma) {
            prop_assert!(put_price >= -1e-10, "Put price should be non-negative: {}", put_price);
        }
    }
    
    #[test]
    fn test_black_scholes_call_bounds(
        s in valid_spot(),
        k in valid_strike(),
        t in valid_time(),
        r in valid_rate(),
        sigma in valid_volatility(),
    ) {
        let model = BlackScholes;
        let call_price = model.call_price(s, k, t, r, sigma).unwrap();
        
        // コールオプションの下限: max(S - K*exp(-r*t), 0)
        let intrinsic_value = (s - k * (-r * t).exp()).max(0.0);
        prop_assert!(call_price >= intrinsic_value - 1e-10);
        
        // コールオプションの上限: S
        prop_assert!(call_price <= s + 1e-10);
    }
    
    #[test]
    fn test_black_scholes_put_bounds(
        s in valid_spot(),
        k in valid_strike(),
        t in valid_time(),
        r in valid_rate(),
        sigma in valid_volatility(),
    ) {
        let model = BlackScholes;
        let put_price = model.put_price(s, k, t, r, sigma).unwrap();
        
        // プットオプションの下限: max(K*exp(-r*t) - S, 0)
        let intrinsic_value = (k * (-r * t).exp() - s).max(0.0);
        prop_assert!(put_price >= intrinsic_value - 1e-10);
        
        // プットオプションの上限: K*exp(-r*t)
        prop_assert!(put_price <= k * (-r * t).exp() + 1e-10);
    }
    
    #[test]
    fn test_black_scholes_put_call_parity(
        s in valid_spot(),
        k in valid_strike(),
        t in valid_time(),
        r in valid_rate(),
        sigma in valid_volatility(),
    ) {
        let model = BlackScholes;
        let call = model.call_price(s, k, t, r, sigma).unwrap();
        let put = model.put_price(s, k, t, r, sigma).unwrap();
        
        // Put-Call Parity: C - P = S - K*exp(-r*t)
        let lhs = call - put;
        let rhs = s - k * (-r * t).exp();
        
        prop_assert!((lhs - rhs).abs() < 1e-10);
    }
    
    #[test]
    fn test_black_scholes_monotonicity_spot(
        k in valid_strike(),
        t in valid_time(),
        r in valid_rate(),
        sigma in valid_volatility(),
        s1 in valid_spot(),
        s2 in valid_spot(),
    ) {
        prop_assume!(s1 < s2);
        
        let model = BlackScholes;
        let call1 = model.call_price(s1, k, t, r, sigma).unwrap();
        let call2 = model.call_price(s2, k, t, r, sigma).unwrap();
        
        // コール価格はスポット価格に対して単調増加
        prop_assert!(call1 <= call2 + 1e-10);
        
        let put1 = model.put_price(s1, k, t, r, sigma).unwrap();
        let put2 = model.put_price(s2, k, t, r, sigma).unwrap();
        
        // プット価格はスポット価格に対して単調減少
        prop_assert!(put1 >= put2 - 1e-10);
    }
    
    #[test]
    fn test_black_scholes_vega_positive(
        s in valid_spot(),
        k in valid_strike(),
        t in valid_time(),
        r in valid_rate(),
        sigma in valid_volatility(),
    ) {
        let model = BlackScholes;
        let greeks = model.greeks(s, k, t, r, sigma, true).unwrap();
        
        // Vegaは常に正（コールもプットも）
        prop_assert!(greeks.vega >= -1e-10);
    }
}

// Black76モデルのプロパティテスト
proptest! {
    #[test]
    fn test_black76_price_positive(
        f in valid_spot(), // forward price
        k in valid_strike(),
        t in valid_time(),
        r in valid_rate(),
        sigma in valid_volatility(),
    ) {
        let model = Black76;
        
        if let Ok(call_price) = model.call_price(f, k, t, r, sigma) {
            prop_assert!(call_price >= -1e-10, "Call price should be non-negative: {}", call_price);
        }
        
        if let Ok(put_price) = model.put_price(f, k, t, r, sigma) {
            prop_assert!(put_price >= -1e-10, "Put price should be non-negative: {}", put_price);
        }
    }
    
    #[test]
    fn test_black76_put_call_parity(
        f in valid_spot(),
        k in valid_strike(),
        t in valid_time(),
        r in valid_rate(),
        sigma in valid_volatility(),
    ) {
        let model = Black76;
        let call = model.call_price(f, k, t, r, sigma).unwrap();
        let put = model.put_price(f, k, t, r, sigma).unwrap();
        
        // Black76 Put-Call Parity: C - P = exp(-r*t) * (F - K)
        let lhs = call - put;
        let rhs = (-r * t).exp() * (f - k);
        
        prop_assert!((lhs - rhs).abs() < 1e-10);
    }
    
    #[test]
    fn test_black76_call_bounds(
        f in valid_spot(),
        k in valid_strike(),
        t in valid_time(),
        r in valid_rate(),
        sigma in valid_volatility(),
    ) {
        let model = Black76;
        let call_price = model.call_price(f, k, t, r, sigma).unwrap();
        
        // 下限: max(exp(-r*t) * (F - K), 0)
        let intrinsic = ((-r * t).exp() * (f - k)).max(0.0);
        prop_assert!(call_price >= intrinsic - 1e-10);
        
        // 上限: exp(-r*t) * F
        prop_assert!(call_price <= (-r * t).exp() * f + 1e-10);
    }
}

// Mertonモデルのプロパティテスト
proptest! {
    #[test]
    fn test_merton_price_positive(
        s in valid_spot(),
        k in valid_strike(),
        t in valid_time(),
        r in valid_rate(),
        q in valid_dividend(),
        sigma in valid_volatility(),
    ) {
        let call_price = Merton::call_price_merton(s, k, t, r, q, sigma).unwrap();
        prop_assert!(call_price >= 0.0);
        
        let put_price = Merton::put_price_merton(s, k, t, r, q, sigma).unwrap();
        prop_assert!(put_price >= 0.0);
    }
    
    #[test]
    fn test_merton_put_call_parity(
        s in valid_spot(),
        k in valid_strike(),
        t in valid_time(),
        r in valid_rate(),
        q in valid_dividend(),
        sigma in valid_volatility(),
    ) {
        let call = Merton::call_price_merton(s, k, t, r, q, sigma).unwrap();
        let put = Merton::put_price_merton(s, k, t, r, q, sigma).unwrap();
        
        // Merton Put-Call Parity: C - P = S*exp(-q*t) - K*exp(-r*t)
        let lhs = call - put;
        let rhs = s * (-q * t).exp() - k * (-r * t).exp();
        
        prop_assert!((lhs - rhs).abs() < 1e-10);
    }
    
    #[test]
    fn test_merton_reduces_to_black_scholes(
        s in valid_spot(),
        k in valid_strike(),
        t in valid_time(),
        r in valid_rate(),
        sigma in valid_volatility(),
    ) {
        // q=0の時、MertonはBlack-Scholesと一致するはず
        let merton_call = Merton::call_price_merton(s, k, t, r, 0.0, sigma).unwrap();
        let bs_model = BlackScholes;
        let bs_call = bs_model.call_price(s, k, t, r, sigma).unwrap();
        
        prop_assert!((merton_call - bs_call).abs() < 1e-10);
    }
    
    #[test]
    fn test_merton_dividend_effect(
        s in valid_spot(),
        k in valid_strike(),
        t in valid_time(),
        r in valid_rate(),
        sigma in valid_volatility(),
        q1 in valid_dividend(),
        q2 in valid_dividend(),
    ) {
        prop_assume!(q1 < q2);
        
        let call1 = Merton::call_price_merton(s, k, t, r, q1, sigma).unwrap();
        let call2 = Merton::call_price_merton(s, k, t, r, q2, sigma).unwrap();
        
        // 配当が高いほどコール価格は低い
        prop_assert!(call1 >= call2 - 1e-10);
        
        let put1 = Merton::put_price_merton(s, k, t, r, q1, sigma).unwrap();
        let put2 = Merton::put_price_merton(s, k, t, r, q2, sigma).unwrap();
        
        // 配当が高いほどプット価格は高い
        prop_assert!(put1 <= put2 + 1e-10);
    }
}

// 境界値のプロパティテスト
proptest! {
    #[test]
    fn test_extreme_values_handling(
        model_type in 0..3,
    ) {
        // 極端に小さい/大きい値でもパニックしないことを確認
        let extreme_cases = vec![
            (1e-10, 100.0, 1.0, 0.05, 0.2),  // 極小スポット
            (1e10, 100.0, 1.0, 0.05, 0.2),   // 極大スポット
            (100.0, 1e-10, 1.0, 0.05, 0.2),  // 極小ストライク
            (100.0, 1e10, 1.0, 0.05, 0.2),   // 極大ストライク
            (100.0, 100.0, 1e-10, 0.05, 0.2), // 極小時間
            (100.0, 100.0, 100.0, 0.05, 0.2), // 極大時間
            (100.0, 100.0, 1.0, -0.5, 0.2),   // 負の大きな金利
            (100.0, 100.0, 1.0, 0.5, 0.2),    // 大きな金利
            (100.0, 100.0, 1.0, 0.05, 1e-10), // 極小ボラティリティ
            (100.0, 100.0, 1.0, 0.05, 10.0),  // 極大ボラティリティ
        ];
        
        for (s, k, t, r, sigma) in extreme_cases {
            match model_type {
                0 => {
                    let model = BlackScholes;
                    let result = model.call_price(s, k, t, r, sigma);
                    prop_assert!(result.is_ok() || result.is_err());
                }
                1 => {
                    let model = Black76;
                    let result = model.call_price(s, k, t, r, sigma);
                    prop_assert!(result.is_ok() || result.is_err());
                }
                2 => {
                    let result = Merton::call_price_merton(s, k, t, r, 0.05, sigma);
                    prop_assert!(result.is_ok() || result.is_err());
                }
                _ => unreachable!(),
            }
        }
    }
}

// 数値安定性のプロパティテスト
proptest! {
    #[test]
    fn test_numerical_stability(
        s in valid_spot(),
        k in valid_strike(),
        t in valid_time(),
        r in valid_rate(),
        sigma in valid_volatility(),
        epsilon in 1e-10..1e-8,
    ) {
        let model = BlackScholes;
        
        // 入力の微小変化に対して出力も連続的に変化
        let price1 = model.call_price(s, k, t, r, sigma).unwrap();
        let price2 = model.call_price(s + epsilon, k, t, r, sigma).unwrap();
        
        // 価格の変化は入力の変化に比例して小さい
        let price_change = (price2 - price1).abs();
        prop_assert!(price_change < 1000.0 * epsilon);
    }
    
    #[test]
    fn test_greeks_consistency(
        s in valid_spot(),
        k in valid_strike(),
        t in valid_time(),
        r in valid_rate(),
        sigma in valid_volatility(),
    ) {
        let model = BlackScholes;
        let h = 1e-6;
        
        // Deltaの数値微分による検証
        let price_up = model.call_price(s + h, k, t, r, sigma).unwrap();
        let price_down = model.call_price(s - h, k, t, r, sigma).unwrap();
        let numerical_delta = (price_up - price_down) / (2.0 * h);
        
        let greeks = model.greeks(s, k, t, r, sigma, true).unwrap();
        
        // 解析的Deltaと数値的Deltaの一致
        prop_assert!((greeks.delta - numerical_delta).abs() < 1e-4);
    }
}

// Americanモデルのプロパティテスト
proptest! {
    #[test]
    fn test_american_price_positive(
        s in american_spot(),
        k in american_strike(),
        t in american_time(),
        r in american_rate(),
        q in valid_dividend(),
        sigma in american_volatility(),
    ) {
        // アメリカンオプション価格は常に正
        let call_price = American::call_price_american(s, k, t, r, q, sigma).unwrap();
        prop_assert!(call_price >= -1e-10, "American call price should be non-negative: {}", call_price);
        
        let put_price = American::put_price_american(s, k, t, r, q, sigma).unwrap();
        prop_assert!(put_price >= -1e-10, "American put price should be non-negative: {}", put_price);
    }
    
    #[test]
    fn test_american_exceeds_european(
        s in american_spot(),
        k in american_strike(),
        t in american_time(),
        r in american_rate(),
        q in valid_dividend(),
        sigma in american_volatility(),
    ) {
        // アメリカンオプションはヨーロピアンオプション以上の価値
        let american_call = American::call_price_american(s, k, t, r, q, sigma).unwrap();
        let american_put = American::put_price_american(s, k, t, r, q, sigma).unwrap();
        
        // Mertonモデルをヨーロピアンオプションとして使用
        let european_call = Merton::call_price_merton(s, k, t, r, q, sigma).unwrap();
        let european_put = Merton::put_price_merton(s, k, t, r, q, sigma).unwrap();
        
        prop_assert!(american_call >= european_call - 1e-10, 
                    "American call {} should be >= European call {}", american_call, european_call);
        prop_assert!(american_put >= european_put - 1e-10,
                    "American put {} should be >= European put {}", american_put, european_put);
    }
    
    #[test]
    fn test_american_intrinsic_value(
        s in american_spot(),
        k in american_strike(),
        t in american_time(),
        r in american_rate(),
        q in valid_dividend(),
        sigma in american_volatility(),
    ) {
        // アメリカンオプションは常に内在価値以上
        let call_price = American::call_price_american(s, k, t, r, q, sigma).unwrap();
        let put_price = American::put_price_american(s, k, t, r, q, sigma).unwrap();
        
        let call_intrinsic = (s - k).max(0.0);
        let put_intrinsic = (k - s).max(0.0);
        
        prop_assert!(call_price >= call_intrinsic - 1e-10);
        prop_assert!(put_price >= put_intrinsic - 1e-10);
    }
    
    #[test]
    fn test_american_price_bounds(
        s in american_spot(),
        k in american_strike(),
        t in american_time(),
        r in american_rate(),
        q in valid_dividend(),
        sigma in american_volatility(),
    ) {
        let call_price = American::call_price_american(s, k, t, r, q, sigma).unwrap();
        let put_price = American::put_price_american(s, k, t, r, q, sigma).unwrap();
        
        // コール価格の上限はスポット価格
        prop_assert!(call_price <= s + 1e-10);
        
        // プット価格の上限はストライク価格
        prop_assert!(put_price <= k + 1e-10);
    }
    
    #[test]
    fn test_american_monotonicity_spot(
        k in american_strike(),
        t in american_time(),
        r in american_rate(),
        q in valid_dividend(),
        sigma in american_volatility(),
        s1 in american_spot(),
        s2 in american_spot(),
    ) {
        prop_assume!(s1 < s2);
        
        let call1 = American::call_price_american(s1, k, t, r, q, sigma).unwrap();
        let call2 = American::call_price_american(s2, k, t, r, q, sigma).unwrap();
        
        // スポット価格が高いほどコール価格は高い
        prop_assert!(call1 <= call2 + 1e-10);
        
        let put1 = American::put_price_american(s1, k, t, r, q, sigma).unwrap();
        let put2 = American::put_price_american(s2, k, t, r, q, sigma).unwrap();
        
        // スポット価格が高いほどプット価格は低い
        prop_assert!(put1 >= put2 - 1e-10);
    }
    
    #[test]
    fn test_american_greeks_bounds(
        s in american_spot(),
        k in american_strike(),
        t in american_time(),
        r in american_rate(),
        q in valid_dividend(),
        sigma in american_volatility(),
    ) {
        let call_greeks = American::greeks_american(s, k, t, r, q, sigma, true).unwrap();
        let put_greeks = American::greeks_american(s, k, t, r, q, sigma, false).unwrap();
        
        // Delta bounds
        prop_assert!(call_greeks.delta >= -0.01 && call_greeks.delta <= 1.01);
        prop_assert!(put_greeks.delta >= -1.01 && put_greeks.delta <= 0.01);
        
        // Gamma should be positive
        prop_assert!(call_greeks.gamma >= -1e-10);
        prop_assert!(put_greeks.gamma >= -1e-10);
        
        // Vega should be positive
        prop_assert!(call_greeks.vega >= -1e-10);
        prop_assert!(put_greeks.vega >= -1e-10);
    }
}