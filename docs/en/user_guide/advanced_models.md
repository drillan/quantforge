---
future_feature: true
---

# Advanced Models

:::{warning}
The features described on this page are currently under development.
Currently, the only available model is the Black-Scholes model.
For implementation timelines, please refer to the project's development plan.
:::

QuantForge plans to introduce advanced option pricing models beyond Black-Scholes in the future.

## American option

### Bjerksund-Stensland 2002 Model

```python
import numpy as np
# API to be implemented in the future
# from quantforge.models import american, black_scholes

# American call option
# american_call = american.call_price(
#     spot=100,
#     strike=95,
#     time=1.0,
#     rate=0.05,
#     sigma=0.25,
#     dividend=0.02  # Dividend yield
# )

# Comparison with European
# european_call = black_scholes.call_price_with_dividend(
#     spot=100,
#     strike=95,
#     time=1.0,
#     rate=0.05,
#     sigma=0.25,
#     dividend=0.02
# )

# early_exercise_premium = american_call - european_call
# print(f"American Call: ${american_call:.2f}")
# print(f"European Call: ${european_call:.2f}")
# print(f"Early Exercise Premium: ${early_exercise_premium:.2f}")
```

### American Put Option

```{code-block} python
:name: advanced-models-code-section
:caption: American put (early exercise is more significant)
:linenos:

# American put (early exercise is more significant)
# To be implemented in the future
# american_put = american.put_price(
#     spot=100,
#     strike=105,
#     time=1.0,
#     rate=0.05,
#     sigma=0.25
# )

# european_put = black_scholes.put_price(
#     spot=100,
#     strike=105,
#     time=1.0,
#     rate=0.05,
#     sigma=0.25
# )

premium = american_put - european_put
print(f"American Put: ${american_put:.2f}")
print(f"European Put: ${european_put:.2f}")
print(f"Early Exercise Premium: ${premium:.2f} ({premium/european_put*100:.1f}%)")
```

### Early Exercise Boundary

```{code-block} python
:name: advanced-models-code-section
:caption: Calculate early exercise boundary
:linenos:

# Calculate early exercise boundary
def early_exercise_boundary(strike, rate, vol, time_points):
    """Early exercise boundary price at each time point"""
    boundaries = []
    for t in time_points:
        if t > 0:
            boundary = qf.american_exercise_boundary(
                strike=strike,
                rate=rate,
                vol=vol,
                time=t,
                option_type="put"
            )
            boundaries.append(boundary)
        else:
            boundaries.append(strike)  # Strike price at maturity
    
    return np.array(boundaries)

# Time grid
times = np.linspace(0, 1, 50)
boundaries = early_exercise_boundary(100, 0.05, 0.25, times)

# Visualization
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 6))
plt.plot(times, boundaries)
plt.axhline(y=100, color='r', linestyle='--', label='Strike')
plt.xlabel('Time to Maturity')
plt.ylabel('Early Exercise Boundary')
plt.title('American Put Early Exercise Boundary')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

## Asian Option

### Arithmetic Average Asian Option

```{code-block} python
:name: advanced-models-code-section
:caption: Arithmetic average price option
:linenos:

# Arithmetic average price option
asian_call = qf.asian_arithmetic_call(
    spot=100,
    strike=100,
    rate=0.05,
    vol=0.2,
    time=1.0,
    averaging_start=0.0,  # Averaging start time
    n_fixings=252  # Number of observations (daily)
)

# Comparison with corresponding European
european = qf.black_scholes_call(100, 100, 0.05, 0.2, 1.0)
print(f"Asian Call: ${asian_call:.2f}")
print(f"European Call: ${european:.2f}")
print(f"Asian Discount: ${european - asian_call:.2f}")
```

### Geometric Asian Option

```{code-block} python
:name: advanced-models-code-section
:caption: Geometric average (has analytical solution)
:linenos:

# Geometric average (has analytical solution)
asian_geometric = qf.asian_geometric_call(
    spot=100,
    strike=100,
    rate=0.05,
    vol=0.2,
    time=1.0
)

print(f"Geometric Asian: ${asian_geometric:.2f}")
```

### Considered Known Prices

```{code-block} python
:name: advanced-models-code-section
:caption: Partially observed Asian option
:linenos:

