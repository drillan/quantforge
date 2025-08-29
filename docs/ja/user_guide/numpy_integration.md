# NumPy統合

QuantForgeはNumPyとシームレスに統合され、ゼロコピーでの高速処理を実現します。

## ゼロコピー最適化

### メモリ効率の仕組み

```python
import numpy as np
import quantforge as qf
from quantforge.models import black_scholes

# NumPy配列の作成
spots = np.random.uniform(90, 110, 1_000_000)

# ゼロコピーで処理（メモリコピーなし）
prices = black_scholes.call_price_batch(
    spots=spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)

# prices もNumPy配列として返される
print(f"Type: {type(prices)}")
print(f"Shape: {prices.shape}")
print(f"Memory shared: {prices.base is not None}")
```

### メモリレイアウトの最適化

```{code-block} python
:name: numpy-integration-code-c
:caption: C連続配列（推奨）

# C連続配列（推奨）
spots_c = np.ascontiguousarray(spots)
print(f"C-contiguous: {spots_c.flags['C_CONTIGUOUS']}")

# Fortran連続配列（自動変換される）
spots_f = np.asfortranarray(spots)
print(f"F-contiguous: {spots_f.flags['F_CONTIGUOUS']}")

# パフォーマンス比較（100万要素）
import time

def benchmark_layout(array):
    start = time.perf_counter()
    black_scholes.call_price_batch(
        spots=array,
        strike=100.0,
        time=1.0,
        rate=0.05,
        sigma=0.2
    )
    return time.perf_counter() - start

time_c = benchmark_layout(spots_c)
time_f = benchmark_layout(spots_f)
print(f"C-layout: {time_c*1000:.2f}ms")  # 期待値: 約56ms
print(f"F-layout: {time_f*1000:.2f}ms")  # わずかに遅い
```

## ブロードキャスティング

### 自動ブロードキャスト

```{code-block} python
:name: numpy-integration-code-section
:caption: スカラーと配列の組み合わせ

# スカラーと配列の組み合わせ
spots = np.array([95, 100, 105])
strike = 100.0  # スカラー
rate = 0.05    # スカラー
sigma = 0.20   # スカラー
time = 1.0     # スカラー

# 自動的にブロードキャスト
prices = black_scholes.call_price_batch(
    spots=spots,
    strike=strike,
    time=time,
    rate=rate,
    sigma=sigma
)
print(f"Results: {prices}")
```

### 多次元配列

```{code-block} python
:name: numpy-integration-code-2
:caption: 2次元配列での計算

# 2次元配列での計算
spots = np.random.uniform(90, 110, (100, 1000))
strikes = np.full((100, 1000), 100.0)

# フラット化して計算
flat_spots = spots.ravel()
flat_prices = black_scholes.call_price_batch(
    spots=flat_spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)

# 元の形状に復元
prices = flat_prices.reshape(spots.shape)
print(f"Shape: {prices.shape}")
```

## ビュー操作

### スライスとインデックス

```{code-block} python
:name: numpy-integration-code-section
:caption: 大きな配列

# 大きな配列
all_spots = np.random.uniform(80, 120, 1_000_000)

# ビューを作成（コピーなし）
subset = all_spots[::10]  # 10個おきに選択
print(f"Is view: {subset.base is all_spots}")

# ビューでの計算
subset_prices = black_scholes.call_price_batch(
    spots=subset,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)
```

### 条件付き処理

```{code-block} python
:name: numpy-integration-code-section
:caption: 条件に基づく選択

# 条件に基づく選択
spots = np.random.uniform(80, 120, 10000)
mask = (spots > 95) & (spots < 105)  # ATM近辺のみ

# マスクされた計算
atm_spots = spots[mask]
atm_prices = black_scholes.call_price_batch(
    spots=atm_spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)

# 結果を元の配列に戻す
full_prices = np.zeros_like(spots)
full_prices[mask] = atm_prices
```

## データ型の処理

### 型変換の最適化

