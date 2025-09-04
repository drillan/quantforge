# ユーザーガイド

QuantForgeの基本的な使い方から高度な機能まで、段階的に学習できます。

## ガイドの構成

### 📚 基本編

- [基本的な使い方](basic_usage.md) - Black-Scholesモデルとグリークス計算
- [NumPy統合](numpy_integration.md) - 効率的な配列処理とゼロコピー最適化

### 🎯 応用編

- [高度なモデル](advanced_models.md) - アメリカンオプション、配当モデル
- [実践例](examples.md) - 実務で使える具体的なユースケース

## 主な機能

### 価格計算モデル

| モデル | 説明 | パフォーマンス（実測値） |
|--------|------|---------------|
| Black-Scholes | ヨーロピアンオプション | 1.4 μs/計算 |
| Black76 | 先物オプション | 計測予定 |
| Merton | 配当付きヨーロピアン | 計測予定 |
| Barone-Adesi-Whaley | アメリカンオプション近似 | 計測予定 |

※測定環境: AMD Ryzen 5 5600G、CUIモード。詳細は[ベンチマーク](../performance/benchmarks.md)を参照。

### グリークス

- **Delta (δ)**: 原資産価格の変化に対する感応度
- **Gamma (Γ)**: Deltaの変化率
- **Vega (ν)**: ボラティリティ変化に対する感応度
- **Theta (Θ)**: 時間経過に対する感応度
- **Rho (ρ)**: 金利変化に対する感応度

## パフォーマンス最適化

QuantForgeは以下の技術により高速化を実現：

```{admonition} 最適化技術
:class: tip

1. **並列処理**: Rayonによる効率的な並列計算（大規模データで有効）
2. **Arrow-native設計**: ゼロコピーFFIによる高速データ交換
3. **メモリ効率**: 列指向ストレージによる効率的な処理
4. **キャッシュ最適化**: メモリアクセスパターンの最適化
```

## 使用例の概要

### シンプルな価格計算

```python
from quantforge.models import black_scholes

# 単一のオプション価格
price = black_scholes.call_price(
    s=100.0, k=110.0, t=1.0, r=0.05, sigma=0.2
)
```

### バッチ処理

```python
import pyarrow as pa
import numpy as np  # 乱数生成用

# 100万件のオプションを一括計算（Arrow-native）
spots = pa.array(np.random.uniform(90, 110, 1_000_000))
prices = black_scholes.call_price_batch(
    spots=spots, k=100.0, t=1.0, r=0.05, sigma=0.2
)
```

### ポートフォリオ評価

```{code-block} python
:name: user-guide-code-portfolio-evaluation
:caption: 複数のオプションポジション
:linenos:

# 複数のオプションポジションの評価
positions = [
    {"is_call": True, "s": 100, "k": 105, "quantity": 100},
    {"is_call": False, "s": 100, "k": 95, "quantity": -50},
]

total_value = 0
for pos in positions:
    if pos["is_call"]:
        price = black_scholes.call_price(
            s=pos["s"], k=pos["k"], t=0.25, r=0.05, sigma=0.2
        )
    else:
        price = black_scholes.put_price(
            s=pos["s"], k=pos["k"], t=0.25, r=0.05, sigma=0.2
        )
    total_value += price * pos["quantity"]
```

## 推奨ワークフロー

```{mermaid}
graph TD
    A[データ準備] --> B[PyArrow配列化<br/>推奨]
    A --> D[NumPy配列化<br/>互換性]
    B --> C[QuantForge計算]
    D --> C
    C --> E[結果の検証]
    E --> F[可視化/レポート]
    
    C --> G[パフォーマンス計測]
    G --> H[チューニング]
    H --> C
```

## ベストプラクティス

### ✅ 推奨

- PyArrow配列を優先使用（Arrow-native、ゼロコピー）
- NumPy配列も使用可能（pyo3-arrowが自動変換）
- 適切なバッチサイズ（10,000～100,000）
- 事前にメモリを確保
- 型を統一（float64）

### ❌ 非推奨

- Pythonのリストを使用
- 1件ずつループ処理
- 頻繁な型変換
- 巨大な単一バッチ（> 1,000,000）

## トラブルシューティング

問題が発生した場合は、以下を確認してください：
- パラメータの有効範囲（s, k, t > 0、sigma > 0）
- 配列の型と形状の一致
- メモリ不足（大規模バッチ処理時）

## 次のステップ

1. [基本的な使い方](basic_usage.md)から始める
2. [NumPy統合](numpy_integration.md)で効率化
3. [高度なモデル](advanced_models.md)を学習
4. [実践例](examples.md)で応用