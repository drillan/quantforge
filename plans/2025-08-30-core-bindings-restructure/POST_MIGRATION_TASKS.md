# Core+Bindings移行後の残タスク計画

## 概要
Core+Bindingsアーキテクチャへの移行は完了しましたが、既存テストの移行、品質改善、CI/CD更新などの残タスクがあります。
このドキュメントは、移行後に必要な全タスクを優先順位付きで整理したものです。

## 現状分析

### 完了済み作業
- ✅ Core層構築（純粋Rust実装）
- ✅ Bindings層構築（PyO3ラッパー）
- ✅ Python パッケージ構造（quantforge.black_scholes等）
- ✅ 基本動作確認（Black-Scholes, Merton計算成功）
- ✅ Greeks API統一（Dict形式に統一）
- ✅ ビルドシステム修復（pyproject.toml設定）

### 発見した問題

#### 1. テスト移行（✅ 部分完了）
- **問題**: 472個のテストが旧API（`quantforge.models`）を使用 → **86%解決済み**
- **影響**: 新構造でのテスト実行不可 → **422テスト中362合格**
- **例**: `test_models_api.py`が`models.call_price()`を呼び出し → **修正済み**

#### 2. コード品質警告
- **Rust警告**:
  - 未使用import: `PyArrayMethods`（converters/array.rs:3）
  - 未使用関数: `quantforge_error_to_pyerr`（converters/mod.rs:16）
  - format!文字列の非効率的使用（error.rs:55）
- **Python警告**: 未確認（ruff/mypy未実行）

#### 3. CI/CD設定未更新
- **問題**: GitHub ActionsがワークスペースビルドNK認識
- **影響**: PR/Push時の自動テスト失敗

#### 4. ディレクトリ整理（✅ 部分完了）
- `Cargo.toml.old`: ✅ 削除済み
- `bindings/python/quantforge/`: 不要ディレクトリ
- `analysis/`: ✅ 削除済み

## タスク一覧（優先順位順）

### Phase 1: テスト移行と品質修正【最優先】

#### 1.1 Pythonテスト移行（推定: 2時間）

**対象ファイル**:
```
tests/test_models_api.py
tests/test_models_api_refactored.py
tests/test_batch_processing.py
tests/test_batch_refactored.py
tests/test_greeks.py
tests/test_greeks_refactored.py
tests/test_golden_master.py
```

**必要な変更**:
```python
# 旧API
from quantforge import models
price = models.call_price(100, 100, 1, 0.05, 0.2)

# 新API
from quantforge import black_scholes
price = black_scholes.call_price(100, 100, 1, 0.05, 0.2)
```

**テスト戦略**:
1. conftest.pyの更新（import調整）
2. 各テストファイルのimport文更新
3. API呼び出しの置換（models → 各モデルモジュール）
4. pytest実行での全テスト合格確認

#### 1.2 Rust品質修正（推定: 1時間）

**必須修正**:
```rust
// converters/array.rs
- use numpy::{PyArrayMethods, PyReadonlyArray1};
+ use numpy::PyReadonlyArray1;

// converters/mod.rs
// 未使用関数の削除または#[allow(dead_code)]追加

// error.rs:55
- format!("{}", msg)
+ format!("{msg}")
```

**実行コマンド**:
```bash
cargo fmt --all
cargo clippy --all-targets --all-features -- -D warnings
cargo test --release
```

#### 1.3 Python品質修正（推定: 30分）

**実行コマンド**:
```bash
uv run ruff format .
uv run ruff check . --fix
uv run mypy .
```

### Phase 2: ディレクトリ整理【中優先】

#### 2.1 不要ファイル削除（推定: 30分）

**削除対象**:
- `Cargo.toml.old` ✅ 削除済み
- `bindings/python/quantforge/`（空ディレクトリ）
- `analysis/`（一時ファイル）✅ 削除済み

**保持対象**:
- `benchmarks/`（移行後も使用）
- `tests/`（移行後に更新）
- `docs/`（API仕様）

#### 2.2 ベンチマーク整理（推定: 1時間）

**確認事項**:
- 新構造でのベンチマーク動作確認
- performance_guard.pyの閾値調整
- baseline更新（必要に応じて）

### Phase 3: CI/CD更新【低優先】

#### 3.1 GitHub Actions更新（推定: 1時間）

**CI.yml更新箇所**:
```yaml
# ワークスペースビルド対応
- name: Build workspace
  run: cargo build --workspace --release

# Python import テスト更新
- run: |
    python -c "from quantforge import black_scholes, black76, merton"
    python -c "black_scholes.call_price(100, 100, 1, 0.05, 0.2)"
```

#### 3.2 リリース準備（推定: 30分）

**更新対象**:
- `pyproject.toml`: バージョン統一（0.1.0）
- `CHANGELOG.md`: Core+Bindings移行エントリ追加
- `README.md`: 新構造の説明追加

## 実施方針

### Critical Rules遵守
- **C002**: エラー即修正（迂回禁止）
- **C004**: 理想実装ファースト（段階的実装禁止）
- **C010**: TDD（テスト先行）
- **C011**: ハードコード禁止
- **C012**: DRY原則
- **C013**: V2クラス禁止

### 品質ゲート
各フェーズ完了時に必須:
```bash
# Rust
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --workspace --release

# Python
uv run ruff format . --check
uv run ruff check .
uv run mypy .
uv run pytest tests/
```

### 実装順序
1. テスト移行を最優先（開発の基盤）
2. 品質修正で警告ゼロ達成
3. ディレクトリ整理で構造明確化
4. CI/CD更新で自動化完成

## 予想所要時間

| Phase | タスク | 所要時間 |
|-------|--------|----------|
| 1 | テスト移行と品質修正 | 3.5時間 |
| 2 | ディレクトリ整理 | 1.5時間 |
| 3 | CI/CD更新 | 1.5時間 |
| **合計** | | **6.5時間** |

## 成功基準

- [ ] 全472テストが新APIで合格（現在86%達成）
- [ ] Rust/Python警告ゼロ（Rust: 58警告、Python: 134エラー残存）
- [ ] CI/CDパイプライン正常動作
- [x] 不要ファイル完全削除（Cargo.toml.old, analysis/削除済み）
- [ ] ドキュメント更新完了

## リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| テスト移行で予期しない破壊的変更発見 | 高 | 段階的実行とgit管理 |
| パフォーマンス劣化 | 中 | performance_guard.pyで継続監視 |
| CI設定ミス | 低 | ローカルで完全テスト後にpush |

## 次のアクション

1. このドキュメントのレビューと承認
2. Phase 1から順次実施
3. 各Phase完了時に進捗報告
4. 全Phase完了後に最終検証

---

作成日: 2025-08-31
作成者: QuantForge Development Team
状態: 計画済み（実施待ち）