# Mertonモデル API

配当を支払う資産のヨーロピアンオプション価格計算モデルです。

## 概要

Mertonモデルは、連続的な配当利回りを考慮したオプション価格モデルです。
株価指数、配当株式、外国為替など、定期的な収益を生む資産のオプション価格を正確に計算します。

詳細な理論的背景は[Mertonモデル理論](../../models/merton.md)を参照してください。

## API使用方法

### 基本的な価格計算

```python
from quantforge.models import merton

# コールオプション価格
# パラメータ: s(spot), k(strike), t(time), r(rate), q(dividend), sigma
call_price = merton.call_price(100.0, 105.0, 1.0, 0.05, 0.03, 0.2)

# プットオプション価格
# パラメータ: s(spot), k(strike), t(time), r(rate), q(dividend), sigma
put_price = merton.put_price(100.0, 105.0, 1.0, 0.05, 0.03, 0.2)
```

### バッチ処理

完全配列サポートとBroadcastingによる効率的な計算：

```python
import numpy as np

# すべてのパラメータが配列を受け付ける（Broadcasting対応）
spots = np.array([95, 100, 105, 110])
strikes = 100.0  # スカラーは自動拡張
times = 1.0
rates = 0.05
dividend_yields = np.array([0.01, 0.02, 0.03, 0.04])
sigmas = np.array([0.18, 0.20, 0.22, 0.24])

# パラメータ: spots, strikes, times, rates, dividend_yields, sigmas
call_prices = merton.call_price_batch(spots, strikes, times, rates, dividend_yields, sigmas)
put_prices = merton.put_price_batch(spots, strikes, times, rates, dividend_yields, sigmas)

# Greeksバッチ計算（辞書形式で返却）
greeks = merton.greeks_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_calls=True)
print(greeks['delta'])         # NumPy配列
print(greeks['dividend_rho'])  # 配当利回り感応度
```

詳細は[Batch Processing API](batch_processing.md)を参照してください。

### グリークス計算

配当を考慮したオプションの感応度（グリークス）を一括計算：

```python
# 全グリークスを一括計算
# パラメータ: s(spot), k, t, r, q, sigma, is_call
greeks = merton.greeks(100.0, 100.0, 1.0, 0.05, 0.03, 0.2, True)

# 個別のグリークスへアクセス
print(f"Delta: {greeks.delta:.4f}")          # スポット価格感応度（配当調整済み）
print(f"Gamma: {greeks.gamma:.4f}")          # デルタの変化率
print(f"Vega: {greeks.vega:.4f}")            # ボラティリティ感応度
print(f"Theta: {greeks.theta:.4f}")          # 時間価値減衰（配当効果含む）
print(f"Rho: {greeks.rho:.4f}")              # 金利感応度
print(f"Dividend Rho: {greeks.dividend_rho:.4f}")  # 配当利回り感応度（Merton特有）
```

### インプライドボラティリティ

市場価格からボラティリティを逆算：

```python
# パラメータ: price, s, k, t, r, q, is_call
iv = merton.implied_volatility(10.45, 100.0, 100.0, 1.0, 0.05, 0.03, True)
print(f"Implied Volatility: {iv:.4f}")
```

## パラメータ説明

### 入力パラメータ

| パラメータ | 型 | 説明 | 有効範囲 |
|-----------|-----|------|----------|
| `s` | float | スポット価格（現在の資産価格） | > 0 |
| `k` | float | 権利行使価格（ストライク） | > 0 |
| `t` | float | 満期までの時間（年） | > 0 |
| `r` | float | 無リスク金利（年率） | 任意 |
| `q` | float | 配当利回り（年率） | ≥ 0 |
| `sigma` | float | ボラティリティ（年率） | > 0 |
| `is_call` | bool | オプションタイプ | True: コール, False: プット |

