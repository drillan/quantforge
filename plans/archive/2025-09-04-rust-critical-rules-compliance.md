# [Rust] Critical Rules違反修正および品質改善 実装計画

> **✅ 完了済み (2025-09-04)**  
> すべてのCritical Rules違反を修正し、品質基準を達成しました。
> - 44件のハードコード違反を修正
> - 7箇所のDRY違反を解消
> - 並列化閾値を統一
> - 不要なclone操作を削除

## メタデータ
- **作成日**: 2025-09-04
- **言語**: Rust
- **ステータス**: COMPLETED
- **推定規模**: 中
- **推定コード行数**: 200-300行（修正箇所多数、各修正は小規模）
- **対象モジュール**: core/src/compute/, core/src/constants.rs, core/src/arrow_native.rs

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 200-300行
- [x] 新規ファイル数: 0個（既存ファイル修正のみ）
- [x] 影響範囲: 複数モジュール
- [ ] PyO3バインディング: 不要（Rust内部修正のみ）
- [ ] SIMD最適化: 不要（禁止事項）
- [x] 並列化: 必要（閾値統一）

### 規模判定結果
**中規模タスク**

## 品質管理ツール（Rust）

### 適用ツール（中規模タスク）
| ツール | 適用 | 実行コマンド |
|--------|------|-------------|
| cargo test | ✅ | `cargo test --all --release` |
| cargo clippy | ✅ | `cargo clippy --all-targets --all-features -- -D warnings` |
| cargo fmt | ✅ | `cargo fmt --all --check` |
| similarity-rs | 条件付き | 重複解消後に実行 |
| rust-refactor.md | 条件付き | 必要に応じて適用 |
| cargo bench | 推奨 | `cargo bench` |

## 1. 概要

レビューで検出されたCritical Rules違反を**すべて一度に修正**し、コード品質を向上させる。段階的実装は禁止、理想実装のみ。

### 検出された違反サマリー
- **[C011-3] ハードコード違反**: 44件
- **[C012] DRY違反**: 7箇所（d1/d2計算重複）
- **[C013] 設計不整合**: 並列化閾値の不統一
- **パフォーマンス**: 不要なclone 1箇所

## 2. 技術詳細

### Phase 1: ハードコード違反修正（C011-3）

#### 1.1 定数定義の追加（constants.rs）
```rust
// core/src/constants.rs に追加

// ============================================================================
// Greeks計算用定数
// ============================================================================

/// Greeksの有限差分計算用: 価格変化率
/// Delta, Gammaの計算で使用する価格の変化割合
pub const GREEK_PRICE_CHANGE_RATIO: f64 = 0.01; // 1%

/// Greeksの有限差分計算用: ボラティリティ変化幅
/// Vegaの計算で使用するボラティリティの変化幅
pub const GREEK_VOL_CHANGE: f64 = 0.01; // 1%

/// Greeksの有限差分計算用: 金利変化幅（ベーシスポイント）
/// Rhoの計算で使用する金利の変化幅
pub const GREEK_RATE_CHANGE: f64 = 0.0001; // 1 basis point

/// 満期直前判定閾値
/// この時間以下の場合、満期直前として特別処理
pub const TIME_NEAR_EXPIRY_THRESHOLD: f64 = 1e-10;

/// 配当利回りゼロ判定閾値
/// アメリカンオプションで早期行使判定に使用
pub const DIVIDEND_ZERO_THRESHOLD: f64 = 1e-10;

/// ボラティリティゼロ判定閾値
/// 決定論的価格計算への切り替え判定
pub const VOLATILITY_ZERO_THRESHOLD: f64 = 1e-10;

// ============================================================================
// テスト用定数
// ============================================================================

/// 標準テストケース: スポット価格
pub const TEST_SPOT: f64 = 100.0;

/// 標準テストケース: 権利行使価格
pub const TEST_STRIKE: f64 = 100.0;

/// 標準テストケース: 満期（年）
pub const TEST_TIME: f64 = 1.0;

/// 標準テストケース: 無リスク金利
pub const TEST_RATE: f64 = 0.05;

/// 標準テストケース: ボラティリティ
pub const TEST_VOLATILITY: f64 = 0.2;

/// 標準テストケース: 配当利回り
pub const TEST_DIVIDEND_YIELD: f64 = 0.02;

/// Black-Scholesテスト期待値範囲（formulas.rs用）
pub const TEST_BS_FORMULAS_PRICE_LOWER: f64 = 6.0;
pub const TEST_BS_FORMULAS_PRICE_UPPER: f64 = 10.0;

/// Black76テスト期待値範囲（formulas.rs用）
pub const TEST_BLACK76_FORMULAS_PRICE_LOWER: f64 = 7.0;
pub const TEST_BLACK76_FORMULAS_PRICE_UPPER: f64 = 11.0;
```

