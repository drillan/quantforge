# QuantForge Documentation

## High-Performance Option Pricing Library

QuantForge is a financial derivatives pricing library built using Rust + PyO3.
It maintains Python's ease of use while providing high-speed computational performance.

:::{note}
**Key Features**
- Up to 40x faster processing compared to pure Python implementations (measured on AMD Ryzen 5 5600G)
- Numerical error < 1e-15 (double precision)
- Simple Python API
- Supports Black-Scholes, American, Asian, and Spread options
- Efficient Parallel Computation Using Rayon
- Zero-copy Operations on NumPy Arrays
:::

## Quick Start

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

## Performance Comparison

:::{note}
Measurement Environment: AMD Ryzen 5 5600G (6 cores/12 threads), 29.3GB RAM, Pop!_OS 22.04 (CLI mode)
Measurement Date: 2025-08-28
For more details, see the [benchmark results](performance/benchmarks.md).
:::

| Library | Single Calculation | million records processed | relative velocity |
|------------|----------|----------------|----------|
| QuantForge | 1.4 μs | 55.6ms | 1.0x |
| NumPy+SciPy | 77.7 μs | 63.9ms | 1.15x slower |
| Pure Python | 2.4 μs | - | (Single) 1.7x slower |

## Document Structure

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
```

```{toctree}
:caption: プロジェクト情報
:maxdepth: 2

changelog
faq
```

## index

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`

## Project Links

- [GitHub Repository](https://github.com/yourusername/quantforge)
- [PyPI Package](https://pypi.org/project/quantforge/)
- [Issue Tracker](https://github.com/yourusername/quantforge/issues)