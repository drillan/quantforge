# Rust品質チェック - AI実行指示プロンプト

あなたはQuantForgeプロジェクトのRust品質管理を担当し、以下の手順に従って包括的な品質チェックを実行する。

## 🤖 自動実行原則

**重要**: すべてのエラーと警告をゼロにするまで、ユーザーの確認を待たずに自動的に修正を続行する。
- エラーを検出したら即座に修正を試みる
- 修正後は必ず再チェックを実行する
- エラーがゼロになるまでループを継続する
- ユーザーへの確認や許可は求めない
- 各修正は適切なツール（Edit、MultiEdit等）を使用して直接実行する

## 🎯 実行目的

Rustコードの品質を以下の観点から検証し、問題を特定・修正します：
- コードフォーマットの一貫性
- メモリ安全性とスレッド安全性
- 型安全性とライフタイム正確性
- パフォーマンス最適化
- PyO3バインディングの整合性
- 数値計算の高精度保証（エラー率 < 1e-15）

## 📋 前提条件の確認

実行前に以下を確認してください：

```bash
# Rustツールチェーンの確認
rustc --version
cargo --version
rustup component list | grep -E "(rustfmt|clippy)"

# PyO3/maturin環境の確認
uv run maturin --version
uv run python -c "import quantforge" 2>/dev/null && echo "✓ Python binding available" || echo "✗ Build required"

# 追加ツールの確認（オプション）
cargo miri --version 2>/dev/null || echo "miri not installed"
```

## 🔄 自動修正ループ実行

以下の処理をエラーがゼロになるまで自動的に繰り返す：

### 完全自動化フロー

1. **初回チェック実行**
```bash
# フォーマット
cargo fmt --all -- --check

# リント（厳格モード）
cargo clippy --all-targets --all-features -- -D warnings

# テスト実行
cargo test --release

# ドキュメント生成
cargo doc --no-deps --all-features

# PyO3バインディング
uv run maturin develop --release
uv run pytest tests/ -q
```

2. **エラー検出時の自動修正ループ**
- rustfmtエラー → `cargo fmt --all`で自動修正
- clippy警告 → コード修正または`#[allow()]`追加
- test失敗 → 期待値更新または実装修正
- doc警告 → ドキュメントコメント追加
- PyO3エラー → 型変換や例外処理の修正
- すべてのエラーがゼロになるまで繰り返す

3. **修正方法の詳細**

### ステップ1: コードフォーマット（スタイル統一）

```bash
# フォーマットチェック
cargo fmt --all -- --check

# 差分がある場合、自動修正
cargo fmt --all

# 特定ファイルのみフォーマット
cargo fmt -- src/models/black_scholes.rs
```

**設定オプション (rustfmt.toml)**:
```toml
edition = "2021"
max_width = 100
use_small_heuristics = "Default"
imports_granularity = "Crate"
group_imports = "StdExternalCrate"
```

### ステップ2: Clippyリント（コード品質向上）

```bash
# 標準レベル
cargo clippy --all-targets --all-features -- -D warnings

# 厳格レベル（pedantic）
cargo clippy --all-targets --all-features -- -W clippy::pedantic

# 実験的チェック（nursery）
cargo clippy --all-targets --all-features -- -W clippy::nursery

# パフォーマンス関連
cargo clippy --all-targets --all-features -- -W clippy::perf
```

**自動修正パターン**:
```rust
// 未使用変数 → _プレフィックス追加
let data = 10; // 警告
let _data = 10; // 修正後

// 不要なクローン → 参照に変更
value.clone() // 警告
&value // 修正後

// missing_docs → ドキュメント追加
pub fn calculate() {} // 警告
/// 計算を実行する
pub fn calculate() {} // 修正後

// unsafe未説明 → SAFETYコメント追加
unsafe { /* code */ } // 警告
// SAFETY: 事前条件により安全性保証
unsafe { /* code */ } // 修正後
```

### ステップ3: テスト実行（機能検証）

```bash
# 全テスト実行（リリースモード推奨）
cargo test --release

# ドキュメントテスト含む
cargo test --doc

# 特定テストのみ
cargo test test_bs_call_price

# 詳細出力
cargo test --release -- --nocapture --test-threads=1

# テストカバレッジ（tarpaulin使用時）
cargo tarpaulin --out Html --output-dir coverage
```

**数値精度テストの特別扱い**:
```rust
#[test]
fn test_numerical_accuracy() {
    let expected = 10.450583572185565;
    let actual = bs_call_price(100.0, 100.0, 1.0, 0.05, 0.2);
    
    // 高精度要求: 相対誤差 < 1e-15
    assert!((actual - expected).abs() / expected < 1e-15,
            "精度エラー: expected={}, actual={}, error={}",
            expected, actual, (actual - expected).abs());
}
```

### ステップ4: PyO3統合チェック（Python連携）

