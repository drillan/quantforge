# Rust API リファレンス

QuantForgeのコアとなるRust実装のAPIドキュメントです。

## モジュール構成

```rust
use quantforge::{
    models::{BlackScholes, American, Asian},
    greeks::Greeks,
    parallel::ParallelExecutor,
};
```

## コア価格計算

### Black-Scholesモデル

```rust
pub fn black_scholes_call(
    spot: f64,
    strike: f64,
    rate: f64,
    vol: f64,
    time: f64,
) -> f64
```

**並列処理版:**

```rust
pub fn black_scholes_call_batch(
    spots: &[f64],
    strikes: &[f64],
    rate: f64,
    vol: f64,
    time: f64,
) -> Vec<f64>
```

### アメリカンオプション

```rust
pub struct AmericanOption {
    spot: f64,
    strike: f64,
    rate: f64,
    vol: f64,
    time: f64,
    dividend: f64,
}

impl AmericanOption {
    pub fn call_price(&self) -> f64 {
        // Bjerksund-Stensland 2002実装
    }
    
    pub fn put_price(&self) -> f64 {
        // プット変換による計算
    }
    
    pub fn early_exercise_boundary(&self) -> f64 {
        // 早期行使境界
    }
}
```

## 並列処理最適化

### Rayon実装

```rust
use rayon::prelude::*;

pub fn black_scholes_parallel(
    spots: &[f64],
    strikes: &[f64],
    rate: f64,
    vol: f64,
    time: f64,
) -> Vec<f64> {
    spots.par_iter()
        .zip(strikes.par_iter())
        .map(|(&s, &k)| {
            black_scholes_call(s, k, rate, vol, time)
        })
        .collect()
}
```

### 高度な並列化

```{code-block} rust
:name: index-code-[cfg(target_feature-=-"avx512f")]
:caption: [cfg(target_feature = "avx512f")]

#[cfg(target_feature = "avx512f")]
pub mod avx512 {
    pub unsafe fn black_scholes_avx512(
        spots: &[f64],
        strikes: &[f64],
        rate: f64,
        vol: f64,
        time: f64,
    ) -> Vec<f64> {
        // 16要素並列処理
    }
}
```

## 並列処理

### Rayonによる並列化

```rust
use rayon::prelude::*;

pub fn parallel_calculate(
    spots: &[f64],
    strikes: &[f64],
    rate: f64,
    vol: f64,
    time: f64,
) -> Vec<f64> {
    spots
        .par_iter()
        .zip(strikes.par_iter())
        .map(|(&s, &k)| black_scholes_call(s, k, rate, vol, time))
        .collect()
}
```

### 適応的並列化

```rust
pub enum ComputeStrategy {
    Sequential,
    SimdOnly,
    Parallel(usize),
    HybridSimdParallel,
}

impl ComputeStrategy {
    pub fn auto_select(data_size: usize) -> Self {
        match data_size {
            0..=1000 => ComputeStrategy::Sequential,
            1001..=10_000 => ComputeStrategy::SimdOnly,
            10_001..=100_000 => ComputeStrategy::Parallel(4),
            _ => ComputeStrategy::HybridSimdParallel,
        }
    }
}
```

## グリークス計算

### Greeks構造体

```{code-block} rust
:name: index-code-[derive(debug,-clone,-copy)]
:caption: [derive(Debug, Clone, Copy)]

#[derive(Debug, Clone, Copy)]
pub struct Greeks {
    pub delta: f64,
    pub gamma: f64,
    pub vega: f64,
    pub theta: f64,
    pub rho: f64,
}

impl Greeks {
    pub fn calculate(
        spot: f64,
        strike: f64,
        rate: f64,
        vol: f64,
        time: f64,
        option_type: OptionType,
    ) -> Self {
        // 全グリークス計算
    }
}
```

### 有限差分法

```rust
pub fn delta_finite_difference(
    spot: f64,
    strike: f64,
    rate: f64,
    vol: f64,
    time: f64,
    h: f64,
) -> f64 {
    let price_up = black_scholes_call(spot + h, strike, rate, vol, time);
    let price_down = black_scholes_call(spot - h, strike, rate, vol, time);
    (price_up - price_down) / (2.0 * h)
}
```

## メモリ管理

### ゼロコピーインターフェース

```rust
use ndarray::{ArrayView1, ArrayViewMut1};

pub fn calculate_inplace(
    spots: ArrayView1<f64>,
    strikes: ArrayView1<f64>,
    rate: f64,
    vol: f64,
    time: f64,
    mut out: ArrayViewMut1<f64>,
) {
    // 直接書き込み
    for i in 0..spots.len() {
        out[i] = black_scholes_call(spots[i], strikes[i], rate, vol, time);
    }
}
```

