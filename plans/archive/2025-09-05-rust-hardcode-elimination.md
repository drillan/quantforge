# [Rust] ハードコード完全排除・Critical Rules準拠 実装計画

## メタデータ
- **作成日**: 2025-09-05
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 中
- **推定コード行数**: 200-300行（修正箇所）
- **対象モジュール**: core/src/compute/, core/src/math/, core/src/constants.rs

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 250行（修正）
- [x] 新規ファイル数: 0個（既存ファイル修正のみ）
- [x] 影響範囲: 複数モジュール（compute, math, constants）
- [x] PyO3バインディング: 不要（Rust層のみ）
- [x] SIMD最適化: 不要
- [x] 並列化: 不要

### 規模判定結果
**中規模タスク**

## 品質管理ツール（Rust）

### 適用ツール（規模に応じて自動選択）
| ツール | 小規模 | 中規模 | 大規模 | 実行コマンド |
|--------|--------|--------|--------|-------------|
| cargo test | - | ✅ | - | `cargo test --all --release` |
| cargo clippy | - | ✅ | - | `cargo clippy --all-targets --all-features -- -D warnings` |
| cargo fmt | - | ✅ | - | `cargo fmt --all -- --check` |
| detect_hardcode.sh | - | ✅ | - | `./scripts/detect_hardcode.sh` |
| pytest | - | ✅ | - | `uv run pytest tests/` |

## 修正対象（Critical Rules違反）

### 1. [C011-3] ハードコード違反: 29件

#### テスト値ハードコード（22件）
**対象ファイル**:
- core/src/compute/american.rs
- core/src/compute/arrow_native.rs  
- core/src/compute/black_scholes.rs
- core/src/compute/black76.rs
- core/src/compute/greeks.rs
- core/src/compute/merton.rs
- core/src/compute/traits.rs
- core/src/compute/american_adaptive.rs
- core/src/math/black_scholes_math.rs

**修正内容**:
```rust
// 現在（違反）
let rates = Float64Array::from(vec![0.05]);
let dividend_yields = Float64Array::from(vec![0.03]);
let r = 0.05;
let q = 0.03;

// 修正後
use crate::constants::{TEST_RATE, TEST_DIVIDEND_YIELD};
let rates = Float64Array::from(vec![TEST_RATE]);
let dividend_yields = Float64Array::from(vec![TEST_DIVIDEND_YIELD]);
let r = TEST_RATE;
let q = TEST_DIVIDEND_YIELD;
```

#### ローカルMIN_SIGMA定義（3件）
**対象ファイル**:
- core/src/compute/black_scholes.rs
- core/src/compute/black76.rs
- core/src/compute/merton.rs

**修正内容**:
```rust
// 現在（違反）
const MIN_SIGMA: f64 = 0.001;

// 修正後（ローカル定義を削除し、共通定数を使用）
use crate::constants::MIN_VOLATILITY;
// MIN_SIGMAへの参照をMIN_VOLATILITYに置換
```

#### その他の数値定数（4件）
**対象ファイル**:
- core/src/compute/american_adaptive.rs
- core/src/compute/arrow_native.rs

**修正内容**:
```rust
// 現在（違反）
assert_relative_eq!(result_array.value(0), 10.45058, epsilon = 0.00001);
assert!((factor - BAW_DAMPENING_FACTOR).abs() < 0.01);

// 修正後
use crate::constants::{NUMERICAL_TOLERANCE, PRACTICAL_TOLERANCE};
assert_relative_eq!(result_array.value(0), expected_value, epsilon = NUMERICAL_TOLERANCE);
assert!((factor - BAW_DAMPENING_FACTOR).abs() < PRACTICAL_TOLERANCE);
```

### 2. [C012] コード重複: 1件

**重複関数**: calculate_d1_d2
**対象ファイル**:
- core/src/compute/black_scholes.rs（削除）
- core/src/math/black_scholes_math.rs（維持）

**修正内容**:
```rust
// core/src/compute/black_scholes.rsから削除
// 代わりに共通実装を使用
use crate::math::black_scholes_math::calculate_d1_d2;
```

### 3. [C013] 命名規則違反: 2件

**対象ファイル**: core/src/compute/black_scholes.rs
**修正内容**:
```rust
// 現在（誤解を招く）
pub fn call_price_unsafe(...) 
pub fn put_price_unsafe(...)

// 修正後（明確な命名）
pub fn call_price_unchecked(...)
pub fn put_price_unchecked(...)
```

## 実装フェーズ

### Phase 1: 準備と調査（30分）
- [x] 既存定数の確認（constants.rs）
- [x] ハードコード箇所の特定
- [x] 影響範囲の確認

### Phase 2: 実装（2時間）

