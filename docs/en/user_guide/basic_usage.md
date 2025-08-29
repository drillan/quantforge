# Basic Usage

Learn about QuantForge's basic functions and option pricing using the Black-Scholes model.

## Import

```python
from quantforge.models import black_scholes
```

## Black-Scholes Model

### Basic Price Calculation

```python
from quantforge.models import black_scholes

# Call option price
call_price = black_scholes.call_price(
    s=100.0,      # Spot price
    k=110.0,      # Strike price
    t=1.0,        # Time to maturity (years)
    r=0.05,       # Risk-free rate (annual)
    sigma=0.2     # Volatility (annual)
)

# Put option price
put_price = black_scholes.put_price(
    s=100.0,
    k=110.0,
    t=1.0,
    r=0.05,
    sigma=0.2
)

print(f"Call Option Price: ${call_price:.2f}")
print(f"Put Option Price: ${put_price:.2f}")

# Put-Call parity verification
import numpy as np
parity = call_price - put_price
theoretical = 100.0 - 110.0 * np.exp(-0.05 * 1.0)
print(f"Put-Call Parity Check: {abs(parity - theoretical) < 1e-10}")
```


## Greek Calculations

### Bulk Calculations for All Greeks

```python
from quantforge.models import black_scholes

# Calculate all Greeks at once (efficient)
greeks = black_scholes.greeks(
    s=100.0,
    k=100.0,
    t=1.0,
    r=0.05,
    sigma=0.2,
    is_call=True
)

print("Call Option Greeks:")
print(f"  Delta: {greeks.delta:.4f}")
print(f"  Gamma: {greeks.gamma:.4f}")
print(f"  Vega:  {greeks.vega:.4f}")
print(f"  Theta: {greeks.theta:.4f}")
print(f"  Rho:   {greeks.rho:.4f}")
```


## Simultaneous Calculation of Multiple Options

### Batch Processing (NumPy Arrays)

```python
import numpy as np
from quantforge.models import black_scholes

# Multiple spot prices
spots = np.array([95, 100, 105, 110])

# Batch calculation (fast)
call_prices = black_scholes.call_price_batch(
    spots=spots,
    k=100.0,
    t=1.0,
    r=0.05,
    sigma=0.2
)

put_prices = black_scholes.put_price_batch(
    spots=spots,
    k=100.0,
    t=1.0,
    r=0.05,
    sigma=0.2
)

for i, (spot, call, put) in enumerate(zip(spots, call_prices, put_prices)):
    print(f"Spot {spot}: Call=${call:.2f}, Put=${put:.2f}")
```

### Multiple Parameter Sets

```{code-block} python
:name: basic-usage-code-section
:caption: Options with different maturities
:linenos:

# Options with different maturities
times = [0.25, 0.5, 1.0, 2.0]
for time_val in times:
    price = black_scholes.call_price(
        s=100.0,
        k=100.0,
        t=time_val,
        r=0.05,
        sigma=0.2
    )
    print(f"Maturity {time_val} years: ${price:.2f}")
```

## implied volatility

### Single IV Calculation

```python
from quantforge.models import black_scholes

# Back out volatility from market price
market_price = 10.45
iv = black_scholes.implied_volatility(
    price=market_price,
    s=100.0,
    k=100.0,
    t=1.0,
    r=0.05,
    is_call=True
)

print(f"Implied Volatility: {iv:.1%}")

# Accuracy verification
calculated_price = black_scholes.call_price(s=100, k=100, t=1.0, r=0.05, sigma=iv)
print(f"Price Check: Market={market_price:.2f}, Calculated={calculated_price:.2f}")
```

### IV Smile Analysis

```python
import numpy as np
from quantforge.models import black_scholes

# Different strike prices
spot = 100.0
strikes = np.array([80, 90, 100, 110, 120])
sigma_true = 0.2

# Calculate theoretical price for each strike
market_prices = []
for strike in strikes:
    price = black_scholes.call_price(s=spot, k=strike, t=1.0, r=0.05, sigma=sigma_true)
    market_prices.append(price)

# Back out implied volatility
for strike, price in zip(strikes, market_prices):
    iv = black_scholes.implied_volatility(
        price=price, s=spot, k=strike, t=1.0, r=0.05, is_call=True
    )
    print(f"Strike {strike}: IV={iv:.1%}")
```

## Application in Risk Management

### Delta Hedging

```python
from quantforge.models import black_scholes

# Position information
spot = 100.0
strike = 105.0
time = 0.5
rate = 0.05
sigma = 0.25

# Calculate option delta
greeks = black_scholes.greeks(s=spot, k=strike, t=time, r=rate, sigma=sigma, is_call=True)
delta = greeks.delta

# Number of shares needed for delta hedge
option_contracts = 100  # 100 contracts
hedge_shares = -option_contracts * delta * 100  # Each contract represents 100 shares

print(f"Delta: {delta:.4f}")
print(f"Hedge position: {hedge_shares:.0f} shares")
```

### Portfolio Greeks

```{code-block} python
:name: basic-usage-code-section
:caption: Portfolio of multiple options
:linenos:

# Portfolio of multiple options
positions = [
    {"spot": 100, "strike": 95, "time": 0.5, "contracts": 10, "is_call": True},
    {"spot": 100, "strike": 105, "time": 0.5, "contracts": -5, "is_call": False},
    {"spot": 100, "strike": 100, "time": 1.0, "contracts": 8, "is_call": True},
]

# Portfolio-wide Greeks
total_delta = 0
total_gamma = 0
total_vega = 0

for pos in positions:
    greeks = black_scholes.greeks(
        s=pos["spot"], k=pos["strike"], t=pos["time"], 
        r=0.05, sigma=0.2, is_call=pos["is_call"]
    )
    total_delta += pos["contracts"] * greeks.delta * 100
    total_gamma += pos["contracts"] * greeks.gamma * 100
    total_vega += pos["contracts"] * greeks.vega * 100

print(f"Portfolio Greeks:")
print(f"  Total Delta: {total_delta:.2f}")
print(f"  Total Gamma: {total_gamma:.2f}")
print(f"  Total Vega:  {total_vega:.2f}")
```

## Performance Measurement

```python
import time
import numpy as np
from quantforge.models import black_scholes

# Large-scale batch processing benchmark
n = 1_000_000
spots = np.random.uniform(90, 110, n)

start = time.perf_counter()
prices = black_scholes.call_price_batch(spots=spots, k=100, t=1.0, r=0.05, sigma=0.2)
elapsed = (time.perf_counter() - start) * 1000

print(f"Processed {n:,} options in {elapsed:.1f}ms")
print(f"Average time per option: {elapsed/n*1000:.1f}ns")
# Expected results (AMD Ryzen 5 5600G): ~55.6ms, 56ns/option
```

For detailed measurement results and machine-specific performance, see the performance section.
