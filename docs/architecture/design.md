# QuantForge Core + Bindings アーキテクチャ設計仕様書

## 1. 概要

本文書は、QuantForgeのCore + Bindingsアーキテクチャの詳細設計を定義する。

## 2. Core層設計

### 2.1 トレイト設計

#### 基本モデルトレイト
```rust
// core/src/traits/model.rs
pub trait OptionPricing {
    type Params;
    type Result;
    
    fn call_price(params: &Self::Params) -> Self::Result;
    fn put_price(params: &Self::Params) -> Self::Result;
}

pub trait Greeks {
    type Params;
    type GreeksResult;
    
    fn calculate_greeks(params: &Self::Params, is_call: bool) -> Self::GreeksResult;
}

pub trait ImpliedVolatility {
    type Params;
    
    fn implied_volatility(
        price: f64,
        params: &Self::Params,
        is_call: bool,
    ) -> Result<f64, QuantForgeError>;
}
```

#### バッチ処理トレイト
```rust
// core/src/traits/batch.rs
use rayon::prelude::*;

pub trait BatchProcessor: Send + Sync {
    type Input;
    type Output;
    
    fn process_batch(&self, inputs: &[Self::Input]) -> Vec<Self::Output>;
    
    fn process_batch_parallel(
        &self,
        inputs: &[Self::Input],
        threshold: usize,
    ) -> Vec<Self::Output> {
        if inputs.len() < threshold {
            self.process_batch(inputs)
        } else {
            inputs
                .par_iter()
                .map(|input| self.process_single(input))
                .collect()
        }
    }
    
    fn process_single(&self, input: &Self::Input) -> Self::Output;
}
```

### 2.2 データ構造定義

#### Black-Scholesパラメータ
```rust
// core/src/models/black_scholes.rs
#[derive(Debug, Clone, Copy)]
pub struct BlackScholesParams {
    pub spot: f64,      // s in API
    pub strike: f64,    // k in API
    pub time: f64,      // t in API
    pub rate: f64,      // r in API
    pub sigma: f64,     // sigma in API
}

#[derive(Debug, Clone, Copy)]
pub struct BlackScholesGreeks {
    pub delta: f64,
    pub gamma: f64,
    pub vega: f64,
    pub theta: f64,
    pub rho: f64,
}
```

#### Black76パラメータ
```rust
// core/src/models/black76.rs
#[derive(Debug, Clone, Copy)]
pub struct Black76Params {
    pub forward: f64,   // f in API
    pub strike: f64,    // k in API
    pub time: f64,      // t in API
    pub rate: f64,      // r in API
    pub sigma: f64,     // sigma in API
}

#[derive(Debug, Clone, Copy)]
pub struct Black76Greeks {
    pub delta: f64,
    pub gamma: f64,
    pub vega: f64,
    pub theta: f64,
    pub rho: f64,
}
```

#### Mertonパラメータ（配当付き）
```rust
// core/src/models/merton.rs
#[derive(Debug, Clone, Copy)]
pub struct MertonParams {
    pub spot: f64,           // s in API
    pub strike: f64,         // k in API
    pub time: f64,           // t in API
    pub rate: f64,           // r in API
    pub dividend_yield: f64, // q in API
    pub sigma: f64,          // sigma in API
}

#[derive(Debug, Clone, Copy)]
pub struct MertonGreeks {
    pub delta: f64,
    pub gamma: f64,
    pub vega: f64,
    pub theta: f64,
    pub rho: f64,
    pub dividend_rho: f64,  // Merton特有
}
```

#### Americanパラメータ
```rust
// core/src/models/american.rs
#[derive(Debug, Clone, Copy)]
pub struct AmericanParams {
    pub spot: f64,           // s in API
    pub strike: f64,         // k in API
    pub time: f64,           // t in API
    pub rate: f64,           // r in API
    pub dividend_yield: f64, // q in API
    pub sigma: f64,          // sigma in API
    pub num_steps: usize,    // 二項ツリーのステップ数
}

#[derive(Debug, Clone, Copy)]
pub struct AmericanGreeks {
    pub delta: f64,
    pub gamma: f64,
    pub vega: f64,
    pub theta: f64,
    pub rho: f64,
    pub dividend_rho: f64,
}

#[derive(Debug, Clone, Copy)]
pub struct AmericanResult {
    pub price: f64,
    pub exercise_boundary: f64,  // 早期行使境界
}
```

### 2.3 エラー型定義

```rust
// core/src/error.rs
use thiserror::Error;

#[derive(Error, Debug)]
pub enum QuantForgeError {
    #[error("Invalid input: {0}")]
    InvalidInput(String),
    
    #[error("Numerical error: {0}")]
    NumericalError(String),
    
    #[error("Convergence failed: {0}")]
    ConvergenceError(String),
    
    #[error("Out of bounds: {0}")]
    OutOfBounds(String),
}

pub type Result<T> = std::result::Result<T, QuantForgeError>;
```

### 2.4 並列処理の最適化

