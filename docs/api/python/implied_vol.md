# インプライドボラティリティAPI

市場価格からボラティリティを逆算する関数群です。

## モジュールベースAPI（推奨）

```python
from quantforge.models import black_scholes

# コールオプションのインプライドボラティリティ
iv = black_scholes.implied_volatility(
    price=10.45,      # 市場価格
    spot=100.0,       # スポット価格
    strike=100.0,     # 権利行使価格
    time=1.0,         # 満期までの時間（年）
    rate=0.05,        # 無リスク金利
    is_call=True      # True: コール, False: プット
)

print(f"Implied Volatility: {iv:.4f}")
```

## 標準関数API

### 個別計算

```python
import quantforge as qf

# コールオプションのIV
iv_call = qf.calculate_implied_volatility_call(
    price=10.45,      # 市場価格
    s=100.0,          # スポット価格
    k=100.0,          # 権利行使価格
    t=1.0,            # 満期までの時間（年）
    r=0.05            # 無リスク金利
)

# プットオプションのIV
iv_put = qf.calculate_implied_volatility_put(
    price=5.57,       # 市場価格
    s=100.0,          # スポット価格
    k=100.0,          # 権利行使価格
    t=1.0,            # 満期までの時間（年）
    r=0.05            # 無リスク金利
)

print(f"Call IV: {iv_call:.4f}, Put IV: {iv_put:.4f}")
```

### バッチ計算

```python
import numpy as np

# 複数の市場価格
market_prices = np.array([10.0, 10.5, 11.0, 11.5])
spots = np.full(4, 100.0)
strikes = np.full(4, 100.0)
times = np.full(4, 1.0)
rates = np.full(4, 0.05)
is_calls = np.array([True, True, True, True])

# バッチIV計算
ivs = qf.calculate_implied_volatility_batch(
    prices=market_prices,
    spots=spots,
    strikes=strikes,
    times=times,
    rates=rates,
    is_calls=is_calls
)

for i, iv in enumerate(ivs):
    print(f"Price {market_prices[i]:.2f} -> IV: {iv:.4f}")
```

## 計算手法

### Newton-Raphson法

QuantForgeは高速収束のNewton-Raphson法を使用しています：

```
σ_{n+1} = σ_n - f(σ_n) / f'(σ_n)
```

where:
- f(σ) = BS(σ) - market_price
- f'(σ) = vega(σ)

### 初期推定値

Brenner-Subrahmanyam近似式を使用：
```
σ_0 ≈ √(2π/T) × (market_price / spot)
```

### Brent法へのフォールバック

Newton-Raphson法が収束しない場合、より堅牢なBrent法に自動的に切り替わります。

## パラメータ説明

### モジュールベースAPI

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `price` | float | オプションの市場価格 |
| `spot` | float | 原資産の現在価格 |
| `strike` | float | 権利行使価格 |
| `time` | float | 満期までの時間（年） |
| `rate` | float | 無リスク金利（年率） |
| `is_call` | bool | True: コール, False: プット |

### 標準関数API

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `price` | float | オプションの市場価格 |
| `s` | float | 原資産の現在価格 |
| `k` | float | 権利行使価格 |
| `t` | float | 満期までの時間（年） |
| `r` | float | 無リスク金利（年率） |

## 収束条件

- 最大反復回数: 100回
- 収束精度: 1e-8
- ボラティリティ範囲: 0.001 ～ 10.0 (0.1% ～ 1000%)

## エラーハンドリング

以下の場合、計算エラーとなります：

- 市場価格が理論的境界を超える場合
- 収束しない場合（100回の反復後）
- 入力パラメータが無効な場合

```python
try:
    iv = black_scholes.implied_volatility(
        price=150,     # 非現実的な価格
        spot=100,
        strike=100,
        time=1.0,
        rate=0.05,
        is_call=True
    )
except RuntimeError as e:
    print(f"IV計算エラー: {e}")
```

## 使用例

### ボラティリティスマイルの計算

```python
from quantforge.models import black_scholes
import numpy as np
import matplotlib.pyplot as plt

# 異なる権利行使価格
spot = 100.0
strikes = np.linspace(80, 120, 21)
time = 0.25
rate = 0.05

# 各ストライクの市場価格（仮定）
market_prices = []
for k in strikes:
    # 実際の市場価格を使用
    price = black_scholes.call_price(spot, k, time, rate, sigma=0.2)
    market_prices.append(price)

# IV計算
ivs = []
for k, price in zip(strikes, market_prices):
    iv = black_scholes.implied_volatility(
        price, spot, k, time, rate, is_call=True
    )
    ivs.append(iv)

# プロット
plt.plot(strikes, ivs)
plt.xlabel('Strike')
plt.ylabel('Implied Volatility')
plt.title('Volatility Smile')
plt.show()
```

## パフォーマンス

| ケース | 計算時間 | 反復回数 |
|--------|----------|----------|
| ATM | < 50ns | 3-5 |
| ITM/OTM | < 100ns | 5-10 |
| Deep ITM/OTM | < 200ns | 10-20 |
| バッチ（1万件） | < 2ms | - |

## 注意事項

- Deep OTMオプションは収束が遅い場合があります
- 満期直前のオプションは数値的に不安定になる可能性があります
- 市場価格が理論的下限に近い場合、高い精度が必要です