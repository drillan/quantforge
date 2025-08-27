# Black76モデル API

商品先物・エネルギーオプションの価格計算のためのBlack76モデルです。

## 概要

Black76モデルは、先物やフォワード契約のオプション価格を計算するためのモデルです。
主に商品（コモディティ）、金利、エネルギー市場で使用されます。

## API使用方法

### 基本的な価格計算

```python
from quantforge.models import black76

# コールオプション価格
# パラメータ: f(forward), k(strike), t(time), r(rate), sigma
call_price = black76.call_price(75.50, 70.00, 0.25, 0.05, 0.3)

# プットオプション価格  
# パラメータ: f(forward), k(strike), t(time), r(rate), sigma
put_price = black76.put_price(75.50, 80.00, 0.25, 0.05, 0.3)
```

### バッチ処理

```python
import numpy as np

# 完全配列サポートとBroadcasting
forwards = np.array([70, 75, 80, 85])
strikes = np.array([65, 70, 75, 80])  # 配列も可能
times = 0.5  # スカラーは自動拡張
rates = 0.05
sigmas = np.array([0.20, 0.25, 0.30, 0.35])

# パラメータ: forwards, strikes, times, rates, sigmas
call_prices = black76.call_price_batch(forwards, strikes, times, rates, sigmas)
put_prices = black76.put_price_batch(forwards, strikes, times, rates, sigmas)

# Greeksバッチ計算（辞書形式）
greeks = black76.greeks_batch(forwards, strikes, times, rates, sigmas, is_calls=True)
print(greeks['delta'])  # NumPy配列
print(greeks['vega'])   # NumPy配列
```

詳細は[Batch Processing API](batch_processing.md)を参照してください。

### グリークス計算

```python
# 全グリークスを一括計算
# パラメータ: f(forward), k(strike), t(time), r(rate), sigma, is_call
greeks = black76.greeks(75.50, 75.00, 0.5, 0.05, 0.3, True)

# 個別のグリークスへアクセス
print(f"Delta: {greeks.delta:.4f}")  # フォワード価格感応度
print(f"Gamma: {greeks.gamma:.4f}")  # デルタの変化率
print(f"Vega: {greeks.vega:.4f}")    # ボラティリティ感応度
print(f"Theta: {greeks.theta:.4f}")  # 時間価値減衰
print(f"Rho: {greeks.rho:.4f}")      # 金利感応度
```

### インプライドボラティリティ

```python
# パラメータ: price, f(forward), k(strike), t(time), r(rate), is_call
iv = black76.implied_volatility(5.50, 75.00, 75.00, 0.5, 0.05, True)
print(f"Implied Volatility: {iv:.4f}")
```

## パラメータ説明

### 入力パラメータ

| パラメータ | 型 | 説明 | 有効範囲 |
|-----------|-----|------|----------|
| `f` | float | フォワード価格（将来価格） | > 0 |
| `k` | float | 権利行使価格（ストライク） | > 0 |
| `t` | float | 満期までの時間（年） | > 0 |
| `r` | float | 無リスク金利（年率） | 任意 |
| `sigma` | float | ボラティリティ（年率） | > 0 |
| `is_call` | bool | オプションタイプ | True: コール, False: プット |

### バッチ処理用パラメータ

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `fs` | np.ndarray | 複数のフォワード価格 |
| `k` | float | 権利行使価格（共通） |
| `t` | float | 満期までの時間（共通） |
| `r` | float | 無リスク金利（共通） |
| `sigma` | float | ボラティリティ（共通） |

## 価格式（参考）

コールオプション:
$$C = e^{-rT} \cdot [F \cdot N(d_1) - K \cdot N(d_2)]$$

プットオプション:
$$P = e^{-rT} \cdot [K \cdot N(-d_2) - F \cdot N(-d_1)]$$

where:
- $d_1 = \frac{\ln(F/K) + \sigma^2 T / 2}{\sigma\sqrt{T}}$
- $d_2 = d_1 - \sigma\sqrt{T}$

詳細な理論的背景は[Black76モデル理論](../../models/black76.md)を参照してください。

## エラーハンドリング

すべての価格計算関数は以下の条件でエラーを返します：

- f ≤ 0（フォワード価格が負または0）
- k ≤ 0（権利行使価格が負または0）
- t ≤ 0（満期までの時間が負または0）
- sigma ≤ 0（ボラティリティが負または0）
- 数値がNaNまたは無限大

```python
try:
    # パラメータ: f(forward), k, t, r, sigma
    price = black76.call_price(-100, 100, 1.0, 0.05, 0.2)  # 無効な負の値
except ValueError as e:
    print(f"入力エラー: {e}")
```

## パフォーマンス指標

| 操作 | 単一計算 | 100万件バッチ |
|------|----------|--------------:|
| コール/プット価格 | < 12ns | < 25ms |
| 全グリークス | < 60ns | < 120ms |
| インプライドボラティリティ | < 250ns | < 600ms |

## 使用例

### エネルギー市場（原油先物）

```python
from quantforge.models import black76

# WTI原油先物オプション
f = 85.00  # 先物価格
k = 90.00  # 権利行使価格
t = 0.25   # 3ヶ月
r = 0.05   # リスクフリーレート
sigma = 0.35  # WTI標準的ボラティリティ

# 価格計算
call_price = black76.call_price(f, k, t, r, sigma)
put_price = black76.put_price(f, k, t, r, sigma)

print(f"Call Price: ${call_price:.2f}")
print(f"Put Price: ${put_price:.2f}")

# グリークス計算
greeks = black76.greeks(f, k, t, r, sigma, is_call=True)
print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
```

### ボラティリティスマイル分析

```python
import numpy as np
from quantforge.models import black76

f = 100.0  # フォワード価格
strikes = np.linspace(80, 120, 21)
t = 0.25
r = 0.05

# 各ストライクでのIV計算
ivs = []
for k in strikes:
    # 実際の市場価格から（ここではモデル価格を使用）
    if k < f:
        price = black76.put_price(f, k, t, r, 0.25)
        is_call = False
    else:
        price = black76.call_price(f, k, t, r, 0.25)
        is_call = True
    
    # パラメータ: price, f, k, t, r, is_call
    iv = black76.implied_volatility(price, f, k, t, r, is_call)
    ivs.append(iv)

# IVスマイルの確認（プロット等）
```

## 関連情報

- [Black-Scholesモデル API](black_scholes.md) - 株式オプション向け
- [Mertonモデル API](merton.md) - 配当付き資産向け
- [インプライドボラティリティAPI](implied_vol.md) - IV計算の詳細
- [Black76理論的背景](../../models/black76.md) - 数学的詳細