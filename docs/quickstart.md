# クイックスタート

QuantForgeを使って5分でオプション価格計算を始めましょう。

## インストール

```bash
# uvを使用したインストール（推奨）
uv pip install quantforge

# または pipを使用
pip install quantforge
```

## 最初のBlack-Scholes計算

### ヨーロピアンコールオプション

```python
import quantforge as qf

# 基本的なコールオプション価格計算
price = qf.black_scholes_call(
    spot=100.0,    # 現在価格
    strike=110.0,  # 行使価格
    rate=0.05,     # 無リスク金利
    vol=0.2,       # ボラティリティ
    time=1.0       # 満期までの時間（年）
)
print(f"Call Option Price: ${price:.2f}")
```

### グリークスの計算

```python
# グリークスを含む詳細な計算
result = qf.calculate(
    spots=100.0,
    strikes=110.0,
    rates=0.05,
    vols=0.2,
    times=1.0,
    option_type="call",
    greeks=True
)

print(f"Price: ${result['price']:.2f}")
print(f"Delta: {result['delta']:.4f}")
print(f"Gamma: {result['gamma']:.4f}")
print(f"Vega: {result['vega']:.4f}")
print(f"Theta: {result['theta']:.4f}")
print(f"Rho: {result['rho']:.4f}")
```

## バッチ処理

QuantForgeの真価は大量データの高速処理にあります：

```python
import numpy as np
import time

# 100万件のオプションデータを生成
n = 1_000_000
spots = np.random.uniform(90, 110, n)
strikes = np.full(n, 100.0)
rates = np.full(n, 0.05)
vols = np.random.uniform(0.1, 0.3, n)
times = np.random.uniform(0.1, 2.0, n)

# 高速バッチ処理
start = time.perf_counter()
prices = qf.calculate(spots, strikes, rates, vols, times)
elapsed = (time.perf_counter() - start) * 1000

print(f"計算時間: {elapsed:.1f}ms")
print(f"1オプションあたり: {elapsed/n*1000:.1f}ns")
```

## インプライドボラティリティ

市場価格からボラティリティを逆算：

```python
# 市場価格からIVを計算
market_price = 12.5
iv = qf.implied_volatility(
    price=market_price,
    spot=100.0,
    strike=110.0,
    rate=0.05,
    time=1.0,
    option_type="call"
)
print(f"Implied Volatility: {iv:.1%}")
```

## アメリカンオプション

早期行使権付きオプション：

```python
# アメリカンプットオプション
american_price = qf.american_put(
    spot=100.0,
    strike=110.0,
    rate=0.05,
    vol=0.2,
    time=1.0
)

# ヨーロピアンとの比較
european_price = qf.black_scholes_put(
    spot=100.0,
    strike=110.0,
    rate=0.05,
    vol=0.2,
    time=1.0
)

premium = american_price - european_price
print(f"American Put: ${american_price:.2f}")
print(f"European Put: ${european_price:.2f}")
print(f"Early Exercise Premium: ${premium:.2f}")
```

## 結果の確認と可視化

```python
import matplotlib.pyplot as plt

# ペイオフダイアグラム
spots = np.linspace(80, 120, 100)
call_prices = qf.calculate(spots, strike=100, rate=0.05, vol=0.2, time=0.25)

plt.figure(figsize=(10, 6))
plt.plot(spots, call_prices, label='Call Option Value')
plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
plt.axvline(x=100, color='r', linestyle='--', alpha=0.5, label='Strike')
plt.xlabel('Spot Price')
plt.ylabel('Option Value')
plt.title('Call Option Price vs Spot Price')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

## パフォーマンステクニック

### 1. NumPy配列を使用

```python
# 効率的: NumPy配列を直接渡す
spots = np.array([100, 105, 110])
prices = qf.calculate(spots, strike=100, rate=0.05, vol=0.2, time=1.0)

# 非効率: Pythonリストを使用（内部で変換が発生）
spots_list = [100, 105, 110]
prices = qf.calculate(spots_list, strike=100, rate=0.05, vol=0.2, time=1.0)
```

### 2. 適切なバッチサイズ

```python
# 最適なバッチサイズは10,000～100,000件
optimal_batch = 50_000
for i in range(0, len(all_data), optimal_batch):
    batch = all_data[i:i+optimal_batch]
    results = qf.calculate(batch, ...)
```

### 3. メモリの事前確保

```python
# 結果配列を事前確保
n = 1_000_000
results = np.empty(n)
qf.calculate_inplace(spots, strikes, rates, vols, times, out=results)
```

## 次のステップ

- [詳細なインストール手順](installation.md)
- [基本的な使い方](user_guide/basic_usage.md)
- [高度なモデル](user_guide/advanced_models.md)
- [APIリファレンス](api/python/index.md)

## トラブルシューティング

### よくある問題

**Q: ImportError: cannot import name 'quantforge'**

A: インストールを確認してください：
```bash
uv pip list | grep quantforge
```

**Q: 計算結果がNaNになる**

A: 入力パラメータを確認してください：
- ボラティリティは正の値
- 満期時間は正の値
- 現在価格と行使価格は正の値

**Q: パフォーマンスが期待より遅い**

A: 以下を確認してください：
- NumPy配列を使用しているか
- AVX2がサポートされているか: `qf.check_simd_support()`
- 適切なバッチサイズか（10,000～100,000件）