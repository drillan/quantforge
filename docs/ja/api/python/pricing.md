# 価格計算API概要

QuantForgeの価格計算APIは、複数のオプション価格モデルを統一されたインターフェースで提供します。

## サポートされているモデル

### Black-Scholesモデル
株式オプションの標準的な価格モデル。スポット価格を入力として使用します。

```{code-block} python
:name: pricing-code-black-scholes-import
:caption: Black-Scholesモデルのインポート
:linenos:

from quantforge.models import black_scholes

# パラメータ: s(spot), k(strike), t(time), r(rate), sigma
price = black_scholes.call_price(100.0, 105.0, 1.0, 0.05, 0.2)
```

詳細: [Black-Scholesモデル API](black_scholes.md)

### Black76モデル
商品先物・金利デリバティブ向けの価格モデル。フォワード価格を入力として使用します。

```{code-block} python
:name: pricing-code-black76-import
:caption: Black76モデルのインポート
:linenos:

from quantforge.models import black76

# パラメータ: f(forward), k(strike), t(time), r(rate), sigma
price = black76.call_price(75.0, 70.0, 0.25, 0.05, 0.3)
```

詳細: [Black76モデル API](black76.md)

### Mertonモデル
配当を支払う資産のオプション価格モデル。連続的な配当利回りを考慮します。

```{code-block} python
:name: pricing-code-merton-import
:caption: Mertonモデルのインポート
:linenos:

from quantforge.models import merton

# パラメータ: s(spot), k(strike), t(time), r(rate), q(dividend), sigma
price = merton.call_price(100.0, 105.0, 1.0, 0.05, 0.03, 0.2)
```

詳細: [Mertonモデル API](merton.md)

### アメリカンオプションモデル
早期行使権を持つオプションの価格モデル。Bjerksund-Stensland (2002) による高精度近似解を提供します。

```{code-block} python
:name: pricing-code-american-import
:caption: アメリカンオプションモデルのインポート
:linenos:

from quantforge.models import american

# パラメータ: s(spot), k(strike), t(time), r(rate), q(dividend), sigma
price = american.call_price(100.0, 105.0, 1.0, 0.05, 0.03, 0.2)
```

詳細: [アメリカンオプションモデル API](american.md)

## モデルの選択ガイド

### Black-Scholesを使用する場合
- **株式オプション**: 個別株、株価指数オプション
- **配当なしの資産**: 配当を支払わない資産のオプション
- **スポット価格ベース**: 現在の市場価格から直接計算

### Black76を使用する場合
- **商品先物オプション**: 原油、金、農産物などの先物オプション
- **金利デリバティブ**: 金利キャップ、フロア、スワプション
- **フォワード価格ベース**: 将来時点の価格から計算
- **保管コスト・便益利回りがある資産**: 商品の保管コストや便益を考慮

### Mertonモデルを使用する場合
- **高配当株式**: 配当利回りが高い個別株のオプション
- **株価指数オプション**: S&P 500、日経225など配当を反映する指数
- **外国為替オプション**: 外国金利を配当利回りとして扱う
- **配当付き資産**: 定期的な配当・分配金がある資産全般

### アメリカンオプションを使用する場合
- **早期行使が重要な場合**: 配当付き資産、深いITMオプション
- **個別株オプション（配当あり）**: 配当支払い日前の早期行使判定
- **高配当利回り資産**: 早期行使プレミアムが重要
- **プットオプション全般**: アメリカンプットは常にヨーロピアンより高価値

## 共通機能

全モデルは以下の同一機能を提供します：

### 価格計算
```{code-block} python
:name: pricing-call-put-price
:caption: コールオプション価格

# コールオプション価格
call_price = model.call_price(...)

# プットオプション価格  
put_price = model.put_price(...)
```

### バッチ処理
```{code-block} python
:name: pricing-code-batch-processing
:caption: バッチ処理の例
:linenos:

import numpy as np

# 複数の価格で一括計算
prices = np.array([90, 95, 100, 105, 110])
results = model.call_price_batch(prices, ...)
```

### グリークス計算
```{code-block} python
:name: pricing-greeks-calculation
:caption: 全グリークスを一括取得

# 全グリークスを一括取得
greeks = model.greeks(..., is_call=True)

print(f"Delta: {greeks.delta}")  # 原資産価格感応度
print(f"Gamma: {greeks.gamma}")  # デルタの変化率
print(f"Vega: {greeks.vega}")    # ボラティリティ感応度
print(f"Theta: {greeks.theta}")  # 時間減衰
print(f"Rho: {greeks.rho}")      # 金利感応度
```

### インプライドボラティリティ
```{code-block} python
:name: pricing-implied-volatility
:caption: 市場価格からボラティリティを逆算

# 市場価格からボラティリティを逆算
iv = model.implied_volatility(market_price, ...)
```

## パラメータの対応

| パラメータ | Black-Scholes | Black76 | Merton | 説明 |
|-----------|---------------|---------|--------|------|
| 原資産価格 | `s` (spot) | `f` (forward) | `s` (spot) | 現在価格 vs 先物価格 |
| 権利行使価格 | `k` | `k` | `k` | 共通 |
| 満期 | `t` | `t` | `t` | 共通（年単位） |
| 金利 | `r` | `r` | `r` | 共通（年率） |
| 配当利回り | - | - | `q` | Merton固有（年率） |
| ボラティリティ | `sigma` | `sigma` | `sigma` | 共通（年率） |

## パフォーマンス

:::{note}
測定環境: AMD Ryzen 5 5600G、CUIモード
測定方法: 実測値は[ベンチマーク](../../performance/benchmarks.md)を参照
:::

| 操作 | 処理時間 | 備考 |
|------|----------|------|
| 単一価格計算 | 1.4 μs | Black-Scholes実測値 |
| グリークス計算 | 計測予定 | - |
| IV計算 | 1.5 μs | Black-Scholes実測値 |
| バッチ処理（100万件） | 55.6ms | Black-Scholes実測値 |

## 使用例の比較

### 株式オプション（Black-Scholes）
```{code-block} python
:name: pricing-code-stock-options-example
:caption: 株式オプションの例
:linenos:

from quantforge.models import black_scholes

# 現在の株価から計算
spot_price = 100.0
strike = 105.0
time_to_maturity = 0.25
risk_free_rate = 0.05
volatility = 0.2

call_price = black_scholes.call_price(
    spot_price, strike, time_to_maturity, risk_free_rate, volatility
)
```

### 原油先物オプション（Black76）
```{code-block} python
:name: pricing-code-crude-oil-options-example
:caption: 原油先物オプションの例
:linenos:

from quantforge.models import black76

# 先物価格から計算
forward_price = 85.0  # WTI先物価格
strike = 90.0
time_to_maturity = 0.25
risk_free_rate = 0.05
volatility = 0.35

call_price = black76.call_price(
    forward_price, strike, time_to_maturity, risk_free_rate, volatility
)
```

## 詳細ドキュメント

### APIリファレンス
- [Black-Scholesモデル API](black_scholes.md)
- [Black76モデル API](black76.md)
- [Mertonモデル API](merton.md)
- [インプライドボラティリティ API](implied_vol.md)

### 理論的背景
- [Black-Scholesモデル理論](../../models/black_scholes.md)
- [Black76モデル理論](../../models/black76.md)
- [Mertonモデル理論](../../models/merton.md)