(american-options)=
# American Option Models

A pricing model for options with early exercise rights.

(american-options-theory)=
## Theoretical Background

(american-options-basic-concepts)=
### Basic Concepts

American options can be exercised at any point before their expiration date.
Early exercise rights make it always more valuable (or equivalent) than European options.

The Bjerksund-Stensland (2002) model provides a highly accurate analytical approximation solution for American options,
It achieves speeds more than 100 times faster than numerical methods (binomial trees, finite difference methods) while maintaining errors below 0.1%.

(american-options-assumptions)=
### Basic Assumption

1. **Lognormal Distribution**: Stock prices follow geometric Brownian motion
   
   ```{math}
   :name: american-options-eq-gbm
   
   dS_t = (\mu - q) S_t dt + \sigma S_t dW_t
   ```

2. **Efficient Market**: No trading costs, no taxes, and unlimited borrowing/lending

3. **Constant Parameters**: Volatilities, interest rates, and dividend yields remain constant

4. **Early exercise**: Allows option holders to exercise the option at any time before its expiration date.

5. **Optimal Exercise Strategy**: Investors choose strategies that maximize value

(american-options-derivation)=
## Derivation of Price Formula

(american-options-pde)=
### Partial Differential Equations for American Option Valuation

Formulated as a free boundary problem:

```{math}
:name: american-options-eq-pde

\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V}{\partial S^2} + (r-q)S\frac{\partial V}{\partial S} - rV = 0
```

Early exercise conditions:

```{math}
:name: american-options-eq-exercise-call

V(S,t) \geq \max(S-K, 0) \text{ for call}
```

```{math}
:name: american-options-eq-exercise-put

V(S,t) \geq \max(K-S, 0) \text{ for put}
```

(american-options-boundary-conditions)=
### boundary conditions

Call option:
- $V(S, T) = \max(S - K, 0)$
- $V(0, t) = 0$
- $V(S^*, t) = S^* - K$ (early exercise boundary)
- $\frac{\partial V}{\partial S}(S^*, t) = 1$ (smooth pasting)

Put Option:
- $V(S, T) = \max(K - S, 0)$
- $V(0, t) = K$
- $V(S^*, t) = K - S^*$ (early exercise boundary)
- $\frac{\partial V}{\partial S}(S^*, t) = -1$ (smooth pasting)

(american-options-analytical-solution)=
## Analytical Solutions

(american-options-european-call)=
### European Call (Bjerksund-Stensland 2002)

Approximate solution for American call:

```{math}
:name: american-options-eq-call-formula

C_{Am} = \alpha S_0^{\beta} - \alpha \phi(S_0, T, \beta, I, I) + \phi(S_0, T, 1, I, I) - \phi(S_0, T, 1, K, I) - K\phi(S_0, T, 0, I, I) + K\phi(S_0, T, 0, K, I)
```

where:
- $I = B_0 + (B_\infty - B_0)(1 - e^{h(T)})$ is the early exercise boundary
- $\alpha, \beta$ are auxiliary parameters
- $\phi$ is the auxiliary function

(american-options-european-put)=
### European Put

The approximate solution for American puts has a more complex structure than call options:

```{math}
:name: american-options-eq-put-formula

P_{Am} = K - S_0 + \text{European Put} + \text{Early Exercise Premium}
```

Early exercise premiums are calculated using optimal stopping theory.

(american-options-greeks)=
## Greeks

Price sensitivity indicators for American options:

```{list-table} American Option Greeks
:name: american-options-table-greeks
:header-rows: 1
:widths: 15 35 25 25

* - Greek
  - meaning
  - call
  - put
* - Delta
  - Stock sensitivity $\partial V/\partial S$
  - discontinuity at early exercise boundary
  - discontinuity at early exercise boundary
* - Gamma
  - rate of change of Delta $\partial^2 V/\partial S^2$
  - Rapid increase near boundary
  - Rapid increase near boundary
* - Vega
  - Volatility Sensitivity $\partial V/\partial \sigma$
  - smaller than European
  - smaller than European
* - Theta
  - Time Value Decay $-\partial V/\partial T$
  - Early exercise complexity
  - Early exercise complexity
* - Rho
  - Interest Sensitivity $\partial V/\partial r$
  - Normal
  - Negative (default)
```

(american-options-specific-features)=
### Characteristics Unique to American Options

1. **Impact of Early Exercise Bounds**
   - Delta: Hedging becomes difficult due to discontinuities at the boundary
   - Gamma: Spike formation near boundaries requires risk management attention

2. **Differences from European Models**
   - Vega: Lower volatility sensitivity due to early exercise possibility
   - Theta: Additional time decay for early exercise premium is added

3. **Numerical Computation Considerations**
   - Since no analytical expression exists, approximate using finite difference methods or Monte Carlo methods
   - Fast calculations are also possible using the Bjerksund-Stensland approximation

(american-options-black-scholes-relation)=
## Relationship with Black-Scholes

