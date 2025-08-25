# [Python] [タイトル] 実装計画

## メタデータ
- **作成日**: YYYY-MM-DD
- **言語**: Python
- **ステータス**: DRAFT
- **推定規模**: [小/中/大]
- **推定コード行数**: [数値]
- **対象モジュール**: [quantforge/, tests/, examples/ など]

## ⚠️ 技術的負債ゼロの原則

**重要**: このプロジェクトでは技術的負債を一切作らないことを最優先とします。

### 禁止事項（アンチパターン）
❌ **段階的実装・TODO残し**
```python
# 絶対にダメな例
def compute(data):
    # TODO: 後で最適化する
    result = []
    for item in data:  # 後でベクトル化
        result.append(item * 2)
    return result
```

❌ **複数バージョンの共存**
```python
# 絶対にダメな例
def algorithm_v1():  # 旧実装を残す
    pass
def algorithm_v2():  # 新実装を追加
    pass
```

✅ **正しいアプローチ：最初から完全実装**
```python
# 最初から最適化された完全な実装
import numpy as np
from numpy.typing import NDArray

def compute(data: NDArray[np.float64]) -> NDArray[np.float64]:
    """完全に最適化された実装."""
    return np.asarray(data, dtype=np.float64) * 2
```

## タスク規模判定

### 判定基準
- [ ] 推定コード行数: _____ 行
- [ ] 新規ファイル数: _____ 個
- [ ] 影響範囲: [単一モジュール/複数モジュール/全体]
- [ ] Rust連携: [必要/不要]
- [ ] NumPy/Pandas使用: [あり/なし]
- [ ] 非同期処理: [必要/不要]

### 規模判定結果
**[小規模/中規模/大規模]タスク**

### NumPy最適化戦略（データサイズ別）
```python
# 自動選択される処理戦略
if size < 1000:
    strategy = "sequential"      # そのまま処理
elif size < 10000:
    strategy = "vectorized"      # NumPyベクトル化
elif size < 100000:
    strategy = "chunked"         # チャンク処理
else:
    strategy = "parallel"        # 並列処理
```

## 品質管理ツール（Python）

### 適用ツール（規模に応じて自動選択）
| ツール | 小規模 | 中規模 | 大規模 | 実行コマンド |
|--------|--------|--------|--------|-------------|
| pytest | ✅ | ✅ | ✅ | `uv run pytest` |
| ruff format | ✅ | ✅ | ✅ | `uv run ruff format .` |
| ruff check | ✅ | ✅ | ✅ | `uv run ruff check .` |
| mypy (strict) | ✅ | ✅ | ✅ | `uv run mypy --strict .` |
| **similarity-py** | - | 重複80%超検出時 | ✅ | `similarity-py --threshold 0.80 --min-lines 5 quantforge/` |
| python-refactor.md | - | 重複80%超検出時 | 必須(Phase 4) | `.claude/commands/python-refactor.md` 適用 |
| pytest-benchmark | - | 推奨 | ✅ | `uv run pytest --benchmark-only` |
| hypothesis | - | ✅ | ✅ | `uv run pytest tests/test_property.py` |
| coverage | ✅ | ✅ | ✅ | `uv run pytest --cov=quantforge --cov-report=term-missing` |

### 品質ゲート（必達基準）
| 項目 | 小規模 | 中規模 | 大規模 |
|------|--------|--------|--------|
| テストカバレッジ | 80%以上 | 90%以上 | 95%以上 |
| 型カバレッジ | 90%以上 | 100% | 100% |
| 重複率（similarity-py） | - | 10%未満 | 5%未満 |
| ruffエラー | 0件 | 0件 | 0件 |
| mypyエラー（strict） | 0件 | 0件 | 0件 |

## フェーズ構成（規模に応じて選択）

<!-- ============ 小規模タスク（< 100行）============ -->
<details>
<summary>小規模実装フェーズ</summary>

### Phase 1: 実装（1-2時間）
- [ ] 単一機能の実装
- [ ] 完全な型アノテーション追加
- [ ] docstring作成（Googleスタイル）

