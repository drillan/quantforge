# 型スタブ（.pyi）実装計画

## 🎯 目的
QuantForgeのPython APIに対する完全な型スタブを実装し、IDE補完、型チェック、ドキュメント生成を改善する。

## 📊 現状分析

### 既存の状況
- **既存型スタブ**: `python/quantforge/quantforge.pyi`（古い構造）
- **新バインディング**: `bindings/python/`配下
- **問題点**:
  - 型スタブが古いモジュール構造を反映
  - 新しいAPI構造（quantforge.black_scholes等）と不一致
  - ArrayLike型の定義が不完全

### 実際のモジュール構造
```python
quantforge/
├── __version__          # バージョン情報
├── black_scholes/       # Black-Scholesモデル
│   ├── call_price()
│   ├── put_price()
│   ├── greeks()
│   ├── implied_volatility()
│   └── *_batch()        # バッチ版
├── black76/             # Black76モデル
│   └── (同様の関数群)
├── merton/              # Mertonモデル（配当付き）
│   └── (同様の関数群 + q parameter)
├── models/              # black_scholesのエイリアス
│   └── american/        # Americanオプション
└── (将来追加予定モデル)
```

## 📝 実装計画

### Phase 1: 準備と分析 [2時間]

#### 1.1 API完全調査
```python
# tools/inspect_api.py
import quantforge
import inspect
import json

def analyze_module(module, name):
    """モジュールの完全なAPI構造を抽出"""
    api_structure = {}
    for attr_name in dir(module):
        if not attr_name.startswith('_'):
            attr = getattr(module, attr_name)
            if callable(attr):
                sig = inspect.signature(attr)
                api_structure[attr_name] = {
                    'signature': str(sig),
                    'params': list(sig.parameters.keys()),
                    'doc': inspect.getdoc(attr)
                }
    return api_structure

# 全モジュールを分析
api_map = {
    'black_scholes': analyze_module(quantforge.black_scholes, 'black_scholes'),
    'black76': analyze_module(quantforge.black76, 'black76'),
    'merton': analyze_module(quantforge.merton, 'merton'),
    # 'american': analyze_module(quantforge.models.american, 'american')
}

# 結果を保存
with open('api_structure.json', 'w') as f:
    json.dump(api_map, f, indent=2)
```

#### 1.2 型パターン分析
- スカラー入力型: `float`
- 配列入力型: `float | NDArray[np.float64] | list[float]`
- 出力型パターン:
  - 単一値: `float`
  - バッチ: `NDArray[np.float64]`
  - Greeks: `dict[str, float]` or `dict[str, NDArray[np.float64]]`

### Phase 2: 型スタブ構造設計 [1時間]

#### 2.1 ファイル配置（PEP 561準拠）
```
bindings/python/python/quantforge/
├── __init__.py
├── py.typed                 # PEP 561マーカー
├── __init__.pyi            # メインモジュール型スタブ
├── black_scholes.pyi       # Black-Scholes型スタブ
├── black76.pyi             # Black76型スタブ
├── merton.pyi              # Merton型スタブ
├── models/
│   ├── __init__.pyi
│   └── american.pyi        # American型スタブ
└── _types.pyi              # 共通型定義
```

#### 2.2 共通型定義
```python
# bindings/python/python/quantforge/_types.pyi
from typing import Union, TypeAlias
import numpy as np
from numpy.typing import NDArray, ArrayLike as NpArrayLike

# 基本型エイリアス
Float: TypeAlias = Union[float, int]
FloatArray: TypeAlias = NDArray[np.float64]

# 入力型（スカラーまたは配列）
ScalarOrArray: TypeAlias = Union[
    Float,                    # スカラー値
    list[Float],             # Pythonリスト
    FloatArray,              # NumPy配列
    NpArrayLike             # ArrayLike全般
]

# Greeks戻り値型
GreeksDict: TypeAlias = dict[str, float]
GreeksBatchDict: TypeAlias = dict[str, FloatArray]

# オプションタイプ
BoolOrArray: TypeAlias = Union[bool, list[bool], NDArray[np.bool_]]
```

