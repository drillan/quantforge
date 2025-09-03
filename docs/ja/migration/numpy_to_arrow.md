# NumPyからPyArrowへの移行ガイド

## 概要

QuantForgeはArrow-native設計を採用していますが、NumPyとの完全な互換性も維持しています。このガイドでは、NumPyからPyArrowへのスムーズな移行方法を説明します。

## なぜPyArrowに移行すべきか

### パフォーマンス上の利点

1. **ゼロコピーFFI**: Python-Rust間でデータコピーが発生しない
2. **メモリ効率**: 中間バッファが不要
3. **処理速度**: 大規模データで約1.5倍高速

### エコシステムの利点

1. **最新のデータフレームライブラリとの統合**: Polars、DuckDB等
2. **分散処理対応**: Ray、Daskとの相性が良い
3. **標準化されたフォーマット**: 言語間での互換性

## 基本的な変換

### 配列の作成

| 操作 | NumPy | PyArrow |
|------|-------|---------|
| リストから作成 | `np.array([1, 2, 3])` | `pa.array([1, 2, 3])` |
| ゼロ配列 | `np.zeros(10)` | `pa.array([0] * 10)` または `pa.nulls(10, pa.float64())` |
| 連番 | `np.arange(10)` | `pa.array(range(10))` |
| リピート | `np.full(10, 5.0)` | `pa.array([5.0] * 10)` |
| ランダム | `np.random.uniform(0, 1, 10)` | `pa.array(np.random.uniform(0, 1, 10))` |

### データ型の指定

| NumPy | PyArrow |
|-------|---------|
| `np.array([1, 2, 3], dtype=np.float64)` | `pa.array([1, 2, 3], type=pa.float64())` |
| `np.array([1, 2, 3], dtype=np.int32)` | `pa.array([1, 2, 3], type=pa.int32())` |
| `np.array([True, False], dtype=bool)` | `pa.array([True, False], type=pa.bool_())` |

## QuantForgeでの使用例

### NumPyからの移行（Before/After）

#### Before（NumPy）
```python
import numpy as np
from quantforge.models import black_scholes

# NumPy配列を使用
spots = np.array([95, 100, 105, 110])
strikes = np.full(4, 100.0)
times = np.ones(4)
rates = np.full(4, 0.05)
sigmas = np.array([0.18, 0.20, 0.22, 0.24])

# バッチ計算
prices = black_scholes.call_price_batch(
    spots=spots,
    strikes=strikes,
    times=times,
    rates=rates,
    sigmas=sigmas
)

# 結果の処理（Arrow配列が返る）
mean_price = np.mean(np.array(prices))  # NumPyに変換が必要
```

#### After（PyArrow）
```python
import pyarrow as pa
import numpy as np  # 統計処理用
from quantforge.models import black_scholes

# PyArrow配列を使用
spots = pa.array([95, 100, 105, 110])
strikes = pa.array([100.0] * 4)
times = pa.array([1.0] * 4)
rates = pa.array([0.05] * 4)
sigmas = pa.array([0.18, 0.20, 0.22, 0.24])

# バッチ計算（より効率的）
prices = black_scholes.call_price_batch(
    spots=spots,
    strikes=strikes,
    times=times,
    rates=rates,
    sigmas=sigmas
)

# 結果の処理（必要に応じてNumPyに変換）
mean_price = np.mean(np.array(prices))
```

### 段階的な移行戦略

#### ステップ1: 入力データのみPyArrowに
```python
# NumPy配列を作成後、PyArrowに変換
np_data = np.random.uniform(90, 110, 1000)
spots = pa.array(np_data)  # PyArrowに変換

prices = black_scholes.call_price_batch(
    spots=spots,  # PyArrow
    strikes=100.0,  # スカラー（自動処理）
    times=1.0,
    rates=0.05,
    sigmas=0.2
)
```

#### ステップ2: 完全なPyArrow移行
```python
# 最初からPyArrowで作業
spots = pa.array(np.random.uniform(90, 110, 1000))
strikes = pa.array([100.0] * 1000)

prices = black_scholes.call_price_batch(
    spots=spots,
    strikes=strikes,
    times=1.0,
    rates=0.05,
    sigmas=0.2
)
```

## データフレームとの統合