# Partially observed Asian option
observed_prices = [98, 102, 101, 99, 103]  # Already observed prices
remaining_time = 0.5  # Remaining time

adjusted_asian = qf.asian_call_partial(
    spot=103,  # Current price
    strike=100,
    rate=0.05,
    vol=0.2,
    remaining_time=remaining_time,
    observed_average=np.mean(observed_prices),
    n_observed=len(observed_prices),
    n_total=252  # Total number of observations
)

print(f"Partial Asian Call: ${adjusted_asian:.2f}")
```

## Spread Options

### Spread Options Under the Kirk Approximation

```{code-block} python
:name: advanced-models-code-2
:caption: Spread option between two assets
:linenos:

# Spread option between two assets
spread_call = qf.spread_option_kirk(
    spot1=100,    # Asset 1 current price
    spot2=95,     # Asset 2 current price
    strike=5,     # Spread strike price
    rate=0.05,
    vol1=0.25,    # Asset 1 volatility
    vol2=0.30,    # Asset 2 volatility
    correlation=0.7,  # Correlation coefficient
    time=1.0
)

print(f"Spread Option: ${spread_call:.2f}")
```

### Markov Spread Option

```{code-block} python
:name: advanced-models-code-section
:caption: More accurate Markov model
:linenos:

# More accurate Markov model
spread_markov = qf.spread_option_markov(
    spot1=100,
    spot2=95,
    strike=5,
    rate=0.05,
    vol1=0.25,
    vol2=0.30,
    correlation=0.7,
    time=1.0,
    n_steps=100  # Number of time steps
)

print(f"Markov Spread: ${spread_markov:.2f}")
```

## Barrier Options

### Knock-in/Knock-out Options

```{code-block} python
:name: advanced-models-code-section
:caption: Up-and-out call option
:linenos:

# Up-and-out call option
barrier_call = qf.barrier_call(
    spot=100,
    strike=105,
    barrier=120,  # Barrier level
    rate=0.05,
    vol=0.25,
    time=1.0,
    barrier_type="up_and_out",
    rebate=0  # Rebate (payment when barrier is hit)
)

vanilla_call = qf.black_scholes_call(100, 105, 0.05, 0.25, 1.0)
print(f"Barrier Call: ${barrier_call:.2f}")
print(f"Vanilla Call: ${vanilla_call:.2f}")
print(f"Barrier Discount: ${vanilla_call - barrier_call:.2f}")
```

### Double Barrier Option

```{code-block} python
:name: advanced-models-code-section
:caption: Double barrier (both upper and lower)
:linenos:

# Double barrier (both upper and lower)
double_barrier = qf.double_barrier_call(
    spot=100,
    strike=100,
    lower_barrier=80,
    upper_barrier=120,
    rate=0.05,
    vol=0.25,
    time=1.0
)

print(f"Double Barrier Call: ${double_barrier:.2f}")
```

## Lookback Option

### Fixed Strike Lookback

```{code-block} python
:name: advanced-models-code-section
:caption: Call based on maximum value during the period
:linenos:

# Call based on maximum value during the period
lookback_call = qf.lookback_call_fixed(
    spot=100,
    strike=95,
    rate=0.05,
    vol=0.25,
    time=1.0
)

print(f"Fixed Strike Lookback Call: ${lookback_call:.2f}")
```

### Variable Strike Lookback

```{code-block} python
:name: advanced-models-code-section
:caption: Choose optimal strike price
:linenos:

# Choose optimal strike price
lookback_floating = qf.lookback_call_floating(
    spot=100,
    min_observed=95,  # Minimum value observed so far
    rate=0.05,
    vol=0.25,
    time=1.0
)

print(f"Floating Strike Lookback: ${lookback_floating:.2f}")
```

## Digital (Binary) Options

### Cash-or-nothing

```{code-block} python
:name: advanced-models-code-itm
:caption: Digital call (pays fixed amount if ITM at maturity)
:linenos:

# Digital call (pays fixed amount if ITM at maturity)
digital_call = qf.digital_call(
    spot=100,
    strike=105,
    rate=0.05,
    vol=0.25,
    time=1.0,
    cash_amount=10  # Payout amount
)