```rust
// core/src/parallel.rs
// 実測に基づく閾値（既存の最適化を維持）
pub const PARALLEL_THRESHOLD_SMALL: usize = 8_000;    // 小規模並列化
pub const PARALLEL_THRESHOLD_MEDIUM: usize = 200_000; // 中規模並列化
pub const PARALLEL_THRESHOLD_LARGE: usize = 1_000_000; // 大規模並列化

pub fn select_parallel_threshold(size: usize) -> usize {
    match size {
        0..=8_000 => usize::MAX,  // 並列化しない
        8_001..=200_000 => PARALLEL_THRESHOLD_SMALL,
        200_001..=1_000_000 => PARALLEL_THRESHOLD_MEDIUM,
        _ => PARALLEL_THRESHOLD_LARGE,
    }
}
```

## 3. Bindings層設計

### 3.1 型変換仕様

#### NumPy配列変換（ゼロコピー最適化）
```rust
// bindings/python/src/converters/numpy.rs
use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;

/// ゼロコピー実装（既存のBroadcastIterator設計を活用）
pub struct ArrayView<'a> {
    data: &'a [f64],
}

impl<'a> ArrayView<'a> {
    pub fn from_numpy(arr: &'a PyReadonlyArray1<f64>) -> Self {
        Self {
            data: arr.as_slice().unwrap(),
        }
    }
    
    pub fn len(&self) -> usize {
        self.data.len()
    }
    
    pub fn get(&self, idx: usize) -> f64 {
        self.data[idx]
    }
}

/// compute_withパターン（FFIオーバーヘッド40%削減済み）
pub fn compute_with_arrays<F, R>(
    py: Python,
    spots: PyReadonlyArray1<f64>,
    strikes: PyReadonlyArray1<f64>,
    times: PyReadonlyArray1<f64>,
    rates: PyReadonlyArray1<f64>,
    sigmas: PyReadonlyArray1<f64>,
    f: F,
) -> PyResult<R>
where
    F: FnOnce(&[f64], &[f64], &[f64], &[f64], &[f64]) -> R,
{
    py.allow_threads(|| {
        Ok(f(
            spots.as_slice()?,
            strikes.as_slice()?,
            times.as_slice()?,
            rates.as_slice()?,
            sigmas.as_slice()?,
        ))
    })
}
```

#### Broadcasting実装
```rust
// bindings/python/src/converters/broadcast.rs
use ndarray::prelude::*;

pub struct BroadcastIterator<'a> {
    arrays: Vec<ArrayView<'a>>,
    size: usize,
    current: usize,
}

impl<'a> BroadcastIterator<'a> {
    pub fn new(arrays: Vec<ArrayView<'a>>) -> Result<Self, &'static str> {
        let size = arrays.iter()
            .map(|a| a.len())
            .filter(|&len| len > 1)
            .max()
            .unwrap_or(1);
        
        // 検証: 長さは1またはsizeでなければならない
        for array in &arrays {
            if array.len() != 1 && array.len() != size {
                return Err("Array size mismatch for broadcasting");
            }
        }
        
        Ok(Self { arrays, size, current: 0 })
    }
    
    pub fn next_values(&mut self) -> Option<Vec<f64>> {
        if self.current >= self.size {
            return None;
        }
        
        let values: Vec<f64> = self.arrays.iter()
            .map(|array| {
                if array.len() == 1 {
                    array.get(0)
                } else {
                    array.get(self.current)
                }
            })
            .collect();
        
        self.current += 1;
        Some(values)
    }
}
```

### 3.2 エラーマッピング

```rust
// bindings/python/src/error.rs
use pyo3::prelude::*;
use pyo3::exceptions::{PyValueError, PyRuntimeError};
use quantforge_core::error::QuantForgeError;

impl From<QuantForgeError> for PyErr {
    fn from(err: QuantForgeError) -> PyErr {
        match err {
            QuantForgeError::InvalidInput(msg) => {
                // パラメータ名は省略形を使用
                PyValueError::new_err(msg)
            }
            QuantForgeError::NumericalError(msg) => {
                PyRuntimeError::new_err(format!("Numerical error: {}", msg))
            }
            QuantForgeError::ConvergenceError(msg) => {
                PyRuntimeError::new_err(format!("Convergence failed: {}", msg))
            }
            QuantForgeError::OutOfBounds(msg) => {
                PyValueError::new_err(format!("Out of bounds: {}", msg))
            }
        }
    }
}
```

### 3.3 メモリ管理方針

#### GIL管理
```rust
// bindings/python/src/gil.rs
use pyo3::prelude::*;

/// GILを適切にリリースして計算を実行
pub fn with_gil_released<F, R>(py: Python, f: F) -> R
where
    F: FnOnce() -> R + Send,
    R: Send,
{
    py.allow_threads(f)
}

/// バッチ処理時のGIL管理
pub fn process_batch_with_gil<F, T, R>(
    py: Python,
    data: Vec<T>,
    threshold: usize,
    f: F,
) -> Vec<R>
where
    F: Fn(&T) -> R + Send + Sync,
    T: Send + Sync,
    R: Send,
{
    if data.len() < threshold {
        // 小規模: GILを保持したまま処理
        data.iter().map(f).collect()
    } else {
        // 大規模: GILをリリースして並列処理
        py.allow_threads(|| {
            use rayon::prelude::*;
            data.par_iter().map(f).collect()
        })
    }
}
```

