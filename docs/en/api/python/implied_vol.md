# Implied Volatility API

A set of functions that derive volatility from market prices. It supports Black-Scholes model, Black76 model, and Merton model.

## Overview

Implied volatility (IV) is the volatility calculated by reverse engineering from observed market option prices.
This reflects market participants' expectations about future price movements.

## API Usage

### Black-Scholes Model

Calculating IV from stock option market prices:

```python
from quantforge.models import black_scholes

# Implied volatility for call option
# Parameters: price, s, k, t, r, is_call
iv = black_scholes.implied_volatility(
    10.45,    # Market price
    100.0,    # Spot price
    100.0,    # Strike price
    1.0,      # Time to maturity (years)
    0.05,     # Risk-free rate
    True      # True: call, False: put
)

print(f"Implied Volatility: {iv:.4f}")
```

### Black76 Model

Calculating IV from market prices of commodity futures options:

```python
from quantforge.models import black76

# Implied volatility for commodity futures options
# Parameters: price, f, k, t, r, is_call
iv = black76.implied_volatility(
    5.50,     # Market price
    75.00,    # Forward price
    75.00,    # Strike price
    0.5,      # Time to maturity (years)
    0.05,     # Risk-free rate
    True      # True: call, False: put
)

print(f"Implied Volatility: {iv:.4f}")
```

### Merton Model

Calculating IV from market price of dividend-paying assets:

```python
from quantforge.models import merton

# Implied volatility for dividend-paying assets
# Parameters: price, s, k, t, r, q, is_call
iv = merton.implied_volatility(
    10.45,    # Market price
    100.0,    # Spot price
    100.0,    # Strike price
    1.0,      # Time to maturity (years)
    0.05,     # Risk-free rate
    0.03,     # Dividend yield
    True      # True: call, False: put
)

print(f"Implied Volatility: {iv:.4f}")
```

### American Option Models

Calculating IV from early exercise option market prices:

```python
from quantforge.models import american

# Implied volatility for American options
# Parameters: price, s, k, t, r, q, is_call
iv = american.implied_volatility(
    15.50,    # Market price
    100.0,    # Spot price
    100.0,    # Strike price
    1.0,      # Time to maturity (years)
    0.05,     # Risk-free rate
    0.03,     # Dividend yield
    True      # True: call, False: put
)

print(f"Implied Volatility: {iv:.4f}")
```

## Batch Processing

You can calculate implied volatility from multiple market prices in bulk:

```python
import numpy as np
from quantforge.models import black_scholes

# Full array support (Broadcasting compatible)
market_prices = np.array([10.0, 10.5, 11.0, 11.5])
spots = 100.0  # Scalars are automatically expanded
strikes = np.array([95, 100, 105, 110])
times = 1.0
rates = 0.05
is_calls = True

# Parameters: prices, spots, strikes, times, rates, is_calls
ivs = black_scholes.implied_volatility_batch(
    market_prices, spots, strikes, times, rates, is_calls
)

# Fast calculation of volatility smile
strikes = np.linspace(80, 120, 41)
market_prices = get_market_prices(strikes)  # Get market data

ivs = black_scholes.implied_volatility_batch(
    market_prices, 100.0, strikes, 0.25, 0.05, strikes >= 100.0
)
```

For details, refer to the [Batch Processing API](batch_processing.md).

## Calculation Method

### Newton-Raphson Method

QuantForge uses the fast-converging Newton-Raphson method:

```
σ_{n+1} = σ_n - f(σ_n) / f'(σ_n)

where:
- f(σ) = Price(σ) - MarketPrice
- f'(σ) = Vega(σ)
```

### Convergence Conditions

- Maximum number of iterations: 100
- Convergence criterion: |σ_{n+1} - σ_n| < 1e-8
- Default: 0.2 (20%)

## Parameter Description

### Common Parameters

| Parameters | type | Description | Valid Range |
|-----------|-----|------|----------|
| `price` | float | Option prices observed in the marketplace | > 0 |
| `k` | float | Exercise Price | > 0 |
| `t` | float | Time to Maturity in Years | > 0 |
| `r` | float | Risk-free interest rate (annual) | optional |
| `is_call` | bool | Option Type | True: Call, False: Put |

### Model-specific parameters