### アラインメント最適化

```{code-block} rust
:name: index-code-[repr(align(64))]
:caption: [repr(align(64))]

#[repr(align(64))]
pub struct AlignedBuffer<T> {
    data: Vec<T>,
}

impl<T> AlignedBuffer<T> {
    pub fn new(size: usize) -> Self {
        let mut data = Vec::with_capacity(size);
        data.resize_with(size, Default::default);
        Self { data }
    }
}
```

## エラー処理

### カスタムエラー型

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum QuantForgeError {
    #[error("Invalid input: {0}")]
    InvalidInput(String),
    
    #[error("Convergence failed after {iterations} iterations")]
    ConvergenceFailed { iterations: usize },
    
    #[error("Numerical overflow")]
    Overflow,
    
    #[error("Memory allocation failed")]
    MemoryError,
}

pub type Result<T> = std::result::Result<T, QuantForgeError>;
```

### 入力検証

```rust
pub fn validate_inputs(
    spot: f64,
    strike: f64,
    rate: f64,
    vol: f64,
    time: f64,
) -> Result<()> {
    if spot <= 0.0 {
        return Err(QuantForgeError::InvalidInput(
            "Spot price must be positive".into()
        ));
    }
    if vol < 0.0 {
        return Err(QuantForgeError::InvalidInput(
            "Volatility cannot be negative".into()
        ));
    }
    // その他の検証...
    Ok(())
}
```

## ベンチマーク

### Criterionによるベンチマーク

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn benchmark_black_scholes(c: &mut Criterion) {
    c.bench_function("black_scholes_single", |b| {
        b.iter(|| {
            black_scholes_call(
                black_box(100.0),
                black_box(105.0),
                black_box(0.05),
                black_box(0.2),
                black_box(1.0),
            )
        })
    });
}

criterion_group!(benches, benchmark_black_scholes);
criterion_main!(benches);
```

## Bindings層（PyO3）

### Core層とBindings層の分離

```rust
// core/src/models/black_scholes.rs - PyO3依存なし
pub struct BlackScholes;

impl OptionModel for BlackScholes {
    fn call_price(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) 
        -> QuantForgeResult<f64> {
        // 純粋なRust実装
    }
}

// bindings/python/src/models/black_scholes.rs - PyO3依存あり
use pyo3::prelude::*;
use quantforge_core::models::black_scholes::BlackScholes;
use quantforge_core::traits::OptionModel;

#[pyfunction]
fn call_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    let model = BlackScholes;
    model.call_price(s, k, t, r, sigma)
        .map_err(to_py_err)
}

#[pymodule]
fn quantforge(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(call_price, m)?)?;
    Ok(())
}
```

## 最適化フラグ

### コンパイル時最適化

```{code-block} toml
:name: index-code-cargo.toml
:caption: Cargo.toml

# Cargo.toml
[profile.release]
opt-level = 3
lto = true
codegen-units = 1
panic = "abort"

[target.'cfg(target_arch = "x86_64")'.dependencies]
packed_simd_2 = "0.3"
```

### CPU機能検出

```rust
pub fn detect_cpu_features() -> CpuFeatures {
    CpuFeatures {
        has_avx2: is_x86_feature_detected!("avx2"),
        has_avx512f: is_x86_feature_detected!("avx512f"),
        has_fma: is_x86_feature_detected!("fma"),
    }
}
```

## テスト

### 単体テスト

```{code-block} rust
:name: index-code-[cfg(test)]
:caption: [cfg(test)]

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;
    
    #[test]
    fn test_black_scholes_call() {
        let price = black_scholes_call(100.0, 105.0, 0.05, 0.2, 1.0);
        assert_relative_eq!(price, 6.0399, epsilon = 1e-4);
    }
    
    #[test]
    fn test_put_call_parity() {
        let call = black_scholes_call(100.0, 100.0, 0.05, 0.2, 1.0);
        let put = black_scholes_put(100.0, 100.0, 0.05, 0.2, 1.0);
        let parity = call - put;
        let theoretical = 100.0 - 100.0 * (-0.05_f64).exp();
        assert_relative_eq!(parity, theoretical, epsilon = 1e-10);
    }
}
```

### プロパティベーステスト

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_price_positive(
        spot in 0.1..1000.0,
        strike in 0.1..1000.0,
        rate in -0.1..0.5,
        vol in 0.01..2.0,
        time in 0.01..10.0,
    ) {
        let price = black_scholes_call(spot, strike, rate, vol, time);
        prop_assert!(price >= 0.0);
        prop_assert!(price <= spot);
    }
}
```