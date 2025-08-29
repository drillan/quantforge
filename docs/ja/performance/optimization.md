# 最適化ガイド

QuantForgeのパフォーマンスを最大化するための詳細な最適化手法です。

## 並列処理最適化

### Rayonによる並列化

8要素並列処理：

```{code-block} rust
:name: optimization-code-[cfg(target_feature-=-"avx2")]
:caption: [cfg(target_feature = "avx2")]

#[cfg(target_feature = "avx2")]
unsafe fn calculate_avx2(data: &[f64]) -> Vec<f64> {
    use std::arch::x86_64::*;
    
    let mut results = Vec::with_capacity(data.len());
    
    for chunk in data.chunks_exact(8) {
        let vec = _mm512_loadu_pd(chunk.as_ptr());
        // 並列演算
        let result = process_avx2(vec);
        _mm512_storeu_pd(results.as_mut_ptr(), result);
    }
    
    results
}
```

### CPU機能検出

```{warning}
このセクションで説明されている高度な最適化機能（戦略選択）は将来実装予定です。
現在は、内部的に並列化が自動的に適用されます。
```

```{code-block} python
:name: optimization-code-api
:caption: 将来的なAPI（現在は未実装）

# 将来的なAPI（現在は未実装）
# from quantforge import system_info
# 現在はQuantForgeが内部で自動的に並列化を適用
from quantforge.models import black_scholes
prices = black_scholes.call_price_batch(spots, 100, 1.0, 0.05, 0.2)
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
:name: optimization-code-section
:caption: 事前確保された配列への直接書き込み

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
:name: optimization-code-bad
:caption: Bad

# Bad
spots = [100, 105, 110]  # 内部で変換が発生
```

2. **小さすぎる/大きすぎるバッチ**
```{code-block} python
:name: optimization-code-bad
:caption: Bad: オーバーヘッドが大きい

# Bad: オーバーヘッドが大きい
for spot in spots:
    from quantforge.models import black_scholes
    price = black_scholes.call_price(spot, 100, 1.0, 0.05, 0.2)
```

3. **頻繁な型変換**
```{code-block} python
:name: optimization-code-bad
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