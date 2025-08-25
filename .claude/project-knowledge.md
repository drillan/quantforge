# プロジェクトナレッジ

## 概要
QuantForgeの開発で蓄積された技術的知見、実装パターン、ベストプラクティスを記録します。

## リファクタリング知見（2025-08-25）

### コード重複検出と解消

#### 使用ツール
- `similarity-rs`: Rustコードの意味的類似性検出ツール
- 閾値85%で検出、4つの重複パターンを発見

#### 重複パターンと解決策

1. **Critical Bug: 条件付きコンパイルの無意味な重複**
   - 問題: `#[cfg]`で分岐しているが実装が同一
   - 解決: 統一実装に変更、将来のSIMD拡張点を明確化
   - ファイル: `src/math/distributions.rs`

2. **ベンチマークパラメータの重複**
   - 問題: 95.45%の類似度、パラメータのハードコード
   - 解決: 共通モジュール`benches/common/mod.rs`を作成
   - 効果: パラメータ変更が一箇所で完結

3. **テストヘルパーの欠如**
   - 問題: 似た構造のテストが繰り返し（94.58%類似）
   - 解決: `TestOption`構造体によるビルダーパターン実装
   - 効果: テストの可読性と保守性が向上

#### 実装パターン

```rust
// テストヘルパーのビルダーパターン
struct TestOption {
    spot: f64,
    strike: f64,
    time: f64,
    rate: f64,
    vol: f64,
}

impl TestOption {
    fn atm() -> Self { /* デフォルト値 */ }
    fn with_spot(mut self, spot: f64) -> Self { 
        self.spot = spot;
        self  // チェーン可能
    }
    fn price(&self) -> f64 { /* 計算実行 */ }
    fn assert_price_near(&self, expected: f64, epsilon: f64) { 
        /* アサーション */ 
    }
}
```

#### 成果
- コード重複: 4箇所 → 3箇所（ベンチマークの本質的な構造類似は許容）
- Critical Bug: 1件解消
- 保守性: パラメータ管理の一元化達成
- テスト可読性: ビルダーパターンで意図が明確に

### Rust品質管理

#### Clippy警告への対応
- `uninlined_format_args`: フォーマット文字列での変数直接使用
  ```rust
  // Before
  assert!(cond, "Value {} is {}", x, y);
  // After  
  assert!(cond, "Value {x} is {y}");
  ```

#### cargo fmt適用
- 一貫したコードフォーマット維持
- CIでの自動チェック推奨

### ベンチマーク設計

#### 共通パラメータモジュール構造
```rust
pub mod test_params {
    pub struct DefaultParams;
    
    impl DefaultParams {
        pub const STRIKE: f64 = 100.0;
        pub const TIME_TO_MATURITY: f64 = 1.0;
        // ...
    }
    
    pub fn atm_params(spot: f64) -> (f64, f64, f64, f64, f64) { }
    pub fn itm_params(premium: f64) -> (f64, f64, f64, f64, f64) { }
    // ...
}
```

### 今後の改善ポイント

1. **SIMD実装の準備**
   - `norm_cdf_simd`関数のスケルトン実装完了
   - target_feature検出によるランタイムディスパッチ準備

2. **プロパティベーステスト**
   - テストヘルパーを活用した網羅的テスト実装可能

3. **CI統合**
   - similarity-rsによる重複検出の自動化
   - 閾値85%での品質ゲート設定推奨