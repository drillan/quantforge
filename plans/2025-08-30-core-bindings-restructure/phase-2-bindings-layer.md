# Phase 2: Python Bindings層構築

## 概要
Core層の純粋Rust実装をPythonから利用可能にするため、PyO3ベースのBindings層を構築します。

## 前提条件
- Phase 1の完了（Core層の完成）
- Core層のテスト合格
- Core APIドキュメントの準備

## タスクリスト

### 1. Bindings層ディレクトリ構造作成 [30分]

#### 1.1 基本構造の作成
```bash
mkdir -p bindings/python/{src,quantforge}
mkdir -p bindings/python/src/{models,converters}
```

#### 1.2 Cargo.toml作成
```toml
# bindings/python/Cargo.toml
[package]
name = "quantforge-python"
version = "0.1.0"
edition = "2021"

[lib]
name = "quantforge"
crate-type = ["cdylib"]

[dependencies]
quantforge-core = { path = "../../core" }
pyo3 = { version = "0.22", features = ["extension-module", "abi3-py312"] }
numpy = "0.22"
ndarray = "0.16"

[build-dependencies]
pyo3-build-config = "0.22"
```

#### 1.3 pyproject.toml作成
```toml
# bindings/python/pyproject.toml
[build-system]
requires = ["maturin>=1.7,<2.0"]
build-backend = "maturin"

[project]
name = "quantforge"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "numpy>=1.20",
]

[tool.maturin]
features = ["pyo3/extension-module"]
module-name = "quantforge._internal"
```

### 2. 型変換層の実装 [4時間]

#### 2.1 基本型変換
**完了条件**: Core型とPython型の相互変換が動作する
```rust
// bindings/python/src/converters/types.rs
use pyo3::prelude::*;
use quantforge_core::models::black_scholes::BlackScholesParams;

/// Core型からPython型への変換
impl ToPyObject for BlackScholesParams {
    fn to_object(&self, py: Python) -> PyObject {
        // 実装
    }
}

/// Python型からCore型への変換
pub fn extract_params(
    s: f64, k: f64, t: f64, r: f64, sigma: f64
) -> PyResult<BlackScholesParams> {
    Ok(BlackScholesParams {
        spot: s,
        strike: k,
        time: t,
        rate: r,
        volatility: sigma,
    })
}
```

#### 2.2 NumPy配列変換
```rust
// bindings/python/src/converters/numpy.rs
use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;

pub fn numpy_to_vec(arr: PyReadonlyArray1<f64>) -> Vec<f64> {
    arr.as_slice().unwrap().to_vec()
}

pub fn vec_to_numpy<'py>(
    py: Python<'py>, 
    vec: Vec<f64>
) -> Bound<'py, PyArray1<f64>> {
    PyArray1::from_vec_bound(py, vec)
}
```

#### 2.3 エラー変換
```rust
// bindings/python/src/converters/errors.rs
use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use quantforge_core::error::QuantForgeError;

impl From<QuantForgeError> for PyErr {
    fn from(err: QuantForgeError) -> PyErr {
        match err {
            QuantForgeError::InvalidInput(msg) => {
                PyValueError::new_err(msg)
            }
            QuantForgeError::NumericalError(msg) => {
                PyValueError::new_err(format!("Numerical error: {}", msg))
            }
        }
    }
}
```

### 3. Python API実装 [6時間]

#### 3.1 Black-Scholesモデル
```rust
// bindings/python/src/models/black_scholes.rs
use pyo3::prelude::*;
use quantforge_core::models::black_scholes as core_bs;

#[pyfunction]
#[pyo3(name = "call_price")]
#[pyo3(signature = (s, k, t, r, sigma))]
pub fn call_price(
    s: f64, k: f64, t: f64, r: f64, sigma: f64
) -> PyResult<f64> {
    let params = core_bs::BlackScholesParams {
        spot: s,
        strike: k,
        time: t,
        rate: r,
        volatility: sigma,
    };
    Ok(params.call_price())
}

#[pyfunction]
#[pyo3(name = "call_price_batch")]
pub fn call_price_batch(
    py: Python,
    spots: PyReadonlyArray1<f64>,
    strikes: PyReadonlyArray1<f64>,
    times: PyReadonlyArray1<f64>,
    rates: PyReadonlyArray1<f64>,
    sigmas: PyReadonlyArray1<f64>,
) -> PyResult<Bound<'_, PyArray1<f64>>> {
    py.allow_threads(|| {
        // Core層のバッチ処理を呼び出し
        let results = core_bs::call_price_batch_parallel(
            spots.as_slice()?,
            strikes.as_slice()?,
            times.as_slice()?,
            rates.as_slice()?,
            sigmas.as_slice()?,
        )?;
        Ok(PyArray1::from_vec_bound(py, results))
    })
}
```

