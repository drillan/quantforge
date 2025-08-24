# 基本的な使い方

QuantForgeの基本的な関数とBlack-Scholesモデルを使ったオプション価格計算を学びます。

## Black-Scholesモデル

### ヨーロピアンコールオプション

```python
import quantforge as qf

# 基本パラメータ
spot = 100.0    # 現在価格
strike = 110.0  # 行使価格
rate = 0.05     # 無リスク金利（年率）
vol = 0.2       # ボラティリティ（年率）
time = 1.0      # 満期までの時間（年）

# コールオプション価格計算
call_price = qf.black_scholes_call(spot, strike, rate, vol, time)
print(f"Call Option Price: ${call_price:.2f}")
```

### ヨーロピアンプットオプション

```python
# プットオプション価格計算
put_price = qf.black_scholes_put(spot, strike, rate, vol, time)
print(f"Put Option Price: ${put_price:.2f}")

# Put-Callパリティの検証
parity = call_price - put_price
theoretical = spot - strike * np.exp(-rate * time)
print(f"Put-Call Parity Check: {abs(parity - theoretical) < 1e-10}")
```

## グリークス計算

### 個別のグリークス

```python
# Delta: 原資産価格に対する感応度
delta_call = qf.delta_call(spot, strike, rate, vol, time)
delta_put = qf.delta_put(spot, strike, rate, vol, time)

# Gamma: Deltaの変化率
gamma = qf.gamma(spot, strike, rate, vol, time)

# Vega: ボラティリティに対する感応度
vega = qf.vega(spot, strike, rate, vol, time)

# Theta: 時間経過に対する感応度
theta_call = qf.theta_call(spot, strike, rate, vol, time)
theta_put = qf.theta_put(spot, strike, rate, vol, time)

# Rho: 金利に対する感応度
rho_call = qf.rho_call(spot, strike, rate, vol, time)
rho_put = qf.rho_put(spot, strike, rate, vol, time)
```

### 一括グリークス計算

```python
# すべてのグリークスを一度に計算（効率的）
result = qf.calculate(
    spots=spot,
    strikes=strike,
    rates=rate,
    vols=vol,
    times=time,
    option_type="call",
    greeks=True
)

print("Call Option Greeks:")
print(f"  Price: ${result['price']:.2f}")
print(f"  Delta: {result['delta']:.4f}")
print(f"  Gamma: {result['gamma']:.4f}")
print(f"  Vega:  {result['vega']:.4f}")
print(f"  Theta: {result['theta']:.4f}")
print(f"  Rho:   {result['rho']:.4f}")
```

## 複数オプションの同時計算

### リスト形式での入力

```python
# 複数のオプションパラメータ
spots = [100, 105, 110]
strikes = [105, 105, 105]
vols = [0.2, 0.22, 0.25]
times = [0.25, 0.5, 1.0]

# バッチ計算
prices = qf.calculate(
    spots=spots,
    strikes=strikes,
    rates=0.05,
    vols=vols,
    times=times,
    option_type="call"
)

for i, price in enumerate(prices):
    print(f"Option {i+1}: ${price:.2f}")
```

### 辞書形式での結果取得

```python
# 構造化された結果を取得
results = qf.calculate_structured(
    spots=[100, 100, 100],
    strikes=[95, 100, 105],
    rates=0.05,
    vols=0.2,
    times=1.0,
    option_type="both"  # コールとプット両方
)

for i, result in enumerate(results):
    print(f"Strike {result['strike']}:")
    print(f"  Call: ${result['call_price']:.2f}")
    print(f"  Put:  ${result['put_price']:.2f}")
```

## インプライドボラティリティ

### 単一のIV計算

```python
# 市場価格からボラティリティを逆算
market_price = 12.5
iv = qf.implied_volatility(
    price=market_price,
    spot=100,
    strike=110,
    rate=0.05,
    time=1.0,
    option_type="call"
)

print(f"Implied Volatility: {iv:.1%}")

# 精度の検証
calculated_price = qf.black_scholes_call(100, 110, 0.05, iv, 1.0)
print(f"Price Check: Market={market_price:.2f}, Calculated={calculated_price:.2f}")
```

### 複数のIV計算

```python
# ボラティリティスマイルの計算
strikes = np.array([90, 95, 100, 105, 110])
market_prices = np.array([15.2, 11.8, 8.5, 5.7, 3.4])

ivs = qf.implied_volatility(
    price=market_prices,
    spot=100,
    strike=strikes,
    rate=0.05,
    time=0.5,
    option_type="call"
)

# ボラティリティスマイルの表示
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.plot(strikes, ivs * 100, 'o-')
plt.xlabel('Strike Price')
plt.ylabel('Implied Volatility (%)')
plt.title('Volatility Smile')
plt.grid(True, alpha=0.3)
plt.show()
```

