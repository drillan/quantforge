(index)=
# QuantForge Documentation

(index-overview)=
## High-Performance Option Pricing Library

QuantForge is a high-performance financial derivatives pricing library built with Rust.
It provides high-speed computational performance while maintaining Python's ease of use.

:::{note}
:name: index-note-features

**Key Features**
- Up to 40x faster processing compared to pure Python implementations (measured on AMD Ryzen 5 5600G)
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
# Process 1 million records in ~56ms (measured on AMD Ryzen 5 5600G, CLI mode)
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

:::{note}
:name: index-note-performance-environment

Measurement Environment: AMD Ryzen 5 5600G (6 cores/12 threads), 29.3GB RAM, Pop!_OS 22.04 (CLI mode)
Measurement Date: 2025-08-28
See [Benchmark Results](performance/benchmarks.md) for details
:::

```{list-table} Performance Comparison
:name: index-table-performance
:header-rows: 1
:widths: 25 25 25 25

* - Library
  - Single Calculation
  - 1 Million Records Processing Time
  - Relative Speed
* - QuantForge
  - 1.4 μs
  - 55.6ms
  - 1.0x
* - NumPy+SciPy
  - 77.7 μs
  - 63.9ms
  - 1.15x slower
* - Pure Python
  - 2.4 μs
  - -
  - (Single) 1.7x slower
```

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