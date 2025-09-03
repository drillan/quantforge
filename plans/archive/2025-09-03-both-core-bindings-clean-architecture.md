# [Both] Core + Bindings クリーンアーキテクチャ完遂計画

## メタデータ
- **作成日**: 2025-09-03
- **言語**: Both (Rust + Python)
- **ステータス**: DRAFT
- **推定規模**: 大規模（完全リアーキテクチャ）
- **推定コード行数**: -856行（削除）、+100行（新規）
- **対象モジュール**: bindings/python全体、python/全体

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 削除856行、新規100行
- [x] 削除ファイル数: 10個以上
- [x] 影響範囲: 全体（プロジェクト構造変更）
- [x] PyO3バインディング: 既存（変更なし）
- [ ] SIMD最適化: 不要
- [ ] 並列化: 既存（変更なし）

### 規模判定結果
**大規模タスク**（プロジェクト全体のリアーキテクチャ）

## 背景と目的

### 現状の問題点
1. **ディレクトリ構造の不整合**
   - `python/`がプロジェクトルートに存在（本来は`bindings/python/python/`）
   - Core + Bindingsアーキテクチャが未完了

2. **中途半端なNumPy互換層**
   - arrow_api.py, arrow_ffi.py等が混在（856行）
   - ユーザー価値のない実装詳細が露出

3. **ドキュメントとの不一致**
   - ドキュメント: `from quantforge.models import black_scholes`
   - 現実: `from quantforge import black_scholes`

### 目標
- **クリーンアーキテクチャ**: Arrow Nativeのみ、NumPy互換削除
- **ドキュメント準拠**: `from quantforge.models`インターフェース
- **技術的負債ゼロ**: 中途半端な実装を完全排除

## 命名定義セクション

### 4.1 使用する既存命名
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
```

### 4.2 新規提案命名
```yaml
proposed_names: []  # 新規命名なし（既存のみ使用）
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 実装フェーズ

### Phase 1: NumPy互換層の削除 [1時間]
**削除対象（856行）:**
- [ ] `python/quantforge/arrow_api.py` (335行)
- [ ] `python/quantforge/arrow_ffi.py` (179行)
- [ ] `python/quantforge/arrow_native.py` (48行)
- [ ] `python/quantforge/numpy_compat.py` (294行)
- [ ] `python/quantforge/wrappers.py`
- [ ] `python/quantforge/compat.py`
- [ ] `python/quantforge/black_scholes.py`

**削除対象テスト:**
- [ ] `tests/test_arrow_*.py`
- [ ] `tests/performance/test_arrow_broadcasting.py`
- [ ] `tests/integration/test_arrow_native_integration.py`

### Phase 2: ディレクトリ構造の修正 [1時間]
- [ ] `python/` → `bindings/python/python/`に移動
- [ ] `bindings/python/python/quantforge/models/`ディレクトリ作成
- [ ] `bindings/python/stubs/`ディレクトリ作成
- [ ] `stubs/pyarrow.pyi`の復元と配置

### Phase 3: modelsモジュール実装 [30分]
**bindings/python/python/quantforge/__init__.py:**
```python
"""QuantForge: Arrow-native option pricing library"""
from .quantforge import __version__
from . import models

__all__ = ["__version__", "models"]
```

**bindings/python/python/quantforge/models/__init__.py:**
```python
"""Option pricing models - Arrow Native implementation"""
from ..quantforge import (
    black_scholes,
    black76,
    merton,
    american
)

__all__ = ["black_scholes", "black76", "merton", "american"]
```

### Phase 4: 設定ファイル更新 [30分]
- [ ] ルート`pyproject.toml`: `python-source`削除、`manifest-path`更新
- [ ] `bindings/python/pyproject.toml`: `python-source = "python"`追加
- [ ] mypy設定: `bindings/python/stubs`を`mypy_path`に設定

### Phase 5: テスト修正 [2時間]
- [ ] インポートパス修正: `from quantforge.models import`
- [ ] NumPy配列をPyArrow配列に変更
- [ ] 未対応テストに`@pytest.mark.skip`追加

### Phase 6: 検証 [1時間]
- [ ] `from quantforge.models import black_scholes`が動作
- [ ] Arrow配列での計算が正常動作
- [ ] パフォーマンステスト実行
- [ ] CI/CDパイプライン確認

## 成功基準

### 必須要件
- [ ] ドキュメント記載のインポートパスが動作
- [ ] Arrow Native実装のみ（NumPy互換なし）
- [ ] ゼロコピー実装の維持
- [ ] 既存テストの修正または適切なスキップ

### 品質基準
- [ ] コード削減: 856行以上削除
- [ ] 新規コード: 100行以下
- [ ] パフォーマンス維持: 現在の性能を維持
- [ ] Critical Rules準拠: C004, C013, C014

## リスクと対策

| リスク | 影響度 | 発生確率 | 対策 |
|--------|--------|----------|------|
| テスト破損 | 高 | 高 | 段階的修正と@pytest.mark.skip |
| インポートエラー | 中 | 中 | modelsモジュールの適切な再エクスポート |
| パフォーマンス劣化 | 低 | 低 | Rust実装は変更なし |

## 成果物

### コード成果物
- `bindings/python/python/quantforge/models/`: クリーンなAPIエントリ
- 削除: NumPy互換層（856行）

### ドキュメント成果物
- 更新なし（既存ドキュメントに準拠）

## 参考資料
- [Core + Bindingsアーキテクチャ計画](archive/2025-08-30-core-bindings-restructure/README.md)
- [Arrow Zero-Copy FFI実装](archive/2025-09-02-rust-arrow-zero-copy-ffi.md)
- [命名規則](../docs/ja/internal/naming_conventions.md)
- [Critical Rules](../.claude/critical-rules.xml)

## 備考
- ユーザーゼロの利点を活かした破壊的変更
- 技術的負債ゼロの理想実装
- 将来のArrow専用APIへの準備完了