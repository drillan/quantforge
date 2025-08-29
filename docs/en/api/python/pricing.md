# Price Calculation API Overview

QuantForge's pricing calculation API provides multiple option pricing models through a unified interface.

## Supported Models

### Black-Scholes Model
A standard pricing model for stock options, using the spot price as the input.

```python
from quantforge.models import black_scholes

# Parameters: s(spot), k(strike), t(time), r(rate), sigma
price = black_scholes.call_price(100.0, 105.0, 1.0, 0.05, 0.2)
```

Details: [Black-Scholes Model API](black_scholes.md)

### Black76 Model
Price model for commodity futures and interest rate derivatives. Forward price is used as input.

```python
from quantforge.models import black76

# Parameters: f(forward), k(strike), t(time), r(rate), sigma
price = black76.call_price(75.0, 70.0, 0.25, 0.05, 0.3)
```

Details: [Black76 Model API](black76.md)

### Merton Model
An option pricing model for assets paying dividends, accounting for continuous dividend yields.

```python
from quantforge.models import merton

# Parameters: s(spot), k(strike), t(time), r(rate), q(dividend), sigma
price = merton.call_price(100.0, 105.0, 1.0, 0.05, 0.03, 0.2)
```

Details: [Merton Model API](merton.md)

### American Option Models
A pricing model for options with early exercise rights, providing high-precision approximate solutions based on Bjerksund-Stensland (2002).

```python
from quantforge.models import american

# Parameters: s(spot), k(strike), t(time), r(rate), q(dividend), sigma
price = american.call_price(100.0, 105.0, 1.0, 0.05, 0.03, 0.2)
```

Details: [American Option Model API](american.md)

## Model Selection Guide

### When Using Black-Scholes
- **Stock Options**: Individual stocks, stock index options
- **Assets Without Dividends**: Option for assets that do not pay dividends
- **Spot Price Base**: Directly calculated from current market prices

### When using Black76
- **Commodity Futures Options**: Options on futures contracts for commodities like crude oil, gold, and agricultural products.
- **Interest Rate Derivatives**: Interest rate caps, floors, and swaptions
- **Forward Price Base**: Calculated from future point prices
- **Assets with storage costs and benefits yield**: Accounts for storage costs and benefits associated with commodities.

### When using the Merton model
- **High-Dividend Stocks**: Options on individual stocks with high dividend yields
- **Stock Index Options**: S&P 500, Nikkei 225, and other indices that incorporate dividend payments
- **Foreign Exchange Options**: Treat foreign interest rates as dividend yields
- **Dividend-paying assets**: Any assets that generate regular dividends or distributions.

### when using American options
- **Early exercise is advantageous in:** Dividend-paying assets, deep ITM options
- **Individual Stock Options with Dividends**: Early exercise determination before dividend payment dates
- **High-yield dividend assets**: Early exercise premium becomes significant
- **General Put Options**: American puts are consistently more valuable than European ones.

## Common Functions

All models provide the following identical functionality:

### Price Calculation
```python
# Call option price
call_price = model.call_price(...)

# Put option price
put_price = model.put_price(...)
```

### Batch Processing
```python
import numpy as np

# Batch calculation with multiple prices
prices = np.array([90, 95, 100, 105, 110])
results = model.call_price_batch(prices, ...)
```

### Greek Calculations
```python
# Get all Greeks at once
greeks = model.greeks(..., is_call=True)

print(f"Delta: {greeks.delta}")  # Underlying asset price sensitivity
print(f"Gamma: {greeks.gamma}")  # Rate of change of delta
print(f"Vega: {greeks.vega}")    # Volatility sensitivity
print(f"Theta: {greeks.theta}")  # Time decay
print(f"Rho: {greeks.rho}")      # Interest rate sensitivity
```

### implied volatility
```python
# Calculate volatility from market prices
iv = model.implied_volatility(market_price, ...)
```

## Parameter Correspondence

| Parameters | Black-Scholes | Black76 | Merton | Description |
|-----------|---------------|---------|--------|------|
| Underlying Asset Price | `s` (spot) | `f` (forward) | `s` (spot) | Current Price vs Futures Price |
| Exercise Price | `k` | `k` | `k` | Common |
| maturity | `t` | `t` | `t` | Common (yearly) |
| interest | `r` | `r` | `r` | Common (Annual) |
| Dividend Yield | - | - | `q` | Merton Unique (annual) |
| Volatility | `sigma` | `sigma` | `sigma` | Common (Annual) |

## Performance

:::{note}
Measurement Environment: AMD Ryzen 5 5600G, CUI Mode
Measurement Method: Actual values refer to [benchmarks](../../performance/benchmarks.md)
:::

| Operation | Processing Time | Remarks |
|------|----------|------|
| Single Price Calculation | 1.4 μs | Black-Scholes Actual Values |
| Greek Calculations | Scheduled Measurement | - |
| IV Calculation | 1.5 μs | Black-Scholes Actual Values |
| Batch Processing (1 million) | 55.6ms | Black-Scholes Actual Values |

## Comparison of Examples

### Stock Options (Black-Scholes)
```python
from quantforge.models import black_scholes

# Calculate from current stock price
spot_price = 100.0
strike = 105.0
time_to_maturity = 0.25
risk_free_rate = 0.05
volatility = 0.2

call_price = black_scholes.call_price(
    spot_price, strike, time_to_maturity, risk_free_rate, volatility
)
```

### Crude Oil Futures Options (Black76)
```python
from quantforge.models import black76

# Calculate from futures price
forward_price = 85.0  # WTI futures price
strike = 90.0
time_to_maturity = 0.25
risk_free_rate = 0.05
volatility = 0.35

call_price = black76.call_price(
    forward_price, strike, time_to_maturity, risk_free_rate, volatility
)
```

## Detailed Documentation

### API Reference
- [Black-Scholes Model API](black_scholes.md)
- [Black76 Model API](black76.md)
- [Merton Model API](merton.md)
- [Implied Volatility API](implied_vol.md)

### Theoretical Background
- [Black-Scholes Model Theory](../../models/black_scholes.md)
- [Black76 Model Theory](../../models/black76.md)
- [Merton Model Theory](../../models/merton.md)
