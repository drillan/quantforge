# 定型実装・コマンドパターン

## よく使うコマンド

### テスト実行パターン

```bash
# 全テスト実行と結果確認
uv run pytest -v 2>&1 | grep -E "failed|passed" | tail -1

# 失敗テストのみ確認
uv run pytest -v 2>&1 | grep FAILED

# 特定テストの詳細デバッグ
uv run pytest tests/path/to/test.py::TestClass::test_method -v --tb=long

# カバレッジ付きテスト
uv run pytest --cov=quantforge --cov-report=html
```

### Rust開発サイクル

```bash
# ビルドとテスト
cargo test --release
maturin develop --release

# 品質チェック
cargo clippy -- -D warnings
cargo fmt --check

# コード重複検出（追加: 2025-08-30）
similarity-rs --threshold 0.80 --min-lines 5 --skip-test src/
similarity-rs --threshold 0.85 --print src/ > duplication-report.md

# ベンチマーク
cargo bench --bench batch_performance
```

## リファクタリングパターン（追加: 2025-08-30）

### マクロによる重複削減

```rust
// バッチ処理の共通パターンをマクロ化
macro_rules! impl_batch_traits {
    ($model:ident, greeks => $greeks_fn:ident, iv => $iv_fn:ident, uses_q: $uses_q:expr) => {
        impl OptionModelBatch for $model {
            type Error = String;
            fn calculate_greeks_batch(params: BatchParams) -> Result<GreeksBatch, Self::Error> {
                batch_helpers::$greeks_fn(/* パラメータ */)
                    .map_err(|e| e.to_string())
            }
        }
        // 他のトレイトも同様
    };
}

// 使用例: 3行で全実装
impl_batch_traits!(
    BlackScholesBatch,
    greeks => greeks_batch_vec,
    iv => implied_volatility_batch_vec,
    uses_q: true
);
```

### PyO3バインディングの統一

```rust
// 汎用マクロでPython関数を生成
macro_rules! impl_batch_price_fn {
    ($fn_name:ident, $batch_fn:path, $doc:literal) => {
        #[doc = $doc]
        #[pyfunction]
        #[pyo3(name = stringify!($fn_name))]
        fn $fn_name<'py>(/* パラメータ */) -> PyResult<Bound<'py, PyArray1<f64>>> {
            // 共通の変換処理
            let results = $batch_fn(/* 引数 */)?;
            Ok(PyArray1::from_vec_bound(py, results))
        }
    };
}
```

### 動的実行戦略

```rust
// データサイズに応じた最適化
pub fn select_strategy(size: usize) -> ExecutionStrategy {
    match size {
        0..=1_000 => ExecutionStrategy::Sequential,
        1_001..=10_000 => ExecutionStrategy::SimdOnly,
        10_001..=50_000 => ExecutionStrategy::Parallel(4),
        _ => ExecutionStrategy::SimdParallel(num_cpus::get()),
    }
}
```

### Python品質管理

```bash
# フォーマットとリント
uv run ruff format .
uv run ruff check .
uv run ruff check --fix .  # 自動修正

# 型チェック
uv run mypy .
```

### ハードコード検出

```bash
# 浮動小数点数の検出
rg '\b\d*\.\d+\b' src/ tests/ --type rust --type python | grep -v "const\|TOLERANCE"

# 大きな整数の検出
rg '\b[1-9]\d{2,}\b' src/ tests/ --type rust --type python | grep -v "const\|MAX\|MIN"
```

## 実装パターン

### Rustテストヘルパー（ビルダーパターン）

```rust
struct TestOption {
    spot: f64,
    strike: f64,
    time: f64,
    rate: f64,
    vol: f64,
}

impl TestOption {
    fn atm() -> Self {
        Self {
            spot: 100.0,
            strike: 100.0,
            time: 1.0,
            rate: 0.05,
            vol: 0.2,
        }
    }
    
    fn with_spot(mut self, spot: f64) -> Self {
        self.spot = spot;
        self
    }
    
    fn price(&self) -> f64 {
        bs_call_price(self.spot, self.strike, self.time, self.rate, self.vol)
    }
    
    fn assert_price_near(&self, expected: f64, epsilon: f64) {
        let actual = self.price();
        assert_relative_eq!(actual, expected, epsilon = epsilon);
    }
}

// 使用例
TestOption::atm()
    .with_spot(110.0)
    .with_vol(0.3)
    .assert_price_near(15.0, PRACTICAL_TOLERANCE);
```

### 数値安定性の確保

```rust
// Deep OTMでの負値防止
pub fn bs_call_price(s: f64, k: f64, t: f64, r: f64, v: f64) -> f64 {
    let result = /* 計算 */;
    result.max(0.0)  // 物理的制約を明示的に適用
}

// NaNチェック
if !value.is_finite() {
    return Err("Invalid input: NaN or infinite");
}
```

### バリデーションパターン

