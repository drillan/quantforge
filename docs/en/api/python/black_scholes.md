(api-black-scholes)=
# Black-Scholes Model API

A standard model for calculating the price of European options.

(api-black-scholes-overview)=
## Overview

The Black-Scholes model serves as the fundamental model for calculating the theoretical price of stock options.
Assuming a stock price process following a lognormal distribution, we provide an analytical pricing formula.

(api-black-scholes-usage)=
## API Usage

(api-black-scholes-basic-calculation)=
### Basic Price Calculation

```{code-block} python
:name: api-black-scholes-code-basic
:caption: Basic price calculation
:linenos:
from quantforge.models import black_scholes

# Call option price
# Parameters: s(spot), k(strike), t(time), r(rate), sigma
call_price = black_scholes.call_price(100.0, 105.0, 1.0, 0.05, 0.2)

# Put option price
# Parameters: s(spot), k(strike), t(time), r(rate), sigma
put_price = black_scholes.put_price(100.0, 105.0, 1.0, 0.05, 0.2)
```

(api-black-scholes-batch-processing)=
### Batch Processing

Full array support and efficient calculations via broadcasting:

```{code-block} python
:name: api-black-scholes-code-batch
:caption: Batch processing example
:linenos:
import numpy as np

# All parameters accept arrays (Broadcasting supported)
spots = np.array([95, 100, 105, 110])
strikes = 100.0  # Scalars are automatically expanded to array size
times = np.array([0.5, 1.0, 1.5, 2.0])
rates = 0.05
sigmas = np.array([0.18, 0.20, 0.22, 0.24])

# Parameters: spots, strikes, times, rates, sigmas
call_prices = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)
put_prices = black_scholes.put_price_batch(spots, strikes, times, rates, sigmas)

# Greeks batch calculation (returned in dictionary format)
greeks = black_scholes.greeks_batch(spots, strikes, times, rates, sigmas, is_calls=True)
portfolio_delta = greeks['delta'].sum()  # NumPy array operations
portfolio_vega = greeks['vega'].sum()
```

For details, refer to the [Batch Processing API](batch_processing.md).

(api-black-scholes-greeks-calculation)=
### Greek Calculations

Bulk calculate optional sensitivities (Greeks):

```{code-block} python
:name: black-scholes-code-greeks-calculation
:caption: Calculate all Greeks at once
:linenos:
# Calculate all Greeks at once
# Parameters: s(spot), k, t, r, sigma, is_call
greeks = black_scholes.greeks(100.0, 100.0, 1.0, 0.05, 0.2, True)

# Access individual Greeks
print(f"Delta: {greeks.delta:.4f}")  # Sensitivity to spot price
print(f"Gamma: {greeks.gamma:.4f}")  # Rate of change of delta
print(f"Vega: {greeks.vega:.4f}")    # Volatility sensitivity
print(f"Theta: {greeks.theta:.4f}")  # Time decay
print(f"Rho: {greeks.rho:.4f}")      # Interest rate sensitivity
```

(api-black-scholes-implied-volatility)=
### implied volatility

Deriving volatility from market prices:

```{code-block} python
:name: black-scholes-code-price-s-k-t-r-iscall
:caption: Parameters: price, s, k, t, r, is_call
:linenos:
# Parameters: price, s, k, t, r, is_call
iv = black_scholes.implied_volatility(10.45, 100.0, 100.0, 1.0, 0.05, True)
print(f"Implied Volatility: {iv:.4f}")
```

(api-black-scholes-parameters)=
## Parameter Description

(api-black-scholes-input-parameters)=
### Input Parameters

```{list-table} Input Parameters
:name: api-black-scholes-table-parameters
:header-rows: 1
:widths: 20 20 40 20

* - Parameters
  - type
  - Description
  - Valid Range
* - `s`
  - float
  - Spot Price (Current Stock Price)
  - > 0
* - `k`
  - float
  - Exercise Price (Strike)
  - > 0
* - `t`
  - float
  - Time to Maturity in Years
  - > 0
* - `r`
  - float
  - Risk-free interest rate (annual)
  - optional
* - `sigma`
  - float
  - Volatility (annualized)
  - > 0
* - `is_call`
  - bool
  - Option Type
  - True: Call, False: Put
```

(api-black-scholes-batch-parameters)=
### Batch Processing Parameters