### バッチ処理用パラメータ

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `spots` | np.ndarray | 複数のスポット価格 |
| `qs` | np.ndarray | 複数の配当利回り |
| `k` | float | 権利行使価格（共通） |
| `t` | float | 満期までの時間（共通） |
| `r` | float | 無リスク金利（共通） |
| `q` | float | 配当利回り（共通、spots使用時） |
| `sigma` | float | ボラティリティ（共通） |

## 価格式（参考）

コールオプション:
$$C = S_0 \cdot e^{-qT} \cdot N(d_1) - K \cdot e^{-rT} \cdot N(d_2)$$

プットオプション:
$$P = K \cdot e^{-rT} \cdot N(-d_2) - S_0 \cdot e^{-qT} \cdot N(-d_1)$$

where:
- $d_1 = \frac{\ln(S_0/K) + (r - q + \sigma^2/2)T}{\sigma\sqrt{T}}$
- $d_2 = d_1 - \sigma\sqrt{T}$

詳細な理論的背景は[Mertonモデル理論](../../models/merton.md)を参照してください。

## エラーハンドリング

すべての価格計算関数は以下の条件でエラーを返します：

- s ≤ 0（スポット価格が負または0）
- k ≤ 0（権利行使価格が負または0）
- t < 0（満期までの時間が負）
- sigma ≤ 0（ボラティリティが負または0）
- q < 0（配当利回りが負）
- 数値がNaNまたは無限大
- q > 1.0（配当利回りが100%超 - 警告）

```python
try:
    # パラメータ: s, k, t, r, q(negative), sigma
    price = merton.call_price(100, 100, 1.0, 0.05, -0.03, 0.2)  # 無効な負の配当
except ValueError as e:
    print(f"入力エラー: {e}")
```

## パフォーマンス指標

:::{note}
測定環境: AMD Ryzen 5 5600G、CUIモード
:::

| 操作 | 単一計算 | 100万件バッチ |
|------|----------|--------------:|
| コール/プット価格 | 計測予定 | 計測予定 |
| 全グリークス（6種） | 計測予定 | 計測予定 |
| インプライドボラティリティ | 計測予定 | 計測予定 |

## 使用例

### 高配当株式のオプション価格

```python
from quantforge.models import merton

# 高配当株（配当利回り4%）
s = 50.0
k = 52.0
t = 0.5  # 6ヶ月
r = 0.05
q = 0.04  # 4%の配当利回り
sigma = 0.3

# 価格計算
call_price = merton.call_price(s, k, t, r, q, sigma)
put_price = merton.put_price(s, k, t, r, q, sigma)

print(f"Call Price: ${call_price:.2f}")
print(f"Put Price: ${put_price:.2f}")

# グリークス計算
greeks = merton.greeks(s, k, t, r, q, sigma, is_call=True)
print(f"Delta: {greeks.delta:.4f}")
print(f"Dividend Rho: {greeks.dividend_rho:.4f}")  # 配当感応度
```

### 株価指数オプション（S&P 500）

```python
import numpy as np
from quantforge.models import merton

# S&P 500指数オプション
s = 4500.0
strikes = np.linspace(4300, 4700, 9)
t = 0.25  # 3ヶ月
r = 0.045
q = 0.018  # S&P 500の典型的な配当利回り
sigma = 0.16

# 各ストライクで価格計算
for k in strikes:
    # パラメータ: s, k, t, r, q, sigma
    call = merton.call_price(s, k, t, r, q, sigma)
    put = merton.put_price(s, k, t, r, q, sigma)
    
    moneyness = "ATM" if abs(s - k) < 50 else ("ITM" if s > k else "OTM")
    print(f"K={k:.0f} ({moneyness}): Call=${call:.2f}, Put=${put:.2f}")
```

## 関連情報

- [Black-Scholesモデル API](black_scholes.md) - 配当なしの基本モデル
- [Black76モデル API](black76.md) - 商品・先物オプション向け
- [インプライドボラティリティAPI](implied_vol.md) - IV計算の詳細
- [Mertonモデル理論的背景](../../models/merton.md) - 数学的詳細