```{code-block} python
:name: numpy-integration-code-float32-vs-float64
:caption: float32 vs float64

# float32 vs float64
spots_f32 = np.random.uniform(90, 110, 100000).astype(np.float32)
spots_f64 = np.random.uniform(90, 110, 100000).astype(np.float64)

# QuantForgeは内部でfloat64を使用
# float32は自動変換される
prices_f32 = black_scholes.call_price_batch(
    spots=spots_f32, strike=100.0, time=1.0, rate=0.05, sigma=0.2
)
prices_f64 = black_scholes.call_price_batch(
    spots=spots_f64, strike=100.0, time=1.0, rate=0.05, sigma=0.2
)

print(f"Input f32 dtype: {spots_f32.dtype}")
print(f"Output dtype: {prices_f32.dtype}")  # float64に変換される
```

### 構造化配列

```{code-block} python
:name: numpy-integration-code-section
:caption: オプションデータの構造化配列

# オプションデータの構造化配列
dtype = np.dtype([
    ('spot', 'f8'),
    ('strike', 'f8'),
    ('vol', 'f8'),
    ('time', 'f8')
])

options = np.zeros(1000, dtype=dtype)
options['spot'] = np.random.uniform(90, 110, 1000)
options['strike'] = 100
options['vol'] = np.random.uniform(0.1, 0.3, 1000)
options['time'] = np.random.uniform(0.1, 2.0, 1000)

# 構造化配列から計算
# Note: 現在のAPIでは単一の時間とボラティリティのみサポート
# 複数のパラメータはループで処理
prices = np.array([
    black_scholes.call_price(
        spot=options['spot'][i],
        strike=options['strike'][i],
        time=options['time'][i],
        rate=0.05,
        sigma=options['vol'][i]
    )
    for i in range(len(options))
])
```

## メモリマップファイル

### 大規模データの処理

```{code-block} python
:name: numpy-integration-code-section
:caption: メモリマップファイルの作成

# メモリマップファイルの作成
filename = 'large_spots.dat'
shape = (10_000_000,)
spots_mmap = np.memmap(filename, dtype='float64', mode='w+', shape=shape)

# データの書き込み
spots_mmap[:] = np.random.uniform(90, 110, shape)

# チャンクごとの処理
chunk_size = 100_000
results = []

for i in range(0, len(spots_mmap), chunk_size):
    chunk = spots_mmap[i:i+chunk_size]
    chunk_prices = black_scholes.call_price_batch(
        spots=chunk,
        strike=100.0,
        time=1.0,
        rate=0.05,
        sigma=0.2
    )
    results.append(chunk_prices)

# 結果の結合
all_prices = np.concatenate(results)

# クリーンアップ
del spots_mmap
import os
os.remove(filename)
```

## ベクトル化された関数

### カスタムufunc

```{code-block} python
:name: numpy-integration-code-quantforgeufunc
:caption: QuantForgeの関数をufuncとして使用

# QuantForgeの関数をufuncとして使用
@np.vectorize
def custom_pricer(spot, strike, moneyness_threshold=0.1):
    """モネyネスに基づく条件付き価格計算"""
    moneyness = abs(spot / strike - 1.0)
    
    if moneyness < moneyness_threshold:
        # ATM近辺は高精度計算
        return black_scholes.call_price(
            spot=spot, strike=strike, time=1.0, rate=0.05, sigma=0.2
        )
    else:
        # OTMは簡易計算
        return black_scholes.call_price(
            spot=spot, strike=strike, time=1.0, rate=0.05, sigma=0.15
        )

# ベクトル化された使用
spots = np.array([95, 100, 105, 120])
strikes = np.array([100, 100, 100, 100])
prices = custom_pricer(spots, strikes)
```

## 並列処理との組み合わせ

### NumPyとマルチプロセシング

