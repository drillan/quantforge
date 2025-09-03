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
from quantforge.models import black_scholes, black76

# Black-Scholesモデル（スポット価格）
# パラメータ: s(spot), k(strike), t(time), r(rate), sigma
price_bs = black_scholes.call_price(100, 105, 1.0, 0.05, 0.2)
greeks_bs = black_scholes.greeks(100, 100, 1.0, 0.05, 0.2, True)
iv_bs = black_scholes.implied_volatility(10.45, 100, 100, 1.0, 0.05, True)

# Black76モデル（フォワード価格）
# パラメータ: f(forward), k(strike), t(time), r(rate), sigma
price_b76 = black76.call_price(75, 70, 0.25, 0.05, 0.3)
greeks_b76 = black76.greeks(75, 70, 0.25, 0.05, 0.3, True)
iv_b76 = black76.implied_volatility(5.5, 75, 75, 0.5, 0.05, True)
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
from quantforge.models import black_scholes, black76

# Black-Scholesバッチ計算（完全配列サポート + Broadcasting）
spots = np.array([95, 100, 105, 110])
strikes = 100.0  # スカラーは自動的に配列サイズに拡張
times = 1.0
rates = 0.05
sigmas = np.array([0.18, 0.20, 0.22, 0.24])

# すべてのパラメータが配列を受け付ける
prices_bs = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)

# Greeksはディクショナリで返される
greeks_bs = black_scholes.greeks_batch(spots, strikes, times, rates, sigmas, is_calls=True)
print(greeks_bs['delta'])  # NumPy配列
print(greeks_bs['gamma'])  # NumPy配列

# Black76バッチ計算
forwards = np.array([70, 75, 80, 85])
prices_b76 = black76.call_price_batch(forwards, 75.0, 0.5, 0.05, 0.25)
```

詳細は[Batch Processing API](batch_processing.md)を参照してください。

### グリークス計算

```{code-block} python
:name: index-code-black-scholes
:caption: Black-Scholesグリークス

# Black-Scholesグリークス
# パラメータ: s(spot), k, t, r, sigma, is_call
greeks = black_scholes.greeks(100, 100, 1.0, 0.05, 0.2, True)
print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
```

## 関数パラメータ仕様

### スカラー計算（単一値）

単一のオプション価格を計算する場合の関数シグネチャ：

**関数**: `call_price(s, k, t, r, sigma)` / `put_price(s, k, t, r, sigma)`

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| s | float | スポット価格（現在価格） |
| k | float | ストライク価格（行使価格） |
| t | float | 満期までの時間（年） |
| r | float | 無リスク金利 |
| sigma | float | ボラティリティ |

**戻り値**: `float` - オプション価格

### バッチ計算（配列処理）

複数のオプション価格を一括計算する場合の関数シグネチャ：

**関数**: `call_price_batch(spots, strikes, times, rates, sigmas)` / `put_price_batch(...)`

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| spots | pa.array \| np.ndarray \| float | スポット価格の配列 |
| strikes | pa.array \| np.ndarray \| float | ストライク価格の配列 |
| times | pa.array \| np.ndarray \| float | 満期までの時間の配列 |
| rates | pa.array \| np.ndarray \| float | 無リスク金利の配列 |
| sigmas | pa.array \| np.ndarray \| float | ボラティリティの配列 |

**戻り値**: `arro3.core.Array` - オプション価格のArrow配列

**注意事項**：
- バッチ版は NumPy のブロードキャスティングに対応
- スカラー値と配列を混在させることが可能（自動的にブロードキャスト）
- 全ての配列は同じ形状か、ブロードキャスト可能な形状である必要がある

### グリークス計算の戻り値

**スカラー版** (`greeks()`): `PyGreeks` オブジェクト
- `delta`, `gamma`, `vega`, `theta`, `rho` 属性を持つ

**バッチ版** (`greeks_batch()`): 辞書形式
- キー: `'delta'`, `'gamma'`, `'vega'`, `'theta'`, `'rho'`
- 値: 各グリークスの `arro3.core.Array`

### 使い分けガイド

| ケース | 推奨関数 | 理由 |
|--------|---------|------|
| 単一計算 | `call_price()` | シンプルで高速 |
| 複数計算（100件以上） | `call_price_batch()` | ベクトル化により大幅に高速 |
| パラメータスイープ | `call_price_batch()` | ブロードキャスティング活用 |
| インタラクティブ計算 | `call_price()` | レスポンスが速い |

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