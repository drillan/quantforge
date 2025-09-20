(market-utils)=
# Market Utils API

Market data processing utilities: mid-price calculation from bid-ask prices, spread analysis, and outlier handling

(market-utils-overview)=
## Overview

The `quantforge.market_utils` module provides price calculation functions from market data:

- **Mid-price calculation**: Simple and volume-weighted mid-prices
- **Spread analysis**: Absolute and percentage spreads
- **Outlier handling**: Processing extreme spreads in options markets
- **Batch processing**: High-speed processing of large datasets using Arrow arrays

(market-utils-imports)=
## Imports

```{code-block} python
:name: market-utils-code-imports
:caption: Module imports

from quantforge.market_utils import (
    # Single-value calculations
    mid_price,
    mid_price_with_config,
    weighted_mid_price,
    weighted_mid_price_with_config,
    spread,
    spread_pct,

    # Batch processing
    mid_price_batch,
    mid_price_batch_with_config,
    mid_price_batch_with_metrics,
    weighted_mid_price_batch,
    weighted_mid_price_batch_with_config,
    spread_batch,
    spread_pct_batch,

    # Configuration
    PricingConfig
)
```

(market-utils-single-value)=
## Single-Value Calculations

(market-utils-mid-price)=
### mid_price

Calculates the simple mid-price from bid and ask.

```{code-block} python
:name: market-utils-code-mid-price
:caption: mid_price function signature

def mid_price(bid: float, ask: float) -> float:
    """
    Simple mid-price calculation

    Parameters
    ----------
    bid : float
        Bid price
    ask : float
        Ask price

    Returns
    -------
    float
        Mid-price. Returns NaN for abnormal cases

    Notes
    -----
    - By default, spreads exceeding 50% return NaN
    - Crossed spreads (bid > ask) return NaN
    - Negative prices return NaN
    """
```

**Usage examples**:

```{code-block} python
:name: market-utils-code-mid-price-example
:caption: mid_price usage example

import math
from quantforge.market_utils import mid_price

# Normal spread
price = mid_price(100.0, 100.2)
assert price == 100.1

# Extreme spread (common in options markets)
price = mid_price(1.0, 1000.0)
assert math.isnan(price)  # By default, >50% returns NaN

# Crossed spread
price = mid_price(105.0, 100.0)
assert math.isnan(price)
```

(market-utils-mid-price-with-config)=
### mid_price_with_config

Calculates mid-price with custom configuration.

```{code-block} python
:name: market-utils-code-mid-price-with-config
:caption: mid_price_with_config function signature

def mid_price_with_config(
    bid: float,
    ask: float,
    config: PricingConfig
) -> float:
    """
    Configurable mid-price calculation

    Parameters
    ----------
    bid : float
        Bid price
    ask : float
        Ask price
    config : PricingConfig
        Pricing calculation configuration

    Returns
    -------
    float
        Mid-price. Handling of abnormal cases depends on configuration
    """
```

**Usage examples**:

```{code-block} python
:name: market-utils-code-mid-price-with-config-example
:caption: mid_price_with_config usage example

from quantforge.market_utils import mid_price_with_config, PricingConfig

# Allow extreme spreads
config = PricingConfig.with_config(max_spread_pct=None)
price = mid_price_with_config(1.0, 1000.0, config)
assert price == 500.5  # Returns mid-price instead of NaN

# Strict spread limit
config = PricingConfig.with_config(max_spread_pct=0.01)  # 1% limit
price = mid_price_with_config(100.0, 102.0, config)
assert math.isnan(price)  # 2% spread, so NaN
```

(market-utils-weighted-mid-price)=
### weighted_mid_price

Calculates volume-weighted mid-price.

