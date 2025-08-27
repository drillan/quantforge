# ユーザーガイド

QuantForgeの基本的な使い方から高度な機能まで、段階的に学習できます。

## ガイドの構成

### 📚 基本編

- [基本的な使い方](basic_usage.md) - Black-Scholesモデルとグリークス計算
- [NumPy統合](numpy_integration.md) - 効率的な配列処理とゼロコピー最適化

### 🎯 応用編

- [高度なモデル](advanced_models.md) - アメリカン、アジアン、スプレッドオプション
- [実践例](examples.md) - 実務で使える具体的なユースケース

## 主な機能

### 価格計算モデル

| モデル | 説明 | パフォーマンス |
|--------|------|---------------|
| Black-Scholes | ヨーロピアンオプション | < 10ns/計算 |
| Bjerksund-Stensland | アメリカンオプション近似 | < 50ns/計算 |
| Asian Options | 平均価格オプション | < 100ns/計算 |
| Spread Options | 2資産スプレッド | < 150ns/計算 |

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

1. **並列処理**: Rayonによる効率的な並列計算
2. **マルチスレッド**: Rayonによる自動並列化
3. **ゼロコピー**: NumPy配列の直接処理
4. **キャッシュ最適化**: メモリアクセスパターンの最適化
```

## 使用例の概要

### シンプルな価格計算

```python
import quantforge as qf

# 単一のオプション価格
price = qf.black_scholes_call(100, 110, 0.05, 0.2, 1.0)
```

### バッチ処理

```python
import numpy as np

# 100万件のオプションを一括計算
spots = np.random.uniform(90, 110, 1_000_000)
prices = qf.calculate(spots, strike=100, rate=0.05, vol=0.2, time=1.0)
```

### ポートフォリオ評価

```python
# 複数のオプションポジション
portfolio = [
    {"type": "call", "spot": 100, "strike": 105, "quantity": 100},
    {"type": "put", "spot": 100, "strike": 95, "quantity": -50},
]

total_value = qf.evaluate_portfolio(portfolio, rate=0.05, vol=0.2, time=0.25)
```

## 推奨ワークフロー

```{mermaid}
graph TD
    A[データ準備] --> B[NumPy配列化]
    B --> C[QuantForge計算]
    C --> D[結果の検証]
    D --> E[可視化/レポート]
    
    B --> F[バッチサイズ最適化]
    F --> C
    
    C --> G[パフォーマンス計測]
    G --> H[チューニング]
    H --> C
```

## ベストプラクティス

### ✅ 推奨

- NumPy配列を使用する
- 適切なバッチサイズ（10,000～100,000）
- 事前にメモリを確保
- 型を統一（float64）

### ❌ 非推奨

- Pythonのリストを使用
- 1件ずつループ処理
- 頻繁な型変換
- 巨大な単一バッチ（> 1,000,000）

## トラブルシューティング

一般的な問題については[FAQ](../faq.md)を参照してください。

## 次のステップ

1. [基本的な使い方](basic_usage.md)から始める
2. [NumPy統合](numpy_integration.md)で効率化
3. [高度なモデル](advanced_models.md)を学習
4. [実践例](examples.md)で応用