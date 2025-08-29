# Merton Model

The standard model for option pricing theory considering dividends.

## Theoretical Background

### Basic Concepts

The Merton model is an extension of the Black-Scholes model to assets with dividend payments.
By considering continuous dividend yield, it enables accurate calculation of option prices for dividend-paying stocks, stock indices, foreign exchange, and other assets.

When there is a dividend yield `q`, the stock price after dividend payment becomes lower than the original stock price, so this effect needs to be incorporated into price calculations.

### Basic Assumptions

1. **Log-normal distribution**: Dividend-adjusted stock prices follow geometric Brownian motion
   $$dS_t = (\mu - q) S_t dt + \sigma S_t dW_t$$

2. **Continuous dividends**: Dividend yield `q` is constant and paid continuously

3. **Efficient market**: Same as Black-Scholes, no transaction costs or taxes, unlimited borrowing and lending

4. **Constant parameters**: Volatility, interest rate, and dividend yield are constant

## Derivation of Pricing Formula

### Merton Equation

Partial differential equation considering dividends:

$$\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V}{\partial S^2} + (r - q)S\frac{\partial V}{\partial S} - rV = 0$$

Note that the dividend yield `q` affects the drift term.

### Boundary Conditions

Call option:
- $V(S, T) = \max(S - K, 0)$
- $V(0, t) = 0$
- $V(S, t) \to S e^{-q(T-t)} - Ke^{-r(T-t)}$ as $S \to \infty$

Put option:
- $V(S, T) = \max(K - S, 0)$
- $V(0, t) = Ke^{-r(T-t)}$
- $V(S, t) \to 0$ as $S \to \infty$

## Analytical Solutions

### European Call

$$C = S_0 e^{-qT} N(d_1) - Ke^{-rT} N(d_2)$$

where:
- $d_1 = \frac{\ln(S_0/K) + (r - q + \sigma^2/2)T}{\sigma\sqrt{T}}$
- $d_2 = d_1 - \sigma\sqrt{T}$
- $N(x)$: Cumulative distribution function of standard normal distribution

### European Put

$$P = Ke^{-rT} N(-d_2) - S_0 e^{-qT} N(-d_1)$$

## Greeks

Option price sensitivity measures considering dividend yield:

| Greek | Meaning | Call | Put |
|-------|---------|------|-----|
| Delta | Stock price sensitivity $\partial V/\partial S$ | $e^{-qT} N(d_1)$ | $-e^{-qT} N(-d_1)$ |
| Gamma | Rate of change of delta $\partial^2 V/\partial S^2$ | $\frac{e^{-qT} \phi(d_1)}{S_0 \sigma \sqrt{T}}$ | Same |
| Vega | Volatility sensitivity $\partial V/\partial \sigma$ | $S_0 e^{-qT} \phi(d_1) \sqrt{T}$ | Same |
| Theta | Time decay $-\partial V/\partial T$ | See below | See below |
| Rho | Interest rate sensitivity $\partial V/\partial r$ | $KTe^{-rT}N(d_2)$ | $-KTe^{-rT}N(-d_2)$ |
| Dividend Rho | Dividend yield sensitivity $\partial V/\partial q$ | $-TS_0 e^{-qT}N(d_1)$ | $TS_0 e^{-qT}N(-d_1)$ |

where $\phi(x) = \frac{1}{\sqrt{2\pi}}e^{-x^2/2}$ is the standard normal probability density function

### Special Notes

- **Delta**: Due to the dividend adjustment factor $e^{-qT}$, it becomes smaller than Black-Scholes without dividends
- **Theta**: The dividend term $qS_0 e^{-qT}N(d_1)$ is added
- **Dividend Rho**: A Greek specific to the Merton model

### Theta Details

Call:
$$\Theta_{\text{call}} = -\frac{S_0 e^{-qT} \phi(d_1) \sigma}{2\sqrt{T}} + qS_0 e^{-qT}N(d_1) - rKe^{-rT}N(d_2)$$

Put:
$$\Theta_{\text{put}} = -\frac{S_0 e^{-qT} \phi(d_1) \sigma}{2\sqrt{T}} - qS_0 e^{-qT}N(-d_1) + rKe^{-rT}N(-d_2)$$

## Relationship with Black-Scholes

### Mathematical Relationship