## 4. Python API設計

### 4.1 モジュール公開インターフェース

```python
# bindings/python/quantforge/__init__.py
"""QuantForge - High-performance option pricing library."""

from . import _internal

# モデルの公開
class models:
    """Option pricing models."""
    
    class black_scholes:
        """Black-Scholes model."""
        call_price = _internal.black_scholes_call_price
        put_price = _internal.black_scholes_put_price
        call_price_batch = _internal.black_scholes_call_price_batch
        put_price_batch = _internal.black_scholes_put_price_batch
        greeks = _internal.black_scholes_greeks
        greeks_batch = _internal.black_scholes_greeks_batch
        implied_volatility = _internal.black_scholes_implied_volatility
        implied_volatility_batch = _internal.black_scholes_implied_volatility_batch
    
    class black76:
        """Black76 model."""
        call_price = _internal.black76_call_price
        put_price = _internal.black76_put_price
        call_price_batch = _internal.black76_call_price_batch
        put_price_batch = _internal.black76_put_price_batch
        greeks = _internal.black76_greeks
        greeks_batch = _internal.black76_greeks_batch
        implied_volatility = _internal.black76_implied_volatility
        implied_volatility_batch = _internal.black76_implied_volatility_batch
    
    class merton:
        """Merton model with dividends."""
        call_price = _internal.merton_call_price
        put_price = _internal.merton_put_price
        call_price_batch = _internal.merton_call_price_batch
        put_price_batch = _internal.merton_put_price_batch
        greeks = _internal.merton_greeks
        greeks_batch = _internal.merton_greeks_batch
        implied_volatility = _internal.merton_implied_volatility
        implied_volatility_batch = _internal.merton_implied_volatility_batch
    
    class american:
        """American options model."""
        call_price = _internal.american_call_price
        put_price = _internal.american_put_price
        call_price_batch = _internal.american_call_price_batch
        put_price_batch = _internal.american_put_price_batch
        greeks = _internal.american_greeks
        greeks_batch = _internal.american_greeks_batch
        exercise_boundary = _internal.american_exercise_boundary
        exercise_boundary_batch = _internal.american_exercise_boundary_batch
        implied_volatility = _internal.american_implied_volatility
        implied_volatility_batch = _internal.american_implied_volatility_batch

__version__ = _internal.__version__
__all__ = ["models", "__version__"]
```

### 4.2 型スタブ定義

```python
# bindings/python/quantforge/py.typed
# PEP 561 marker file
```

```python
# bindings/python/quantforge/quantforge.pyi
from typing import Union, Dict, Any, overload
import numpy as np
from numpy.typing import ArrayLike

class models:
    class black_scholes:
        @staticmethod
        def call_price(s: float, k: float, t: float, r: float, sigma: float) -> float: ...
        
        @staticmethod
        def put_price(s: float, k: float, t: float, r: float, sigma: float) -> float: ...
        
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
        
        @staticmethod
        def greeks_batch(
            spots: ArrayLike,
            strikes: ArrayLike,
            times: ArrayLike,
            rates: ArrayLike,
            sigmas: ArrayLike,
            is_call: bool = True
        ) -> Dict[str, np.ndarray]: ...
    
    # 他のモデルも同様に定義
```

## 5. 移行設計

### 5.1 依存関係の分離

現在のPyO3依存箇所:
- `#[pyfunction]` マクロ: 183箇所
- `#[pyclass]` マクロ: 27箇所
- `PyResult` 型: 256箇所
- `Python` 引数: 312箇所

分離方針:
1. Core層: すべてのPyO3依存を除去
2. Bindings層: PyO3ラッパーとして再実装

### 5.2 テスト戦略

```
Core層テスト:
- Rust単体テスト（#[test]）
- Property-based testing（proptest）
- ベンチマーク（criterion）

Bindings層テスト:
- Python統合テスト（pytest）
- NumPy相互運用テスト
- GILリリース検証

E2Eテスト:
- ゴールデンマスター（95%カバレッジ済み）
- パフォーマンス回帰テスト（performance_guard.py）
```

## 6. 技術的決定事項

### 6.1 並列化戦略

- Rayon使用（既存実装を維持）
- 閾値は実測ベース（8,000、200,000、1,000,000）
- GILリリース時のみ並列化

### 6.2 数学関数実装

- norm_cdf: erfベース（高精度）
- norm_pdf: 直接計算
- erf: libm または statrs使用

### 6.3 メモリ最適化

- ゼロコピー（NumPy ↔ Rust）
- スライス参照の活用
- 中間アロケーション最小化

## 7. リスク対策

| リスク | 対策 |
|--------|------|
| PyO3分離の複雑性 | 段階的な抽出とテスト駆動開発 |
| パフォーマンス劣化 | performance_guard.pyによる継続的検証 |
| API非互換 | ゴールデンマスターテスト |
| メモリリーク | Valgrindによる検証 |