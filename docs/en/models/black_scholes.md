(black-scholes)=
# Black-Scholes Model

The standard model that forms the foundation of option pricing theory.

(black-scholes-theory)=
## Theoretical Background

(black-scholes-basic-concepts)=
### Basic Concepts

The Black-Scholes model is an option pricing model published by Fischer Black and Myron Scholes in 1973.
Robert Merton also independently developed a similar model during the same period, and Scholes and Merton received the Nobel Prize in Economics in 1997.

This model uses risk-neutral valuation and no-arbitrage pricing theory to analytically derive the theoretical price of European options.

(black-scholes-assumptions)=
### Basic Assumptions

1. **Log-normal distribution**: Stock prices follow geometric Brownian motion
   
   ```{math}
   :name: black-scholes-eq-gbm
   
   dS_t = \mu S_t dt + \sigma S_t dW_t
   ```

2. **Efficient market**: No transaction costs or taxes, unlimited borrowing and lending

3. **Constant parameters**: Volatility and interest rate are constant

4. **No arbitrage**: No arbitrage opportunities exist in the market

5. **European style**: Exercise only at expiration

(black-scholes-derivation)=
## Derivation of Pricing Formula

(black-scholes-pde)=
### Black-Scholes Equation

Partial differential equation under the risk-neutral measure:

```{math}
:name: black-scholes-eq-pde

\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V}{\partial S^2} + rS\frac{\partial V}{\partial S} - rV = 0
```

(black-scholes-boundary-conditions)=
### Boundary Conditions

Call option:
- $V(S, T) = \max(S - K, 0)$
- $V(0, t) = 0$
- $V(S, t) \to S - Ke^{-r(T-t)}$ as $S \to \infty$

Put option:
- $V(S, T) = \max(K - S, 0)$
- $V(0, t) = Ke^{-r(T-t)}$
- $V(S, t) \to 0$ as $S \to \infty$

(black-scholes-solutions)=
## Analytical Solutions

(black-scholes-call-formula)=
### European Call

```{math}
:name: black-scholes-eq-call-formula

C = S_0 N(d_1) - Ke^{-rT} N(d_2)
```

where:

```{math}
:name: black-scholes-eq-d1-d2

d_1 = \frac{\ln(S_0/K) + (r + \sigma^2/2)T}{\sigma\sqrt{T}}, \quad d_2 = d_1 - \sigma\sqrt{T}
```
- $N(x)$: Cumulative distribution function of standard normal distribution

(black-scholes-put-formula)=
### European Put

```{math}
:name: black-scholes-eq-put-formula

P = Ke^{-rT} N(-d_2) - S_0 N(-d_1)
```

Put-Call parity:

```{math}
:name: black-scholes-eq-put-call-parity

C - P = S_0 - Ke^{-rT}
```

(black-scholes-greeks)=
## Greeks

Option price sensitivity measures:

```{list-table} Greeks Definition
:name: black-scholes-table-greeks
:header-rows: 1
:widths: 15 35 25 25

* - Greek
  - Meaning
  - Call
  - Put
* - Delta
  - Stock price sensitivity $\partial V/\partial S$
  - $N(d_1)$
  - $-N(-d_1)$
* - Gamma
  - Rate of change of delta $\partial^2 V/\partial S^2$
  - $\frac{\phi(d_1)}{S_0 \sigma \sqrt{T}}$
  - Same
* - Vega
  - Volatility sensitivity $\partial V/\partial \sigma$
  - $S_0 \phi(d_1) \sqrt{T}$
  - Same
* - Theta
  - Time decay $-\partial V/\partial T$
  - $-\frac{S_0 \phi(d_1) \sigma}{2\sqrt{T}} - rKe^{-rT}N(d_2)$
  - $-\frac{S_0 \phi(d_1) \sigma}{2\sqrt{T}} + rKe^{-rT}N(-d_2)$
* - Rho
  - Interest rate sensitivity $\partial V/\partial r$
  - $KTe^{-rT}N(d_2)$
  - $-KTe^{-rT}N(-d_2)$
```

where $\phi(x) = \frac{1}{\sqrt{2\pi}}e^{-x^2/2}$ is the standard normal probability density function

(black-scholes-merton-relationship)=
## Relationship with Merton Model

(black-scholes-continuous-dividends)=
### Extension to Continuous Dividends

Merton model considering dividend yield $q$:

```{math}
:name: black-scholes-eq-merton-call

C = S_0 e^{-qT} N(d_1) - Ke^{-rT} N(d_2)
```

where:

```{math}
:name: black-scholes-eq-merton-d1

d_1 = \frac{\ln(S_0/K) + (r - q + \sigma^2/2)T}{\sigma\sqrt{T}}
```
- When $q = 0$, reduces to the standard Black-Scholes model

(black-scholes-discrete-dividends)=
### Treatment of Discrete Dividends