```{list-table} Batch Processing Parameters
:name: api-black-scholes-table-batch-params
:header-rows: 1
:widths: 25 25 50

* - Parameters
  - type
  - Description
* - `spots`
  - pa.array | np.ndarray | list
  - Multiple Spot Prices (Arrow/NumPy arrays)
* - `strikes`
  - float | pa.array | np.ndarray
  - Exercise Price (scalar or array)
* - `times`
  - float | pa.array | np.ndarray
  - Time to Maturity (scalar or array)
* - `rates`
  - float | pa.array | np.ndarray
  - Risk-free rate (scalar or array)
* - `sigmas`
  - float | pa.array | np.ndarray
  - Volatility (scalar or array)
```

(api-black-scholes-formulas)=
## Price Formula (Reference)

Call option:

```{math}
:name: api-black-scholes-eq-call

C = S_0 \cdot N(d_1) - K \cdot e^{-rT} \cdot N(d_2)
```

Put Option:

```{math}
:name: api-black-scholes-eq-put

P = K \cdot e^{-rT} \cdot N(-d_2) - S_0 \cdot N(-d_1)
```

where:

```{math}
:name: api-black-scholes-eq-d1-d2

d_1 = \frac{\ln(S_0/K) + (r + \sigma^2/2)T}{\sigma\sqrt{T}}, \quad d_2 = d_1 - \sigma\sqrt{T}
```

For detailed theoretical background, refer to the [Mathematical Model](../../models/black_scholes.md).

(api-black-scholes-error-handling)=
## Error Handling

All price calculation functions return an error under the following conditions:

- s ≤ 0 (spot price is negative or zero)
- k ≤ 0 (strike price is negative or zero)
- t < 0 (time to maturity is negative)
- sigma ≤ 0 (volatility is negative or zero)
- number is NaN or infinity

```{code-block} python
:name: api-black-scholes-code-error
:caption: Error handling example
:linenos:
try:
    # Parameters: s(spot), k, t, r, sigma
    price = black_scholes.call_price(-100, 100, 1.0, 0.05, 0.2)  # Invalid negative value
except ValueError as e:
    print(f"Input error: {e}")
```

(api-black-scholes-performance)=
## Performance Metrics

:::{note}
Measurement Environment: AMD Ryzen 5 5600G, CUI Mode
Measurement Method: Actual values refer to [benchmarks](../../performance/benchmarks.md)
:::

```{list-table} Performance Metrics
:name: api-black-scholes-table-performance
:header-rows: 1
:widths: 40 30 30

* - Operation
  - Single Calculation
  - 1 million batch
* - Call/Put Price
  - 1.4 μs
  - 55.6ms
* - all Greeks
  - Scheduled Measurement
  - Scheduled Measurement
* - implied volatility
  - 1.5 μs
  - Scheduled Measurement
```

(api-black-scholes-examples)=
## Examples

(api-black-scholes-atm-example)=
### ATM Option Pricing and Greeks

```python
from quantforge.models import black_scholes

# ATM (At The Money) option
s = 100.0
k = 100.0
t = 0.25  # 3 months
r = 0.05
sigma = 0.2

# Price calculation
call_price = black_scholes.call_price(s, k, t, r, sigma)
put_price = black_scholes.put_price(s, k, t, r, sigma)

print(f"Call Price: ${call_price:.2f}")
print(f"Put Price: ${put_price:.2f}")

# Greeks calculation
greeks = black_scholes.greeks(s, k, t, r, sigma, is_call=True)
print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
```

### Volatility Smile Analysis

```python
import numpy as np
from quantforge.models import black_scholes

s = 100.0
t = 0.25
r = 0.05
strikes = np.linspace(80, 120, 21)

# Calculate IV from market prices (hypothetical) for each strike
ivs = []
for k in strikes:
    # Use actual market prices
    market_price = get_market_price(k)  # Market data retrieval function
    is_call = k >= s
    
    # Parameters: price, s, k, t, r, is_call
    iv = black_scholes.implied_volatility(
        market_price, s, k, t, r, is_call
    )
    ivs.append(iv)

# Plot IV smile (example)
import matplotlib.pyplot as plt
plt.plot(strikes, ivs)
plt.xlabel('Strike')
plt.ylabel('Implied Volatility')
plt.title('Volatility Smile')
plt.show()
```

## Related Information

- [Black76 Model API](black76.md) - For commodities and futures options
- [Implied Volatility API](implied_vol.md) - Details on IV calculation
- [Black-Scholes Theoretical Background](../../models/black_scholes.md) - Mathematical Details