#### 3.2 Greeksの実装
```rust
#[pyfunction]
#[pyo3(name = "greeks")]
pub fn greeks(
    py: Python,
    s: f64, k: f64, t: f64, r: f64, sigma: f64, 
    is_call: bool
) -> PyResult<PyObject> {
    let params = extract_params(s, k, t, r, sigma)?;
    let greeks = core_bs::calculate_greeks(&params, is_call);
    
    // Dictとして返却
    let dict = PyDict::new_bound(py);
    dict.set_item("delta", greeks.delta)?;
    dict.set_item("gamma", greeks.gamma)?;
    dict.set_item("vega", greeks.vega)?;
    dict.set_item("theta", greeks.theta)?;
    dict.set_item("rho", greeks.rho)?;
    Ok(dict.into())
}
```

#### 3.3 他モデルの実装
同様の方法で実装：
- [ ] Black76モデル
- [ ] Mertonモデル
- [ ] Americanモデル

### 4. Pythonモジュール構成 [2時間]

#### 4.1 メインモジュール
```rust
// bindings/python/src/lib.rs
use pyo3::prelude::*;

mod models;
mod converters;

#[pymodule]
fn quantforge(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", "0.1.0")?;
    
    // modelsサブモジュール
    let models = PyModule::new_bound(m.py(), "models")?;
    
    // Black-Scholes
    models.add_function(wrap_pyfunction!(
        models::black_scholes::call_price, &models
    )?)?;
    models.add_function(wrap_pyfunction!(
        models::black_scholes::put_price, &models
    )?)?;
    models.add_function(wrap_pyfunction!(
        models::black_scholes::greeks, &models
    )?)?;
    
    // Black76サブモジュール
    let black76 = PyModule::new_bound(m.py(), "black76")?;
    models::black76::register(&black76)?;
    models.add_submodule(&black76)?;
    
    // Mertonサブモジュール
    let merton = PyModule::new_bound(m.py(), "merton")?;
    models::merton::register(&merton)?;
    models.add_submodule(&merton)?;
    
    // Americanサブモジュール
    let american = PyModule::new_bound(m.py(), "american")?;
    models::american::register(&american)?;
    models.add_submodule(&american)?;
    
    m.add_submodule(&models)?;
    Ok(())
}
```

#### 4.2 Python側ラッパー
```python
# bindings/python/quantforge/__init__.py
"""QuantForge - High-performance option pricing library."""

from __future__ import annotations
from . import _internal

__version__ = _internal.__version__

# Re-export models
models = _internal.models

__all__ = ["models", "__version__"]
```

```python
# bindings/python/quantforge/py.typed
# Marker file for PEP 561
```

#### 4.3 型スタブ生成
```python
# bindings/python/quantforge/quantforge.pyi
from typing import Union, Optional, Dict, Any
import numpy as np
from numpy.typing import ArrayLike

class models:
    @staticmethod
    def call_price(
        s: float, k: float, t: float, r: float, sigma: float
    ) -> float: ...
    
    @staticmethod
    def call_price_batch(
        spots: ArrayLike,
        strikes: ArrayLike,
        times: ArrayLike,
        rates: ArrayLike,
        sigmas: ArrayLike
    ) -> np.ndarray: ...
    
    @staticmethod
    def greeks(
        s: float, k: float, t: float, r: float, sigma: float,
        is_call: bool = True
    ) -> Dict[str, float]: ...
```

### 5. Bindings層テスト [3時間]

