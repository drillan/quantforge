---
future_feature: true
---

# Asian Options Model

:::{warning}
The features described on this page are currently under development.
Please check the [Model List](index.md) for currently available models.
Please refer to the project development plan for the expected implementation timeline.
:::

A pricing model for path-dependent options based on average prices.

## Theoretical Background

### Basic Concepts

Asian options are exotic options where the payoff is determined based on the average price of the underlying asset over the period until maturity.
By using average prices instead of single point-in-time prices, they reduce the risk of price manipulation and lower volatility.

They are primarily used in commodity markets, foreign exchange markets, and energy markets, with designs that fit corporate hedging needs.

### Basic Assumptions

1. **Log-normal distribution**: Underlying asset prices follow geometric Brownian motion
   $$dS_t = \mu S_t dt + \sigma S_t dW_t$$

2. **Efficient market**: No transaction costs or taxes, unlimited borrowing and lending

3. **Constant parameters**: Volatility and interest rate are constant

4. **Observation frequency**: Discrete (daily, weekly, etc.) or continuous

5. **Average type**: Arithmetic average or geometric average

## Derivation of Pricing Formula

### Arithmetic Average Asian Options

Arithmetic average price:
$$A_T = \frac{1}{n}\sum_{i=1}^{n} S_{t_i}$$

Partial differential equation (2-dimensional):
$$\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V}{\partial S^2} + rS\frac{\partial V}{\partial S} + \frac{S}{n}\frac{\partial V}{\partial A} - rV = 0$$

### Boundary Conditions

Call option:
- $V(S, A, T) = \max(A - K, 0)$ (average price type)
- $V(S, A, T) = \max(S - K, 0)$ (average strike type)

Put option:
- $V(S, A, T) = \max(K - A, 0)$ (average price type)
- $V(S, A, T) = \max(K - S, 0)$ (average strike type)

## Analytical Solutions

### Geometric Average Asian Call

Closed-form solution exists for geometric average:

$$C_{geo} = S_0 e^{(r-q-\sigma_A^2/2)T} N(d_1) - K e^{-rT} N(d_2)$$

where:
- $\sigma_A = \sigma / \sqrt{3}$ (for continuous observation)
- $d_1 = \frac{\ln(S_0/K) + (r - q + \sigma_A^2/2)T}{\sigma_A\sqrt{T}}$
- $d_2 = d_1 - \sigma_A\sqrt{T}$

### Arithmetic Average Approximation (Turnbull-Wakeman)

Approximation for arithmetic average:

$$C_{arith} \approx C_{BS}(S_0, K, T, r, \sigma_{adj})$$

Adjusted volatility:
$$\sigma_{adj} = \sqrt{\frac{\ln(M_2) - 2\ln(M_1)}{T}}$$

where $M_1, M_2$ are first and second moments

## Greeks

Greeks for Asian options:

| Greek | Meaning | Characteristics |
|-------|---------|----------------|
| Delta | Stock price sensitivity $\partial V/\partial S$ | Smaller than vanilla |
| Gamma | Rate of change of delta $\partial^2 V/\partial S^2$ | Complex near maturity |
| Vega | Volatility sensitivity $\partial V/\partial \sigma$ | About 1/√3 of vanilla |
| Theta | Time decay $-\partial V/\partial T$ | Changes with observation period |
| Rho | Interest rate sensitivity $\partial V/\partial r$ | Similar to vanilla |

## Relationship with Black-Scholes

### Volatility Reduction Effect

Volatility decreases due to averaging:
- Continuous observation: $\sigma_{asian} = \sigma / \sqrt{3}$
- Discrete observation: $\sigma_{asian} = \sigma \sqrt{\frac{n+1}{3n}}$

### Price Relationship

Asian price < Vanilla price (typically):
$$C_{Asian} < C_{Black-Scholes}$$

### Convergence at Limit

With one observation, matches vanilla option:
$$\lim_{n \to 1} C_{Asian}^{(n)} = C_{Black-Scholes}$$

## Applications

### Commodity Markets
Used for monthly average oil price options and seasonal average price options for agricultural products.
In metal markets, utilized for quarterly average price hedging, reducing price manipulation risks.
Settlement based on average prices significantly reduces single point-in-time price volatility risk.

### Foreign Exchange Markets
Suitable for hedging continuous FX exposure of corporations.
Monthly average rate options are popular among companies with regular overseas remittances.
Used in the tourism industry for managing seasonal FX volatility risks.

### Energy Markets
Daily average electricity price options are essential for power company risk management.
Monthly average natural gas swaps function as hedges against seasonal demand fluctuations.
Also contribute to long-term revenue stabilization for renewable energy operators.

