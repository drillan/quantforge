# Python API リファレンス

QuantForgeのPython APIの完全なリファレンスです。

## モジュール構成

```python
import quantforge as qf
```

## API カテゴリ

### 価格計算
- [価格計算関数](pricing.md) - オプション価格の計算
- [インプライドボラティリティ](implied_vol.md) - IV計算

### グリークス
- `delta_call()`, `delta_put()` - デルタ計算
- `gamma()` - ガンマ計算
- `vega()` - ベガ計算
- `theta()` - シータ計算
- `rho()` - ロー計算

### ユーティリティ
- `check_simd_support()` - SIMD機能の確認
- `print_system_info()` - システム情報表示
- `version()` - バージョン情報

## 基本的な使用パターン

### 単一計算

```python
# 単一のオプション価格
price = qf.black_scholes_call(
    spot=100.0,
    strike=105.0,
    rate=0.05,
    vol=0.2,
    time=1.0
)
```

### バッチ計算

```python
import numpy as np

# NumPy配列でのバッチ処理
spots = np.array([95, 100, 105])
prices = qf.calculate(
    spots=spots,
    strikes=100,
    rates=0.05,
    vols=0.2,
    times=1.0
)
```

### グリークス付き計算

```python
# 価格とグリークスを同時計算
result = qf.calculate(
    spots=100,
    strikes=105,
    rates=0.05,
    vols=0.2,
    times=1.0,
    option_type="call",
    greeks=True
)

# 結果は辞書形式
print(result['price'])
print(result['delta'])
print(result['gamma'])
```

## 型システム

### 入力型

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| spot | float \| np.ndarray | 現在価格 |
| strike | float \| np.ndarray | 行使価格 |
| rate | float \| np.ndarray | 無リスク金利 |
| vol | float \| np.ndarray | ボラティリティ |
| time | float \| np.ndarray | 満期までの時間 |

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
    price = qf.black_scholes_call(
        spot=-100,  # 無効な負の値
        strike=100,
        rate=0.05,
        vol=0.2,
        time=1.0
    )
except qf.InvalidInputError as e:
    print(f"入力エラー: {e}")
except qf.QuantForgeError as e:
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