## 配当付きオプション

```python
# 配当利回りを考慮した計算
dividend_yield = 0.02  # 2%の配当利回り

# 調整後の計算
call_price = qf.black_scholes_call_dividend(
    spot=100,
    strike=105,
    rate=0.05,
    dividend=dividend_yield,
    vol=0.2,
    time=1.0
)

print(f"Call with Dividends: ${call_price:.2f}")
```

## エラーハンドリング

### 入力検証

```python
import quantforge as qf
from quantforge import QuantForgeError

try:
    # 無効な入力（負のボラティリティ）
    price = qf.black_scholes_call(100, 100, 0.05, -0.2, 1.0)
except QuantForgeError as e:
    print(f"Error: {e}")

# 安全な計算関数
def safe_calculate(spot, strike, rate, vol, time):
    """入力検証付き計算"""
    if vol <= 0:
        return None, "Volatility must be positive"
    if time <= 0:
        return None, "Time to maturity must be positive"
    if spot <= 0 or strike <= 0:
        return None, "Spot and strike must be positive"
    
    try:
        return qf.black_scholes_call(spot, strike, rate, vol, time), None
    except Exception as e:
        return None, str(e)
```

### NaN/Inf処理

```python
# 極端な値の処理
extreme_values = [
    (1e-10, 100, 0.05, 0.2, 1.0),  # 極小スポット
    (100, 1e10, 0.05, 0.2, 1.0),   # 極大ストライク
    (100, 100, 0.05, 1e-10, 1.0),  # 極小ボラティリティ
]

for spot, strike, rate, vol, time in extreme_values:
    price = qf.black_scholes_call(spot, strike, rate, vol, time)
    if np.isnan(price) or np.isinf(price):
        print(f"Warning: Invalid result for spot={spot}, strike={strike}")
    else:
        print(f"Price: ${price:.10f}")
```

## パフォーマンスのモニタリング

```python
import time

# パフォーマンス測定
def benchmark_calculation(n):
    """n個のオプション計算のベンチマーク"""
    spots = np.random.uniform(90, 110, n)
    strikes = np.full(n, 100)
    vols = np.random.uniform(0.1, 0.3, n)
    times = np.random.uniform(0.1, 2.0, n)
    
    start = time.perf_counter()
    prices = qf.calculate(spots, strikes, 0.05, vols, times)
    elapsed = time.perf_counter() - start
    
    return elapsed, prices

# 異なるサイズでテスト
sizes = [100, 1000, 10000, 100000, 1000000]
for size in sizes:
    elapsed, _ = benchmark_calculation(size)
    print(f"{size:8d} options: {elapsed*1000:6.2f}ms ({elapsed/size*1e9:.1f}ns/option)")
```

## ユーティリティ関数

### 満期日からの時間計算

```python
from datetime import datetime, timedelta

def time_to_expiry(expiry_date):
    """満期日までの年換算時間"""
    today = datetime.now()
    days = (expiry_date - today).days
    return days / 365.25

# 使用例
expiry = datetime(2025, 12, 31)
time = time_to_expiry(expiry)
price = qf.black_scholes_call(100, 105, 0.05, 0.2, time)
```

### モンテカルロ価格との比較

```python
def monte_carlo_call(spot, strike, rate, vol, time, n_sims=100000):
    """検証用のモンテカルロ実装"""
    np.random.seed(42)
    z = np.random.standard_normal(n_sims)
    ST = spot * np.exp((rate - 0.5 * vol**2) * time + vol * np.sqrt(time) * z)
    payoffs = np.maximum(ST - strike, 0)
    return np.exp(-rate * time) * np.mean(payoffs)

# 比較
mc_price = monte_carlo_call(100, 105, 0.05, 0.2, 1.0)
bs_price = qf.black_scholes_call(100, 105, 0.05, 0.2, 1.0)
print(f"Monte Carlo: ${mc_price:.4f}")
print(f"Black-Scholes: ${bs_price:.4f}")
print(f"Difference: ${abs(mc_price - bs_price):.4f}")
```

## まとめ

この章では、QuantForgeの基本的な使い方を学びました：

- Black-Scholesモデルによる価格計算
- グリークスの計算と解釈
- インプライドボラティリティの逆算
- 複数オプションの効率的な処理
- エラーハンドリングとパフォーマンス測定

次は[NumPy統合](numpy_integration.md)で、より高度な配列処理を学びましょう。