### Equity Markets
Employee stock ownership plans reduce participant risk through average acquisition price guarantees.
Used for index fund period average return guarantees and pension fund average price protection.
Also applicable to investment strategy implementation combined with dollar-cost averaging.

## Numerical Computation Considerations

### Precision Requirements
- Price precision: Relative error < $10^{-6}$
- Greeks precision: Relative error < $10^{-5}$
- Geometric/arithmetic approximation error: < 1%

### Numerical Challenges and Countermeasures

1. **Curse of dimensionality**
   - Countermeasure: PDE dimension reduction techniques
   - One-dimensionalization through variable transformation

2. **Complexity of arithmetic average**
   - Countermeasure: Moment matching method
   - Turnbull-Wakeman approximation

3. **Handling partial observations**
   - Countermeasure: Use conditional expectations
   - Incorporation of observed averages

## Model Limitations and Extensions

### Limitations
- **No analytical solution for arithmetic average**: Depends on approximation methods
- **Path dependency**: High computational burden
- **Discrete observation**: Continuous approximation errors
- **Early exercise**: American-style is very complex

### Extended Models
- **Stochastic volatility**: Asian Heston model
- **Jump diffusion**: Asian Merton model
- **Multi-asset**: Basket Asian options
- **Double Asian**: Using two average prices

## Implementation Example (Conceptual)

```python
# Conceptual implementation example (different from actual API)
# Future planned API

import numpy as np
from scipy.stats import norm

def geometric_asian_call_price(s, k, t, r, sigma, n_fixings):
    """
    Geometric average Asian call option price (exact solution)
    
    Parameters:
        s: Spot price
        k: Strike price
        t: Time to maturity
        r: Risk-free interest rate
        sigma: Volatility
        n_fixings: Number of observations
    
    Returns:
        Geometric average Asian call price
    """
    # Adjustment parameters
    sigma_a = sigma * np.sqrt((n_fixings + 1) / (3 * n_fixings))
    mu_a = (r - 0.5 * sigma**2) * (n_fixings + 1) / (2 * n_fixings)
    
    # Calculate d1, d2
    d1 = (np.log(s / k) + (mu_a + 0.5 * sigma_a**2) * t) / (sigma_a * np.sqrt(t))
    d2 = d1 - sigma_a * np.sqrt(t)
    
    # Geometric average Asian price
    price = s * np.exp((mu_a - r) * t) * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)
    
    return price


def arithmetic_asian_call_approximation(s, k, t, r, sigma, n_fixings):
    """
    Arithmetic average Asian call approximation price (Turnbull-Wakeman)
    
    Parameters:
        s: Spot price
        k: Strike price
        t: Time to maturity
        r: Risk-free interest rate
        sigma: Volatility
        n_fixings: Number of observations
    
    Returns:
        Arithmetic average Asian call approximation price
    """
    # Moment calculation
    dt = t / n_fixings
    
    # First moment (expected value)
    m1 = s * np.exp(r * t) * (1 - np.exp(-r * t * n_fixings / n_fixings)) / (n_fixings * r * dt)
    
    # Second moment
    sigma2_adj = sigma**2 * (2 * n_fixings + 1) / (6 * n_fixings)
    m2 = m1**2 * np.exp(sigma2_adj * t)
    
    # Adjusted volatility
    sigma_adj = np.sqrt(np.log(m2 / m1**2) / t)
    
    # Black-Scholes approximation
    d1 = (np.log(m1 / k) + 0.5 * sigma_adj**2 * t) / (sigma_adj * np.sqrt(t))
    d2 = d1 - sigma_adj * np.sqrt(t)
    
    price = np.exp(-r * t) * (m1 * norm.cdf(d1) - k * norm.cdf(d2))
    
    return price
```

## References

1. Kemna, A.G.Z. and Vorst, A.C.F. (1990). "A Pricing Method for Options Based on Average Asset Values." *Journal of Banking and Finance*, 14(1), 113-129.

2. Turnbull, S.M. and Wakeman, L.M. (1991). "A Quick Algorithm for Pricing European Average Options." *Journal of Financial and Quantitative Analysis*, 26(3), 377-389.

3. Hull, J.C. and White, A. (1993). "Efficient Procedures for Valuing European and American Path-Dependent Options." *Journal of Derivatives*, 1(1), 21-31.

4. Vecer, J. (2001). "A New PDE Approach for Pricing Arithmetic Average Asian Options." *Journal of Computational Finance*, 4(4), 105-113.

## Related Documents

- Asian Options API (under development)
- [Black-Scholes Model](black_scholes.md)
- [Merton Model](merton.md)
- Monte Carlo Methods (under development)
- Exotic Options List (under development)