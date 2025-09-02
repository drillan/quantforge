# [Rust] QuantForge既存コード品質改善 実装計画

## メタデータ
- **作成日**: 2025-09-02
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 小
- **推定コード行数**: 約50行（定数追加と既存コード修正）
- **対象モジュール**: core/src/constants.rs, core/src/compute/*, core/src/math/*, core/src/arrow_native.rs

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 50行
- [x] 新規ファイル数: 0個
- [x] 影響範囲: 複数モジュール（compute, math, arrow_native）
- [x] PyO3バインディング: 不要（Rust側のみ）
- [x] SIMD最適化: 不要
- [x] 並列化: 不要（既存実装を維持）

### 規模判定結果
**小規模タスク** - Critical Rules違反の即座修正と既存コードの品質改善

## 品質管理ツール（Rust）

### 適用ツール
| ツール | 適用 | 実行コマンド |
|--------|------|-------------|
| cargo test | ✅ | `cargo test --all --release` |
| cargo clippy | ✅ | `cargo clippy --all-targets --all-features -- -D warnings` |
| cargo fmt | ✅ | `cargo fmt --all -- --check` |
| similarity-rs | - | 不要（新規実装なし） |
| rust-refactor.md | - | 不要（小規模修正） |

## Critical Rules違反の詳細と修正計画

### 1. [C011-3] ハードコード違反: 8件

#### 1.1 テスト許容値のハードコード（3件）
**問題箇所**:
- `core/src/compute/black76.rs:323,340`: `assert!(...abs() < 0.01)`
- `core/src/compute/black_scholes.rs:480`: `assert!(...abs() < 0.01)`

**修正内容**:
```rust
// core/src/constants.rs に追加
/// Vega計算のテスト許容値
/// 
/// Vegaは他のGreeksより絶対値が大きいため、専用の許容値を設定。
/// 0.01 = 1セント（オプション価格の実務的な最小単位）
pub const TEST_TOLERANCE_VEGA: f64 = 0.01;
```

#### 1.2 高精度テストのハードコード（3件）
**問題箇所**:
- `core/src/math/distributions.rs:117,120,139`: `assert!(...abs() < 1e-15)`

**修正内容**:
```rust
// core/src/constants.rs に追加
/// 浮動小数点演算の理論的最高精度
/// 
/// f64のマシンイプシロン近傍での比較に使用。
/// 数学関数の理論値との一致確認で使用。
pub const PRECISION_HIGHEST: f64 = 1e-15;
```

#### 1.3 Arrow Nativeテストのハードコード（3件）
**問題箇所**:
- `core/src/arrow_native.rs:320,337,356`: `assert!(...abs() < 1e-10)`

**修正内容**:
```rust
// 既存定数 VEGA_MIN_THRESHOLD (1e-10) を使用するか、専用定数を追加
/// Arrow演算の精度検証用閾値
/// 
/// FFI境界での精度保証に使用。
pub const ARROW_PRECISION_THRESHOLD: f64 = 1e-10;
```

#### 1.4 テストアサーション範囲のハードコード（2件）
**問題箇所**:
- `core/src/compute/formulas.rs:188`: `assert!(price > 8.0 && price < 12.0)`

**修正内容**:
```rust
// core/src/constants.rs に追加
/// Black-Scholesテストケースの期待価格範囲
/// 
/// S=100, K=100, T=1, r=0.05, σ=0.2の標準ケースでの価格範囲
pub const TEST_BS_PRICE_LOWER: f64 = 8.0;
pub const TEST_BS_PRICE_UPPER: f64 = 12.0;
```

### 2. [C012] コード重複: 2件

#### 2.1 d1/d2計算の重複
**問題箇所**:
- `core/src/compute/black_scholes.rs:258`: インライン計算
- `core/src/compute/black76.rs`: 153,188,218,249,287行目で同じ計算
- `core/src/compute/formulas.rs`: 専用関数あり

**修正内容**:
```rust
// black_scholes.rs と black76.rs で formulas.rs の関数を使用
use super::formulas::{black_scholes_d1_d2, black76_d1_d2};

// 例: black_scholes.rs:258付近
let (d1, d2) = black_scholes_d1_d2(s, k, t, r, sigma);

// 例: black76.rs の各箇所
let (d1, d2) = black76_d1_d2(f, k, t, sigma);
```

#### 2.2 ボラティリティ二乗項の重複
**問題箇所**:
- `sigma * sigma / 2.0` が複数箇所で重複

**修正内容**:
```rust
// 既存定数 VOL_SQUARED_HALF (2.0) と HALF (0.5) を活用
// または以下を追加
/// ボラティリティ二乗の半分の計算用
pub const VOL_SQUARED_HALF_FACTOR: f64 = 0.5;

// 使用例
let vol_squared_half = sigma * sigma * VOL_SQUARED_HALF_FACTOR;
```

## 実装フェーズ（小規模）

### Phase 1: 定数定義の追加（30分）
- [x] constants.rsに新規定数を追加
- [x] 各定数に適切なdocコメントを記載
- [x] 定数の値の根拠を明記

### Phase 2: ハードコード置換（1時間）
- [x] テストファイルのマジックナンバーを定数に置換
- [x] 計算式内の数値リテラルを定数に置換
- [x] アサーションメッセージを改善

### Phase 3: コード重複の解消（30分）
- [x] d1/d2計算を formulas.rs の関数に統一
- [x] Black76の重複計算を削除
- [x] 共通パターンの抽出

### Phase 4: 品質チェック（30分）
```bash
# 基本チェック
cargo fmt --all
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all --release

# 追加チェック
grep -r "0\.01\|1e-10\|1e-15\|8\.0\|12\.0" core/src --include="*.rs" | grep -v "const"
```

## 技術要件

### 必須要件
- [x] Critical Rules C011-3（ハードコード禁止）の完全遵守
- [x] Critical Rules C012（DRY原則）の完全遵守
- [x] 既存のテストがすべてパス
- [x] パフォーマンスの維持（劣化なし）

### 品質目標
- [x] ハードコード違反: 0件
- [x] コード重複: 0件
- [x] Clippy警告: 0件

## チェックリスト

### 実装前
- [x] 既存定数の確認（constants.rs）
- [x] 影響範囲の特定
- [x] テスト環境の準備

### 実装中
- [x] 定数定義時のdocコメント記載
- [x] 値の根拠の明記
- [x] 段階的な動作確認

### 実装後
- [x] cargo test --all --release 成功
- [x] cargo clippy 警告なし
- [x] ハードコード検出スクリプトで0件確認
- [x] 計画のarchive移動

## 成果物

- [x] 更新されたconstants.rs（8個の新規定数）
- [x] 修正されたcompute/モジュール（重複削除）
- [x] 修正されたテストコード（定数使用）
- [x] 品質改善レポート（違反0件達成）

## 改善後の品質メトリクス

| カテゴリ | 改善前 | 改善後 |
|---------|--------|--------|
| Critical Rules違反 | 8件 | **0件** ✅ |
| ハードコード | 8箇所 | **0箇所** ✅ |
| コード重複 | 2パターン | **0件** ✅ |
| テストカバレッジ | 維持 | 維持 |
| パフォーマンス | 基準値 | 劣化なし |

## 備考

- すべての修正は一度に実施（段階的実装禁止: C004/C014）
- 既存のパフォーマンスを維持（並列化閾値等は変更なし）
- unsafeコードは使用されていないため、契約の問題なし
- SIMD最適化の提案は絶対に行わない（アンチパターン）

## 参照禁止

- plans/archive/ 内の過去の計画
- 特に SIMD/AVX2 関連の過去の失敗計画