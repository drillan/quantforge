# 最適化ガイド

QuantForgeのパフォーマンスを最大化するための詳細な最適化手法です。

## 並列処理最適化

### 動的並列化戦略

QuantForgeは、データサイズに基づいて最適な並列化戦略を自動的に選択します：

```{code-block} rust
:name: optimization-parallel-strategy
:caption: 動的並列化戦略の自動選択

// ParallelStrategyによる自動最適化
pub fn process_batch(data: &[f64]) -> Vec<f64> {
    let strategy = ParallelStrategy::select(data.len());
    
    match strategy {
        ProcessingMode::Sequential => {
            // 小規模データ（<1,000要素）は逐次処理
            process_sequential(data)
        }
        ProcessingMode::CacheOptimizedL1 => {
            // 1,000-10,000要素はL1キャッシュ最適化
            process_with_cache_optimization(data, L1_CACHE_SIZE)
        }
        ProcessingMode::FullParallel => {
            // 大規模データは完全並列化
            data.par_iter().map(process_single).collect()
        }
        _ => process_hybrid(data)
    }
}
```

### 最適化の閾値

| データサイズ | 処理戦略 | 特徴 |
|------------|---------|------|
| 0-1,000 | Sequential | オーバーヘッド回避 |
| 1,001-10,000 | CacheOptimizedL1 | L1キャッシュ効率最大化 |
| 10,001-100,000 | CacheOptimizedL2 | L2キャッシュ活用 |
| 100,001-1,000,000 | FullParallel | Rayonによる完全並列 |
| 1,000,000+ | HybridParallel | 複数レベル最適化 |

### Rayonによる並列化

大規模データセットでは、Rayonのワークスティーリングアルゴリズムが自動的に適用されます：

```{code-block} rust
:name: optimization-rayon-parallel
:caption: Rayonによる自動並列化

use rayon::prelude::*;

// 10,000要素以上で自動的に並列化
pub fn parallel_process(values: &[[f64; 5]]) -> Vec<f64> {
    if values.len() >= PARALLELIZATION_THRESHOLD {
        values.par_iter()
            .map(|vals| calculate_price(vals))
            .collect()
    } else {
        values.iter()
            .map(|vals| calculate_price(vals))
            .collect()
    }
}
```

### Python APIでの利用

```{code-block} python
:name: optimization-python-api
:caption: 自動最適化されるバッチ処理

from quantforge.models import black_scholes
import numpy as np

# データサイズに応じて自動的に最適な戦略が選択される
small_batch = np.array([100, 101, 102])  # Sequential処理
medium_batch = np.random.uniform(90, 110, 5000)  # Cache最適化
large_batch = np.random.uniform(90, 110, 500000)  # 完全並列化

# すべて同じAPIで、内部的に最適化される
prices_small = black_scholes.call_price_batch(small_batch, 100, 1.0, 0.05, 0.2)
prices_medium = black_scholes.call_price_batch(medium_batch, 100, 1.0, 0.05, 0.2)
prices_large = black_scholes.call_price_batch(large_batch, 100, 1.0, 0.05, 0.2)
```

## マイクロバッチ最適化

### 4要素ループアンローリング

100-1000要素の小規模バッチに対して、特別な最適化を実装しています：

```{code-block} rust
:name: optimization-micro-batch
:caption: マイクロバッチ専用最適化

// 4要素単位で処理（コンパイラの自動ベクトル化を促進）
pub fn black_scholes_call_micro_batch(
    spots: &[f64],
    strikes: &[f64],
    times: &[f64],
    rates: &[f64],
    sigmas: &[f64],
    output: &mut [f64],
) {
    let len = spots.len();
    let chunks = len / 4;

    // 4要素ループアンローリング
    for i in 0..chunks {
        let idx = i * 4;
        output[idx] = black_scholes_call_scalar(
            spots[idx], strikes[idx], times[idx], 
            rates[idx], sigmas[idx]
        );
        output[idx + 1] = black_scholes_call_scalar(
            spots[idx + 1], strikes[idx + 1], times[idx + 1],
            rates[idx + 1], sigmas[idx + 1]
        );
        output[idx + 2] = black_scholes_call_scalar(
            spots[idx + 2], strikes[idx + 2], times[idx + 2],
            rates[idx + 2], sigmas[idx + 2]
        );
        output[idx + 3] = black_scholes_call_scalar(
            spots[idx + 3], strikes[idx + 3], times[idx + 3],
            rates[idx + 3], sigmas[idx + 3]
        );
    }

    // 余りを処理
    for i in (chunks * 4)..len {
        output[i] = black_scholes_call_scalar(
            spots[i], strikes[i], times[i], rates[i], sigmas[i]
        );
    }
}
```