```{code-block} python
:name: market-utils-code-weighted-mid-price
:caption: weighted_mid_price function signature

def weighted_mid_price(
    bid: float,
    ask: float,
    bid_qty: Optional[float] = None,
    ask_qty: Optional[float] = None
) -> float:
    """
    Volume-weighted mid-price calculation

    Parameters
    ----------
    bid : float
        Bid price
    ask : float
        Ask price
    bid_qty : float, optional
        Bid quantity. Falls back to simple mid-price if None
    ask_qty : float, optional
        Ask quantity. Falls back to simple mid-price if None

    Returns
    -------
    float
        Weighted mid-price

    Notes
    -----
    - (bid * ask_qty + ask * bid_qty) / (bid_qty + ask_qty)
    - Same as simple mid-price when quantities are equal
    - Falls back to simple mid-price if one or both quantities are 0 or None
    """
```

**Usage examples**:

```{code-block} python
:name: market-utils-code-weighted-mid-price-example
:caption: weighted_mid_price usage example

from quantforge.market_utils import weighted_mid_price

# Market with thick bid side
price = weighted_mid_price(100.0, 100.2, bid_qty=2000.0, ask_qty=1000.0)
# (100.0 * 1000.0 + 100.2 * 2000.0) / 3000.0 ≈ 100.133

# No quantities (fallback to simple mid-price)
price = weighted_mid_price(100.0, 100.2)
assert price == 100.1
```

(market-utils-spread)=
### spread / spread_pct

Calculates spread and spread percentage.

```{code-block} python
:name: market-utils-code-spread
:caption: spread/spread_pct function signatures

def spread(bid: float, ask: float) -> float:
    """Calculate absolute spread (ask - bid)"""

def spread_pct(bid: float, ask: float) -> float:
    """Calculate spread percentage

    Returns
    -------
    float
        (ask - bid) / mid_price
        Returns NaN for crossed spreads
    """
```

(market-utils-batch)=
## Batch Processing

(market-utils-mid-price-batch)=
### mid_price_batch

Calculates mid-prices for multiple price pairs in batch.

```{code-block} python
:name: market-utils-code-mid-price-batch
:caption: mid_price_batch function signature

def mid_price_batch(
    bids: np.ndarray,
    asks: np.ndarray
) -> np.ndarray:
    """
    Batch mid-price calculation (high-speed processing with Arrow arrays)

    Parameters
    ----------
    bids : np.ndarray
        Bid price array (scalars also supported)
    asks : np.ndarray
        Ask price array (scalars also supported)

    Returns
    -------
    np.ndarray
        Mid-price array

    Notes
    -----
    - Automatic parallel processing for 10,000+ elements
    - Broadcasting support
    - Zero-copy processing with Arrow arrays
    """
```

**Usage examples**:

```{code-block} python
:name: market-utils-code-mid-price-batch-example
:caption: mid_price_batch usage example

import numpy as np
from quantforge.market_utils import mid_price_batch

# Batch processing of multiple prices
bids = np.array([100.0, 101.0, 102.0])
asks = np.array([100.2, 101.3, 102.4])
mids = mid_price_batch(bids, asks)
# array([100.1, 101.15, 102.2])

# Broadcasting (scalar × array)
bid = np.array([100.0])  # scalar
asks = np.array([100.2, 100.3, 100.4])
mids = mid_price_batch(bid, asks)
# array([100.1, 100.15, 100.2])
```

(market-utils-mid-price-batch-with-metrics)=
### mid_price_batch_with_metrics

Collects statistics along with mid-price calculations.

```{code-block} python
:name: market-utils-code-mid-price-batch-with-metrics
:caption: mid_price_batch_with_metrics function signature

def mid_price_batch_with_metrics(
    bids: np.ndarray,
    asks: np.ndarray,
    config: PricingConfig
) -> Tuple[np.ndarray, BatchMetrics]:
    """
    Batch processing with metrics

    Returns
    -------
    tuple
        (mid-price array, BatchMetrics object)

    BatchMetrics attributes:
        - total_processed: Number of processed items
        - nan_count: Number of NaN results
        - crossed_spreads: Number of crossed spreads
        - abnormal_spreads: Number of abnormal spreads
        - mean_spread_pct: Mean spread percentage
        - max_spread_pct: Maximum spread percentage
    """
```

**Usage examples**:

