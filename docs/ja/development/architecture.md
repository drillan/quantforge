# システムアーキテクチャ

QuantForgeの内部設計と実装詳細です。

## 全体構成

```{mermaid}
graph TB
    subgraph "Python Layer"
        PY[Python API]
        NP[NumPy Interface]
    end
    
    subgraph "Binding Layer"
        PYO3[PyO3 Bindings]
        MAT[Maturin Build]
    end
    
    subgraph "Rust Core"
        MODELS[Price Models]
        PARALLEL[Parallel Executor]
        MATH[Math Functions]
    end
    
    subgraph "Hardware"
        CPU[CPU]
        CACHE[Cache]
    end
    
    PY --> PYO3
    NP --> PYO3
    PYO3 --> MODELS
    MODELS --> PARALLEL
    MODELS --> MATH
    PARALLEL --> CPU
    MATH --> CACHE
```

## コンポーネント設計

### Python API層

```{code-block} python
:name: architecture-code-quantforge/__init__.py
:caption: quantforge/__init__.py

# quantforge/__init__.py
class QuantForgeAPI:
    """Pythonユーザー向けインターフェース"""
    
    def __init__(self):
        self._rust_core = _quantforge_rust
        self._config = Config()
    
    def calculate(self, spots, strikes, rate, vol, time, **kwargs):
        # 入力検証
        validated = self._validate_inputs(spots, strikes, rate, vol, time)
        
        # Rust関数呼び出し
        return self._rust_core.calculate_batch(validated)
```

### Rust コア層

```{code-block} rust
:name: architecture-code-src/lib.rs
:caption: src/lib.rs

// src/lib.rs
pub struct QuantForgeCore {
    parallel_executor: ParallelExecutor,
    memory_pool: MemoryPool,
}

impl QuantForgeCore {
    pub fn calculate(&self, params: &CalculationParams) -> Result<Vec<f64>> {
        // 戦略選択
        let strategy = self.select_strategy(params.size());
        
        match strategy {
            Strategy::Sequential => self.calculate_sequential(params),
            Strategy::Parallel => self.parallel_executor.calculate(params),
            Strategy::Hybrid => self.calculate_hybrid(params),
        }
    }
}
```

## メモリレイアウト

### データ構造

```{code-block} rust
:name: architecture-code-[repr(c)]
:caption: [repr(C)]

#[repr(C)]
pub struct OptionData {
    spot: f64,
    strike: f64,
    rate: f64,
    vol: f64,
    time: f64,
}

// メモリアラインメント
#[repr(align(64))]
pub struct AlignedBuffer {
    data: Vec<f64>,
}
```

### ゼロコピー設計

```rust
use numpy::PyReadonlyArray1;

#[pyfunction]
fn calculate_zero_copy(
    spots: PyReadonlyArray1<f64>,
) -> PyResult<Py<PyArray1<f64>>> {
    // NumPy配列を直接参照（コピーなし）
    let spots_slice = spots.as_slice()?;
    
    // 処理
    let results = process(spots_slice);
    
    // 結果もゼロコピーで返却
    Python::with_gil(|py| {
        Ok(PyArray1::from_vec(py, results).to_owned())
    })
}
```

## 並列処理アーキテクチャ

### 階層的並列化

```rust
pub enum ParallelStrategy {
    
    // レベル2: スレッド（タスクレベル並列）
    ThreadPool {
        num_threads: usize,
        chunk_size: usize,
    },
    
    // レベル3: ハイブリッド（複数レベルの並列化）
    Hybrid {
        num_threads: usize,
        chunk_strategy: String,
    },
}
```

### ワークスティーリング

```rust
use rayon::prelude::*;

pub fn parallel_calculate(data: &[f64]) -> Vec<f64> {
    data.par_chunks(1000)
        .flat_map(|chunk| {
            // 各チャンクを処理
            process(chunk)
        })
        .collect()
}
```

## エラーハンドリング

### 型安全なエラー

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum QuantForgeError {
    #[error("Invalid spot price: {0}")]
    InvalidSpot(f64),
    
    #[error("Convergence failed after {0} iterations")]
    ConvergenceFailed(usize),
    
}

// Result型エイリアス
pub type Result<T> = std::result::Result<T, QuantForgeError>;
```

## 最適化パイプライン

### コンパイル時最適化

```{code-block} rust
:name: architecture-code-section
:caption: 定数畳み込み

// 定数畳み込み
const SQRT_2PI: f64 = 2.5066282746310007;

// インライン展開
#[inline(always)]
fn fast_exp(x: f64) -> f64 {
    // テイラー展開による高速化
    if x.abs() < 0.5 {
        1.0 + x + x * x / 2.0 + x * x * x / 6.0
    } else {
        x.exp()
    }
}
```

### 実行時最適化

```{code-block} rust
:name: architecture-code-cpu
:caption: CPU機能の動的検出

// CPU機能の動的検出
fn select_implementation() -> fn(&[f64]) -> Vec<f64> {
    if is_x86_feature_detected!("avx512f") {
        calculate_avx512
    } else if is_x86_feature_detected!("avx2") {
        calculate_avx2
    } else {
        calculate_scalar
    }
}
```

## テストアーキテクチャ

### 多層テスト戦略

```{code-block} rust
:name: architecture-code-[cfg(test)]
:caption: [cfg(test)]

#[cfg(test)]
mod tests {
    // 単体テスト
    #[test]
    fn test_black_scholes() { ... }
    
    // 統合テスト
    #[test]
    fn test_python_binding() { ... }
    
    // プロパティベーステスト
    #[quickcheck]
    fn prop_put_call_parity(s: f64, k: f64) -> bool { ... }
    
    // ベンチマーク
    #[bench]
    fn bench_million_options(b: &mut Bencher) { ... }
}
```

## ビルドシステム

### Cargo.toml

```toml
[package]
name = "quantforge"
version = "0.1.0"

[lib]
name = "quantforge"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.20", features = ["extension-module"] }
numpy = "0.20"
rayon = "1.7"

[profile.release]
lto = true
codegen-units = 1
opt-level = 3
```

### pyproject.toml

```toml
[build-system]
requires = ["maturin>=1.0"]
build-backend = "maturin"

[tool.maturin]
features = ["pyo3/extension-module"]
python-source = "python"
```

## デプロイメントアーキテクチャ

### マルチプラットフォーム

```{code-block} yaml
:name: architecture-code-.github/workflows/build.yml
:caption: .github/workflows/build.yml

# .github/workflows/build.yml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python: ["3.12"]
    
steps:
  - uses: actions/setup-python@v4
  - uses: dtolnay/rust-toolchain@stable
  - run: pip install maturin
  - run: maturin build --release
```

## セキュリティ考慮事項

### メモリ安全性

- Rustの所有権システムによる保証
- `unsafe`ブロックの最小化
- Miriによる検証

### 入力検証

```rust
fn validate_inputs(spot: f64, strike: f64) -> Result<()> {
    if !spot.is_finite() || spot <= 0.0 {
        return Err(QuantForgeError::InvalidSpot(spot));
    }
    if !strike.is_finite() || strike <= 0.0 {
        return Err(QuantForgeError::InvalidStrike(strike));
    }
    Ok(())
}
```

## まとめ

QuantForgeのアーキテクチャは：
- **階層的設計**: 各層が明確な責任を持つ
- **ゼロコスト抽象化**: Rustの強みを活用
- **適応的最適化**: 実行時に最適な戦略を選択
- **型安全性**: コンパイル時にエラーを防ぐ