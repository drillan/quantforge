(api-black-scholes)=
# Black-Scholesモデル API

ヨーロピアンオプションの価格計算のための標準的なモデルです。

(api-black-scholes-overview)=
## 概要

Black-Scholesモデルは、株式オプションの理論価格を計算するための基本モデルです。
対数正規分布に従う株価プロセスを仮定し、解析的な価格式を提供します。

(api-black-scholes-usage)=
## API使用方法

(api-black-scholes-basic-calculation)=
### 基本的な価格計算

```{code-block} python
:name: api-black-scholes-code-basic
:caption: 基本的な価格計算
:linenos:

from quantforge.models import black_scholes

# コールオプション価格
# パラメータ: s(spot), k(strike), t(time), r(rate), sigma
call_price = black_scholes.call_price(100.0, 105.0, 1.0, 0.05, 0.2)

# プットオプション価格
# パラメータ: s(spot), k(strike), t(time), r(rate), sigma
put_price = black_scholes.put_price(100.0, 105.0, 1.0, 0.05, 0.2)
```

(api-black-scholes-batch-processing)=
### バッチ処理

完全配列サポートとBroadcastingによる効率的な計算：

```{code-block} python
:name: api-black-scholes-code-batch
:caption: バッチ処理の例
:linenos:

import pyarrow as pa
import numpy as np  # NumPyとの互換性

# すべてのパラメータが配列を受け付ける（Broadcasting対応）
# PyArrow使用（推奨 - Arrow-native）
spots = pa.array([95, 100, 105, 110])
times = pa.array([0.5, 1.0, 1.5, 2.0])
sigmas = pa.array([0.18, 0.20, 0.22, 0.24])

# NumPy配列も使用可能（互換性）
# spots = np.array([95, 100, 105, 110])

# パラメータ: spots, strikes, times, rates, sigmas
call_prices = black_scholes.call_price_batch(
    spots, 
    100.0,    # スカラーは自動的に配列サイズに拡張
    times, 
    0.05,     # rate
    sigmas
)  # 返り値: arro3.core.Array

put_prices = black_scholes.put_price_batch(spots, 100.0, times, 0.05, sigmas)

# Greeksバッチ計算（辞書形式で返却）
greeks = black_scholes.greeks_batch(spots, 100.0, times, 0.05, sigmas, is_calls=True)
# greeks['delta']はarro3.core.Array

# NumPy操作が必要な場合は変換
portfolio_delta = np.sum(np.array(greeks['delta']))
portfolio_vega = np.sum(np.array(greeks['vega']))
```

詳細は[Batch Processing API](batch_processing.md)を参照してください。

(api-black-scholes-greeks-calculation)=
### グリークス計算

オプションの感応度（グリークス）を一括計算：

```{code-block} python
:name: black-scholes-code-section
:caption: 全グリークスを一括計算

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

(api-black-scholes-implied-volatility)=
### インプライドボラティリティ

市場価格からボラティリティを逆算：

```{code-block} python
:name: black-scholes-code-price-s-k-t-r-iscall
:caption: パラメータ: price, s, k, t, r, is_call

# パラメータ: price, s, k, t, r, is_call
iv = black_scholes.implied_volatility(10.45, 100.0, 100.0, 1.0, 0.05, True)
print(f"Implied Volatility: {iv:.4f}")
```

(api-black-scholes-parameters)=
## パラメータ説明

(api-black-scholes-input-parameters)=
### 入力パラメータ

```{list-table} 入力パラメータ
:name: api-black-scholes-table-parameters
:header-rows: 1
:widths: 20 20 40 20

* - パラメータ
  - 型
  - 説明
  - 有効範囲
* - `s`
  - float
  - スポット価格（現在の株価）
  - > 0
* - `k`
  - float
  - 権利行使価格（ストライク）
  - > 0
* - `t`
  - float
  - 満期までの時間（年）
  - > 0
* - `r`
  - float
  - 無リスク金利（年率）
  - 任意
* - `sigma`
  - float
  - ボラティリティ（年率）
  - > 0
* - `is_call`
  - bool
  - オプションタイプ
  - True: コール, False: プット
```

(api-black-scholes-batch-parameters)=
### バッチ処理用パラメータ

```{list-table} バッチ処理用パラメータ
:name: api-black-scholes-table-batch-params
:header-rows: 1
:widths: 30 30 40

* - パラメータ
  - 型
  - 説明
* - `spots`
  - pa.array | np.ndarray | list
  - 複数のスポット価格（Arrow/NumPy配列）
* - `strikes`
  - float | pa.array | np.ndarray
  - 権利行使価格（スカラーまたは配列）
* - `times`
  - float | pa.array | np.ndarray
  - 満期までの時間（スカラーまたは配列）
* - `rates`
  - float | pa.array | np.ndarray
  - 無リスク金利（スカラーまたは配列）
* - `sigmas`
  - float | pa.array | np.ndarray
  - ボラティリティ（スカラーまたは配列）
```

(api-black-scholes-formulas)=
## 価格式（参考）

コールオプション:

```{math}
:name: api-black-scholes-eq-call

C = S_0 \cdot N(d_1) - K \cdot e^{-rT} \cdot N(d_2)
```

プットオプション:

```{math}
:name: api-black-scholes-eq-put

P = K \cdot e^{-rT} \cdot N(-d_2) - S_0 \cdot N(-d_1)
```

where:

```{math}
:name: api-black-scholes-eq-d1-d2

d_1 = \frac{\ln(S_0/K) + (r + \sigma^2/2)T}{\sigma\sqrt{T}}, \quad d_2 = d_1 - \sigma\sqrt{T}
```

詳細な理論的背景は[数理モデル](../../models/black_scholes.md)を参照してください。

(api-black-scholes-error-handling)=
## エラーハンドリング

すべての価格計算関数は以下の条件でエラーを返します：

- s ≤ 0（スポット価格が負または0）
- k ≤ 0（権利行使価格が負または0）
- t < 0（満期までの時間が負）
- sigma ≤ 0（ボラティリティが負または0）
- 数値がNaNまたは無限大

```{code-block} python
:name: api-black-scholes-code-error
:caption: エラーハンドリングの例
:linenos:

try:
    # パラメータ: s(spot), k, t, r, sigma
    price = black_scholes.call_price(-100, 100, 1.0, 0.05, 0.2)  # 無効な負の値
except ValueError as e:
    print(f"入力エラー: {e}")
```

(api-black-scholes-performance)=
## パフォーマンス指標

:::{note}
測定環境: AMD Ryzen 5 5600G、CUIモード
測定方法: 実測値は[ベンチマーク](../../performance/benchmarks.md)を参照
:::

```{list-table} パフォーマンス指標
:name: api-black-scholes-table-performance
:header-rows: 1
:widths: 40 30 30

* - 操作
  - 単一計算
  - 100万件バッチ
* - コール/プット価格
  - 1.4 μs
  - 55.6ms
* - 全グリークス
  - 計測予定
  - 計測予定
* - インプライドボラティリティ
  - 1.5 μs
  - 計測予定
```

(api-black-scholes-examples)=
## 使用例

(api-black-scholes-atm-example)=
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