# プロジェクトナレッジ

## 概要
QuantForgeの開発で蓄積された技術的知見、実装パターン、ベストプラクティスを記録します。

## 重要な設計原則

### 理想実装ファースト（C004）
- 段階的実装や「後で改善」は禁止
- 最初から正しい実装を選択
- 例: Abramowitz-Stegun → erfベース直接移行

### ZERO HARDCODE POLICY（C011）
- すべての数値定数に名前を付ける
- 定数の根拠をコメントで明記
- 例: `const PARALLEL_THRESHOLD: usize = 10000;`

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

## norm_cdf実装の進化（2025-08-25）

### Abramowitz-Stegun → erfベース移行

#### 技術選定の転換
```rust
// 以前: Abramowitz-Stegun 5次多項式近似
// 精度: ~7.5×10⁻⁸（最大誤差）
pub fn norm_cdf(x: f64) -> f64 {
    // 5つの係数による多項式近似
    // 高速だが精度限界あり
}

// 現在: erfベース実装
// 精度: <1e-15（機械精度）
use libm::erf;
pub fn norm_cdf(x: f64) -> f64 {
    0.5 * (1.0 + erf(x / std::f64::consts::SQRT_2))
}
```

#### パフォーマンスへの影響
- **単一計算**: 10ns → 10-12ns（わずかな増加）
- **バッチ処理**: 20ms → 51ms（2.5倍遅い）
- **精度**: 1e-5 → 1e-15（3000倍改善）

#### 設計決定の根拠
1. **精度優先**: 金融計算では精度が最重要
2. **外部ライブラリ容認**: libmは高品質で信頼性が高い
3. **最適化戦略の変更**: 精度を落とさずSIMD/並列化で高速化

### Deep OTMでの数値安定性

#### 問題と解決
```rust
// Deep OTMで浮動小数点誤差により負値が発生
// 例: -7.98e-17

// 解決: 物理的制約を明示的に適用
pub fn bs_call_price(...) -> f64 {
    (計算結果).max(0.0)  // コールオプション価格は非負
}
```

#### バッチ処理のバリデーション追加
```rust
// 以前: バリデーション完全欠落（重大な欠陥）
// 現在: 包括的なバリデーション
for &s in spots {
    if !s.is_finite() {
        return Err("NaN or infinite values");
    }
    if s <= 0.0 {
        return Err(format!("Spot price must be positive, got {}", s));
    }
}
```

### テスト期待値の更新戦略

#### ゴールデンマスターテストの扱い
1. **実装変更時**: すべての期待値を再計算
2. **検証方法**: SciPyとの照合で正確性を確認
3. **許容誤差の調整**: 実装精度に応じて動的に変更

#### ATM近似の前提条件
```python
# ATM近似式: S * v * sqrt(T/(2π))
# 前提: 金利r≈0

# テストパラメータの制限
r=st.floats(min_value=-0.02, max_value=0.02)  # 低金利のみ
t=st.floats(min_value=0.1, max_value=1)        # 短期のみ
v=st.floats(min_value=0.15, max_value=0.4)     # 中程度のボラティリティ
```