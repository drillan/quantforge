# 基本的な使い方

QuantForgeの基本的な関数とBlack-Scholesモデルを使ったオプション価格計算を学びます。

## インポート

```python
from quantforge.models import black_scholes
```

## Black-Scholesモデル

### 基本的な価格計算

```python
from quantforge.models import black_scholes

# コールオプション価格
call_price = black_scholes.call_price(
    s=100.0,      # 現在価格
    k=110.0,      # 権利行使価格
    t=1.0,        # 満期までの時間（年）
    r=0.05,       # 無リスク金利（年率）
    sigma=0.2     # ボラティリティ（年率）
)

# プットオプション価格
put_price = black_scholes.put_price(
    s=100.0,
    k=110.0,
    t=1.0,
    r=0.05,
    sigma=0.2
)

print(f"Call Option Price: ${call_price:.2f}")
print(f"Put Option Price: ${put_price:.2f}")

# Put-Callパリティの検証
import numpy as np
parity = call_price - put_price
theoretical = 100.0 - 110.0 * np.exp(-0.05 * 1.0)
print(f"Put-Call Parity Check: {abs(parity - theoretical) < 1e-10}")
```


## グリークス計算

### 全グリークスの一括計算

```python
from quantforge.models import black_scholes

# 全グリークスを一括計算（効率的）
greeks = black_scholes.greeks(
    s=100.0,
    k=100.0,
    t=1.0,
    r=0.05,
    sigma=0.2,
    is_call=True
)

print("Call Option Greeks:")
print(f"  Delta: {greeks.delta:.4f}")
print(f"  Gamma: {greeks.gamma:.4f}")
print(f"  Vega:  {greeks.vega:.4f}")
print(f"  Theta: {greeks.theta:.4f}")
print(f"  Rho:   {greeks.rho:.4f}")
```


## 複数オプションの同時計算

### バッチ処理（NumPy配列）

```python
import numpy as np
from quantforge.models import black_scholes

# 複数のスポット価格
spots = np.array([95, 100, 105, 110])

# バッチ計算（高速）
call_prices = black_scholes.call_price_batch(
    spots=spots,
    k=100.0,
    t=1.0,
    r=0.05,
    sigma=0.2
)

put_prices = black_scholes.put_price_batch(
    spots=spots,
    k=100.0,
    t=1.0,
    r=0.05,
    sigma=0.2
)

for i, (spot, call, put) in enumerate(zip(spots, call_prices, put_prices)):
    print(f"Spot {spot}: Call=${call:.2f}, Put=${put:.2f}")
```

### 複数のパラメータセット

```python
# 異なる満期のオプション
times = [0.25, 0.5, 1.0, 2.0]
for time_val in times:
    price = black_scholes.call_price(
        s=100.0,
        k=100.0,
        t=time_val,
        r=0.05,
        sigma=0.2
    )
    print(f"Maturity {t} years: ${price:.2f}")
```

## インプライドボラティリティ

### 単一のIV計算

```python
from quantforge.models import black_scholes

# 市場価格からボラティリティを逆算
market_price = 10.45
iv = black_scholes.implied_volatility(
    price=market_price,
    s=100.0,
    k=100.0,
    t=1.0,
    r=0.05,
    is_call=True
)

print(f"Implied Volatility: {iv:.1%}")

# 精度の検証
calculated_price = black_scholes.call_price(s=100, k=100, t=1.0, r=0.05, sigma=iv)
print(f"Price Check: Market={market_price:.2f}, Calculated={calculated_price:.2f}")
```

### IVスマイルの分析

```python
import numpy as np
from quantforge.models import black_scholes

# 異なる権利行使価格
spot = 100.0
strikes = np.array([80, 90, 100, 110, 120])
sigma_true = 0.2

# 各ストライクの理論価格を計算
market_prices = []
for strike in strikes:
    price = black_scholes.call_price(s=spot, k=strike, t=1.0, r=0.05, sigma=sigma_true)
    market_prices.append(price)

# IVを逆算
for strike, price in zip(strikes, market_prices):
    iv = black_scholes.implied_volatility(
        price=price, s=spot, k=strike, t=1.0, r=0.05, is_call=True
    )
    print(f"Strike {k}: IV={iv:.1%}")
```

## リスク管理への応用

### デルタヘッジ

```python
from quantforge.models import black_scholes

# ポジション情報
spot = 100.0
strike = 105.0
time = 0.5
rate = 0.05
sigma = 0.25

# オプションのデルタ計算
greeks = black_scholes.greeks(s=spot, k=strike, t=time, r=rate, sigma=sigma, is_call=True)
delta = greeks.delta

# デルタヘッジに必要な株式数
option_contracts = 100  # 100契約
hedge_shares = -option_contracts * delta * 100  # 各契約は100株

print(f"Delta: {delta:.4f}")
print(f"Hedge position: {hedge_shares:.0f} shares")
```

### ポートフォリオのグリークス

```python
# 複数オプションのポートフォリオ
positions = [
    {"spot": 100, "strike": 95, "time": 0.5, "contracts": 10, "is_call": True},
    {"spot": 100, "strike": 105, "time": 0.5, "contracts": -5, "is_call": False},
    {"spot": 100, "strike": 100, "time": 1.0, "contracts": 8, "is_call": True},
]

# ポートフォリオ全体のグリークス
total_delta = 0
total_gamma = 0
total_vega = 0

for pos in positions:
    greeks = black_scholes.greeks(
        s=pos["spot"], k=pos["strike"], t=pos["time"], 
        r=0.05, sigma=0.2, is_call=pos["is_call"]
    )
    total_delta += pos["contracts"] * greeks.delta * 100
    total_gamma += pos["contracts"] * greeks.gamma * 100
    total_vega += pos["contracts"] * greeks.vega * 100

print(f"Portfolio Greeks:")
print(f"  Total Delta: {total_delta:.2f}")
print(f"  Total Gamma: {total_gamma:.2f}")
print(f"  Total Vega:  {total_vega:.2f}")
```

## パフォーマンス測定

```python
import time
import numpy as np
from quantforge.models import black_scholes

# 大規模バッチ処理のベンチマーク
n = 1_000_000
spots = np.random.uniform(90, 110, n)

start = time.perf_counter()
prices = black_scholes.call_price_batch(spots=spots, k=100, t=1.0, r=0.05, sigma=0.2)
elapsed = (time.perf_counter() - start) * 1000

print(f"Processed {n:,} options in {elapsed:.1f}ms")
print(f"Average time per option: {elapsed/n*1000:.1f}ns")
# 期待される結果（AMD Ryzen 5 5600G）: 約55.6ms、56ns/option
```

詳細な測定結果とマシン別の性能は[ベンチマーク](../performance/benchmarks.md)を参照してください。