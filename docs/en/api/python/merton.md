# Merton Model API

A model for calculating the price of a European option on an asset that pays dividends.

## Overview

The Merton model is an option pricing model that accounts for continuous dividend yields.
Accurately calculates option prices for assets that generate regular returns, such as stock indices, dividend stocks, and foreign exchange.

For detailed theoretical background, refer to the [Merton Model Theory](../../models/merton.md).

## API Usage

### Basic Price Calculation

```python
from quantforge.models import merton

# Call option price
# Parameters: s(spot), k(strike), t(time), r(rate), q(dividend), sigma
call_price = merton.call_price(100.0, 105.0, 1.0, 0.05, 0.03, 0.2)

# Put option price
# Parameters: s(spot), k(strike), t(time), r(rate), q(dividend), sigma
put_price = merton.put_price(100.0, 105.0, 1.0, 0.05, 0.03, 0.2)
```

### Batch Processing

Full array support and efficient calculations via broadcasting:

```python
import numpy as np

# All parameters accept arrays (Broadcasting supported)
spots = np.array([95, 100, 105, 110])
strikes = 100.0  # Scalars are automatically expanded
times = 1.0
rates = 0.05
dividend_yields = np.array([0.01, 0.02, 0.03, 0.04])
sigmas = np.array([0.18, 0.20, 0.22, 0.24])

# Parameters: spots, strikes, times, rates, dividend_yields, sigmas
call_prices = merton.call_price_batch(spots, strikes, times, rates, dividend_yields, sigmas)
put_prices = merton.put_price_batch(spots, strikes, times, rates, dividend_yields, sigmas)

# Greeks batch calculation (returned in dictionary format)
greeks = merton.greeks_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_calls=True)
print(greeks['delta'])         # NumPy array
print(greeks['dividend_rho'])  # Dividend yield sensitivity
```

For details, refer to the [Batch Processing API](batch_processing.md).

### Greek Calculations

Bulk calculation of option sensitivities (Greeks) considering dividends:

```{code-block} python
:name: merton-code-greeks-calculation
:caption: Calculate all Greeks at once
:linenos:

# Calculate all Greeks at once
# Parameters: s(spot), k, t, r, q, sigma, is_call
greeks = merton.greeks(100.0, 100.0, 1.0, 0.05, 0.03, 0.2, True)

# Access individual Greeks
print(f"Delta: {greeks.delta:.4f}")          # Spot price sensitivity (dividend-adjusted)
print(f"Gamma: {greeks.gamma:.4f}")          # Rate of change of delta
print(f"Vega: {greeks.vega:.4f}")            # Volatility sensitivity
print(f"Theta: {greeks.theta:.4f}")          # Time decay (including dividend effect)
print(f"Rho: {greeks.rho:.4f}")              # Interest rate sensitivity
print(f"Dividend Rho: {greeks.dividend_rho:.4f}")  # Dividend yield sensitivity (Merton-specific)
```

### implied volatility

Deriving volatility from market prices:

```{code-block} python
:name: merton-code-price-s-k-t-r-q-iscall
:caption: Parameters: price, s, k, t, r, q, is_call
:linenos:

# Parameters: price, s, k, t, r, q, is_call
iv = merton.implied_volatility(10.45, 100.0, 100.0, 1.0, 0.05, 0.03, True)
print(f"Implied Volatility: {iv:.4f}")
```

## Parameter Description

### Input Parameters

| Parameters | type | Description | Valid Range |
|-----------|-----|------|----------|
| `s` | float | Spot Price (Current Asset Price) | > 0 |
| `k` | float | Exercise Price (Strike) | > 0 |
| `t` | float | Time to Maturity in Years | > 0 |
| `r` | float | Risk-free interest rate (annual) | optional |
| `q` | float | Dividend Yield (Annual) | ≥ 0 |
| `sigma` | float | Volatility (annualized) | > 0 |
| `is_call` | bool | Option Type | True: Call, False: Put |

### Batch Processing Parameters

