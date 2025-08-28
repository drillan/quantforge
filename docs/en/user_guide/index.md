# User Guide

Learn step-by-step from basic to advanced features of QuantForge.

## Guide Composition

### 📚 Fundamentals

- [Basic Usage](basic_usage.md) - Black-Scholes Model and Greeks Calculation
- [NumPy Integration](numpy_integration.md) - Efficient array processing and zero-copy optimizations

### 🎯 Advanced Applications

- [Advanced Models](advanced_models.md) - American, Asian, and Spread Options
- [Implementation Examples](examples.md) - Practical use cases for real-world applications

## Main Features

### Price Calculation Model

| model | Description | Performance (Actual) |
|--------|------|---------------|
| Black-Scholes | European Option | 1.4 μs/calculation |
| Bjerksund-Stensland | American Option Approximation | Scheduled Measurement |
| Asian Options | Average Price Option | Scheduled Measurement |
| Spread Options | 2 Asset Spread | Scheduled Measurement |

※ Measurement environment: AMD Ryzen 5 5600G, CUI mode. For details, see [Benchmarks](../performance/benchmarks.md).

### Greeks

- **Delta (δ)**: Sensitivity to changes in the underlying asset price
- **Gamma (Γ)**: The rate of change of Delta
- **Vega (ν)**: Sensitivity to changes in volatility
- **Theta (Θ)**: Sensitivity over time
- **Rho (ρ)**: Sensitivity to interest rate changes

## Performance Optimization

QuantForge achieves acceleration through the following technologies:

```{admonition} 最適化技術
:class: tip

1. **並列処理**: Rayonによる効率的な並列計算（大規模データで有効）
2. **SIMD最適化**: CPUのベクトル命令を活用
3. **ゼロコピー**: NumPy配列の直接処理（PyO3経由）
4. **キャッシュ最適化**: メモリアクセスパターンの最適化
```

## Usage Examples Overview

### Simple Price Calculation

```python
import quantforge as qf

# 単一のオプション価格
price = qf.black_scholes_call(100, 110, 0.05, 0.2, 1.0)
```

### Batch Processing

```python
import numpy as np

# 100万件のオプションを一括計算
spots = np.random.uniform(90, 110, 1_000_000)
prices = qf.calculate(spots, strike=100, rate=0.05, vol=0.2, time=1.0)
```

### Portfolio Evaluation

```python
# 複数のオプションポジション
portfolio = [
    {"type": "call", "spot": 100, "strike": 105, "quantity": 100},
    {"type": "put", "spot": 100, "strike": 95, "quantity": -50},
]

total_value = qf.evaluate_portfolio(portfolio, rate=0.05, vol=0.2, time=0.25)
```

## Recommended Workflow

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

## Best Practices

### ✅ Recommended

- Use NumPy arrays
- Appropriate batch size (10,000–100,000)
- Pre-allocate memory
- Standardize type (float64)

### ❌ Deprecated

- Using Python lists
- Loop through each item
- Frequent type conversions
- Giant Single-Batch (> 1,000,000)

## Troubleshooting

For general issues, refer to the [FAQ](../faq.md).

## Next Step

1. Start with [Basic Usage](basic_usage.md)
2. [Efficiency with NumPy Integration](numpy_integration.md)
3. Train [Advanced Models](advanced_models.md)
4. [Practical Applications](examples.md)