```{code-block} python
:name: market-utils-code-mid-price-batch-with-metrics-example
:caption: mid_price_batch_with_metrics usage example

from quantforge.market_utils import mid_price_batch_with_metrics, PricingConfig

# Option chain processing
bids = np.array([100.0, 1.0, 105.0, 100.0])
asks = np.array([100.2, 1000.0, 104.0, 100.5])
config = PricingConfig.with_config(max_spread_pct=0.1)  # 10% limit

mids, metrics = mid_price_batch_with_metrics(bids, asks, config)

print(f"Processed: {metrics.total_processed}")
print(f"Abnormal spreads: {metrics.abnormal_spreads}")
print(f"Crossed spreads: {metrics.crossed_spreads}")
print(f"Mean spread: {metrics.mean_spread_pct:.2%}")
```

(market-utils-weighted-mid-price-batch)=
### weighted_mid_price_batch

Performs batch calculation of volume-weighted mid-prices.

```{code-block} python
:name: market-utils-code-weighted-mid-price-batch
:caption: weighted_mid_price_batch function signature

def weighted_mid_price_batch(
    bids: np.ndarray,
    asks: np.ndarray,
    bid_qtys: Optional[np.ndarray] = None,
    ask_qtys: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Batch calculation of volume-weighted mid-prices

    Parameters
    ----------
    bids : np.ndarray
        Bid price array
    asks : np.ndarray
        Ask price array
    bid_qtys : np.ndarray, optional
        Bid quantity array
    ask_qtys : np.ndarray, optional
        Ask quantity array

    Notes
    -----
    - Elements with 0 or None quantities use simple mid-price
    - Broadcasting support
    """
```

(market-utils-config)=
## Configuration Classes

(market-utils-pricing-config)=
### PricingConfig

Configuration class that controls price calculation behavior.

```{code-block} python
:name: market-utils-code-pricing-config
:caption: PricingConfig class definition

class PricingConfig:
    """
    Price calculation configuration

    Attributes
    ----------
    max_spread_pct : float, optional
        Maximum allowable spread percentage (default: 0.5 = 50%)
        No limit if None
    abnormal_handling : str
        How to handle abnormal spreads
        - "return_nan": Return NaN (default)
        - "log_and_continue": Log and return mid-price
    crossed_handling : str
        How to handle crossed spreads
        - "return_nan": Return NaN (default)
        - "swap_and_continue": Swap bid/ask and proceed
    """

    @staticmethod
    def with_config(
        max_spread_pct: Optional[float] = None,
        abnormal_handling: str = "return_nan",
        crossed_handling: str = "return_nan"
    ) -> PricingConfig:
        """Create custom configuration"""
```

**Usage examples**:

```{code-block} python
:name: market-utils-code-pricing-config-example
:caption: PricingConfig usage example

from quantforge.market_utils import PricingConfig

# Default configuration (50% limit)
config = PricingConfig()

# No limit (for deep OTM options)
config = PricingConfig.with_config(max_spread_pct=None)

# Strict limit (highly liquid markets)
config = PricingConfig.with_config(max_spread_pct=0.001)  # 0.1%

# Auto-fix crossed spreads
config = PricingConfig.with_config(
    crossed_handling="swap_and_continue"
)
```

(market-utils-use-cases)=
## Real-World Use Cases

(market-utils-option-chain-processing)=
### Option Chain Processing

```{code-block} python
:name: market-utils-code-option-chain-processing
:caption: Option chain processing example

import numpy as np
from quantforge.market_utils import (
    mid_price_batch_with_metrics,
    PricingConfig
)

# Nikkei 225 options (100 strikes)
n = 100
strikes = np.linspace(40000, 50000, n)
atm = 45000

# Spreads widen with distance from ATM
distance = np.abs(strikes - atm) / atm
spread_pct = 0.002 + distance * 2.0  # 0.2% ~ 200%+

bids = strikes * (1 - spread_pct / 2)
asks = strikes * (1 + spread_pct / 2)

# Filter spreads exceeding 10%
config = PricingConfig.with_config(max_spread_pct=0.1)
mids, metrics = mid_price_batch_with_metrics(bids, asks, config)

# Extract only valid mid-prices
valid_mids = mids[~np.isnan(mids)]
print(f"Valid strikes: {len(valid_mids)}/{n}")
print(f"Mean spread: {metrics.mean_spread_pct:.2%}")
```