(american-options-value-relation)=
### Value Relationships

American option value ≥ European option value:

```{math}
:name: american-options-eq-value-relation

C_{American} \geq C_{European}, \quad P_{American} \geq P_{European}
```

(american-options-dividend-effect)=
### Dividend Impact

- **Dividend-Arbitrage Call**: American = European (not exercised early)
- **Dividend-paying calls**: American > European (can be exercised just before the dividend)
- **Put**: American > European regardless of dividend

(american-options-convergence)=
### Convergence Conditions

In the limit of short maturity, both approaches converge:

```{math}
:name: american-options-eq-convergence

\lim_{T \to 0} (American - European) = 0
```

(american-options-applications)=
## Applications

(american-options-equity-options)=
### Stock Options
- Individual Stock Options (During Dividend Payment)
- Employee Stock Options
- Early Exercise Option Warrants

(american-options-commodity-derivatives)=
### Product Derivatives
- Commodity Futures Options
- Energy Options (Crude Oil, Natural Gas)
- Agricultural Options

(american-options-interest-rate-derivatives)=
### Interest Rate Derivatives
- Bermuda swaptions
- Mortgage-Backed Securities (MBS)
- Prepayment Options

(american-options-numerical-considerations)=
## Numerical Computation Considerations

(american-options-accuracy-requirements)=
### Accuracy Requirements
- Price Accuracy: Error < 0.1% from true value
- Greeks Precision: Relative error < 1%
- Early exercise boundary: error < 0.5%

(american-options-numerical-challenges)=
### Numerical Challenges and Solutions

1. **Free boundary problems**
   - Solution: Exploring boundaries through iterative methods
   - Convergence criterion: $|S^*_{n+1} - S^*_n| < \epsilon$

2. **Handling Discontinuities**
   - Solution: Adaptive Mesh Refining
   - High resolution near early exercise boundary

3. **High-Speed Computation**
   - Solution: Use Bjerksund-Stensland approximation
   - Calculation time: < 50ns/option

(american-options-limitations-extensions)=
## Model Limitations and Extensions

(american-options-limitations)=
### Limitations
- **Discrete Dividends**: Discontinuities on ex-dividend dates
- **Stochastic Parameters**: Ignores fluctuations in volatility and interest rates
- **Trading Constraints**: Does not account for real-world market limitations
- **Taxation**: Taxes are ignored

(american-options-extensions)=
### Extended Models
- **Least Squares Monte Carlo**: Longstaff-Schwartz Method
- **Stochastic Volatility**: American Heston Model
- **Jump Diffusion**: American Merton Jump Model
- **Multi-Asset**: Basket American Option

(american-options-implementation-example)=
## Implementation Example (Conceptual)

```{code-block} python
:name: american-options-code-example
:caption: American call option pricing
:linenos:

# Conceptual implementation example (differs from actual API)
def american_call_price(s, k, t, r, sigma, q=0.0):
    """
    American call price using Bjerksund-Stensland 2002 model
    
    Parameters:
        s: Spot price
        k: Strike price
        t: Time to maturity
        r: Risk-free rate
        sigma: Volatility
        q: Dividend yield
    
    Returns:
        American call option price
    """
    # For no dividends, same as European
    if q == 0:
        return european_call_price(s, k, t, r, sigma)
    
    # Bjerksund-Stensland parameter calculation
    beta = calculate_beta(r, q, sigma)
    b_infinity = calculate_b_infinity(k, r, q, sigma)
    b_zero = max(k, r * k / (r - q))
    
    # Early exercise boundary calculation
    h_t = -(q * t + 2 * sigma * np.sqrt(t))
    i = b_zero + (b_infinity - b_zero) * (1 - np.exp(h_t))
    
    # Approximate price calculation
    if s >= i:
        return s - k  # Exercise immediately
    else:
        # Apply Bjerksund-Stensland formula
        alpha = calculate_alpha(i, k, r, q, beta)
        price = alpha * s**beta + phi_functions(s, t, beta, i, k, r, q, sigma)
        
    return price
```

(american-options-references)=
## References

1. Bjerksund, P. and Stensland, G. (2002). "Closed Form Valuation of American Options." *Working Paper, NHH Bergen*.

2. Longstaff, F.A. and Schwartz, E.S. (2001). "Valuing American Options by Simulation: A Simple Least-Squares Approach." *Review of Financial Studies*, 14(1), 113-147.

3. Hull, J.C. (2018). *Options, Futures, and Other Derivatives* (10th ed.). Pearson.

4. Barone-Adesi, G. and Whaley, R.E. (1987). "Efficient Analytic Approximation of American Option Values." *Journal of Finance*, 42(2), 301-320.

(american-options-related-docs)=
## Related Documents

- [American Option API](../api/python/american.md)
- [Black-Scholes Model](black_scholes.md)
- [Merton Model](merton.md)
- Binomial Tree Model (Under Development)
- Finite Difference Method (Under Development)