### Phase 3: 型スタブ実装 [4時間]

#### 3.1 メインモジュール型スタブ
```python
# bindings/python/python/quantforge/__init__.pyi
"""QuantForge - High-performance option pricing library"""

from . import black_scholes as black_scholes
from . import black76 as black76
from . import merton as merton
from . import models as models

__version__: str
__all__: list[str]
```

#### 3.2 Black-Scholes型スタブ
```python
# bindings/python/python/quantforge/black_scholes.pyi
from typing import overload
from ._types import Float, FloatArray, ScalarOrArray, GreeksDict, GreeksBatchDict

# 単一計算
@overload
def call_price(s: Float, k: Float, t: Float, r: Float, sigma: Float) -> float: ...

# バッチ計算（broadcasting対応）
@overload
def call_price_batch(
    spots: ScalarOrArray,
    strikes: ScalarOrArray,
    times: ScalarOrArray,
    rates: ScalarOrArray,
    sigmas: ScalarOrArray
) -> FloatArray: ...

def put_price(s: Float, k: Float, t: Float, r: Float, sigma: Float) -> float: ...

def put_price_batch(
    spots: ScalarOrArray,
    strikes: ScalarOrArray,
    times: ScalarOrArray,
    rates: ScalarOrArray,
    sigmas: ScalarOrArray
) -> FloatArray: ...

def greeks(
    s: Float,
    k: Float,
    t: Float,
    r: Float,
    sigma: Float,
    is_call: bool = True
) -> GreeksDict: ...

def greeks_batch(
    spots: ScalarOrArray,
    strikes: ScalarOrArray,
    times: ScalarOrArray,
    rates: ScalarOrArray,
    sigmas: ScalarOrArray,
    is_calls: ScalarOrArray | bool = True
) -> GreeksBatchDict: ...

def implied_volatility(
    price: Float,
    s: Float,
    k: Float,
    t: Float,
    r: Float,
    is_call: bool = True
) -> float: ...

def implied_volatility_batch(
    prices: ScalarOrArray,
    spots: ScalarOrArray,
    strikes: ScalarOrArray,
    times: ScalarOrArray,
    rates: ScalarOrArray,
    is_calls: ScalarOrArray | bool = True
) -> FloatArray: ...
```

#### 3.3 Black76型スタブ
```python
# bindings/python/python/quantforge/black76.pyi
from typing import overload
from ._types import Float, FloatArray, ScalarOrArray, GreeksDict, GreeksBatchDict

def call_price(f: Float, k: Float, t: Float, r: Float, sigma: Float) -> float:
    """Calculate Black76 call option price for futures/forwards"""
    ...

def call_price_batch(
    forwards: ScalarOrArray,  # Note: 'f' -> 'forwards' for clarity in batch
    strikes: ScalarOrArray,
    times: ScalarOrArray,
    rates: ScalarOrArray,
    sigmas: ScalarOrArray
) -> FloatArray: ...

# 以下、put_price, greeks, implied_volatility等も同様
```

#### 3.4 Merton型スタブ（配当付き）
```python
# bindings/python/python/quantforge/merton.pyi
from typing import overload
from ._types import Float, FloatArray, ScalarOrArray, GreeksDict, GreeksBatchDict

def call_price(
    s: Float,
    k: Float,
    t: Float,
    r: Float,
    q: Float,  # 配当利回り
    sigma: Float
) -> float: ...

def call_price_batch(
    spots: ScalarOrArray,
    strikes: ScalarOrArray,
    times: ScalarOrArray,
    rates: ScalarOrArray,
    dividend_yields: ScalarOrArray,  # 'q' -> 'dividend_yields' in batch
    sigmas: ScalarOrArray
) -> FloatArray: ...

# Greeks with dividend sensitivity
def greeks(
    s: Float,
    k: Float,
    t: Float,
    r: Float,
    q: Float,
    sigma: Float,
    is_call: bool = True
) -> GreeksDict:
    """
    Returns dict with keys:
    - delta, gamma, vega, theta, rho
    - dividend_rho (sensitivity to dividend yield)
    """
    ...
```