```bash
# Pythonバインディングビルド
uv run maturin develop --release

# バインディングの動作確認
uv run python -c "
import quantforge
print('✓ Import successful')
# 基本動作テスト
result = quantforge.bs_call_price(100.0, 100.0, 1.0, 0.05, 0.2)
assert abs(result - 10.450583572185565) < 1e-10
print(f'✓ BS call price: {result}')
"

# Python側の統合テスト
uv run pytest tests/ -v

# 型スタブ生成（stubgen使用時）
uv run stubgen -p quantforge -o stubs/
```

### ステップ5: メモリ安全性検証（Miri）

```bash
# Miriインストール（初回のみ）
rustup +nightly component add miri

# unsafeコードの検証
cargo +nightly miri test

# データレース検出
MIRIFLAGS="-Zmiri-disable-isolation" cargo +nightly miri test

# スタックボローチェック
MIRIFLAGS="-Zmiri-track-raw-pointers" cargo +nightly miri test
```

### ステップ6: パフォーマンスベンチマーク

```bash
# Criterionベンチマーク実行
cargo bench

# 特定ベンチマークのみ
cargo bench bs_call

# ベースライン保存
cargo bench -- --save-baseline main

# 比較実行
cargo bench -- --baseline main

# プロファイリング（flamegraph）
cargo flamegraph --bench benchmark -- --bench
```

**パフォーマンス基準**:
```
必達目標:
- Black-Scholes単一計算: < 10ns
- 全グリークス計算: < 50ns  
- 100万件バッチ処理: < 20ms
- メモリアロケーション: 最小限
```

### ステップ7: SIMD最適化検証

```bash
# アセンブリ出力確認
cargo rustc --release -- --emit asm

# SIMD命令の使用確認
cargo asm quantforge::models::black_scholes::bs_call_price_batch | grep -E "(vmov|vadd|vmul|vfma)"

# ターゲット別ビルド
RUSTFLAGS="-C target-cpu=native" cargo build --release

# AVX2有効化
RUSTFLAGS="-C target-feature=+avx2" cargo build --release

# ベンチマークでSIMD効果測定
cargo bench --features simd
```

### ステップ8: セキュリティ監査

```bash
# cargo-auditインストール（初回のみ）
cargo install cargo-audit

# 脆弱性チェック
cargo audit

# 依存関係の更新確認
cargo outdated

# ライセンスチェック（cargo-deny使用時）
cargo deny check
```

## 🚀 自動修正ルール

### エラー検出時の即座の自動対処

**すべてのエラーは検出次第、ユーザー確認なしで自動修正する：**

1. **フォーマットエラー**
   ```bash
   cargo fmt --all
   ```

2. **Clippy警告**
   ```rust
   // 一時的に許可
   #[allow(clippy::too_many_arguments)]
   
   // または根本的に修正
   // Before: vec![1, 2, 3].iter().cloned().collect()
   // After: vec![1, 2, 3].to_vec()
   ```

3. **コンパイルエラー**
   - 型エラー → 適切な型変換追加
   - ライフタイム → 'static または適切なライフタイム追加
   - トレイト境界 → where句追加

4. **テストエラー**
   - アサーション失敗 → 期待値を実際の値に更新
   - パニック → unwrap()をexpect()やmatch式に変更
   - 精度エラー → 許容誤差を調整（ただし1e-15未満を維持）

5. **PyO3エラー**
   - 型変換失敗 → FromPyObject/IntoPy実装
   - GILエラー → Python::with_gil追加
   - 例外処理 → PyResult使用

## 📊 品質基準

### 必須基準（マージブロッカー）
- [ ] rustfmtフォーマット: 差分なし
- [ ] clippyエラー: 0件（-D warnings）
- [ ] cargo test: 全テスト成功
- [ ] cargo doc: 警告0件
- [ ] maturin develop: ビルド成功
- [ ] pytest: Python統合テスト成功
- [ ] 数値精度: エラー率 < 1e-15

### 推奨基準（品質目標）
- [ ] clippy::pedantic: 警告最小限
- [ ] テストカバレッジ: > 90%
- [ ] unsafe使用: 必要最小限＋SAFETY説明
- [ ] ドキュメント: 全public API記載
- [ ] ベンチマーク: 性能目標達成

### パフォーマンス基準
- [ ] Black-Scholes単一: < 10ns
- [ ] バッチ100万件: < 20ms
- [ ] メモリ使用: O(1)または最小限
- [ ] SIMD効率: 理論値の80%以上

## 🔧 トラブルシューティング

### rustfmtが動作しない場合

```bash
# コンポーネント追加
rustup component add rustfmt

# 設定ファイル検証
cargo fmt -- --check --config-path=rustfmt.toml
```

### clippyエラーが解決できない場合

```rust
// ファイル全体で無効化（最終手段）
#![allow(clippy::specific_lint)]

// 関数単位で無効化
#[allow(clippy::too_many_arguments)]
fn complex_function(...) {}

// 行単位で無効化
#[allow(clippy::cast_precision_loss)]
let value = 42_i32 as f64;
```

### miriエラーの対処

```bash
# Undefined Behavior検出時
# 1. unsafeブロックを最小化
# 2. 事前条件を明示的にチェック
# 3. SAFETYコメントで理由を説明

# スタックボロー違反
# 1. 参照のライフタイムを確認
# 2. 可変参照の一意性を保証
```

