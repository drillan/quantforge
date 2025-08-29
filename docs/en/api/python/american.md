# American Option Model API

A high-precision approximation model for calculating the price of options with early exercise rights.

## Overview

Provides analytical approximate solutions based on the Bjerksund-Stensland (2002) model.
High-speed analytical approximation enables efficient price calculation, with numerical errors below 0.1%.

## API Usage

### Basic Price Calculation

```python
from quantforge.models import american

# Call option price
# Parameters: s(spot), k(strike), t(time), r(rate), q(dividend), sigma
call_price = american.call_price(100.0, 105.0, 1.0, 0.05, 0.03, 0.2)

# Put option price
# Parameters: s(spot), k(strike), t(time), r(rate), q(dividend), sigma
put_price = american.put_price(100.0, 105.0, 1.0, 0.05, 0.03, 0.2)
```

### Batch Processing

```python
import numpy as np

# Full array support with Broadcasting
spots = np.array([95, 100, 105, 110])
strikes = 100.0  # Scalar automatically broadcasts
times = np.array([0.5, 1.0, 1.5, 2.0])
rates = 0.05
dividend_yields = 0.03
sigmas = np.array([0.18, 0.20, 0.22, 0.24])

# Parameters: spots, strikes, times, rates, dividend_yields, sigmas
call_prices = american.call_price_batch(spots, strikes, times, rates, dividend_yields, sigmas)
put_prices = american.put_price_batch(spots, strikes, times, rates, dividend_yields, sigmas)

# Greeks batch calculation (dictionary format)
greeks = american.greeks_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_calls=False)
print(greeks['delta'])  # NumPy array
print(greeks['gamma'])  # NumPy array

# Early exercise boundary batch calculation
boundaries = american.exercise_boundary_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_calls=False)
```

For details, refer to the [Batch Processing API](batch_processing.md).

### Greek Calculations

```python
# Calculate all Greeks at once
# Parameters: s, k, t, r, q, sigma, is_call
greeks = american.greeks(100.0, 100.0, 1.0, 0.05, 0.03, 0.2, True)

# Access individual Greeks
print(f"Delta: {greeks.delta:.4f}")  # Spot price sensitivity
print(f"Gamma: {greeks.gamma:.4f}")  # Rate of change of delta
print(f"Vega: {greeks.vega:.4f}")    # Volatility sensitivity
print(f"Theta: {greeks.theta:.4f}")  # Time decay
print(f"Rho: {greeks.rho:.4f}")      # Interest rate sensitivity
```

### implied volatility

```python
# Parameters: price, s, k, t, r, q, is_call
iv = american.implied_volatility(15.50, 100.0, 100.0, 1.0, 0.05, 0.03, True)
print(f"Implied Volatility: {iv:.4f}")
```

### Early Exercise Boundary

```python
# Early exercise boundary calculation
# Parameters: s, k, t, r, q, sigma, is_call
boundary = american.exercise_boundary(100.0, 100.0, 1.0, 0.05, 0.03, 0.2, True)
print(f"Exercise boundary: {boundary:.2f}")
```

## Parameter Description

### Input Parameters

| Parameters | type | Description | Valid Range |
|-----------|-----|------|----------|
| `s` | float | Spot Price | > 0 |
| `k` | float | Exercise Price | > 0 |
| `t` | float | Time to Maturity in Years | > 0 |
| `r` | float | risk-free rate | ≥ 0 |
| `q` | float | Dividend Yield | ≥ 0 |
| `sigma` | float | Volatility (annualized) | > 0 |
| `is_call` | bool | Option Type | True: Call, False: Put |

### Batch Processing Parameters

| Parameters | type | Description |
|-----------|-----|------|
| `spots` | np.ndarray | Multiple Spot Prices |
| `k` | float | Exercise Price (Common) |
| `t` | float | Time to Maturity (Common) |
| `r` | float | Risk-free rate (common) |
| `q` | float | Dividend Yield (Common) |
| `sigma` | float | Volatility (Common) |

## Price Formula (Reference)

Call option (Bjerksund-Stensland approximation):
$$C_{Am} = \alpha S_0^{\beta} - \alpha \phi(S_0, T, \beta, I, I) + \phi(S_0, T, 1, I, I) - K\phi(S_0, T, 0, K, I)$$

Early exercise boundary:
$$I = B_0 + (B_\infty - B_0)(1 - e^{h(T)})$$

where:
- $I$ is the early exercise boundary
- $\alpha, \beta$ are auxiliary parameters
- $\phi$ is the auxiliary function

For detailed theoretical background, refer to the [American Options Model Theory](../../models/american_options.md).

## Error Handling

All price calculation functions return an error under the following conditions:

- s ≤ 0 (spot price is negative or zero)
- k ≤ 0 (strike price is negative or zero)
- t ≤ 0 (time to maturity is negative or zero)
- sigma ≤ 0 (volatility is negative or zero)
- q < 0 (dividend yield is negative)
- q > r (dividend yield exceeds risk-free rate - dividend arbitrage opportunity)
- number is NaN or infinity

```python
try:
    # Parameters: s, k, t, r, q, sigma
    price = american.call_price(100.0, 100.0, 1.0, 0.05, 0.10, 0.2)  # q > r
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
| Early Exercise Boundary | Scheduled Measurement | Scheduled Measurement |

## Examples

### Valuation of Dividend-Bearing Stock Options

```python
from quantforge.models import american

# American put for stock with 3% dividend yield
s = 100.0    # Current stock price
k = 105.0    # Strike price (ITM)
t = 0.5      # 6-month maturity
r = 0.05     # Risk-free rate 5%
q = 0.03     # Dividend yield 3%
sigma = 0.25 # Volatility 25%

# Price calculation
put_price = american.put_price(s, k, t, r, q, sigma)

print(f"Put Price: ${put_price:.2f}")

# Greeks calculation
greeks = american.greeks(s, k, t, r, q, sigma, False)
print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
```

### Early Exercise Determinations

```python
import numpy as np
from quantforge.models import american

# Parameter settings
k = 100.0    # Strike price
t = 1.0      # 1-year maturity
r = 0.05     # Risk-free rate
q = 0.03     # Dividend yield
sigma = 0.2  # Volatility

# Early exercise boundary calculation
boundary_call = american.exercise_boundary(100.0, k, t, r, q, sigma, True)
boundary_put = american.exercise_boundary(100.0, k, t, r, q, sigma, False)

print(f"Call exercise boundary: ${boundary_call:.2f}")
print(f"Put exercise boundary: ${boundary_put:.2f}")

# Exercise determination at current stock price
spots = np.array([80, 90, 100, 110, 120])
for s in spots:
    call_price = american.call_price(s, k, t, r, q, sigma)
    put_price = american.put_price(s, k, t, r, q, sigma)
    
    # Intrinsic value
    intrinsic_call = max(s - k, 0)
    intrinsic_put = max(k - s, 0)
    
    print(f"S=${s}: Call=${call_price:.2f} (intrinsic=${intrinsic_call:.2f}), "
          f"Put=${put_price:.2f} (intrinsic=${intrinsic_put:.2f})")
```

## Related Information

- [Black-Scholes Model](black_scholes.md) - European Options
- [Merton Model](merton.md) - Dividend-paying European Options
- [Implied Volatility API](implied_vol.md) - Details on IV calculation
- [American Options Theoretical Background](../../models/american_options.md) - Mathematical Details