# Probability calculation
prob_itm = qf.probability_itm(
    spot=100,
    strike=105,
    rate=0.05,
    vol=0.25,
    time=1.0,
    option_type="call"
)

print(f"Digital Call Value: ${digital_call:.2f}")
print(f"Probability of ITM: {prob_itm:.1%}")
```

### Asset or Nothing

```{code-block} python
:name: advanced-models-code-section
:caption: Asset-or-nothing digital option
:linenos:

# Asset-or-nothing digital option
asset_or_nothing = qf.asset_or_nothing_call(
    spot=100,
    strike=105,
    rate=0.05,
    vol=0.25,
    time=1.0
)

print(f"Asset-or-Nothing Call: ${asset_or_nothing:.2f}")
```

## Combination Option Strategies

### straddling

```{code-block} python
:name: advanced-models-code-straddle_value
:caption: straddle_value
:linenos:

def straddle_value(spot, strike, rate, vol, time):
    """Straddle (call + put at same strike)"""
    call = qf.black_scholes_call(spot, strike, rate, vol, time)
    put = qf.black_scholes_put(spot, strike, rate, vol, time)
    return call + put

# Straddle payoff
spots = np.linspace(80, 120, 100)
straddle_values = [straddle_value(s, 100, 0.05, 0.25, 0.25) for s in spots]

plt.figure(figsize=(10, 6))
plt.plot(spots, straddle_values, label='Straddle Value')
plt.axvline(x=100, color='r', linestyle='--', alpha=0.5, label='Strike')
plt.xlabel('Spot Price')
plt.ylabel('Strategy Value')
plt.title('Straddle Payoff')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

### Butterfly Spread

```{code-block} python
:name: advanced-models-code-butterfly_spread
:caption: butterfly_spread
:linenos:

def butterfly_spread(spot, k1, k2, k3, rate, vol, time):
    """Butterfly spread"""
    c1 = qf.black_scholes_call(spot, k1, rate, vol, time)
    c2 = qf.black_scholes_call(spot, k2, rate, vol, time)
    c3 = qf.black_scholes_call(spot, k3, rate, vol, time)
    return c1 - 2*c2 + c3

# Butterfly value
spots = np.linspace(85, 115, 100)
butterfly = [butterfly_spread(s, 95, 100, 105, 0.05, 0.25, 0.25) for s in spots]

plt.figure(figsize=(10, 6))
plt.plot(spots, butterfly)
plt.axvline(x=95, color='r', linestyle='--', alpha=0.3)
plt.axvline(x=100, color='r', linestyle='--', alpha=0.3)
plt.axvline(x=105, color='r', linestyle='--', alpha=0.3)
plt.xlabel('Spot Price')
plt.ylabel('Butterfly Value')
plt.title('Butterfly Spread')
plt.grid(True, alpha=0.3)
plt.show()
```

## Model Comparison

### Performance Comparison of Each Model

```{code-block} python
:name: advanced-models-code-section
:caption: Comparison of calculation time for different models
:linenos:

# Comparison of calculation time for different models
import time

n = 100000
spots = np.random.uniform(90, 110, n)

models = {
    'Black-Scholes': lambda s: qf.black_scholes_call(s, 100, 0.05, 0.2, 1.0),
    'American': lambda s: qf.american_call(s, 100, 0.05, 0.2, 1.0),
    'Asian': lambda s: qf.asian_arithmetic_call(s, 100, 0.05, 0.2, 1.0),
    'Barrier': lambda s: qf.barrier_call(s, 100, 120, 0.05, 0.2, 1.0, "up_and_out"),
}

for name, func in models.items():
    start = time.perf_counter()
    prices = [func(s) for s in spots[:1000]]  # Sample calculation
    elapsed = time.perf_counter() - start
    print(f"{name:15s}: {elapsed*1000:.2f}ms for 1000 options")
```

## Summary

Advanced models enable:

- **American Options**: Valuation of Early Exercise Rights
- **Asian Options**: Path-dependent options
- **Spread Options**: Relative value of multiple assets
- **Barrier Option**: Conditional Payoff
- **Composite Strategies**: Evaluating strategies used in practice

Next, let's examine [practical examples](examples.md) to see real-world use cases.
