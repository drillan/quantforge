# [Python] モジュールインポートAPI整合性修正 実装計画

## メタデータ
- **作成日**: 2025-08-28
- **言語**: Python
- **ステータス**: DRAFT
- **推定規模**: 小
- **推定コード行数**: 80-100行
- **対象モジュール**: python/quantforge/

## ⚠️ 技術的負債ゼロの原則

**重要**: このプロジェクトでは技術的負債を一切作らないことを最優先とします。

### 実装方針
- ドキュメント（docs/api/python/）が唯一の真実（D-SSoT原則）
- ドキュメント通りのAPIを完全実装
- 一時的な回避策や段階的移行は行わない
- 最初から理想的な構造を実装

## 1. 問題の背景

### 現状
- **CI失敗**: GitHub Actions のホイールテストで `ModuleNotFoundError: No module named 'quantforge.models'`
- **API不整合**: ドキュメントとRust実装のインターフェースが異なる

### 根本原因
```python
# ドキュメントの期待（docs/api/python/black_scholes.md）
from quantforge.models import black_scholes
call_price = black_scholes.call_price(100, 105, 1, 0.05, 0.2)

# 実際のRust実装
from quantforge import models
call_price = models.call_price(100, 105, 1, 0.05, 0.2)  # Black-Scholes直接
```

## 2. 解決方針

### アプローチ: Pythonラッパーモジュール実装
ドキュメントを真実の源（SSoT）として、APIに完全準拠したPythonラッパーを作成

### 実装後の構造
```
python/quantforge/
├── __init__.py (既存、修正)
├── models/             # 新規ディレクトリ
│   ├── __init__.py    # モデルの公開
│   ├── black_scholes.py  # BSラッパー
│   ├── black76.py    # Black76パススルー
│   ├── merton.py     # Mertonパススルー
│   └── american.py   # Americanパススルー
└── quantforge.abi3.so  # Rust実装
```

## 3. タスク規模判定

### 判定基準
- [x] 推定コード行数: 80-100行
- [x] 新規ファイル数: 5個
- [x] 影響範囲: 単一モジュール（python/quantforge/）
- [x] Rust連携: 必要（既存のRustモジュールをラップ）
- [ ] NumPy/Pandas使用: なし（パススルーのみ）
- [ ] 非同期処理: 不要

### 規模判定結果
**小規模タスク**

## 4. 命名定義セクション

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
  - name: "black_scholes"
    meaning: "Black-Scholesモデル"
    source: "docs/api/python/black_scholes.md"
  - name: "black76"
    meaning: "Black76モデル"
    source: "docs/api/python/black76.md"
```

### 4.2 新規提案命名
```yaml
proposed_names: []  # 新規命名なし（既存のAPIに準拠）
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 5. 実装詳細

### Phase 1: ディレクトリ構造作成（15分）
```bash
mkdir -p python/quantforge/models
touch python/quantforge/models/__init__.py
touch python/quantforge/models/black_scholes.py
touch python/quantforge/models/black76.py
touch python/quantforge/models/merton.py
touch python/quantforge/models/american.py
```

### Phase 2: 実装内容（45分）

#### models/__init__.py
```python
"""QuantForge models subpackage."""

from . import american, black76, black_scholes, merton

__all__ = ["black_scholes", "black76", "merton", "american"]
```

#### models/black_scholes.py
```python
"""Black-Scholes model wrapper for API compatibility."""

from quantforge import models as _rust_models

# Black-Scholesの関数を直接公開（RustのmodelsはデフォルトでBS）
call_price = _rust_models.call_price
put_price = _rust_models.put_price
call_price_batch = _rust_models.call_price_batch
put_price_batch = _rust_models.put_price_batch
implied_volatility = _rust_models.implied_volatility
implied_volatility_batch = _rust_models.implied_volatility_batch
greeks = _rust_models.greeks
greeks_batch = _rust_models.greeks_batch

__all__ = [
    "call_price",
    "put_price",
    "call_price_batch",
    "put_price_batch",
    "implied_volatility",
    "implied_volatility_batch",
    "greeks",
    "greeks_batch",
]
```

