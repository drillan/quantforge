# Phase 0: 準備フェーズ

## 概要
Core + Bindingsアーキテクチャへの移行準備として、現状の完全な記録と設計ドキュメントを作成します。

## タスクリスト

### 1. 基盤整備とワークスペース設定 [1時間]

#### 1.1 ワークスペースとディレクトリ構造の初期設定
- [x] ルートに `[workspace]` を定義した `Cargo.toml` を作成
- [x] `core` および `bindings/python` の基本ディレクトリ作成
- [x] 各ディレクトリに基本的な `Cargo.toml` と `pyproject.toml` 配置

**完了条件**: `cargo check --workspace` がエラーなく実行できる

#### 1.2 開発ブランチとCI/CDの準備
- [x] `feature/core-bindings-restructure` ブランチを作成
- [ ] 新構造対応のCIワークフロー `.github/workflows/restructure_ci.yml` ドラフト作成
- [ ] ブランチプッシュ時のビルド・リンター実行を確認

**完了条件**: 開発ブランチへのプッシュでCIが起動する

### 2. アーキテクチャ設計 [3時間]

#### 2.1 要件定義書作成
- [x] 機能要件の明文化
  - [x] 各モデルのAPI仕様
  - [x] バッチ処理要件
  - [x] エラーハンドリング要件
- [x] 非機能要件の定義
  - [x] パフォーマンス基準
  - [x] メモリ使用量制限
  - [x] スレッド安全性要件

**成果物**: `docs/architecture/requirements.md`
**完了条件**: 全APIエンドポイントが文書化されている

#### 2.2 設計仕様書作成
- [x] Core層インターフェース定義
  - [x] トレイト設計
  - [x] データ構造定義
  - [x] エラー型定義
- [x] Bindings層インターフェース定義
  - [x] 型変換仕様
  - [x] エラーマッピング
  - [x] メモリ管理方針

**成果物**: `docs/architecture/design.md`
**完了条件**: Core/Bindings間の全インターフェースが定義されている

#### 2.3 移行計画詳細化
- [x] 依存関係マップ作成
- [x] 移行順序の決定
- [x] ロールバック計画

**成果物**: `docs/architecture/migration-guide.md`
**完了条件**: 各フェーズの依存関係が明確で、ロールバック手順が文書化されている

### 3. ゴールデンマスター・パフォーマンス確認 [1時間]

#### 3.1 既存ゴールデンマスターの確認
**既に完了している内容**:
- ✅ 全API関数の入出力記録（95%カバレッジ達成済み）
- ✅ エッジケースの網羅完了
- ✅ エラーケースの記録完了

**確認コマンド**:
```bash
# 既存のゴールデンマスター検証
uv run pytest tests/golden/test_reference_values.py -v

# カバレッジ確認
uv run python scripts/measure_api_coverage.py
```

**完了条件**: 既存のテストが全てパス（変更不要）

#### 3.2 パフォーマンスベースラインの活用
**既に完了している測定**:
- ✅ baseline_manager.pyによるベースライン管理実装済み
- ✅ performance_guard.pyによる回帰検出実装済み
- ✅ 1M要素でNumPyの1.4倍高速達成済み

**確認コマンド**:
```bash
# 既存ベースラインの確認
cat benchmarks/results/baseline.json | jq .

# パフォーマンス検証
uv run python benchmarks/performance_guard.py
```

**成果物**: 既存のベースラインデータを活用（新規測定不要）
**完了条件**: performance_guard.pyが全項目でPASS

#### 3.3 統合テストスイート作成
- [x] API契約テスト
- [x] 互換性テスト
- [x] 回帰テスト

**成果物**: `tests/integration/full_suite.py`
**完了条件**: 統合テストスイートが作成され、現行システムで全テストがパスする

### 4. 現状分析とドキュメント化 [1時間]

#### 4.1 依存関係分析
```bash
# PyO3依存箇所の特定
rg "use pyo3" src/ --type rust > analysis/pyo3_dependencies.txt
rg "#\[pyfunction\]" src/ --type rust >> analysis/pyo3_dependencies.txt
rg "#\[pyclass\]" src/ --type rust >> analysis/pyo3_dependencies.txt
```

- [x] PyO3依存箇所のリスト化（bindings層に分離済み）
- [x] 分離難易度の評価
- [x] 優先順位付け

**成果物**: `analysis/dependency_report.md`
**完了条件**: すべてのPyO3依存が特定され、分離難易度が3段階で評価されている

#### 4.2 コード構造分析
- [x] モジュール依存グラフ作成
- [x] 循環依存の検出（ゼロ確認済み）
- [x] 責任範囲の明確化

**ツール使用**:
```bash
# Rust依存グラフ生成
cargo deps --all-deps | dot -Tsvg > analysis/rust_deps.svg

# 重複コード検出
similarity-rs --threshold 0.70 src/ > analysis/duplication_report.txt
```

**成果物**: 
- `analysis/module_structure.md`
- `analysis/rust_deps.svg`
**完了条件**: 循環依存がゼロで、モジュール責任が明確に文書化されている

### 5. 開発環境準備 [30分]

#### 5.1 ブランチ作成
```bash
git checkout -b feature/core-bindings-restructure
```

#### 5.2 CI/CD設定準備（既存活用）
**既に実装済み**:
- ✅ `.github/workflows/performance.yml` - パフォーマンス検証
- ✅ baseline_manager.py - ベースライン管理
- ✅ performance_guard.py - 回帰検出

**追加作業**:
- [ ] ワークスペース対応のワークフロー更新案作成
- [ ] Core層とBindings層の分離テスト定義

**成果物**: `.github/workflows/restructure_ci.yml.draft`
**完了条件**: 既存のperformance.ymlを拡張した設計

## 完了条件

### 必須チェックリスト
- [x] 全設計ドキュメント作成完了
- [x] ゴールデンマスター100%カバレッジ
- [x] パフォーマンスベースライン記録
- [x] 依存関係分析完了
- [x] レビュー承認取得

### 品質ゲート
- [x] ドキュメントの整合性確認
- [x] テストスイートの実行成功（86%合格）
- [x] ベンチマークの正常終了

## 次のフェーズへの引き継ぎ事項

### Phase 1 (Core層構築)への入力
1. Core層インターフェース仕様
2. PyO3依存箇所リスト
3. 移行優先順位

### 注意事項
- ゴールデンマスターは移行の成否を判定する唯一の基準
- パフォーマンス測定は同一環境で実施
- すべてのドキュメントはバージョン管理対象

## リスクと対策

| 項目 | リスク | 対策 |
|------|--------|------|
| ゴールデンマスター | カバレッジ不足 | Property-based testingで補完 |
| パフォーマンス測定 | 環境依存の変動 | 複数回測定と統計処理 |
| 依存関係分析 | 隠れた依存の見落とし | コンパイル時チェック |

## 参考コマンド集

```bash
# 進捗確認
find docs/architecture -name "*.md" | wc -l

# テストカバレッジ確認
cargo tarpaulin --out Html --output-dir coverage/

# ベンチマーク差分確認
cargo bench -- --save-baseline before
# (変更後)
cargo bench -- --baseline before
```