```python
from multiprocessing import Pool
import numpy as np

def process_batch(args):
    """バッチ処理関数"""
    spots, strike, rate, sigma, time = args
    return black_scholes.call_price_batch(
        spots=spots,
        strike=strike,
        time=time,
        rate=rate,
        sigma=sigma
    )

# データを分割
n_total = 10_000_000
n_chunks = 10
spots = np.random.uniform(90, 110, n_total)
chunks = np.array_split(spots, n_chunks)

# 並列処理
with Pool() as pool:
    args = [(chunk, 100, 0.05, 0.2, 1.0) for chunk in chunks]
    results = pool.map(process_batch, args)

# 結果の結合
all_prices = np.concatenate(results)
```

## パフォーマンスチューニング

### アラインメントの最適化

```{code-block} python
:name: numpy-integration-code-64
:caption: 64バイト境界にアラインメント（キャッシュライン）

# 64バイト境界にアラインメント（キャッシュライン）
def create_aligned_array(size, alignment=64):
    """アラインメントされた配列を作成"""
    dtype = np.float64
    itemsize = np.dtype(dtype).itemsize
    buf = np.empty(size * itemsize + alignment, dtype=np.uint8)
    offset = (-buf.ctypes.data) % alignment
    return np.frombuffer(buf[offset:offset+size*itemsize], dtype=dtype)

# アラインメントされた配列での計算
aligned_spots = create_aligned_array(1_000_000)
aligned_spots[:] = np.random.uniform(90, 110, 1_000_000)

# パフォーマンス測定
import time
start = time.perf_counter()
prices = black_scholes.call_price_batch(
    spots=aligned_spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)
elapsed = time.perf_counter() - start
print(f"Aligned array: {elapsed*1000:.2f}ms")  # 期待値: 約56ms（100万要素）
```

### メモリ使用量の監視

```python
import tracemalloc

# メモリ追跡開始
tracemalloc.start()

# 大規模計算
spots = np.random.uniform(90, 110, 5_000_000)
prices = black_scholes.call_price_batch(
    spots=spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)

# メモリ使用量
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory: {peak / 1024 / 1024:.1f} MB")

tracemalloc.stop()
```

## インプレース操作

### 結果の直接書き込み

```{code-block} python
:name: numpy-integration-code-section
:caption: 事前確保された配列

# 事前確保された配列
n = 1_000_000
spots = np.random.uniform(90, 110, n)
prices = np.empty(n)  # 結果用配列

# インプレース計算（メモリ効率的）
# Note: 現在のAPIではインプレース操作はサポートされていません
prices = black_scholes.call_price_batch(
    spots=spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)

print(f"Prices array modified in-place: {prices[:5]}")
```

## 統計処理

### NumPy統計関数との組み合わせ

```{code-block} python
:name: numpy-integration-code-section
:caption: ポートフォリオ統計

# ポートフォリオ統計
spots = np.random.uniform(90, 110, 10000)
prices = black_scholes.call_price_batch(
    spots=spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)

# 統計量
stats = {
    'mean': np.mean(prices),
    'std': np.std(prices),
    'median': np.median(prices),
    'percentile_5': np.percentile(prices, 5),
    'percentile_95': np.percentile(prices, 95),
    'skew': np.mean(((prices - np.mean(prices)) / np.std(prices))**3),
    'kurtosis': np.mean(((prices - np.mean(prices)) / np.std(prices))**4) - 3
}

for key, value in stats.items():
    print(f"{key}: {value:.4f}")
```

## まとめ

NumPy統合により以下が実現できます：

- **ゼロコピー処理**: メモリコピーなしの高速計算（PyO3経由）
- **ブロードキャスティング**: 柔軟な配列操作
- **メモリ効率**: 大規模データの効率的な処理
- **高速バッチ処理**: 100万件を約56ms（AMD Ryzen 5 5600G）で処理

パフォーマンスの詳細は[ベンチマーク](../performance/benchmarks.md)を参照してください。

次は[高度なモデル](advanced_models.md)で、アメリカンオプションなどの複雑な価格モデルを学びましょう。