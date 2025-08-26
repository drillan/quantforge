# Black76 モデル API

商品先物・エネルギーオプションの価格計算のためのBlack76モデルです。

## 概要

Black76モデルは、先物やフォワード契約のオプション価格を計算するためのモデルです。
主に商品（コモディティ）、金利、エネルギー市場で使用されます。

スポット価格ではなくフォワード価格を使用することで、保管コストや便益利回りを
暗黙的に考慮できるため、商品市場で広く利用されています。

詳細な理論的背景は[Black76モデル理論](../../models/black76.md)を参照してください。

## API使用方法

```python
from quantforge.models import black76

# 商品先物のコールオプション価格
# パラメータ: f(forward), k(strike), t(time), r(rate), sigma
call_price = black76.call_price(75.50, 70.00, 0.25, 0.05, 0.3)

# 商品先物のプットオプション価格  
# パラメータ: f(forward), k(strike), t(time), r(rate), sigma
put_price = black76.put_price(75.50, 80.00, 0.25, 0.05, 0.3)
```

## 価格計算関数

### call_price

商品先物のコールオプション価格を計算します。

```python
def call_price(forward, strike, time, rate, sigma) -> float:
    """
    Black76モデルによるコールオプション価格
    
    Parameters:
        forward (float): フォワード価格
        strike (float): 権利行使価格
        time (float): 満期までの時間（年）
        rate (float): リスクフリーレート（年率）
        sigma (float): ボラティリティ（年率）
    
    Returns:
        float: コールオプション価格
    """
```

### put_price

商品先物のプットオプション価格を計算します。

```python
def put_price(forward, strike, time, rate, sigma) -> float:
    """
    Black76モデルによるプットオプション価格
    
    Parameters:
        forward (float): フォワード価格
        strike (float): 権利行使価格
        time (float): 満期までの時間（年）
        rate (float): リスクフリーレート（年率）
        sigma (float): ボラティリティ（年率）
    
    Returns:
        float: プットオプション価格
    """
```

### バッチ計算

```python
# 複数のフォワード価格でのコール価格
import numpy as np

forwards = np.array([70, 75, 80, 85])
# パラメータ: forwards, k, t, r, sigma
call_prices = black76.call_price_batch(forwards, 75.0, 0.5, 0.05, 0.25)
```

## グリークス計算

### greeks

Black76モデルのグリークス（感応度）を計算します。

```python
# パラメータ: f(forward), k(strike), t(time), r(rate), sigma, is_call
greeks = black76.greeks(75.50, 75.00, 0.5, 0.05, 0.3, True)

print(f"Delta: {greeks.delta:.4f}")  # フォワード価格に対する感応度
print(f"Gamma: {greeks.gamma:.4f}")  # デルタの変化率
print(f"Vega: {greeks.vega:.4f}")    # ボラティリティ感応度
print(f"Theta: {greeks.theta:.4f}")  # 時間価値減衰
print(f"Rho: {greeks.rho:.4f}")      # 金利感応度
```

### グリークスの意味

| グリーク | 説明 | 計算式 |
|---------|------|--------|
| Delta | フォワード価格に対する価格感応度 | ∂V/∂F |
| Gamma | デルタの変化率 | ∂²V/∂F² |
| Vega | ボラティリティに対する感応度 | ∂V/∂σ |
| Theta | 時間経過に対する価値減少 | -∂V/∂T |
| Rho | 金利に対する感応度 | ∂V/∂r |

## インプライドボラティリティ

市場価格からボラティリティを逆算します。

```python
# 市場価格からインプライドボラティリティを計算
# パラメータ: price, f(forward), k(strike), t(time), r(rate), is_call
iv = black76.implied_volatility(5.50, 75.00, 75.00, 0.5, 0.05, True)

print(f"Implied Volatility: {iv:.4f}")
```

## スポット価格からフォワード価格への変換

Black76モデルはフォワード価格を入力として使用しますが、
スポット価格からフォワード価格への変換が必要な場合があります。

```python
def spot_to_forward(spot, rate, div_yield, time) -> float:
    """
    スポット価格からフォワード価格への変換
    
    F = S * exp((r - q) * T)
    
    Parameters:
        spot (float): スポット価格
        rate (float): リスクフリーレート
        div_yield (float): 配当利回り（商品の保管コストや便益利回り）
        time (float): 満期までの時間
    
    Returns:
        float: フォワード価格
    """
    import math
    return spot * math.exp((rate - div_yield) * time)

# 使用例
spot = 70.00
rate = 0.05
div_yield = 0.02  # 便益利回り
time = 0.5

forward = spot_to_forward(spot, rate, div_yield, time)
# パラメータ: f(forward), k(strike), t(time), r(rate), sigma
price = black76.call_price(forward, 75.0, time, rate, 0.3)
```

## Black-Scholesモデルとの比較

| 特徴 | Black-Scholes | Black76 |
|------|--------------|---------|
| 入力価格 | スポット価格（現在価格） | フォワード価格（将来価格） |
| 主な用途 | 株式オプション | 商品・金利デリバティブ |
| パラメータ | s, k, t, r, sigma | f, k, t, r, sigma |
| 配当・保管コスト | 明示的に扱う必要あり | フォワード価格に暗黙的に含む |

