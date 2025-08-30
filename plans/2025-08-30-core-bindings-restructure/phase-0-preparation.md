# Phase 0: 準備フェーズ

## 概要
Core + Bindingsアーキテクチャへの移行準備として、現状の完全な記録と設計ドキュメントを作成します。

## タスクリスト

### 1. 基盤整備とワークスペース設定 [1時間]

#### 1.1 ワークスペースとディレクトリ構造の初期設定
- [ ] ルートに `[workspace]` を定義した `Cargo.toml` を作成
- [ ] `core` および `bindings/python` の基本ディレクトリ作成
- [ ] 各ディレクトリに基本的な `Cargo.toml` と `pyproject.toml` 配置

**完了条件**: `cargo check --workspace` がエラーなく実行できる

#### 1.2 開発ブランチとCI/CDの準備
- [ ] `feature/core-bindings-restructure` ブランチを作成
- [ ] 新構造対応のCIワークフロー `.github/workflows/restructure_ci.yml` ドラフト作成
- [ ] ブランチプッシュ時のビルド・リンター実行を確認

**完了条件**: 開発ブランチへのプッシュでCIが起動する

### 2. アーキテクチャ設計 [3時間]

#### 2.1 要件定義書作成
- [ ] 機能要件の明文化
  - [ ] 各モデルのAPI仕様
  - [ ] バッチ処理要件
  - [ ] エラーハンドリング要件
- [ ] 非機能要件の定義
  - [ ] パフォーマンス基準
  - [ ] メモリ使用量制限
  - [ ] スレッド安全性要件

**成果物**: `docs/architecture/requirements.md`
**完了条件**: 全APIエンドポイントが文書化されている

#### 2.2 設計仕様書作成
- [ ] Core層インターフェース定義
  - [ ] トレイト設計
  - [ ] データ構造定義
  - [ ] エラー型定義
- [ ] Bindings層インターフェース定義
  - [ ] 型変換仕様
  - [ ] エラーマッピング
  - [ ] メモリ管理方針

**成果物**: `docs/architecture/design.md`
**完了条件**: Core/Bindings間の全インターフェースが定義されている

#### 2.3 移行計画詳細化
- [ ] 依存関係マップ作成
- [ ] 移行順序の決定
- [ ] ロールバック計画

**成果物**: `docs/architecture/migration-guide.md`
**完了条件**: 各フェーズの依存関係が明確で、ロールバック手順が文書化されている

### 3. ゴールデンマスター拡充 [3時間]

#### 3.1 現状API完全記録
```python
# 記録対象
- Black-Scholes: call_price, put_price, greeks, implied_volatility
- Black76: 同上
- Merton: 同上
- American: 同上
- バッチ処理: *_batch variants
- ArrayLike: broadcasting behavior
```

- [ ] 全API関数の入出力記録
- [ ] エッジケースの網羅（境界値、ゼロ、無限大）
- [ ] エラーケースの記録（不正入力、範囲外）
- [ ] APIカバレッジ測定

**実行コマンド**:
```bash
# 既存のゴールデンマスター生成
uv run pytest tests/golden/generate_golden_master.py --regenerate-golden

# 拡充版の作成
uv run python tests/golden/generate_comprehensive_suite.py
```

**成果物**: `tests/golden/comprehensive_suite.json`
**完了条件**: 主要な公開APIの95%以上がゴールデンマスターに含まれる

#### 3.2 パフォーマンスベースライン測定
- [ ] 単一計算のレイテンシ
- [ ] バッチ処理のスループット
- [ ] メモリ使用量プロファイル
- [ ] 並列処理の効率性

**実行コマンド**:
```bash
# Rustベンチマーク
cargo bench --all | tee benchmarks/baseline_rust.txt

# Pythonベンチマーク
python -m benchmarks.runners.comparison | tee benchmarks/baseline_python.txt
python -m benchmarks.runners.practical | tee benchmarks/baseline_practical.txt
```

**成果物**: 
- `benchmarks/baseline_rust.txt`
- `benchmarks/baseline_python.json`
- `benchmarks/performance_criteria.md`
**完了条件**: ベースラインデータが3回の測定平均値として保存され、バージョン管理されている

#### 3.3 統合テストスイート作成
- [ ] API契約テスト
- [ ] 互換性テスト
- [ ] 回帰テスト

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

- [ ] PyO3依存箇所のリスト化
- [ ] 分離難易度の評価
- [ ] 優先順位付け

**成果物**: `analysis/dependency_report.md`
**完了条件**: すべてのPyO3依存が特定され、分離難易度が3段階で評価されている

#### 4.2 コード構造分析
- [ ] モジュール依存グラフ作成
- [ ] 循環依存の検出
- [ ] 責任範囲の明確化

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

#### 5.2 CI/CD設定準備
- [ ] GitHub Actions ワークフロー更新案作成
- [ ] テストマトリックス定義
- [ ] ベンチマーク自動化設定

**成果物**: `.github/workflows/restructure_ci.yml.draft`
**完了条件**: ドラフトワークフローがyaml-lintを通過し、dry-runで動作確認済み

## 完了条件

### 必須チェックリスト
- [ ] 全設計ドキュメント作成完了
- [ ] ゴールデンマスター100%カバレッジ
- [ ] パフォーマンスベースライン記録
- [ ] 依存関係分析完了
- [ ] レビュー承認取得

### 品質ゲート
- [ ] ドキュメントの整合性確認
- [ ] テストスイートの実行成功
- [ ] ベンチマークの正常終了

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