Considering dividends $D_i$ on ex-dividend dates $t_i$:

```{math}
:name: black-scholes-eq-discrete-div

S_{\text{ex-div}} = S_0 - \sum_{t_i < T} D_i e^{-rt_i}
```

(black-scholes-applications)=
## Applications

(black-scholes-stock-options)=
### Stock Options
This model forms the foundation for pricing individual stock options and risk management.
It is also used for valuing employee stock options (ESO) and warrant pricing.
Extension to the Merton model is necessary when adjustments for ex-dividend dates are required.

(black-scholes-index-options)=
### Stock Index Options
Used for pricing major stock index options such as S&P 500, Nikkei 225, and FTSE 100.
Widely applied to ETF option valuation and utilized by institutional investors for portfolio hedging.
The Merton extension is commonly used in practice as it considers the continuous dividend yield of indices.

(black-scholes-fx-options)=
### Foreign Exchange Options
The Garman-Kohlhagen extension enables pricing of foreign exchange options.
It considers both domestic and foreign interest rates, treating foreign rates as dividend yields.
Used for corporate FX risk hedging and speculative FX trading valuations.

(black-scholes-derivatives-general)=
### Derivatives Pricing in General
This theory serves as the foundation for more complex models (stochastic volatility, jump diffusion, etc.).
Essential for understanding volatility surface calibration and risk-neutral valuation concepts.
Functions as the core of risk management systems in financial institutions and as a benchmark model for VaR and stress testing.

(black-scholes-numerical)=
## Numerical Computation Considerations

(black-scholes-precision)=
### Precision Requirements
- Price precision: Relative error < $10^{-8}$
- Greeks precision: Relative error < $10^{-7}$
- Put-Call parity: Error < $10^{-12}$

(black-scholes-numerical-challenges)=
### Numerical Challenges and Countermeasures

1. **Instability at extreme values**
   - Near expiration ($T \to 0$): Return boundary values directly
   - Zero volatility ($\sigma \to 0$): Deterministic payoff
   - Deep ITM/OTM: Use asymptotic expansion

2. **High precision calculation of cumulative normal distribution**
   - Use Hart68 algorithm or AS241
   - Error < $10^{-15}$ (double precision arithmetic)

3. **Parallel processing**
   - Parallel computation using Rayon
   - Improved processing speed in batch processing

(black-scholes-limitations)=
## Model Limitations and Extensions

(black-scholes-model-limitations)=
### Limitations

:::{important}
The Black-Scholes model has the following limitations:
:::

- **Volatility smile**: Cannot explain phenomena observed in real markets
- **Early exercise**: Not applicable to American options
- **Jump risk**: Does not consider discontinuous price movements
- **Transaction costs**: Does not consider market frictions

(black-scholes-extended-models)=
### Extended Models
- **Stochastic volatility**: Heston, SABR models
- **Jump diffusion**: Merton Jump Diffusion
- **Local volatility**: Dupire model
- **American options**: Binomial tree, finite difference methods

(black-scholes-implementation)=
## Implementation Example (Conceptual)

:::{note}
The following is a conceptual implementation example (not available in the current API)
:::

```{code-block} python
:name: black-scholes-code-call-price
:caption: Black-Scholes call price calculation
:linenos:

import numpy as np
from scipy.stats import norm

def black_scholes_call_price(s, k, t, r, sigma):
    """
    Call option price using Black-Scholes model
    
    Parameters:
        s: Spot price
        k: Strike price
        t: Time to maturity
        r: Risk-free interest rate
        sigma: Volatility
    
    Returns:
        Call option price
    """
    # Numerical stability check
    if t < 1e-10:
        return max(s - k, 0.0)
    
    if sigma < 1e-10:
        forward = s * np.exp(r * t)
        return max((forward - k) * np.exp(-r * t), 0.0)
    
    # Calculate d1, d2
    d1 = (np.log(s / k) + (r + 0.5 * sigma**2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)
    
    # Black-Scholes pricing formula
    call_price = s * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)
    
    return call_price
```

(black-scholes-references)=
## References

1. Black, F. and Scholes, M. (1973). "The Pricing of Options and Corporate Liabilities." *Journal of Political Economy*, 81(3), 637-654.

2. Merton, R.C. (1973). "Theory of Rational Option Pricing." *Bell Journal of Economics and Management Science*, 4(1), 141-183.

3. Hull, J.C. (2018). *Options, Futures, and Other Derivatives* (10th ed.). Pearson.

4. Wilmott, P. (2006). *Paul Wilmott on Quantitative Finance* (2nd ed.). Wiley.

(black-scholes-related)=
## Related Documents

- [Black-Scholes API](../api/python/black_scholes.md)
- [Merton Model](merton.md)
- [Black76 Model](black76.md)
- [Implied Volatility](../api/python/implied_vol.md)