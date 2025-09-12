(index)=
# QuantForge Documentation

(index-overview)=
## High-Performance Option Pricing Library

QuantForge is a high-performance financial derivatives pricing library built with Rust.
It provides high-speed computational performance while maintaining Python's ease of use.

:::{note}
:name: index-note-features

**Key Features**
- Up to 170x faster processing compared to pure Python implementations (Implied Volatility calculation)
- Numerical error < 1e-15 (double precision)
- Simple Python API
- Supports Black-Scholes, Black76, Merton, and American options
- Efficient parallel computation using Rayon
- Zero-copy processing of NumPy arrays
:::

(index-quickstart)=
## Quick Start

```{code-block} python
:name: index-code-quickstart
:caption: Quick Start Code Example
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

# Batch processing
# Process 1 million records at high speed (see performance table above for details)
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
## Performance Comparison

```{csv-table}
:file: _static/benchmark_data/environment.csv
:header-rows: 1
:widths: 30, 70
```

See [Benchmark Results](performance/benchmarks.md) for details

(index-iv-performance)=
## 🔥 Implied Volatility Performance

Fair comparison using Newton-Raphson method (same algorithm, same parameters):

```{csv-table}
:file: _static/benchmark_data/implied_volatility_newton.csv
:header-rows: 1
:widths: 20, 20, 20, 20, 10, 10
```

- **Single calculation**: Slightly slower due to PyO3 overhead
- **Batch processing**: Overwhelming speedup through Rayon parallelization
- **10,000 items**: **170x faster than Pure Python**

(index-documentation-structure)=
## Documentation Structure

```{toctree}
:name: index-toc-introduction
:caption: Getting Started
:maxdepth: 2

quickstart
installation
```

```{toctree}
:name: index-toc-user-guide
:caption: User Guide
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
:caption: API Reference
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
:caption: Mathematical Models
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
:caption: Performance
:maxdepth: 2

performance/benchmarks
performance/optimization
performance/tuning
```

```{toctree}
:name: index-toc-development
:caption: For Developers
:maxdepth: 2

development/setup
development/architecture
development/contributing
development/testing
development/hardcode-prevention
migration/numpy_to_arrow
```

(index-indices)=
## Indices

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`

(index-project-links)=
## Project Links

- [GitHub Repository](https://github.com/yourusername/quantforge)
- [PyPI Package](https://pypi.org/project/quantforge/)
- [Issue Tracker](https://github.com/yourusername/quantforge/issues)