### Phase 2: テスト作成（30分）
- [ ] ユニットテスト作成
- [ ] エッジケースのテスト
- [ ] カバレッジ80%以上確認

### Phase 3: 品質チェック（30分）
```bash
# 必須チェック
uv run pytest --cov=quantforge
uv run ruff format .
uv run ruff check .
uv run mypy --strict .
```

### Phase 4: 完了確認
- [ ] 機能動作確認
- [ ] 品質ゲート通過（カバレッジ80%、型カバレッジ90%）
- [ ] ドキュメント更新

</details>

<!-- ============ 中規模タスク（100-500行）============ -->
<details>
<summary>中規模実装フェーズ</summary>

### Phase 1: 設計（1-2時間）
- [ ] APIインターフェース設計
- [ ] データクラス/型定義（TypedDict、Protocol使用）
- [ ] エラーハンドリング設計
- [ ] NumPy最適化戦略決定

### Phase 2: 実装（4-8時間）
- [ ] コア機能実装
- [ ] 完全な型アノテーション（mypy strict準拠）
- [ ] 包括的なdocstring
- [ ] NumPyベクトル化（該当する場合）

### Phase 3: テスト作成（2-3時間）
- [ ] ユニットテスト
- [ ] パラメトライズドテスト
- [ ] **Hypothesisプロパティテスト**
  ```python
  from hypothesis import given, strategies as st
  
  @given(data=st.lists(st.floats(min_value=-1e6, max_value=1e6)))
  def test_property(data):
      # 不変条件のテスト
  ```
- [ ] カバレッジ確認（目標: 90%以上）

### Phase 4: 品質チェック（1時間）
```bash
# 基本チェック
uv run pytest --cov=quantforge --cov-report=term-missing
uv run ruff format .
uv run ruff check --fix .
uv run mypy --strict .

# 重複チェックとリファクタリング判断
similarity-py --threshold 0.80 --min-lines 5 quantforge/

# 判断フロー
# - 重複80%超を検出 → python-refactor.md を適用
# - 重複80%未満 → リファクタリング不要
# - テストファイルは対象外（--skip-test）
```

### Phase 5: 最適化（必要に応じて）
- [ ] pytest-benchmarkでパフォーマンス測定
  ```bash
  uv run pytest --benchmark-only --benchmark-autosave
  ```
- [ ] ボトルネック特定
- [ ] NumPy最適化適用

</details>

<!-- ============ 大規模タスク（500行以上）============ -->
<details>
<summary>大規模実装フェーズ</summary>

### Phase 1: 設計フェーズ（1日）
- [ ] アーキテクチャ設計
- [ ] モジュール分割設計
- [ ] API設計ドキュメント作成
- [ ] 型システム設計（Protocol、ABC活用）
- [ ] NumPy最適化戦略策定

### Phase 2: 段階的実装（3-5日）

#### マイルストーン1: 基盤実装
- [ ] 基本データ構造（TypedDict、dataclass）
- [ ] コアロジック
- [ ] 基本的なテスト
- [ ] **中間品質チェック**
  ```bash
  uv run pytest
  uv run ruff check
  uv run mypy --strict .
  similarity-py --threshold 0.85 quantforge/
  ```

#### マイルストーン2: 機能拡張
- [ ] 追加機能実装
- [ ] Rust連携（必要な場合）
- [ ] 統合テスト
- [ ] **Hypothesisテスト追加**
- [ ] **カバレッジ90%達成**

#### マイルストーン3: 最適化
- [ ] NumPyベクトル化完全実装
- [ ] 並列処理（concurrent.futures）
- [ ] **pytest-benchmarkによる性能測定**
  ```bash
  uv run pytest --benchmark-only --benchmark-compare
  ```

### Phase 3: 統合テスト（1日）
- [ ] エンドツーエンドテスト
- [ ] **ゴールデンマスターテスト**
  ```python
  # 既存動作の保証
  def test_golden_master(golden_data):
      for case in golden_data:
          assert compute(case.input) == case.expected
  ```