この最適化により：
- **命令レベル並列性（ILP）** の向上
- **コンパイラの自動ベクトル化** を促進
- **分岐予測** の効率化
- **キャッシュライン** の有効活用

### マイクロバッチの閾値

```rust
// MICRO_BATCH_THRESHOLD: 1000要素以下でマイクロバッチ最適化を適用
if data.len() <= MICRO_BATCH_THRESHOLD {
    black_scholes_call_micro_batch(/* ... */);
} else {
    // 通常の並列処理
}
```

## メモリ最適化

### アラインメント

64バイト境界へのアラインメント：

```python
import numpy as np

# アラインメントされた配列
def create_aligned_array(size, alignment=64):
    dtype = np.float64
    itemsize = np.dtype(dtype).itemsize
    buf = np.empty(size * itemsize + alignment, dtype=np.uint8)
    offset = (-buf.ctypes.data) % alignment
    return np.frombuffer(buf[offset:offset+size*itemsize], dtype=dtype)

# 使用例
aligned_data = create_aligned_array(1_000_000)
```

### キャッシュ最適化

```{code-block} python
:name: optimization-code-l2
:caption: 最適なバッチサイズ（L2キャッシュに収まる）

# 最適なバッチサイズ（L2キャッシュに収まる）
OPTIMAL_BATCH = 50_000

def process_large_dataset(data):
    results = []
    for i in range(0, len(data), OPTIMAL_BATCH):
        batch = data[i:i+OPTIMAL_BATCH]
        from quantforge.models import black_scholes
        results.append(black_scholes.call_price_batch(batch, 100, 1.0, 0.05, 0.2))
    return np.concatenate(results)
```

## 並列処理最適化

### スレッド数調整

```python
import os

# 物理コア数に合わせる
os.environ["RAYON_NUM_THREADS"] = str(os.cpu_count() // 2)

# NumPyスレッドを無効化（QuantForge側で並列化）
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
```

### ワークロード分散

```{code-block} python
:name: optimization-code-optimal_parallel_strategy
:caption: optimal_parallel_strategy

def optimal_parallel_strategy(data_size):
    """データサイズに基づく最適戦略"""
    if data_size < 1_000:
        return "sequential"
    elif data_size < 10_000:
        return "parallel_2"
    elif data_size < 100_000:
        return "parallel_4"
    else:
        return "parallel_auto"

# 将来的な戦略選択（現在は内部で自動最適化）
strategy = optimal_parallel_strategy(len(data))
# 注：set_compute_strategy APIは将来実装予定
```

## インプレース操作

### メモリ割り当て削減

```{code-block} python
:name: optimization-code-preallocated-arrays
:caption: 事前確保された配列への直接書き込み
:linenos:

# 事前確保された配列への直接書き込み
n = 1_000_000
results = np.empty(n)

# 将来的なインプレース操作（現在は未実装）
# qf.calculate_inplace(
#     spots=spots,
#     strikes=100,
#     rate=0.05,
#     vol=0.2,
#     time=1.0,
#     out=results  # 結果を直接書き込み
# )

# 現在は以下のように使用
from quantforge.models import black_scholes
results = black_scholes.call_price_batch(spots, 100, 1.0, 0.05, 0.2)
```

## プロファイリング

### パフォーマンス測定

```python
import cProfile
import pstats

def profile_code():
    # プロファイル対象コード
    spots = np.random.uniform(90, 110, 1_000_000)
    from quantforge.models import black_scholes
    prices = black_scholes.call_price_batch(spots, 100, 1.0, 0.05, 0.2)
    return prices

# プロファイル実行
cProfile.run('profile_code()', 'profile_stats')

# 結果分析
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### ボトルネック特定

```python
import time

class Timer:
    def __init__(self):
        self.times = {}
    
    def __call__(self, label):
        return self.TimerContext(self, label)
    
    class TimerContext:
        def __init__(self, timer, label):
            self.timer = timer
            self.label = label
        
        def __enter__(self):
            self.start = time.perf_counter()
        
        def __exit__(self, *args):
            elapsed = time.perf_counter() - self.start
            self.timer.times[self.label] = elapsed

timer = Timer()

with timer("data_prep"):
    data = np.random.uniform(90, 110, 1_000_000)

with timer("calculation"):
    from quantforge.models import black_scholes
    results = black_scholes.call_price_batch(data, 100, 1.0, 0.05, 0.2)