#### 5.1 単体テスト
```python
# bindings/python/tests/test_black_scholes.py
import pytest
import numpy as np
from quantforge import models

def test_call_price():
    """Test single call price calculation."""
    price = models.call_price(
        s=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2
    )
    assert abs(price - 10.450583572185565) < 1e-10

def test_call_price_batch():
    """Test batch call price calculation."""
    spots = np.array([90.0, 100.0, 110.0])
    prices = models.call_price_batch(
        spots=spots,
        strikes=100.0,
        times=1.0,
        rates=0.05,
        sigmas=0.2
    )
    assert len(prices) == 3
    assert all(p > 0 for p in prices)

def test_greeks():
    """Test Greeks calculation."""
    greeks = models.greeks(
        s=100.0, k=100.0, t=1.0, r=0.05, sigma=0.2
    )
    assert "delta" in greeks
    assert 0 < greeks["delta"] < 1
```

#### 5.2 統合テスト
```python
# bindings/python/tests/test_integration.py
import pytest
import numpy as np
from quantforge import models

def test_consistency_with_golden_master():
    """Verify consistency with golden master values."""
    # ゴールデンマスターとの比較
    pass

def test_numpy_interop():
    """Test NumPy array interoperability."""
    # NumPy配列との相互運用性テスト
    pass

def test_error_handling():
    """Test error handling and validation."""
    with pytest.raises(ValueError):
        models.call_price(s=-100, k=100, t=1, r=0.05, sigma=0.2)
```

#### 5.3 パフォーマンステスト
```python
# bindings/python/tests/test_performance.py
import time
import numpy as np
from quantforge import models

def test_gil_release():
    """Verify GIL is released during computation."""
    # マルチスレッドでの並列実行テスト
    pass

def test_batch_performance():
    """Test batch processing performance."""
    n = 1_000_000
    spots = np.random.uniform(50, 150, n)
    
    start = time.perf_counter()
    _ = models.call_price_batch(
        spots=spots, strikes=100.0, 
        times=1.0, rates=0.05, sigmas=0.2
    )
    elapsed = time.perf_counter() - start
    
    # 性能基準: 100万件を1秒以内
    assert elapsed < 1.0
```

### 6. ビルドとテスト [1時間]

#### 6.1 ビルド手順
```bash
cd bindings/python

# 開発用ビルド
maturin develop --release

# Wheelビルド
maturin build --release

# テスト実行
pytest tests/ -v
```

#### 6.2 品質チェック
```bash
# Rustコード
cargo fmt --all -- --check
cargo clippy --all-targets -- -D warnings

# Pythonコード
ruff check .
mypy .
```

## 完了条件

### 必須チェックリスト
- [ ] Core層の全機能をPython APIとして公開
- [ ] NumPy配列との相互運用
- [ ] エラーの適切な変換
- [ ] GILの適切な解放
- [ ] 型スタブの完備

### パフォーマンス基準
- [ ] GIL解放率 > 95%
- [ ] バッチ処理: Core層と同等性能（オーバーヘッド < 5%）
- [ ] メモリ効率: ゼロコピー実装

### 品質基準
- [ ] テストカバレッジ > 90%
- [ ] 型チェック合格（mypy）
- [ ] リンター合格（ruff）

## 成果物

### コード成果物
```
bindings/python/
├── Cargo.toml
├── pyproject.toml
├── src/
│   ├── lib.rs
│   ├── models/
│   └── converters/
└── quantforge/
    ├── __init__.py
    ├── py.typed
    └── quantforge.pyi
```

### ドキュメント成果物
- Python API仕様書
- 型スタブドキュメント
- 移行ガイド

## リスクと対策

| リスク | 対策 |
|--------|------|
| 型変換のオーバーヘッド | ゼロコピー実装 |
| GIL競合 | allow_threadsの適切な使用 |
| メモリリーク | 参照カウント管理 |
| API非互換 | ゴールデンマスターで検証 |

## Phase 3への引き継ぎ

### 提供物
1. 完全なPython Bindings
2. テストスイート
3. パフォーマンス測定結果

### 注意事項
- Core層への変更は不要
- APIの互換性を維持
- パフォーマンス劣化なし