詳細な数学的関係は[Black76モデル理論](../../models/black76.md#black-scholesとの関係)を参照してください。

## 使用例

### エネルギー市場（原油先物）

```python
from quantforge.models import black76

# WTI原油先物オプション
wti_forward = 85.00  # 先物価格
strike = 90.00
time_to_maturity = 0.25  # 3ヶ月
rate = 0.05  # リスクフリーレート
wti_volatility = 0.35  # WTI標準的ボラティリティ

# パラメータ: f(forward), k(strike), t(time), r(rate), sigma
call_price = black76.call_price(
    wti_forward, strike, time_to_maturity, rate, wti_volatility
)

print(f"WTI Call Option Price: ${call_price:.2f}")
```

### 農産物市場（コーン先物）

```python
from quantforge.models import black76

# コーン先物オプション
corn_forward = 650.00  # セント/ブッシェル
strike = 675.00
time_to_maturity = 0.5  # 6ヶ月
rate = 0.05  # リスクフリーレート
corn_volatility = 0.25  # コーン標準的ボラティリティ

# パラメータ: f(forward), k(strike), t(time), r(rate), sigma
put_price = black76.put_price(
    corn_forward, strike, time_to_maturity, rate, corn_volatility
)

# ブッシェルあたりのセントからドルに変換
put_price_dollars = put_price / 100
print(f"Corn Put Option Price: ${put_price_dollars:.2f}/bushel")
```

### ボラティリティスマイルの計算

```python
import numpy as np
import matplotlib.pyplot as plt
from quantforge.models import black76

# 異なる権利行使価格でのインプライドボラティリティ
forward = 100.0
strikes = np.linspace(80, 120, 21)
time = 0.25
rate = 0.05

# 市場価格（仮定）
market_prices = []
for strike in strikes:
    # 実際には市場データから取得
    if strike < forward:
        # OTMプット
        # パラメータ: f, k, t, r, sigma
        price = black76.put_price(forward, strike, time, rate, 0.25)
    else:
        # OTMコール
        # パラメータ: f, k, t, r, sigma
        price = black76.call_price(forward, strike, time, rate, 0.25)
    market_prices.append(price)

# IV計算
ivs = []
for strike, price in zip(strikes, market_prices):
    is_call = strike >= forward
    # パラメータ: price, f, k, t, r, is_call
    iv = black76.implied_volatility(
        price, forward, strike, time, rate, is_call
    )
    ivs.append(iv)

# プロット
plt.plot(strikes, ivs)
plt.xlabel('Strike')
plt.ylabel('Implied Volatility')
plt.title('Black76 Volatility Smile')
plt.grid(True)
plt.show()
```

## パラメータ制限

### 入力値の有効範囲

| パラメータ | 最小値 | 最大値 | 単位 |
|-----------|--------|--------|------|
| forward | 0.001 | 10^6 | 価格単位 |
| strike | 0.001 | 10^6 | 価格単位 |
| time | 1/365 | 100 | 年 |
| rate | -0.1 | 1.0 | 年率 |
| sigma | 0.001 | 10.0 | 年率 |

### エラー条件

以下の場合、`ValueError`が発生します：

- forward ≤ 0 または strike ≤ 0
- time ≤ 0
- sigma ≤ 0
- 入力値がNaNまたは無限大

## パフォーマンス

| 計算タイプ | 処理時間 | スループット |
|-----------|----------|--------------|
| 単一価格計算 | < 12ns | 8300万回/秒 |
| グリークス計算 | < 60ns | 1600万回/秒 |
| IV計算（Newton法） | < 250ns | 400万回/秒 |
| バッチ処理（100万件） | < 25ms | 4000万件/秒 |

## 精度

| 指標 | 目標値 | 実測値 |
|------|--------|--------|
| 価格精度（相対誤差） | < 10^-6 | < 10^-8 |
| グリークス精度 | < 10^-5 | < 10^-7 |
| Put-Callパリティ | < 10^-10 | < 10^-12 |
| IV精度 | < 10^-8 | < 10^-10 |

## 注意事項

1. **フォワード価格の使用**: Black76はスポット価格ではなくフォワード価格を使用
2. **金利の役割**: 割引のみに使用（ドリフト項には現れない）
3. **配当の扱い**: フォワード価格に暗黙的に含まれる
4. **満期時点**: フォワード契約の満期とオプションの満期が一致する前提

## 関連モデル

以下のモデルは独立して実装されます（Black76の拡張ではありません）：

- **Asian76**: アジアンオプション（平均価格オプション）
- **Kirk's Approximation**: スプレッドオプション
- **Seasonal Models**: 季節性を考慮した商品オプション

## 参考文献

- Black, F. (1976). "The pricing of commodity contracts", Journal of Financial Economics, 3(1-2), 167-179.
- Hull, J. C. (2018). "Options, Futures, and Other Derivatives", 10th Edition.
- Haug, E. G. (2007). "The Complete Guide to Option Pricing Formulas", 2nd Edition.