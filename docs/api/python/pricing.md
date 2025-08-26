# 価格計算API

オプション価格計算のための主要な関数群です。

## Black-Scholesモデル

現在、QuantForgeはBlack-Scholesモデルのヨーロピアンオプションをサポートしています。

### API使用方法

```python
from quantforge.models import black_scholes

# コールオプション価格
call_price = black_scholes.call_price(
    s=100.0,      # スポット価格
    k=105.0,      # 権利行使価格
    t=1.0,        # 満期までの時間（年）
    r=0.05,       # 無リスク金利
    sigma=0.2     # ボラティリティ
)

# プットオプション価格
put_price = black_scholes.put_price(
    s=100.0,
    k=105.0,
    t=1.0,
    r=0.05,
    sigma=0.2
)
```

#### バッチ処理

```python
import numpy as np

# 複数のスポット価格でバッチ計算
spots = np.array([95, 100, 105, 110])
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
```


## グリークス計算

```python
from quantforge.models import black_scholes

# 全グリークスを一括計算
greeks = black_scholes.greeks(
    s=100.0,
    k=100.0,
    t=1.0,
    r=0.05,
    sigma=0.2,
    is_call=True  # True: コール, False: プット
)

# 個別のグリークスへアクセス
print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
print(f"Theta: {greeks.theta:.4f}")
print(f"Rho: {greeks.rho:.4f}")
```


## 数式

### Black-Scholesモデル

ヨーロピアンコールオプション:
$$C = S_0 \cdot N(d_1) - K \cdot e^{-rT} \cdot N(d_2)$$

ヨーロピアンプットオプション:
$$P = K \cdot e^{-rT} \cdot N(-d_2) - S_0 \cdot N(-d_1)$$

where:
- $d_1 = \frac{\ln(S_0/K) + (r + \sigma^2/2)T}{\sigma\sqrt{T}}$
- $d_2 = d_1 - \sigma\sqrt{T}$
- $N(x)$: 標準正規分布の累積分布関数

## パラメータ説明

### API パラメータ

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `s` | float | 原資産の現在価格（スポット価格） |
| `k` | float | オプションの権利行使価格（ストライク） |
| `t` | float | 満期までの時間（年） |
| `r` | float | 無リスク金利（年率） |
| `sigma` | float | ボラティリティ（年率） |
| `is_call` | bool | True: コール, False: プット |

#### バッチ処理用パラメータ

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `spots` | np.ndarray | 複数のスポット価格 |
| `k` | float | オプションの権利行使価格（ストライク） |
| `t` | float | 満期までの時間（年） |
| `r` | float | 無リスク金利（年率） |
| `sigma` | float | ボラティリティ（年率） |

## パフォーマンス指標

| 操作 | 単一計算 | 100万件バッチ |
|------|----------|--------------|
| コール/プット価格 | < 10ns | < 20ms |
| 全グリークス | < 50ns | < 100ms |
| インプライドボラティリティ | < 200ns | < 500ms |

## エラーハンドリング

すべての価格計算関数は以下の条件でエラーを返します：

- スポット価格が負または0
- 権利行使価格が負または0
- 満期までの時間が負
- ボラティリティが負
- 数値がNaNまたは無限大

```python
try:
    price = black_scholes.call_price(
        s=-100,  # 無効な負の値
        k=100,
        t=1.0,
        r=0.05,
        sigma=0.2
    )
except ValueError as e:
    print(f"入力エラー: {e}")
```