#### 3.5 Americanオプション型スタブ
```python
# bindings/python/python/quantforge/models/american.pyi
from typing import overload
from .._types import Float, FloatArray, ScalarOrArray, GreeksDict, GreeksBatchDict

def call_price(
    s: Float,
    k: Float,
    t: Float,
    r: Float,
    q: Float,
    sigma: Float
) -> float:
    """Calculate American call option price using Bjerksund-Stensland 2002"""
    ...

def put_price(
    s: Float,
    k: Float,
    t: Float,
    r: Float,
    q: Float,
    sigma: Float
) -> float:
    """Calculate American put option price using Bjerksund-Stensland 2002"""
    ...

# Early exercise boundary
def exercise_boundary(
    s: Float,
    k: Float,
    t: Float,
    r: Float,
    q: Float,
    sigma: Float,
    is_call: bool = True
) -> float:
    """Calculate optimal exercise boundary for American option"""
    ...

def exercise_boundary_batch(
    spots: ScalarOrArray,
    strikes: ScalarOrArray,
    times: ScalarOrArray,
    rates: ScalarOrArray,
    dividend_yields: ScalarOrArray,
    sigmas: ScalarOrArray,
    is_calls: ScalarOrArray | bool = True
) -> FloatArray: ...
```

### Phase 4: 検証とテスト [2時間]

#### 4.1 型チェックテスト
```python
# tests/test_type_stubs.py
import numpy as np
from quantforge import black_scholes, black76, merton

def test_type_inference():
    """IDE型推論のテスト"""
    # スカラー入力 -> float出力
    price: float = black_scholes.call_price(100, 100, 1, 0.05, 0.2)
    
    # 配列入力 -> ndarray出力
    spots = np.array([100, 105, 110])
    prices: np.ndarray = black_scholes.call_price_batch(
        spots, 100, 1, 0.05, 0.2
    )
    
    # Greeks -> dict出力
    greeks: dict[str, float] = black_scholes.greeks(100, 100, 1, 0.05, 0.2)
    assert 'delta' in greeks
    
    # Broadcasting
    strikes = [95, 100, 105]
    prices = black_scholes.call_price_batch(100, strikes, 1, 0.05, 0.2)
    assert len(prices) == 3
```

#### 4.2 mypy設定
```ini
# bindings/python/pyproject.toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
check_untyped_defs = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict_equality = true

[[tool.mypy.overrides]]
module = "quantforge.*"
ignore_missing_imports = false
```

#### 4.3 検証スクリプト
```bash
#!/bin/bash
# scripts/validate_type_stubs.sh

echo "=== Type Stub Validation ==="

# 1. mypy型チェック
echo "Running mypy..."
cd bindings/python
mypy python/quantforge --config-file pyproject.toml

# 2. stubtest（型スタブと実装の一致確認）
echo "Running stubtest..."
python -m mypy.stubtest quantforge \
    --allowlist stubtest_allowlist.txt

# 3. IDE補完テスト（手動）
echo "Testing IDE completion..."
python -c "
import quantforge
# IDEで以下の補完をテスト:
# quantforge.black_scholes.<Tab>
# quantforge.black76.<Tab>
"

# 4. Sphinx型ドキュメント生成
echo "Generating type documentation..."
sphinx-apidoc -o docs/api python/quantforge
```

### Phase 5: 自動生成とメンテナンス [2時間]