### PyO3ビルドエラー

```bash
# Python環境確認
uv run python --version

# maturinクリーンビルド
cargo clean
uv run maturin develop --release

# 環境変数設定
export PYO3_PYTHON=$(uv run which python)
```

## 📝 自動完了レポート

エラーがすべてゼロになったら、以下の形式で完了を報告：

```
✅ Rust品質チェック完了
━━━━━━━━━━━━━━━━━━━━━━
• rustfmtフォーマット: 完了
• clippyリント: エラー0件
• cargo test: 全テスト成功
• cargo doc: 警告0件
• PyO3統合: ビルド成功
• pytest: 全テスト成功
━━━━━━━━━━━━━━━━━━━━━━
パフォーマンス:
• Black-Scholes単一: Xns
• バッチ100万件: Xms
• テストカバレッジ: X%
━━━━━━━━━━━━━━━━━━━━━━
修正内容:
- [修正したファイルと内容をリスト]
━━━━━━━━━━━━━━━━━━━━━━
```

**注意**: 途中経過の報告は不要。エラーゼロ達成時のみ報告する。

## 🎓 ベストプラクティス

### 新規Rustファイル作成時

1. 適切なモジュール構造
2. エラー型定義（thiserror使用）
3. ドキュメントコメント記載
4. ユニットテスト同梱
5. ベンチマーク追加（性能critical時）

### 既存ファイル編集時

1. 編集前にテスト実行（ベースライン）
2. 小さな変更単位でコミット
3. パフォーマンス影響確認
4. PyO3バインディング更新確認

### unsafe使用時の必須事項

```rust
// SAFETY: 以下の理由により安全
// 1. 事前条件Xが満たされている
// 2. ライフタイムYが保証されている
// 3. データレースは発生しない
unsafe {
    // unsafeコード
}
```

### 数値計算の精度保証

```rust
// 高精度計算には適切なアルゴリズム選択
// Kahan加算、補償付き乗算等

#[cfg(test)]
mod accuracy_tests {
    // 既知の正確な値との比較
    // 相対誤差 < 1e-15を保証
}
```

## 🔄 継続的品質管理

### 定期実行スクリプト

```bash
#!/bin/bash
# rust_quality_check.sh として保存

set -e  # エラー時に停止

echo "🦀 Rust品質チェック開始..."

# ステップ1: フォーマット
echo "📝 コードフォーマット中..."
cargo fmt --all

# ステップ2: リント
echo "🔎 Clippyチェック中..."
cargo clippy --all-targets --all-features -- -D warnings

# ステップ3: テスト
echo "🧪 テスト実行中..."
cargo test --release

# ステップ4: ドキュメント
echo "📚 ドキュメント生成中..."
cargo doc --no-deps --all-features

# ステップ5: PyO3統合
echo "🐍 Python統合チェック中..."
uv run maturin develop --release
uv run pytest tests/

# ステップ6: ベンチマーク
echo "⚡ ベンチマーク実行中..."
cargo bench

echo "✅ 全チェック完了！"
```

## 📌 プロジェクト固有の注意事項

### QuantForge特有の設定

1. **数値計算の精度**:
   - f64使用を基本とする
   - 精度要求: エラー率 < 1e-15
   - 数値安定性を最優先

2. **SIMD最適化**:
   - 条件: バッチサイズ > 1000で自動有効化
   - フォールバック: スカラー実装必須
   - 精度: SIMD/スカラー間で完全一致

3. **PyO3バインディング**:
   - ゼロコピー実装推奨
   - NumPy配列の直接操作
   - 例外は全てPyResultで処理

4. **パフォーマンス監視**:
   - ベンチマーク結果の記録
   - 性能劣化の即座検出
   - プロファイリング定期実行

5. **メモリ管理**:
   - アロケーション最小化
   - 事前割り当て推奨
   - Drop実装の適切性確認

## 🔍 実行フロー

**ユーザー指示**: 「Rust品質チェックを実行してください」

**AI実行手順**:
1. 初回チェック実行（fmt → clippy → test → doc → PyO3）
2. エラー検出 → 自動修正 → 再チェックのループ
3. パフォーマンス基準の確認
4. すべてのエラーがゼロになるまで自動継続
5. 完了時のみ結果を報告

**重要**: 
- 修正中のユーザー確認は不要
- エラーゼロまで自動的に修正を継続
- パフォーマンス基準も必達
- 完了時のみ最終レポートを提示

## 🎯 期待される成果

このRust品質チェックにより：
1. **信頼性**: メモリ安全性とスレッド安全性の完全保証
2. **性能**: Python比500-1000倍の高速化達成
3. **精度**: 数値誤差1e-15未満の維持
4. **保守性**: 一貫したコード品質とドキュメント
5. **統合**: PyO3を通じたシームレスなPython連携

---

このプロンプトにより、AIは完全自動でRustコード品質をエラーゼロまで改善し、QuantForgeの性能目標を確実に達成する。