#### Step 1: テスト値のハードコード修正
- [ ] american.rs修正（TEST_RATE, TEST_DIVIDEND_YIELD使用）
- [ ] arrow_native.rs修正
- [ ] black_scholes.rs修正
- [ ] black76.rs修正
- [ ] greeks.rs修正
- [ ] merton.rs修正
- [ ] traits.rs修正
- [ ] american_adaptive.rs修正
- [ ] math/black_scholes_math.rs修正

#### Step 2: MIN_SIGMA統一
- [ ] black_scholes.rsのMIN_SIGMA削除、MIN_VOLATILITY使用
- [ ] black76.rsのMIN_SIGMA削除、MIN_VOLATILITY使用
- [ ] merton.rsのMIN_SIGMA削除、MIN_VOLATILITY使用

#### Step 3: calculate_d1_d2重複削除
- [ ] compute/black_scholes.rsの実装削除
- [ ] math実装への参照に置換

#### Step 4: unsafe関数名改名
- [ ] call_price_unsafe → call_price_unchecked
- [ ] put_price_unsafe → put_price_unchecked
- [ ] 関数呼び出し箇所の更新

### Phase 3: 品質チェック（1時間）
```bash
# Rust品質チェック
cargo fmt --all
cargo clippy --all-targets --all-features -- -D warnings
cargo test --lib --release

# ハードコード検出（0件になることを確認）
./scripts/detect_hardcode.sh

# Python統合テスト
uv run pytest tests/
```

### Phase 4: 検証（30分）
- [ ] すべてのテスト合格確認
- [ ] ベンチマーク実行（パフォーマンス劣化がないことを確認）
- [ ] ドキュメント更新（必要に応じて）

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "TEST_RATE"
    meaning: "テスト用無リスク金利"
    source: "constants.rs"
    value: "0.05"
  
  - name: "TEST_DIVIDEND_YIELD"
    meaning: "テスト用配当利回り"
    source: "constants.rs"
    value: "0.02"
  
  - name: "MIN_VOLATILITY"
    meaning: "最小ボラティリティ"
    source: "constants.rs"
    value: "0.001"
  
  - name: "NUMERICAL_TOLERANCE"
    meaning: "数値計算許容誤差"
    source: "constants.rs"
    value: "1e-7"
  
  - name: "PRACTICAL_TOLERANCE"
    meaning: "実用許容誤差"
    source: "constants.rs"
    value: "1e-3"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  # 新規命名なし（既存定数で対応可能）
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 技術要件

### 必須要件
- [x] Critical Rules C011-3準拠（ハードコード禁止）
- [x] Critical Rules C012準拠（DRY原則）
- [x] Critical Rules C013準拠（V2クラス禁止）
- [x] すべての既存テスト合格
- [x] パフォーマンス劣化なし

### パフォーマンス目標
- [x] 変更前後でベンチマーク結果に有意な差がないこと
- [x] コンパイル時定数の使用により実行時オーバーヘッドなし

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| テスト値変更による既存テスト失敗 | 低 | TEST_RATEは既に0.05と定義済み |
| 関数名変更によるAPI破壊 | 中 | 内部関数のため影響範囲限定的 |
| 定数参照によるコンパイル時間増加 | 低 | Rustの最適化により影響なし |

## チェックリスト

### 実装前
- [x] 既存コードの確認（ハードコード箇所特定）
- [x] constants.rsの定数確認
- [x] 影響範囲の特定

### 実装中
- [ ] 各ファイル修正後のコンパイル確認
- [ ] 段階的なテスト実行
- [ ] コミット前の`cargo fmt`

### 実装後
- [ ] cargo test --all --release 合格
- [ ] cargo clippy警告なし
- [ ] ./scripts/detect_hardcode.sh で検出0件
- [ ] uv run pytest tests/ 合格
- [ ] ベンチマーク結果の記録
- [ ] 計画のarchive移動

## 成果物

- [x] 修正コード（core/src/compute/配下）
- [x] 修正コード（core/src/math/配下）
- [ ] テスト合格（既存テストすべて）
- [ ] 品質チェック合格証明
- [ ] Critical Rules準拠証明

## 成功条件

1. **ハードコード完全排除**
   - `./scripts/detect_hardcode.sh`で違反0件
   - grep検索で0.05, 0.03等の直接記述なし

2. **コード重複解消**
   - calculate_d1_d2が1箇所のみ存在

3. **命名規則準拠**
   - unsafe関数名をuncheckedに改名

4. **品質基準達成**
   - 全テスト合格（554/554）
   - clippy警告0件
   - パフォーマンス劣化なし

## 備考

- このタスクはCritical Rules準拠の一環として最優先で実施
- 段階的実装は禁止、すべての修正を一度に実施
- 修正は機械的な置換が主体のため、リスクは低い
- TEST_DIVIDEND_YIELDは0.02と定義されているため、テストでの0.03使用箇所は要確認