# 高度なモデル

QuantForgeは、基本的なBlack-Scholesモデルに加えて、以下の高度なオプション価格モデルを提供しています。

## 実装済みモデル

### Black-Scholesモデル
ヨーロピアンオプションの標準的な価格計算モデル。詳細は[Black-Scholesモデル](../api/python/black_scholes.md)を参照。

### Black76モデル
先物オプションの価格計算モデル。詳細は[Black76モデル](../api/python/black76.md)を参照。

### Mertonモデル
配当を考慮したヨーロピアンオプションの価格計算モデル。詳細は[Mertonモデル](../api/python/merton.md)を参照。

### アメリカンオプション

Barone-Adesi-Whaley近似を使用した早期行使可能なオプションの価格計算。

```python
from quantforge.models import american, black_scholes

# アメリカンコールオプション
american_call = american.call_price(
    s=100.0,    # スポット価格
    k=95.0,     # 権利行使価格
    t=1.0,      # 満期までの時間（年）
    r=0.05,     # 無リスク金利
    sigma=0.25  # ボラティリティ
)

# ヨーロピアンとの比較
european_call = black_scholes.call_price(
    s=100.0,
    k=95.0,
    t=1.0,
    r=0.05,
    sigma=0.25
)

early_exercise_premium = american_call - european_call
print(f"American Call: ${american_call:.2f}")
print(f"European Call: ${european_call:.2f}")
print(f"Early Exercise Premium: ${early_exercise_premium:.2f}")
```

#### アメリカンプットオプション

プットオプションの場合、早期行使の価値がより重要になることがあります：

```python
# アメリカンプット
american_put = american.put_price(
    s=100.0,
    k=105.0,
    t=1.0,
    r=0.05,
    sigma=0.25
)

# ヨーロピアンプット
european_put = black_scholes.put_price(
    s=100.0,
    k=105.0,
    t=1.0,
    r=0.05,
    sigma=0.25
)

premium = american_put - european_put
print(f"American Put: ${american_put:.2f}")
print(f"European Put: ${european_put:.2f}")
print(f"Early Exercise Premium: ${premium:.2f} ({premium/european_put*100:.1f}%)")
```

詳細は[アメリカンオプションAPI](../api/python/american.md)を参照。

## モデル選択ガイド

| モデル | 用途 | 特徴 |
|--------|------|------|
| Black-Scholes | 株式のヨーロピアンオプション | 最も基本的、高速 |
| Black76 | 先物・商品オプション | 先物価格ベース |
| Merton | 配当付き株式オプション | 連続配当を考慮 |
| American | 早期行使可能なオプション | BAW近似使用 |

## パフォーマンス比較

実測値（AMD Ryzen 5 5600G）：

| モデル | 単一計算 | 100万件バッチ |
|--------|----------|---------------|
| Black-Scholes | 1.4 μs | 55.6 ms |
| Black76 | 計測予定 | 計測予定 |
| Merton | 計測予定 | 計測予定 |
| American | 計測予定 | 計測予定 |

## 使用例：ポートフォリオ評価

複数のオプションポジションを一括評価する例：

```python
import pyarrow as pa
from quantforge.models import black_scholes, american

# ポートフォリオデータ
positions = [
    {"model": "bs", "is_call": True, "s": 100, "k": 105, "quantity": 100},
    {"model": "bs", "is_call": False, "s": 100, "k": 95, "quantity": -50},
    {"model": "am", "is_call": True, "s": 110, "k": 105, "quantity": 75},
]

total_value = 0
for pos in positions:
    if pos["model"] == "bs":
        if pos["is_call"]:
            price = black_scholes.call_price(
                s=pos["s"], k=pos["k"], t=0.25, r=0.05, sigma=0.2
            )
        else:
            price = black_scholes.put_price(
                s=pos["s"], k=pos["k"], t=0.25, r=0.05, sigma=0.2
            )
    elif pos["model"] == "am":
        if pos["is_call"]:
            price = american.call_price(
                s=pos["s"], k=pos["k"], t=0.25, r=0.05, sigma=0.2
            )
        else:
            price = american.put_price(
                s=pos["s"], k=pos["k"], t=0.25, r=0.05, sigma=0.2
            )
    
    position_value = price * pos["quantity"]
    total_value += position_value
    print(f"Position: {pos['model'].upper()} {'Call' if pos['is_call'] else 'Put'} K={pos['k']}: ${position_value:.2f}")

print(f"Total Portfolio Value: ${total_value:.2f}")
```

## まとめ

QuantForgeは以下の実装済みモデルを提供しています：

- **Black-Scholes**: 標準的なヨーロピアンオプション
- **Black76**: 先物オプション
- **Merton**: 配当付きオプション
- **American**: 早期行使可能なオプション（BAW近似）

すべてのモデルで以下の機能が利用可能：
- 高速な単一計算
- Arrow-nativeバッチ処理
- 完全なグリークス計算
- インプライドボラティリティ逆算

詳細な使用方法は各モデルのAPIドキュメントを参照してください。