(market-utils-high-frequency-stream)=
### High-Frequency Data Stream

```{code-block} python
:name: market-utils-code-high-frequency-stream
:caption: High-frequency data stream processing example

import numpy as np
from quantforge.market_utils import mid_price_batch

# 1 second of tick data (100 updates)
np.random.seed(42)
base_price = 100.0
n = 100

# Random walk
noise = np.random.randn(n) * 0.01
bids = base_price + np.cumsum(noise) - 0.1
asks = bids + np.random.uniform(0.05, 0.15, n)

# High-speed batch processing (parallelized for 10,000+ items)
mids = mid_price_batch(bids, asks)

# Price movement analysis
returns = np.diff(mids) / mids[:-1]
volatility = np.std(returns) * np.sqrt(252 * 86400)  # Annualized
print(f"Volatility: {volatility:.2%}")
```

(market-utils-volume-analysis)=
### Volume Analysis with Mid-Price Calculation

```{code-block} python
:name: market-utils-code-volume-analysis
:caption: Volume analysis with mid-price calculation example

from quantforge.market_utils import weighted_mid_price_batch

# Order book data
bids = np.array([100.0, 99.9, 99.8])
bid_qtys = np.array([100, 200, 500])  # Cumulative volume
asks = np.array([100.1, 100.2, 100.3])
ask_qtys = np.array([150, 300, 400])

# Weighted mid-price for each level
weighted_mids = weighted_mid_price_batch(
    bids, asks, bid_qtys, ask_qtys
)

# Order book imbalance analysis
imbalance = (bid_qtys - ask_qtys) / (bid_qtys + ask_qtys)
print(f"Order book imbalance: {imbalance}")
```

(market-utils-error-handling)=
## Error Handling

This module follows the IEEE 754 standard and returns NaN instead of raising errors:

```{code-block} python
:name: market-utils-code-error-handling
:caption: Error handling example

import math
from quantforge.market_utils import mid_price

# Does not raise errors
result = mid_price(-100.0, 100.0)  # Negative price
assert math.isnan(result)  # Returns NaN, not error

result = mid_price(float('inf'), 100.0)  # Infinity
assert math.isnan(result)  # Returns NaN, not error

# Large-scale processing continues
results = mid_price_batch(
    np.array([100.0, -50.0, 200.0]),  # Contains invalid values
    np.array([101.0, 100.0, 201.0])
)
# [100.5, NaN, 200.5]  # Processing continues
```

(market-utils-notes)=
## Notes

(market-utils-option-market-usage)=
### Usage in Options Markets

Extreme spreads are common in deep ITM options:

```{code-block} python
:name: market-utils-code-option-market-usage
:caption: Options market usage example

# Bad example: Processing stops with error
if ask - bid > bid:
    raise ValueError("Spread too wide")

# Good example: Continue with NaN
config = PricingConfig.with_config(max_spread_pct=0.5)
price = mid_price_with_config(1.0, 1000.0, config)
if math.isnan(price):
    # Estimate price using alternative method
    pass
```

(market-utils-memory-efficiency)=
### Memory Efficiency

For large datasets, leverage the zero-copy characteristics of Arrow arrays:

```{code-block} python
:name: market-utils-code-memory-efficiency
:caption: Memory-efficient usage example

# Efficient: Use views
mids = mid_price_batch(bids[mask], asks[mask])

# Inefficient: Create copies
mids = mid_price_batch(bids.copy(), asks.copy())
```

(market-utils-related-items)=
## Related Items

- [Black-Scholes Model](black_scholes.md) - Option pricing calculations
- [Implied Volatility](implied_vol.md) - IV back-calculation from market prices
- [Batch Processing](batch_processing.md) - Efficient large-scale processing