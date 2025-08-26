# 価格計算API

オプション価格計算のための主要な関数群です。

## Black-Scholesモデル

現在、QuantForgeはBlack-Scholesモデルのヨーロピアンオプションをサポートしています。

### モジュールベースAPI（推奨）

より明示的で将来の拡張に対応したAPI構造です。

```python
from quantforge.models import black_scholes

# コールオプション価格
call_price = black_scholes.call_price(
    spot=100.0,    # スポット価格
    strike=105.0,  # 権利行使価格
    time=1.0,      # 満期までの時間（年）
    rate=0.05,     # 無リスク金利
    sigma=0.2      # ボラティリティ
)

# プットオプション価格
put_price = black_scholes.put_price(
    spot=100.0,
    strike=105.0,
    time=1.0,
    rate=0.05,
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
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)

put_prices = black_scholes.put_price_batch(
    spots=spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)
```


## グリークス計算

### モジュールベースAPI（推奨）

```python
from quantforge.models import black_scholes

# 全グリークスを一括計算
greeks = black_scholes.greeks(
    spot=100.0,
    strike=100.0,
    time=1.0,
    rate=0.05,
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

### 標準関数API

```python
import quantforge as qf

# 全グリークス一括計算
greeks = qf.calculate_all_greeks(
    s=100.0,
    k=100.0,
    t=1.0,
    r=0.05,
    sigma=0.2,
    is_call=True
)

# 個別グリークス計算
delta_call = qf.calculate_delta_call(s=100, k=100, t=1.0, r=0.05, sigma=0.2)
delta_put = qf.calculate_delta_put(s=100, k=100, t=1.0, r=0.05, sigma=0.2)
gamma = qf.calculate_gamma(s=100, k=100, t=1.0, r=0.05, sigma=0.2)
vega = qf.calculate_vega(s=100, k=100, t=1.0, r=0.05, sigma=0.2)
theta_call = qf.calculate_theta_call(s=100, k=100, t=1.0, r=0.05, sigma=0.2)
theta_put = qf.calculate_theta_put(s=100, k=100, t=1.0, r=0.05, sigma=0.2)
rho_call = qf.calculate_rho_call(s=100, k=100, t=1.0, r=0.05, sigma=0.2)
rho_put = qf.calculate_rho_put(s=100, k=100, t=1.0, r=0.05, sigma=0.2)
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

### モジュールベースAPI

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `spot` | float | 原資産の現在価格 |
| `strike` | float | オプションの権利行使価格 |
| `time` | float | 満期までの時間（年） |
| `rate` | float | 無リスク金利（年率） |
| `sigma` | float | ボラティリティ（年率） |
| `is_call` | bool | True: コール, False: プット |

### 標準関数API

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `s` | float | 原資産の現在価格（スポット価格） |
| `k` | float | オプションの権利行使価格（ストライク） |
| `t` | float | 満期までの時間（年） |
| `r` | float | 無リスク金利（年率） |
| `sigma` | float | ボラティリティ（年率） |
| `is_call` | bool | True: コール, False: プット |

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
        spot=-100,  # 無効な負の値
        strike=100,
        time=1.0,
        rate=0.05,
        sigma=0.2
    )
except ValueError as e:
    print(f"入力エラー: {e}")
```