#### 1.2 American Greeks修正例
```rust
// core/src/compute/american.rs の修正

use crate::constants::{
    GREEK_PRICE_CHANGE_RATIO,
    GREEK_VOL_CHANGE,
    GREEK_RATE_CHANGE,
    TIME_NEAR_EXPIRY_THRESHOLD,
    DIVIDEND_ZERO_THRESHOLD,
    VOLATILITY_ZERO_THRESHOLD,
    DAYS_PER_YEAR,
    BASIS_POINT_MULTIPLIER,
    HALF,  // 既存
};

// Line 139の修正
if t < TIME_NEAR_EXPIRY_THRESHOLD {
    return (s - k).max(0.0);
}

// Line 251の修正
let h = GREEK_PRICE_CHANGE_RATIO * s;

// Line 303の修正
let h = 1.0 / DAYS_PER_YEAR;

// Line 329の修正
let h = GREEK_RATE_CHANGE;
```

### Phase 2: DRY違反修正（C012）

#### 2.1 共通計算関数の作成
```rust
// core/src/math/mod.rs に追加（または新規ファイル core/src/math/black_scholes_math.rs）

/// Black-Scholes d1, d2パラメータの計算
/// 
/// # Arguments
/// * `s` - スポット価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間
/// * `r` - 無リスク金利
/// * `q` - 配当利回り（0の場合は配当なし）
/// * `sigma` - ボラティリティ
/// 
/// # Returns
/// (d1, d2) のタプル
#[inline]
pub fn calculate_d1_d2(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> (f64, f64) {
    let sqrt_t = t.sqrt();
    let variance_term = sigma * sigma * HALF;
    let d1 = ((s / k).ln() + (r - q + variance_term) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;
    (d1, d2)
}

/// Black76 d1, d2パラメータの計算
/// 
/// # Arguments
/// * `f` - フォワード価格
/// * `k` - 権利行使価格
/// * `t` - 満期までの時間
/// * `sigma` - ボラティリティ
/// 
/// # Returns
/// (d1, d2) のタプル
#[inline]
pub fn calculate_black76_d1_d2(f: f64, k: f64, t: f64, sigma: f64) -> (f64, f64) {
    let sqrt_t = t.sqrt();
    let d1 = ((f / k).ln() + (sigma * sigma * HALF) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;
    (d1, d2)
}
```

#### 2.2 既存コードの修正
```rust
// core/src/compute/traits.rs の修正
use crate::math::{calculate_d1_d2, calculate_black76_d1_d2};

impl BlackScholesParams {
    pub fn calculate_prices(&self) -> (f64, f64) {
        let (d1, d2) = calculate_d1_d2(self.s, self.k, self.t, self.r, 0.0, self.sigma);
        // 残りの計算...
    }
}

impl Black76Params {
    pub fn calculate_prices(&self) -> (f64, f64) {
        let (d1, d2) = calculate_black76_d1_d2(self.f, self.k, self.t, self.sigma);
        // 残りの計算...
    }
}

// core/src/arrow_native.rs の修正も同様
```

### Phase 3: 並列化閾値統一（設計不整合修正）

#### 3.1 arrow_native.rsの修正
```rust
// core/src/arrow_native.rs の修正

use crate::constants::get_parallel_threshold;

// Line 11の独自定数を削除
// const PARALLEL_THRESHOLD: usize = 50_000; // 削除

// 使用箇所の修正
pub fn black_scholes_call_batch(...) -> Result<Float64Array> {
    let threshold = get_parallel_threshold();
    
    if len >= threshold {
        // 並列処理
    } else {
        // シーケンシャル処理
    }
}
```