for label, elapsed in timer.times.items():
    print(f"{label}: {elapsed*1000:.2f}ms")
```

## 高速数学関数

### 高速erf近似実装

Abramowitz & Stegun近似を使用した高速erf実装により、norm_cdf計算を大幅に高速化：

```{code-block} rust
:name: optimization-fast-erf
:caption: 高速erf近似（Abramowitz & Stegun）

/// 高速erf近似
/// 精度: 1.5e-7（金融計算には十分）
/// 速度: libm::erfの2-3倍高速
#[inline(always)]
pub fn fast_erf(x: f64) -> f64 {
    // Abramowitz & Stegun係数
    let a1 = 0.254829592;
    let a2 = -0.284496736;
    let a3 = 1.421413741;
    let a4 = -1.453152027;
    let a5 = 1.061405429;
    let p = 0.3275911;

    let sign = if x < 0.0 { -1.0 } else { 1.0 };
    let x = x.abs();

    let t = 1.0 / (1.0 + p * x);
    let y = 1.0 - (((((a5 * t + a4) * t + a3) * t + a2) * t + a1) 
            * t * (-x * x).exp());

    sign * y
}

/// 高速norm_cdf実装
#[inline(always)]
pub fn fast_norm_cdf(x: f64) -> f64 {
    if x > NORM_CDF_UPPER_BOUND {
        1.0
    } else if x < NORM_CDF_LOWER_BOUND {
        0.0
    } else {
        0.5 * (1.0 + fast_erf(x / std::f64::consts::SQRT_2))
    }
}
```

### パフォーマンス特性

| 関数 | 従来実装 | 高速実装 | 改善率 |
|------|----------|----------|--------|
| erf | libm::erf | fast_erf | 2-3倍 |
| norm_cdf | erf依存 | fast_norm_cdf | 2-3倍 |
| norm_pdf | 変更なし | fast_norm_pdf | - |

### 精度とトレードオフ

- **絶対誤差**: < 1.5e-7
- **相対誤差**: < 1e-6
- **用途**: オプション価格計算には十分な精度
- **注意**: 科学計算や高精度要求時は標準実装を使用

## コンパイラ最適化

### Rust側の最適化

```{code-block} toml
:name: optimization-code-cargo.toml
:caption: Cargo.toml

# Cargo.toml
[profile.release]
opt-level = 3
lto = true
codegen-units = 1
panic = "abort"
strip = true

[profile.release.build-override]
opt-level = 3
```

### CPU固有の最適化

```{code-block} bash
:name: optimization-code-cpu
:caption: ターゲットCPU向けビルド

# ターゲットCPU向けビルド
RUSTFLAGS="-C target-cpu=native" maturin build --release
```

## ベストプラクティス

### Do's ✅

1. **NumPy配列を使用**
```{code-block} python
:name: optimization-code-good
:caption: Good

# Good
spots = np.array([100, 105, 110])
from quantforge.models import black_scholes
prices = black_scholes.call_price_batch(spots, 100, 1.0, 0.05, 0.2)
```

2. **適切なバッチサイズ**
```{code-block} python
:name: optimization-code-good-10000-100000
:caption: Good: 10,000-100,000要素

# Good: 10,000-100,000要素
batch_size = 50_000
```

3. **型の統一**
```{code-block} python
:name: optimization-code-good-float64
:caption: Good: float64で統一

# Good: float64で統一
data = data.astype(np.float64)
```

### Don'ts ❌

1. **Python リストの使用**
```{code-block} python
:name: optimization-code-bad-list
:caption: Bad

# Bad
spots = [100, 105, 110]  # 内部で変換が発生
```

2. **小さすぎる/大きすぎるバッチ**
```{code-block} python
:name: optimization-code-bad-batch
:caption: Bad: オーバーヘッドが大きい

# Bad: オーバーヘッドが大きい
for spot in spots:
    from quantforge.models import black_scholes
    price = black_scholes.call_price(spot, 100, 1.0, 0.05, 0.2)
```

3. **頻繁な型変換**
```{code-block} python
:name: optimization-code-bad-conversion
:caption: Bad

# Bad
data = data.astype(np.float32)  # 変換が発生
```

## まとめ

最適化の優先順位：
1. **アルゴリズム選択**: 適切なモデルを選ぶ
2. **データ構造**: NumPy配列、適切なレイアウト
3. **バッチ処理**: 適切なサイズでまとめて処理
4. **並列化**: データ量に応じた戦略
5. **並列化**: マルチコアを最大限活用