- [ ] 負荷テスト
- [ ] Rust連携テスト（該当する場合）

### Phase 4: リファクタリングフェーズ（必須: 1日）
- [ ] **python-refactor.md 完全適用**
- [ ] **similarity-py最終確認**（重複率5%未満）
  ```bash
  similarity-py --threshold 0.80 --print quantforge/ > similarity-report.md
  ```
- [ ] デザインパターン適用
- [ ] 型安全性の最終確認（mypy strict 100%）

### Phase 5: 最終品質保証
- [ ] **カバレッジ95%以上達成**
- [ ] **型カバレッジ100%達成**
- [ ] 全lintエラー解消
- [ ] パフォーマンスベンチマーク基準達成
- [ ] ドキュメント完成

</details>

## 技術要件

### 必須要件
- [ ] Python 3.9+ 互換性（型ヒント機能のため）
- [ ] **完全な型アノテーション（mypy strict準拠）**
- [ ] Googleスタイルdocstring（全public関数）
- [ ] エラーハンドリング（カスタム例外クラス）
- [ ] 数値精度: `src/constants.rs::EPSILON`参照（実務精度1e-3）※数値計算の場合

### パフォーマンス目標
- [ ] 応答時間: < [X] ms
- [ ] メモリ使用量: 入力データの2倍以内
- [ ] スループット: > [Z] req/s
- [ ] NumPy最適化: Pure Python比10倍以上

### Rust連携（該当する場合）
- [ ] quantforgeモジュール利用
- [ ] NumPy配列のゼロコピー受け渡し
- [ ] エラーハンドリングの統一
- [ ] 型の整合性確保

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| GILによる性能制限 | 中 | Rust関数へのオフロード |
| 型チェックの複雑さ | 低 | Protocol/ABCによる構造化 |
| NumPy互換性 | 低 | numpy.typingの活用 |
| テストの実行時間 | 中 | pytest-xdistによる並列実行 |

## チェックリスト

### 実装前
- [ ] 既存コードの確認（**similarity-pyで類似実装チェック**）
  ```bash
  similarity-py --threshold 0.80 quantforge/
  ```
- [ ] 依存パッケージの確認
- [ ] 設計レビュー（大規模の場合）
- [ ] **アンチパターンの回避確認**
  - ❌ TODO/FIXMEコメントを残さない
  - ❌ 「後で最適化」という前提で実装しない
  - ❌ 暫定的な実装を作らない
  - ✅ 最初から本番品質のコードを書く

### 実装中
- [ ] 定期的なテスト実行
- [ ] コミット前の`ruff format`
- [ ] 型アノテーションの追加（mypy strict準拠）
- [ ] NumPy最適化の適用判断

### 実装後
- [ ] 全品質ゲート通過
  - カバレッジ目標達成
  - 型カバレッジ100%
  - similarity-py重複率基準以下
- [ ] ベンチマーク結果記録
- [ ] ドキュメント更新
- [ ] 計画のarchive移動

## 成果物

- [ ] 実装コード（quantforge/以下）
- [ ] テストコード（tests/以下）
  - ユニットテスト
  - プロパティテスト（hypothesis）
  - ベンチマーク（pytest-benchmark）
- [ ] サンプルコード（examples/以下）
- [ ] APIドキュメント
- [ ] 型スタブファイル（.pyi）必要に応じて

## テスト戦略詳細

### テストファイル構成
```
tests/
├── test_unit_*.py          # ユニットテスト
├── test_property_*.py      # Hypothesisプロパティテスト
├── test_integration_*.py   # 統合テスト
├── test_benchmark_*.py     # パフォーマンステスト
└── test_golden_master.py   # ゴールデンマスターテスト
```

### 実行コマンド例
```bash
# 全テスト実行（カバレッジ付き）
uv run pytest --cov=quantforge --cov-report=html

# プロパティテストのみ
uv run pytest tests/test_property_*.py

# ベンチマークのみ
uv run pytest --benchmark-only

# 並列実行（高速化）
uv run pytest -n auto
```

## 備考

[追加の注意事項、参考資料、関連issue等を記載]