### Pandas DataFrameとの相互変換
```python
import pandas as pd
import pyarrow as pa

# Pandas DataFrame
df = pd.DataFrame({
    'spot': [95, 100, 105],
    'strike': [100, 100, 100],
    'time': [1.0, 1.0, 1.0],
    'rate': [0.05, 0.05, 0.05],
    'sigma': [0.2, 0.2, 0.2]
})

# PandasからPyArrowへ
spots_arrow = pa.array(df['spot'].values)
strikes_arrow = pa.array(df['strike'].values)

# QuantForgeで計算
prices = black_scholes.call_price_batch(
    spots=spots_arrow,
    strikes=strikes_arrow,
    times=df['time'].iloc[0],  # スカラー値
    rates=df['rate'].iloc[0],
    sigmas=df['sigma'].iloc[0]
)

# 結果をDataFrameに追加
df['option_price'] = np.array(prices)
```

### Polars DataFrameとの統合（推奨）
```python
import polars as pl

# Polars DataFrame（Arrow-native）
df = pl.DataFrame({
    'spot': [95, 100, 105],
    'strike': [100, 100, 100],
    'time': [1.0, 1.0, 1.0],
    'rate': [0.05, 0.05, 0.05],
    'sigma': [0.2, 0.2, 0.2]
})

# Polarsは内部でArrowを使用
prices = black_scholes.call_price_batch(
    spots=df['spot'].to_arrow(),
    strikes=df['strike'].to_arrow(),
    times=df['time'][0],  # スカラー値
    rates=df['rate'][0],
    sigmas=df['sigma'][0]
)

# 結果を追加（効率的）
df = df.with_columns(
    pl.Series('option_price', prices)
)
```

## 大規模データ処理の比較

### NumPyスタイル（従来）
```python
import numpy as np
import time

n = 10_000_000

# NumPy配列の作成
start = time.perf_counter()
spots_np = np.random.uniform(90, 110, n)
strikes_np = np.full(n, 100.0)

# 計算（内部でArrowに変換）
prices = black_scholes.call_price_batch(
    spots=spots_np,
    strikes=strikes_np,
    times=1.0,
    rates=0.05,
    sigmas=0.2
)
total_time = time.perf_counter() - start

print(f"NumPy入力: {total_time:.3f}秒")
```

### PyArrowスタイル（推奨）
```python
import pyarrow as pa
import numpy as np
import time

n = 10_000_000

# PyArrow配列の作成
start = time.perf_counter()
spots_pa = pa.array(np.random.uniform(90, 110, n))
strikes_pa = pa.array([100.0] * n)

# 計算（ゼロコピー）
prices = black_scholes.call_price_batch(
    spots=spots_pa,
    strikes=strikes_pa,
    times=1.0,
    rates=0.05,
    sigmas=0.2
)
total_time = time.perf_counter() - start

print(f"PyArrow入力: {total_time:.3f}秒")
# 約10-20%高速化が期待できる
```

## よくある質問

### Q: 既存のNumPyコードを全て書き換える必要がありますか？

A: いいえ、QuantForgeはNumPy配列も受け付けるため、段階的な移行が可能です。パフォーマンスが重要な部分から徐々に移行できます。

### Q: PyArrowで統計処理はできますか？

A: 基本的な集計（sum、mean等）は可能ですが、高度な統計処理にはNumPyやSciPyが必要です。計算結果をNumPyに変換して処理することを推奨します。

```python
# PyArrowで計算
prices = black_scholes.call_price_batch(...)

# 統計処理はNumPyで
prices_np = np.array(prices)
mean = np.mean(prices_np)
std = np.std(prices_np)
percentile_95 = np.percentile(prices_np, 95)
```

### Q: メモリ使用量は増えますか？

A: いいえ、むしろ減少します。Arrow形式は効率的なメモリレイアウトを持ち、中間バッファも不要なため、全体的なメモリ使用量は削減されます。

### Q: 互換性の問題はありますか？

A: QuantForgeは内部でNumPyとPyArrowの両方を適切に処理するため、互換性の問題はありません。ただし、返り値は常にArrow配列（arro3.core.Array）となります。

## 移行チェックリスト

- [ ] PyArrowをインストール: `pip install pyarrow`
- [ ] パフォーマンスクリティカルな部分を特定
- [ ] 入力データをPyArrow配列に変換
- [ ] 結果の処理方法を確認（NumPyへの変換が必要か）
- [ ] ベンチマークで改善を確認
- [ ] 段階的に全体を移行

## まとめ

PyArrowへの移行は以下のメリットをもたらします：

1. **即座の効果**: 大規模データで10-20%の高速化
2. **将来性**: 最新のデータ処理エコシステムとの統合
3. **メモリ効率**: ゼロコピーによるメモリ使用量削減
4. **互換性維持**: 既存コードを壊さずに段階的移行可能

QuantForgeのArrow-native設計を最大限活用するため、新規コードではPyArrowの使用を推奨します。