When dividend yield `q = 0`, the Merton model perfectly matches the Black-Scholes model:

- $d_1 = \frac{\ln(S_0/K) + (r + \sigma^2/2)T}{\sigma\sqrt{T}}$ (identical to Black-Scholes)
- $C = S_0 N(d_1) - Ke^{-rT} N(d_2)$ (Black-Scholes pricing formula)

### Forward Price Interpretation

With dividend-adjusted Forward price $F = S_0 e^{(r-q)T}$:

$$d_1 = \frac{\ln(F/K) + \sigma^2T/2}{\sigma\sqrt{T}}$$

This structure is similar to the Black76 model.

## Applications

### Stock Index Options

Stock indices (S&P 500, Nikkei 225, etc.) reflect dividends from constituent stocks, so the Merton model is appropriate.
Example: Option pricing calculation for a stock index with 2% dividend yield

### Foreign Exchange Options

Can be applied to FX option pricing by treating foreign currency interest rates as dividend yields.
- Domestic interest rate: `r`
- Foreign interest rate: `q` (treated as dividend yield)

### Commodity Futures Options

Storage costs or convenience yields are incorporated into the dividend yield parameter for price calculation.

## Numerical Computation Considerations

### Precision Requirements

| Domain | Precision Target | Implementation Notes |
|--------|------------------|---------------------|
| Price precision | Relative error < 1e-6 | Standard implementation sufficient |
| Greeks | Relative error < 1e-5 | Finite difference verification recommended |
| Put-Call parity | Error < 1e-10 | For theoretical consistency verification |

### Numerical Challenges and Countermeasures

1. **Pre-calculation of dividend adjustment**
   - Pre-calculate and reuse dividend discount factor $e^{-qT}$
   - Minimize numerical errors by calculating with adjusted spot prices

2. **Stability at extreme values**
   - $q \to 0$: Switch to Black-Scholes calculation
   - $q \to r$: Handle as special case
   - Large $q$: Range check to prevent numerical overflow

3. **Optimization of exp function**
   - Pre-calculate common terms: $e^{-rT}$, $e^{-qT}$
   - Speed up through batch calculation in parallel processing

## Model Limitations and Extensions

### Limitations

1. **Continuous dividend assumption**: Actual dividends are discrete
2. **Constant dividend yield**: In reality, varies over time
3. **Constant volatility**: Fluctuates around ex-dividend dates
4. **Early exercise**: Does not handle American options

### Extended Models

1. **Discrete dividend models**: Explicitly model ex-dividend dates
2. **Stochastic dividend models**: Treat dividend yield as stochastic process
3. **American option support**: Combination with numerical methods (binomial trees, finite differences)
4. **Jump-Diffusion models**: Consider ex-dividend jumps

## Implementation Example (Conceptual)

```python
# Conceptual implementation example (different from actual API)
import numpy as np
from scipy.stats import norm

def merton_call(s, k, t, r, q, sigma):
    """
    Call option price using Merton model
    
    Parameters:
        s: Spot price
        k: Strike price
        t: Time to maturity (years)
        r: Risk-free interest rate
        q: Dividend yield
        sigma: Volatility
    """
    # Dividend adjustment
    dividend_discount = np.exp(-q * t)
    rate_discount = np.exp(-r * t)
    
    # Calculate d1, d2
    d1 = (np.log(s / k) + (r - q + 0.5 * sigma**2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)
    
    # Price calculation
    call_price = s * dividend_discount * norm.cdf(d1) - k * rate_discount * norm.cdf(d2)
    
    return call_price
```

## References

1. Merton, R.C. (1973). "Theory of Rational Option Pricing." *Bell Journal of Economics and Management Science*, 4(1), 141-183.

2. Black, F. and Scholes, M. (1973). "The Pricing of Options and Corporate Liabilities." *Journal of Political Economy*, 81(3), 637-654.

3. Hull, J.C. (2018). *Options, Futures, and Other Derivatives* (10th ed.). Pearson.

4. Haug, E.G. (2007). *The Complete Guide to Option Pricing Formulas* (2nd ed.). McGraw-Hill.

## Related Documents

- [Merton API](../api/python/merton.md) - Python API usage
- [Black-Scholes Model](black_scholes.md) - Basic model without dividends
- [Black76 Model](black76.md) - Model for futures and commodity options