### Phase 4: パフォーマンス改善

#### 4.1 不要なclone削除
```rust
// core/src/compute/greeks.rs:89 の修正

// 現在
let fields: Vec<String> = greeks.fields().iter().map(|f| f.name().clone()).collect();

// 修正後（所有権が必要な場合）
let fields: Vec<String> = greeks.fields().iter().map(|f| f.name().to_string()).collect();

// または（参照で十分な場合）
let fields: Vec<&str> = greeks.fields().iter().map(|f| f.name()).collect();
```

## 3. 実装チェックリスト

### Phase 1: ハードコード修正
- [x] constants.rsに新規定数追加 ✅
- [x] american.rs内の44箇所のハードコード修正 ✅
- [x] formulas.rs内のテスト値修正 ✅
- [x] その他のモジュールのハードコード修正 ✅

### Phase 2: DRY違反修正
- [x] math/black_scholes_math.rs作成 ✅
- [x] calculate_d1_d2関数実装 ✅
- [x] calculate_black76_d1_d2関数実装 ✅
- [x] 5箇所のd1/d2計算を共通関数に置換 ✅

### Phase 3: 並列化閾値統一
- [x] arrow_native.rsの独自定数削除 ✅
- [x] get_parallel_threshold()使用に統一 ✅
- [x] 環境変数対応の確認 ✅

### Phase 4: パフォーマンス改善
- [x] 不要なclone削除 ✅
- [x] ベンチマーク実行で改善確認 ✅

## 4. 品質確認

### 必須テスト
```bash
# フォーマットチェック
cargo fmt --all -- --check

# Lintチェック
cargo clippy --all-targets --all-features -- -D warnings

# テスト実行
cargo test --all --release

# Python統合テスト
uv run pytest tests/

# ハードコード検出（ゼロになることを確認）
./scripts/detect_hardcode.sh
```

### パフォーマンス確認
```bash
# ベンチマーク実行
cargo bench --bench performance

# 特定のベンチマーク
cargo bench american
```

## 5. 成功基準

- [x] すべてのCritical Rules違反が解消（C011-3, C012, C013） ✅
- [x] cargo test --all --release がすべてパス ✅
- [x] cargo clippy警告ゼロ ✅
- [x] ./scripts/detect_hardcode.sh で検出ゼロ ✅
- [x] パフォーマンステストで劣化なし ✅
- [x] Python統合テスト（pytest）すべてパス ✅

## 6. リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 定数変更による挙動変化 | 高 | 既存テストで回帰確認 |
| 並列化閾値変更の影響 | 中 | ベンチマークで性能確認 |
| d1/d2統合のバグ | 高 | 単体テスト充実 |

## 7. 命名定義

### 7.1 使用する既存命名
```yaml
existing_names:
  - name: "s"
    meaning: "スポット価格"
    source: "naming_conventions.md#共通パラメータ"
  - name: "k"
    meaning: "権利行使価格"
    source: "naming_conventions.md#共通パラメータ"
  - name: "t"
    meaning: "満期までの時間"
    source: "naming_conventions.md#共通パラメータ"
  - name: "r"
    meaning: "無リスク金利"
    source: "naming_conventions.md#共通パラメータ"
  - name: "sigma"
    meaning: "ボラティリティ"
    source: "naming_conventions.md#共通パラメータ"
  - name: "q"
    meaning: "配当利回り"
    source: "naming_conventions.md#Black-Scholes系"
```

### 7.2 新規提案命名
```yaml
proposed_names:
  # 新規定数名（constants.rs）
  - name: "GREEK_PRICE_CHANGE_RATIO"
    meaning: "Greeks計算の価格変化率"
    justification: "有限差分法で使用する標準的な変化率"
    status: "implementing"
  
  - name: "TIME_NEAR_EXPIRY_THRESHOLD"
    meaning: "満期直前判定閾値"
    justification: "数値的に満期と見なす閾値"
    status: "implementing"
```

### 7.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 8. 備考

- Critical Rules C001-C014を厳格に遵守
- 段階的実装は絶対禁止、すべての修正を一度に実施
- SIMD最適化は提案禁止（過去に210行削除済み）
- プロファイリングなしの推測最適化は禁止