```rust
// 入力検証の集約
fn validate_inputs(s: f64, k: f64, t: f64, r: f64, v: f64) -> Result<(), Error> {
    // スポット価格
    if s <= 0.0 || !s.is_finite() {
        return Err(Error::InvalidSpotPrice(s));
    }
    
    // 行使価格
    if k <= 0.0 || !k.is_finite() {
        return Err(Error::InvalidStrikePrice(k));
    }
    
    // 満期までの時間
    if t <= 0.0 || !t.is_finite() {
        return Err(Error::InvalidTimeToMaturity(t));
    }
    
    // ボラティリティ
    if v <= 0.0 || !v.is_finite() {
        return Err(Error::InvalidVolatility(v));
    }
    
    Ok(())
}
```

### 定数管理パターン

```rust
// src/constants.rs - 精度定数
pub const PRACTICAL_TOLERANCE: f64 = 1e-3;
pub const THEORETICAL_TOLERANCE: f64 = 1e-5;
pub const NUMERICAL_TOLERANCE: f64 = 1e-7;

// src/constants.rs - パフォーマンス定数（新規追加）
pub const L1_CACHE_SIZE: usize = 32 * 1024;  // 32KB
pub const L2_CACHE_SIZE: usize = 256 * 1024; // 256KB
pub const L3_CACHE_SIZE: usize = 8 * 1024 * 1024; // 8MB

pub const CHUNK_SIZE_L1: usize = L1_CACHE_SIZE / 8 / 4;  // 1024要素
pub const CHUNK_SIZE_L2: usize = L2_CACHE_SIZE / 8 / 4;  // 8192要素
pub const CHUNK_SIZE_L3: usize = L3_CACHE_SIZE / 8 / 4;  // 262144要素

pub const PARALLEL_THRESHOLD_SMALL: usize = 1000;
pub const PARALLEL_THRESHOLD_MEDIUM: usize = 10_000;
pub const PARALLEL_THRESHOLD_LARGE: usize = 100_000;

// アルゴリズム係数（使用箇所の近くで定義）
const NORM_CDF_UPPER_BOUND: f64 = 8.0;  // Φ(8) ≈ 1.0
```

### 動的並列化戦略パターン

```rust
use crate::optimization::ParallelStrategy;

// データサイズに基づく動的戦略選択
let strategy = ParallelStrategy::select(data.len());

// 汎用バッチ処理
let results = strategy.process_batch(&data, |item| {
    // 処理ロジック
    process_item(item)
});

// ゼロコピー処理（出力配列への直接書き込み）
strategy.process_into(&input, &mut output, |item| {
    calculate_value(item)
});

// スレッドプール制御付き処理
let results = strategy.process_with_pool_control(&data, |item| {
    heavy_computation(item)
});
```

### BatchProcessorパターン

```rust
// 基本プロセッサ実装（配当なし）
pub struct ModelCallProcessor;

impl BatchProcessor for ModelCallProcessor {
    type Params = ModelParams;
    type Output = f64;
    
    fn create_params(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        ModelParams::new(s, k, t, r, sigma)
    }
    
    fn process_single(&self, params: &Self::Params) -> Self::Output {
        Model::call_price(params)
    }
}

// 配当対応プロセッサ（Merton等）
impl BatchProcessorWithDividend for MertonCallProcessor {
    type ParamsWithDividend = MertonParams;
    
    fn create_params_with_dividend(
        &self, s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64
    ) -> Self::ParamsWithDividend {
        MertonParams::new_unchecked(s, k, t, r, q, sigma)
    }
    
    fn process_single_with_dividend(&self, params: &Self::ParamsWithDividend) -> Self::Output {
        MertonModel::call_price(params)
    }
}
```

### Pythonテストパターン

```python
# Hypothesisを使ったプロパティテスト
from hypothesis import given, strategies as st

@given(
    s=st.floats(min_value=0.01, max_value=10000),
    k=st.floats(min_value=0.01, max_value=10000),
    t=st.floats(min_value=0.001, max_value=30),
    r=st.floats(min_value=-0.5, max_value=0.5),
    v=st.floats(min_value=0.005, max_value=5.0),
)
def test_price_bounds(s, k, t, r, v):
    price = calculate_call_price(s, k, t, r, v)
    
    # 価格の物理的制約
    assert price >= 0
    assert price <= s
    
    # 本質的価値との関係
    intrinsic = max(s - k * np.exp(-r * t), 0)
    assert price >= intrinsic
```

### エラーメッセージの具体化

```rust
// 曖昧なエラー ❌
#[error("Invalid price: {0}")]
InvalidPrice(f64),

// 具体的なエラー ✅
#[error("Spot price must be positive, got {0}")]
InvalidSpotPrice(f64),

#[error("Strike price must be positive, got {0}")]
InvalidStrikePrice(f64),
```

## デバッグパターン

### 検証スクリプトの作成

