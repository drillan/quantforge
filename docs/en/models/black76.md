(black76)=
# Black76 Model

The standard model for pricing theory of commodity futures, interest rate derivatives, and foreign exchange options.

(black76-theory)=
## Theoretical Background

(black76-basic-concepts)=
### Basic Concepts

The Black76 model was proposed by Fischer Black (1976) as a futures option pricing model.
It is an extension of the Black-Scholes model based on forward prices, with the following characteristics:

1. **Use of forward prices**: Uses forward prices instead of spot prices
2. **Implicit treatment of storage costs**: Forward prices reflect storage costs and convenience yields
3. **Role of interest rates**: Used only for discounting (does not appear in drift term)

(black76-assumptions)=
### Basic Assumptions

1. **Log-normal distribution**: Forward prices follow geometric Brownian motion
   
   ```{math}
   :name: black76-eq-gbm
   
   dF_t = \sigma F_t dW_t
   ```
   
   (Note the absence of drift term)

2. **Efficient market**: No transaction costs or taxes, unlimited borrowing and lending

3. **Constant parameters**: Volatility and interest rate are constant

4. **Martingale property of forward prices**: Forward prices are martingales under the risk-neutral measure

(black76-derivation)=
## Derivation of Pricing Formula

(black76-pde)=
### Black76 Equation

The option value $V(F,t)$ for forward price $F$ satisfies the following partial differential equation:

```{math}
:name: black76-eq-pde

\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 F^2 \frac{\partial^2 V}{\partial F^2} - rV = 0
```

(black76-boundary-conditions)=
### Boundary Conditions

Call option:
- $V(F, T) = \max(F - K, 0)$
- $V(0, t) = 0$
- $V(F, t) \to e^{-r(T-t)}(F - K)$ as $F \to \infty$

Put option:
- $V(F, T) = \max(K - F, 0)$
- $V(0, t) = Ke^{-r(T-t)}$
- $V(F, t) \to 0$ as $F \to \infty$

(black76-solutions)=
## Analytical Solutions

(black76-call-formula)=
### European Call

```{math}
:name: black76-eq-call-formula

C = e^{-rT}[F N(d_1) - K N(d_2)]
```

where:

```{math}
:name: black76-eq-d1-d2

d_1 = \frac{\ln(F/K) + \sigma^2 T/2}{\sigma\sqrt{T}}, \quad d_2 = d_1 - \sigma\sqrt{T}
```
- $N(x)$: Cumulative distribution function of standard normal distribution

(black76-put-formula)=
### European Put

```{math}
:name: black76-eq-put-formula

P = e^{-rT}[K N(-d_2) - F N(-d_1)]
```

(black76-greeks)=
## Greeks

Option price sensitivity measures:

```{list-table} Greeks Definition
:name: black76-table-greeks
:header-rows: 1
:widths: 15 35 25 25

* - Greek
  - Meaning
  - Call
  - Put
* - Delta
  - Forward price sensitivity $\partial V/\partial F$
  - $e^{-rT} N(d_1)$
  - $-e^{-rT} N(-d_1)$
* - Gamma
  - Rate of change of delta $\partial^2 V/\partial F^2$
  - $\frac{e^{-rT} \phi(d_1)}{F \sigma \sqrt{T}}$
  - Same
* - Vega
  - Volatility sensitivity $\partial V/\partial \sigma$
  - $e^{-rT} F \phi(d_1) \sqrt{T}$
  - Same
* - Theta
  - Time decay $-\partial V/\partial T$
  - See below
  - See below
* - Rho
  - Interest rate sensitivity $\partial V/\partial r$
  - $-T \cdot C$
  - $-T \cdot P$
```

where $\phi(x) = \frac{1}{\sqrt{2\pi}}e^{-x^2/2}$ is the standard normal probability density function

(black76-theta-details)=
### Theta Details

Time decay (per day):

Call:

```{math}
:name: black76-eq-theta-call

\Theta_C = -e^{-rT} \left[ \frac{F \phi(d_1) \sigma}{2\sqrt{T}} + rK N(d_2) - rF N(d_1) \right] / 365
```

Put:

```{math}
:name: black76-eq-theta-put

\Theta_P = -e^{-rT} \left[ \frac{F \phi(d_1) \sigma}{2\sqrt{T}} - rK N(-d_2) + rF N(-d_1) \right] / 365
```

(black76-black-scholes-relationship)=
## Relationship with Black-Scholes

(black76-mathematical-equivalence)=
### Mathematical Equivalence

The Black76 model is mathematically equivalent to the Black-Scholes model when the dividend yield $q = r$:

```{math}
:name: black76-eq-forward-price

F = S e^{(r-q)T}
```

