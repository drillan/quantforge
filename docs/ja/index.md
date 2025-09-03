(index)=
# QuantForge Documentation

(index-overview)=
## 高性能オプション価格計算ライブラリ

QuantForgeは、Rustで構築された高性能金融デリバティブ価格計算ライブラリです。
Pythonの使いやすさを保ちながら、高速な計算性能を提供します。

:::{note}
**主要機能**
- Pure Python実装比 最大40倍の処理速度（AMD Ryzen 5 5600G測定値）
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
# 100万件を約56msで処理（測定環境: AMD Ryzen 5 5600G、CUIモード）
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

:::{note}
測定環境: AMD Ryzen 5 5600G（6コア/12スレッド）、29.3GB RAM、Pop!_OS 22.04（CUIモード）
測定日: 2025-08-28
詳細は[ベンチマーク結果](performance/benchmarks.md)を参照
:::

```{list-table} パフォーマンス比較
:name: index-table-performance
:header-rows: 1
:widths: 25 25 25 25

* - ライブラリ
  - 単一計算
  - 100万件処理時間
  - 相対速度
* - QuantForge
  - 1.4 μs
  - 55.6ms
  - 1.0x
* - NumPy+SciPy
  - 77.7 μs
  - 63.9ms
  - 1.15x遅い
* - Pure Python
  - 2.4 μs
  - -
  - （単一）1.7x遅い
```

(index-documentation-structure)=
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
user_guide/arrow_native_guide
user_guide/examples
```

```{toctree}
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