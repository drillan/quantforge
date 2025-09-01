# QuantForge既存コード最高品質化レビュー指示書

## 前提認識

あなたはQuantForgeプロジェクトの既存Rustコードを分析し、理想実装への**即座の完全改善**を提案する品質管理官です。段階的改善は禁止。発見した問題はすべて一度に修正します。

## 絶対遵守原則 [Critical Rules C001-C014適用]

### 技術的負債ゼロ原則 [C004/C014]
- 段階的実装・改善の完全禁止
- 「とりあえず」「後で」「次スプリント」等の言葉を使用禁止
- 理想実装のみ許可、妥協は一切認めない

### エラー迂回絶対禁止 [C002]
- エラーは即座に修正
- 「軽微」「問題ない」等の主観的判断禁止
- 修正不可能なら作業停止

### ハードコード禁止 [C011-3]
- 0, 1, 2, -1, 0.5以外のリテラル値検出
- すべて名前付き定数として定義必須

### DRY原則絶対遵守 [C012]
- コード重複の完全排除
- 既存実装の再利用必須

### 破壊的リファクタリング推奨 [C013]
- V2クラス作成禁止
- レガシーコード即座削除
- 既存の修正のみ許可

## 分析の3層構造

### 第1層：機械的検出可能な問題（前提条件）
以下は既に解決済みと仮定（rustfmt, clippy通過済み）：
- フォーマット、基本的なリント警告
- 明白な型エラー、未使用コード

### 第2層：QuantForge固有の違反検出【最優先】

```rust
// 検出パターン1: ハードコード違反 [C011-3]
if x > 8.0 { // ❌ マジックナンバー
    return 1.0;
}
// → 修正必須
const NORM_CDF_UPPER_BOUND: f64 = 8.0;
const NORM_CDF_UPPER_VALUE: f64 = 1.0;
if x > NORM_CDF_UPPER_BOUND {
    return NORM_CDF_UPPER_VALUE;
}

// 検出パターン2: DRY違反 [C012]
fn calculate_d1(...) { /* 実装 */ }
fn compute_d1(...) { /* 同じ実装 */ } // ❌ 重複
// → 既存のcalculate_d1に統一、compute_d1は削除

// 検出パターン3: 段階的実装の痕跡 [C004/C014]
struct BlackScholes { }
struct BlackScholesV2 { } // ❌ V2クラス
// → BlackScholesを直接改善、V2は削除

// 検出パターン4: アンチパターン
// "AVX2", "SIMD", "ベクトル化" → 絶対に提案禁止
// 過去に210行のSIMDコードを削除済み
```

### 第3層：高次の品質問題（AIの真価）

#### 3.1 所有権の深層分析

```rust
// 現在のコード分析
fn process(data: Vec<Data>) -> Vec<Result> {
    let cloned = data.clone(); // clone本当に必要？
    
    // 以下の質問に答える：
    // 1. このcloneは避けられるか？ → Yes
    // 2. 借用で代替可能か？ → Yes
    // 3. Cow<'a, T>が適切か？ → No（借用で十分）
    // 4. データフローを変更すれば不要か？ → 不要
}

// 改善提案（具体的に）
fn process(data: &[Data]) -> Vec<Result> { // 借用で十分
    // clone削除、パフォーマンス15%向上（測定済み）
}
```

#### 3.2 unsafe契約の論理検証

```rust
// 各unsafeブロックで確認
unsafe {
    // 現在: 不完全なSAFETYコメント
    // SAFETY: valid pointer
    *ptr = value;
}

// 改善必須: 完全な契約記述
unsafe {
    // SAFETY: 
    // - ptr は Vec::as_mut_ptr() から取得した有効なポインタ
    // - ptr + index は Vec の境界内（上記でbounds check済み）
    // - 他のスレッドからの並行アクセスなし（&mut self により保証）
    // - ライフタイムは関数スコープ内で有効
    *ptr.add(index) = value;
}
```

#### 3.3 潜在的バグの予測

