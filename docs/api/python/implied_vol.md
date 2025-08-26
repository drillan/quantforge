# インプライドボラティリティAPI

市場価格からボラティリティを逆算する関数群です。Black-Scholesモデル、Black76モデル、Mertonモデルをサポートしています。

## 概要

インプライドボラティリティ（IV）は、市場で観測されるオプション価格から逆算されるボラティリティです。
市場参加者の将来の価格変動に対する期待を反映しています。

## API使用方法

### Black-Scholesモデル

株式オプションの市場価格からIVを計算：

```python
from quantforge.models import black_scholes

# コールオプションのインプライドボラティリティ
# パラメータ: price, s, k, t, r, is_call
iv = black_scholes.implied_volatility(
    10.45,    # 市場価格
    100.0,    # スポット価格
    100.0,    # 権利行使価格
    1.0,      # 満期までの時間（年）
    0.05,     # 無リスク金利
    True      # True: コール, False: プット
)

print(f"Implied Volatility: {iv:.4f}")
```

### Black76モデル

商品先物オプションの市場価格からIVを計算：

```python
from quantforge.models import black76

# 商品先物オプションのインプライドボラティリティ
# パラメータ: price, f, k, t, r, is_call
iv = black76.implied_volatility(
    5.50,     # 市場価格
    75.00,    # フォワード価格
    75.00,    # 権利行使価格
    0.5,      # 満期までの時間（年）
    0.05,     # 無リスク金利
    True      # True: コール, False: プット
)

print(f"Implied Volatility: {iv:.4f}")
```

### Mertonモデル

配当付き資産の市場価格からIVを計算：

```python
from quantforge.models import merton

# 配当付き資産のインプライドボラティリティ
# パラメータ: price, s, k, t, r, q, is_call
iv = merton.implied_volatility(
    10.45,    # 市場価格
    100.0,    # スポット価格
    100.0,    # 権利行使価格
    1.0,      # 満期までの時間（年）
    0.05,     # 無リスク金利
    0.03,     # 配当利回り
    True      # True: コール, False: プット
)

print(f"Implied Volatility: {iv:.4f}")
```

## 計算手法

### Newton-Raphson法

QuantForgeは高速収束のNewton-Raphson法を使用しています：

```
σ_{n+1} = σ_n - f(σ_n) / f'(σ_n)

where:
- f(σ) = Price(σ) - MarketPrice
- f'(σ) = Vega(σ)
```

### 収束条件

- 最大反復回数: 100
- 収束判定: |σ_{n+1} - σ_n| < 1e-8
- 初期値: 0.2（20%）

## パラメータ説明

### 共通パラメータ

| パラメータ | 型 | 説明 | 有効範囲 |
|-----------|-----|------|----------|
| `price` | float | 市場で観測されるオプション価格 | > 0 |
| `k` | float | 権利行使価格 | > 0 |
| `t` | float | 満期までの時間（年） | > 0 |
| `r` | float | 無リスク金利（年率） | 任意 |
| `is_call` | bool | オプションタイプ | True: コール, False: プット |

### モデル固有パラメータ

| パラメータ | Black-Scholes | Black76 | Merton | 説明 |
|-----------|---------------|---------|--------|------|
| 原資産価格 | `s` (スポット) | `f` (フォワード) | `s` (スポット) | 現在価格 vs 将来価格 |
| 配当利回り | - | - | `q` | 配当利回り（年率） |

## エラーハンドリング

以下の条件でエラーが発生します：

### ValueError（入力エラー）
- 市場価格が負またはゼロ
- オプション価格が内在価値を下回る
- 入力パラメータが無効（NaN、無限大）

### RuntimeError（収束エラー）
- Newton-Raphson法が収束しない
- ボラティリティが妥当な範囲（0.001～10.0）外

```python
try:
    # 無効な市場価格（内在価値以下）
    iv = black_scholes.implied_volatility(
        0.01,     # 市場価格が低すぎる
        100.0,    # スポット価格
        50.0,     # 権利行使価格（深いITM）
        1.0,      # 満期
        0.05,     # 金利
        True      # コール
    )
except RuntimeError as e:
    print(f"収束エラー: {e}")
```

## 使用例

### ボラティリティスマイルの計算

```python
import numpy as np
from quantforge.models import black_scholes, black76
import matplotlib.pyplot as plt

# Black-Scholesでのボラティリティスマイル
spot = 100.0
time = 0.25
rate = 0.05
strikes = np.linspace(80, 120, 21)

ivs_bs = []
for strike in strikes:
    # 市場価格を取得（実際のデータまたはシミュレーション）
    market_price = get_market_price_bs(spot, strike)
    is_call = strike >= spot
    
    # パラメータ: price, s, k, t, r, is_call
    iv = black_scholes.implied_volatility(
        market_price, spot, strike, time, rate, is_call
    )
    ivs_bs.append(iv)

# Black76でのボラティリティスマイル（商品市場）
f = 75.0
t = 0.5
r = 0.05
strikes_b76 = np.linspace(60, 90, 21)

ivs_b76 = []
for strike in strikes_b76:
    # 市場価格を取得
    market_price = get_market_price_b76(f, strike)
    is_call = strike >= f
    
    # パラメータ: price, f, k, t, r, is_call
    iv = black76.implied_volatility(
        market_price, f, strike, t, r, is_call
    )
    ivs_b76.append(iv)

# プロット
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.plot(strikes, ivs_bs)
ax1.set_xlabel('Strike')
ax1.set_ylabel('Implied Volatility')
ax1.set_title('Equity Options (Black-Scholes)')

ax2.plot(strikes_b76, ivs_b76)
ax2.set_xlabel('Strike')
ax2.set_ylabel('Implied Volatility')
ax2.set_title('Commodity Options (Black76)')

plt.show()
```

### IV時系列分析

```python
from datetime import datetime, timedelta
from quantforge.models import black_scholes

# ATMオプションのIV推移
spot_prices = [100, 101, 99, 102, 98]
market_prices = [5.2, 5.5, 5.3, 5.7, 5.4]
dates = [datetime.now() + timedelta(days=i) for i in range(5)]

ivs = []
for spot, price in zip(spot_prices, market_prices):
    # パラメータ: price, s, k, t, r, is_call
    iv = black_scholes.implied_volatility(
        price, spot, 100.0, 0.25, 0.05, True
    )
    ivs.append(iv)

# IV推移をプロット
plt.plot(dates, ivs)
plt.xlabel('Date')
plt.ylabel('Implied Volatility')
plt.title('ATM IV Time Series')
plt.xticks(rotation=45)
plt.show()
```

## パフォーマンス

| モデル | 単一計算 | 1000件バッチ |
|--------|----------|--------------|
| Black-Scholes IV | < 200ns | < 200μs |
| Black76 IV | < 200ns | < 200μs |
| Merton IV | < 300ns | < 300μs |

収束性能：
- 平均反復回数: 3-5回
- 最悪ケース: 10-15回（深いOTM/ITM）
- 収束率: > 99.9%

## 注意事項

1. **初期値の重要性**: デフォルトの初期値（20%）は多くの場合で良好に動作しますが、
   極端な市場状況では調整が必要な場合があります。

2. **アービトラージ条件**: 市場価格が理論的な下限（内在価値）を下回る場合、
   IVは計算できません。

3. **数値精度**: 深いOTM/ITMオプションでは数値精度の問題が発生する可能性があります。

## 関連情報

- [Black-Scholesモデル API](black_scholes.md)
- [Black76モデル API](black76.md)
- [Mertonモデル API](merton.md)
- [価格計算API概要](pricing.md)