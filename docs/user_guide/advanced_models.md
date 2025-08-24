# 高度なモデル

QuantForgeは、Black-Scholesを超えた高度なオプション価格モデルを提供します。

## アメリカンオプション

### Bjerksund-Stensland 2002モデル

```python
import quantforge as qf
import numpy as np

# アメリカンコールオプション
american_call = qf.american_call(
    spot=100,
    strike=95,
    rate=0.05,
    vol=0.25,
    time=1.0,
    dividend=0.02  # 配当利回り
)

# ヨーロピアンとの比較
european_call = qf.black_scholes_call_dividend(
    spot=100,
    strike=95,
    rate=0.05,
    dividend=0.02,
    vol=0.25,
    time=1.0
)

early_exercise_premium = american_call - european_call
print(f"American Call: ${american_call:.2f}")
print(f"European Call: ${european_call:.2f}")
print(f"Early Exercise Premium: ${early_exercise_premium:.2f}")
```

### アメリカンプットオプション

```python
# アメリカンプット（早期行使がより重要）
american_put = qf.american_put(
    spot=100,
    strike=105,
    rate=0.05,
    vol=0.25,
    time=1.0
)

european_put = qf.black_scholes_put(
    spot=100,
    strike=105,
    rate=0.05,
    vol=0.25,
    time=1.0
)

premium = american_put - european_put
print(f"American Put: ${american_put:.2f}")
print(f"European Put: ${european_put:.2f}")
print(f"Early Exercise Premium: ${premium:.2f} ({premium/european_put*100:.1f}%)")
```

### 早期行使境界

```python
# 早期行使境界の計算
def early_exercise_boundary(strike, rate, vol, time_points):
    """各時点での早期行使境界価格"""
    boundaries = []
    for t in time_points:
        if t > 0:
            boundary = qf.american_exercise_boundary(
                strike=strike,
                rate=rate,
                vol=vol,
                time=t,
                option_type="put"
            )
            boundaries.append(boundary)
        else:
            boundaries.append(strike)  # 満期時は行使価格
    
    return np.array(boundaries)

# 時間グリッド
times = np.linspace(0, 1, 50)
boundaries = early_exercise_boundary(100, 0.05, 0.25, times)

# 可視化
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 6))
plt.plot(times, boundaries)
plt.axhline(y=100, color='r', linestyle='--', label='Strike')
plt.xlabel('Time to Maturity')
plt.ylabel('Early Exercise Boundary')
plt.title('American Put Early Exercise Boundary')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

## アジアンオプション

### 算術平均アジアンオプション

```python
# 算術平均価格オプション
asian_call = qf.asian_arithmetic_call(
    spot=100,
    strike=100,
    rate=0.05,
    vol=0.2,
    time=1.0,
    averaging_start=0.0,  # 平均開始時点
    n_fixings=252  # 観測回数（日次）
)

# 対応するヨーロピアンとの比較
european = qf.black_scholes_call(100, 100, 0.05, 0.2, 1.0)
print(f"Asian Call: ${asian_call:.2f}")
print(f"European Call: ${european:.2f}")
print(f"Asian Discount: ${european - asian_call:.2f}")
```

### 幾何平均アジアンオプション

```python
# 幾何平均（解析解あり）
asian_geometric = qf.asian_geometric_call(
    spot=100,
    strike=100,
    rate=0.05,
    vol=0.2,
    time=1.0
)

print(f"Geometric Asian: ${asian_geometric:.2f}")
```

### 既観測価格を考慮

```python
# 部分的に観測済みのアジアンオプション
observed_prices = [98, 102, 101, 99, 103]  # 既に観測された価格
remaining_time = 0.5  # 残り期間

adjusted_asian = qf.asian_call_partial(
    spot=103,  # 現在価格
    strike=100,
    rate=0.05,
    vol=0.2,
    remaining_time=remaining_time,
    observed_average=np.mean(observed_prices),
    n_observed=len(observed_prices),
    n_total=252  # 総観測回数
)

print(f"Partial Asian Call: ${adjusted_asian:.2f}")
```

## スプレッドオプション

### Kirk近似によるスプレッドオプション

```python
# 2資産間のスプレッドオプション
spread_call = qf.spread_option_kirk(
    spot1=100,    # 資産1の現在価格
    spot2=95,     # 資産2の現在価格
    strike=5,     # スプレッドの行使価格
    rate=0.05,
    vol1=0.25,    # 資産1のボラティリティ
    vol2=0.30,    # 資産2のボラティリティ
    correlation=0.7,  # 相関係数
    time=1.0
)

print(f"Spread Option: ${spread_call:.2f}")
```

### マルコフ・スプレッドオプション

```python
# より精密なマルコフモデル
spread_markov = qf.spread_option_markov(
    spot1=100,
    spot2=95,
    strike=5,
    rate=0.05,
    vol1=0.25,
    vol2=0.30,
    correlation=0.7,
    time=1.0,
    n_steps=100  # 時間ステップ数
)

print(f"Markov Spread: ${spread_markov:.2f}")
```

## バリアオプション

### ノックイン/ノックアウトオプション

```python
# アップアンドアウト・コールオプション
barrier_call = qf.barrier_call(
    spot=100,
    strike=105,
    barrier=120,  # バリアレベル
    rate=0.05,
    vol=0.25,
    time=1.0,
    barrier_type="up_and_out",
    rebate=0  # リベート（バリアヒット時の支払い）
)

