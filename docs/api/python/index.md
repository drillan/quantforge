# Python API リファレンス

QuantForgeのPython APIの完全なリファレンスです。

## インポート方法

```python
from quantforge.models import black_scholes
```

## API構造

### API構造

明示的で拡張性の高いモジュールベース設計を採用しています。

```python
from quantforge.models import black_scholes

# 価格計算
price = black_scholes.call_price(s=100, k=105, t=1.0, r=0.05, sigma=0.2)

# グリークス
greeks = black_scholes.greeks(s=100, k=100, t=1.0, r=0.05, sigma=0.2, is_call=True)

# インプライドボラティリティ
iv = black_scholes.implied_volatility(price=10.45, s=100, k=100, t=1.0, r=0.05, is_call=True)
```


## API カテゴリ

### 価格計算
- [価格計算関数](pricing.md) - オプション価格の計算
- [インプライドボラティリティ](implied_vol.md) - IV計算

### グリークス
- `black_scholes.greeks()` - 全グリークス一括計算

### バッチ計算

```python
import numpy as np
from quantforge.models import black_scholes

spots = np.array([95, 100, 105, 110])
prices = black_scholes.call_price_batch(spots=spots, k=100, t=1.0, r=0.05, sigma=0.2)
```

### グリークス計算

```python
greeks = black_scholes.greeks(
    s=100,
    k=100,
    t=1.0,
    r=0.05,
    sigma=0.2,
    is_call=True
)
print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
```

## 型システム

### 入力型

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| s | float \| np.ndarray | 現在価格（スポット） |
| k | float \| np.ndarray | 行使価格（ストライク） |
| r | float \| np.ndarray | 無リスク金利 |
| sigma | float \| np.ndarray | ボラティリティ |
| t | float \| np.ndarray | 満期までの時間 |

### 戻り値型

| 関数 | 戻り値 | 説明 |
|------|--------|------|
| 価格関数 | float \| np.ndarray | オプション価格 |
| グリークス関数 | float \| np.ndarray | 感応度 |
| calculate(..., greeks=True) | dict | 価格とグリークスの辞書 |

## エラーハンドリング

### 例外クラス

```python
class QuantForgeError(Exception):
    """QuantForge基底例外クラス"""
    
class InvalidInputError(QuantForgeError):
    """無効な入力パラメータ"""
    
class ConvergenceError(QuantForgeError):
    """数値計算の収束失敗"""
```

### エラー処理例

```python
try:
    price = black_scholes.call_price(
        s=-100,  # 無効な負の値
        k=100,
        r=0.05,
        sigma=0.2,
        t=1.0
    )
except ValueError as e:
    print(f"入力エラー: {e}")
except RuntimeError as e:
    print(f"計算エラー: {e}")
```

## パフォーマンス考慮事項

### 最適な使用方法

1. **NumPy配列を使用**: リストより高速
2. **適切なバッチサイズ**: 10,000～100,000要素
3. **メモリアラインメント**: 64バイト境界
4. **型の統一**: float64を使用

### パフォーマンス測定

```python
import time

def benchmark(func, *args, n_iter=100):
    """関数のベンチマーク"""
    times = []
    for _ in range(n_iter):
        start = time.perf_counter()
        func(*args)
        times.append(time.perf_counter() - start)
    
    return {
        'mean': np.mean(times) * 1000,  # ms
        'std': np.std(times) * 1000,
        'min': np.min(times) * 1000,
        'max': np.max(times) * 1000
    }

# ベンチマーク実行
spots = np.random.uniform(90, 110, 100000)
stats = benchmark(qf.calculate, spots, 100, 0.05, 0.2, 1.0)
print(f"Mean: {stats['mean']:.2f}ms ± {stats['std']:.2f}ms")
```

## スレッドセーフティ

QuantForgeの関数は**スレッドセーフ**です：

```python
from concurrent.futures import ThreadPoolExecutor

def price_batch(spots):
    return qf.calculate(spots, 100, 0.05, 0.2, 1.0)

# マルチスレッド実行
with ThreadPoolExecutor(max_workers=4) as executor:
    batches = np.array_split(large_spots_array, 4)
    results = list(executor.map(price_batch, batches))
    final_results = np.concatenate(results)
```

## 次のステップ

- [価格計算API](pricing.md) - 詳細な価格計算関数
- [インプライドボラティリティAPI](implied_vol.md) - IV計算関数
- [Rust API](../rust/index.md) - 低レベルRust API