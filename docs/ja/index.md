(index)=
# QuantForge Documentation

(index-overview)=
## 高性能オプション価格計算ライブラリ

QuantForgeは、Rustで構築された高性能金融デリバティブ価格計算ライブラリです。
Pythonの使いやすさを保ちながら、高速な計算性能を提供します。

:::{note}
:name: index-note-features

**主要機能**
- Pure Python実装比 最大170倍の処理速度（インプライドボラティリティ計算）
- 数値誤差 < 1e-15（倍精度演算）
- シンプルなPython API
- Black-Scholes、Black76、Merton、アメリカンオプション対応
- Rayonによる効率的な並列計算
- NumPy配列のゼロコピー処理
:::

(index-quickstart)=
## クイックスタート

```{code-block} python
:name: index-code-quickstart
:caption: クイックスタートコード例
:linenos:

import numpy as np
from quantforge.models import black_scholes

price = black_scholes.call_price(
    spot=100.0,
    strike=110.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)

# バッチ処理
# 100万件を高速処理（詳細は上記パフォーマンス表参照）
spots = np.random.uniform(90, 110, 1_000_000)
prices = black_scholes.call_price_batch(
    spots=spots,
    strike=100.0,
    time=1.0,
    rate=0.05,
    sigma=0.2
)
```

(index-performance)=
## パフォーマンス比較

```{csv-table}
:file: _static/benchmark_data/environment.csv
:header-rows: 1
:widths: 30, 70
```

詳細は[ベンチマーク結果](performance/benchmarks.md)を参照

(index-iv-performance)=
## 🔥 インプライドボラティリティ計算性能

Newton-Raphson法での公正な比較（同一アルゴリズム・同一パラメータ）：

```{csv-table}
:file: _static/benchmark_data/implied_volatility_newton.csv
:header-rows: 1
:widths: 20, 20, 20, 20, 10, 10
```

- **単一計算**: PyO3のオーバーヘッドにより僅かに劣る
- **バッチ処理**: Rayonの並列処理により圧倒的な高速化を実現
- **10,000件**: **Pure Pythonの170倍高速**

(index-documentation-structure)=
## ドキュメント構成

```{toctree}
:name: index-toc-introduction
:caption: はじめに
:maxdepth: 2

quickstart
installation
```

```{toctree}
:name: index-toc-user-guide
:caption: ユーザーガイド
:maxdepth: 2

user_guide/index
user_guide/basic_usage
user_guide/advanced_models
user_guide/numpy_integration
user_guide/arrow_native_guide
user_guide/examples
```

```{toctree}
:name: index-toc-api-reference
:caption: API リファレンス
:maxdepth: 2

api/python/index
api/python/pricing
api/python/greeks
api/python/batch_processing
api/python/american
api/python/black_scholes
api/python/black76
api/python/merton
api/python/implied_vol
api/rust/index
```

```{toctree}
:name: index-toc-mathematical-models
:caption: 数理モデル
:maxdepth: 2

models/index
models/black_scholes
models/black76
models/merton
models/american_options
models/asian_options
```

```{toctree}
:name: index-toc-performance
:caption: パフォーマンス
:maxdepth: 2

performance/benchmarks
performance/optimization
performance/tuning
```

```{toctree}
:name: index-toc-development
:caption: 開発者向け
:maxdepth: 2

development/setup
development/architecture
development/contributing
development/testing
development/hardcode-prevention
migration/numpy_to_arrow
```

(index-indices)=
## インデックス

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`

(index-project-links)=
## プロジェクトリンク

- [GitHub Repository](https://github.com/yourusername/quantforge)
- [PyPI Package](https://pypi.org/project/quantforge/)
- [Issue Tracker](https://github.com/yourusername/quantforge/issues)