#### 5.1 型スタブ自動生成スクリプト
```python
# tools/generate_stubs.py
"""Rustバインディングから型スタブを自動生成"""

import inspect
import ast
from pathlib import Path
from typing import Any, get_type_hints

def extract_rust_signature(func) -> str:
    """Rust関数から型情報を抽出"""
    # PyO3のドキュメント文字列から型情報を解析
    doc = inspect.getdoc(func)
    # 簡易パーサーで型を抽出
    # 実装詳細...
    pass

def generate_stub_for_module(module: Any, output_path: Path):
    """モジュールの型スタブを生成"""
    stub_content = []
    
    # インポート
    stub_content.append("from typing import overload")
    stub_content.append("from ._types import *")
    stub_content.append("")
    
    # 関数定義
    for name in dir(module):
        if name.startswith('_'):
            continue
        attr = getattr(module, name)
        if callable(attr):
            sig = extract_rust_signature(attr)
            stub_content.append(f"def {name}{sig}: ...")
            stub_content.append("")
    
    # ファイル出力
    output_path.write_text('\n'.join(stub_content))

# 実行
if __name__ == "__main__":
    import quantforge
    base_path = Path("bindings/python/python/quantforge")
    
    generate_stub_for_module(
        quantforge.black_scholes,
        base_path / "black_scholes.pyi"
    )
```

#### 5.2 CI/CD統合
```yaml
# .github/workflows/type_stubs.yml
name: Type Stubs Validation

on:
  push:
    paths:
      - 'bindings/python/**/*.rs'
      - 'bindings/python/**/*.pyi'
  pull_request:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install uv
          uv sync --group dev
      
      - name: Build extension
        run: |
          cd bindings/python
          maturin develop --release
      
      - name: Validate type stubs
        run: |
          mypy bindings/python/python/quantforge
          python -m mypy.stubtest quantforge
      
      - name: Test type inference
        run: |
          pytest tests/test_type_stubs.py -v
```

## 📋 実装チェックリスト

### Phase 1: 準備と分析
- [ ] API構造の完全な調査
- [ ] 型パターンの分析
- [ ] 既存型スタブとのギャップ分析

### Phase 2: 構造設計
- [ ] ファイル配置計画
- [ ] 共通型定義（_types.pyi）
- [ ] PEP 561準拠確認

### Phase 3: 実装
- [ ] __init__.pyi
- [ ] black_scholes.pyi
- [ ] black76.pyi
- [ ] merton.pyi
- [ ] models/american.pyi
- [ ] py.typedファイル作成

### Phase 4: 検証
- [ ] mypy型チェック合格
- [ ] IDE補完テスト
- [ ] stubtestでの検証
- [ ] ドキュメント生成テスト

### Phase 5: 自動化
- [ ] 自動生成スクリプト作成
- [ ] CI/CD統合
- [ ] メンテナンスガイド作成

## 🎯 完了条件

1. **型チェック**: mypy --strict合格
2. **IDE補完**: VSCode/PyCharmで完全な補完
3. **ドキュメント**: 型情報を含むAPIドキュメント生成
4. **CI/CD**: 自動検証パイプライン構築
5. **カバレッジ**: 全公開APIの型定義100%

## 📈 期待される効果

- **開発効率向上**: IDE補完により50%高速化
- **バグ削減**: 型エラーの事前検出
- **ドキュメント改善**: 型情報の自動反映
- **保守性向上**: APIの変更を型レベルで追跡

## ⏰ タイムライン

- **Phase 1-2**: 3時間（分析と設計）
- **Phase 3**: 4時間（実装）
- **Phase 4**: 2時間（検証）
- **Phase 5**: 2時間（自動化）
- **合計**: 11時間（1.5日）

## 🔧 必要なツール

```bash
pip install mypy numpy-stubs types-setuptools
pip install sphinx sphinx-autodoc-typehints
pip install stubgen  # 自動生成用
```

## 📚 参考資料

- [PEP 561 - Distributing and Packaging Type Information](https://www.python.org/dev/peps/pep-0561/)
- [mypy - Using Stubs](https://mypy.readthedocs.io/en/stable/stubs.html)
- [numpy-stubs](https://github.com/numpy/numpy-stubs)
- [PyO3 Type Annotations](https://pyo3.rs/main/python_typing)