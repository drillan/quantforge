# Black76 Model API

The Black76 model for calculating prices of commodity futures and energy options.

## Overview

The Black76 model is used to calculate option prices for futures and forward contracts.
Primarily used in commodity, interest rate, and energy markets.

## API Usage

### Basic Price Calculation

```python
from quantforge.models import black76

# Call option price
# Parameters: f(forward), k(strike), t(time), r(rate), sigma
call_price = black76.call_price(75.50, 70.00, 0.25, 0.05, 0.3)

# Put option price  
# Parameters: f(forward), k(strike), t(time), r(rate), sigma
put_price = black76.put_price(75.50, 80.00, 0.25, 0.05, 0.3)
```

### Batch Processing

```python
import numpy as np

# Full array support with Broadcasting
forwards = np.array([70, 75, 80, 85])
strikes = np.array([65, 70, 75, 80])  # Arrays also possible
times = 0.5  # Scalars are automatically expanded
rates = 0.05
sigmas = np.array([0.20, 0.25, 0.30, 0.35])

# Parameters: forwards, strikes, times, rates, sigmas
call_prices = black76.call_price_batch(forwards, strikes, times, rates, sigmas)
put_prices = black76.put_price_batch(forwards, strikes, times, rates, sigmas)

# Greeks batch calculation (dictionary format)
greeks = black76.greeks_batch(forwards, strikes, times, rates, sigmas, is_calls=True)
print(greeks['delta'])  # NumPy array
print(greeks['vega'])   # NumPy array
```

For details, refer to the [Batch Processing API](batch_processing.md).

### Greek Calculations

```{code-block} python
:name: black76-code-greeks-calculation
:caption: Calculate all Greeks at once
:linenos:

# Calculate all Greeks at once
# Parameters: f(forward), k(strike), t(time), r(rate), sigma, is_call
greeks = black76.greeks(75.50, 75.00, 0.5, 0.05, 0.3, True)

# Access individual Greeks
print(f"Delta: {greeks.delta:.4f}")  # Forward price sensitivity
print(f"Gamma: {greeks.gamma:.4f}")  # Rate of change of delta
print(f"Vega: {greeks.vega:.4f}")    # Volatility sensitivity
print(f"Theta: {greeks.theta:.4f}")  # Time decay
print(f"Rho: {greeks.rho:.4f}")      # Interest rate sensitivity
```

### implied volatility

```{code-block} python
:name: black76-code-price-fforward-kstrike-ttime-rrate-iscall
:caption: Parameters: price, f(forward), k(strike), t(time), r(rate), is_call
:linenos:

# Parameters: price, f(forward), k(strike), t(time), r(rate), is_call
iv = black76.implied_volatility(5.50, 75.00, 75.00, 0.5, 0.05, True)
print(f"Implied Volatility: {iv:.4f}")
```

## Parameter Description

### Input Parameters

| Parameters | type | Description | Valid Range |
|-----------|-----|------|----------|
| `f` | float | Forward Price | > 0 |
| `k` | float | Exercise Price (Strike) | > 0 |
| `t` | float | Time to Maturity in Years | > 0 |
| `r` | float | Risk-free interest rate (annual) | optional |
| `sigma` | float | Volatility (annualized) | > 0 |
| `is_call` | bool | Option Type | True: Call, False: Put |

### Batch Processing Parameters

| Parameters | type | Description |
|-----------|-----|------|
| `forwards` | pa.array \| np.ndarray \| list | Multiple Forward Prices (Arrow/NumPy arrays) |
| `strikes` | float \| pa.array \| np.ndarray | Exercise Price (scalar or array) |
| `times` | float \| pa.array \| np.ndarray | Time to Maturity (scalar or array) |
| `rates` | float \| pa.array \| np.ndarray | Risk-free rate (scalar or array) |
| `sigmas` | float \| pa.array \| np.ndarray | Volatility (scalar or array) |

## Price Formula (Reference)

Call option:
$$C = e^{-rT} \cdot [F \cdot N(d_1) - K \cdot N(d_2)]$$

Put Option:
$$P = e^{-rT} \cdot [K \cdot N(-d_2) - F \cdot N(-d_1)]$$

where:
- $d_1 = \frac{\ln(F/K) + \sigma^2 T / 2}{\sigma\sqrt{T}}$
- $d_2 = d_1 - \sigma\sqrt{T}$

For detailed theoretical background, refer to the [Black76 Model Theory](../../models/black76.md).

## Error Handling

All price calculation functions return an error under the following conditions:

- f ≤ 0 (forward price is negative or zero)
- k ≤ 0 (strike price is negative or zero)
- t ≤ 0 (time to maturity is negative or zero)
- sigma ≤ 0 (volatility is negative or zero)
- number is NaN or infinity

```python
try:
    # Parameters: f(forward), k, t, r, sigma
    price = black76.call_price(-100, 100, 1.0, 0.05, 0.2)  # Invalid negative value
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
| all Greeks | Scheduled Measurement | Scheduled Measurement |
| implied volatility | Scheduled Measurement | Scheduled Measurement |

## Examples

### Energy Markets (Crude Oil Futures)

```python
from quantforge.models import black76

# WTI crude oil futures options
f = 85.00  # Futures price
k = 90.00  # Strike price
t = 0.25   # 3 months
r = 0.05   # Risk-free rate
sigma = 0.35  # Typical WTI volatility

# Price calculation
call_price = black76.call_price(f, k, t, r, sigma)
put_price = black76.put_price(f, k, t, r, sigma)

print(f"Call Price: ${call_price:.2f}")
print(f"Put Price: ${put_price:.2f}")

# Greeks calculation
greeks = black76.greeks(f, k, t, r, sigma, is_call=True)
print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
```

### Volatility Smile Analysis

```python
import numpy as np
from quantforge.models import black76

f = 100.0  # Forward price
strikes = np.linspace(80, 120, 21)
t = 0.25
r = 0.05

# Calculate IV for each strike
ivs = []
for k in strikes:
    # From actual market prices (using model prices here)
    if k < f:
        price = black76.put_price(f, k, t, r, 0.25)
        is_call = False
    else:
        price = black76.call_price(f, k, t, r, 0.25)
        is_call = True
    
    # Parameters: price, f, k, t, r, is_call
    iv = black76.implied_volatility(price, f, k, t, r, is_call)
    ivs.append(iv)

# Verify IV smile (plotting, etc.)
```

## Related Information

- [Black-Scholes Model API](black_scholes.md) - For stock options
- [Merton Model API](merton.md) - For assets with dividends
- [Implied Volatility API](implied_vol.md) - Details on IV calculation
- [Black76 Theoretical Background](../../models/black76.md) - Mathematical Details
