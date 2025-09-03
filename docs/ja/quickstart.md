# クイックスタート

QuantForgeを使って5分でオプション価格計算を始めましょう。

## インストール

```{code-block} bash
:name: quickstart-code-testpypi
:caption: TestPyPIから最新開発版をインストール（現在利用可能）

# TestPyPIから最新開発版をインストール（現在利用可能）
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ quantforge

# PyPIから安定版をインストール（安定版リリース後）
pip install quantforge

# またはソースから開発版をインストール
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
    s=100.0,      # 現在価格
    k=110.0,      # 権利行使価格
    t=1.0,        # 満期（年）
    r=0.05,       # 無リスク金利
    sigma=0.2     # ボラティリティ
)

print(f"Call Option Price: ${price:.2f}")
```

### グリークスの計算

```{code-block} python
:name: quickstart-code-section
:caption: グリークスを含む詳細な計算

# グリークスを含む詳細な計算
greeks = black_scholes.greeks(
    s=100.0,
    k=100.0,
    t=1.0,
    r=0.05,
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
import pyarrow as pa
import numpy as np  # 乱数生成用
import time
from quantforge.models import black_scholes

# 100万件のオプションデータ
n = 1_000_000

# PyArrowを使用（推奨 - Arrow-native設計）
spots = pa.array(np.random.uniform(90, 110, n))

# 高速バッチ処理（ゼロコピーFFI）
start = time.perf_counter()
prices = black_scholes.call_price_batch(
    spots=spots,  # Arrow配列
    k=100.0,
    t=1.0,
    r=0.05,
    sigma=0.2
)  # 返り値: arro3.core.Array
elapsed = (time.perf_counter() - start) * 1000

print(f"計算時間: {elapsed:.1f}ms")
print(f"1オプションあたり: {elapsed/n*1000:.1f}ns")

# NumPy配列も使用可能（互換性のため）
spots_np = np.random.uniform(90, 110, n)
prices_np_input = black_scholes.call_price_batch(
    spots=spots_np,  # NumPy配列も受け付け可能
    k=100.0,
    t=1.0,
    r=0.05,
    sigma=0.2
)  # 返り値は同じArrow配列
```

## インプライドボラティリティ

市場価格からボラティリティを逆算：

```{code-block} python
:name: quickstart-code-iv
:caption: 市場価格からIVを計算

# 市場価格からIVを計算
market_price = 10.45
iv = black_scholes.implied_volatility(
    price=market_price,
    s=100.0,
    k=100.0,
    t=1.0,
    r=0.05,
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
        s=pos["spot"], k=pos["strike"], t=1.0, r=0.05, sigma=0.2, is_call=True
    )
    total_delta += pos["contracts"] * greeks.delta * 100

print(f"Portfolio Delta: {total_delta:.2f} shares")
```

## パフォーマンス

QuantForgeの実測値（AMD Ryzen 5 5600G、CUIモード）：

| 操作 | 処理時間 |
|------|----------|
| 単一価格計算 | 1.4 μs |
| 全グリークス | 計測予定 |
| IV計算 | 1.5 μs |
| 100万件バッチ | 55.6 ms |

詳細な測定結果は[ベンチマーク](performance/benchmarks.md)を参照してください。

## 次のステップ

- [基本的な使い方](user_guide/basic_usage.md) - 詳細なAPI説明
- [NumPy統合](user_guide/numpy_integration.md) - 大規模データ処理
- [APIリファレンス](api/python/index.md) - 完全なAPI文書