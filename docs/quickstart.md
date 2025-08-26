# クイックスタート

QuantForgeを使って5分でオプション価格計算を始めましょう。

## インストール

```bash
# pipを使用したインストール
pip install quantforge

# または開発版のインストール
git clone https://github.com/drillan/quantforge.git
cd quantforge
pip install maturin
maturin develop --release
```

## 最初の計算

### モジュールベースAPI

```python
from quantforge.models import black_scholes

# Black-Scholesモデルでコールオプション価格を計算
price = black_scholes.call_price(
    spot=100.0,    # 現在価格
    strike=110.0,  # 権利行使価格
    time=1.0,      # 満期（年）
    rate=0.05,     # 無リスク金利
    sigma=0.2      # ボラティリティ
)

print(f"Call Option Price: ${price:.2f}")
```

### グリークスの計算

```python
# グリークスを含む詳細な計算
greeks = black_scholes.greeks(
    spot=100.0,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2,
    is_call=True
)

print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
print(f"Theta: {greeks.theta:.4f}")
print(f"Rho: {greeks.rho:.4f}")
```

## バッチ処理

QuantForgeの真価は大量データの高速処理にあります：

```python
import numpy as np
import time
from quantforge.models import black_scholes

# 100万件のオプションデータ
n = 1_000_000
spots = np.random.uniform(90, 110, n)

# 高速バッチ処理
start = time.perf_counter()
prices = black_scholes.call_price_batch(
    spots=spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)
elapsed = (time.perf_counter() - start) * 1000

print(f"計算時間: {elapsed:.1f}ms")
print(f"1オプションあたり: {elapsed/n*1000:.1f}ns")
```

## インプライドボラティリティ

市場価格からボラティリティを逆算：

```python
# 市場価格からIVを計算
market_price = 10.45
iv = black_scholes.implied_volatility(
    price=market_price,
    spot=100.0,
    strike=100.0,
    time=1.0,
    rate=0.05,
    is_call=True
)
print(f"Implied Volatility: {iv:.1%}")
```


## リアルタイムリスク管理

```python
from quantforge.models import black_scholes

# ポートフォリオのデルタ計算
positions = [
    {"spot": 100, "strike": 95, "contracts": 10},
    {"spot": 100, "strike": 105, "contracts": -5},
]

total_delta = 0
for pos in positions:
    greeks = black_scholes.greeks(
        pos["spot"], pos["strike"], 1.0, 0.05, 0.2, is_call=True
    )
    total_delta += pos["contracts"] * greeks.delta * 100

print(f"Portfolio Delta: {total_delta:.2f} shares")
```

## パフォーマンス

QuantForgeは高速計算を実現：

| 操作 | 処理時間 |
|------|----------|
| 単一価格計算 | < 10ns |
| 全グリークス | < 50ns |
| IV計算 | < 200ns |
| 100万件バッチ | < 20ms |

## 次のステップ

- [基本的な使い方](user_guide/basic_usage.md) - 詳細なAPI説明
- [NumPy統合](user_guide/numpy_integration.md) - 大規模データ処理
- [APIリファレンス](api/python/index.md) - 完全なAPI文書