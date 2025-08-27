# Black-Scholesモデル API

ヨーロピアンオプションの価格計算のための標準的なモデルです。

## 概要

Black-Scholesモデルは、株式オプションの理論価格を計算するための基本モデルです。
対数正規分布に従う株価プロセスを仮定し、解析的な価格式を提供します。

## API使用方法

### 基本的な価格計算

```python
from quantforge.models import black_scholes

# コールオプション価格
# パラメータ: s(spot), k(strike), t(time), r(rate), sigma
call_price = black_scholes.call_price(100.0, 105.0, 1.0, 0.05, 0.2)

# プットオプション価格
# パラメータ: s(spot), k(strike), t(time), r(rate), sigma
put_price = black_scholes.put_price(100.0, 105.0, 1.0, 0.05, 0.2)
```

### バッチ処理

完全配列サポートとBroadcastingによる効率的な計算：

```python
import numpy as np

# すべてのパラメータが配列を受け付ける（Broadcasting対応）
spots = np.array([95, 100, 105, 110])
strikes = 100.0  # スカラーは自動的に配列サイズに拡張
times = np.array([0.5, 1.0, 1.5, 2.0])
rates = 0.05
sigmas = np.array([0.18, 0.20, 0.22, 0.24])

# パラメータ: spots, strikes, times, rates, sigmas
call_prices = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)
put_prices = black_scholes.put_price_batch(spots, strikes, times, rates, sigmas)

# Greeksバッチ計算（辞書形式で返却）
greeks = black_scholes.greeks_batch(spots, strikes, times, rates, sigmas, is_calls=True)
portfolio_delta = greeks['delta'].sum()  # NumPy配列の操作
portfolio_vega = greeks['vega'].sum()
```

詳細は[Batch Processing API](batch_processing.md)を参照してください。

### グリークス計算

オプションの感応度（グリークス）を一括計算：

```python
# 全グリークスを一括計算
# パラメータ: s(spot), k, t, r, sigma, is_call
greeks = black_scholes.greeks(100.0, 100.0, 1.0, 0.05, 0.2, True)

# 個別のグリークスへアクセス
print(f"Delta: {greeks.delta:.4f}")  # スポット価格に対する感応度
print(f"Gamma: {greeks.gamma:.4f}")  # デルタの変化率
print(f"Vega: {greeks.vega:.4f}")    # ボラティリティ感応度
print(f"Theta: {greeks.theta:.4f}")  # 時間価値減衰
print(f"Rho: {greeks.rho:.4f}")      # 金利感応度
```

### インプライドボラティリティ

市場価格からボラティリティを逆算：

```python
# パラメータ: price, s, k, t, r, is_call
iv = black_scholes.implied_volatility(10.45, 100.0, 100.0, 1.0, 0.05, True)
print(f"Implied Volatility: {iv:.4f}")
```

## パラメータ説明

### 入力パラメータ

| パラメータ | 型 | 説明 | 有効範囲 |
|-----------|-----|------|----------|
| `s` | float | スポット価格（現在の株価） | > 0 |
| `k` | float | 権利行使価格（ストライク） | > 0 |
| `t` | float | 満期までの時間（年） | > 0 |
| `r` | float | 無リスク金利（年率） | 任意 |
| `sigma` | float | ボラティリティ（年率） | > 0 |
| `is_call` | bool | オプションタイプ | True: コール, False: プット |

### バッチ処理用パラメータ

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `spots` | np.ndarray | 複数のスポット価格 |
| `k` | float | 権利行使価格（共通） |
| `t` | float | 満期までの時間（共通） |
| `r` | float | 無リスク金利（共通） |
| `sigma` | float | ボラティリティ（共通） |

## 価格式（参考）

コールオプション:
$$C = S_0 \cdot N(d_1) - K \cdot e^{-rT} \cdot N(d_2)$$

プットオプション:
$$P = K \cdot e^{-rT} \cdot N(-d_2) - S_0 \cdot N(-d_1)$$

where:
- $d_1 = \frac{\ln(S_0/K) + (r + \sigma^2/2)T}{\sigma\sqrt{T}}$
- $d_2 = d_1 - \sigma\sqrt{T}$

詳細な理論的背景は[数理モデル](../../models/black_scholes.md)を参照してください。

## エラーハンドリング

すべての価格計算関数は以下の条件でエラーを返します：

- s ≤ 0（スポット価格が負または0）
- k ≤ 0（権利行使価格が負または0）
- t < 0（満期までの時間が負）
- sigma ≤ 0（ボラティリティが負または0）
- 数値がNaNまたは無限大

```python
try:
    # パラメータ: s(spot), k, t, r, sigma
    price = black_scholes.call_price(-100, 100, 1.0, 0.05, 0.2)  # 無効な負の値
except ValueError as e:
    print(f"入力エラー: {e}")
```

## パフォーマンス指標

:::{note}
測定環境: Intel Core i9-12900K、Ubuntu 22.04
測定方法: 1000回実行の中央値
:::

| 操作 | 単一計算 | 100万件バッチ |
|------|----------|--------------:|
| コール/プット価格 | < 10ns | < 20ms |
| 全グリークス | < 50ns | < 100ms |
| インプライドボラティリティ | < 200ns | < 500ms |

## 使用例

### ATMオプションの価格とグリークス

```python
from quantforge.models import black_scholes

# ATM（At The Money）オプション
s = 100.0
k = 100.0
t = 0.25  # 3ヶ月
r = 0.05
sigma = 0.2

# 価格計算
call_price = black_scholes.call_price(s, k, t, r, sigma)
put_price = black_scholes.put_price(s, k, t, r, sigma)

print(f"Call Price: ${call_price:.2f}")
print(f"Put Price: ${put_price:.2f}")

# グリークス計算
greeks = black_scholes.greeks(s, k, t, r, sigma, is_call=True)
print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
```

### ボラティリティスマイル分析

```python
import numpy as np
from quantforge.models import black_scholes

s = 100.0
t = 0.25
r = 0.05
strikes = np.linspace(80, 120, 21)

# 各ストライクでの市場価格（仮定）からIVを計算
ivs = []
for k in strikes:
    # 実際の市場価格を使用
    market_price = get_market_price(k)  # 市場データ取得関数
    is_call = k >= s
    
    # パラメータ: price, s, k, t, r, is_call
    iv = black_scholes.implied_volatility(
        market_price, s, k, t, r, is_call
    )
    ivs.append(iv)

# IVスマイルのプロット（例）
import matplotlib.pyplot as plt
plt.plot(strikes, ivs)
plt.xlabel('Strike')
plt.ylabel('Implied Volatility')
plt.title('Volatility Smile')
plt.show()
```

## 関連情報

- [Black76モデル API](black76.md) - 商品・先物オプション向け
- [インプライドボラティリティAPI](implied_vol.md) - IV計算の詳細
- [Black-Scholes理論的背景](../../models/black_scholes.md) - 数学的詳細