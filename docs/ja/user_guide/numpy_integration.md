# NumPy相互運用ガイド

## 概要

QuantForgeは**Arrow-native**設計を採用しており、すべてのバッチ関数は`arro3.core.Array`（Arrow配列）を返します。しかし、NumPyユーザーも簡単に使用できるよう、優れた相互運用性を提供しています。

## 入力：柔軟な型サポート

`call_price_batch`などのバッチ関数は、以下の入力を自動的に受け付けます：

```python
import numpy as np
import pyarrow as pa
from quantforge import black_scholes

# すべて動作します！
result = black_scholes.call_price_batch(
    spots=np.array([100, 105, 110]),    # NumPy配列 ✅
    strikes=pa.array([95, 100, 105]),   # PyArrow配列 ✅
    times=1.0,                           # スカラー ✅
    rates=0.05,
    sigmas=np.array([0.18, 0.20, 0.22]) # NumPy配列 ✅
)
```

## 出力：Arrow配列の利点

すべてのバッチ関数は`arro3.core.Array`を返します。これは`__array__`プロトコルを実装しているため、多くのNumPy関数が**直接動作**します：

```python
# NumPy配列を入力
spots = np.array([100, 105, 110, 95, 90])
result = black_scholes.call_price_batch(spots, 100.0, 1.0, 0.05, 0.2)

# 多くのNumPy関数が直接動作！
mean_price = np.mean(result)    # ✅ 動作
total = np.sum(result)          # ✅ 動作
std_dev = np.std(result)        # ✅ 動作
min_price = np.min(result)      # ✅ 動作
max_price = np.max(result)      # ✅ 動作
```

## 明示的な変換

より高度なNumPy操作（インデクシング、スライシング、要素ごとの演算）が必要な場合は、明示的に変換します：

### 方法1: `np.array()`を使用

```python
result = black_scholes.call_price_batch(spots, 100.0, 1.0, 0.05, 0.2)
np_result = np.array(result)  # NumPy配列に変換

# NumPy固有の操作
first_element = np_result[0]      # インデクシング
sliced = np_result[1:3]          # スライシング
doubled = np_result * 2          # 要素ごとの演算
```

### 方法2: `.to_numpy()`メソッド

```python
result = black_scholes.call_price_batch(spots, 100.0, 1.0, 0.05, 0.2)
np_result = result.to_numpy()  # より明示的な変換

# 以降はNumPyとして扱う
```

## パフォーマンス特性

変換コストは非常に軽量です：

| データサイズ | 変換時間 |
|------------|---------|
| 100要素    | ~1.7μs  |
| 1,000要素  | ~1.8μs  |
| 10,000要素 | ~3.6μs  |
| 100,000要素 | ~34μs  |

## 使用パターン例

### パターン1: 基本的な統計計算

```python
# 集約関数は変換不要
spots = np.array([95, 100, 105, 110])
prices = black_scholes.call_price_batch(spots, 100.0, 1.0, 0.05, 0.2)

# 直接使用可能
avg_price = np.mean(prices)
volatility = np.std(prices)
price_range = np.max(prices) - np.min(prices)
```

### パターン2: 高度なNumPy操作

```python
# 複雑な操作には変換が必要
spots = np.array([95, 100, 105, 110])
prices = black_scholes.call_price_batch(spots, 100.0, 1.0, 0.05, 0.2)

# NumPyに変換
np_prices = prices.to_numpy()

# NumPy固有の操作
log_returns = np.log(np_prices[1:] / np_prices[:-1])
percentiles = np.percentile(np_prices, [25, 50, 75])
weighted_avg = np.average(np_prices, weights=[0.1, 0.2, 0.3, 0.4])
```

### パターン3: Pandas統合

```python
import pandas as pd

# DataFrameとの統合
spots = np.linspace(80, 120, 41)
prices = black_scholes.call_price_batch(spots, 100.0, 1.0, 0.05, 0.2)

# DataFrameに直接格納（自動変換）
df = pd.DataFrame({
    'spot': spots,
    'call_price': prices.to_numpy()  # 明示的変換推奨
})
```

## なぜArrow配列を返すのか？

1. **一貫性**: すべての関数が同じ型を返す
2. **パフォーマンス**: 不要な変換を避ける
3. **ゼロコピー**: Arrow間の操作は効率的
4. **明示性**: "Explicit is better than implicit" (PEP 20)

## まとめ

- **入力**: NumPy、PyArrow、スカラーを自由に混在可能
- **出力**: 常にArrow配列（`arro3.core.Array`）
- **NumPy互換**: 多くの関数は直接動作
- **変換**: 必要な時は`np.array()`または`.to_numpy()`
- **パフォーマンス**: 変換コストは軽微（μs単位）

これにより、NumPyユーザーもPyArrowユーザーも、それぞれのワークフローで効率的にQuantForgeを使用できます。