| Parameters | type | Description |
|-----------|-----|------|
| `spots` | pa.array \| np.ndarray \| list | Multiple Spot Prices (Arrow/NumPy arrays) |
| `strikes` | float \| pa.array \| np.ndarray | Exercise Price (scalar or array) |
| `times` | float \| pa.array \| np.ndarray | Time to Maturity (scalar or array) |
| `rates` | float \| pa.array \| np.ndarray | Risk-free rate (scalar or array) |
| `dividend_yields` | float \| pa.array \| np.ndarray | Dividend Yield (scalar or array) |
| `sigmas` | float \| pa.array \| np.ndarray | Volatility (scalar or array) |

## Price Formula (Reference)

Call option:
$$C = S_0 \cdot e^{-qT} \cdot N(d_1) - K \cdot e^{-rT} \cdot N(d_2)$$

Put Option:
$$P = K \cdot e^{-rT} \cdot N(-d_2) - S_0 \cdot e^{-qT} \cdot N(-d_1)$$

where:
- $d_1 = \frac{\ln(S_0/K) + (r - q + \sigma^2/2)T}{\sigma\sqrt{T}}$
- $d_2 = d_1 - \sigma\sqrt{T}$

For detailed theoretical background, refer to the [Merton Model Theory](../../models/merton.md).

## Error Handling

All price calculation functions return an error under the following conditions:

- s ≤ 0 (spot price is negative or zero)
- k ≤ 0 (strike price is negative or zero)
- t < 0 (time to maturity is negative)
- sigma ≤ 0 (volatility is negative or zero)
- q < 0 (dividend yield is negative)
- number is NaN or infinity
- q > 1.0 (dividend yield > 100% - warning)

```python
try:
    # Parameters: s, k, t, r, q(negative), sigma
    price = merton.call_price(100, 100, 1.0, 0.05, -0.03, 0.2)  # Invalid negative dividend
except ValueError as e:
    print(f"Input error: {e}")
```

## Performance Metrics

:::{note}
Measurement Environment: AMD Ryzen 5 5600G, CUI Mode
:::

| Operation | Single Calculation | 1 million batch |
|------|----------|--------------:|
| Call/Put Price | Scheduled Measurement | Scheduled Measurement |
| All Greeks (6 species) | Scheduled Measurement | Scheduled Measurement |
| implied volatility | Scheduled Measurement | Scheduled Measurement |

## Examples

### Option Pricing for High Dividend Stocks

```python
from quantforge.models import merton

# High dividend stock (4% dividend yield)
s = 50.0
k = 52.0
t = 0.5  # 6 months
r = 0.05
q = 0.04  # 4% dividend yield
sigma = 0.3

# Price calculation
call_price = merton.call_price(s, k, t, r, q, sigma)
put_price = merton.put_price(s, k, t, r, q, sigma)

print(f"Call Price: ${call_price:.2f}")
print(f"Put Price: ${put_price:.2f}")

# Greeks calculation
greeks = merton.greeks(s, k, t, r, q, sigma, is_call=True)
print(f"Delta: {greeks.delta:.4f}")
print(f"Dividend Rho: {greeks.dividend_rho:.4f}")  # Dividend sensitivity
```

### Stock Index Options (S&P 500)

```python
import numpy as np
from quantforge.models import merton

# S&P 500 index options
s = 4500.0
strikes = np.linspace(4300, 4700, 9)
t = 0.25  # 3 months
r = 0.045
q = 0.018  # Typical S&P 500 dividend yield
sigma = 0.16

# Calculate prices for each strike
for k in strikes:
    # Parameters: s, k, t, r, q, sigma
    call = merton.call_price(s, k, t, r, q, sigma)
    put = merton.put_price(s, k, t, r, q, sigma)
    
    moneyness = "ATM" if abs(s - k) < 50 else ("ITM" if s > k else "OTM")
    print(f"K={k:.0f} ({moneyness}): Call=${call:.2f}, Put=${put:.2f}")
```

## Related Information

- [Black-Scholes Model API](black_scholes.md) - Basic model without dividends
- [Black76 Model API](black76.md) - For commodities and futures options
- [Implied Volatility API](implied_vol.md) - Details on IV calculation
- [Theoretical Background of the Merton Model](../../models/merton.md) - Mathematical Details
