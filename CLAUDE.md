# CLAUDE.md

QuantForge 高性能オプション価格計算ライブラリ（Rust + PyO3）の開発ガイド。

## ⚠️ アンチパターン警告（計画立案時・Plan Mode時は必須確認）

### 📋 計画立案チェックリスト

**新しい計画を立てる前に必ず確認**:
- [ ] パフォーマンス改善？ → SIMD提案は禁止
- [ ] 複雑な実装？ → 段階的実装は禁止  
- [ ] 最適化提案？ → プロファイリング結果はあるか
- [ ] Arrow統合？ → NumPy/PyList変換は禁止

### 🚫 絶対禁止リスト（計画に含めてはいけない）

1. **SIMD最適化** → @.claude/antipatterns/simd-optimization-trap.md
   - 2025-08-27に完全削除済み（210行のコード削除）
   - ❌ 禁句: 「AVX2」「ベクトル化」「SIMD」
   - ✅ 代替: 並列化閾値調整、キャッシュ最適化
   
2. **段階的実装** → @.claude/antipatterns/stage-implementation.md
   - C004/C014違反（理想実装ファースト）
   - ❌ 禁句: 「とりあえず」「後で改善」「Phase 1, 2, 3...」
   - ✅ 代替: 最初から理想実装のみ

3. **早すぎる最適化** → @.claude/antipatterns/premature-optimization.md
   - プロファイリング前の推測禁止
   - ❌ 禁句: 「おそらく遅い」「〜が原因と思われる」
   - ✅ 代替: 測定→分析→改善

4. **Arrow型変換** → @.claude/antipatterns/arrow-type-conversion-trap.md
   - Arrow Nativeと言いながらNumPy/PyList変換は矛盾
   - ❌ 禁句: 「to_numpy()」「to_pylist()」「互換性のため変換」
   - ✅ 代替: pyo3-arrow/arro3-coreで直接処理