vanilla_call = qf.black_scholes_call(100, 105, 0.05, 0.25, 1.0)
print(f"Barrier Call: ${barrier_call:.2f}")
print(f"Vanilla Call: ${vanilla_call:.2f}")
print(f"Barrier Discount: ${vanilla_call - barrier_call:.2f}")
```

### ダブルバリアオプション

```python
# ダブルバリア（上下両方）
double_barrier = qf.double_barrier_call(
    spot=100,
    strike=100,
    lower_barrier=80,
    upper_barrier=120,
    rate=0.05,
    vol=0.25,
    time=1.0
)

print(f"Double Barrier Call: ${double_barrier:.2f}")
```

## ルックバックオプション

### 固定行使価格ルックバック

```python
# 期間中の最大値に基づくコール
lookback_call = qf.lookback_call_fixed(
    spot=100,
    strike=95,
    rate=0.05,
    vol=0.25,
    time=1.0
)

print(f"Fixed Strike Lookback Call: ${lookback_call:.2f}")
```

### 変動行使価格ルックバック

```python
# 最適な行使価格を選択
lookback_floating = qf.lookback_call_floating(
    spot=100,
    min_observed=95,  # これまでの最小値
    rate=0.05,
    vol=0.25,
    time=1.0
)

print(f"Floating Strike Lookback: ${lookback_floating:.2f}")
```

## デジタル（バイナリー）オプション

### キャッシュオアナッシング

```python
# デジタルコール（満期時にITMなら固定額支払い）
digital_call = qf.digital_call(
    spot=100,
    strike=105,
    rate=0.05,
    vol=0.25,
    time=1.0,
    cash_amount=10  # 支払額
)

# 確率計算
prob_itm = qf.probability_itm(
    spot=100,
    strike=105,
    rate=0.05,
    vol=0.25,
    time=1.0,
    option_type="call"
)

print(f"Digital Call Value: ${digital_call:.2f}")
print(f"Probability of ITM: {prob_itm:.1%}")
```

### アセットオアナッシング

```python
# 資産払いデジタルオプション
asset_or_nothing = qf.asset_or_nothing_call(
    spot=100,
    strike=105,
    rate=0.05,
    vol=0.25,
    time=1.0
)

print(f"Asset-or-Nothing Call: ${asset_or_nothing:.2f}")
```

## 複合オプション戦略

### ストラドル

```python
def straddle_value(spot, strike, rate, vol, time):
    """ストラドル（同一行使価格のコール+プット）"""
    call = qf.black_scholes_call(spot, strike, rate, vol, time)
    put = qf.black_scholes_put(spot, strike, rate, vol, time)
    return call + put

# ストラドルのペイオフ
spots = np.linspace(80, 120, 100)
straddle_values = [straddle_value(s, 100, 0.05, 0.25, 0.25) for s in spots]

plt.figure(figsize=(10, 6))
plt.plot(spots, straddle_values, label='Straddle Value')
plt.axvline(x=100, color='r', linestyle='--', alpha=0.5, label='Strike')
plt.xlabel('Spot Price')
plt.ylabel('Strategy Value')
plt.title('Straddle Payoff')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

### バタフライスプレッド

```python
def butterfly_spread(spot, k1, k2, k3, rate, vol, time):
    """バタフライスプレッド"""
    c1 = qf.black_scholes_call(spot, k1, rate, vol, time)
    c2 = qf.black_scholes_call(spot, k2, rate, vol, time)
    c3 = qf.black_scholes_call(spot, k3, rate, vol, time)
    return c1 - 2*c2 + c3

# バタフライの価値
spots = np.linspace(85, 115, 100)
butterfly = [butterfly_spread(s, 95, 100, 105, 0.05, 0.25, 0.25) for s in spots]

plt.figure(figsize=(10, 6))
plt.plot(spots, butterfly)
plt.axvline(x=95, color='r', linestyle='--', alpha=0.3)
plt.axvline(x=100, color='r', linestyle='--', alpha=0.3)
plt.axvline(x=105, color='r', linestyle='--', alpha=0.3)
plt.xlabel('Spot Price')
plt.ylabel('Butterfly Value')
plt.title('Butterfly Spread')
plt.grid(True, alpha=0.3)
plt.show()
```

## モデル比較

### 各モデルのパフォーマンス比較

```python
# 異なるモデルの計算時間比較
import time

n = 100000
spots = np.random.uniform(90, 110, n)

models = {
    'Black-Scholes': lambda s: qf.black_scholes_call(s, 100, 0.05, 0.2, 1.0),
    'American': lambda s: qf.american_call(s, 100, 0.05, 0.2, 1.0),
    'Asian': lambda s: qf.asian_arithmetic_call(s, 100, 0.05, 0.2, 1.0),
    'Barrier': lambda s: qf.barrier_call(s, 100, 120, 0.05, 0.2, 1.0, "up_and_out"),
}

for name, func in models.items():
    start = time.perf_counter()
    prices = [func(s) for s in spots[:1000]]  # サンプル計算
    elapsed = time.perf_counter() - start
    print(f"{name:15s}: {elapsed*1000:.2f}ms for 1000 options")
```

## まとめ

高度なモデルにより以下が可能になります：

- **アメリカンオプション**: 早期行使権の評価
- **アジアンオプション**: パス依存型オプション
- **スプレッドオプション**: 複数資産の相対価値
- **バリアオプション**: 条件付きペイオフ
- **複合戦略**: 実務で使用される戦略の評価

次は[実践例](examples.md)で、実際のユースケースを見ていきましょう。