```python
# playground/verify_価格.py
from quantforge import calculate_call_price
import numpy as np
from scipy import stats

# パラメータ
s, k, t, r, v = 100, 100, 1, 0.05, 0.2

# QuantForge計算
qf_price = calculate_call_price(s, k, t, r, v)

# SciPy理論値
d1 = (np.log(s/k) + (r + 0.5*v**2)*t) / (v*np.sqrt(t))
d2 = d1 - v*np.sqrt(t)
scipy_price = s * stats.norm.cdf(d1) - k * np.exp(-r*t) * stats.norm.cdf(d2)

print(f"QuantForge: {qf_price:.5f}")
print(f"SciPy理論値: {scipy_price:.5f}")
print(f"差異: {abs(qf_price - scipy_price):.2e}")
```

### プロファイリング

```bash
# Rustプロファイリング
cargo flamegraph --bench batch_performance

# Pythonプロファイリング
python -m cProfile -o profile.stats main.py
python -m pstats profile.stats
```

## CI/CD統合パターン

### GitHub Actions設定例

```yaml
- name: Rust品質チェック
  run: |
    cargo test --release
    cargo clippy -- -D warnings
    cargo fmt --check

- name: Python品質チェック
  run: |
    uv run ruff check .
    uv run mypy .
    uv run pytest --cov=quantforge

- name: ハードコード検出
  run: |
    ./scripts/detect_hardcode.sh
```

## ゼロコピー最適化パターン（2025-08-30追加）

### BroadcastIteratorの最適化パターン

```rust
// ❌ 旧実装：大量のメモリアロケーション
let values: Vec<_> = iter.collect();  // 各要素でVec<f64>作成
strategy.process_batch(&values, |vals| compute(vals));

// ✅ 新実装：ゼロコピー処理
let results = match strategy.mode() {
    ProcessingMode::Sequential => {
        // バッファ1つを再利用
        iter.compute_with(|vals| compute(vals))
    }
    _ => {
        // チャンクごとにバッファ（並列実行用）
        iter.compute_parallel_with(
            |vals| compute(vals),
            strategy.chunk_size()
        )
    }
};
```

### compute_withの実装パターン

```rust
impl<'a> BroadcastIterator<'a> {
    pub fn compute_with<F, R>(&self, f: F) -> Vec<R>
    where
        F: Fn(&[f64]) -> R,
        R: Send,
    {
        let mut buffer = vec![0.0; self.inputs.len()];
        let mut results = Vec::with_capacity(self.size);
        
        for i in 0..self.size {
            // バッファを再利用（アロケーションなし）
            for (j, input) in self.inputs.iter().enumerate() {
                buffer[j] = input.get_broadcast(i);
            }
            results.push(f(&buffer));
        }
        results
    }
}
```

### バッチ処理の統一実装パターン

```rust
// 各モデルのバッチ処理で共通パターン
pub fn call_price_batch(/* params */) -> Result<Vec<f64>, QuantForgeError> {
    let inputs = vec![spots, strikes, times, rates, sigmas];
    let iter = BroadcastIterator::new(inputs)?;
    let size = iter.size_hint().0;
    
    let strategy = ParallelStrategy::select(size);
    
    let results = match strategy.mode() {
        ProcessingMode::Sequential => {
            iter.compute_with(|vals| {
                compute_single_price(vals[0], vals[1], vals[2], vals[3], vals[4])
            })
        }
        _ => {
            iter.compute_parallel_with(
                |vals| compute_single_price(vals[0], vals[1], vals[2], vals[3], vals[4]),
                strategy.chunk_size()
            )
        }
    };
    
    Ok(results)
}

// 共通のヘルパー関数
#[inline(always)]
fn compute_single_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> f64 {
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        f64::NAN
    } else {
        let params = BlackScholesParams { spot: s, strike: k, time: t, rate: r, sigma };
        BlackScholes::call_price(&params)
    }
}
```

### パフォーマンステストパターン

```python
#!/usr/bin/env python3
"""ゼロコピー最適化の性能測定"""

import time
import numpy as np
from quantforge import models

def benchmark_zero_copy(size):
    # テストデータ準備
    np.random.seed(42)
    data = {
        'spots': np.random.uniform(90, 110, size),
        'strikes': np.random.uniform(95, 105, size),
        'times': np.random.uniform(0.1, 2.0, size),
        'rates': np.random.uniform(0.01, 0.05, size),
        'sigmas': np.random.uniform(0.15, 0.35, size)
    }
    
    # ウォームアップ（JIT最適化）
    _ = models.call_price_batch(**{k: v[:100] for k, v in data.items()})
    
    # 実測
    start = time.perf_counter()
    results = models.call_price_batch(**data)
    elapsed = time.perf_counter() - start
    
    return {
        'size': size,
        'time': elapsed,
        'throughput': size / elapsed,
        'us_per_op': elapsed * 1e6 / size
    }

# ベンチマーク実行
for size in [100, 1_000, 10_000, 100_000, 1_000_000]:
    metrics = benchmark_zero_copy(size)
    print(f"Size: {metrics['size']:,}")
    print(f"  Throughput: {metrics['throughput']:,.0f} ops/sec")
    print(f"  Per operation: {metrics['us_per_op']:.2f} μs")
```