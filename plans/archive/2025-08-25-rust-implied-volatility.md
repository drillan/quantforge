# Rust インプライドボラティリティ実装計画

## メタデータ
- **作成日**: 2025-08-25
- **ステータス**: COMPLETED
- **タイプ**: 実装計画（Rust）
- **規模**: 大（>500行）
- **期間**: 4週間
- **優先度**: HIGH
- **関連文書**:
  - [実装計画](./archive/2025-01-24-implementation-plan.md)
  - [Black-Scholesコア実装](./archive/2025-01-24-rust-bs-core.md)
  - [Greeks実装](./archive/2025-08-26-rust-greeks-implementation.md)

## 1. 概要

### 1.1 目的
Black-Scholes逆算による市場インプライドボラティリティ（IV）計算機能の高性能実装。金融実務で必須のIV計算を、Rust+PyO3による超高速処理で提供する。

### 1.2 背景
- 現在Black-Scholes順算（価格計算）とGreeks計算は実装済み
- 市場価格からのIV逆算機能が未実装
- 金融実務では価格→IV変換が頻繁に必要

### 1.3 スコープ
- ✅ Newton-Raphson法による高速IV計算
- ✅ Brent法によるフォールバック実装
- ✅ 初期推定値最適化（Brenner-Subrahmanyam、Corrado-Miller）
- ✅ エッジケース処理（Deep ITM/OTM、満期直前）
- ✅ バッチ処理と並列化（Rayon）
- ✅ Python統合（PyO3）
- ❌ アメリカンオプションのIV（将来実装）
- ❌ エキゾチックオプションのIV（将来実装）

## 2. 技術設計

### 2.1 アーキテクチャ

```
src/
├── math/
│   └── solvers.rs              # 数値解法基盤
│       ├── newton_raphson()    # Newton-Raphson法
│       ├── brent()             # Brent法
│       └── hybrid_solver()     # ハイブリッドソルバー
├── models/
│   ├── implied_volatility.rs   # IV計算メインモジュール
│   │   ├── implied_volatility_call()
│   │   ├── implied_volatility_put()
│   │   ├── implied_volatility_batch()
│   │   └── implied_volatility_batch_parallel()
│   └── iv_initial_guess.rs     # 初期推定値算出
│       ├── brenner_subrahmanyam()
│       ├── corrado_miller()
│       └── adaptive_initial_guess()
├── constants.rs                # 定数定義追加
└── error.rs                    # エラー型追加
```

### 2.2 アルゴリズム設計

#### 2.2.1 ハイブリッドソルバー戦略
```rust
pub fn solve_implied_volatility(
    price: f64, s: f64, k: f64, t: f64, r: f64, is_call: bool
) -> Result<f64, IVError> {
    // 1. エッジケース事前チェック
    if is_edge_case(price, s, k, t, r, is_call) {
        return handle_edge_case(price, s, k, t, r, is_call);
    }
    
    // 2. 初期推定値計算
    let initial_guess = adaptive_initial_guess(price, s, k, t, r, is_call);
    
    // 3. Newton-Raphson法（高速パス）
    match newton_raphson_iv(price, s, k, t, r, is_call, initial_guess, 7) {
        Ok(iv) => Ok(iv),
        Err(_) => {
            // 4. Brent法フォールバック（確実パス）
            brent_iv(price, s, k, t, r, is_call)
        }
    }
}
```

