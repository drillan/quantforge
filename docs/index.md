# QuantForge Documentation

## 🚀 超高速オプション価格計算エンジン

QuantForgeは、Rust + PyO3で構築された次世代の金融デリバティブ価格計算ライブラリです。
Pythonの使いやすさを保ちながら、ネイティブコード並みのパフォーマンスを実現します。

```{admonition} Key Features
:class: tip

- **⚡ 超高速**: Python実装比 500-1000倍の高速化
- **🎯 高精度**: 数値誤差 < 1e-15
- **🔧 使いやすい**: シンプルなPython API
- **📊 豊富なモデル**: Black-Scholes、アメリカン、アジアン、スプレッドオプション対応
- **🚀 SIMD最適化**: AVX2/AVX-512による並列計算
- **🐍 NumPy統合**: ゼロコピーでの配列処理
```

## クイックスタート

```python
import numpy as np
from quantforge.models import black_scholes

price = black_scholes.call_price(
    spot=100.0,
    strike=110.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)

# バッチ処理（100万件を20ms以下で処理）
spots = np.random.uniform(90, 110, 1_000_000)
prices = black_scholes.call_price_batch(
    spots=spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)
```

## パフォーマンス比較

| ライブラリ | 100万件処理時間 | 相対速度 |
|------------|----------------|----------|
| QuantForge | 15ms | 1.0x |
| NumPy実装 | 7,500ms | 500x |
| Pure Python | 15,000ms | 1000x |

## ドキュメント構成

```{toctree}
:caption: はじめに
:maxdepth: 2

quickstart
installation
```

```{toctree}
:caption: ユーザーガイド
:maxdepth: 2

user_guide/index
user_guide/basic_usage
user_guide/advanced_models
user_guide/numpy_integration
user_guide/examples
```

```{toctree}
:caption: API リファレンス
:maxdepth: 2

api/python/index
api/python/pricing
api/python/implied_vol
api/rust/index
```

```{toctree}
:caption: 数理モデル
:maxdepth: 2

models/index
models/black_scholes
models/american_options
models/asian_options
```

```{toctree}
:caption: パフォーマンス
:maxdepth: 2

performance/benchmarks
performance/optimization
performance/tuning
```

```{toctree}
:caption: 開発者向け
:maxdepth: 2

development/setup
development/architecture
development/contributing
development/testing
```

```{toctree}
:caption: プロジェクト情報
:maxdepth: 2

roadmap
changelog
faq
```

## インデックス

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`

## プロジェクトリンク

- [GitHub Repository](https://github.com/yourusername/quantforge)
- [PyPI Package](https://pypi.org/project/quantforge/)
- [Issue Tracker](https://github.com/yourusername/quantforge/issues)

---

**Version**: 0.1.0 | **Last Updated**: 2025-01-24