| Parameters | Black-Scholes | Black76 | Merton | American | Description |
|-----------|---------------|---------|--------|----------|------|
| Underlying Asset Price | `s` (spot) | `f` (forward) | `s` (spot) | `s` (spot) | Current Price vs Future Price |
| Dividend Yield | - | - | `q` | `q` | Dividend Yield (Annual) |

## Error Handling

The following error occurs under the following conditions:

### ValueError (input error)
- Market price is negative or zero
- Option price is below intrinsic value
- invalid input parameter (NaN, infinity)

### RuntimeError (convergence error)
- Newton-Raphson method does not converge
- Volatility outside reasonable range (0.001 to 10.0)

```python
try:
    # Invalid market price (below intrinsic value)
    iv = black_scholes.implied_volatility(
        0.01,     # Market price is too low
        100.0,    # Spot price
        50.0,     # Strike price (deep ITM)
        1.0,      # Time to maturity
        0.05,     # Risk-free rate
        True      # Call
    )
except RuntimeError as e:
    print(f"Convergence error: {e}")
```

## Examples

### Calculating Volatility Smile

```python
import numpy as np
from quantforge.models import black_scholes, black76
import matplotlib.pyplot as plt

# Volatility smile with Black-Scholes
spot = 100.0
time = 0.25
rate = 0.05
strikes = np.linspace(80, 120, 21)

ivs_bs = []
for strike in strikes:
    # Get market price (actual data or simulation)
    market_price = get_market_price_bs(spot, strike)
    is_call = strike >= spot
    
    # Parameters: price, s, k, t, r, is_call
    iv = black_scholes.implied_volatility(
        market_price, spot, strike, time, rate, is_call
    )
    ivs_bs.append(iv)

# Volatility smile with Black76 (commodity markets)
f = 75.0
t = 0.5
r = 0.05
strikes_b76 = np.linspace(60, 90, 21)

ivs_b76 = []
for strike in strikes_b76:
    # Get market price
    market_price = get_market_price_b76(f, strike)
    is_call = strike >= f
    
    # Parameters: price, f, k, t, r, is_call
    iv = black76.implied_volatility(
        market_price, f, strike, t, r, is_call
    )
    ivs_b76.append(iv)

# Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.plot(strikes, ivs_bs)
ax1.set_xlabel('Strike')
ax1.set_ylabel('Implied Volatility')
ax1.set_title('Equity Options (Black-Scholes)')

ax2.plot(strikes_b76, ivs_b76)
ax2.set_xlabel('Strike')
ax2.set_ylabel('Implied Volatility')
ax2.set_title('Commodity Options (Black76)')

plt.show()
```

### IV Time Series Analysis

```python
from datetime import datetime, timedelta
from quantforge.models import black_scholes

# ATM option IV evolution
spot_prices = [100, 101, 99, 102, 98]
market_prices = [5.2, 5.5, 5.3, 5.7, 5.4]
dates = [datetime.now() + timedelta(days=i) for i in range(5)]

ivs = []
for spot, price in zip(spot_prices, market_prices):
    # Parameters: price, s, k, t, r, is_call
    iv = black_scholes.implied_volatility(
        price, spot, 100.0, 0.25, 0.05, True
    )
    ivs.append(iv)

# Plot IV evolution
plt.plot(dates, ivs)
plt.xlabel('Date')
plt.ylabel('Implied Volatility')
plt.title('ATM IV Time Series')
plt.xticks(rotation=45)
plt.show()
```

## Performance

:::{note}
Measurement Environment: AMD Ryzen 5 5600G, CUI Mode
:::

| model | Single Calculation | 1000-item batch |
|--------|----------|--------------|
| Black-Scholes IV | 1.5 μs | Scheduled Measurement |
| Black76 IV | Scheduled Measurement | Scheduled Measurement |
| Merton IV | Scheduled Measurement | Scheduled Measurement |

Convergence Performance:
- Average repetitions: 3-5
- Worst-case: 10-15 times (deep OTM/ITM)
- Convergence Rate: > 99.9%

## Precautions

1. **Importance of Initial Values**: While the default initial value (20%) works well in many cases,
Extreme market conditions may require adjustments.

2. **Arbitrage Opportunities**: When market prices fall below their theoretical lower bounds (intrinsic value),
IV cannot be calculated.

3. **Numerical Precision**: Deep OTM/ITM options may encounter numerical precision issues.

## Related Information

- [Black-Scholes Model API](black_scholes.md)
- [Black76 Model API](black76.md)
- [Merton Model API](merton.md)
- [Pricing API Overview](pricing.md)