#### models/black76.py
```python
"""Black76 model direct export."""

from quantforge.models import black76 as _black76

# Black76サブモジュールをそのまま公開
call_price = _black76.call_price
put_price = _black76.put_price
call_price_batch = _black76.call_price_batch
put_price_batch = _black76.put_price_batch
implied_volatility = _black76.implied_volatility
implied_volatility_batch = _black76.implied_volatility_batch
greeks = _black76.greeks
greeks_batch = _black76.greeks_batch

__all__ = [
    "call_price",
    "put_price", 
    "call_price_batch",
    "put_price_batch",
    "implied_volatility",
    "implied_volatility_batch",
    "greeks",
    "greeks_batch",
]
```

#### models/merton.py と models/american.py
同様のパターンで実装

### Phase 3: テスト作成（30分）

#### ローカルビルドテスト
```bash
# クリーンビルド
cargo clean
rm -rf python/quantforge/quantforge.abi3.so

# Rustライブラリビルド
uv run maturin develop --release

# インポートテスト
python -c "from quantforge.models import black_scholes, black76, merton, american"
python -c "from quantforge.models import black_scholes; print(black_scholes.call_price(100, 100, 1, 0.05, 0.2))"

# 既存テストの実行
uv run pytest tests/ -v

# ホイールビルドテスト
uv run maturin build --release
pip install target/wheels/*.whl --force-reinstall
python -c "from quantforge.models import black_scholes; print('Import success!')"
```

### Phase 4: 品質チェック（15分）
```bash
# 必須チェック
uv run ruff format python/quantforge/models/
uv run ruff check python/quantforge/models/
uv run mypy python/quantforge/models/ --strict
uv run pytest tests/
```

## 6. 技術要件

### 必須要件
- [x] Python 3.12+ 互換性（プロジェクト要件）
- [x] 完全な型アノテーション（必要に応じて.pyiファイル利用）
- [x] ドキュメント準拠API
- [x] エラーハンドリング（Rustエラーの適切な伝播）

### パフォーマンス目標
- [x] オーバーヘッド: なし（単純なパススルー）
- [x] メモリ使用量: 追加なし
- [x] レイテンシ: < 1μs（関数参照のみ）

## 7. リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| Rustモジュール構造変更 | 低 | テストで検出、即座に修正 |
| インポート循環参照 | 低 | 遅延インポートで回避 |
| 型スタブの不整合 | 低 | quantforge.pyiの確認と更新 |

## 8. チェックリスト

### 実装前
- [x] 既存コードの確認（quantforge/__init__.py、quantforge.pyi）
- [x] ドキュメント（docs/api/python/）の確認
- [x] CI.ymlのテストコマンド確認
- [x] naming_conventions.mdとの整合性確認

### 実装中
- [ ] 各モデルのラッパー作成
- [ ] __all__によるエクスポート管理
- [ ] 型アノテーションの確認

### 実装後
- [ ] ローカルインポートテスト成功
- [ ] 既存テストスイート（pytest）通過
- [ ] ホイールビルドとインストールテスト成功
- [ ] ruff/mypyエラー: 0件
- [ ] GitHub Actions CIの成功確認

## 9. 成果物

- [ ] python/quantforge/models/__init__.py
- [ ] python/quantforge/models/black_scholes.py
- [ ] python/quantforge/models/black76.py
- [ ] python/quantforge/models/merton.py
- [ ] python/quantforge/models/american.py
- [ ] CIテスト成功（グリーンビルド）

## 10. 完了基準

1. `from quantforge.models import black_scholes, black76, merton, american` が成功
2. ドキュメントのすべてのコード例が動作
3. GitHub Actions CIがグリーン
4. 品質ゲート通過（ruff、mypy、pytest）

## 備考

- この修正により、ドキュメントと実装の完全な整合性が保たれる（D-SSoT原則）
- 技術的負債ゼロ：一時的な回避策ではなく、恒久的な解決策
- 後方互換性の考慮不要（プロジェクト前提条件より）