When $q = r$: $F = S$ (Forward price = Spot price)

(black76-practical-differences)=
### Practical Differences

```{list-table} Model Comparison
:name: black76-table-comparison
:header-rows: 1
:widths: 30 35 35

* - Feature
  - Black-Scholes
  - Black76
* - Input price
  - Spot $S$
  - Forward $F$
* - Drift
  - $(r - q)$
  - 0 (Martingale)
* - Storage cost
  - Explicit ($q$)
  - Implicit (included in $F$)
* - Main use
  - Equities
  - Commodities, rates
```

(black76-applications)=
## Applications

(black76-commodity-markets)=
### Commodity Markets
Widely used for pricing energy options (crude oil WTI/Brent, natural gas, electricity).
Uses forward price $F = S e^{(r + u - y)T}$ considering storage cost rate $u$ and convenience yield $y$.
For agricultural products (grains, soft commodities), seasonality considerations are important.

(black76-interest-rate-derivatives)=
### Interest Rate Derivatives
Used for pricing individual caplets/floorlets in caps and floors.
For swaptions, forward swap rates are treated as underlying assets and adjusted by annuity factors.
An important pricing theory that forms the foundation of the LIBOR Market Model.

(black76-fx-options)=
### Foreign Exchange Options
Pricing is performed by treating foreign currency as a commodity and interest rate differentials as storage costs.
Using forward exchange rates provides prices consistent with covered interest rate parity.
A standard pricing model for corporate FX hedging and currency option trading.

(black76-numerical)=
## Numerical Computation Considerations

(black76-precision)=
### Precision Requirements

```{list-table} Precision Requirements
:name: black76-table-precision
:header-rows: 1
:widths: 30 30 40

* - Domain
  - Precision Target
  - Implementation Notes
* - Near ATM
  - Relative error < 1e-8
  - Standard implementation sufficient
* - Deep ITM/OTM
  - Absolute error < 1e-10
  - Logarithmic scale calculation recommended
* - Short maturity
  - Relative error < 1e-6
  - Pay attention to $\sqrt{T}$ precision
```

(black76-numerical-challenges)=
### Numerical Challenges and Countermeasures

1. **$d_1, d_2$ calculation**
   - Minimum value limit to avoid divergence as $T \to 0$
   - Ensure precision of $\ln(F/K)$

2. **Normal distribution function $N(x)$**
   - Use approximation for $|x| > 8$ ($N(8) \approx 1$)
   - High precision calculation using Erfcx function

3. **Very small volatility**
   - Special treatment for $\sigma < 0.001$
   - Ensure convergence to intrinsic value

(black76-limitations)=
## Model Limitations and Extensions

(black76-model-limitations)=
### Limitations

1. **Volatility smile**: Limitation of constant volatility assumption
2. **Early exercise**: Does not handle American options
3. **Jump risk**: Assumption of continuous price movements

(black76-extended-models)=
### Extended Models

1. **SABR Model**: Consideration of volatility smile
2. **Stochastic volatility models**: Heston, SVI models
3. **Jump diffusion models**: Merton, Kou models

(black76-implementation)=
## Implementation Example (Conceptual)

```{code-block} python
:name: black76-code-implementation
:caption: Black76 model implementation
:linenos:

import numpy as np
from scipy.stats import norm

def black76_call(F, K, T, r, sigma):
    """Black76 call option price"""
    d1 = (np.log(F/K) + 0.5*sigma**2*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    
    call_price = np.exp(-r*T) * (F*norm.cdf(d1) - K*norm.cdf(d2))
    return call_price

def black76_put(F, K, T, r, sigma):
    """Black76 put option price"""
    d1 = (np.log(F/K) + 0.5*sigma**2*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    
    put_price = np.exp(-r*T) * (K*norm.cdf(-d2) - F*norm.cdf(-d1))
    return put_price
```

(black76-references)=
## References

1. Black, F. (1976). "The pricing of commodity contracts", *Journal of Financial Economics*, 3(1-2), 167-179.

2. Hull, J. C. (2018). *Options, Futures, and Other Derivatives* (10th ed.). Pearson.

3. Haug, E. G. (2007). *The Complete Guide to Option Pricing Formulas* (2nd ed.). McGraw-Hill.

4. Shreve, S. E. (2004). *Stochastic Calculus for Finance II: Continuous-Time Models*. Springer.

5. Musiela, M., & Rutkowski, M. (2005). *Martingale Methods in Financial Modelling*. Springer.

(black76-related)=
## Related Documents

- [Black76 Model API](../api/python/black76.md) - Python API usage
- [Black-Scholes Model](black_scholes.md) - Equity option model
- [Pricing API Overview](../api/python/pricing.md) - Integrated API interface