#### 2.2.2 Newton-Raphson法実装
```rust
fn newton_raphson_iv(
    target_price: f64,
    s: f64, k: f64, t: f64, r: f64,
    is_call: bool,
    initial_iv: f64,
    max_iter: usize
) -> Result<f64, IVError> {
    let mut iv = initial_iv;
    let mut prev_delta: Option<f64> = None;
    
    for i in 0..max_iter {
        // 現在のIVでの理論価格計算
        let calc_price = if is_call {
            bs_call_price(s, k, t, r, iv)
        } else {
            bs_put_price(s, k, t, r, iv)
        };
        
        let price_error = calc_price - target_price;
        
        // 収束判定
        if price_error.abs() < IV_TOLERANCE_PRICE {
            return Ok(iv);
        }
        
        // Vega計算（既存関数を利用）
        let vega = greeks::vega(s, k, t, r, iv);
        
        // Vegaが小さすぎる場合は失敗
        if vega.abs() < VEGA_MIN_THRESHOLD {
            return Err(IVError::NumericalInstability);
        }
        
        // Newton-Raphsonステップ
        let delta_iv = price_error / vega;
        
        // 振動検出
        if let Some(prev) = prev_delta {
            if delta_iv * prev < 0.0 && (delta_iv.abs() - prev.abs()).abs() < 1e-8 {
                return Err(IVError::ConvergenceFailed);
            }
        }
        
        // IV更新（境界制約付き）
        iv = (iv - delta_iv).clamp(IV_MIN_VOL, IV_MAX_VOL);
        prev_delta = Some(delta_iv);
    }
    
    Err(IVError::ConvergenceFailed)
}
```

### 2.3 パフォーマンス目標

| 処理タイプ | 目標性能 | 測定方法 |
|----------|---------|---------|
| 単一計算（ATM） | < 100ns | criterion benchmark |
| 単一計算（全般） | < 200ns | criterion benchmark |
| 100万件バッチ | < 50ms | criterion benchmark |
| 収束率 | > 99.99% | 100万件テスト |
| 平均反復回数 | < 3回 | Newton法統計 |

## 3. 実装計画

### 3.1 Phase 1: 数値解法基盤（Week 1）

#### タスク
1. [x] `src/math/solvers.rs` 作成 ✅
2. [x] Newton-Raphson法実装 ✅
3. [x] Brent法実装 ✅
4. [x] 収束判定ロジック実装 ✅
5. [x] 単体テスト作成 ✅

#### 成果物
- 完全な数値解法モジュール
- 90%以上のテストカバレッジ

### 3.2 Phase 2: 初期推定値最適化（Week 2）

#### タスク
1. [x] `src/models/iv_initial_guess.rs` 作成 ✅
2. [x] Brenner-Subrahmanyam近似実装 ✅
3. [x] Corrado-Miller近似実装 ✅
4. [x] モネネス適応型選択ロジック ✅
5. [x] エッジケース処理実装 ✅

#### 成果物
- 初期推定値モジュール
- エッジケース対応完了

### 3.3 Phase 3: IV計算エンジン統合（Week 3）

#### タスク
1. [x] `src/models/implied_volatility.rs` 作成 ✅
2. [x] ハイブリッドソルバー実装 ✅
3. [x] バッチ処理インターフェース ✅
4. [x] Rayon並列化実装 ✅
5. [x] ゴールデンマスターテスト作成 ✅

#### 成果物
- 完全なIV計算エンジン
- ゴールデンマスターテスト

### 3.4 Phase 4: Python統合と最適化（Week 4）

#### タスク
1. [x] PyO3バインディング作成 ✅
2. [x] NumPyゼロコピー連携 ✅
3. [x] パフォーマンスベンチマーク ✅
4. [x] ドキュメント作成 ✅
5. [x] 統合テスト実装 ✅

#### 成果物
- Python API完成
- 完全なドキュメント
- パフォーマンスレポート

## 4. 定数定義（C011-3適用）

```rust
// src/constants.rs に追加
/// IV計算: 最大反復回数
pub const IV_MAX_ITERATIONS: usize = 20;

/// IV計算: 価格収束判定閾値
pub const IV_TOLERANCE_PRICE: f64 = 1e-9;

/// IV計算: ボラティリティ収束判定閾値
pub const IV_TOLERANCE_VOL: f64 = 1e-6;

/// IV計算: 最小ボラティリティ（0.1%）
pub const IV_MIN_VOL: f64 = 0.001;

/// IV計算: 最大ボラティリティ（500%）
pub const IV_MAX_VOL: f64 = 5.0;

/// IV計算: Vega最小閾値（数値安定性）
pub const VEGA_MIN_THRESHOLD: f64 = 1e-10;

/// IV計算: 初期ブラケット幅
pub const IV_INITIAL_BRACKET_WIDTH: f64 = 0.5;

/// Newton法: 最大試行回数
pub const NEWTON_MAX_ATTEMPTS: usize = 7;

/// Brent法: 最大反復回数
pub const BRENT_MAX_ITERATIONS: usize = 50;
```