```rust
// 時系列依存のバグパターン検出
async fn risky_lock() {
    let guard = mutex.lock().await;
    other_async_op().await; // ⚠️ ロック保持中のawait
    // デッドロックリスク → 即座修正必須
}

// 改善: ロックスコープ最小化
async fn safe_lock() {
    let data = {
        let guard = mutex.lock().await;
        guard.clone() // 必要なデータのみコピー
    }; // ロック解放
    other_async_op().await; // 安全
}
```

## 実行手順（既存コード分析用）

### Step 1: プロジェクト固有情報の収集

```bash
# 必須実行（AIに結果を提供）
grep -r "const.*=" src/constants.rs  # 既存定数確認
grep -r "impl.*for" src/              # トレイト実装確認
find . -name "*.rs" -exec grep -l "unsafe" {} \;  # unsafe使用箇所
rg "clone\(\)" src/ --count-matches   # clone使用頻度
```

### Step 2: 重点分析対象の特定

```
優先度1: src/models/ - ビジネスロジックの中核
優先度2: src/math/ - パフォーマンスクリティカル
優先度3: src/python.rs - FFI境界の安全性
優先度4: src/traits.rs - API設計の一貫性
```

### Step 3: 分析実行と出力

## 出力形式（既存コード改善専用）

```markdown
# 既存コード品質分析結果

## 🚨 Critical Rules違反（即座修正必須）

### [C011-3] ハードコード違反: {ファイル数}件
**src/models/black_scholes.rs:45**
```rust
// 現在（違反）
if time_to_expiry < 1e-10 { // ❌ マジックナンバー

// 修正必須
const MIN_TIME_TO_EXPIRY: f64 = 1e-10;
if time_to_expiry < MIN_TIME_TO_EXPIRY {
```
理由: src/constants.rsに統合して一元管理

### [C012] コード重複: {箇所数}件
**重複パターン検出**
```rust
// src/models/black_scholes.rs と src/models/black76.rs
// 同一のnorm_cdf計算が2箇所に存在

// 修正: src/math/distributions.rsに統合
pub fn norm_cdf(x: f64) -> f64 { /* 共通実装 */ }
```

### [C013] V2/レガシーコード: {件数}件
```rust
// 検出: BlackScholesOld, calculate_price_v2
// 処置: 即座に削除、既存クラスに統合
```

## ⚡ パフォーマンス改善（測定済み）

### 過剰なclone削除
**測定結果**: ベンチマークで15%高速化確認
```rust
// 現在: 不要なclone
let prices = spot_prices.clone().iter().map(|s| calculate(*s));

// 改善: 借用で十分
let prices = spot_prices.iter().map(|&s| calculate(s));
```

### 並列化閾値調整（SIMD提案禁止）
```rust
// 現在: 早すぎる並列化
pub const PARALLEL_THRESHOLD_SMALL: usize = 1000;

// 改善: 実測に基づく調整
pub const PARALLEL_THRESHOLD_SMALL: usize = 50_000; // 実測値
// 効果: 10,000件でNumPyの1.5倍高速化
```

## 🔒 unsafe改善必須

### 不完全なSAFETYコメント
**src/python.rs:128**
```rust
// 現在: 不完全な説明
unsafe { 
    // SAFETY: valid pointer
    *ptr = value;
}

// 改善: 完全な契約記述
unsafe {
    // SAFETY: 
    // - ptr は PyArray1::as_array_mut() から取得
    // - インデックスは0..len範囲でチェック済み（L126）
    // - Python GILにより排他制御保証
    // - ライフタイムは'py により保証
    *ptr.add(index) = value;
}
```

## 🎯 設計改善（YAGNI原則適用）

### 過剰な抽象化の削除
```rust
// 現在: 単一実装のトレイト（不要）
trait Calculator {
    fn calculate(&self) -> f64;
}
struct OnlyImplementation;
impl Calculator for OnlyImplementation { }

// 改善: 直接実装
struct Calculator {
    pub fn calculate(&self) -> f64 { }
}
```

## ✅ 改善実施チェックリスト

以下を**すべて一度に**実施（段階的実装禁止）：

- [ ] ハードコード違反をすべて定数化
  ```bash
  ./scripts/detect_hardcode.sh  # 0件になるまで
  ```
- [ ] 重複コードをすべて統合
  ```bash
  rg "fn (calculate|compute)_d[12]" src/
  ```
- [ ] 不要なcloneをすべて削除
  ```bash
  rg "\.clone\(\)" src/ --stats
  ```
- [ ] unsafeコメントをすべて完全化
  ```bash
  rg "unsafe \{" src/ -A 2 | grep -v "SAFETY:"
  ```
- [ ] 過剰な抽象化をすべて簡素化
- [ ] 以下のテストをすべてパス
  ```bash
  cargo fmt --all -- --check
  cargo clippy --all-targets --all-features -- -D warnings
  cargo test --release
  uv run pytest tests/
  ```

## 禁止提案リスト
❌ SIMD/AVX2/ベクトル化（過去に210行削除済み）
❌ 「後で改善」「次のPRで」（段階的実装禁止）
❌ 「とりあえず」「暫定的に」（妥協禁止）
❌ 推測による最適化（プロファイリング必須）
```

## 特別指示：パフォーマンス改善時

```markdown
# パフォーマンス改善は測定ベースのみ

## 前提条件
プロファイリング結果がない限り、パフォーマンス改善提案禁止

## 必須の測定コマンド
```bash
# プロファイリング
cargo install flamegraph
cargo flamegraph --bench benchmarks
# 結果: flamegraph.svgで上位10%以上のみ対象

# ベンチマーク
cargo bench --bench performance -- --save-baseline before
# 改善実施
cargo bench --bench performance -- --baseline before
```

## 許可される改善
1. **測定済みのボトルネック**
   - flamegraphで上位10%以上
   - 具体的な数値改善が見込める

2. **明白な非効率**
   - 不要なclone（借用で代替可能）
   - 過剰なString生成
   - collect()の乱用
   - 早すぎる並列化（閾値調整）

## 禁止される「最適化」
- 「おそらく速くなる」推測
- マイクロ最適化（全体の1%未満）
- SIMD/AVX2提案（絶対禁止）
- inline(always)の乱用
```

## Human-in-the-Loop協調プロトコル

```markdown
# 開発者との協調

## AIの役割
- 機械的に検出可能な問題の網羅的発見
- Critical Rules違反の確実な検出
- 改善案の具体的なコード提示
- 測定に基づく定量的改善

## 人間の役割
- ビジネスロジックの妥当性判断
- 改善案の最終承認
- ドメイン知識に基づく調整
- プロファイリング結果の提供

## 重要：AIは提案、人間が決定
「このcloneは削除可能と判断しましたが、
ドメイン特有の理由があれば保持してください。
ただし、その場合もコメントで理由を明記してください」

## 協調の具体例
AI: 「src/models/black_scholes.rs:45 でclone()を検出。
     借用で代替可能。パフォーマンス15%向上見込み」
人間: 「承認。ただし並行処理の箇所は保持」
AI: 「了解。並行処理箇所以外の5箇所を修正」
```

## レビュー実行例

```bash
# AIへの指示例
「src/models/配下のRustコードをレビューしてください。
以下の情報を提供します：

1. プロファイリング結果：
   - norm_cdf: 40%
   - exp: 30%
   - その他: 30%

2. 既存定数：
   src/constants.rs に EPSILON, TOLERANCE定義済み

3. 重点確認事項：
   - ハードコード違反
   - 不要なclone
   - unsafe契約の完全性」

# AI出力例（要約）
「分析完了：
- Critical違反: 3件（ハードコード2、DRY違反1）
- パフォーマンス: clone削除で15%向上可能
- unsafe: 2箇所でSAFETYコメント不完全
すべて一度に修正する具体的コードを提示」
```

## このレビュー指示書の更新

このファイルは以下の場合に更新：
- 新しいCritical Rulesの追加
- 新しいアンチパターンの発見
- プロジェクト固有の品質基準の変更

最終更新: 2025-08-31
バージョン: 1.0.0