**Plan Mode時の必須アクション**: 
1. 上記チェックリスト確認
2. 過去の失敗計画を参照: plans/archive/*cancelled*.md
3. アンチパターン詳細確認: @.claude/antipatterns/README.md

## 🚀 頻繁に使用するコマンド

### 品質チェック（毎回実行）

```bash
# Python品質
uv run ruff format .
uv run ruff check . --fix
uv run mypy .

# Rust品質
cargo fmt --all
cargo clippy --all-targets --all-features -- -D warnings
cargo test --lib --release

# 統合テスト
uv run maturin develop --release
uv run pytest tests/
```

### ビルド・リリース

```bash
# 開発用ビルド
uv sync --group dev
uv run maturin develop

# ドキュメント
uv run sphinx-build -M html docs/en/ docs/en/_build/ && uv run sphinx-build -M html docs/ja/ docs/ja/_build/
```

### ベンチマーク

@docs/ja/internal/benchmark_management_guide.md

## 🎯 プロジェクト原則

### 前提条件（破壊的変更推奨）

- 既存ユーザー: ゼロ → 後方互換性不要
- 技術的負債: ゼロ → 理想実装のみ
- 段階的実装: 禁止 → 完成形で実装

@.claude/development-principles.md  # 詳細な開発原則

### 絶対ルール

@.claude/critical-rules.xml を遵守。特に重要：

- C002: エラー迂回禁止 → 即座に修正
- C004: 理想実装ファースト → 技術的負債ゼロ
- C010: TDD 必須 → Red-Green-Refactor
- C011: ハードコード禁止 → 定数使用
- C012: DRY 原則 → コード重複禁止
- C013: V2 クラス禁止 → 既存を修正

### 技術的負債ゼロの実装方針

@.claude/development-principles.md

### 🔤 命名規則

@docs/ja/internal/naming_conventions.md  # 具体的な命名規則
@.claude/naming-protocol.md              # AIの命名プロトコル

## 📊 品質基準

### 必須メトリクス

| カテゴリ       | 基準             | 測定方法      |
| -------------- | ---------------- | ------------- |
| テスト         | 463/472 以上     | pytest        |
| パフォーマンス | 15M+ ops/sec     | ベンチマーク  |
| メモリ         | < 100MB/100 万件 | valgrind      |
| 精度           | エラー率 < 1e-3  | Golden Master |
| unsafe 使用    | 4 箇所以下       | cargo count   |
| unwrap 使用    | 本番コード 0     | grep 検索     |

### 品質ゲート

1. **コミット時**: フォーマット + 基本リント
2. **PR 時**: 全テスト + パフォーマンス
3. **リリース時**: クロスプラットフォーム + セキュリティ監査

## 🔧 プロジェクト構造

### コアディレクトリ

```
src/           # Rustコア実装
├── models/    # Black-Scholes, Black76, Merton, American
├── math/      # 数学関数（norm_cdf, norm_pdf）
├── traits/    # バッチ処理トレイト
└── error/     # エラーハンドリング

python/        # Pythonラッパー
tests/         # テストスイート（unit, integration, property）
playground/    # 実験用（Git管理外、品質チェック対象外）
examples/      # 公式サンプル（品質チェック必須）
```

### 依存関係

- Python 3.12+（abi3-py312）
- Rust stable（SIMD 最適化）
- PyO3 + maturin（バインディング）
- NumPy（配列処理）

## ⚡ パフォーマンス目標

- 単一計算: < 10ns
- 全 Greeks: < 50ns
- IV 計算: < 200ns
- 100 万件バッチ: < 20ms
- GIL リリース率: > 95%

## ⚠️ 重要な制約

### 禁止事項

- 妥協実装 - 「とりあえず動く」は作らない
- レガシーコード - \_old, \_v2 サフィックス禁止
- 段階的移行 - Python→Rust 移植などは行わない
- plans/archive/参照 - 過去の誤りを含むため禁止

### 必須事項

- ドキュメント駆動 - docs/api/が唯一の真実
- エラー即修正 - 迂回や後回しは禁止
- テスト先行 - 実装前にテストを書く
- 定数使用 - マジックナンバー禁止

## 📝 開発フロー

1. **実装前**

   - docs/api/で仕様確認
   - 既存コード調査（DRY 原則）
   - テスト作成（TDD）

2. **実装中**

   - 定数定義（ハードコード禁止）
   - エラー即修正（迂回禁止）
   - 品質チェック随時実行

3. **実装後**
   - 全品質チェック実行
   - パフォーマンス測定
   - ドキュメント更新

## 📁 ファイル配置管理原則 [C015適用]

### ディレクトリ用途の厳格な定義

| ディレクトリ | 用途 | 作成条件 | 品質要件 |
|------------|------|---------|---------|
| scripts/ | 本番運用スクリプト | 恒久的に使用 | 品質チェック必須 |
| playground/ | 実験・検証用 | 一時的な作業 | チェック不要（Git管理外） |
| .internal/ | 内部開発ツール | 開発支援用 | チェック不要（Git管理外） |
| プロジェクトルート | 設定・ドキュメント | **ユーザー承認必須** | - |

### ファイル作成判断フロー

```
新規ファイル作成が必要
    ↓
一時的な検証・実験？
    Yes → playground/ に作成（存在しない場合は先に作成）
    No ↓
内部開発ツール？
    Yes → .internal/ に作成
    No ↓
本番運用スクリプト？
    Yes → scripts/ に作成（品質チェック必須）
    No ↓
プロジェクト設定・ドキュメント？
    Yes → ユーザー承認を得てルートに作成
    No → 作成を中止して方針を確認
```

### 禁止パターン

- ❌ `test_xxx.py` をプロジェクトルートに作成
- ❌ `verify_xxx.py` をscripts/に作成（一時的検証の場合）
- ❌ `temp_xxx.py` `*_scratch.py` をplayground/以外に作成
- ❌ プロジェクトルートに無承認でディレクトリ作成
- ❌ scripts/に品質チェック未実施のファイル追加

### 推奨パターン

- ✅ 一時検証 → `playground/verify_xxx.py`
- ✅ 実験コード → `playground/experiment_xxx.py`
- ✅ 本番スクリプト → `scripts/xxx.sh`（品質チェック後）
- ✅ 内部ツール → `.internal/tools/xxx.py`
- ✅ 新規設定ファイル → ユーザー承認後にルートへ

### プロジェクトルート作成時の必須確認

プロジェクトルートに新規ファイル・ディレクトリを作成する場合：

1. **必ずユーザーに確認**：「プロジェクトルートに〇〇を作成してよろしいですか？」
2. **作成理由の説明**：なぜルートに必要か明確に説明
3. **代替案の提示**：他のディレクトリで代用可能か検討

詳細ルールは @.claude/critical-rules.xml 参照。