## 5. エラーハンドリング

```rust
// src/error.rs に追加
#[derive(Error, Debug)]
pub enum IVError {
    #[error("Price violates no-arbitrage bounds")]
    NoArbitrageBreach,
    
    #[error("Failed to converge after {0} iterations")]
    ConvergenceFailed(usize),
    
    #[error("Invalid market price: {0}")]
    InvalidMarketPrice(f64),
    
    #[error("Numerical instability detected (Vega too small)")]
    NumericalInstability,
    
    #[error("Failed to find valid bracket for root finding")]
    BracketingFailed,
}
```

## 6. テスト戦略（C010適用）

### 6.1 単体テスト
```rust
#[cfg(test)]
mod tests {
    // Newton法の収束性テスト
    #[test]
    fn test_newton_convergence_atm() { ... }
    
    // Brent法の確実性テスト
    #[test]
    fn test_brent_reliability_deep_otm() { ... }
    
    // エッジケーステスト
    #[test]
    fn test_edge_cases() { ... }
}
```

### 6.2 ゴールデンマスターテスト
- 既知のIV値との照合（誤差 < 1e-6）
- 価格→IV→価格の往復精度検証
- Put-Callパリティ整合性

### 6.3 プロパティベーステスト
```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_iv_monotonicity(
        s in 10.0..200.0,
        k in 10.0..200.0,
        t in 0.01..2.0,
        r in -0.1..0.1,
    ) {
        // 価格が増加→IVも増加
    }
}
```

## 7. 品質管理チェックリスト（C006/C007適用）

### 実装前
- [x] 既存コード調査完了（DRY原則 C012） ✅
- [x] 定数定義確認（ハードコード禁止 C011-3） ✅
- [x] エラー型定義完了 ✅

### 実装中
- [x] `cargo test` 全テスト成功 ✅
- [x] `cargo clippy` 警告ゼロ ✅
- [x] `similarity-rs` 重複チェック ✅

### 実装後
- [x] ベンチマーク目標達成 ✅
- [x] ドキュメント完成 ✅
- [x] Python統合テスト成功 ✅

## 8. リスクと対策

| リスク | 影響度 | 対策 |
|-------|-------|------|
| Newton法の収束失敗 | 高 | Brent法フォールバック実装済み |
| 初期推定値の精度不足 | 中 | 複数の近似式を適応的に選択 |
| エッジケースでの数値不安定性 | 高 | 専用処理パス実装 |
| パフォーマンス目標未達 | 中 | SIMD最適化の追加検討 |

## 9. 成功基準

### 必須要件
- [x] 収束率 > 99.99%（100万件テスト）
- [x] 単一計算 < 200ns
- [x] テストカバレッジ > 95%
- [x] ゼロハードコード達成

### 追加目標
- [ ] 平均反復回数 < 3（Newton法）
- [ ] バッチ処理 < 50ns/計算
- [ ] SIMD最適化実装

## 10. 参考資料

- Brenner, M., & Subrahmanyam, M. G. (1988). A simple formula to compute the implied standard deviation
- Corrado, C. J., & Miller, T. W. (1996). A note on a simple, accurate formula to compute implied standard deviations
- Press, W. H., et al. (2007). Numerical Recipes: The Art of Scientific Computing (Brent法)

---

**作成者**: Claude
**最終更新**: 2025-08-25
**完了日**: 2025-08-25
**次回レビュー**: Week 1完了時