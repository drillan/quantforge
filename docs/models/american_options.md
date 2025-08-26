---
future_feature: true
---

# アメリカンオプション

:::{warning}
このページで説明されている機能は現在開発中です。
現在利用可能なのは[Black-Scholesモデル](black_scholes.md)のみです。
実装予定時期については[ロードマップ](../roadmap.md)をご確認ください。
:::

早期行使権を持つオプションの価格評価モデルです（将来実装予定）。

## Bjerksund-Stensland 2002モデル

### 概要

アメリカンオプションの解析的近似解を提供する高精度なモデルです。

### 特徴

- **高精度**: 誤差 < 0.1%
- **高速**: 数値解法より100倍以上高速
- **安定性**: 極端なパラメータでも安定

### 数式

アメリカンコールの価格：

$$C_{Am} = \alpha S_0^{\beta} - \alpha \phi(S_0, T, \beta, I, I) + \phi(S_0, T, 1, I, I) - \phi(S_0, T, 1, K, I) - K\phi(S_0, T, 0, I, I) + K\phi(S_0, T, 0, K, I)$$

ここで、$I$は早期行使境界、$\alpha$と$\beta$は補助パラメータです。

### 早期行使境界

最適行使価格$S^*$は以下の条件を満たします：

$$S^* - K = C(S^*, K, T) + \left(1 - e^{-qT}N(d_1(S^*))\right)S^*$$

### 実装

```python
import quantforge as qf

# アメリカンコール
american_call = qf.american_call(
    spot=100,
    strike=95,
    rate=0.05,
    vol=0.25,
    time=1.0,
    dividend=0.02
)

# アメリカンプット
american_put = qf.american_put(
    spot=100,
    strike=105,
    rate=0.05,
    vol=0.25,
    time=1.0
)
```

## アメリカンプット

### 特殊性

アメリカンプットは早期行使がより重要：
- 深いITMでは即座に行使が最適
- 配当なしでも早期行使プレミアムが存在

### 数値例

```python
# 早期行使プレミアムの計算
spot = 100
strike = 110
rate = 0.05
vol = 0.3
time = 1.0

american = qf.american_put(spot, strike, rate, vol, time)
european = qf.black_scholes_put(spot, strike, rate, vol, time)
premium = american - european

print(f"American Put: ${american:.2f}")
print(f"European Put: ${european:.2f}")
print(f"Early Exercise Premium: ${premium:.2f} ({premium/european*100:.1f}%)")
```

## パフォーマンス

- 単一計算: < 50ns
- バッチ処理: < 50ns/オプション
- 精度: 真値との誤差 < 0.1%